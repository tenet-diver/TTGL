from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from ttgl.experiment_mcp import decide, handle, inspect, launch, plan
from ttgl.experience_routing.io import write_new
from ttgl.sim_ablation.study import SEED


class ExperimentMCPTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.after = {**SEED, "tool_use": "scoped"}

    def register(self):
        return plan(self.root, SEED, self.after, "Bound noise while preserving evidence", ["source:evidence-1"])

    def test_plan_content_identity_and_no_change_to_normal_harness(self):
        registered = self.register()
        identity = registered["trial_id"]
        self.assertEqual(self.register(), registered)
        self.assertEqual(inspect(self.root, identity)["status"], "planned")
        self.assertIn("Read only relevant files", registered["protocol"]["prompt_diff"])
        self.assertEqual(registered["protocol"]["maximum_native_calls"], 6)
        self.assertEqual(list(self.root.iterdir()), [self.root / identity])

    def test_rejects_noop_and_multiple_setting_changes(self):
        for after in (SEED, {**self.after, "verification": "boundary"}):
            with self.assertRaisesRegex(ValueError, "exactly one"):
                plan(self.root, SEED, after, "Hypothesis", [])

    def test_launch_requires_host_permission_and_dispatches_only_once(self):
        identity = self.register()["trial_id"]
        with patch("ttgl.experiment_mcp.subprocess.Popen") as spawn:
            with self.assertRaisesRegex(ValueError, "host authorization"):
                launch(self.root, identity, False)
            self.assertEqual(launch(self.root, identity, True)["status"], "queued")
            self.assertEqual(launch(self.root, identity, True)["status"], "queued")
            spawn.assert_called_once()

    def test_keep_requires_independent_acceptance(self):
        identity = self.register()["trial_id"]
        with self.assertRaisesRegex(ValueError, "measured trial"):
            decide(self.root, identity, "keep", "Rationale")
        write_new(self.root / identity / "result.json", {"acceptance_passed": False})
        with self.assertRaisesRegex(ValueError, "acceptance"):
            decide(self.root, identity, "keep", "Rationale")
        self.assertEqual(decide(self.root, identity, "reject", "No check improvement")["decision"], "reject")
        self.assertEqual(inspect(self.root, identity)["status"], "measured")

    def test_stdio_tool_payload_response_and_path_validation(self):
        self.assertEqual(len(handle(self.root, False, "tools/list", {})["tools"]), 5)
        result = handle(self.root, False, "tools/call", {"name": "get_harness_trial", "arguments": {"trial_id": "../other"}})
        self.assertTrue(result["isError"])
