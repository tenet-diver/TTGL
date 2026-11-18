"""One host-owned offline actor shell over the existing stdio MCP protocol.

No SDK download, arbitrary host command or container choice is exposed to models.
Exact inputs/results are retained in local S3 before returning derived output.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from ..experience_routing.io import digest, read, write_new
from .mcp import serve
from .retention import LocalS3Retention

TOOL = {'name': 'shell', 'description': 'Read/edit source and run public checks in your assigned offline /testbed. No host files, credentials, hidden grader or network are available.',
        'inputSchema': {'type': 'object', 'additionalProperties': False, 'required': ['command'],
                        'properties': {'command': {'type': 'string', 'minLength': 1, 'maxLength': 50000},
                                       'timeout_seconds': {'type': 'integer', 'minimum': 1, 'maximum': 120}}}}


class Bridge:
    def __init__(self, config):
        self.config = read(config)
        self.container = self.config['container']
        if not re.fullmatch(r'ttgl-worker-[a-f0-9]{24}', self.container):
            raise ValueError('Exact host-owned actor required')
        self.root = Path(self.config['output'])
        self.client = LocalS3Retention(self.config['repository_root'], self.root/'retention')
        self.deadline = self.config['deadline_epoch']

    def call(self, ident, args):
        if (not isinstance(args, dict) or set(args)-{'command', 'timeout_seconds'}
                or not isinstance(args.get('command'), str) or not 0 < len(args['command']) <= 50000):
            raise ValueError('Invalid shell arguments')
        timeout = args.get('timeout_seconds', 60)
        if type(timeout) is not int or not 1 <= timeout <= 120:
            raise ValueError('Invalid timeout')
        if time.time()+timeout+5 > self.deadline:
            raise ValueError('Insufficient integration/operation time remaining')
        key = digest(ident)
        folder = self.root/key
        if (folder/'started.json').exists():
            result = read(folder/'result.json')
            if read(folder/'started.json')['arguments'] != args:
                raise ValueError('Conflicting RPC identity')
            return result
        if len(list(self.root.glob('*/started.json'))) >= self.config['maximum_tool_calls']:
            raise ValueError('Tool budget exhausted')
        write_new(folder/'started.json', {'arguments': args, 'container': self.container})
        self.client.retain_file(folder/'started.json', kind='actor-command', identity=key)
        started = time.monotonic()
        with (folder/'stdout').open('xb') as out, (folder/'stderr').open('xb') as err:
            try:
                process = subprocess.run(['docker', 'exec', '--env', 'PYTHONDONTWRITEBYTECODE=1', '--workdir', '/testbed', self.container,
                    'timeout', '-s', 'KILL', str(timeout), 'sh', '-c', args['command']],
                    stdout=out, stderr=err, timeout=timeout+5)
                code = process.returncode
            except subprocess.TimeoutExpired:
                code = None  # Uncertain operation: retain, never retry.
        command_runtime = time.monotonic()-started
        refs = [self.client.retain_file(folder/name, kind='actor-'+name, identity=key+':'+name)
                for name in ('stdout', 'stderr')]
        result = {'exit_code': code, 'stdout': (folder/'stdout').read_text(errors='replace')[-40000:],
                  'stderr': (folder/'stderr').read_text(errors='replace')[-10000:],
                  'elapsed_seconds': time.monotonic()-started, 'exact_archive_refs': refs,
                  'command_runtime_seconds': command_runtime,
                  'elapsed_scope': 'agent-blocking tool time including output retention; command runtime is separate',
                  'output_may_be_clipped': (folder/'stdout').stat().st_size > 40000 or (folder/'stderr').stat().st_size > 10000}
        write_new(folder/'result.json', result)
        return result


def run(config, source, sink):
    bridge = Bridge(config)
    for line in source:
        request = None
        try:
            if len(line.encode()) > 100000:
                raise ValueError('RPC bound exceeded')
            request = json.loads(line)
            if 'id' not in request:
                continue
            method = request['method']
            if method == 'initialize':
                result = {'protocolVersion': request.get('params', {}).get('protocolVersion', '2025-06-18'),
                          'capabilities': {'tools': {}}, 'serverInfo': {'name': 'observatory-actor', 'version': '1'}}
            elif method == 'ping':
                result = {}
            elif method == 'tools/list':
                tools = [TOOL]
                if bridge.config.get('delegation'):
                    from .live_delegation import TOOLS as delegation_tools
                    tools += delegation_tools
                result = {'tools': tools}
            elif method == 'tools/call' and request['params']['name'] in ('route_subtask', 'delegate_subtask') and bridge.config.get('delegation'):
                from .live_delegation import decision, delegate
                try:
                    args = request['params'].get('arguments', {})
                    value = decision(bridge.config['delegation'], args) if request['params']['name'] == 'route_subtask' else delegate(bridge, args)
                    result = {'content': [{'type': 'text', 'text': json.dumps(value)}], 'isError': False}
                except Exception as error:
                    result = {'content': [{'type': 'text', 'text': type(error).__name__+': '+str(error)[:300]}], 'isError': True}
            elif method == 'tools/call' and request['params']['name'] == 'shell':
                try:
                    value = bridge.call(request['id'], request['params'].get('arguments', {}))
                    result = {'content': [{'type': 'text', 'text': json.dumps(value)}], 'isError': value['exit_code'] is None}
                except Exception as error:
                    result = {'content': [{'type': 'text', 'text': type(error).__name__+': '+str(error)[:300]}], 'isError': True}
            else:
                raise ValueError('Unsupported actor method')
            response = {'jsonrpc': '2.0', 'id': request['id'], 'result': result}
        except Exception:
            response = {'jsonrpc': '2.0', 'id': request.get('id') if isinstance(request, dict) else None,
                        'error': {'code': -32602, 'message': 'Invalid actor request'}}
        sink.write(json.dumps(response)+'\n')
        sink.flush()


if __name__ == '__main__':
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    run(parser.parse_args().config, sys.stdin, sys.stdout)
