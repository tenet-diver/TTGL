"""Freeze compatibility-qualified partitions before construction inference."""
from .accumulation import validate_partitions
from ..experience_routing.io import digest


def qualified_split(reservation,preparation,rules):
    original=[t for tasks in reservation['partitions'].values() for t in tasks]+reservation['spares_before_any_assignment']
    expected=[t['task_id'] for t in original]
    rows=preparation['results']
    if len({r['task_id'] for r in rows})!=len(rows) or set(expected)!={r['task_id'] for r in rows}:
        raise ValueError('Every reserved metadata control must reconcile exactly once')
    if preparation.get('native_model_calls')!=0:raise ValueError('Eligibility must precede model use')
    qualified={r['task_id']:r for r in rows if r['eligible']}
    tasks=[{**t,'control_result':qualified[t['task_id']]} for t in original if t['task_id'] in qualified]
    n=len(tasks)
    if n<rules['minimum_viable_eligible_tasks']:
        return {'execution_ready':False,'eligible_count':n,'reason':'Insufficient compatibility-qualified sources',
                'main_model_calls':0,'full_comparison_complete':False}
    allocation=next((a for a in rules['allocation'] if n>=a['eligible_count_at_least'] and
                     ('eligible_count_below' not in a or n<a['eligible_count_below'])),None)
    if allocation is None:raise ValueError('No frozen compatibility allocation rule')
    c,d=allocation['construction'],allocation['development']
    if type(allocation['heldout']) is int:h=allocation['heldout']
    elif allocation['heldout']==f'eligible_count minus{c+d}':h=n-c-d
    else:raise ValueError('Unknown frozen allocation expression')
    partitions={'construction':tasks[:c],'development':tasks[c:c+d],'heldout':tasks[c+d:c+d+h]}
    fingerprint=validate_partitions(partitions)
    prefixes=allocation['prefixes']
    if max(prefixes)!=c:raise ValueError('Knowledge prefixes must cover the frozen construction set')
    body={'execution_ready':False,'allow_model_execution':False,'partitions':partitions,'partition_hash':fingerprint,
          'eligible_count':n,'rules_hash':digest(rules),'preparation_hash':digest(preparation),
          'excluded':[{'task_id':r['task_id'],'reason':r.get('reason','control_failure')} for r in rows if not r['eligible']],
          'unused_development_reserve':tasks[c+d+h:],'prefixes':prefixes,'heldout_assignments_expected':h*(3*len(prefixes)+8),
          'split_basis':'Original metadata order filtered only by frozen environment controls; no main model outcomes',
          'scope':'SymPy compatibility-qualified subset; prescribed evaluator adaptation',
          'main_model_calls':0,'further_requirements':'Separate finite source-bound construction/development and full heldout registrations'}
    return {**body,'split_id':digest(body)}
