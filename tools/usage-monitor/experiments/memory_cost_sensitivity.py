#!/usr/bin/env python3
"""Role-aware published-rate sensitivity; never reprice research judges as deployment."""
import argparse
import json
from pathlib import Path
import sqlite3
from cost_context_study import price,PRICING,REPO


def summarize(cells,rates,api):
    arms={}
    for cell in cells:
        if cell['role']=='judge_overhead':continue
        arm=arms.setdefault(cell['condition'],dict(usage={k:0 for k in ('input_tokens','cached_input_tokens','output_tokens')},api_rate_sensitivity_usd=0,api_long_context_responses=0))
        for key in arm['usage']:arm['usage'][key]+=cell['usage'][key]
        for response in cell['responses']:
            u=response['usage'];adjusted=dict(api)
            if u['input_tokens']>api['long_context_threshold_input_tokens']:
                arm['api_long_context_responses']+=1
                for key in ('fresh_input_per_million','cached_input_per_million'):adjusted[key]*=api['long_context_input_multiplier']
                adjusted['output_per_million']*=api['long_context_output_multiplier']
            value=price(u,adjusted) if u.get('cache_write_input_tokens')==0 else None
            if value is None:arm['api_rate_sensitivity_usd']=None
            elif arm['api_rate_sensitivity_usd'] is not None:arm['api_rate_sensitivity_usd']+=value
    for arm in arms.values():
        arm['primary_credit_rate_scenario']=price(arm['usage'],rates)
        ratio=rates['output_per_million']/rates['fresh_input_per_million']
        arm['normalized_cache_price_sensitivity']={str(x):price(arm['usage'],dict(fresh_input_per_million=1,cached_input_per_million=x,output_per_million=ratio)) for x in (0,.01,.05,.1,.25,1)}
    return arms


def audit(directory,database,pricing):
    result=json.loads((directory/'results.json').read_text());cells=[];seen=set()
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
        for cell in result['cells']:
            responses=[]
            for ident in cell['native_response_ids']:
                if ident in seen:raise ValueError('Duplicate native response across study roles')
                seen.add(ident)
                row=db.execute('SELECT usage FROM events WHERE id=? AND kind=?',(ident,'generation')).fetchone()
                if row is None:raise ValueError('Missing native response')
                u=json.loads(row[0]);price(u,pricing['primary_scenario']);responses.append(dict(usage=u))
            u={k:sum(r['usage'].get(k,0) for r in responses) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')}
            if u!=cell['usage']:raise ValueError('Native reconciliation changed')
            cells.append(dict(role=cell['role'],condition=cell['condition'],usage=u,responses=responses))
    return dict(study=result['protocol']['id'],arms=summarize(cells,pricing['primary_scenario'],pricing['secondary_scenario']),native_responses=len(seen),judges_excluded_from_deployment=True,method='Per-response API threshold; all deployment roles including extraction; frozen observed cache counters under counterfactual rates.',limitations=['Cache-ratio sweep holds observed behavior fixed; it is not measured behavior under different providers or prices.','API values require explicit native zero-write counters, remain scenarios rather than invoices, and do not reproduce API caching.','Unknown monetary local compute and research overhead remain separate.'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve previous sensitivity receipt')
    result=audit(a.directory,REPO/'work/security/workspace/workspace.sqlite',json.loads(PRICING.read_text()));a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
