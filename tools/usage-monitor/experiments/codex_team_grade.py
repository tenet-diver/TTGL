#!/usr/bin/env python3
"""Source-only independent replay and three-source usage audit; zero inference."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

from codex_team_coding import docker
from codex_team_evidence import counters, FIELDS
from codex_team_probe import save, sha
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'observability'))
from capture_objects import read_capture, CaptureObjects


def grade(root):
    if not any((root/n).exists() for n in ('completed.json','stopped.json')):
        raise ValueError('Generation must end before independent replay')
    target=root/'independent-grade';target.mkdir(exist_ok=False)
    m=json.loads((root/'manifest.json').read_text());entry=m['base'];base=Path(entry['source'])
    if any(sha(base/p)!=v for p,v in entry['hashes'].items()):
        raise ValueError('Sealed base changed')
    actor=root/'actor';relative=m.get('src_dir','tinydb')
    source=actor/relative
    if any(p.is_symlink() for p in source.rglob('*')):
        raise ValueError('Symlink artifacts require audit; not replayed')
    shutil.copytree(base,target/'replay')
    shutil.rmtree(target/'replay'/relative)
    shutil.copytree(source,target/'replay'/relative)
    paths=set(entry['hashes'])|{str(p.relative_to(actor)) for p in actor.rglob('*') if p.is_file()}
    changed=[p for p in sorted(paths) if not (actor/p).is_file() or entry['hashes'].get(p)!=sha(actor/p)]
    outside=[p for p in changed if not (p==relative or p.startswith(relative+'/'))]
    unexpected=[p for p in outside if not (p.endswith('.md') and '/' not in p and p not in entry['hashes'])]
    command=['run','--rm','--name','ttgl-grade-'+root.name,'--network=none','--read-only','--cap-drop=ALL',
        '--security-opt=no-new-privileges','--user','1000:1000','--pids-limit','64','--memory','512m','--cpus','2',
        '--tmpfs','/tmp:rw,noexec,nosuid,size=128m',
        '--mount',f'type=bind,src={target/"replay"},dst=/task,readonly',
        '--mount',f'type=bind,src={m["runtime"]},dst=/runtime,readonly',
        '--mount',f'type=bind,src={target},dst=/results',
        '--env','PYTHONPATH=/runtime:/task/src:/task','--env','PYTHONDONTWRITEBYTECODE=1',
        '--env','COVERAGE_FILE=/tmp/.coverage','--workdir','/task',m['image'],
        'python3','-m','pytest','-p','no:cacheprovider','-q','--junitxml=/results/junit.xml','tests/']
    save(target/'started.json',dict(command=command,at=datetime.now(timezone.utc).isoformat(),source_sha256=sha(Path(__file__)),
        submitted_source_hashes={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()},changed_paths=changed,excluded_changes=outside))
    with (target/'stdout.log').open('xb') as log:
        process=docker(command,stdout=log,stderr=__import__('subprocess').STDOUT,timeout=240)
    suites=list(ET.parse(target/'junit.xml').getroot().iter('testsuite'))
    stats={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    value=dict(exit_code=process.returncode,junit=stats,passed=process.returncode==0 and stats['tests']>0 and not stats['errors'] and not stats['failures'],
        artifact_policy_clean=not unexpected,excluded_changes=outside,unexpected_changes=unexpected,
        scope='Prescribed public tests restored from sealed base; source-only replay, new root Markdown notes excluded; no hidden-test claim',model_calls=0)
    save(target/'result.json',value);print(json.dumps(value))


def audit(root):
    manifest=json.loads((root/'manifest.json').read_text());threads={};owned={};snapshots={}
    messages=[json.loads(l).get('message',{}) for l in (root/'rpc.jsonl').read_text().splitlines()]
    for m in messages:
        if m.get('method')=='thread/tokenUsage/updated':
            p=m['params'];snapshots.setdefault(p['threadId'],[]).append(p['tokenUsage'])
    rpc={sid:counters(values) for sid,values in snapshots.items()}
    for path in (root/'home/sessions').rglob('*.jsonl'):
        rows=[json.loads(l) for l in path.read_text().splitlines()]
        meta=next(r['payload'] for r in rows if r['type']=='session_meta');sid=meta['id']
        records=[r['payload'] for r in rows if r['type']=='token_usage_record' and r['payload'].get('thread_id')==sid]
        byid={}
        for r in records:
            ident=r['response_id']
            if ident in byid and r['usage']!=byid[ident]['usage']:
                raise ValueError('Inconsistent duplicate native response')
            byid[ident]=r
        sums={key:sum(r['usage'][key] for r in byid.values()) for key in FIELDS.values()}
        if any(ident in owned for ident in byid):
            raise ValueError('Response attributed to multiple threads')
        owned.update({ident:sid for ident in byid})
        threads[sid]=dict(parent=meta.get('parent_thread_id'),model_ids=sorted({r['payload']['model'] for r in rows if r['type']=='turn_context' and r['payload'].get('model')}),
            unique_responses=len(byid),usage=sums,records=byid)
    captures={};unknown=[]
    for p in Path(manifest['private_capture']).glob('*.json'):
        r=read_capture(p)
        metadata=r.get('request',{}).get('client_metadata',{})
        capture_thread=metadata.get('thread_id') or r.get('request',{}).get('prompt_cache_key')
        if capture_thread not in threads:
            continue
        for ident in r.get('response_ids',[]):
            if ident in owned:captures.setdefault(ident,[]).append((p,r))
        if r.get('operation')!='catalog' and (r.get('status')!=200 or r.get('response_truncated')):
            unknown.append(p.name)
    evidence=[];auxiliary=[]
    retained=root/'captures'
    retained.mkdir(exist_ok=False)
    retained_store=CaptureObjects(retained/'capture-objects.sqlite')
    retained_db=retained_store.connect()
    for sid,t in threads.items():
        for ident,native in t['records'].items():
            matches=captures.get(ident,[])
            if not matches:raise ValueError('Missing transport receipt: '+ident)
            for p,r in matches:
                if r.get('status')!=200 or r.get('response_truncated') or r['original_request_sha256']!=r['forwarded_request_sha256']:
                    raise ValueError('Incomplete/changed transport')
                ends=[e['response'] for e in r['response'].get('sse_events',[]) if e.get('type')=='response.completed' and e['response']['id']==ident]
                if len(ends)!=1:raise ValueError('Missing unique transport completion')
                response=ends[0];u=response['usage']
                observed=dict(input_tokens=u['input_tokens'],cached_input_tokens=u.get('input_tokens_details',{}).get('cached_tokens',0),
                    cache_write_input_tokens=u.get('input_tokens_details',{}).get('cache_write_tokens',0),output_tokens=u['output_tokens'],
                    reasoning_output_tokens=u.get('output_tokens_details',{}).get('reasoning_tokens',0),total_tokens=u['total_tokens'])
                if observed!=native['usage'] or response['model']!=manifest['model']:
                    raise ValueError('Native/transport usage or model mismatch')
                original=json.loads(p.read_text())
                with retained_db:
                    for key in ('request','forwarded_request','response'):
                        if key in r and retained_store.pack(r[key],retained_db)!=original[key]:
                            raise ValueError('Retained capture descriptor mismatch')
                copied=retained/p.name
                if copied.exists():
                    if copied.read_bytes()!=p.read_bytes():raise ValueError('Capture identity collision')
                else:
                    copied.write_bytes(p.read_bytes())
                if read_capture(copied)!=r:
                    raise ValueError('Durable capture roundtrip failed')
                if any(x.get('type')=='compaction_trigger' for x in r['request'].get('input',[])):
                    auxiliary.append(ident)
            evidence.append(dict(id=ident,thread=sid,usage=native['usage'],capture_files=[p.name for p,r in matches],duplicate_deliveries=len(matches)-1))
        ordinary={key:sum(r['usage'][key] for ident,r in t['records'].items() if ident not in auxiliary) for key in FIELDS.values()}
        if sid not in rpc or not rpc[sid]['complete'] or {key:rpc[sid]['total'][k] for k,key in FIELDS.items()}!=ordinary:
            raise ValueError('RPC/native ordinary usage mismatch')
        del t['records']
    if set(rpc)!=set(threads) or not owned:raise ValueError('Thread coverage missing')
    retained_db.close()
    value=dict(at=datetime.now(timezone.utc).isoformat(),complete=not unknown,unknown_http_receipts=unknown,
        threads=threads,responses=evidence,auxiliary_response_ids=sorted(set(auxiliary)),
        usage={k:sum(t['usage'][k] for t in threads.values()) for k in FIELDS.values()},
        subscription_cash_expense=None,rate_scenario_cost=None,
        runtime_seconds=json.loads((root/'completed.json').read_text())['wall_seconds'] if (root/'completed.json').exists() else None,
        source='Deduplicated native response records, unchanged capture SSE, and RPC counters; cached/reasoning subsets counted once')
    save(root/'usage-audit.json',value);print(json.dumps({k:v for k,v in value.items() if k not in ('threads','responses')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['grade','audit']);p.add_argument('--root',required=True,type=Path)
    a=p.parse_args();(grade if a.action=='grade' else audit)(a.root.resolve())
