import unittest
from ttgl.model_delegation.reports import paired_target,groups,baseline_mixture_envelope


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
