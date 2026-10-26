import pytest

from ttgl.pilot import summarize, validate_record


def trial(task, arm, success, cost=None):
    return dict(task_id=task, arm=arm, status="graded", model_id=arm, resolved=success,
                grader_report_sha256="a" * 64, cost_usd=cost,
                cost_source="fixture invoice" if cost is not None else None,
                wall_seconds=1, expert_calls=0)


def test_unknown_cost_is_not_free_and_failed_tasks_stay_in_denominator():
    records = [trial("1", "small", True), trial("2", "small", False),
               trial("1", "large", True, 2), trial("2", "large", False, 3)]
    report = summarize(records, ["1", "2"], ["small", "large"], "large")
    assert report["arms"]["small"]["cost_per_assigned_usd"] is None
    assert report["arms"]["large"]["cost_per_resolved_usd"] == 5
    assert report["arms"]["large"]["cost_per_assigned_usd"] == 2.5
    assert report["arms"]["small"]["resolved_per_assigned"] == .5


def test_paired_analysis_and_integrity():
    records = [trial("1", "s", False), trial("2", "s", True),
               trial("1", "l", True), trial("2", "l", True)]
    assert summarize(records, ["1", "2"], ["s", "l"], "l")["paired_differences"]["s"]["quality_difference"] == -.5
    with pytest.raises(ValueError, match="Incomplete"):
        summarize(records[:-1], ["1", "2"], ["s", "l"], "l")
    with pytest.raises(ValueError, match="Duplicate"):
        summarize(records + records[:1], ["1", "2"], ["s", "l"], "l")
    with pytest.raises(ValueError, match="source"):
        validate_record({**records[0], "cost_usd": 0, "cost_source": None})


def test_ungraded_failure_is_retained_without_inventing_test_result():
    records = [trial("1", "s", None), trial("1", "l", True)]
    report = summarize(records, ["1"], ["s", "l"], "l")
    assert report["arms"]["s"]["ungraded"] == 1
    assert report["paired_differences"]["s"]["status"] == "unavailable_ungraded_pairs"
