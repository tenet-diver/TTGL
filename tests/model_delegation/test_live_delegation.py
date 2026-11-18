import io
import json
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from ttgl.model_delegation.live_delegation import delegate


class LiveDelegationTests(unittest.TestCase):
    def fixture(self, d):
        config = {'task': {'task_id': 'new', 'allowed_write_paths': ['app.py']},
                  'worker_timeout_seconds': 20, 'integration_reserve_seconds': 10,
                  'source_home': '/private/source', 'image_review': {}, 'experiences': [],
                  'maximum_packet_bytes': 8000, 'worker_maximum_tool_calls': 4}
        bridge = SimpleNamespace(config={'delegation': config, 'repository_root': d},
            root=Path(d)/'bridge', container='ttgl-worker-'+'a'*24, deadline=time.time()+100)
        args = {'goal': 'repair public utility', 'subtask_type': 'implementation',
                'idempotency_key': 'one', 'allowed_write_paths': ['app.py']}
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as t:
            m = tarfile.TarInfo('app.py'); m.size = 5; m.mode = 0o666
            t.addfile(m, io.BytesIO(b'pass\n'))
        return bridge, args, buf.getvalue()

    def test_same_handoff_runs_once_and_integrates_only_verified_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            bridge, args, raw = self.fixture(d)
            selection = {'selected_model': 'gpt-6-luna', 'decision_id': 'decision'}
            def solve(**kwargs):
                (kwargs['source']/'app.py').write_text('answer = 1\n')
                return {'status': 'completed', 'native_usage': {'total_tokens': 123}, 'candidate_archive': {'id': 'artifact'}, 'model_report': {'complete': True}}
            with patch('ttgl.model_delegation.live_delegation.decision', return_value=selection), \
                 patch('ttgl.model_delegation.live_delegation.packet', return_value={}), \
                 patch('ttgl.model_delegation.live_delegation.docker', return_value=raw) as docker, \
                 patch('ttgl.model_delegation.episode.run_episode', side_effect=solve) as execute:
                args['allowed_write_paths'] = ['/testbed/app.py']
                result = delegate(bridge, args)
                self.assertEqual(result['status'], 'integrated_public_candidate')
                self.assertEqual(delegate(bridge, args), result)
                self.assertEqual(execute.call_count, 1)
                with self.assertRaises(ValueError): delegate(bridge, {**args, 'idempotency_key': 'two'})
                self.assertIn('umask 000', str(docker.call_args_list[-1]))

    def test_route_denial_invokes_no_worker(self):
        with tempfile.TemporaryDirectory() as d:
            bridge, args, _ = self.fixture(d)
            with patch('ttgl.model_delegation.live_delegation.decision', return_value={'selected_model': None, 'decision_id': 'd'}), \
                 patch('ttgl.model_delegation.episode.run_episode') as execute:
                self.assertEqual(delegate(bridge, args)['status'], 'needs_parent')
                execute.assert_not_called()

    def test_parent_scope_and_integration_reserve_enforced(self):
        with tempfile.TemporaryDirectory() as d:
            bridge, args, _ = self.fixture(d)
            with self.assertRaises(ValueError): delegate(bridge, {**args, 'allowed_write_paths': ['secret.py']})
            bridge.deadline = time.time()+25
            with patch('ttgl.model_delegation.live_delegation.decision', return_value={'selected_model': 'gpt-6-luna'}):
                with self.assertRaises(ValueError): delegate(bridge, args)

    def test_uncertain_worker_cannot_be_repeated(self):
        with tempfile.TemporaryDirectory() as d:
            bridge, args, raw = self.fixture(d)
            with patch('ttgl.model_delegation.live_delegation.decision', return_value={'selected_model': 'gpt-6-luna'}), \
                 patch('ttgl.model_delegation.live_delegation.packet', return_value={}), \
                 patch('ttgl.model_delegation.live_delegation.docker', return_value=raw), \
                 patch('ttgl.model_delegation.episode.run_episode', side_effect=RuntimeError('uncertain')) as execute:
                with self.assertRaises(RuntimeError): delegate(bridge, args)
                with self.assertRaises(ValueError): delegate(bridge, args)
                self.assertEqual(execute.call_count, 1)
