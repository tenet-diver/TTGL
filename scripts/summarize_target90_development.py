#!/usr/bin/env python3
"""Development progress only: never declare the held-out target achieved."""
import argparse
from decimal import Decimal
import json
import hashlib
from pathlib import Path


def summarize(plan,pairs):
    expected={t['task_id'] for t in plan['tasks']}
    observed=[p['task_id'] for p in pairs]
    if len(set(observed))!=len(observed) or not set(observed)<=expected:
        raise ValueError('Duplicate or unregistered development task')
    if any(p['status']!='audited_development_pair_not_final_target_evidence' for p in pairs):
        raise ValueError('Use audited complete pairs only')
    quality={a:sum(p['arms'][a]['resolved'] for p in pairs) for a in ['large','optional']}
    costs={}
    for arm in ['large','optional']:
        values=[p['arms'][arm]['cost_scenario_usd'] for p in pairs]
        costs[arm]=sum((Decimal(str(c)) for c in values),Decimal(0)) if all(c is not None for c in values) else None
    ratio=(costs['optional']/costs['large'] if costs['large'] is not None and costs['large']>0
           and costs['optional'] is not None else None)
    complete=set(observed)==expected
    identities={json.dumps(p['policy_identity'],sort_keys=True) for p in pairs}
    fixed=len(identities)==1
    gate=(bool(fixed and ratio is not None and ratio<=Decimal('0.10') and quality['large']>0
               and quality['optional']>=quality['large']) if complete else None)
    count=len(pairs)
    return {'status':'development_progress_not_held_out_target_proof',
            'planned_tasks':len(expected),'completed_pairs':count,'all_registered_pairs_complete':complete,
            'fixed_policy_across_completed_pairs':fixed,
            'quality':{'sol_resolved':quality['large'],'router_resolved':quality['optional'],
                'assigned_per_arm':count,'resolved_delta':quality['optional']-quality['large'],
                'sol_successes_lost':sum(p['comparison']['sol_success_lost'] for p in pairs),
                'router_extra_successes':sum(p['comparison']['router_extra_success'] for p in pairs)},
            'cost_scope':'Audited completed pairs only; unfinished assignments are not zero cost and cannot pass the full-panel gate',
            'cost_scenario_usd':{a:float(c) if c is not None else None for a,c in costs.items()},
            'cost_per_assigned_usd':{a:float(c/count) if c is not None and count else None for a,c in costs.items()},
            'cost_per_resolved_usd':{a:float(c/quality[a]) if c is not None and quality[a] else None for a,c in costs.items()},
            'aggregate_model_cost_ratio':float(ratio) if ratio is not None else None,
            'aggregate_scenario_saving':float(1-ratio) if ratio is not None else None,
            'development_point_gate':gate,'held_out_target_achieved':False,
            'actual_cash_saving':None,'subscription_quota_saving':None,
            'uncertainty':'Selected development tasks; no population equivalence, final-policy causal improvement or held-out90% proof',
            'tasks':observed}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--results',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    pairs=[]
    for path in sorted(args.results.glob('*-analysis-*/summary.json')):
        manifest=json.loads((path.parent/'artifact-manifest.json').read_text())
        if manifest['files'].get('summary.json')!=hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError('Pair summary differs from sealed analysis export')
        pairs.append(json.loads(path.read_text()))
    result=summarize(json.loads(args.plan.read_text()),pairs)
    unfinished=[]
    complete={p['task_id'] for p in pairs}
    for unit in sorted(args.results.glob('*-pair-*')):
        if not unit.is_dir():continue
        protocol_path=args.plan.parent/(unit.name+'.json')
        protocol=json.loads(protocol_path.read_text())
        for arm in ['large','optional']:
            if (unit/('first-block-'+arm+'-invocation.json')).exists() and protocol['task_id'] not in complete:
                unfinished.append({'task_id':protocol['task_id'],'arm':arm,
                    'audited_total_cost':None,'status':'invoked_but_complete_pair_not_yet_audited'})
    result['unfinished_invoked_assignments']=unfinished
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['completed_pairs','aggregate_scenario_saving','development_point_gate','held_out_target_achieved']}))


if __name__=='__main__':main()
