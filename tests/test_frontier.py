import pytest
from ttgl.frontier import compare


def rows(p=(True, True), r=(True, True), pc=.04, rc=1.):
    return [dict(task_id=str(i), arm=a, resolved=v, cost_usd=c)
            for i in range(len(p)) for a,v,c in [('small',p[i],pc),('large',r[i],rc)]]


def test_relative_retention_and_total_cost_both_required():
    result = compare(rows(), policy='small')
    assert result['joint_95_95_point_target_met'] is True
    assert result['model_cost_reduction_fraction'] == .96
    loss = compare(rows((True, False)), policy='small')
    assert loss['accuracy_retention_ratio'] == .5
    assert loss['reference_successes_lost'] == 1
    assert loss['joint_95_95_point_target_met'] is False
    expensive = compare(rows(pc=.06), policy='small')
    assert expensive['joint_95_95_point_target_met'] is False


def test_missing_cost_and_zero_denominators_remain_unknown():
    result = compare(rows(pc=None), policy='small')
    assert result['cost_ratio'] is None
    assert result['joint_95_95_point_target_met'] is None
    result = compare(rows(r=(False,False), rc=0), policy='small')
    assert result['accuracy_retention_ratio'] is None
    assert result['cost_ratio'] is None


def test_unmatched_or_duplicate_or_ungraded_results_are_rejected():
    with pytest.raises(ValueError, match='matched'):
        compare(rows()[:-1], policy='small')
    with pytest.raises(ValueError, match='Duplicate'):
        compare(rows()+rows(), policy='small')
    with pytest.raises(ValueError, match='grade'):
        compare(rows(p=(None,True)), policy='small')
