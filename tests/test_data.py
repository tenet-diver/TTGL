"""Tests for provenance, pairing, task independence, and split leakage."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from ttgl.data import (
    LOCAL_MODEL, grouped_temporal_split, load_source, prepare_pair,
)


def source_row(task_id="1", contest="a", date="2024-01-01T00:00:00"):
    return {
        "platform": "test", "question_id": task_id, "contest_id": contest,
        "contest_date": date, "question_content": "Solve this task.",
        "question_title": "Task", "starter_code": "", "difficulty": "easy",
        "output_list": ["```python\npass\n```"] * 10,
        "code_list": ["pass"] * 10, "graded_list": [False] * 10,
    }


class PairingTests(unittest.TestCase):
    def test_pair_by_identity_not_file_order(self):
        a, b = source_row("a"), source_row("b")
        b["question_content"] = "Different task."
        result, counts = prepare_pair([a, b], [copy.deepcopy(b), copy.deepcopy(a)])
        self.assertEqual([r["task_id"] for r in result], ["test:a", "test:b"])
        self.assertEqual(counts["shared_tasks"], 2)

    def test_duplicate_task_key_rejected(self):
        a = source_row()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            prepare_pair([a, copy.deepcopy(a)], [a])

    def test_prompt_mismatch_rejected(self):
        a, b = source_row(), source_row()
        b["question_content"] = "Changed problem."
        with self.assertRaisesRegex(ValueError, "Mismatched"):
            prepare_pair([a], [b])

    def test_blank_sanitized_output_is_retained(self):
        a, b = source_row(), source_row()
        a["code_list"][0] = ""
        result, _ = prepare_pair([a], [b])
        self.assertEqual(result[0]["local_outputs"][0], "")
        self.assertEqual(len(result[0]["local_grades"]), 10)

    def test_missing_generation_and_nonboolean_grade_rejected(self):
        for field, replacement in [("output_list", [""] * 10), ("graded_list", [0] * 10)]:
            with self.subTest(field=field):
                a, b = source_row(), source_row()
                a[field] = replacement
                with self.assertRaises(ValueError):
                    prepare_pair([a], [b])

    def test_mismatched_sample_lengths_rejected(self):
        a, b = source_row(), source_row()
        a["graded_list"] = [False] * 9
        with self.assertRaisesRegex(ValueError, "Expected 10"):
            prepare_pair([a], [b])


class SplitTests(unittest.TestCase):
    def build_rows(self):
        source = [source_row(str(i), str(i // 2), f"2024-01-{i // 2 + 1:02d}T00:00:00") for i in range(20)]
        return prepare_pair(source, copy.deepcopy(source))[0]

    def test_split_keeps_entire_contest_and_samples(self):
        rows = self.build_rows()
        splits, manifest = grouped_temporal_split(rows)
        self.assertEqual([len(splits[k]) for k in ("train", "calibration", "test")], [12, 4, 4])
        self.assertTrue(manifest["task_sets_disjoint"])
        self.assertTrue(manifest["contest_groups_disjoint"])
        self.assertEqual(sum(len(v) for v in splits.values()), len(rows))
        self.assertTrue(all(len(r["local_grades"]) == 10 for batch in splits.values() for r in batch))

    def test_assignment_independent_of_outcomes_and_input_order(self):
        rows = self.build_rows()
        before, _ = grouped_temporal_split(rows)
        modified = copy.deepcopy(rows[::-1])
        for row in modified:
            row["local_grades"] = [True] * 10
            row["teacher_grades"] = [True] * 10
        after, _ = grouped_temporal_split(modified)
        self.assertEqual({k: [x["task_id"] for x in v] for k, v in before.items()},
                         {k: [x["task_id"] for x in v] for k, v in after.items()})

    def test_group_max_date_controls_order(self):
        rows = self.build_rows()
        rows[0]["contest_date"] = "2024-12-01T00:00:00"
        splits, _ = grouped_temporal_split(rows)
        self.assertTrue({"test:0", "test:1"} <= {x["task_id"] for x in splits["test"]})

    def test_too_few_groups_rejected(self):
        rows = prepare_pair([source_row()], [source_row()])[0]
        with self.assertRaisesRegex(ValueError, "three contest groups"):
            grouped_temporal_split(rows)


class ProvenanceTests(unittest.TestCase):
    def test_modified_source_rejected_before_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / f"{LOCAL_MODEL}.json").write_text(json.dumps([source_row()]))
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                load_source(root, LOCAL_MODEL)


if __name__ == "__main__":
    unittest.main()
