import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ttgl.model_delegation.knowledge import validate_check,verify_public_reproduction,extract
from ttgl.experience_routing.io import write_new,file_digest
from ttgl.personal import Response


class KnowledgeTests(unittest.TestCase):
    def test_completed_annotation_records_native_usage_before_empty_result(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);episode=p/'episode'
            write_new(episode/'completion.json',{'status':'completed','invalid_paths':[],
                'model':'gpt-6-luna','model_report':{'summary':'public'},'public_check_passed':True})
            with patch('ttgl.model_delegation.knowledge.source_binding',return_value={'account_hash':'source'}), \
                 patch('ttgl.model_delegation.knowledge.admit',return_value=({'codex_executable_sha256':file_digest(__file__),'maximum_invocations':1},p,'registration')), \
                 patch('ttgl.model_delegation.knowledge.claim'), \
                 patch('ttgl.model_delegation.knowledge.shutil.which',return_value=__file__), \
                 patch('ttgl.model_delegation.knowledge.LocalS3Retention'), \
                 patch('ttgl.model_delegation.knowledge.SubscriptionBackend') as backend:
                backend.return_value.complete.return_value=Response(status='completed',text='{"records":[]}',
                    thread_id='fresh',usage={'input_tokens':100,'cached_input_tokens':0,'output_tokens':10})
                backend.return_value.last_native_artifact_hash='native'
                backend.return_value.last_response_ids=['response']
                result=extract(root=p,output=p/'out',base=p,candidate=p,episode=episode,
                    task={'task_id':'task','prompt':'public request'},source_home=p,image_review={'image_id':'image'},
                    registration=p/'registration.json',scope={})
            self.assertEqual(backend.return_value.complete.call_count,1)
            self.assertEqual(result['native_usage']['total_tokens'],110)
            self.assertEqual(result['records'],[])
            self.assertIn('seed_construction',(p/'out/accounting/usage-ledger.jsonl').read_text())

    def test_public_reproduction_is_bounded_assertion_language(self):
        good='from sympy import Integer\nassert Integer(2)+2 == 4\n'
        self.assertEqual(validate_check(good),good)
        for code in ['print(1)','import os\nassert True','assert open("x")','assert eval("1")',
                     'while True: pass\nassert True','assert (1).__class__','from .sympy import Integer\nassert True']:
            with self.subTest(code=code),self.assertRaises(ValueError):validate_check(code)

    def test_differential_requires_expected_assertion_exit_not_arbitrary_failure(self):
        class Actor:
            codes=[]
            def __init__(self,**kwargs):pass
            def public_check(self,argv,source,timeout,raw_output=None):
                Path(raw_output).write_bytes(b'exact result\n')
                self.assert_wrapper=(Path(source)/argv[-1]).read_text()
                assert 'except AssertionError:' in self.assert_wrapper
                return {'returncode':self.codes.pop(0),'infrastructure_error':False}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);base=p/'base';base.mkdir();(base/'app.py').write_text('a=1\n')
            for i,(codes,positive,negative) in enumerate([([17,0],True,False),([1,0],False,False),([17,17],False,True),([0,0],False,False)]):
                Actor.codes=codes
                with patch('ttgl.model_delegation.knowledge.ExactModeActor',Actor),patch('ttgl.model_delegation.knowledge.LocalS3Retention') as client:
                    result=verify_public_reproduction('assert 1 == 2',base=base,candidate=base,output=p/str(i),image_review={'image_id':'image'})
                    self.assertEqual(client.return_value.retain_file.call_count,2)
                self.assertEqual(result['supported_positive'],positive)
                self.assertEqual(result['supported_negative'],negative)
