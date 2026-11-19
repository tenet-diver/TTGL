"""Receipt-based quality/cost summaries with explicit unknowns and paired bounds."""
from pathlib import Path
import math
import random
from .accounting import reconcile
from .campaign import scenario_cost
from ..experience_routing.io import read


def assignment_rows(campaign,grades,generation,rates,*,cpu_usd_per_core_hour):
    by_id = {g['assignment_id']: g for g in grades}
    rows = {}
    for assignment in campaign['assignments']:
        ident=assignment['assignment_id'];folder=Path(generation)/ident
        result=read(folder/'completion.json');grade=by_id[ident]
        row={**assignment,**grade,'native_token_scenario_usd':None,'local_model_cpu_scenario_usd':None,
             'total_model_scenario_usd':None,'actual_cash':None}
        rows[ident] = row
        if result['status'] == 'unrun_infeasible':
            continue
        if result['status'] == 'native_timeout':
            row['accounting_gap'] = 'Native deadline reached with incomplete inference usage'
            continue
        if result['status'] == 'duplicate_policy':
            reference = result['shared_assignment_id']
            original = rows[reference]
            if grade['shared_assignment_id'] != reference or any(
                grade[field] != original[field] for field in ('official_resolved', 'protocol_resolved')
            ):
                raise ValueError('Duplicate point does not match its independent source grade')
            rows[ident] = {**original, **assignment, **grade, 'native_invocations': 0,
                           'reference_native_invocations': original.get('native_invocations')}
            continue
        paths=list(folder.rglob('usage-ledger.jsonl'))
        if not paths:
            row['accounting_gap'] = 'No native receipts; do not infer zero inference'
            continue
        accounted=reconcile(paths)
        expected=result['usage']['maximum_invocations']
        if accounted['native_receipts']!=expected or accounted['issues']:
            row['accounting_gap']=accounted['issues'] or ['Native invocation count differs']
            continue
        costs=[scenario_cost(usage,rates[model]) for model,usage in accounted['models'].items()]
        operations=result.get('local_scorer_operations')
        if operations is None:
            row['accounting_gap'] = 'Local-model accounting absent'
            continue
        seconds=sum(op['cpu_seconds'] for op in operations)
        if not math.isfinite(seconds) or seconds<0:raise ValueError('Invalid finite local model CPU runtime')
        row['local_model_cpu_seconds']=seconds
        row['local_model_cpu_scenario_usd']=seconds*cpu_usd_per_core_hour/3600
        row['native_usage']=accounted['native_usage'];row['native_invocations']=accounted['native_receipts']
        if all(c is not None for c in costs):
            row['native_token_scenario_usd']=sum(costs)
            row['total_model_scenario_usd']=sum(costs)+row['local_model_cpu_scenario_usd']
        row['agent_and_public_check_envelope_seconds']=result['usage']['maximum_elapsed_seconds']
    return list(rows.values())


def groups(rows):
    grouped={}
    for row in rows:
        key=(row['system'],row['snapshot_id'],row['point'])
        grouped.setdefault(key,[]).append(row)
    result=[]
    for (system,snapshot,point),items in grouped.items():
        known=[r for r in items if type(r['protocol_resolved']) is bool]
        success=sum(r['protocol_resolved'] for r in known);unknown=len(items)-len(known)
        costs=[r.get('total_model_scenario_usd') for r in items]
        usage_unknown = sum(
            ('native_invocations' not in r and r['status'] != 'unrun_infeasible')
            or (r['status'] == 'duplicate_policy' and r['reference_native_invocations'] is None)
            for r in items
        )
        result.append({'system':system,'snapshot_id':snapshot,'point':point,'registered_tasks':len(items),
            'protocol_successes_known':success,'quality_unknown':unknown,
            'protocol_accuracy':success/len(items) if not unknown else None,
            'protocol_accuracy_bounds':[success/len(items),(success+unknown)/len(items)],
            'official_successes_known':sum(r['official_resolved'] is True for r in items),
            'official_unknown':sum(r['official_resolved'] is None for r in items),
            'mean_model_scenario_usd':sum(costs)/len(costs) if all(c is not None for c in costs) else None,
            'usage_unknown_tasks':usage_unknown,
            'shared_policy_tasks':sum(r['status'] == 'duplicate_policy' for r in items),
            'native_invocations':None if usage_unknown else sum(r.get('native_invocations',0) for r in items),
            'actual_cash':None})
    return result


def paired_target(candidate,control,*,seed=18112026,resamples=10000):
    a={r['task_id']:r for r in candidate};b={r['task_id']:r for r in control}
    if not a or set(a)!=set(b):raise ValueError('Identical nonempty matched task set required')
    items=[(a[t],b[t]) for t in sorted(a)]
    fields=('protocol_resolved','total_model_scenario_usd')
    if any(r.get(k) is None for pair in items for r in pair for k in fields):
        return {'evaluable':False,'reason':'Unknown matched quality or full model-inference scenario','target_met':None}
    def measures(sample):
        ca=sum(x['total_model_scenario_usd'] for x,y in sample);cb=sum(y['total_model_scenario_usd'] for x,y in sample)
        qa=sum(x['protocol_resolved'] for x,y in sample);qb=sum(y['protocol_resolved'] for x,y in sample)
        return (1-ca/cb if cb>0 else None,(qa-qb)/len(sample),qa/qb if qb>0 else None)
    saving,difference,retention=measures(items)
    if retention is None or saving is None:
        return {'evaluable':False,'reason':'Zero matched Sol success or inference-cost denominator','target_met':None,
                'observed_quality_difference':difference,'observed_scenario_saving':saving}
    rng=random.Random(seed);samples=[measures([items[rng.randrange(len(items))] for _ in items]) for _ in range(resamples)]
    def interval(index):
        values=sorted(s[index] for s in samples if s[index] is not None)
        if not values:return None
        return [values[int(.025*(len(values)-1))],values[int(.975*(len(values)-1))]]
    return {'evaluable':True,'matched_tasks':len(items),'observed_scenario_saving':saving,
        'observed_quality_difference':difference,'relative_quality_retention':retention,
        'target_met':saving>=.90 and difference>=0,
        'task_bootstrap_95_percent':{'saving':interval(0),'quality_difference':interval(1),'relative_retention':interval(2)},
        'uncertainty_scope':'Task-cluster resampling of one registered attempt per cell; conditional on this compatibility subset and model aliases, not inference-repeat or population noninferiority proof',
        'actual_cash_saving':None}


def baseline_mixture_envelope(points,cost):
    """Expected convex mixtures of measured baseline points, not new trials."""
    valid=[p for p in points if p.get('mean_model_scenario_usd') is not None and p.get('protocol_accuracy') is not None]
    values=[p['protocol_accuracy'] for p in valid if p['mean_model_scenario_usd']<=cost]
    for left in valid:
        for right in valid:
            low,high=left['mean_model_scenario_usd'],right['mean_model_scenario_usd']
            if low<high and low<=cost<=high:
                w=(cost-low)/(high-low)
                values.append((1-w)*left['protocol_accuracy']+w*right['protocol_accuracy'])
    return max(values) if values else None
