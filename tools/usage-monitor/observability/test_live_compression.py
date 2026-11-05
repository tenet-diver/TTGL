import copy
import json
import unittest

from live_compression import transform_request, transform_text
from vendor.headroom.lossless_compaction import search_unheading, search_dir_unheading, expand_runs


class LiveCompressionTests(unittest.TestCase):
    def document(self, text):
        return dict(input=[dict(type='message', role='user', content=text),
                           dict(type='reasoning', encrypted_content='opaque'),
                           dict(type='custom_tool_call', call_id='c', name='exec_command', input='unchanged'),
                           dict(type='custom_tool_call_output', call_id='c', output=[dict(type='text', text=text)])])

    def test_only_tool_outputs_are_changed_and_source_is_retained(self):
        text=' abcdef012345 Downloading 12B\n'*200+'Error: disk quota\n Image x Pulled\n'
        doc=self.document(text);before=copy.deepcopy(doc);retained=[]
        updated, metadata=transform_request(doc,'progress',lambda digest,raw:retained.append((digest,raw)))
        self.assertEqual(doc,before)
        self.assertEqual(updated['input'][:3],doc['input'][:3])
        self.assertEqual(retained[0][1],text)
        result=updated['input'][3]['output'][0]['text']
        self.assertIn('Error: disk quota',result)
        self.assertNotIn('Downloading 12B',result)
        self.assertEqual(metadata['changes'][0]['call_id'],'c')

    def test_actual_headroom_search_and_log_transforms_round_trip(self):
        search=''.join('src/really/long/repeated/directory/application/checks.py:'+str(i)+':value_'+str(i)+'\n' for i in range(100))
        value,meta=transform_text(search,'headroom-lossless');self.assertIsNotNone(meta)
        body=value.split('\n',1)[1]
        inverse=search_unheading if meta['kind']=='headroom.search_heading' else search_dir_unheading
        self.assertEqual(inverse(body),search)
        log='INFO service cache warming step unchanged\n'*200+'ERROR disk quota\n'
        value,meta=transform_text(log,'headroom-lossless')
        self.assertEqual(meta['kind'],'headroom.collapse_runs')
        self.assertEqual(expand_runs(value.split('\n',1)[1]),log)

    def test_raw_retrieval_unknown_shapes_and_off_are_unchanged(self):
        for policy in ('off','progress','headroom-lossless'):
            doc=self.document('TTGL_RAW_EVIDENCE\n'+' abcdef012345 Downloading 12B\n'*100)
            self.assertEqual(transform_request(doc,policy)[0],doc)
        doc=self.document('def important_function():\n    return 1\n'*100)
        self.assertEqual(transform_request(doc,'headroom-lossless')[0],doc)

    def test_retention_failure_fails_open(self):
        doc=self.document(' abcdef012345 Downloading 12B\n'*200)
        def broken(*args): raise OSError('No space')
        updated,meta=transform_request(doc,'progress',broken)
        self.assertEqual(updated,doc)
        self.assertEqual(meta['changes'],[])
        self.assertEqual(meta['passthrough_reason'],'OSError')
