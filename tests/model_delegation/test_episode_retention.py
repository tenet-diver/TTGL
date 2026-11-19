import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ttgl.personal import Response
from ttgl.experience_routing.io import read, file_digest
from ttgl.model_delegation.episode import run_episode


class EpisodeRetentionTests(unittest.TestCase):
    def test_completed_no_action_is_retained_and_metered_for_later_grading(self):
        class Actor:
            created=False
            def __init__(self,**kwargs):pass
            def start(self,source):self.created=True;return 'actor'
            def after_attempt(self,source):pass
            def public_check(self,argv,source,timeout,raw_output=None):
                Path(raw_output).write_bytes(b'public smoke passes\n')
                return {'returncode':0,'infrastructure_error':False,'output':'public smoke passes'}
            def close(self):pass
        class Backend:
            last_native_artifact_hash='native';last_response_ids=['response']
            def __init__(self,**kwargs):pass
            def complete(self,request):
                return Response(status='completed',thread_id='fresh',text='{"summary":"Incomplete","complete":false,"checks":[],"remaining_uncertainty":"No repair made"}',
                    usage={'input_tokens':100,'cached_input_tokens':0,'output_tokens':10})
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source';source.mkdir();(source/'app.py').write_text('original=True\n')
            with patch('ttgl.model_delegation.episode.source_binding',return_value={'account_hash':'source'}), \
                 patch('ttgl.model_delegation.episode.admit',return_value=({'maximum_invocations':1,'maximum_observed_total_tokens':1000,
                    'codex_executable_sha256':file_digest(__file__),'maximum_tool_calls':12},root,'freeze')), \
                 patch('ttgl.model_delegation.episode.claim'), \
                 patch('ttgl.model_delegation.episode.shutil.which',return_value=__file__), \
                 patch('ttgl.model_delegation.episode.ExactModeActor',Actor), \
                 patch('ttgl.model_delegation.episode.ActorSubscriptionBackend',Backend), \
                 patch('ttgl.model_delegation.episode.LocalS3Retention') as archive:
                archive.return_value.retain_file.return_value={'artifactId':'retained'}
                result=run_episode(root=root,output=root/'attempt',source=source,source_home=root,
                    model='gpt-6-luna',image_review={'image_id':'actor'},task={'task_id':'task','prompt':'repair',
                    'allowed_write_paths':['app.py'],'public_check':['python3','check.py']},packet={})
            self.assertFalse(result['actor_tools_used']);self.assertEqual(result['native_usage']['total_tokens'],110)
            self.assertEqual(result['changed_paths'],[]);self.assertFalse(result['model_report']['complete'])
            self.assertIsNone(result['benchmark_grade'])

    def test_failed_native_response_seals_partial_candidate_without_retry(self):
        class Actor:
            created = False
            exports = 0
            def __init__(self, **kwargs): pass
            def start(self, source): self.created = True; return 'actor'
            def after_attempt(self, source):
                self.exports += 1
                (source/'app.py').write_text('partial_candidate = True\n')
            def close(self): pass
        class Backend:
            calls = 0
            last_native_artifact_hash = 'native-evidence'
            last_response_ids = []
            def __init__(self, **kwargs): pass
            def complete(self, request):
                Backend.calls += 1
                return Response(status='failed', thread_id='fresh-thread',
                    usage={'input_tokens': 100, 'cached_input_tokens': 0, 'output_tokens': 10})
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'source'; source.mkdir(); (source/'app.py').write_text('original = True\n')
            output = root/'attempt'
            with patch('ttgl.model_delegation.episode.source_binding', return_value={'account_hash': 'source'}), \
                 patch('ttgl.model_delegation.episode.admit', return_value=({'maximum_invocations': 2,
                     'codex_executable_sha256': file_digest(__file__), 'maximum_tool_calls': 12}, root, 'freeze')), \
                 patch('ttgl.model_delegation.episode.claim'), \
                 patch('ttgl.model_delegation.episode.shutil.which', return_value=__file__), \
                 patch('ttgl.model_delegation.episode.ExactModeActor', Actor), \
                 patch('ttgl.model_delegation.episode.ActorSubscriptionBackend', Backend), \
                 patch('ttgl.model_delegation.episode.LocalS3Retention') as archive:
                archive.return_value.retain_file.return_value = {'artifactId': 'retained'}
                with self.assertRaises(ValueError):
                    run_episode(root=root, output=output, source=source, source_home=root,
                        model='gpt-6-luna', image_review={'image_id': 'actor'},
                        task={'task_id': 'task', 'prompt': 'repair', 'allowed_write_paths': ['app.py']}, packet={})
            self.assertEqual(Backend.calls, 1)
            stopped = read(output/'stopped.json')
            self.assertEqual(stopped['quarantined_candidate']['artifactId'], 'retained')
            self.assertEqual(stopped['quarantined_candidate']['format'], 'source-file-delta-v1')
            self.assertIn('partial_candidate', (source/'app.py').read_text())
            self.assertIsNone(stopped['preservation_error'])
            self.assertTrue(stopped['model_may_have_started'])
