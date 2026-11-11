#!/usr/bin/env python3
"""Read-only pilot analysis from preserved evidence; no inference or tuning."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import statistics
import sys
import tarfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'observability'))
from capture_objects import read_capture


class Evidence:
    def __init__(self, root):
        self.root=root
        path=root/('snapshot.tar.xz' if (root/'snapshot.tar.xz').exists() else 'snapshot.tar.gz')
        self.archive=tarfile.open(path) if path.exists() else None

    def read(self, relative):
        p=self.root/relative
        if p.is_file():return p.read_bytes()
        if self.archive:return self.archive.extractfile(relative).read()
        raise FileNotFoundError(relative)

    def close(self):
        if self.archive:self.archive.close()

    def names(self):
        names={str(p.relative_to(self.root)) for p in self.root.rglob('*') if p.is_file()}
        if self.archive:names.update(self.archive.getnames())
        return names


def price(usage):
    i,k,o=usage['input_tokens'],usage['cached_input_tokens'],usage['output_tokens']
    if not 0<=k<=i or usage.get('cache_write_input_tokens',0):
        raise ValueError('Unsupported cache counter semantics')
    return dict(standard_credit_scenario=((i-k)*50+k*2.5+o*250)/1e6,
        standard_api_equivalent_usd=((i-k)*2+k*.1+o*10)/1e6)


def memory_exposure(items):
    """Exact returned observation exposure; assertion/retrieval is not causality."""
    published={};reads=[];writes=0;errors=0
    for (sid,ident),item in sorted(items.items(),key=lambda pair:pair[1].get('completedAtMs') or 0):
        if item.get('type')!='mcpToolCall' or item.get('server')!='team_memory':continue
        result=item.get('result') or {}
        if item.get('error') or result.get('isError'):
            errors+=1;continue
        value=result.get('structuredContent')
        if value is None:
            texts=[c['text'] for c in result.get('content',[]) if c.get('type')=='text']
            try:value=json.loads(texts[0]) if len(texts)==1 else {}
            except (ValueError,TypeError):value={}
        tool=item['tool'];finished=item.get('completedAtMs');started=item.get('startedAtMs')
        if tool=='create_entities':
            entities=value.get('entities',[]) if isinstance(value,dict) else value
            for entity in entities or []:
                for note in entity.get('observations',[]):
                    key=(entity['name'],note);published[key]=(sid,finished);writes+=1
        elif tool=='add_observations':
            values=value.get('results',[]) if isinstance(value,dict) else value
            for entity in values or []:
                for note in entity.get('addedObservations',[]):
                    key=(entity['entityName'],note);published[key]=(sid,finished);writes+=1
        elif tool in ('read_graph','search_nodes','open_nodes'):
            entities=value.get('entities',[]) if isinstance(value,dict) else []
            peers=[]
            for entity in entities:
                for note in entity.get('observations',[]):
                    origin=published.get((entity['name'],note))
                    if origin and origin[0]!=sid and origin[1] is not None and started is not None and origin[1]<=started:
                        peers.append(dict(entity=entity['name'],observation_sha256=hashlib.sha256(note.encode()).hexdigest(),author_thread=origin[0]))
            reads.append(dict(item_id=ident,reader_thread=sid,completed_at_ms=finished,returned_entities=len(entities),peer_observations=peers))
    return dict(published_observations=writes,successful_reads=reads,explicit_tool_errors=errors,
        cross_agent_read_calls=sum(bool(r['peer_observations']) for r in reads),
        cross_agent_observation_exposures=sum(len(r['peer_observations']) for r in reads),
        definition='Exact observation text returned to a different thread after its publishing call completed. Conservative timing; relation-only/metadata-only exposure excluded. No causal action inference.')


def mechanism(root):
    e=Evidence(root)
    try:
        rows=[json.loads(l).get('message',{}) for l in e.read('rpc.jsonl').splitlines()]
        statuses={};peak_active=0
        for row in rows:
            if row.get('method')=='thread/status/changed':
                p=row['params'];statuses[p['threadId']]=p['status']['type']
                peak_active=max(peak_active,sum(v=='active' for v in statuses.values()))
        items={}
        for r in rows:
            if r.get('method')=='item/completed':
                p=r['params'];item=p['item'];items[(p.get('threadId'),item['id'])]=item
        terminal=[];memory=[];activity=Counter();notebook=[]
        for (sid,ident),i in items.items():
            if i['type']=='subAgentActivity':activity[i['kind']]+=1
            if i['type']!='mcpToolCall':continue
            if i.get('server')=='repository' and i.get('tool')=='terminal':
                command=i.get('arguments',{}).get('command','')
                terminal.append(dict(thread=sid,id=ident,command=command,native_duration_ms=i.get('durationMs')))
                if 'KNOWLEDGE.md' in command:
                    notebook.append(dict(thread=sid,id=ident,command_sha256=hashlib.sha256(command.encode()).hexdigest()))
            if i.get('server')=='team_memory':
                memory.append(dict(thread=sid,id=ident,tool=i['tool'],status=i.get('status')))
        commands=defaultdict(list)
        for t in terminal:commands[t['command']].append(t)
        repeated=[dict(command_sha256=hashlib.sha256(command.encode()).hexdigest(),calls=len(ts),threads=len({t['thread'] for t in ts}),item_ids=[t['id'] for t in ts])
            for command,ts in commands.items() if len(ts)>1 and len({t['thread'] for t in ts})>1]
        usage=json.loads(e.read('usage-audit.json'))
        communication=[];communication_ids=set();triggered_messages=0;native_versions=set()
        for name in sorted(e.names()):
            if not name.startswith('home/sessions/') or not name.endswith('.jsonl'):continue
            native=[json.loads(line) for line in e.read(name).splitlines()]
            meta=next(r['payload'] for r in native if r['type']=='session_meta');sid=meta['id']
            if meta.get('multi_agent_version'):native_versions.add(meta['multi_agent_version'])
            turns={r['payload']['turn_id'] for r in native if r['type']=='token_usage_record' and r['payload'].get('thread_id')==sid}
            returned={r['payload'].get('call_id') for r in native if r['type']=='response_item' and r['payload'].get('type')=='function_call_output'}
            own_context=False
            for row in native:
                p=row['payload']
                if row['type']=='turn_context':own_context=p.get('turn_id') in turns
                if not own_context:continue
                if row['type']=='inter_agent_communication_metadata' and p.get('trigger_turn'):triggered_messages+=1
                if row['type']!='response_item' or p.get('type')!='function_call' or p.get('namespace')!='collaboration':continue
                if p['id'] in communication_ids:continue
                communication_ids.add(p['id']);args=json.loads(p['arguments'])
                message=args.get('message')
                communication.append(dict(item_id=p['id'],at=row.get('timestamp'),source_agent=meta.get('agent_path','/root'),
                    operation=p['name'],target=args.get('target') or args.get('task_name'),
                    call_id=p.get('call_id'),tool_return_observed=p.get('call_id') in returned,
                    message_content='opaque_encrypted' if isinstance(message,str) and message.startswith('gAAAA') else 'visible' if message is not None else 'absent'))
        intervals=[];max_prompt=0;seen_frames=set();capacity_guidance=set();checked_root=False
        for response in usage['responses']:
            if not response['capture_files']:raise ValueError('No capture')
            raw=json.loads(e.read('captures/'+response['capture_files'][0]))
            intervals.append((raw['started_ns'],raw['ended_ns']))
            seen_frames.add(response['capture_files'][0])
            max_prompt=max(max_prompt,response['usage']['input_tokens'])
            # This is server-supplied runtime guidance, separate from CLI flags.
            if not checked_root and usage['threads'][response['thread']]['parent'] is None:
                checked_root=True
                decoded=read_capture(root/'captures'/response['capture_files'][0])
                for item in decoded.get('request',{}).get('input',[]):
                    for content in item.get('content',[]):
                        text=content.get('text','') if isinstance(content,dict) else ''
                        if isinstance(text,str):
                            capacity_guidance.update(map(int,re.findall(r'There are (\d+) available concurrency slots',text)))
        try:
            classification=json.loads(e.read('usage-classification-001.json'))
        except (FileNotFoundError, KeyError):
            classification=dict(unknown_requests=[])
        for unknown in classification['unknown_requests']:
            name=unknown['capture']
            if name not in seen_frames:
                raw=json.loads(e.read('captures/'+name));intervals.append((raw['started_ns'],raw['ended_ns']));seen_frames.add(name)
        events=[(s,1) for s,t in intervals]+[(t,-1) for s,t in intervals]
        active=peak=0
        for at,delta in sorted(events):active+=delta;peak=max(peak,active)
        rates=price(usage['usage'])
        if max_prompt>272000:
            rates['standard_api_equivalent_usd']=sum(
                price(r['usage'])['standard_api_equivalent_usd']*(1 if r['usage']['input_tokens']<=272000 else 0)
                + (((r['usage']['input_tokens']-r['usage']['cached_input_tokens'])*4+r['usage']['cached_input_tokens']*.2+r['usage']['output_tokens']*15)/1e6 if r['usage']['input_tokens']>272000 else 0)
                for r in usage['responses'])
        try:completion=json.loads(e.read('completed.json'))
        except (FileNotFoundError,KeyError):completion=dict(turn=dict(status='stopped',error=None))
        return dict(actual_threads=len(usage['threads']),observed_models=sorted({model for t in usage['threads'].values() for model in t['model_ids']}),
            parent_native_status=completion['turn']['status'],parent_native_error=completion['turn'].get('error'),
            rpc_delivery_complete=usage.get('rpc_delivery_complete',True),
            observed_active_threads_peak=peak_active if statuses else None,
            native_status_coverage_complete=set(statuses)==set(usage['threads']),
            thread_count_definition='Distinct owned threads; peak native active includes coordination/waiting. HTTP overlap is separately observed and does not equal GPU use.',
            peak_overlapping_http_requests=peak,terminal_calls=len(terminal),
            summed_native_terminal_ms=sum(t['native_duration_ms'] or 0 for t in terminal),
            cross_thread_exact_command_repetitions=repeated,
            memory_calls=memory,memory_exposure=memory_exposure(items),notebook_mentions=notebook,subagent_activity=dict(activity),
            collaboration_calls=communication,turn_triggering_message_metadata=triggered_messages,
            communication_content_limit='Only native function-call routing metadata; encrypted messages remain opaque. Inherited parent context excluded using owned turn IDs.',
            observed_native_multi_agent_versions=sorted(native_versions),server_capacity_guidance=sorted(capacity_guidance),
            max_request_input_tokens=max_prompt,**rates)
    finally:e.close()


def analyze(root, output):
    if output.exists():raise ValueError('Preserve prior analysis snapshots')
    checkpoints=sorted(root.glob('checkpoint-*.json'))
    if not checkpoints:raise ValueError('No completed audited assignments')
    assignments=json.loads(checkpoints[-1].read_text())['assignments'];cells=[]
    for assignment in assignments:
        m=mechanism(root/assignment['directory'])
        complete=assignment.get('inference_accounting_complete',True)
        value=dict(assignment,**m,inference_accounting_complete=complete)
        value['standard_credit_lower_bound']=value.pop('standard_credit_scenario')
        value['api_equivalent_lower_bound_usd']=value.pop('standard_api_equivalent_usd')
        value['full_standard_credit_scenario']=value['standard_credit_lower_bound'] if complete else None
        value['full_standard_api_equivalent_usd']=value['api_equivalent_lower_bound_usd'] if complete else None
        if value['wall_seconds'] is None:
            value['wall_seconds']=json.loads((root/assignment['directory']/'stopped.json').read_text())['wall_seconds']
        cells.append(value)
    grouped=[]
    for condition in ('native','notebook','mcp_memory'):
        for cap in (1,2,4,8):
            selected=[x for x in cells if x['condition']==condition and x['total_agent_capacity']==cap]
            if not selected:continue
            successes=sum(x['grade']['passed'] and x['grade']['artifact_policy_clean'] for x in selected)
            cost=sum(x['standard_credit_lower_bound'] for x in selected)
            complete=all(x['inference_accounting_complete'] for x in selected)
            grouped.append(dict(condition=condition,total_agent_capacity=cap,assignments=len(selected),verified_resolutions=successes,
                mean_attempt_seconds=statistics.mean(x['wall_seconds'] for x in selected),
                cost_accounting_complete=complete,total_standard_credit_lower_bound=cost,
                total_full_standard_credit_scenario=cost if complete else None,
                cost_per_verified_resolution=cost/successes if successes and complete else None,
                cost_per_verified_resolution_lower_bound=cost/successes if successes else None,
                total_api_equivalent_lower_bound_usd=sum(x['api_equivalent_lower_bound_usd'] for x in selected),
                mean_actual_threads=statistics.mean(x['actual_threads'] for x in selected)))
    output.mkdir(parents=True,exist_ok=False)
    paired=[]
    for cell in cells:
        for comparison,control in [('versus_native_single',next((x for x in cells if x['task']==cell['task'] and x['condition']=='native' and x['total_agent_capacity']==1),None)),
                                   ('versus_native_same_capacity',next((x for x in cells if x['task']==cell['task'] and x['condition']=='native' and x['total_agent_capacity']==cell['total_agent_capacity']),None))]:
            if control is None or control['directory']==cell['directory']:continue
            a,b=cell['standard_credit_lower_bound'],control['standard_credit_lower_bound']
            exact=a/b if cell['inference_accounting_complete'] and control['inference_accounting_complete'] else None
            lower=a/b if control['inference_accounting_complete'] else None
            upper=a/b if cell['inference_accounting_complete'] else None
            paired.append(dict(task=cell['task'],condition=cell['condition'],capacity=cell['total_agent_capacity'],comparison=comparison,
                both_verified=cell['grade']['passed'] and control['grade']['passed'] and cell['grade']['artifact_policy_clean'] and control['grade']['artifact_policy_clean'],
                observed_attempt_speedup=control['wall_seconds']/cell['wall_seconds'],
                exact_credit_ratio=exact,credit_ratio_lower_bound=lower,credit_ratio_upper_bound=upper,
                strictly_more_expensive_identified=lower is not None and lower>1,
                strictly_cheaper_identified=upper is not None and upper<1))
    result=dict(at=datetime.now(timezone.utc).isoformat(),complete=(root/'completion.json').exists(),completed=len(cells),planned=24,
        cells=cells,grouped=grouped,paired=paired,pricing_sources=['https://learn.chatgpt.com/docs/pricing','https://developers.openai.com/api/docs/models/gpt-6.1-sol'],
        pricing_checked='2026-11-11',subscription_cash_expense=None,
        limitations=['Two development repositories, one attempt per cell; descriptive, no population inference',
            'HTTP overlap includes network/queueing; not a GPU utilization measure',
            'Exact command repetition can be useful verification; not automatically wasted work',
            'Standard-rate scenarios are not observed subscription charges or quota savings',
            'Interrupted native streams can lack usage; completed-response totals are lower bounds, full cost is unknown in those cells',
            'A lower bound above a fully measured control can identify a cost increase; overlapping unknown bounds cannot establish a ranking',
            'Knowledge mentions/exposure are not proof of a causal effect',
            'Attempt time includes failures; success-only latency must not substitute for completion rates'])
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    with (output/'cells.csv').open('w') as stream:
        fields=['task','condition','total_agent_capacity','verified','parent_native_status','wall_seconds','actual_threads','observed_active_threads_peak','peak_overlapping_http_requests','terminal_calls','metered_tokens_lower_bound','inference_accounting_complete','standard_credit_lower_bound','full_standard_credit_scenario','api_equivalent_lower_bound_usd','full_standard_api_equivalent_usd']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for x in cells:
            writer.writerow({k:(x['grade']['passed'] and x['grade']['artifact_policy_clean'] if k=='verified' else x['usage']['total_tokens'] if k=='metered_tokens_lower_bound' else x[k]) for k in fields})
    print(json.dumps(dict(completed=len(cells),complete=result['complete'],grouped=grouped)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();analyze(a.root.resolve(),a.output.resolve())
