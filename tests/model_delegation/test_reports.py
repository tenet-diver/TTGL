from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ttgl.experience_routing.io import write_new
from ttgl.model_delegation.reports import assignment_rows, paired_target, groups, baseline_mixture_envelope


class ReportTests(unittest.TestCase):
    def row(self,task,quality,cost):
        return {'task_id':task,'protocol_resolved':quality,'total_model_scenario_usd':cost}
    def test_relative_retention_and_zero_quality_denominator_not_success(self):
        control=[self.row('a',True,1),self.row('b',True,1)]
        candidate=[self.row('a',True,.05),self.row('b',False,.05)]
        r=paired_target(candidate,control,resamples=100)
        self.assertEqual(r['relative_quality_retention'],.5);self.assertFalse(r['target_met'])
        self.assertAlmostEqual(r['observed_scenario_saving'],.95)
        r=paired_target([self.row('a',False,.01)],[self.row('a',False,1)],resamples=100)
        self.assertFalse(r['evaluable']);self.assertIsNone(r['target_met'])
    def test_missing_cost_or_quality_preserves_unknown(self):
        r=paired_target([self.row('a',True,None)],[self.row('a',True,1)])
        self.assertFalse(r['evaluable'])
        with self.assertRaises(ValueError):paired_target([self.row('a',True,.1)],[self.row('b',True,1)])
        result=groups([{'system':'luna','snapshot_id':'s','point':'endpoint','status':'graded',
                       'official_resolved':None,'protocol_resolved':None,'total_model_scenario_usd':None}])[0]
        self.assertIsNone(result['native_invocations']);self.assertIsNone(result['protocol_accuracy'])
        self.assertEqual(result['protocol_accuracy_bounds'],[0,1])
    def test_endpoint_mixture_envelope_has_no_oracle_task_selection(self):
        points=[{'mean_model_scenario_usd':1,'protocol_accuracy':.5},
                {'mean_model_scenario_usd':3,'protocol_accuracy':1}]
        self.assertEqual(baseline_mixture_envelope(points,2),.75)
        self.assertIsNone(baseline_mixture_envelope(points,.5))

    def test_shared_policy_reports_measured_cost_without_a_second_invocation(self):
        shared = {'task_id': 'task', 'system': 'routellm_native', 'snapshot_id': 'frozen'}
        assignments = [{**shared, 'assignment_id': 'original', 'point': 'cost'},
                       {**shared, 'assignment_id': 'alias', 'point': 'quality'}]
        verdict = {'official_resolved': True, 'protocol_resolved': True}
        grades = [{**verdict, 'assignment_id': 'original', 'status': 'graded'},
                  {**verdict, 'assignment_id': 'alias', 'status': 'duplicate_policy',
                   'shared_assignment_id': 'original'}]
        counters = {'input_tokens': 100, 'cached_input_tokens': 10, 'output_tokens': 20, 'total_tokens': 120}
        reconciled = {'native_receipts': 1, 'issues': [], 'models': {'luna': counters}, 'native_usage': counters}
        rates = {'luna': {'input': 2, 'cached': 0.1, 'output': 10}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_new(root / 'original' / 'completion.json', {
                'status': 'completed', 'usage': {'maximum_invocations': 1, 'maximum_elapsed_seconds': 20},
                'local_scorer_operations': [],
            })
            (root / 'original' / 'usage-ledger.jsonl').touch()
            write_new(root / 'alias' / 'completion.json', {
                'status': 'duplicate_policy', 'shared_assignment_id': 'original', 'native_invocations': 0,
            })
            with patch('ttgl.model_delegation.reports.reconcile', return_value=reconciled) as reconcile:
                original, alias = assignment_rows({'assignments': assignments}, grades, root, rates, cpu_usd_per_core_hour=0)
            reconcile.assert_called_once()
            self.assertEqual(alias['total_model_scenario_usd'], original['total_model_scenario_usd'])
            self.assertEqual(alias['protocol_resolved'], original['protocol_resolved'])
            self.assertEqual(alias['native_invocations'], 0)
            self.assertEqual(alias['reference_native_invocations'], 1)
            self.assertEqual(groups([alias])[0]['shared_policy_tasks'], 1)
