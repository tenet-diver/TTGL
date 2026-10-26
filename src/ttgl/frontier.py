"""Paired quality/cost evidence for a declared relative-retention target."""
import math
import numpy as np


def compare(records, *, policy, reference='large', seed=1729, samples=10000):
    selected = [row for row in records if row['arm'] in (policy, reference)]
    index = {}
    for row in selected:
        key = row['task_id'], row['arm']
        if key in index:
            raise ValueError('Duplicate task/condition result')
        if type(row.get('resolved')) is not bool:
            raise ValueError('Every assigned outcome must have an independent grade')
        cost = row.get('cost_usd')
        if cost is not None and (type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0):
            raise ValueError('Invalid model cost')
        index[key] = row
    tasks = sorted({key[0] for key in index})
    if not tasks or any((task, arm) not in index for task in tasks for arm in (policy, reference)):
        raise ValueError('A complete matched task set is required')
    p = np.array([index[t, policy]['resolved'] for t in tasks], dtype=float)
    r = np.array([index[t, reference]['resolved'] for t in tasks], dtype=float)
    cost_complete = all(index[t, a].get('cost_usd') is not None for t in tasks for a in (policy, reference))
    pc = np.array([index[t, policy]['cost_usd'] for t in tasks], dtype=float) if cost_complete else None
    rc = np.array([index[t, reference]['cost_usd'] for t in tasks], dtype=float) if cost_complete else None
    quality_ratio = float(p.sum()/r.sum()) if r.sum() > 0 else None
    cost_ratio = float(pc.sum()/rc.sum()) if cost_complete and rc.sum() > 0 else None
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(tasks), size=(samples, len(tasks)))
    boot_r = r[draw].sum(axis=1)
    quality_ci = (np.quantile(p[draw].sum(axis=1)/boot_r, [.025, .975]).tolist()
                  if np.all(boot_r > 0) else None)
    cost_ci = None
    if cost_complete:
        boot_rc = rc[draw].sum(axis=1)
        if np.all(boot_rc > 0):
            cost_ci = np.quantile(pc[draw].sum(axis=1)/boot_rc, [.025, .975]).tolist()
    joint = quality_ratio >= .95 and cost_ratio <= .05 if quality_ratio is not None and cost_ratio is not None else None
    return {'policy': policy, 'reference': reference, 'paired_tasks': len(tasks),
        'policy_resolved': int(p.sum()), 'reference_resolved': int(r.sum()),
        'reference_successes_lost': int(((r == 1) & (p == 0)).sum()),
        'reference_failures_rescued': int(((r == 0) & (p == 1)).sum()),
        'accuracy_retention_ratio': quality_ratio, 'cost_ratio': cost_ratio,
        'model_cost_reduction_fraction': 1-cost_ratio if cost_ratio is not None else None,
        'accuracy_difference_points': float(100*(p.mean()-r.mean())),
        'accuracy_retention_paired_bootstrap_95_interval': quality_ci,
        'cost_ratio_paired_bootstrap_95_interval': cost_ci,
        'joint_95_95_point_target_met': joint,
        'bootstrap_intervals_within_target': bool(quality_ci[0] >= .95 and cost_ci[1] <= .05)
            if quality_ci is not None and cost_ci is not None else None,
        'bootstrap': {'samples': samples, 'seed': seed, 'unit': 'paired task',
                      'method': 'percentile; interval unavailable if any bootstrap reference denominator is zero'},
        'limitations': ['Small samples and ceiling outcomes can produce degenerate bootstrap intervals; these do not prove population noninferiority.',
                        'Cost inherits the input accounting definition; published token-rate scenarios are not observed bills.',
                        'Development-set policy selection invalidates a held-out interpretation of the same cases.']}
