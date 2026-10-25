"""Leakage and provenance checks for the optional GPU experiment's data path."""

import copy
import json
import hashlib

import pytest

from ttgl.train import compose_user_prompt, internal_validation_split, load_source_metadata, main, prepare_examples


def row(task_id="task-1"):
    return {
        "task_id": task_id,
        "prompt": "Read n and print its square.",
        "teacher_outputs": ["bad", "n=int(input()); print(n*n)", "print(int(input())**2)"],
        "teacher_grades": [False, True, True],
        "split": "train",
        "source_revision": "pinned-upstream-commit",
    }


@pytest.mark.parametrize("split", ["calibration", "test", None])
def test_rejects_non_training_tasks(split):
    item = row()
    item["split"] = split
    with pytest.raises(ValueError, match="non-training"):
        prepare_examples([item])


def test_selection_is_verified_and_independent_of_order():
    a, b = row("a"), row("b")
    forward, _ = prepare_examples([a, b])
    reverse, _ = prepare_examples([b, a])
    assert forward == reverse
    for selected in forward:
        assert selected["provenance"]["selected_sample_index"] in (1, 2)
        assert selected["provenance"]["source_revision"] == "pinned-upstream-commit"
        assert selected["completion"][0]["role"] == "assistant"
        assert len(selected["provenance"]["teacher_output_sha256"]) == 64


def test_skips_unsolved_without_hiding_counts():
    failed = row("failed")
    failed["teacher_grades"] = [False, False, False]
    examples, summary = prepare_examples([row(), failed])
    assert len(examples) == 1
    assert summary["input_task_count"] == 2
    assert summary["skipped_task_ids"] == ["failed"]


def test_all_failed_is_not_a_successful_dataset():
    item = row()
    item["teacher_grades"] = [False, False, False]
    with pytest.raises(ValueError, match="No nonempty verified"):
        prepare_examples([item])


@pytest.mark.parametrize("kind", ["duplicates", "grades", "alignment", "prompt"])
def test_rejects_invalid_data(kind):
    item = row()
    if kind == "duplicates":
        inputs = [item, copy.deepcopy(item)]
    elif kind == "grades":
        item["teacher_grades"] = [0, 1, 1]
        inputs = [item]
    elif kind == "alignment":
        item["teacher_grades"] = [True]
        inputs = [item]
    else:
        item["prompt"] = ""
        inputs = [item]
    with pytest.raises(ValueError):
        prepare_examples(inputs)


def test_internal_validation_is_disjoint_and_train_only():
    examples, _ = prepare_examples([row(str(i)) for i in range(30)])
    train, validation = internal_validation_split(examples, seed=1729)
    a = {x["task_id"] for x in train}
    b = {x["task_id"] for x in validation}
    assert not a & b
    assert len(a | b) == 30
    assert len(b) == 3
    assert all(x["provenance"]["split"] == "train" for x in train + validation)


def test_dry_run_cannot_claim_training_or_overwrite_evidence(tmp_path):
    source = tmp_path / "train.jsonl"
    source.write_text(json.dumps(row()) + "\n")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"seed": 1729, "model_id": "unloaded-model", "model_revision": "main"}))
    target = tmp_path / "prepared"
    arguments = ["--dataset", str(source), "--output-dir", str(target), "--config", str(config), "--dry-run"]
    assert main(arguments) == 0
    manifest = json.loads((target / "manifest.json").read_text())
    assert manifest["status"] == "prepared_not_trained"
    assert "train_metrics" not in manifest
    with pytest.raises(FileExistsError):
        main(arguments)


def test_source_metadata_is_pinned_and_excludes_labels(tmp_path):
    path = tmp_path / "source.json"
    path.write_text(json.dumps([{
        "platform": "test", "question_id": "1", "question_content": "problem",
        "question_title": "Title", "starter_code": "class Solution: pass",
        "graded_list": [True], "code_list": ["private solution"],
        "metadata": {"private_test": "must not be used"},
    }]))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata = load_source_metadata(path, digest)
    assert set(metadata["test:1"]) == {"platform", "question_id", "prompt", "title", "starter_code"}
    text = compose_user_prompt("test:1", "problem", metadata)
    assert "class Solution: pass" in text
    assert "preserving its class and function signatures" in text
    assert "private solution" not in text
    with pytest.raises(ValueError, match="SHA256"):
        load_source_metadata(path, "wrong")
    with pytest.raises(ValueError, match="does not match"):
        compose_user_prompt("test:1", "changed problem", metadata)
    with pytest.raises(ValueError, match="No source"):
        compose_user_prompt("missing:1", "problem", metadata)
