import copy

import pytest

from ttgl.generate import build_custom_outputs, extract_code, prepare_tasks


def fixture():
    rows = [{"task_id": "site:1", "split": "test", "prompt": "problem", "teacher_grades": [True]}]
    metadata = {"site:1": {"platform": "site", "question_id": "1", "prompt": "problem", "title": "Title",
                           "starter_code": "class Solution:\n    def solve(self): pass"}}
    return rows, metadata


def test_outcome_fields_cannot_change_generation_prompt():
    rows, metadata = fixture()
    original = prepare_tasks(rows, metadata)
    rows[0]["teacher_grades"] = [False]
    rows[0]["teacher_outputs"] = ["a gold answer that must not enter a prompt"]
    assert original == prepare_tasks(rows, metadata)
    assert "class Solution:" in original[0]["messages"][1]["content"]
    assert "gold answer" not in str(original)


@pytest.mark.parametrize("failure", ["duplicate", "split", "mismatch", "missing"])
def test_task_alignment_failures(failure):
    rows, metadata = fixture()
    if failure == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif failure == "split":
        rows[0]["split"] = "train"
    elif failure == "mismatch":
        rows[0]["prompt"] = "wrong problem"
    else:
        metadata = {}
    with pytest.raises(ValueError):
        prepare_tasks(rows, metadata)


def test_official_style_extraction_keeps_empty_failure():
    assert extract_code("explanation\n```python\nprint(1)\n```") == "print(1)"
    assert extract_code("```python\nold\n```\n```python\nnew\n```") == "new"
    assert extract_code("No code fence") == ""


def test_export_requires_all_samples_and_keeps_empty_code():
    tasks = prepare_tasks(*fixture())
    records = [{"task_id": "site:1", "sample_index": 0, "code": ""},
               {"task_id": "site:1", "sample_index": 1, "code": "print(1)"}]
    assert build_custom_outputs(tasks, records, 2) == [{"question_id": "1", "code_list": ["", "print(1)"]}]
    with pytest.raises(ValueError, match="Incomplete"):
        build_custom_outputs(tasks, records[:1], 2)
    with pytest.raises(ValueError, match="duplicate"):
        build_custom_outputs(tasks, records + [records[0]], 2)
