"""A completed model attempt is retained; only an untouched suffix can run."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from continue_team_memory_text_runtime_v8 import continuation_rows


class PostGenerationContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.write(self.root/'queue-started.json',dict(pid=999999999))
        self.write(self.root/'equivalence.json',dict(passed=True))
        self.write(self.root/'post-generation-recovery-011.json',dict(passed=True,model_calls=0,
            next_assignment_directory_absent=True,prior_queue_pids=[999999999]))
        rows=[];assignments=[]
        for i in range(33):
            a=dict(task='task',arm='native',total_agent_capacity=1,directory=f'{i+1:03}-task');assignments.append(a)
            if i==32:continue
            cell=self.root/a['directory'];cell.mkdir();(cell/'independent-grade').mkdir()
            u=dict(input_tokens=10,cached_input_tokens=4,output_tokens=2,total_tokens=12);g=dict(passed=True)
            audit=dict(usage=u,usage_by_model={'gpt-6.1-sol':u},complete=True,unknown_requests=[],distinct_responses=1,
                responses=[dict(response_id=str(i))])
            rows.append(dict(a,grade=g,usage=u,usage_by_model=audit['usage_by_model'],inference_accounting_complete=True,
                unknown_requests=[],total_inference_usage=u))
            self.write(cell/'combined-usage-audit.json',audit);self.write(cell/'independent-grade/result.json',g)
            self.write(cell/'recompression-001.json',{})
        self.write(self.root/'protocol.json',dict(assignments=assignments));self.write(self.root/'checkpoint-032.json',dict(assignments=rows))
        self.config=dict(continue_after_checkpoint=32,protocol=str(self.root/'protocol.json'),
            text_equivalence=str(self.root/'equivalence.json'),preparation_audit=str(self.root/'post-generation-recovery-011.json'))

    def write(self,p,value):p.write_text(json.dumps(value))
    def check(self):return continuation_rows(self.config,self.root)

    def test_retains_all_ended_assignments(self):self.assertEqual(len(self.check()),32)

    def test_any_future_directory_blocks_work(self):
        (self.root/'033-task').mkdir()
        with self.assertRaises(ValueError):self.check()

    def test_live_prior_queue_blocks_work(self):
        self.write(self.root/'post-generation-recovery-011.json',dict(passed=True,model_calls=0,
            next_assignment_directory_absent=True,prior_queue_pids=[os.getpid()]))
        with self.assertRaises(ValueError):self.check()

    def test_stale_stop_blocks_work(self):
        self.write(self.root/'stopped.json',{})
        with self.assertRaises(ValueError):self.check()

    def test_duplicate_owner_blocks_work(self):
        self.write(self.root/'continuation-007-started.json',{})
        with self.assertRaises(ValueError):self.check()

    def test_unsealed_completed_cell_blocks_work(self):
        (self.root/'032-task/recompression-001.json').unlink()
        with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main()
