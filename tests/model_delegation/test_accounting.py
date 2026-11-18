import json,tempfile,unittest
from pathlib import Path
from ttgl.model_delegation.accounting import reconcile


class AccountingTests(unittest.TestCase):
    def row(self):
        return {'kind':'native','model':'luna','thread_id':'thread','raw_artifact_hash':'raw','signature':'sig',
                'response_ids':['response'],'delta':{'input_tokens':100,'output_tokens':10,'total_tokens':110},
                'role':'small_execution','purpose':'research_measurement'}
    def test_copied_receipt_not_added_twice_and_logical_charges_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);row=self.row();a=p/'a';b=p/'b'
            a.write_text(json.dumps(row)+'\n'+json.dumps({'kind':'logical_policy_charge'})+'\n');b.write_text(json.dumps(row)+'\n')
            result=reconcile([a,b]);self.assertEqual(result['native_usage']['total_tokens'],110)
            self.assertEqual(result['native_receipts'],1);self.assertEqual(len(result['duplicates_excluded']),1)
            self.assertIsNone(result['wall_time_total'])
    def test_overlap_or_separate_cumulative_thread_requires_reconciliation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);a=p/'a';b=p/'b';row=self.row();a.write_text(json.dumps(row)+'\n')
            row.update(raw_artifact_hash='other',signature='other');b.write_text(json.dumps(row)+'\n')
            result=reconcile([a,b]);self.assertIsNone(result['native_usage']['total_tokens'])
            self.assertIn('overlapping_native_response_ids',result['issues'])
