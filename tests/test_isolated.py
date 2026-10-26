"""Real-container boundary checks; opt in with TTGL_CONTAINER_TESTS=1.

Build the small Git/Python fixture image before enabling these checks. No model
calls or benchmark answers are needed.
"""
import json
import os
from pathlib import Path
import subprocess

import pytest

from ttgl.isolated import ContainerBackend, DockerWorkers, SERVER, docker

pytestmark = pytest.mark.skipif(os.getenv('TTGL_CONTAINER_TESTS') != '1',
                                reason='requires the local Docker fixture image')


@pytest.fixture
def worker(tmp_path):
    workspace = tmp_path / 'source'
    workspace.mkdir()
    subprocess.run(['git', 'init', '-q', str(workspace)], check=True)
    (workspace / 'value.txt').write_text('21\n')
    (workspace / '.gitignore').write_text('compiled-*\n')
    subprocess.run(['git', '-C', str(workspace), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(workspace), '-c', 'user.name=TTGL',
                    '-c', 'user.email=ttgl@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    base = subprocess.check_output(['git', '-C', str(workspace), 'rev-parse', 'HEAD'], text=True).strip()
    backend = ContainerBackend()
    image = json.loads(docker('image', 'inspect', 'ttgl-worker-fixture:20261026'))[0]['Id']
    runtime = DockerWorkers(backend, {'fixture': image}, tmp_path / 'environments')
    task = {'instance_id': 'fixture', 'base_commit': base}
    runtime.prepare(task, workspace, tmp_path / 'runs' / 'fixture')
    try:
        yield backend, runtime, task, workspace
    finally:
        if backend.container:
            runtime.close()


def test_mcp_changes_only_assigned_container_and_exports_applicable_patch(worker):
    backend, runtime, task, workspace = worker
    info = json.loads(docker('inspect', backend.container))[0]
    assert info['Mounts'] == []
    assert info['HostConfig']['NetworkMode'] == 'none'
    assert info['HostConfig']['CapDrop'] == ['ALL']
    script = '''
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
const client = new Client({name: 'boundary-test', version: '1'});
await client.connect(new StdioClientTransport({command: process.execPath,
  args: [process.argv[1], process.argv[2]]}));
const tools = await client.listTools();
if (tools.tools.length !== 1 || tools.tools[0].name !== 'shell') throw Error('Unexpected tools');
const result = await client.callTool({name: 'shell', arguments: {
  command: "python -c \\\"from pathlib import Path; assert not Path('/var/run/docker.sock').exists(); assert not Path('/ttgl').exists(); Path('answer.txt').write_text(str(int(Path('value.txt').read_text()) * 2))\\\""
}});
console.log(JSON.stringify(result));
await client.close();
'''
    result = subprocess.run(['node', '--input-type=module', '-e', script,
                             str(SERVER), backend.container],
                            cwd=SERVER.parent, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    assert not response.get('isError'), response
    assert docker('exec', backend.container, 'cat', '/testbed/answer.txt') == '42'
    assert not (workspace / 'answer.txt').exists()
    patch = runtime.export_patch(task, workspace)
    applied = subprocess.run(['git', '-C', str(workspace), 'apply', '--check'],
                             input=patch, text=True, capture_output=True)
    assert applied.returncode == 0, applied.stderr
    assert 'answer.txt' in patch


def test_changed_worker_revision_cannot_be_exported(worker):
    backend, runtime, task, workspace = worker
    docker('exec', backend.container, 'git', '-C', '/testbed', '-c', 'user.name=TTGL',
           '-c', 'user.email=ttgl@example.invalid', 'commit', '--allow-empty', '-m', 'changed')
    with pytest.raises(ValueError, match='HEAD'):
        runtime.export_patch(task, workspace)


def test_staged_worker_retains_preinstalled_ignored_extensions(worker, tmp_path):
    backend, runtime, task, workspace = worker
    docker('exec', backend.container, 'bash', '-lc', 'echo prepared-extension > /testbed/compiled-fixture.so')
    tag = 'ttgl-test-dependencies:' + task['base_commit'][:12]
    image = docker('commit', backend.container, tag).strip()
    runtime.close()
    second_backend = ContainerBackend()
    second = DockerWorkers(second_backend, {'fixture': {
        'image_id': image, 'reference': tag, 'size_bytes': 0,
    }}, tmp_path / 'second-environments')
    try:
        second.prepare(task, workspace, tmp_path / 'second-runs' / 'fixture')
        assert docker('exec', second_backend.container, 'cat', '/testbed/compiled-fixture.so').strip() == 'prepared-extension'
        assert second.export_patch(task, workspace) == ''
    finally:
        if second_backend.container:
            second.close()
        docker('image', 'rm', tag)
