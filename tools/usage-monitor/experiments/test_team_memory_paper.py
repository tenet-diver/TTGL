"""Publication must preserve pilot evidence and never upgrade partial results."""
from copy import deepcopy
from pathlib import Path
import unittest

from update_team_memory_paper import render,LABELS


class PaperTests(unittest.TestCase):
    def fixture(self):
        cells=[dict(directory=f'cell{i}',arm=list(LABELS)[i//8],native_usage_lower_bound=dict(total_tokens=100),
            passed=True,parent_status='completed',inference_accounting_complete=True) for i in range(56)]
        arms=[dict(arm=arm,completed=8,successes=8,normal_parents=8,accounting_complete=True,accounting_complete_cells=8,
            mean_seconds=100,mean_credit_lower_bound=2) for arm in LABELS]
        result=dict(state='complete',completed=56,planned=56,cells=cells,arms=arms,
            audit=dict(source_passes=56,normal_parents=56,complete_usage_cells=56))
        audit=dict(passed=True,registered_cells=56,archives=[dict(directory=c['directory']) for c in cells],
            official_mcp_exposure=[],exposure=[],totals=dict(recorded_native_usage_lower_bound=dict(total_tokens=5600),
            standard_scenario_credits_lower_bound=112,unknown_requests=0))
        text=(Path(__file__).resolve().parents[3]/'docs/paper/codex-team-knowledge/paper.md').read_text()
        return text,result,audit

    def test_incomplete_matrix_cannot_publish_complete_paper(self):
        text,result,audit=self.fixture();result['completed']=55
        with self.assertRaises(ValueError):render(text,result,audit)

    def test_stale_audit_or_false_headline_is_rejected(self):
        text,result,audit=self.fixture();audit['totals']['recorded_native_usage_lower_bound']['total_tokens']=5599
        with self.assertRaises(ValueError):render(text,result,audit)
        text,result,audit=self.fixture();result['audit']['source_passes']=55
        with self.assertRaises(ValueError):render(text,result,audit)

    def test_historical_pilot_is_preserved_and_render_is_idempotent(self):
        text,result,audit=self.fixture();after=render(text,result,audit)
        pilot=text.split('## 6. Results: completed development pilot',1)[1].split('## 7. Discussion',1)[0]
        # The original pilot result block ends before the separately added extension.
        pilot=pilot.split('### 6.6 Completed memory-aware extension',1)[0]
        self.assertIn(pilot,after)
        self.assertEqual(render(after,result,audit),after)

    def test_failed_source_and_stopped_parent_remain_distinct(self):
        text,result,audit=self.fixture();result['cells'][0]['passed']=False;result['audit']['source_passes']=55
        result['cells'][1]['parent_status']='stopped';result['audit']['normal_parents']=55
        result['arms'][0]['successes']=7;result['arms'][0]['normal_parents']=7
        after=render(text,result,audit)
        self.assertIn('55/56 sealed source artifacts',after)
        self.assertIn('Normal parent completion in the extension is 55/56',after)
        self.assertNotIn('All 56 sealed source artifacts pass',after)


if __name__=='__main__':unittest.main()
