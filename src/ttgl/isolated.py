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
from urllib.request import urlopen

from . import benchmark, personal

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / 'tools/worker-mcp/server.mjs'
DEPENDENCIES = ROOT / 'tools/worker-dependencies.json'
# Exact, inspected dependency/runner-only changes made by official image setup.
# Every listed file is restored to its original base blob before model access.
AUDITED_SETUP_BLOBS = {
    ('astropy/astropy', 'pyproject.toml'): {
        ('3364d307406a06457fba6b129db98c2399e7d624', '02dddbe713a3d037b3e5f6ba49af3b7ec1c49c0b')},
    ('sphinx-doc/sphinx', 'setup.py'): {
        ('2538952e376408be7da679fc647fac447dd30602', '94e1d8b320a57b3b1d0a556e15e9a90080e39d6d'),
        # 9320 image: dependency caps only; inspected before held-out inference.
        ('206ff4ad4904cd24b81e00dc0b3383fcbb54e6a2', '4bb5faeb12fe7d313b81413f3655954aaa09d9cb')},
    ('sphinx-doc/sphinx', 'tox.ini'): {
        ('a363e187faaecc3096f41168ccedd93a17a0cf50', '3b8bc12d02028feaac4d488c13b662e3e6db163d')},
}


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
                'adapter_sha256': benchmark.digest(Path(__file__)),
                'worker_dependencies_sha256': benchmark.digest(DEPENDENCIES)}

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
        self.pending_container = None

    def prepare(self, task: dict, workspace: Path, output: Path):
        image = self.images[task['instance_id']]
        benchmark_image = isinstance(image, dict)
        if isinstance(image, dict):
            image_bytes = image.get('size_bytes', 0)
            reference, image = image['reference'], image['image_id']
            observed = json.loads(docker('image', 'inspect', reference)) if subprocess.run(
                ['docker', 'image', 'inspect', reference], capture_output=True).returncode == 0 else []
            if not observed:
                if shutil.disk_usage(workspace).free < 10 * 1024**3 + image_bytes:
                    raise RuntimeError('Insufficient free space for the next worker image plus reserve')
                docker('pull', reference, timeout=1200)
            if json.loads(docker('image', 'inspect', reference))[0]['Id'] != image:
                raise ValueError('Pulled worker differs from frozen image')
            if self.previous_image and self.previous_image != image:
                # Pull before removing the predecessor so shared immutable
                # layers survive. The reserve above covers the incoming image.
                # Only our completed task image is removed, never global caches.
                docker('image', 'rm', self.previous_image)
                self.previous_image = None
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
        self.pending_container = name
        docker('start', name)
        dependency_records = []
        packages = json.loads(DEPENDENCIES.read_text())['repositories'].get(task.get('repo'), [])
        for package in packages:
            cache = ROOT / 'artifacts/worker-dependencies'
            cache.mkdir(parents=True, exist_ok=True)
            wheel = cache / package['filename']
            if not wheel.exists():
                with urlopen(package['url'], timeout=60) as response:
                    content = response.read()
                if hashlib.sha256(content).hexdigest() != package['sha256']:
                    raise ValueError('Worker dependency download checksum mismatch')
                wheel.write_bytes(content)
            if benchmark.digest(wheel) != package['sha256']:
                raise ValueError('Cached worker dependency changed')
            docker('cp', str(wheel), name + ':/tmp/' + wheel.name)
            docker('exec', name, '/opt/miniconda3/envs/testbed/bin/python', '-m', 'pip',
                   'install', '--no-index', '--no-deps', '/tmp/' + wheel.name)
            dependency_records.append({'name': package['name'], 'version': package['version'],
                                       'wheel_sha256': package['sha256']})
        # Keep ignored compiled extensions from the prepared image. Removing
        # the whole repository would destroy editable sklearn/astropy builds.
        # Verify tracked content before replacing the original Git history.
        restored_setup_files = []
        if benchmark_image:
            if docker('exec', name, 'git', '-C', '/testbed', 'status', '--porcelain').strip():
                raise RuntimeError('Prepared image contains uncommitted tracked source changes')
            source_diff = docker('exec', name, 'git', '-C', '/testbed', 'diff', '--raw',
                                 '--no-abbrev', '-z', task['base_commit'], 'HEAD', '--', '.')
            # Compare blob identities, including binary files, independently of
            # image setup's execute-bit changes. Inspected dependency/runner
            # metadata exceptions require exact hashes; staging restores base.
            fields = source_diff.split('\0')
            for index in range(0, len(fields)-1, 2):
                metadata, path = fields[index], fields[index+1]
                old_mode, new_mode, old_blob, new_blob, status = metadata[1:].split()
                regular = old_mode in {'100644', '100755'} and new_mode in {'100644', '100755'}
                audited_setup = (old_blob, new_blob) in AUDITED_SETUP_BLOBS.get((task.get('repo'), path), set())
                if not regular or status != 'M' or (old_blob != new_blob and not audited_setup):
                    raise RuntimeError('Prepared image contains tracked source changes beyond audited setup')
                if audited_setup:
                    restored_setup_files.append({'path': path, 'base_blob': old_blob,
                                                 'image_setup_blob': new_blob})
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
        if docker('exec', name, 'git', '-C', '/testbed', 'status', '--porcelain').strip():
            raise RuntimeError('Staged worker source is dirty before inference')
        benchmark.write_new(record_path, {
            'container': name, 'image_id': image, 'base_commit': observed,
            'mounts': info['Mounts'], 'network': info['HostConfig']['NetworkMode'],
            'cap_drop': info['HostConfig']['CapDrop'], 'memory_bytes': info['HostConfig']['Memory'],
            'native_host_tools': False, 'solver_reference_material': False,
            'image_tracked_source_audited': benchmark_image,
            'restored_image_setup_files': restored_setup_files,
            'ignored_compiled_dependencies_retained': benchmark_image,
            'additional_worker_dependencies': dependency_records,
        })
        self.backend.container, self.task = name, task
        self.previous_image = image
        self.pending_container = None

    def export_patch(self, task, workspace):
        name = self.backend.container
        actual = docker('exec', name, 'git', '-C', '/testbed', 'rev-parse', 'HEAD').strip()
        if actual != task['base_commit']:
            raise ValueError('Agent changed worker HEAD')
        docker('exec', name, 'git', '-C', '/testbed', 'add', '--intent-to-add', '--all')
        return docker('exec', name, 'git', '-C', '/testbed', 'diff', '--binary',
                      '--no-ext-diff', task['base_commit'], '--', '.')

    def close(self):
        owned = self.backend.container or self.pending_container
        if owned:
            docker('rm', '-f', owned)
        self.backend.container = None
        self.pending_container = None
