#!/usr/bin/env python3
"""Reconcile the complete coding transfer panel, including unapplied policies."""
import collections,hashlib,json
from pathlib import Path
from coding_context_transfer import ROOT,frozen
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
        commands=[r['item'] for r in records(cell) if r.get('type')=='item.completed' and r.get('item',{}).get('type')=='command_execution'];recovery=[c for c in commands if 'read_compression_source' in c.get('command','')];m['application']=dict(transformations=len(changes),unique_exact_sources=len(sources),status='APPLIED' if changes else 'UNAPPLIED' if item['condition']!='off' else 'raw control',recovery_attempts=len(recovery),recovery_exit_codes=[c.get('exit_code') for c in recovery]);cells.append(m)
    ids=[i for c in cells for i in c['native_response_ids']]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate response')
    totals={}
    for arm in sorted({c['condition'] for c in cells}):
        selected=[c for c in cells if c['condition']==arm];totals[arm]=dict(native_tokens=sum(c['usage']['total_tokens'] for c in selected),credit_rate_scenario=sum(c['cost'] for c in selected),passed=sum(c['grade']['passed'] for c in selected),cells=len(selected),applied_cells=sum(c['application']['transformations']>0 for c in selected))
    result=dict(protocol=json.loads((ROOT/'protocol.json').read_text()),cells=cells,totals=totals,cash_cost=None,local_operational_cost=None,note='Three public exercise development cases; zero-transform cells are unapplied, not compression efficacy. No official benchmark, population noninferiority or long-horizon memory claim.');(ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(totals,indent=2))
if __name__=='__main__':measure()
