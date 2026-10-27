"""Paired routing rescue metrics from independent, post-generation grades."""
import math

ARMS = ('small', 'large', 'optional', 'required_review')


def summarize(rows):
    grouped = {}
    for row in rows:
        key, arm = row['task_id'], row['arm']
        if not isinstance(key, str) or not key or arm not in ARMS or type(row['resolved']) is not bool:
            raise ValueError('Invalid independently graded row')
        if arm in grouped.setdefault(key, {}):
            raise ValueError('Duplicate assignment; no best-of selection')
        calls = row['expert_calls']
        attempts = row.get('expert_requests_attempted', calls)
        if type(calls) is not int or calls < 0 or (arm in ('small', 'large') and calls):
            raise ValueError('Invalid expert-call count')
        if type(attempts) is not int or attempts < calls or (arm in ('small','large') and attempts):
            raise ValueError('Invalid attempted expert-request count')
        prior = row.get('pre_handoff_resolved')
        if prior is not None and (type(prior) is not bool or attempts == 0):
            raise ValueError('Pre-handoff grade requires an actual consultation')
        cost = row.get('cost_scenario_usd')
        if cost is not None and (type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0):
            raise ValueError('Invalid model-cost scenario')
        grouped[key][arm] = row
    if not grouped or any(set(group) != set(ARMS) for group in grouped.values()):
        raise ValueError('Require complete matched four-arm blocks')
    blocks = list(grouped.values())
    baseline_failures = sum(not b['small']['resolved'] for b in blocks)
    rescuable = [b for b in blocks if not b['small']['resolved'] and b['large']['resolved']]
    result = {'tasks': len(blocks), 'luna_failures': baseline_failures,
              'luna_fail_sol_succeed': len(rescuable), 'arms': {},
              'scope': 'Paired independent attempts are not identical initial trajectories; pre-handoff grades isolate observed within-run repair, not a randomized causal effect'}
    for arm in ARMS:
        values = [b[arm] for b in blocks]
        costs = [r.get('cost_scenario_usd') for r in values]
        result['arms'][arm] = {
            'resolved': sum(r['resolved'] for r in values),
            'expert_calls': sum(r['expert_calls'] for r in values),
            'expert_requests_attempted': sum(r.get('expert_requests_attempted', r['expert_calls']) for r in values),
            'cost_scenario_usd': sum(costs) if all(c is not None for c in costs) else None,
        }
        if arm in ('optional', 'required_review'):
            assisted = result['arms'][arm]
            recovered = sum(b[arm]['resolved'] for b in rescuable)
            assisted.update({
                'luna_fail_assisted_succeed': sum(not b['small']['resolved'] and b[arm]['resolved'] for b in blocks),
                'luna_succeed_assisted_fail': sum(b['small']['resolved'] and not b[arm]['resolved'] for b in blocks),
                'rescued_sol_rescuable': recovered,
                'rescue_fraction_of_sol_rescuable': recovered/len(rescuable) if rescuable else None,
                'consulted_on_sol_rescuable': sum(b[arm]['expert_calls'] > 0 for b in rescuable),
                'requested_on_sol_rescuable': sum(b[arm].get('expert_requests_attempted',b[arm]['expert_calls']) > 0 for b in rescuable),
                'consulted_missing_pre_handoff_grade': sum(r.get('expert_requests_attempted',r['expert_calls']) > 0 and r.get('pre_handoff_resolved') is None for r in values),
                'pre_handoff_fail_final_pass': sum(r.get('pre_handoff_resolved') is False and r['resolved'] for r in values),
                'pre_handoff_pass_final_fail': sum(r.get('pre_handoff_resolved') is True and not r['resolved'] for r in values),
            })
    result['required_review_noncompliance'] = sum(b['required_review']['expert_calls'] == 0 for b in blocks)
    return result
