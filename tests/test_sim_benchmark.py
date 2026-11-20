import collections
import dataclasses
import unittest

from ttgl.sim_ablation.benchmark import VERSION, evaluate, load_tasks, qualify


class SimBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = load_tasks()

    def test_split_counts_and_fingerprints(self):
        self.assertEqual(VERSION, "observatory-python-repair-001")
        counts = collections.Counter(task.split for task in self.tasks.values())
        self.assertEqual(counts, {"historical": 4, "optimization": 3, "heldout": 4})
        self.assertEqual(len({task.function for task in self.tasks.values()}), 11)
        self.assertEqual(len({task.fingerprint for task in self.tasks.values()}), 11)
        self.assertEqual(self.tasks, load_tasks())

    def test_public_roster_has_no_hidden_vectors_or_reference_sources(self):
        for task in self.tasks.values():
            with self.subTest(task=task.id):
                public = task.public_files()
                self.assertEqual(set(public), {"README.md", "solution.py", "test_public.py"})
                self.assertEqual(public["solution.py"], task.starter)
                self.assertNotIn(task.reference, "".join(public.values()))
                self.assertNotEqual(task.fingerprint,
                                    dataclasses.replace(task, hidden_tests=()).fingerprint)

    def test_real_empty_patch_and_independent_reference_controls(self):
        controls = qualify(self.tasks)
        self.assertEqual(set(self.tasks), set(controls))
        for task_id, control in controls.items():
            with self.subTest(task=task_id):
                self.assertFalse(control["empty_patch"]["passed"])
                self.assertTrue(control["reference"]["passed"])
                self.assertEqual(control["reference"]["passed_checks"],
                                 len(self.tasks[task_id].hidden_tests))

    def test_no_code_parse_failure_and_candidate_timeout_preserve_denominators(self):
        task = self.tasks["apportion-cents"]
        for candidate in ("", "def apportion", "while True: pass"):
            with self.subTest(candidate=candidate):
                grade = evaluate(task, candidate, timeout=0.5)
                self.assertFalse(grade.passed)
                self.assertEqual(grade.total_checks, len(task.hidden_tests))
                self.assertTrue(grade.failure)
        self.assertEqual(evaluate(task, "while True: pass", timeout=0.5).failure,
                         "evaluation timeout")

    def test_candidate_receives_no_host_tree_or_expected_result_file(self):
        task = self.tasks["apportion-cents"]
        source = (
            "import os\n"
            "assert set(os.listdir('/testbed')) == {'solution.py'}\n"
            "assert not os.path.exists('/workspaces')\n"
            "assert not os.path.exists('/home')\n"
            "assert not os.environ.get('CODEX_HOME')\n"
            "assert not os.environ.get('OPENAI_API_KEY')\n"
            + task.reference
        )
        self.assertTrue(evaluate(task, source).passed)

    def test_grader_detects_argument_mutation_and_detaches_overlay_outputs(self):
        task = self.tasks["overlay-bundles"]
        mutating = task.reference.replace("result = deepcopy(base)", "result = base")
        alias = task.reference.replace("result = deepcopy(base)", "result = base.copy()")
        self.assertFalse(evaluate(task, mutating).passed)
        self.assertFalse(evaluate(task, alias).passed)
        self.assertTrue(evaluate(task, task.reference).passed)


if __name__ == "__main__":
    unittest.main()
