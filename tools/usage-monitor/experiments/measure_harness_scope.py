#!/usr/bin/env python3
"""Reconcile the complete coding transfer panel, including unapplied policies."""
import collections,hashlib,json
from pathlib import Path
from harness_scope_trial import ROOT,frozen
from native_jsonl import records,meter_cell
from longmemeval_codex_trial import Store
from cost_context_study import REPO,PRICING

def measure():
    frozen()
    if not (ROOT/'complete.json').exists() or (ROOT/'results.json').exists():raise ValueError('Incomplete or previously measured panel')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();rates=json.loads(PRICING.read_text())['primary_scenario'];captures=[json.loads(p.read_text()) for p in (ROOT/'captures').glob('*.json')];cells=[]
    for item in json.loads((ROOT/'generation-complete.json').read_text())['cells']:
        cell=ROOT/item['case']/item['condition'];m=meter_cell(store,cell,item['session_id'],dict(case=item['case'],condition=item['condition'],role='reader'),rates);m['grade']=json.loads((cell/'grade.json').read_text());response_ids={i.rsplit(':response:',1)[-1] for i in m['native_response_ids']};matched=[d for d in captures if response_ids.intersection(d.get('response_ids',[]))];changes=[c for d in matched for c in d.get('compression',{}).get('changes',[])];sources=set()
        if len(matched)!=len(response_ids):raise ValueError('Request/native response coverage mismatch')
        for d in matched:
            for c in d.get('compression',{}).get('changes',[]):
                original=d['request']
                for key in c['path']:original=json.loads(original) if key=='json' else original[key]
                digest=c['source_sha256'];source=json.loads((ROOT/'captures/compression_sources'/(digest+'.json')).read_text())
                if hashlib.sha256(original.encode()).hexdigest()!=digest or source['content']!=original or source['retained_sha256']!=digest:raise ValueError('Nonexact archived source')
                sources.add(digest)
        marker_flags=[];message_characters=[]
        for d in matched:
            messages=[json.dumps(i.get('content'),ensure_ascii=False) for i in d['request'].get('input',[]) if i.get('type')=='message']
            marker_flags.append(any('HANDOVER.md' in t and 'Project preferences' in t for t in messages));message_characters.append(sum(map(len,messages)))
        applied=item['condition']=='scoped' and not any(marker_flags)
        m['application']=dict(kind='Experimental actor project-instruction scope',applied=applied,research_marker_requests=sum(marker_flags),requests=len(marker_flags),message_character_range=[min(message_characters),max(message_characters)],status='APPLIED' if applied else 'inherited control' if item['condition']=='inherited' else 'UNAPPLIED')
        cells.append(m)
    ids=[i for c in cells for i in c['native_response_ids']]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate response')
    totals={}
    for arm in sorted({c['condition'] for c in cells}):
        selected=[c for c in cells if c['condition']==arm];totals[arm]=dict(native_tokens=sum(c['usage']['total_tokens'] for c in selected),credit_rate_scenario=sum(c['cost'] for c in selected),passed=sum(c['grade']['passed'] for c in selected),cells=len(selected),applied_cells=sum(c['application']['applied'] for c in selected))
    result=dict(protocol=json.loads((ROOT/'protocol.json').read_text()),cells=cells,totals=totals,cash_cost=None,local_operational_cost=None,note='Reused3-case development setup diagnostic. Instructions remain unchanged for ordinary user agents. Observed native cost, not character savings; no official benchmark, population noninferiority or long-horizon memory claim.');(ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(totals,indent=2))
if __name__=='__main__':measure()
