"""Source-bound Codex execution and a Docker-free, offline task workspace."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

from ..experience_routing.backend import NativeCallFailure, source_binding
from ..experience_routing.io import digest, file_digest, now, read, write_new
from ..experience_routing.ledger import UsageLedger
from ..model_delegation.retention import LocalS3Retention
from ..model_delegation.transport import SubscriptionBackend
from ..model_delegation.worker_bridge import TOOL
from ..personal import Request

MODEL = 'gpt-6-luna'
MAX_FILE_BYTES = 256 * 1024
MAX_OUTPUT_BYTES = 256 * 1024
MAX_TOOL_CALLS = 20
CALL_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}\Z')
FILENAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}\Z')
STAGES = {'smoke', 'historical', 'optimization', 'heldout', 'baseline'}


class AmbiguousInvocation(RuntimeError):
    """The invocation was admitted and cannot be automatically repeated."""


def run_sandbox(workspace, command, *, timeout, read_only=False, input_data=None, protected=()):
    """Execute only in the given workspace, with offline PID and user namespaces."""
    workspace = Path(workspace).resolve(strict=True)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Sandbox timeout must be finite and positive')
    outer = [
        '/usr/bin/bwrap', '--unshare-user', '--unshare-ipc', '--unshare-pid',
        '--unshare-net', '--unshare-uts', '--disable-userns', '--new-session',
        '--die-with-parent', '--clearenv', '--ro-bind', '/usr/bin', '/usr/bin',
        '--ro-bind', '/usr/lib', '/usr/lib', '--ro-bind', '/usr/lib64', '/usr/lib64',
        '--symlink', 'usr/bin', '/bin', '--symlink', 'usr/lib', '/lib',
        '--symlink', 'usr/lib64', '/lib64', '--proc', '/proc', '--dev', '/dev',
        '--size', str(16 * 1024 * 1024), '--tmpfs', '/tmp',
        '--ro-bind' if read_only else '--bind', str(workspace), '/testbed',
        '--chdir', '/testbed', '--setenv', 'HOME', '/tmp', '--setenv', 'PATH', '/usr/bin:/bin',
        '--setenv', 'LC_ALL', 'C', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1',
    ]
    for name in protected:
        if name != '.git' and not FILENAME.fullmatch(name):
            raise ValueError('Invalid protected workspace file')
        path = workspace / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Protected workspace file changed')
        # Git metadata belongs to the trusted host, including its private path.
        outer += ['--ro-bind', '/dev/null' if name == '.git' else str(path), '/testbed/' + name]
    outer += [
        '--', '/usr/bin/prlimit', '--core=0', '--nofile=128', '--nproc=512',
        '--as=1073741824', '--fsize=' + str(MAX_OUTPUT_BYTES),
        '--cpu=' + str(max(1, math.ceil(timeout))), '--', *command,
    ]
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(outer, stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            process.communicate(input_data, timeout=timeout)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
        stdout.seek(0)
        stderr.seek(0)
        return subprocess.CompletedProcess(command, process.returncode, stdout.read(), stderr.read())


def qualify_sandbox(workspace):
    """Check the real boundary without contacting the model service."""
    script = '''import errno, os, socket
assert os.getcwd() == '/testbed'
assert set(os.listdir('/')) == {'bin', 'dev', 'lib', 'lib64', 'proc', 'testbed', 'tmp', 'usr'}
assert not any(os.path.exists(path) for path in ('/home', '/workspaces', '/root', '/etc'))
assert not any(key in os.environ for key in ('CODEX_HOME', 'OPENAI_API_KEY', 'PYTHONPATH', 'HTTPS_PROXY'))
with socket.socket() as connection:
    connection.settimeout(1)
    assert connection.connect_ex(('1.1.1.1', 53)) == errno.ENETUNREACH
'''
    result = run_sandbox(workspace, ['/usr/bin/python3', '-I', '-B', '-c', script], timeout=15)
    if result.returncode:
        raise RuntimeError('Offline actor boundary did not qualify')


def _regular_bytes(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_FILE_BYTES:
            raise ValueError('Candidate must be a bounded regular file')
        return stream.read(MAX_FILE_BYTES + 1)


def _git(cwd, *args):
    environment = {
        'PATH': '/usr/bin:/bin', 'HOME': str(cwd), 'GIT_CONFIG_NOSYSTEM': '1',
        'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_AUTHOR_NAME': 'Observatory',
        'GIT_AUTHOR_EMAIL': 'observatory@localhost', 'GIT_COMMITTER_NAME': 'Observatory',
        'GIT_COMMITTER_EMAIL': 'observatory@localhost', 'GIT_AUTHOR_DATE': '2026-11-20T00:00:00Z',
        'GIT_COMMITTER_DATE': '2026-11-20T00:00:00Z', 'LC_ALL': 'C',
    }
    return subprocess.run(['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', *args], cwd=cwd,
                          env=environment, check=True, capture_output=True, timeout=20).stdout


def _worktree(root, files):
    seed = root / 'seed'
    seed.mkdir(mode=0o700)
    _git(seed, 'init', '--quiet', '--template=')
    for name, value in files.items():
        (seed / name).write_text(value, encoding='utf-8')
    _git(seed, 'add', '--', *files)
    _git(seed, 'commit', '--quiet', '-m', 'Frozen public workspace')
    worktree = root / 'task'
    _git(seed, 'worktree', 'add', '--quiet', '--detach', str(worktree))
    return worktree, _git(seed, 'rev-parse', 'HEAD').decode().strip()


def _actor_command(config, ident, arguments):
    if not isinstance(arguments, dict) or set(arguments) - {'command', 'timeout_seconds'}:
        raise ValueError('Invalid shell argument shape')
    command = arguments.get('command')
    timeout = arguments.get('timeout_seconds', 15)
    if not isinstance(command, str) or not 0 < len(command) <= 50000 or '\x00' in command:
        raise ValueError('Invalid shell command')
    if type(timeout) is not int or not 1 <= timeout <= 30:
        raise ValueError('Tool timeout must be an integer from 1 through 30 seconds')
    folder = Path(config['spool']) / digest(ident)
    started = folder / 'started.json'
    result = folder / 'result.json'
    if started.exists():
        if read(started)['arguments'] != arguments or not result.exists():
            raise ValueError('Conflicting or incomplete tool receipt')
        return read(result)
    if len(list(folder.parent.glob('*/started.json'))) >= MAX_TOOL_CALLS:
        raise ValueError('Tool call budget exhausted')
    remaining = config['deadline'] - time.monotonic() - 4
    if remaining < 1:
        raise ValueError('Tool deadline exhausted')
    actual_timeout = min(timeout, remaining)
    write_new(started, {'arguments': arguments, 'started_at': now(), 'timeout_seconds': actual_timeout})
    start_time = time.monotonic()
    try:
        process = run_sandbox(config['workspace'], ['/bin/sh', '-c', command], timeout=actual_timeout,
                              protected=config['protected'])
        stdout, stderr, code = process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired:
        # This is an observed tool deadline. Any model follow-up is retained by the caller.
        stdout, stderr, code = b'', b'', None
    for label, content in (('stdout.bin', stdout), ('stderr.bin', stderr)):
        with (folder / label).open('xb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    value = {
        'exit_code': code, 'timed_out': code is None,
        'stdout': stdout[-20000:].decode(errors='replace'), 'stderr': stderr[-6000:].decode(errors='replace'),
        'output_may_be_clipped': len(stdout) > 20000 or len(stderr) > 6000,
        'command_runtime_seconds': time.monotonic() - start_time,
    }
    write_new(result, value)
    return value


def _bridge(config, source, sink):
    shell_tool = {**TOOL, 'inputSchema': {**TOOL['inputSchema'], 'properties': {
        **TOOL['inputSchema']['properties'], 'timeout_seconds': {'type': 'integer', 'minimum': 1, 'maximum': 30}}}}
    for line in source:
        ident = None
        try:
            if len(line.encode()) > 100000:
                raise ValueError('Oversized JSON-RPC request')
            request = json.loads(line)
            if request.get('jsonrpc') != '2.0':
                raise ValueError('Bad JSON-RPC version')
            if 'id' not in request:
                continue
            ident, method = request['id'], request['method']
            params = request.get('params', {})
            if method == 'initialize':
                result = {'protocolVersion': params.get('protocolVersion', '2025-06-18'),
                          'capabilities': {'tools': {}}, 'serverInfo': {'name': 'observatory-sim-actor', 'version': '1'}}
            elif method == 'ping':
                result = {}
            elif method == 'tools/list':
                result = {'tools': [shell_tool]}
            elif method == 'tools/call' and params.get('name') == 'shell':
                try:
                    value = _actor_command(config, ident, params.get('arguments', {}))
                    result = {'content': [{'type': 'text', 'text': json.dumps(value)}], 'isError': value['timed_out']}
                except (ValueError, OSError) as error:
                    result = {'content': [{'type': 'text', 'text': type(error).__name__}], 'isError': True}
            else:
                raise ValueError('Unsupported actor method')
            response = {'jsonrpc': '2.0', 'id': ident, 'result': result}
        except (ValueError, TypeError, KeyError, AttributeError):
            response = {'jsonrpc': '2.0', 'id': ident, 'error': {'code': -32602, 'message': 'Invalid actor request'}}
        sink.write(json.dumps(response) + '\n')
        sink.flush()


class _SandboxSubscriptionBackend(SubscriptionBackend):
    def __init__(self, *, bridge_config, **kwargs):
        # The inherited request builder requires a worker command for writable
        # requests. Replace its Node worker with the installed Python actor.
        super().__init__(container='sim-isolated-workspace' if bridge_config else None,
                         node_executable=sys.executable, **kwargs)
        self.bridge_config = bridge_config

    def preflight(self, request):
        if request.thread_id is not None or request.model != MODEL:
            raise ValueError('Fresh matched Luna invocation required')
        if file_digest(self.executable) != self.executable_sha256 or source_binding(self.binding['codex_home']) != self.binding:
            raise ValueError('Native executable/source identity drift')
        if request.read_only == bool(self.bridge_config):
            raise ValueError('Native tool boundary does not match invocation role')

    def command(self, request, schema):
        inherited = iter(super().command(request, schema))
        command = []
        for item in inherited:
            if item == '--config':
                setting = next(inherited)
                if setting.startswith(('mcp_servers.worker.command=', 'mcp_servers.worker.args=',
                                       'mcp_servers.worker.tool_timeout_sec=')):
                    continue
                command += [item, setting]
            else:
                command.append(item)
        assert command.pop() == '-'
        for feature in ('apply_patch_freeform', 'goals'):
            command += ['--disable', feature]
        if self.bridge_config:
            settings = {
                'mcp_servers.worker.command': sys.executable,
                'mcp_servers.worker.args': ['-m', 'ttgl.sim_ablation.runtime', '--bridge', str(self.bridge_config)],
                'mcp_servers.worker.required': True,
                'mcp_servers.worker.tool_timeout_sec': 35,
            }
            for key, value in settings.items():
                command += ['--config', key + '=' + json.dumps(value)]
            source = json.dumps(str(Path(__file__).resolve().parents[2]))
            command += ['--config', 'mcp_servers.worker.env={"PYTHONPATH"=' + source + '}']
        else:
            # Keep native rollouts during optimizer calls too. The isolated
            # client home is fresh and unmounted from the actor.
            command.remove('--ephemeral')
        return command + ['-']


class NativeRuntime:
    """Run independent Luna calls with exact input receipts and no retry."""

    def __init__(self, repository, output, *, source_home=None, effort='low', timeout_seconds=120,
                 rates=None, retention=None):
        self.repository = Path(repository).resolve(strict=True)
        self.output = Path(output).resolve()
        self.output.mkdir(parents=True, exist_ok=True, mode=0o700)
        if effort not in {'low', 'medium', 'high'} or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 600:
            raise ValueError('Unsupported reasoner effort or model-call deadline')
        self.effort, self.timeout_seconds = effort, timeout_seconds
        executable = shutil.which('codex')
        if not executable:
            raise ValueError('A preinstalled native Codex CLI is required')
        self.executable = str(Path(executable).resolve(strict=True))
        self.codex_sha256 = file_digest(self.executable)
        self.version = subprocess.check_output([self.executable, '--version'], timeout=15, text=True).strip()
        self.binding = source_binding(source_home or os.environ.get('CODEX_HOME') or Path.home() / '.codex')
        self.rates = rates or {}
        self.retention = retention if retention is not None else LocalS3Retention(self.repository, self.output / 'retention')

    def invoke(self, call_id, *, prompt, schema, files=None, editable=None, stage='optimization'):
        if not isinstance(call_id, str) or not CALL_ID.fullmatch(call_id) or stage not in STAGES:
            raise ValueError('Unknown or unsafe native invocation identity')
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode()) > 100000 or not isinstance(schema, dict):
            raise ValueError('Invalid native prompt or output schema')
        if files is not None:
            if (not isinstance(files, dict) or not 0 < len(files) <= 20 or editable not in files
                    or any(not FILENAME.fullmatch(name) or not isinstance(value, str) or len(value.encode()) > MAX_FILE_BYTES
                           for name, value in files.items())):
                raise ValueError('A bounded public roster and editable path are required')
        elif editable is not None:
            raise ValueError('An editable path requires a public roster')
        folder = self.output / 'invocations' / call_id
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (folder / 'lock').open('ab') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise AmbiguousInvocation(f'{call_id}: invocation already active') from error
            return self._invoke(folder, call_id, prompt=prompt, schema=schema, files=files, editable=editable, stage=stage)

    def _invoke(self, folder, call_id, *, prompt, schema, files, editable, stage):
        identity = {
            'call_id': call_id, 'stage': stage, 'model': MODEL, 'effort': self.effort,
            'timeout_seconds': self.timeout_seconds, 'codex_version': self.version, 'codex_sha256': self.codex_sha256,
            'source_account_hash': self.binding['account_hash'], 'prompt_sha256': digest(prompt.encode()),
            'prompt_bytes': len(prompt.encode()), 'schema_sha256': digest(schema),
            'public_roster_sha256': digest(files), 'editable': editable, 'rates': self.rates, 'automatic_retries': 0,
        }
        pending, started, completed = (folder / (name + '.json') for name in ('pending', 'started', 'completed'))
        if pending.exists() and read(pending) != identity:
            raise ValueError(f'{call_id}: immutable invocation identity changed')
        if completed.exists():
            return read(completed)
        if started.exists():
            raise AmbiguousInvocation(f'{call_id}: admitted invocation has no terminal receipt')
        if not pending.exists():
            write_new(pending, identity)
        # This exact local S3 read-back gate runs before the admission marker.
        self.retention.retain_file(pending, kind='sim-invocation-registration', identity=call_id)
        with tempfile.TemporaryDirectory(prefix='observatory-sim-') as temporary:
            isolated = Path(temporary)
            workspace = isolated / 'client-workspace'
            workspace.mkdir(mode=0o700)
            bridge_config = worktree = base = None
            if files is not None:
                qualify_sandbox(workspace)
                worktree, base = _worktree(isolated, files)
                bridge_config = isolated / 'actor.json'
                write_new(bridge_config, {'workspace': str(worktree), 'spool': str(folder / 'actor-spool'),
                          'protected': ['.git', *(name for name in files if name != editable)],
                          'deadline': time.monotonic() + self.timeout_seconds})
            backend = _SandboxSubscriptionBackend(executable=self.executable, executable_sha256=self.codex_sha256,
                source_home=self.binding['codex_home'], source_account_hash=self.binding['account_hash'],
                output=folder / 'native', client=self.retention, bridge_config=bridge_config)
            request = Request(call_id, MODEL, stage, prompt, workspace, schema, self.timeout_seconds,
                              read_only=worktree is None, reasoning_effort=self.effort)
            backend.preflight(request)
            write_new(started, {'started_at': now(), 'identity_sha256': digest(identity), 'base_commit': base})
            try:
                response = backend.complete(request)
            except NativeCallFailure as error:
                response = error.response
            measurement = self._record_usage(request, response, backend, stage)
            first_input = _first_input_tokens(folder / 'native' / call_id / 'client-home', response.thread_id)
            candidate, integrity, diff = _candidate(worktree, files, editable)
            tool_summary = self._retain_tools(folder, call_id)
            wire_prompt = folder / 'native' / call_id / 'prompt.txt'
            result = {
                **identity, 'status': response.status, 'error_type': response.error_type,
                'answer': _decode_answer(response.text), 'candidate': candidate, 'candidate_integrity': integrity,
                'candidate_sha256': None if candidate is None else digest(candidate.encode()),
                'git_diff': diff, 'base_commit': base, 'thread_id': response.thread_id,
                'usage': measurement['delta'], 'usage_evidence': measurement['usage_evidence'],
                'first_request_input_tokens': first_input,
                'usage_issues': measurement['accounting_issues'], 'scenario_cost': measurement['scenario_cost'],
                'actual_cash': measurement['actual_cash'], 'provider_estimate': measurement['provider_estimate'],
                'elapsed_seconds': response.elapsed_seconds, 'events_ref': backend.artifacts.get('events.jsonl'),
                'events_sha256': backend.last_native_artifact_hash, 'rollout_refs': backend.rollout_artifacts,
                'native_stdout_metering_scope': response.usage_scope, 'tool_count': len(response.tool_events),
                'actor_tool_calls': len(tool_summary), 'tool_summary': tool_summary, 'finished_at': now(),
                'wire_prompt_sha256': file_digest(wire_prompt), 'wire_prompt_bytes': wire_prompt.stat().st_size,
            }
            write_new(folder / 'parsed-response.json', asdict(response))
            self.retention.retain_file(folder / 'parsed-response.json', kind='sim-parsed-response', identity=call_id)
            write_new(completed, result)
            return result

    def _record_usage(self, request, response, backend, stage):
        purpose = 'seed_construction' if stage == 'historical' else 'research_measurement'
        role = 'small_execution' if not request.read_only else 'planning'
        with (self.output / 'usage.lock').open('ab') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            ledger = UsageLedger(self.output / 'accounting', self.rates)
            return ledger.record(request, response, role, purpose, backend.last_native_artifact_hash,
                                 response_ids=backend.last_response_ids)

    def _retain_tools(self, folder, call_id):
        tool_summary = []
        for operation in sorted((folder / 'actor-spool').glob('*/started.json'), key=lambda path: path.stat().st_mtime_ns):
            records = (operation, operation.with_name('stdout.bin'), operation.with_name('stderr.bin'),
                       operation.with_name('result.json'))
            refs = [self.retention.retain_file(record, kind='sim-actor-' + record.name,
                    identity=call_id + ':' + record.parent.name) for record in records if record.is_file()]
            receipt = read(records[-1]) if records[-1].exists() else {'exit_code': None, 'timed_out': None}
            tool_summary.append({'exit_code': receipt['exit_code'], 'timed_out': receipt['timed_out'],
                                 'command_runtime_seconds': receipt.get('command_runtime_seconds'), 'retained_refs': refs})
        return tool_summary


def _decode_answer(text):
    try:
        return json.loads(text) if text else None
    except (TypeError, ValueError):
        return None


def _first_input_tokens(home, thread_id):
    """Use the first observed provider response in the fresh native root thread."""
    if not thread_id:
        return None
    for path in sorted((home / 'sessions').rglob('*.jsonl')):
        with path.open() as lines:
            for line in lines:
                try:
                    record = json.loads(line)
                    payload = record['payload']
                    if (record['type'] != 'token_usage_record' or payload.get('thread_id') != thread_id
                            or not payload.get('response_id')):
                        continue
                    tokens = payload['usage']['input_tokens']
                    return tokens if type(tokens) is int and tokens > 0 else None
                except (KeyError, TypeError, ValueError, AttributeError):
                    continue
    return None


def _candidate(worktree, files, editable):
    if worktree is None:
        return None, None, None
    if set(path.name for path in worktree.iterdir()) != {'.git', *files}:
        return None, False, None
    try:
        protected_unchanged = all(_regular_bytes(worktree / name) == value.encode()
                                  for name, value in files.items() if name != editable)
        if not protected_unchanged:
            return None, False, None
        content = _regular_bytes(worktree / editable).decode('utf-8')
        changes = _git(worktree, 'diff', '--no-ext-diff', '--binary', 'HEAD', '--', editable).decode()
        return content, True, changes
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
        return None, False, None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the host-owned offline SIM worker MCP')
    parser.add_argument('--bridge', type=Path, required=True)
    _bridge(read(parser.parse_args().bridge), sys.stdin, sys.stdout)
