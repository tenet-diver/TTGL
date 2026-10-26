"""Container workers accessed through the maintained MCP SDK, using host Codex auth.

The inference client runs on the host. Its native filesystem tools are disabled;
the only solving tool executes inside a disposable, offline Docker container.
Credentials and private evaluator material are never mounted in that container.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from . import benchmark, personal

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / 'tools/worker-mcp/server.mjs'


def docker(*args: str, timeout: float = 300) -> str:
    result = subprocess.run(['docker', *args], capture_output=True, text=True,
                            timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f'Docker {args[0]} failed: {result.stderr[-3000:]}')
    return result.stdout


class ContainerBackend(personal.CodexBackend):
    def __init__(self, executable: str = 'codex'):
        super().__init__(executable)
        self.container = None
        self.node = shutil.which('node')
        if not self.node or not SERVER.exists():
            raise ValueError('Install Node and tools/worker-mcp dependencies first')

    def describe(self):
        return {**super().describe(), 'worker_tools': 'offline Docker through MCP',
                'server_sha256': benchmark.digest(SERVER),
                'lock_sha256': benchmark.digest(SERVER.parent / 'package-lock.json'),
                'adapter_sha256': benchmark.digest(Path(__file__))}

    def command(self, request, schema_path):
        # Do not inherit personal instructions, connectors, hooks, or native host
        # tools. Authentication stays with the ordinary signed-in host CLI.
        command = [self.executable, 'exec', '--json', '--skip-git-repo-check',
                   '--ignore-user-config', '--ignore-rules',
                   '--model', request.model, '--cd', str(request.workspace),
                   '--output-schema', str(schema_path)]
        for feature in ('shell_tool', 'unified_exec', 'multi_agent', 'plugins',
                        'apps', 'browser_use', 'computer_use', 'image_generation',
                        'workspace_dependencies', 'view_image'):
            command += ['--disable', feature]
        settings = {
            'approval_policy': 'never', 'web_search': 'disabled',
            'project_doc_max_bytes': 0,
            'model_reasoning_effort': request.reasoning_effort,
            'default_permissions': 'ttgl-context',
            'permissions.ttgl-context.filesystem': {':root': 'deny', ':minimal': 'read'},
            'permissions.ttgl-context.network.enabled': False,
            'features.skip_host_skill_discovery': True,
        }
        # TOML inline values; JSON strings/booleans are valid TOML values, but
        # inline tables need TOML '=' separators.
        for key, value in settings.items():
            if isinstance(value, dict):
                encoded = '{' + ','.join(json.dumps(k) + '=' + json.dumps(v)
                                        for k, v in value.items()) + '}'
            else:
                encoded = json.dumps(value)
            command += ['--config', key + '=' + encoded]
        if self.container and not request.read_only:
            command += ['--config', 'mcp_servers.worker.command=' + json.dumps(self.node),
                        '--config', 'mcp_servers.worker.args=' + json.dumps([str(SERVER), self.container]),
                        '--config', 'mcp_servers.worker.tool_timeout_sec=130',
                        '--config', 'mcp_servers.worker.enabled_tools=["shell"]',
                        '--config', 'mcp_servers.worker.tools.shell.approval_mode="approve"']
        if request.thread_id:
            command += ['resume', request.thread_id]
        return command + ['-']

    def complete(self, request):
        if self.container and not request.read_only:
            request = replace(request, prompt=request.prompt +
                '\nAll repository actions must use the worker shell MCP tool. '
                'The repository and prepared Python environment are in /testbed '
                'inside that tool, not the host workspace. Use heredocs or Python '
                'through the shell tool to edit files. Network is disabled.')
        return super().complete(request)


class DockerWorkers:
    def __init__(self, backend: ContainerBackend, images: dict, records: Path):
        self.backend, self.images, self.records = backend, images, records
        self.task = None
        self.previous_image = None

    def prepare(self, task: dict, workspace: Path, output: Path):
        image = self.images[task['instance_id']]
        benchmark_image = isinstance(image, dict)
        if isinstance(image, dict):
            if self.previous_image and self.previous_image != image['image_id']:
                # Task-blocked execution keeps only the preceding task's image
                # warm. Remove only our now-unused image, never global caches.
                docker('image', 'rm', self.previous_image)
                self.previous_image = None
            if shutil.disk_usage(workspace).free < 10 * 1024**3 + image.get('size_bytes', 0):
                raise RuntimeError('Insufficient free space for the next worker image plus reserve')
            reference, image = image['reference'], image['image_id']
            observed = json.loads(docker('image', 'inspect', reference)) if subprocess.run(
                ['docker', 'image', 'inspect', reference], capture_output=True).returncode == 0 else []
            if not observed:
                docker('pull', reference, timeout=1200)
            if json.loads(docker('image', 'inspect', reference))[0]['Id'] != image:
                raise ValueError('Pulled worker differs from frozen image')
        # Image IDs, not mutable tags, enter the execution freeze.
        if not image.startswith('sha256:'):
            raise ValueError('Worker image must be bound to its local immutable image ID')
        name = 'ttgl-worker-' + hashlib.sha256(str(output).encode()).hexdigest()[:24]
        record_path = self.records / output.parent.name / (task['instance_id'] + '.json')
        if record_path.exists():
            raise ValueError('Existing worker requires explicit reconciliation; no implicit replay')
        if shutil.disk_usage(workspace).free < 10 * 1024**3:
            raise RuntimeError('Less than 10 GiB free before worker creation')
        docker('create', '--name', name, '--network', 'none', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--pids-limit', '256',
               '--memory', '4g', '--cpus', '2', '--label', 'ttgl.worker=true',
               '--workdir', '/testbed', '--entrypoint', 'sleep', image, 'infinity')
        docker('start', name)
        # Keep ignored compiled extensions from the prepared image. Removing
        # the whole repository would destroy editable sklearn/astropy builds.
        # Verify tracked content before replacing the original Git history.
        if benchmark_image:
            docker('exec', name, 'git', '-C', '/testbed', 'diff', '--quiet',
                   task['base_commit'], '--', '.')
        docker('exec', name, 'bash', '-lc', 'mkdir -p /testbed && rm -rf /testbed/.git')
        # Recreate files as the container user. docker cp preserves host UIDs
        # on Docker Desktop, which makes Git reject the checkout and prevents
        # writes with all capabilities dropped.
        with subprocess.Popen(['tar', '-C', str(workspace), '-cf', '-', '.'],
                              env={**os.environ, 'COPYFILE_DISABLE': '1'},
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as archive:
            copied = subprocess.run(['docker', 'exec', '-i', name, 'tar',
                                     '--no-same-owner', '-xf', '-', '-C', '/testbed'],
                                    stdin=archive.stdout, capture_output=True, timeout=120)
            archive.stdout.close()
            if copied.returncode or archive.wait(timeout=10):
                raise RuntimeError('Failed to stage the exact-base source archive')
        info = json.loads(docker('inspect', name))[0]
        if info['Mounts'] or info['HostConfig']['NetworkMode'] != 'none':
            raise RuntimeError('Worker isolation verification failed')
        observed = docker('exec', name, 'git', '-C', '/testbed', 'rev-parse', 'HEAD').strip()
        if observed != task['base_commit']:
            raise RuntimeError('Worker base mismatch')
        benchmark.write_new(record_path, {
            'container': name, 'image_id': image, 'base_commit': observed,
            'mounts': info['Mounts'], 'network': info['HostConfig']['NetworkMode'],
            'cap_drop': info['HostConfig']['CapDrop'], 'memory_bytes': info['HostConfig']['Memory'],
            'native_host_tools': False, 'solver_reference_material': False,
            'image_tracked_source_verified_at_base': benchmark_image,
            'ignored_compiled_dependencies_retained': benchmark_image,
        })
        self.backend.container, self.task = name, task
        self.previous_image = image

    def export_patch(self, task, workspace):
        name = self.backend.container
        actual = docker('exec', name, 'git', '-C', '/testbed', 'rev-parse', 'HEAD').strip()
        if actual != task['base_commit']:
            raise ValueError('Agent changed worker HEAD')
        docker('exec', name, 'git', '-C', '/testbed', 'add', '--intent-to-add', '--all')
        return docker('exec', name, 'git', '-C', '/testbed', 'diff', '--binary',
                      '--no-ext-diff', task['base_commit'], '--', '.')

    def close(self):
        docker('rm', '-f', self.backend.container)
        self.backend.container = None
