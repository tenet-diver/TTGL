#!/usr/bin/env python3
"""Response-level cache-aware inference cost audit; never a subscription invoice."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sqlite3

REPO=Path(__file__).resolve().parents[3]
PRICING=REPO/'tools/usage-monitor/studies/context-memory-pricing-20261107.json'


def price(usage,rates):
    required=('input_tokens','cached_input_tokens','output_tokens')
    if any(type(usage.get(k)) is not int or usage[k]<0 for k in required):
        raise ValueError('Missing/invalid usage; unknown cost must not become zero')
    if usage['cached_input_tokens']>usage['input_tokens']:raise ValueError('Cache subset exceeds input')
    return ((usage['input_tokens']-usage['cached_input_tokens'])*rates['fresh_input_per_million']+
            usage['cached_input_tokens']*rates['cached_input_per_million']+
            usage['output_tokens']*rates['output_per_million'])/1e6


def audit(directory,database,pricing):
    result=json.loads((directory/'results.json').read_text());rates=pricing['primary_scenario'];api=pricing['secondary_scenario']
    cells=[]
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as db:
        for cell in result['cells']:
            records=[]
            for ident in cell['native_response_ids']:
                row=db.execute('SELECT usage FROM events WHERE id=? AND kind=?',(ident,'generation')).fetchone()
                if row is None:raise ValueError('Native response missing')
                u=json.loads(row[0]);cost=price(u,rates)
                api_cost=None
                # Do not assume missing write counters mean no writes, or assign
                # API write categories to Codex usage when their partition is unknown.
                if u.get('cache_write_input_tokens')==0:
                    adjusted=dict(api)
                    long=u['input_tokens']>api['long_context_threshold_input_tokens']
                    if long:
                        adjusted['fresh_input_per_million']*=api['long_context_input_multiplier']
                        adjusted['cached_input_per_million']*=api['long_context_input_multiplier']
                        adjusted['output_per_million']*=api['long_context_output_multiplier']
                    api_cost=price(u,adjusted)
                records.append(dict(id=ident,usage=u,credit_rate_scenario=cost,api_rate_sensitivity_usd=api_cost))
            if len({r['id'] for r in records})!=len(records):raise ValueError('Duplicate response')
            observed={k:sum(r['usage'].get(k,0) for r in records) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')}
            if observed!=cell['usage']:raise ValueError('Native totals changed or mismatch')
            cells.append(dict(case=cell.get('case',cell.get('sequence')),stage=cell.get('stage'),condition=cell['condition'],
                usage=observed,responses=records,credit_rate_scenario=sum(r['credit_rate_scenario'] for r in records),
                api_rate_sensitivity_usd=sum(r['api_rate_sensitivity_usd'] for r in records) if all(r['api_rate_sensitivity_usd'] is not None for r in records) else None))
    baseline='baseline' if any(c['condition']=='baseline' for c in cells) else 'none'
    totals={}
    for arm in sorted({c['condition'] for c in cells}):
        selected=[c for c in cells if c['condition']==arm]
        u={k:sum(c['usage'][k] for c in selected) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')}
        u['fresh_input_tokens']=u['input_tokens']-u['cached_input_tokens']
        totals[arm]=dict(usage=u,cache_hit_fraction=u['cached_input_tokens']/u['input_tokens'],
            credit_rate_scenario=sum(c['credit_rate_scenario'] for c in selected),
            api_rate_sensitivity_usd=sum(c['api_rate_sensitivity_usd'] for c in selected) if all(c['api_rate_sensitivity_usd'] is not None for c in selected) else None)
    for arm,total in totals.items():
        total['cost_reduction_fraction']=1-total['credit_rate_scenario']/totals[baseline]['credit_rate_scenario']
        total['token_reduction_fraction']=1-total['usage']['total_tokens']/totals[baseline]['usage']['total_tokens']
        delta={k:total['usage'][k]-totals[baseline]['usage'][k] for k in ('fresh_input_tokens','cached_input_tokens','output_tokens')}
        output_ratio=rates['output_per_million']/rates['fresh_input_per_million']
        total['cache_to_fresh_break_even_ratio']=-(delta['fresh_input_tokens']+output_ratio*delta['output_tokens'])/delta['cached_input_tokens'] if delta['cached_input_tokens'] else None
        total['sensitivity']={str(ratio):price(total['usage'],dict(fresh_input_per_million=1,cached_input_per_million=ratio,output_per_million=output_ratio)) for ratio in (0,.01,.05,.1,.25,1)}
    return dict(id=pricing['id'],at=datetime.now(timezone.utc).isoformat(),study=result.get('protocol'),
        pricing=pricing,cells=cells,totals=totals,baseline=baseline,
        primary='Total quality-constrained published Codex credit-rate scenario; fresh/cached/output per actual response, not raw token count.',
        design_status='Post-hoc cost audit of completed development evidence; does not rewrite the frozen token gate.',
        cash_expense=None,actual_account_credit_consumption=None,quota_saving=None,
        limitation='Deployment cost and local embedding compute are not monetized. API sensitivity uses observed native zero-write reports and is not a recreation of API cache behavior. Subsequent memory trials must add all extraction/ranking inference before comparing total system cost.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--database',type=Path,default=REPO/'work/security/workspace/workspace.sqlite');args=p.parse_args()
    if args.output.exists():raise ValueError('Preserve prior cost receipt')
    result=audit(args.directory,args.database,json.loads(PRICING.read_text()));args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['totals'],indent=2))
