import unittest
from unittest.mock import patch
from ttgl.model_delegation.calibration import calibrate,select_routes


class CalibrationTests(unittest.TestCase):
    def test_missing_failure_class_stops_before_fitting_or_baseline_claim(self):
        records=[]
        for i in range(6):
            for model in ('gpt-6-luna','gpt-6.1-sol'):
                records.append({'task_id':str(i),'model':model,'resolved':True if model.endswith('sol') else i%2==0,'scenario_cost':1})
        with patch('ttgl.model_delegation.calibration.load_cores') as fit:
            result=calibrate({'partition':'development','records':records,'evaluation_ids':['unseen']})
            fit.assert_not_called()
        self.assertFalse(result['sufficiency_passed']);self.assertIsNone(result['points'])
        with self.assertRaises(ValueError):calibrate({'partition':'development','records':records,'evaluation_ids':['0']})

    def test_infeasible_operating_point_retained_and_quality_cost_selection_explicit(self):
        pairs=[{'task_id':'a','luna':{'resolved':False,'scenario_cost':1},'sol':{'resolved':True,'scenario_cost':10}},
               {'task_id':'b','luna':{'resolved':True,'scenario_cost':1},'sol':{'resolved':True,'scenario_cost':10}}]
        points,_=select_routes(pairs,{'a':.8,'b':.2},{'impossible':.5,'balanced':5.5,'quality':10})
        self.assertIsNone(points['impossible'])
        self.assertEqual(points['balanced']['resolved'],2)
        self.assertEqual(points['balanced']['mean_scenario_cost'],5.5)
