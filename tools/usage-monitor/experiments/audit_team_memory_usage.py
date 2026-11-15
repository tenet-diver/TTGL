#!/usr/bin/env python3
"""Reconcile coding-team AND Luna maintenance responses; retain unknown requests.

Native response IDs are the deduplication key. Cached/reasoning tokens are
subsets. CLI completion counters and capture SSE are independent witnesses.
No inference, rate estimation, cash inference or log replay occurs here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observability'))
from capture_objects import CaptureObjects, read_capture
from codex_team_probe import save, sha
from codex_team_evidence import FIELDS, counters


def usage(response):
    u=response['usage']
    result=dict(input_tokens=u['input_tokens'],cached_input_tokens=u.get('input_tokens_details',{}).get('cached_tokens',0),
        cache_write_input_tokens=u.get('input_tokens_details',{}).get('cache_write_tokens',0),
        output_tokens=u['output_tokens'],reasoning_output_tokens=u.get('output_tokens_details',{}).get('reasoning_tokens',0),total_tokens=u['total_tokens'])
    if result['cached_input_tokens']>result['input_tokens'] or result['reasoning_output_tokens']>result['output_tokens'] or result['total_tokens']!=result['input_tokens']+result['output_tokens']:
        raise ValueError('Invalid provider usage subsets/total')
    return result


def unique_records(rows,sid):
    records={}
    for row in rows:
        if row.get('type')!='token_usage_record' or row.get('payload',{}).get('thread_id')!=sid:
            continue
        r=row['payload'];ident=r['response_id']
        if ident in records and records[ident]['usage']!=r['usage']:
            raise ValueError('Conflicting duplicate native response')
        records[ident]=r
    return records


def audit(root,capture_root):
    manifest=json.loads((root/'manifest.json').read_text()) if (root/'manifest.json').exists() else {}
    owners={};sessions={};unknown=[];expected_models={};cli_usage={}
    retained=root/'maintenance-owned-sessions';retained.mkdir(exist_ok=True)
    native_home=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
    # Account every started maintenance intent, including calls that never
    # reached a validated result/registry entry.
    for intent in sorted(root.rglob('call-*/intent.json')):
        cell=intent.parent;events=cell/'agent.jsonl'
        if (cell/'started.json').exists() and not (cell/'completion.json').exists():
            pid=json.loads((cell/'started.json').read_text())['pid']
            command=Path(f'/proc/{pid}/cmdline')
            if command.exists() and str(cell).encode() in command.read_bytes():
                raise ValueError('Owned maintenance process still active; audit before continuation')
        rows=[json.loads(x) for x in events.read_bytes().split(b'\n') if x.startswith(b'{')] if events.exists() else []
        ids={r['thread_id'] for r in rows if r.get('type')=='thread.started'}
        if len(ids)!=1:
            unknown.append(dict(kind='maintenance_intent_without_unique_session',path=str(cell.relative_to(root)),usage=None));continue
        sid=ids.pop();expected_models[sid]='gpt-6-luna'
        completions=[r['usage'] for r in rows if r.get('type')=='turn.completed']
        if len(completions)==1:cli_usage[sid]=completions[0]
        else:unknown.append(dict(kind='maintenance_without_cli_completion',thread=sid,usage=None))
        matches=list((native_home/'sessions').rglob('*'+sid+'.jsonl'))
        if len(matches)!=1:
            unknown.append(dict(kind='missing_or_ambiguous_maintenance_rollout',thread=sid,usage=None));continue
        copied=retained/matches[0].name
        if copied.exists() and copied.read_bytes()!=matches[0].read_bytes():raise ValueError('Previously sealed maintenance rollout changed')
        if not copied.exists():shutil.copyfile(matches[0],copied)
    paths=list((root/'home/sessions').rglob('*.jsonl'))+list(retained.glob('*.jsonl'))
    for path in paths:
        rows=[json.loads(line) for line in path.read_bytes().split(b'\n') if line]
        meta=next(r['payload'] for r in rows if r['type']=='session_meta');sid=meta['id']
        if sid in sessions:raise ValueError('Duplicate owned session file')
        records=unique_records(rows,sid)
        expected=expected_models.get(sid,manifest.get('model','gpt-6.1-sol'))
        models={r['payload']['model'] for r in rows if r['type']=='turn_context' and r['payload'].get('model')}
        if models and models!={expected}:raise ValueError('Unexpected model in owned session')
        for ident in records:
            if ident in owners:raise ValueError('Response belongs to multiple sessions')
            owners[ident]=sid
        summed={k:sum(r['usage'][k] for r in records.values()) for k in FIELDS.values()}
        if not records:unknown.append(dict(kind='owned_session_without_positive_records',thread=sid,usage=None))
        if sid in cli_usage and any(cli_usage[sid].get(k)!=summed[k] for k in ('input_tokens','cached_input_tokens','output_tokens')):
            raise ValueError('Maintenance CLI/native counters disagree')
        sessions[sid]=dict(model=expected,records=records,usage=summed,rollout_sha256=sha(path))
    # Coding RPC counters must be consistent and cover owned coding threads.
    rpc={}
    if (root/'rpc.jsonl').exists():
        snapshots={}
        for line in (root/'rpc.jsonl').read_bytes().split(b'\n'):
            if not line:continue
            m=json.loads(line).get('message',{})
            if m.get('method')=='thread/tokenUsage/updated':
                p=m['params'];snapshots.setdefault(p['threadId'],[]).append(p['tokenUsage'])
        rpc={sid:counters(values) for sid,values in snapshots.items()}
        for sid in set(rpc)-set(sessions):
            unknown.append(dict(kind='coding_rpc_without_owned_rollout',thread=sid,usage=None))
        for sid,s in sessions.items():
            if s['model']=='gpt-6-luna':continue
            if sid not in rpc or not rpc[sid]['complete']:
                unknown.append(dict(kind='coding_rpc_counter_gap',thread=sid,usage=None))
    target=root/'captures';target.mkdir(exist_ok=True)
    store=CaptureObjects(target/'capture-objects.sqlite');db=store.connect();seen=set();evidence=[];auxiliary=set()
    try:
        for path in sorted(capture_root.glob('*.json'))+sorted((capture_root/'pending').glob('*.json')):
            if path.parent.name=='pending' and (capture_root/path.name).exists():continue
            r=read_capture(path);request=r.get('request',{})
            sid=request.get('client_metadata',{}).get('thread_id') or request.get('prompt_cache_key')
            if sid not in sessions:continue
            original=json.loads(path.read_text())
            with db:
                for key in ('request','forwarded_request','response'):
                    if key in r and store.pack(r[key],db)!=original[key]:raise ValueError('Capture retention descriptor mismatch')
            copy=target/path.name
            if copy.exists() and copy.read_bytes()!=path.read_bytes():raise ValueError('Capture collision')
            if not copy.exists():shutil.copyfile(path,copy)
            if read_capture(copy)!=r:raise ValueError('Capture roundtrip failed')
            if r.get('status')!=200 or r.get('response_truncated') or path.parent.name=='pending':
                unknown.append(dict(kind='incomplete_transport',thread=sid,capture=path.name,usage=None));continue
            if r.get('original_request_sha256')!=r.get('forwarded_request_sha256'):raise ValueError('Model-facing request changed')
            for event in r.get('response',{}).get('sse_events',[]):
                if event.get('type')!='response.completed':continue
                response=event['response'];ident=response['id']
                if ident not in owners:raise ValueError('Captured response absent from native records')
                session=sessions[owners[ident]];native=session['records'][ident]
                if usage(response)!=native['usage'] or response['model']!=session['model']:raise ValueError('Native/provider usage or model mismatch')
                seen.add(ident);evidence.append(dict(response_id=ident,thread=sid,model=session['model'],capture=path.name))
                if any(x.get('type')=='compaction_trigger' for x in request.get('input',[])):
                    auxiliary.add(ident)
        missing=set(owners)-seen
        if missing:raise ValueError('Missing response transport receipts: '+str(len(missing)))
    finally:db.close()
    bymodel={};rpc_tails=[]
    for sid,s in sessions.items():
        if sid in rpc and rpc[sid]['complete']:
            ordinary=[r for ident,r in s['records'].items() if ident not in auxiliary]
            target={name:rpc[sid]['total'][key] for key,name in FIELDS.items()}
            summed={key:sum(r['usage'][key] for r in ordinary) for key in FIELDS.values()}
            if summed!=target:
                from codex_team_grade_v2 import prefix_length
                length=prefix_length(ordinary,target)
                rpc_tails.append(dict(thread=sid,rpc_response_prefix=length,native_responses=len(ordinary),
                    scope='Exact native+transport tail counted; RPC delivery incomplete'))
        bucket=bymodel.setdefault(s['model'],dict.fromkeys(FIELDS.values(),0))
        for k in bucket:bucket[k]+=s['usage'][k]
        del s['records']
    known={k:sum(v[k] for v in bymodel.values()) for k in FIELDS.values()}
    if not owners:unknown.append(dict(kind='no_positive_native_inference',usage=None))
    result=dict(complete=not unknown,usage=known,usage_by_model=bymodel,total_inference_usage=known if not unknown else None,
        unknown_requests=unknown,distinct_responses=len(owners),sessions=sessions,responses=evidence,
        rpc_delivery_complete=not rpc_tails,rpc_consistent_prefixes=rpc_tails,
        includes='parent, workers and every recorded Luna maintenance intent; complete native responses deduplicated',
        subscription_cash_expense=None,source_sha256=sha(Path(__file__)))
    save(root/'combined-usage-audit.json',result)
    print(json.dumps({k:result[k] for k in ('complete','usage','usage_by_model','distinct_responses','unknown_requests')}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--capture-root',type=Path,required=True)
    a=p.parse_args();audit(a.root.resolve(),a.capture_root.resolve())
