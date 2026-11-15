"""The security continuation must never repeat a prepared or started cell."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from continue_team_memory_text_runtime import continuation_rows


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        def write(p,d):p.write_text(json.dumps(d))
        self.write=write
        write(self.root/'security-interruption-001.json',{})
        write(self.root/'queue-started.json',dict(pid=999999999))
        write(self.root/'equivalence.json',dict(passed=True))
        rows=[];assignments=[]
        for i in range(13):
            a=dict(task='task',arm='native',total_agent_capacity=1,directory=f'{i+1:03}-task')
            assignments.append(a)
            if i==12:continue
            cell=self.root/a['directory'];cell.mkdir();(cell/'independent-grade').mkdir()
            u=dict(input_tokens=10,cached_input_tokens=4,output_tokens=2,total_tokens=12);g=dict(passed=True)
            audit=dict(usage=u,usage_by_model={'gpt-6.1-sol':u},complete=True,unknown_requests=[],distinct_responses=1,responses=[dict(response_id=str(i))])
            row=dict(a,grade=g,usage=u,usage_by_model=audit['usage_by_model'],inference_accounting_complete=True,unknown_requests=[],total_inference_usage=u)
            rows.append(row)
            write(cell/'combined-usage-audit.json',audit);write(cell/'independent-grade/result.json',g);write(cell/'recompression-001.json',{})
        write(self.root/'protocol.json',dict(assignments=assignments));write(self.root/'checkpoint-012.json',dict(assignments=rows))
        self.config=dict(continue_after_checkpoint=12,protocol=str(self.root/'protocol.json'),text_equivalence=str(self.root/'equivalence.json'))

    def check(self):return continuation_rows(self.config,self.root)

    def test_accepts_only_the_sealed_registered_prefix(self):self.assertEqual(len(self.check()),12)

    def test_even_unstarted_future_directory_blocks_automatic_work(self):
        (self.root/'013-task').mkdir()
        with self.assertRaises(ValueError):self.check()

    def test_existing_continuation_receipt_blocks_second_worker(self):
        self.write(self.root/'continuation-001-started.json',{})
        with self.assertRaises(ValueError):self.check()

    def test_live_original_process_blocks_continuation(self):
        self.write(self.root/'queue-started.json',dict(pid=os.getpid()))
        with self.assertRaises(ValueError):self.check()

    def test_changed_order_or_missing_archive_blocks_continuation(self):
        p=self.root/'checkpoint-012.json';d=json.loads(p.read_text());d['assignments'][0]['directory']='002-task';self.write(p,d)
        with self.assertRaises(ValueError):self.check()

    def test_failed_equivalence_blocks_model_work(self):
        self.write(self.root/'equivalence.json',dict(passed=False))
        with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main()
