import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from team_memory_post_generation_wait import active_maintenance,wait_for_maintenance


class PassiveWaitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def test_reused_pid_for_other_command_is_not_owned(self):
        call=self.root/'memory/backend/maintenance/call-001';call.mkdir(parents=True)
        (call/'intent.json').write_text('{}');(call/'started.json').write_text(json.dumps(dict(pid=123)))
        proc=self.root/'proc/123';proc.mkdir(parents=True);(proc/'cmdline').write_bytes(b'other-service\0')
        self.assertEqual(active_maintenance(self.root,self.root/'proc'),[])
        (proc/'cmdline').write_bytes(b'codex\0'+str(call/'answer.txt').encode()+b'\0')
        self.assertEqual(active_maintenance(self.root,self.root/'proc'),[123])

    def test_no_process_finishes_without_inference(self):
        v=wait_for_maintenance(self.root)
        self.assertEqual(v['model_calls'],0);self.assertEqual(v['signals_sent'],0)

    def test_waits_for_existing_process_without_starting_or_killing_it(self):
        with patch('team_memory_post_generation_wait.active_maintenance',side_effect=[[123],[]]),patch('team_memory_post_generation_wait.time.sleep') as sleep:
            v=wait_for_maintenance(self.root)
        self.assertEqual(v['already_started_processes_observed'],1);sleep.assert_called_once_with(.2)

    def test_deadline_stops_without_restart_or_completion_receipt(self):
        with patch('team_memory_post_generation_wait.active_maintenance',return_value=[123]):
            with self.assertRaises(TimeoutError):wait_for_maintenance(self.root,limit=0)
        self.assertFalse((self.root/'post-generation-maintenance-wait.json').exists())


if __name__=='__main__':unittest.main()
