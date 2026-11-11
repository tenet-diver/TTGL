#!/usr/bin/env python3
"""Independent base/reference admission in a declared newer Python profile.

Reuses Docker, the reviewed image, and a pinned venv. No task setup scripts,
package installation, reference exposure to solvers, or model calls.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import time
import xml.etree.ElementTree as ET

IMAGE = 'sha256:9ed8bd351e618aa9075306abee2a94a14954f35c23dbdc22902080e0dfbb930e'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(archive, output):
    output.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as tar:
        members = []
        prefix = None
        for member in tar:
            if PurePosixPath(member.name).is_absolute():
                raise ValueError('Absolute archive member: ' + member.name)
            parts = PurePosixPath(member.name).parts
            if not parts or '..' in parts:
                raise ValueError('Unsafe archive path')
            prefix = prefix or parts[0]
            if parts[0] != prefix:
                raise ValueError('Archive has multiple source roots')
            relative = PurePosixPath(*parts[1:])
            if not relative.parts:
                continue
            if member.islnk() or not (member.isdir() or member.isfile() or member.issym()):
                raise ValueError('Unsafe archive member: ' + member.name)
            members.append(member.replace(name=str(relative), deep=True))
        # CPython's maintained filter resolves and rejects escaping links/paths.
        tar.extractall(output, members=members, filter='data')
    return {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file()}


def command(runtime, source, results, name, test_dir='tests/', pytest_args=(), profile='host314', writable_source=False):
    cmd = ['docker', '--host=unix:///var/run/docker.sock', 'run', '--rm', '--name', name,
           '--network=none', '--read-only', '--cap-drop=ALL',
           '--security-opt=no-new-privileges', '--user', '1000:1000',
           '--pids-limit', '128', '--memory', '2g', '--cpus', '2',
           '--tmpfs', '/tmp:rw,nosuid,size=512m']
    mounts = [(runtime, '/runtime')]
    if profile == 'host314':
        mounts += [('/usr', '/usr'), ('/usr/lib', '/lib'), ('/usr/lib64', '/lib64'),
                   ('/opt/conda', '/opt/conda')]
    elif profile != 'alpine311':
        raise ValueError('Unknown runtime profile')
    for src, dst in mounts:
        cmd += ['--mount', f'type=bind,src={src},dst={dst},readonly']
    cmd += ['--mount', f'type=bind,src={source},dst=/task' + ('' if writable_source else ',readonly')]
    cmd += ['--mount', f'type=bind,src={results},dst=/results']
    for value in ['PYTHONPATH=' + ('/runtime:' if profile == 'alpine311' else '') + '/task/src:/task', 'PYTHONDONTWRITEBYTECODE=1',
                  'COVERAGE_FILE=/tmp/.coverage', 'HOME=/tmp',
                  'NUMBA_CACHE_DIR=/tmp/numba-cache', 'HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis',
                  'OMP_NUM_THREADS=2', 'OPENBLAS_NUM_THREADS=2', 'NUMBA_NUM_THREADS=2',
                  'HTTP_PROXY=', 'HTTPS_PROXY=', 'ALL_PROXY=']:
        cmd += ['--env', value]
    return cmd + ['--workdir', '/task', '--entrypoint', '/runtime/bin/python' if profile == 'host314' else 'python3', IMAGE,
                  '-m', 'pytest', '-p', 'no:cacheprovider', '-q',
                  '--junitxml=/results/junit.xml', *pytest_args, test_dir]


def run(assets, runtime, output, task, test_dir='tests/', pytest_args=(), profile='host314', writable_source=False, data_assets=None):
    output.mkdir(parents=True, exist_ok=False)
    runtime = runtime.resolve()
    env = {k: v for k, v in os.environ.items() if k not in
           ('DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH')}
    rows = []
    for phase in ['base', 'reference']:
        archive = assets / f'{task}-{phase}.tar.gz'
        receipt = json.loads((assets / f'{task}-{phase}.json').read_text())
        if digest(archive) != receipt['sha256']:
            raise ValueError('Archive differs from pinned receipt')
        root = output / phase
        root.mkdir()
        source, resultdir = root / 'source', root / 'results'
        hashes = extract(archive, source)
        resource_hashes = {}
        if data_assets:
            asset_root = data_assets.resolve()
            manifest = json.loads((asset_root / 'manifest.json').read_text())
            for relative, expected in manifest['resources'].items():
                path = PurePosixPath(relative)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('Invalid data asset path')
                src, dst = asset_root / relative, source / relative
                if src.is_symlink() or digest(src) != expected or dst.exists():
                    raise ValueError('Data assets must be sealed additions, not source replacements')
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
                resource_hashes[relative] = expected
            (root / 'data-assets.json').write_text(json.dumps(manifest, indent=2))
        resultdir.mkdir()
        resultdir.chmod(0o777)
        (root / 'source-manifest.json').write_text(json.dumps(hashes, indent=2))
        name = f'ttgl-compat-{output.name}-{task}-{phase}'
        cmd = command(runtime, source.resolve(), resultdir.resolve(), name, test_dir, pytest_args, profile, writable_source)
        plan = dict(at=datetime.now(timezone.utc).isoformat(), task=task, phase=phase,
                    source=receipt, command=cmd, source_sha256=digest(Path(__file__)),
                    model_calls=0, automatic_retries=0,
                    profile=profile, writable_source=writable_source,
                    runtime_note='Declared compatibility variant; original tests unmodified')
        (root / 'started.json').write_text(json.dumps(plan, indent=2))
        began = time.perf_counter()
        with (root / 'stdout.log').open('xb') as log:
            proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                code, timed_out = proc.wait(timeout=600), False
            except subprocess.TimeoutExpired:
                subprocess.run(['docker', '--host=unix:///var/run/docker.sock', 'kill', name],
                               env=env, capture_output=True, timeout=20)
                code, timed_out = proc.wait(timeout=20), True
        stats = None
        if (resultdir / 'junit.xml').exists():
            suites = list(ET.parse(resultdir / 'junit.xml').getroot().iter('testsuite'))
            stats = {k: sum(int(s.attrib.get(k, 0)) for s in suites)
                     for k in ['tests', 'failures', 'errors', 'skipped']}
        changed = [name for name, sha in (hashes | resource_hashes).items()
                   if not (source / name).is_file() or digest(source / name) != sha]
        row = dict(task=task, phase=phase, exit_code=code, timeout=timed_out,
                   wall_seconds=time.perf_counter()-began, junit=stats, model_calls=0,
                   original_source_changed=changed, profile=profile,
                   reference_pass=phase == 'reference' and code == 0 and bool(stats) and stats['tests'] > 0 and not changed)
        (root / 'result.json').write_text(json.dumps(row, indent=2))
        rows.append(row)
        print(json.dumps(row), flush=True)
    (output / 'summary.json').write_text(json.dumps(rows, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--test-dir', default='tests/')
    parser.add_argument('--pytest-arg', action='append', default=[])
    parser.add_argument('--profile', choices=['host314', 'alpine311'], default='host314')
    parser.add_argument('--writable-source', action='store_true')
    parser.add_argument('--data-assets', type=Path)
    args = parser.parse_args()
    run(args.assets, args.runtime, args.output, args.task, args.test_dir, args.pytest_arg, args.profile, args.writable_source, args.data_assets)
