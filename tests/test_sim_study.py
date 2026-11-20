import unittest

from ttgl.sim_ablation.analysis import paired
from ttgl.sim_ablation.memory import build_bank, project
from ttgl.sim_ablation.study import ROOT, SEED, proposer_prompt, select


class MemoryStudyTests(unittest.TestCase):
    def test_nested_projections_hide_excluded_fields_and_records(self):
        bank = build_bank(ROOT)
        c0, c1, c2, c3 = (project(bank, arm) for arm in ("C0", "C1", "C2", "C3"))
        self.assertEqual(c0, [])
        self.assertEqual({row["classification"] for row in c1}, {"success"})
        self.assertEqual({row["classification"] for row in c2}, {"failure", "success"})
        self.assertEqual(len(c2), len(c3))
        for before, after in zip(c2, c3):
            self.assertEqual(before, {key: after[key] for key in before})
            self.assertNotIn("hypothesis", before)
            self.assertNotIn("evidence", after)
        self.assertNotIn("progress-replay", proposer_prompt(SEED, [], [], ""))

    def test_selector_prioritizes_task_success_and_rejects_regressions(self):
        def cells(ok, tokens):
            return [{"task_id": str(i), "grade": {"passed": flag}, "usage": {"total_tokens": token}}
                    for i, (flag, token) in enumerate(zip(ok, tokens))]
        baseline = cells([True, False], [100, 100])
        self.assertEqual(select(baseline, cells([False, True], [10, 10])), (False, "regression", ["0"]))
        self.assertEqual(select(baseline, cells([True, True], [1000, 1000])), (True, "more_tasks_passed", []))
        self.assertEqual(select(baseline, cells([True, False], [90, 90])),
                         (True, "same_outcomes_at_least_ten_percent_fewer_tokens", []))

    def test_inference_requires_independent_repetitions(self):
        result = paired([0.25])
        self.assertEqual(result["mean"], 0.25)
        self.assertIsNone(result["bootstrap_95"])
        self.assertIsNone(result["signflip_p_two_sided"])
        self.assertEqual(paired([0.25] * 5)["signflip_p_two_sided"], 0.0625)
        self.assertEqual(paired([0] * 5)["bootstrap_95"], [0, 0])
