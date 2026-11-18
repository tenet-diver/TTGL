"""Disjoint native development fitting/selection; never consumes heldout rows.

Run in the reviewed numerical child environment. Released method adaptations,
sufficiency failures and infeasible operating points stay explicit.
"""
import time
from .released_baselines import load_cores,make_routellm,train_quality,select_cascades
from ..experience_routing.io import digest


def select_routes(pairs,scores,budgets):
    candidates=[]
    for threshold in [i/20 for i in range(21)]:
        chosen=[p['sol'] if scores[p['task_id']]>=threshold else p['luna'] for p in pairs]
        candidates.append({'threshold':threshold,'resolved':sum(r['resolved'] for r in chosen),
            'tasks':len(chosen),'mean_scenario_cost':sum(r['scenario_cost'] for r in chosen)/len(chosen)})
    return {name:min((c for c in candidates if c['mean_scenario_cost']<=budget),
        key=lambda c:(-c['resolved'],c['mean_scenario_cost'],c['threshold']),default=None)
            for name,budget in budgets.items()},candidates


def calibrate(config):
    if config.get('partition')!='development' or set(config['evaluation_ids']) & {r['task_id'] for r in config['records']}:
        raise ValueError('Disjoint development only')
    records=config['records'];models=('gpt-6-luna','gpt-6.1-sol')
    by_task={}
    for record in records:
        if record['model'] not in models or type(record.get('resolved')) is not bool or record.get('scenario_cost') is None:
            raise ValueError('Native known outcome/cost/pair required')
        group=by_task.setdefault(record['task_id'],{})
        if record['model'] in group:raise ValueError('Duplicate native development candidate')
        group[record['model']]=record
    if any(set(rows)!=set(models) for rows in by_task.values()):raise ValueError('Complete native pairs required')
    counts={model:{str(label):sum(r['resolved']==label for r in records if r['model']==model) for label in (False,True)} for model in models}
    # Mixed outcomes need two examples of each class for task-OOF fitting.
    # A genuinely single-class sample uses an explicitly labelled empirical
    # prior. This is a feasibility floor, not statistical adequacy established.
    if len(by_task)<6 or any(0<min(c.values())<2 for c in counts.values()):
        return {'sufficiency_passed':False,'reason':'Insufficient native outcome classes for honest task-disjoint scorer fitting',
                'class_counts':counts,'training_tasks':len(by_task),'heldout_used':False,'points':None}
    started=time.process_time();wall=time.monotonic();cores=load_cores(config['pins'])
    pair_rows=[]
    for task,rows in by_task.items():
        luna,sol=rows[models[0]],rows[models[1]]
        if luna['public_input']!=sol['public_input']:raise ValueError('Matched public input/knowledge required')
        pair_rows.append({'task_id':task,'public_input':luna['public_input'],
            'luna_resolved':luna['resolved'],'sol_resolved':sol['resolved'],'luna':luna,'sol':sol})
    quality_scores={};route_scores={}
    for pair in pair_rows:
        task=pair['task_id'];train=[r for r in records if r['task_id']!=task]
        scorers,_=train_quality(cores,train)
        quality_scores[task]={model:scorers[model].get_score(cores[1]['scorer_text'](pair['public_input']+' '+pair['luna' if model==models[0] else 'sol']['candidate_text'])) for model in models}
        router=make_routellm(cores,[p for p in pair_rows if p['task_id']!=task])
        route_scores[task]=float(router.calculate_strong_win_rate(pair['public_input']))
    briers={}
    for model in models:
        rows=[r for r in records if r['model']==model]
        learned=sum((quality_scores[r['task_id']][model]-r['resolved'])**2 for r in rows)/len(rows)
        constant=sum(((sum(s['resolved'] for s in rows if s['task_id']!=r['task_id'])/(len(rows)-1))-r['resolved'])**2 for r in rows)/len(rows)
        briers[model]={'oof_brier':learned,'oof_constant_prior_brier':constant}
    sufficient=all(s['oof_brier']<=s['oof_constant_prior_brier']+.02 for s in briers.values())
    sol_mean=sum(r['scenario_cost'] for r in records if r['model']==models[1])/len(by_task)
    budgets={name:sol_mean*ratio for name,ratio in config['cost_budget_fractions'].items()}
    cascade=select_cascades(records,quality_scores,budgets=budgets)
    routes,grid=select_routes(pair_rows,route_scores,budgets)
    _,statistics=train_quality(cores,records)
    parameters={'pins':config['pins'],'records':records,'pairs':[{k:p[k] for k in ('task_id','public_input','luna_resolved','sol_resolved')} for p in pair_rows]}
    return {'sufficiency_passed':sufficient,'reason':None if sufficient else 'Out-of-fold learned scorer exceeds frozen constant-prior Brier tolerance',
        'training_tasks':len(by_task),'class_counts':counts,'scorer_statistics':statistics,'brier':briers,
        'routellm_points':routes,'routellm_grid':grid,'frugalgpt_selection':cascade,'budget_scenarios':budgets,
        'cross_validation':'leave-one-task-out; fitted once more on all development only',
        'parameters':parameters,'parameters_sha256':digest(parameters),'heldout_used':False,
        'local_setup_cpu_seconds':time.process_time()-started,'local_setup_wall_seconds':time.monotonic()-wall,
        'adaptation':'released methods, local hashing/linear scorer and exhaustive two-model optimizer; not original pretrained checkpoints'}
