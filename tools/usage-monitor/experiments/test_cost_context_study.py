import unittest
from cost_context_study import price


class CostContracts(unittest.TestCase):
    def test_cached_subset_is_not_charged_again_as_fresh(self):
        rates=dict(fresh_input_per_million=2,cached_input_per_million=.1,output_per_million=10)
        self.assertAlmostEqual(price(dict(input_tokens=1000000,cached_input_tokens=900000,output_tokens=10000),rates),.39)

    def test_fewer_tokens_can_cost_more(self):
        rates=dict(fresh_input_per_million=2,cached_input_per_million=.1,output_per_million=10)
        cached=dict(input_tokens=1000000,cached_input_tokens=900000,output_tokens=1000)
        shorter=dict(input_tokens=500000,cached_input_tokens=0,output_tokens=1000)
        self.assertGreater(price(shorter,rates),price(cached,rates))

    def test_missing_usage_and_invalid_cache_are_unknown_not_zero(self):
        rates=dict(fresh_input_per_million=2,cached_input_per_million=.1,output_per_million=10)
        for usage in ({},dict(input_tokens=1,cached_input_tokens=2,output_tokens=0)):
            with self.assertRaises(ValueError):price(usage,rates)


if __name__=='__main__':unittest.main()
