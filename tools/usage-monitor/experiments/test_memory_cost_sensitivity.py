import unittest
from memory_cost_sensitivity import summarize
R=dict(fresh_input_per_million=50,cached_input_per_million=2.5,output_per_million=250)
A=dict(fresh_input_per_million=2,cached_input_per_million=.1,output_per_million=10,long_context_threshold_input_tokens=272000,long_context_input_multiplier=2,long_context_output_multiplier=1.5)
def cell(role,n,write=0):
    u=dict(input_tokens=n,cached_input_tokens=0,output_tokens=100,cache_write_input_tokens=write)
    return dict(role=role,condition='memory',usage=u,responses=[dict(usage=u)])
class SensitivityTests(unittest.TestCase):
    def test_extraction_included_and_judges_excluded(self):
        r=summarize([cell('reader',100),cell('memory_extraction',100),cell('judge_overhead',1000000)],R,A)['memory']
        self.assertAlmostEqual(r['primary_credit_rate_scenario'],.06)
    def test_long_context_threshold_is_per_response(self):
        r=summarize([cell('reader',200000),cell('memory_extraction',200000)],R,A)['memory']
        self.assertEqual(r['api_long_context_responses'],0)
        self.assertAlmostEqual(r['api_rate_sensitivity_usd'],.802)
        r=summarize([cell('reader',300000)],R,A)['memory']
        self.assertEqual(r['api_long_context_responses'],1)
        self.assertAlmostEqual(r['api_rate_sensitivity_usd'],1.2015)
    def test_unknown_write_accounting_is_not_zero(self):
        c=cell('reader',100);c['responses'][0]['usage'].pop('cache_write_input_tokens')
        self.assertIsNone(summarize([c],R,A)['memory']['api_rate_sensitivity_usd'])
if __name__=='__main__':unittest.main()
