import json
import unittest
from inspect_team_official_memory import inspect_body


def call(thread,ident,tool,value):
    return dict(message=dict(method='item/completed',params=dict(threadId=thread,item=dict(type='mcpToolCall',server='team_memory',id=ident,tool=tool,result=dict(structuredContent=value)))))


class OfficialExposureTests(unittest.TestCase):
    def report(self,rows):return inspect_body(b'\n'.join(json.dumps(r).encode() for r in rows))

    def test_future_publication_cannot_explain_an_earlier_read(self):
        entity=dict(name='module',observations=['claim'])
        rows=[call('reader','1','open_nodes',dict(entities=[entity])),call('writer','2','create_entities',dict(entities=[entity]))]
        self.assertEqual(self.report(rows)['known_peer_read_queries'],0)

    def test_entity_metadata_and_self_reads_are_not_peer_text(self):
        entity=dict(name='module',observations=['claim'])
        rows=[call('writer','1','create_entities',dict(entities=[entity])),
              call('reader','2','open_nodes',dict(entities=[dict(name='module',observations=[])])),
              call('writer','3','open_nodes',dict(entities=[entity]))]
        self.assertEqual(self.report(rows)['known_peer_read_queries'],0)

    def test_exact_peer_observation_and_duplicate_delivery(self):
        entity=dict(name='module',observations=['claim'])
        publish=call('writer','1','create_entities',dict(entities=[entity]))
        read=call('reader','2','open_nodes',dict(entities=[entity]))
        result=self.report([publish,publish,read,read])
        self.assertEqual(result['returned_publication_observations'],1)
        self.assertEqual(result['known_peer_read_queries'],1)
        self.assertEqual(result['completed_memory_calls'],2)

    def test_publication_and_final_retention_are_separate(self):
        entity=dict(name='module',observations=['claim'])
        body=json.dumps(call('writer','1','create_entities',dict(entities=[entity]))).encode()
        result=inspect_body(body,set())
        self.assertEqual(result['unique_announced_observations'],1)
        self.assertEqual(result['accepted_observations_absent_from_sealed_file'],1)


if __name__=='__main__':unittest.main()
