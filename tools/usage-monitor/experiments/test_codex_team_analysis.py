import unittest
from analyze_codex_team_scaling import memory_exposure, price


def event(tool, value, start, end, error=None):
    return dict(type='mcpToolCall',server='team_memory',tool=tool,startedAtMs=start,
        completedAtMs=end,result=dict(structuredContent=value),error=error)


class AnalysisTests(unittest.TestCase):
    def test_peer_exposure_requires_prior_publication_and_different_reader(self):
        value={'entities':[{'name':'procedure','observations':['run the checked command']}]}
        items={('writer','write'):event('create_entities',value,5,10),
            ('reader','overlap'):event('search_nodes',value,9,11),
            ('reader','later'):event('open_nodes',value,12,15),
            ('writer','self'):event('read_graph',value,16,18)}
        result=memory_exposure(items)
        self.assertEqual(result['cross_agent_read_calls'],1)
        self.assertEqual(result['cross_agent_observation_exposures'],1)

    def test_failed_write_does_not_create_author_evidence(self):
        value={'entities':[{'name':'procedure','observations':['unpublished']} ]}
        items={('writer','write'):event('create_entities',value,5,10,{'message':'failure'}),
            ('reader','read'):event('open_nodes',value,12,15)}
        result=memory_exposure(items)
        self.assertEqual(result['published_observations'],0)
        self.assertEqual(result['cross_agent_read_calls'],0)
        self.assertEqual(result['explicit_tool_errors'],1)

    def test_same_entity_with_different_observation_is_not_exact_exposure(self):
        original={'entities':[{'name':'procedure','observations':['original']} ]}
        returned={'entities':[{'name':'procedure','observations':['different']} ]}
        result=memory_exposure({('a','w'):event('create_entities',original,1,2),('b','r'):event('open_nodes',returned,3,4)})
        self.assertEqual(result['cross_agent_read_calls'],0)

    def test_cached_input_is_priced_once(self):
        result=price(dict(input_tokens=1000000,cached_input_tokens=500000,output_tokens=100000,cache_write_input_tokens=0))
        self.assertEqual(result['standard_credit_scenario'],51.25)
        self.assertEqual(result['standard_api_equivalent_usd'],2.05)


if __name__=='__main__':unittest.main()
