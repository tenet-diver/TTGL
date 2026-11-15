"""Protect published cost bounds, assignment ownership and unknown metering."""
from copy import deepcopy
import unittest

from analyze_team_memory_extension import scenario, matched_comparisons, validate_assignment


class AnalysisTests(unittest.TestCase):
    def test_cached_and_reasoning_subsets_are_not_added_twice(self):
        u=dict(input_tokens=1000000,cached_input_tokens=800000,output_tokens=10000,
               reasoning_output_tokens=8000,total_tokens=1010000)
        self.assertAlmostEqual(scenario({'gpt-6.1-sol':u}),14.5)
        with self.assertRaises(ValueError):scenario({'gpt-6.1-sol':dict(u,cached_input_tokens=1000001)})

    def pair(self,arm_complete,control_complete):
        common=dict(task='task',total_agent_capacity=2,passed=True,parent_status='completed',coding_run_seconds=100)
        return [dict(common,arm='native',standard_credit_scenario_lower_bound=10,inference_accounting_complete=control_complete),
                dict(common,arm='mem0_luna',standard_credit_scenario_lower_bound=15,inference_accounting_complete=arm_complete)]

    def test_two_unknown_totals_cannot_be_ranked(self):
        result=matched_comparisons(self.pair(False,False))[0]
        self.assertIsNone(result['scenario_credit_ratio'])
        self.assertEqual(result['scenario_ratio_kind'],'unidentified')

    def test_one_unknown_total_has_correct_bound_direction(self):
        for arm,control,label in [(False,True,'lower bound'),(True,False,'upper bound'),(True,True,'exact scenario ratio')]:
            result=matched_comparisons(self.pair(arm,control))[0]
            self.assertEqual(result['scenario_ratio_kind'],label)
            self.assertEqual(result['scenario_credit_ratio'],1.5)

    def example(self):
        expected=dict(task='task',arm='native',total_agent_capacity=1,directory='001-task-native-1')
        u=dict(input_tokens=10,cached_input_tokens=4,output_tokens=2,total_tokens=12)
        audit=dict(usage=u,usage_by_model={'gpt-6.1-sol':u},complete=True,unknown_requests=[],
                   distinct_responses=1,responses=[dict(response_id='response')])
        grade=dict(passed=True)
        row=dict(expected,grade=grade,usage=u,usage_by_model=audit['usage_by_model'],
                 inference_accounting_complete=True,unknown_requests=[],total_inference_usage=u)
        return row,expected,audit,grade

    def test_registered_order_and_sealed_result_are_required(self):
        row,expected,audit,grade=self.example()
        validate_assignment(row,expected,audit,grade,set())
        with self.assertRaises(ValueError):validate_assignment(dict(row,arm='notebook'),expected,audit,grade,set())
        with self.assertRaises(ValueError):validate_assignment(row,expected,audit,dict(passed=False),set())

    def test_response_cannot_be_reused_across_cells(self):
        row,expected,audit,grade=self.example();owners=set()
        validate_assignment(row,expected,audit,grade,owners)
        with self.assertRaises(ValueError):validate_assignment(row,expected,audit,grade,owners)

    def test_unknown_request_cannot_have_a_total(self):
        row,expected,audit,grade=self.example();row=deepcopy(row);audit=deepcopy(audit)
        row['unknown_requests']=audit['unknown_requests']=[dict(usage=None)]
        row['inference_accounting_complete']=audit['complete']=False
        with self.assertRaises(ValueError):validate_assignment(row,expected,audit,grade,set())
        row['total_inference_usage']=None
        validate_assignment(row,expected,audit,grade,set())


if __name__=='__main__':unittest.main()
