#!/usr/bin/env python3
"""Fixed-container MCP terminal for native teams; no orchestration or memory.

Reuses the already exercised stdio MCP envelope. Cross-process flock reserves a
single total tool budget. Each command has an immutable intent and output; an
uncertain invocation is never executed again. The actor cannot select a host
path, container, user or runtime. All inference remains inside native Codex.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

TOOL = dict(name='terminal', description='Run a shell command in the isolated repository at /task. Read source, edit implementation and run Python tests here. No network or package installation. Each command is recorded; exit status alone is not a correctness grade.',
    inputSchema=dict(type='object', properties=dict(command=dict(type='string'),
        timeout_seconds=dict(type='integer', minimum=1, maximum=180)), required=['command'], additionalProperties=False))


class Terminal:
    def __init__(self, config):
        self.config = json.loads(Path(config).read_text())
        self.root = Path(self.config['records'])
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.boot = uuid.uuid4().hex
        self.env = {k: v for k, v in os.environ.items() if k not in ('DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH')}

    def execute(self, request):
        args = request['params'].get('arguments') or {}
        command, timeout = args.get('command'), args.get('timeout_seconds', 180)
        if request['params'].get('name') != 'terminal' or set(args) - {'command', 'timeout_seconds'}:
            raise ValueError('Unknown tool/argument')
        if not isinstance(command, str) or not 0 < len(command) <= 60000 or type(timeout) is not int or not 1 <= timeout <= 180:
            raise ValueError('Invalid command or timeout')
        fingerprint = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        ident = self.boot + '-' + hashlib.sha256(json.dumps(request['id']).encode()).hexdigest()[:24]
        intent, result = self.root / (ident + '.intent.json'), self.root / (ident + '.result.json')
        if intent.exists():
            if json.loads(intent.read_text())['request_sha256'] != fingerprint:
                raise RuntimeError('RPC identity collision')
            if result.exists():
                return json.loads(result.read_text())
            raise RuntimeError('Prior command started or uncertain; never re-executed')
        with (self.root / 'budget.lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            count = len(list(self.root.glob('*.intent.json')))
            if count >= self.config['tool_budget'] or time.time_ns() >= self.config['close_at_ns']:
                return dict(tools_closed=True, instruction='Return your current evidence-backed final status. Do not retry tools.', task_success_inferred=False)
            with intent.open('x') as stream:
                json.dump(dict(at_ns=time.time_ns(), request_sha256=fingerprint, command=command, timeout_seconds=timeout, ordinal=count+1), stream)
        start = time.perf_counter()
        stdout, stderr = self.root / (ident + '.stdout'), self.root / (ident + '.stderr')
        cmd = ['docker', '--host=unix:///var/run/docker.sock', 'exec', '--user', '1000:1000',
            self.config['container'], 'timeout', '-s', 'TERM', '-k', '3', str(timeout), '/bin/sh', '-c', command]
        with stdout.open('xb') as out, stderr.open('xb') as err:
            process = subprocess.run(cmd, env=self.env, stdout=out, stderr=err, timeout=timeout+15)
        value = dict(id=ident, exit_code=process.returncode, seconds=time.perf_counter()-start,
            stdout=stdout.read_text(errors='replace')[:16000], stderr=stderr.read_text(errors='replace')[:4000],
            stdout_bytes=stdout.stat().st_size, stderr_bytes=stderr.stat().st_size,
            stdout_sha256=hashlib.sha256(stdout.read_bytes()).hexdigest(), stderr_sha256=hashlib.sha256(stderr.read_bytes()).hexdigest())
        with result.open('x') as stream:
            json.dump(value, stream)
        return value

    def handle(self, request):
        method = request.get('method')
        if method == 'initialize':
            return dict(protocolVersion=request.get('params', {}).get('protocolVersion', '2025-06-18'),
                capabilities=dict(tools={}), serverInfo=dict(name='ttgl-fixed-container-terminal', version='1'))
        if method == 'ping':
            return {}
        if method == 'tools/list':
            return dict(tools=[TOOL])
        if method == 'tools/call':
            try:
                return dict(content=[dict(type='text', text=json.dumps(self.execute(request)))], isError=False)
            except Exception as error:
                return dict(content=[dict(type='text', text=repr(error))], isError=True)
        raise ValueError('Unsupported method')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    os.umask(0o077)
    terminal = Terminal(parser.parse_args().config)
    for line in sys.stdin:
        try:
            if len(line) > 1024*1024:
                raise ValueError('Oversize request')
            request = json.loads(line)
            if 'id' not in request:
                continue
            response = dict(jsonrpc='2.0', id=request['id'], result=terminal.handle(request))
        except Exception as error:
            response = dict(jsonrpc='2.0', id=request.get('id') if isinstance(locals().get('request'), dict) else None,
                error=dict(code=-32603, message=repr(error)))
        print(json.dumps(response), flush=True)
