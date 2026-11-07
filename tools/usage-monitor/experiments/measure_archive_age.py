#!/usr/bin/env python3
"""Audit actual old-history application by exact response IDs and native inputs."""
import hashlib,json
from pathlib import Path
from native_jsonl import records,validate_native_completion,meter_cell
from cost_context_study import PRICING,REPO
from longmemeval_codex_trial import Store
ROOT=REPO/'work/security/context-memory-20261107/archive-age-canary-001'
def path_value(value,path):
    for key in path:value=json.loads(value) if key=='json' else value[key]
    return value
def measure():
    if not (ROOT/'complete.json').exists():raise ValueError('Incomplete gate')
    if (ROOT/'results.json').exists():raise ValueError('Preserve previous measurement')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();rates=json.loads(PRICING.read_text())['primary_scenario'];cells=[];by_arm={};captures=[]
    for p in (ROOT/'captures').glob('*.json'):
        d=json.loads(p.read_text())
        if d.get('method')=='POST' and d.get('response_ids'):captures.append(d)
    captures.sort(key=lambda x:x['started_ns'])
    for arm in ('off','older-shell-mask'):
        cell=ROOT/arm;sid=validate_native_completion(cell);meter=meter_cell(store,cell,sid,dict(case='matched-age-mechanism',condition=arm),rates)
        with store.connection() as db:rows=[dict(r) for r in db.execute("SELECT id,usage FROM events WHERE session_id=? AND kind='generation'",(sid,))]
        native={r['id'].rsplit(':response:',1)[-1]:json.loads(r['usage']) for r in rows};requests=[d for d in captures if any(i in native for i in d['response_ids'])]
        if len(requests)!=len(native) or any(len(d['response_ids'])!=1 for d in requests):raise ValueError('Ambiguous request/native-response alignment')
        trajectory=[];sources=set();bypass=0
        for d in requests:
            request=d['request'];forward=d.get('forwarded_request',request);changes=d.get('compression',{}).get('changes',[]);outputs=[i for i,x in enumerate(request.get('input',[])) if x.get('type') in ('custom_tool_call_output','function_call_output') and x.get('status','completed')=='completed']
            protected=set(outputs[-4:]);changed_indices={c['path'][1] for c in changes}
            if protected.intersection(changed_indices):raise ValueError('Recent output transformed')
            for i in protected:
                if request['input'][i]!=forward['input'][i]:raise ValueError('Recent output metadata changed')
            for c in changes:
                text=path_value(request,c['path']);digest=c['source_sha256'];source=json.loads((ROOT/'captures/compression_sources'/(digest+'.json')).read_text())
                if hashlib.sha256(text.encode()).hexdigest()!=digest or source['content']!=text or source['retained_sha256']!=digest:raise ValueError('Source not exact')
                sources.add(digest)
            for i,x in enumerate(request.get('input',[])):
                if 'TTGL_RAW_EVIDENCE' in json.dumps(x.get('output','')):
                    if x!=forward['input'][i]:raise ValueError('Raw retrieval modified')
                    bypass+=1
            trajectory.append(dict(response_id=d['response_ids'][0],completed_outputs=len(outputs),transformations=len(changes),input_tokens=native[d['response_ids'][0]]['input_tokens']))
        commands=[r['item'] for r in records(cell) if r.get('type')=='item.completed' and r.get('item',{}).get('type')=='command_execution'];recovery=[c for c in commands if 'read_compression_source' in c['command']]
        correct=json.loads((cell/'mechanism-completion.json').read_text())['answer_correct'];by_arm[arm]=dict(trajectory=trajectory,unique_sources=len(sources),raw_bypasses=bypass,recovery_exit_codes=[c.get('exit_code') for c in recovery],answer_correct=correct);cells.append(meter)
    treated=by_arm['older-shell-mask'];raw=by_arm['off'];first=next((i for i,r in enumerate(treated['trajectory']) if r['transformations']),None);drop=None;raw_drop=None
    if first is not None and first>0:
        now=treated['trajectory'][first];drop=treated['trajectory'][first-1]['input_tokens']-now['input_tokens'];matches=[i for i,r in enumerate(raw['trajectory']) if r['completed_outputs']==now['completed_outputs']]
        if len(matches)==1 and matches[0]>0:
            i=matches[0];raw_drop=raw['trajectory'][i-1]['input_tokens']-raw['trajectory'][i]['input_tokens']
    passed=all(v['answer_correct'] for v in by_arm.values()) and drop is not None and drop>=256 and raw_drop is not None and raw_drop<256 and treated['raw_bypasses']>0 and treated['recovery_exit_codes']==[0]
    public=dict(id=ROOT.name,acceptance_passed=passed,first_transform_effective_input_drop=drop,raw_corresponding_drop=raw_drop,arms=by_arm,note='Actual native input application gate only. No token/cost saving or coding-performance inference; all calls are research expense.')
    result=dict(protocol=json.loads((ROOT/'protocol.json').read_text()),cells=cells,mechanism=public);(ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n');(REPO/'tools/usage-monitor/studies/archive-age-canary-results-001.json').write_text(json.dumps(public,indent=2)+'\n');print(json.dumps(public))
if __name__=='__main__':measure()
