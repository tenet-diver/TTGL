import pytest

from ttgl.handoff_metrics import ARMS, summarize


def block(task, successes, calls=None, prior=None):
    return [{'task_id': task, 'arm': arm, 'resolved': arm in successes,
             'expert_calls': (calls or {}).get(arm, 0),
             'pre_handoff_resolved': (prior or {}).get(arm), 'cost_scenario_usd': None}
            for arm in ARMS]


def test_rescue_and_regression_are_separate_and_missing_evidence_stays_unknown():
    rows = block('miss', {'large', 'required_review'}, {'required_review': 1}, {'required_review': False})
    rows += block('regression', {'small', 'large', 'optional'}, {'optional': 1, 'required_review': 1},
                  {'optional': True, 'required_review': True})
    result = summarize(rows)
    assert result['luna_fail_sol_succeed'] == 1
    assert result['arms']['optional']['rescue_fraction_of_sol_rescuable'] == 0
    review = result['arms']['required_review']
    assert review['rescue_fraction_of_sol_rescuable'] == 1
    assert review['pre_handoff_fail_final_pass'] == 1
    assert review['pre_handoff_pass_final_fail'] == 1
    assert review['luna_succeed_assisted_fail'] == 1
    assert review['cost_scenario_usd'] is None


def test_no_rescuable_cases_is_not_perfect_recall_and_noncompliance_is_retained():
    result = summarize(block('already-correct', set(ARMS)))
    assert result['arms']['optional']['rescue_fraction_of_sol_rescuable'] is None
    assert result['required_review_noncompliance'] == 1


def test_consultation_without_snapshot_is_not_reported_as_verified_recovery():
    result = summarize(block('miss', {'large', 'optional'}, {'optional': 1, 'required_review': 1}))
    assert result['arms']['optional']['consulted_missing_pre_handoff_grade'] == 1
    assert result['arms']['optional']['pre_handoff_fail_final_pass'] == 0


@pytest.mark.parametrize('kind', ['duplicate', 'missing', 'invented-prior'])
def test_invalid_or_selected_assignments_are_rejected(kind):
    rows = block('task', set(ARMS))
    if kind == 'duplicate':
        rows.append(rows[0])
    elif kind == 'missing':
        rows.pop()
    else:
        rows[0]['pre_handoff_resolved'] = False
    with pytest.raises(ValueError):
        summarize(rows)
