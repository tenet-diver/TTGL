import copy
import hashlib
import json
import unittest

from context_archive_policy import rewrite


class ArchivePolicyContracts(unittest.TestCase):
    def document(self):
        return dict(input=[dict(type='message',role='system',content='protect '+('s'*2000)),
                           dict(type='message',role='user',content='requirements '+('u'*2000)),
                           dict(type='reasoning',encrypted_content='opaque'),
                           *[dict(type='function_call_output',call_id=f'c{i}',output=dict(exit_code=i%2,output=f'row{i}: '+('x'*2000),opaque={'must_preserve':'v'})) for i in range(6)]])

    def test_age_selection_protects_non_tool_items_and_status(self):
        doc=self.document();before=copy.deepcopy(doc);archive={}
        updated,meta=rewrite(doc,'older-mask',lambda h,t:archive.__setitem__(h,t),keep_last=4)
        self.assertEqual(doc,before)
        self.assertEqual(updated['input'][:3],doc['input'][:3])
        self.assertEqual(updated['input'][-4:],doc['input'][-4:])
        self.assertEqual(len(meta['changes']),2)
        for change in meta['changes']:
            self.assertEqual(hashlib.sha256(archive[change['source_sha256']].encode()).hexdigest(),change['source_sha256'])
        for old,new in zip(doc['input'][3:],updated['input'][3:]):
            self.assertEqual(new['call_id'],old['call_id']);self.assertEqual(new['output']['exit_code'],old['output']['exit_code'])
            self.assertEqual(new['output']['opaque'],old['output']['opaque'])

    def test_handles_are_stable_but_age_boundary_changes_prior_context(self):
        doc=self.document();archive=lambda *args:None
        handles,_=rewrite(doc,'reversible-handles',archive)
        extended=dict(input=doc['input']+[dict(type='function_call_output',call_id='new',output='new')])
        later,_=rewrite(extended,'reversible-handles',archive)
        self.assertEqual(handles['input'],later['input'][:-1])
        masked,_=rewrite(doc,'older-mask',archive,keep_last=4)
        later,_=rewrite(extended,'older-mask',archive,keep_last=4)
        self.assertNotEqual(masked['input'],later['input'][:-1])

    def test_json_wrappers_raw_recovery_and_archive_failure(self):
        doc=self.document();doc['input'][3]['output']=json.dumps(doc['input'][3]['output'])
        updated,meta=rewrite(doc,'reversible-handles',lambda *args:None)
        self.assertEqual(json.loads(updated['input'][3]['output'])['exit_code'],0)
        raw=dict(input=[dict(type='function_call_output',call_id='raw',output='TTGL_RAW_EVIDENCE '+('x'*2000))])
        self.assertEqual(rewrite(raw,'reversible-handles',lambda *args:None)[0],raw)
        def broken(*args):raise OSError('archive unavailable')
        updated,meta=rewrite(doc,'older-mask',broken)
        self.assertEqual(updated,doc);self.assertEqual(meta['changes'],[])
        self.assertEqual(meta['passthrough_reason'],'OSError')
        self.assertEqual(rewrite(doc,'older-mask')[0],doc)

    def test_partial_archival_failure_and_provider_references_fail_open(self):
        doc=self.document();saved=[]
        def partial(digest,body):
            if saved:raise OSError('second archival write failed')
            saved.append((digest,body))
        updated,meta=rewrite(doc,'reversible-handles',partial)
        self.assertEqual(updated,doc);self.assertEqual(meta['changes'],[])
        self.assertEqual(len(saved),1)
        self.assertEqual(meta['archived_fields_before_failure'],1)
        references=dict(input=[dict(type='item_reference',id='opaque-provider-reference')])
        updated,meta=rewrite(references,'older-mask',partial)
        self.assertEqual(updated,references);self.assertEqual(meta['completed_outputs_present'],0)
        self.assertIsNone(rewrite(doc,'off')[1]['completed_outputs_present'])


if __name__=='__main__':unittest.main()
