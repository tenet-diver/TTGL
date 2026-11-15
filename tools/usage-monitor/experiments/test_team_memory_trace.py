import json
from pathlib import Path
import tempfile
import unittest

from inspect_team_memory_trace import hit_count,inspect


class ExposureTests(unittest.TestCase):
    def test_empty_graph_metadata_is_not_a_hit(self):
        self.assertEqual(hit_count(dict(facts=[],episodes=[],method='stock RRF')),0)

    def test_cross_thread_mapping_and_duplicate_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def event(thread,ident,tool,args,value):
                return dict(message=dict(method='item/completed',params=dict(threadId=thread,item=dict(type='mcpToolCall',server='team_memory',id=ident,tool=tool,arguments=args,result=dict(content=[dict(type='text',text=json.dumps(value))])))))
            publish=event('parent','p','publish_finding',{},dict(record_id='r',backend_result={}))
            read=event('child','r','read_record',dict(id='r'),dict(id='r',body='checked claim',characters=13,author='spoofed-self-label'))
            search=event('child','s','search_memory',{},dict(hits=[dict(id='r',author='spoofed-self-label',preview='checked claim')]))
            (root/'rpc.jsonl').write_bytes(b'\n'.join(json.dumps(r).encode() for r in [publish,publish,read,search])+b'\n')
            value=inspect(root)
            self.assertEqual(value['completed_memory_calls'],3)
            self.assertEqual(value['known_peer_record_reads'],1)
            self.assertEqual(value['known_peer_search_calls'],1)

    def test_incomplete_stream_line_is_a_coverage_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'rpc.jsonl').write_text('{"unfinished":')
            value=inspect(root)
            self.assertTrue(value['partial_line_or_schema_gap'])
            self.assertEqual(value['completed_memory_calls'],0)

    def test_log_author_need_not_call_memory_tools_to_be_a_peer(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'combined-usage-audit.json').write_text(json.dumps(dict(sessions={
                'parent':dict(model='gpt-6.1-sol'),'quiet_worker':dict(model='gpt-6.1-sol')})))
            item=dict(type='mcpToolCall',server='team_memory',id='read',tool='read_record',arguments=dict(id='log'),
                result=dict(structuredContent=dict(id='log',body='exact tool output',author='quiet_worker')))
            (root/'rpc.jsonl').write_text(json.dumps(dict(message=dict(method='item/completed',params=dict(threadId='parent',item=item))))+'\n')
            value=inspect(root)
            self.assertEqual(value['known_peer_record_reads'],1)
            self.assertEqual(value['reads'][0]['origin'],'native-log')


if __name__=='__main__':unittest.main()
