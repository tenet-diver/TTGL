"""Behavior checks for the optional host/Harbor transport; no model calls."""
import asyncio
import contextvars
from dataclasses import replace
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request as HTTPRequest, urlopen
import pytest

from ttgl.harbor_bridge import EnvironmentBridge, HarborBackend, SERVER
from ttgl.personal import Request


def test_only_authenticated_bounded_calls_reach_environment_and_trace(tmp_path):
    phase = contextvars.ContextVar('benchmark_phase', default='setup')
    class Environment:
        def __init__(self):
            self.calls = []

        async def exec(self, **kwargs):
            assert phase.get() == 'agent'
            self.calls.append(kwargs)
            return SimpleNamespace(return_code=7, stdout='visible observation', stderr='failed public check')

    async def scenario():
        phase.set('agent')
        env = Environment()
        bridge = EnvironmentBridge(env, '/app/repository', tmp_path/'trace.jsonl').start()

        def call(token, timeout):
            request = HTTPRequest(f'http://127.0.0.1:{bridge.port}/shell',
                data=json.dumps({'command': 'run-public-check', 'timeout_seconds': timeout}).encode(),
                headers={'Authorization': 'Bearer '+token})
            try:
                with urlopen(request, timeout=5) as response:
                    return response.status, json.load(response)
            except HTTPError as exc:
                return exc.code, None

        try:
            assert (await asyncio.to_thread(call, 'wrong', 5))[0] == 403
            assert (await asyncio.to_thread(call, bridge.token, 121))[0] == 400
            assert env.calls == []
            status, response = await asyncio.to_thread(call, bridge.token, 5)
            assert status == 200
            assert response == {'exit_code': 7, 'stdout': 'visible observation', 'stderr': 'failed public check'}
            assert len(env.calls) == 1
            assert env.calls[0]['command'].startswith('cd /app/repository && timeout --signal=KILL 5 ')
            rows = [json.loads(s) for s in (tmp_path/'trace.jsonl').read_text().splitlines()]
            assert [r['event'] for r in rows] == ['tool_request', 'tool_response']
            assert rows[0]['sequence'] == rows[1]['sequence']
            assert bridge.token not in (tmp_path/'trace.jsonl').read_text()
        finally:
            await bridge.close()

    asyncio.run(scenario())


def test_context_only_expert_has_no_environment_tool(tmp_path):
    bridge = SimpleNamespace(repository='/app', port=12345, token='a'*64)
    backend = HarborBackend(bridge, audit_root=tmp_path/'prompts')
    request = Request(request_id='test', model='fixture', kind='controller', prompt='fixture',
                      workspace=tmp_path, schema={}, timeout_seconds=10)
    acting = backend.command(request, tmp_path/'schema.json')
    assert any('harbor-server.mjs' in part for part in acting)
    assert not any('server.mjs", "harbor-environment-transport' in part for part in acting)
    expert = backend.command(replace(request, kind='expert', read_only=True), tmp_path/'schema.json')
    assert not any('mcp_servers.worker' in part for part in expert)
    for feature in ('shell_tool', 'unified_exec', 'apps', 'browser_use'):
        assert expert[expert.index(feature)-1] == '--disable'


@pytest.mark.skipif(not shutil.which('node') or not (SERVER.parent/'node_modules').exists(),
                    reason='Requires the installed official worker MCP SDK')
def test_official_mcp_client_roundtrip_reaches_only_bound_environment(tmp_path):
    class Environment:
        async def exec(self, **kwargs):
            assert 'printf bridge-ok' in kwargs['command']
            return SimpleNamespace(return_code=0, stdout='bridge-ok', stderr='')

    async def scenario():
        bridge = EnvironmentBridge(Environment(), '/app', tmp_path/'trace.jsonl').start()
        code = '''
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
const client = new Client({name:'bridge-behavior-check',version:'1'});
await client.connect(new StdioClientTransport({command:process.execPath,
  args:['harbor-server.mjs',...process.argv.slice(1)]}));
const result = await client.callTool({name:'shell',arguments:{command:'printf bridge-ok',timeout_seconds:5}});
process.stdout.write(JSON.stringify(result));
await client.close();
'''
        try:
            process = await asyncio.create_subprocess_exec('node', '--input-type=module', '-e', code,
                str(bridge.port), bridge.token, cwd=SERVER.parent,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
            assert process.returncode == 0, stderr.decode()
            result = json.loads(stdout)
            assert result.get('isError') is False
            assert json.loads(result['content'][0]['text'])['stdout'] == 'bridge-ok'
        finally:
            await bridge.close()

    asyncio.run(scenario())
