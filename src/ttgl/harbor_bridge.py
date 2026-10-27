"""Host-side transport to one maintained Harbor environment; no evaluator access.

The bridge keeps Codex authentication on the host. Only environment.exec receives
model shell commands. This module does not provision, grade, or call a model.
"""
from __future__ import annotations

import asyncio
import contextvars
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import shlex
import threading
import time

from . import benchmark, personal, policy
from .isolated import ContainerBackend

SERVER = Path(__file__).resolve().parents[2]/'tools/worker-mcp/harbor-server.mjs'


class EnvironmentBridge:
    """Expose one already-created environment to a bounded authenticated tool."""

    def __init__(self, environment, repository: str, trace: Path):
        if not repository.startswith('/') or '\n' in repository:
            raise ValueError('Require an absolute environment repository path')
        self.environment, self.repository, self.trace = environment, repository, Path(trace)
        self.token = secrets.token_hex(32)
        self.lock = threading.Lock()
        self.sequence = 0
        self.active_request = {}

    def start(self):
        self.loop = asyncio.get_running_loop()
        # Harbor binds phase/network policy and runtime identity to context.
        # HTTP handler threads must not schedule agent work as setup work.
        self.execution_context = contextvars.copy_context()
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # Never log authorization headers.

            def do_POST(self):
                if self.path != '/shell' or not secrets.compare_digest(
                        self.headers.get('Authorization', ''), 'Bearer '+bridge.token):
                    self.send_error(403)
                    return
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 210000:
                        raise ValueError('Invalid request length')
                    request = json.loads(self.rfile.read(length))
                    command, timeout = request['command'], request['timeout_seconds']
                    if (not isinstance(command, str) or not 0 < len(command) <= 50000
                            or type(timeout) is not int or not 1 <= timeout <= 120):
                        raise ValueError('Invalid shell request')
                except (ValueError, KeyError, TypeError):
                    self.send_error(400)
                    return
                future = bridge.execution_context.copy().run(
                    asyncio.run_coroutine_threadsafe, bridge.execute(command, timeout), bridge.loop)
                try:
                    result = future.result(timeout=timeout+10)
                    body = json.dumps(result).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except Exception:
                    future.cancel()
                    self.send_error(502)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    async def execute(self, command, timeout):
        identity = dict(self.active_request)
        with self.lock:
            self.sequence += 1
            sequence = self.sequence
        self.record({**identity, 'event': 'tool_request', 'sequence': sequence, 'command': command,
                     'timeout_seconds': timeout})
        try:
            result = await self.environment.exec(
                command=f'cd {shlex.quote(self.repository)} && timeout --signal=KILL {timeout} bash -lc {shlex.quote(command)}',
                timeout_sec=timeout+5)
            response = {'exit_code': result.return_code,
                        'stdout': (result.stdout or '')[-40000:],
                        'stderr': (result.stderr or '')[-10000:]}
            self.record({**identity, 'event': 'tool_response', 'sequence': sequence, **response})
            return response
        except BaseException as exc:
            self.record({**identity, 'event': 'tool_error', 'sequence': sequence, 'error_type': type(exc).__name__})
            raise

    def record(self, event):
        with self.lock:
            self.trace.parent.mkdir(parents=True, exist_ok=True)
            with self.trace.open('a') as stream:
                stream.write(json.dumps({'epoch': time.time(), 'schema': 'visible-harbor-tool-v1', **event})+'\n')

    async def close(self):
        await asyncio.to_thread(self.server.shutdown)
        self.server.server_close()
        self.thread.join(timeout=2)


class HarborBackend(ContainerBackend):
    def __init__(self, bridge, *, mode='fallback', audit_root: Path, executable='codex'):
        super().__init__(executable)
        if mode not in policy.MODES:
            raise ValueError('Unknown policy')
        self.bridge, self.mode, self.audit_root = bridge, mode, Path(audit_root)
        self.container = 'harbor-environment-transport'  # Enables the inherited MCP-only command path.
        self.policy_identity = {'mode': mode, 'source': benchmark.digest(Path(policy.__file__)),
                                'prompts': {p.name: benchmark.digest(p) for p in policy.PROMPTS.glob('controller-v2-*.txt')}}

    def describe(self):
        description = super().describe()
        description.pop('worker_dependencies_sha256', None)
        return {**description, 'worker_tools': 'One Harbor environment.exec via authenticated loopback MCP',
                'server_sha256': benchmark.digest(SERVER),
                'harbor_bridge_sha256': benchmark.digest(Path(__file__)),
                'controller_policy': self.policy_identity,
                'visible_tool_trace': 'Bounded public tool actions/observations; no private reasoning or evaluator feedback'}

    def command(self, request, schema_path):
        command = super().command(request, schema_path)
        matches = [i for i, part in enumerate(command) if part.startswith('mcp_servers.worker.args=')]
        if request.read_only:
            if matches:
                raise ValueError('Context-only role has worker access')
        else:
            if len(matches) != 1:
                raise ValueError('Unexpected parent MCP command contract')
            command[matches[0]] = 'mcp_servers.worker.args='+json.dumps(
                [str(SERVER), str(self.bridge.port), self.bridge.token])
        return command

    def complete(self, request):
        current = {'mode': self.mode, 'source': benchmark.digest(Path(policy.__file__)),
                   'prompts': {p.name: benchmark.digest(p) for p in policy.PROMPTS.glob('controller-v2-*.txt')}}
        if current != self.policy_identity:
            raise ValueError('Policy changed during execution')
        prompt = policy.policy_prompt(request, self.mode)
        if not request.read_only:
            prompt += '\nUse only the worker shell MCP tool for repository work. Its repository is '+self.bridge.repository+' inside the assigned Harbor environment; the host workspace is empty. Network access is governed by the benchmark environment.'
        benchmark.write_new(self.audit_root/(personal._digest(request.request_id)+'.json'),
                            {'request_id': request.request_id, 'kind': request.kind, 'prompt': prompt,
                             'policy': self.policy_identity})
        if not request.read_only:
            self.bridge.active_request = {'request_id': request.request_id, 'model': request.model,
                                          'kind': request.kind}
        try:
            return personal.CodexBackend.complete(self, replace(request, prompt=prompt))
        finally:
            if not request.read_only:
                self.bridge.active_request = {}
