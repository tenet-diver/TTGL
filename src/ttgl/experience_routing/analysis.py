"""Paired, failure-inclusive results; fixture results never become model scores."""
from __future__ import annotations
import math
import random
import statistics
from .io import read


def paired(records,control='LPM',candidate='HRM',seed=0,bootstrap=2000):
    indexed={}
    for row in records:
        key=(row['task_id'],row['arm'])
        if key in indexed:raise ValueError('Repeated attempts require an explicit separate repetition identity')
        indexed[key]=row
    tasks=sorted({t for t,a in indexed if a==control}&{t for t,a in indexed if a==candidate})
    if not tasks:return {'matched_tasks':0,'target90_met':False,'reason':'No paired independent grades'}
    pairs=[(indexed[t,control],indexed[t,candidate]) for t in tasks]
    valid=[(a,b) for a,b in pairs if a.get('grade_valid') is True and b.get('grade_valid') is True]
    successes=[sum(bool(r.get('passed')) for r in arm) for arm in zip(*valid)] if valid else [0,0]
    lost=[a['task_id'] for a,b in valid if a.get('passed') and not b.get('passed')]
    gained=[a['task_id'] for a,b in valid if b.get('passed') and not a.get('passed')]
    complete_cost=all(r.get('scenario_cost') is not None for pair in pairs for r in pair)
    costs=[sum(r['scenario_cost'] for r in arm) for arm in zip(*pairs)] if complete_cost else [None,None]
    saving=1-costs[1]/costs[0] if complete_cost and costs[0]>0 else None
    retention=successes[1]/successes[0] if successes[0] else None
    difference=(successes[1]-successes[0])/len(valid) if valid else None
    groups={}
    for a,b in valid:groups.setdefault(a.get('repository',a['task_id']),[]).append(int(bool(b.get('passed')))-int(bool(a.get('passed'))))
    rng=random.Random(seed);keys=sorted(groups);samples=[]
    if keys:
        for _ in range(bootstrap):
            values=[v for _ in keys for v in groups[rng.choice(keys)]];samples.append(sum(values)/len(values))
        samples.sort()
    interval=[samples[int(.025*(len(samples)-1))],samples[int(.975*(len(samples)-1))]] if samples else None
    fixture=any(r.get('fixture_only') for pair in pairs for r in pair)
    return {'matched_tasks':len(tasks),'valid_evaluation_pairs':len(valid),'invalid_or_unresolved_pairs':len(tasks)-len(valid),
        'control_successes':successes[0],'candidate_successes':successes[1],'success_difference':difference,
        'relative_retention':retention,'paired_losses':lost,'paired_gains':gained,'scenario_costs':{control:costs[0],candidate:costs[1]},
        'scenario_saving':saving,'quality_interval':interval,'interval_method':'repository-cluster paired percentile bootstrap; exploratory with few clusters',
        'fixture_only':fixture,'target90_met':False if fixture else saving is not None and saving>=.9 and successes[0]>0 and not lost and len(valid)==len(tasks) and successes[1]>=successes[0],
        'cash_saving':None,'population_noninferiority_established':False}


def annotation_audit(rows):
    adjudicated=[r for r in rows if r.get('reference') in ('successful','unsuccessful')]
    positive=[r for r in adjudicated if r.get('prediction')=='successful']
    true=sum(r['reference']=='successful' for r in positive);false=len(positive)-true
    actual_positive=sum(r['reference']=='successful' for r in adjudicated)
    actual_negative=len(adjudicated)-actual_positive
    def wilson(k,n):
        if not n:return None
        z=1.959963984540054;den=1+z*z/n;mid=(k/n+z*z/(2*n))/den
        half=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/den
        return [max(0,mid-half),min(1,mid+half)]
    support=[r for r in rows if r.get('support_correct') is not None]
    return {'rows':len(rows),'adjudicated':len(adjudicated),'unresolved':len(rows)-len(adjudicated),
        'precision':true/len(positive) if positive else None,'recall':true/actual_positive if actual_positive else None,
        'false_success_rate':false/len(positive) if positive else None,'false_success_interval':wilson(false,len(positive)),
        'false_positive_rate':false/actual_negative if actual_negative else None,
        'abstentions':sum(r.get('prediction')=='abstain' for r in rows),'support_link_precision':sum(r['support_correct'] for r in support)/len(support) if support else None,
        'reference_kinds':sorted({r.get('reference_kind','unrecorded') for r in rows}),'source_reference_validity':all(r.get('source_valid') is True for r in rows)}


def learning_curves(rows):
    output=[];counts={};successes={};lineages={}
    for r in sorted(rows,key=lambda x:(x['order'],x['arm'],x['sequence'])):
        key=(r['order'],r['arm']);lineage=r['memory_lineage']
        if key in lineages and lineages[key]!=lineage:raise ValueError('Online order changed memory lineage')
        lineages[key]=lineage;fkey=(*key,r['family']);prior=counts.get(fkey,0)
        output.append({**r,'prior_family_exposures':prior,'prior_successful_small_reuses':successes.get(fkey,0),
                       'familiarity':'novel' if prior==0 else 'recurrent','descriptive_only':True})
        counts[fkey]=prior+1
        if r.get('small_integrated_success'):successes[fkey]=successes.get(fkey,0)+1
    return output
