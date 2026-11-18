import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from ttgl.model_delegation.transport import SubscriptionBackend, ActorSubscriptionBackend
from ttgl.model_delegation.worker_bridge import Bridge, run
from ttgl.personal import Request


class TransportTests(unittest.TestCase):
    def test_named_provider_preserves_subscription_and_zero_retries(self):
        b = object.__new__(SubscriptionBackend)
        b.executable = '/codex'
        r = Request('id', 'gpt-6-luna', 'q', 'q', Path('/tmp'), {}, 20, read_only=True)
        command = b.command(r, '/schema.json')
        configs = [command[i+1] for i, x in enumerate(command) if x == '--config']
        self.assertFalse(any(c.startswith('model_providers.openai.') for c in configs))
        self.assertIn('model_providers.observatory_subscription.request_max_retries=0', configs)
        self.assertIn('model_providers.observatory_subscription.stream_max_retries=0', configs)
        self.assertIn('forced_login_method="chatgpt"', configs)
        self.assertIn('model_providers.observatory_subscription.base_url="https://chatgpt.com/backend-api/codex"', configs)
        self.assertEqual(command[-1], '-')

    def test_actor_uses_only_host_frozen_python_bridge(self):
        b = object.__new__(ActorSubscriptionBackend)
        b.executable = '/codex'
        b.node_executable = '/python'
        b.container = 'ttgl-worker-'+'a'*24
        b.bridge_config = '/private/bridge.json'
        r = Request('id', 'gpt-6-luna', 'q', 'q', Path('/tmp'), {}, 20)
        with patch('ttgl.experience_routing.io.read', return_value={}):
            cmd = b.command(r, '/schema.json')
        joined = '\n'.join(cmd)
        self.assertIn('ttgl.model_delegation.worker_bridge', joined)
        self.assertNotIn('server.mjs', joined)
        self.assertIn('mcp_servers.worker.required=true', joined)
        self.assertIn('"deny"', joined)
        with patch('ttgl.experience_routing.io.read', return_value={'delegation': True}):
            delegated = '\n'.join(b.command(r, '/schema.json'))
        for tool in ('shell', 'route_subtask', 'delegate_subtask'):
            self.assertIn('mcp_servers.worker.tools.'+tool+'.approval_mode="approve"', delegated)

    def config(self, root):
        p = Path(root)/'config.json'
        p.write_text(json.dumps({'container': 'ttgl-worker-'+'a'*24, 'output': str(Path(root)/'bridge'),
            'repository_root': root, 'deadline_epoch': time.time()+300, 'maximum_tool_calls': 3}))
        return p

    def test_bridge_input_validation_and_idempotency(self):
        with tempfile.TemporaryDirectory() as d, patch('ttgl.model_delegation.worker_bridge.LocalS3Retention') as archive, \
             patch('ttgl.model_delegation.worker_bridge.subprocess.run') as execute:
            archive.return_value.retain_file.return_value = {'sha256': 'x'}
            execute.return_value.returncode = 0
            b = Bridge(self.config(d))
            a = {'command': 'true', 'timeout_seconds': 1}
            self.assertEqual(b.call(1, a), b.call(1, a))
            self.assertEqual(execute.call_count, 1)
            with self.assertRaises(ValueError): b.call(1, {'command': 'other'})
            with self.assertRaises(ValueError): b.call(2, {'command': 'x', 'container': 'other'})
            with self.assertRaises(ValueError): b.call(2, {'command': 'x', 'timeout_seconds': True})

    def test_incomplete_bridge_attempt_never_reexecutes(self):
        from ttgl.experience_routing.io import write_new, digest
        with tempfile.TemporaryDirectory() as d, patch('ttgl.model_delegation.worker_bridge.LocalS3Retention'), \
             patch('ttgl.model_delegation.worker_bridge.subprocess.run') as execute:
            b = Bridge(self.config(d))
            write_new(b.root/digest(1)/'started.json', {'arguments': {'command': 'true'}})
            with self.assertRaises(FileNotFoundError): b.call(1, {'command': 'true'})
            execute.assert_not_called()

    def test_retention_failure_blocks_command(self):
        with tempfile.TemporaryDirectory() as d, patch('ttgl.model_delegation.worker_bridge.LocalS3Retention') as archive, \
             patch('ttgl.model_delegation.worker_bridge.subprocess.run') as execute:
            archive.return_value.retain_file.side_effect = RuntimeError('archival unavailable')
            b = Bridge(self.config(d))
            with self.assertRaises(RuntimeError): b.call(1, {'command': 'true'})
            execute.assert_not_called()
