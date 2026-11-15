"""Exercise the actual server and hook entry points with disposable private state."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent


class WorkspaceServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.origin = f'http://127.0.0.1:{self.port}'
        self.process = None
        self.addCleanup(self.stop)
        self.start()

    def start(self):
        self.process = subprocess.Popen(
            [sys.executable, str(HERE / 'workspace.py'), '--data', str(self.data),
             '--codex-root', str(self.root / 'empty-codex'), '--port', str(self.port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.fail(f'Workspace exited during startup: {self.process.returncode}')
            try:
                self.assertEqual(self.get('/api/health'), {'status': 'OK'})
                return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(.05)
        self.fail('Workspace did not become healthy')

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)

    def get(self, path):
        with urllib.request.urlopen(self.origin + path, timeout=2) as response:
            return json.load(response)

    def post(self, path, values, machine=False):
        headers = {'Content-Type': 'application/json'}
        if machine:
            headers['Authorization'] = 'Bearer ' + (self.data / 'steering-token').read_text()
        else:
            headers['Origin'] = self.origin
        request = urllib.request.Request(self.origin + path, json.dumps(values).encode(), headers)
        with urllib.request.urlopen(request, timeout=2) as response:
            return json.load(response)

    def cli(self, payload, url=None):
        return subprocess.run(
            [sys.executable, str(HERE / 'steering_hook.py'), 'send', '--data', str(self.data),
             '--url', url or self.origin], input=json.dumps(payload),
            text=True, capture_output=True, timeout=4)

    def test_fresh_checkout_serves_all_pages_and_native_assets(self):
        for path in ('/', '/live', '/live/rules', '/impact', '/outcomes', '/suggestions', '/process', '/agents', '/timeline', '/costs', '/tools', '/tasks/fixture', '/tasks', '/overview'):
            with self.subTest(path=path), urllib.request.urlopen(self.origin + path) as response:
                self.assertIn(b'workspace.js', response.read())
                self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
        for path in ('/workspace.js', '/ui.js', '/collection.js', '/optimization.js', '/optimization.css', '/activity-views.js', '/activity-views.css', '/usage-views.js', '/usage-views.css', '/task-report.js', '/dashboard-views.js'):
            with self.subTest(asset=path), urllib.request.urlopen(self.origin + path) as response:
                self.assertEqual(response.status, 200)
                self.assertGreater(len(response.read()), 0)
        self.assertEqual(len(self.get('/api/steering')['rules']), 11)
        self.assertEqual(self.get('/api/optimization')['coverage']['events'], 0)
        for view in ('process','agents','timeline','outcomes'):
            self.assertEqual(self.get('/api/analysis-pages?view='+view)['source_events'],0)
        for view in ('costs','tools'):
            self.assertEqual(self.get('/api/usage-pages?view='+view)['view'],view)
        for view in ('overview','taskactivity'):
            self.assertEqual(self.get('/api/activity-dashboard?view='+view)['counts']['turns'],0)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get('/missing-page')
        self.assertEqual(error.exception.code, 404)

    def test_rule_note_token_and_duplicate_receipts_survive_restart(self):
        original_token = (self.data / 'steering-token').read_text()
        self.assertEqual((self.data / 'steering-token').stat().st_mode & 0o777, 0o600)
        self.post('/api/steering-rule', {'name': 'Restart rule', 'kind': 'command', 'mode': 'block',
                  'message': 'Inspect this call', 'config': {'pattern': 'release', 'tool': 'Bash'}})
        self.post('/api/steering-hook', {'session_id': 'persisted', 'event_id': 'start', 'event': 'start'}, True)
        self.post('/api/live-control', {'session_id': 'persisted', 'note': 'Persist this note'})
        self.stop()
        self.start()
        self.assertEqual((self.data / 'steering-token').read_text(), original_token)
        self.assertEqual(self.get('/api/steering')['sessions'][0]['pending_notes'], 1)
        raw = {'hook_event_name': 'PreToolUse', 'session_id': 'persisted', 'tool_use_id': 'call-1',
               'tool_name': 'Bash', 'tool_input': {'command': 'release'}, 'cwd': '/repo'}
        first, replay = self.cli(raw), self.cli(raw)
        self.assertEqual((first.returncode, replay.returncode), (0, 0))
        output = json.loads(first.stdout)['hookSpecificOutput']
        self.assertEqual(output['permissionDecision'], 'deny')
        self.assertIn('Persist this note', output['permissionDecisionReason'])
        self.assertEqual(json.loads(first.stdout), json.loads(replay.stdout))
        state = self.get('/api/steering')
        self.assertEqual(state['sessions'][0]['pending_notes'], 0)
        self.assertEqual(len([r for r in state['log'] if r['rule_name'] == 'Session note']), 1)
        self.assertEqual(len([r for r in state['log'] if r['rule_name'] == 'Restart rule']), 1)

    def test_adapter_fails_open_without_echoing_invalid_or_private_input(self):
        for payload in ([], None, 'private input must not be echoed', {'hook_event_name': 'Unknown'}):
            with self.subTest(payload_type=type(payload).__name__):
                result = self.cli(payload)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertIn('TTGL advisory hook unavailable:', result.stderr)
                self.assertNotIn('private input', result.stderr)
        self.stop()
        result = self.cli({'session_id': 's', 'event_id': 'offline', 'event': 'start'})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertNotIn((self.data / 'steering-token').read_text(), result.stderr)


if __name__ == '__main__':
    unittest.main()
