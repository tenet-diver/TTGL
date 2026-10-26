import pytest
from ttgl.frontier import compare, added_value


def rows(p=(True, True), r=(True, True), pc=.04, rc=1.):
    return [dict(task_id=str(i), arm=a, resolved=v, cost_usd=c)
            for i in range(len(p)) for a,v,c in [('small',p[i],pc),('large',r[i],rc)]]


def test_relative_retention_and_total_cost_both_required():
    result = compare(rows(), policy='small')
    assert result['joint_95_95_point_target_met'] is True
    assert result['model_cost_reduction_fraction'] == .96
    assert result['reference_success_retention_one_sided_95_exact_lower_bound'] < .95
    loss = compare(rows((True, False)), policy='small')
    assert loss['accuracy_retention_ratio'] == .5
    assert loss['reference_successes_lost'] == 1
    assert loss['joint_95_95_point_target_met'] is False
    expensive = compare(rows(pc=.06), policy='small')
    assert expensive['joint_95_95_point_target_met'] is False


def test_perfect_tiny_panels_do_not_establish_tight_retention():
    twelve = compare(rows(p=(True,)*12, r=(True,)*12), policy='small')
    assert twelve['reference_success_retention_one_sided_95_exact_lower_bound'] < .8
    fifty_nine = compare(rows(p=(True,)*59, r=(True,)*59), policy='small')
    assert fifty_nine['reference_success_retention_one_sided_95_exact_lower_bound'] > .95


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


def test_gap_closure_distinguishes_cheap_baseline_from_strong_reference():
    records=[]
    for i in range(3):
        for arm,outcomes,cost in [('small',[True,False,False],.01),
                                  ('personal',[True,True,False],.03),
                                  ('large',[True,True,True],.2)]:
            records.append(dict(task_id=str(i),arm=arm,resolved=outcomes[i],cost_usd=cost))
    result=added_value(records,policy='personal')
    assert result['additional_resolved_vs_cheap']==1
    assert result['fraction_of_positive_strong_cheap_gap_closed']==.5
    assert result['extra_model_cost_scenario_usd_vs_cheap']==pytest.approx(.06)


def test_gap_closure_is_unknown_when_cheap_control_already_matches_strong():
    records=rows()+[dict(task_id=str(i),arm='personal',resolved=True,cost_usd=None) for i in range(2)]
    result=added_value(records,policy='personal')
    assert result['fraction_of_positive_strong_cheap_gap_closed'] is None
    assert result['incremental_scenario_usd_per_additional_resolved'] is None
