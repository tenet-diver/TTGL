#!/usr/bin/env python3
"""Run sealed Commit0 development base/reference controls, no model inference.

Uses a previously reviewed local runtime image. Never builds or pulls an image,
installs dependencies, or runs source setup commands. A failing control remains
evidence; changing the environment requires a new output directory.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

IMAGE = 'sha256:9ed8bd351e618aa9075306abee2a94a14954f35c23dbdc22902080e0dfbb930e'


def run(manifest_path, runtime, output):
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=False)
    sources = json.loads(manifest_path.read_text())
    docker = ['docker', '--host=unix:///var/run/docker.sock']
    env = {k: v for k, v in os.environ.items() if k not in (
        'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH')}
    results = []
    for entry in sources:
        unit = entry['name'] + '-' + entry['phase']
        root = output / unit
        root.mkdir()
        source = Path(entry['source']).resolve()
        for relative, expected in entry['hashes'].items():
            if hashlib.sha256((source / relative).read_bytes()).hexdigest() != expected:
                raise ValueError('Sealed control source changed: ' + relative)
        name = 'ttgl-team-' + output.name + '-' + unit
        command = docker + ['run', '--rm', '--name', name, '--network=none', '--read-only',
            '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user', '1000:1000',
            '--pids-limit', '64', '--memory', '512m', '--cpus', '2',
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=128m',
            '--mount', f'type=bind,src={source},dst=/task,readonly',
            '--mount', f'type=bind,src={runtime.resolve()},dst=/runtime,readonly',
            '--mount', f'type=bind,src={root.resolve()},dst=/results',
            '--env', 'PYTHONPATH=/runtime:/task/src:/task', '--env', 'PYTHONDONTWRITEBYTECODE=1',
            '--env', 'COVERAGE_FILE=/tmp/.coverage', '--env', 'HTTP_PROXY=',
            '--env', 'HTTPS_PROXY=', '--env', 'ALL_PROXY=', '--workdir', '/task', IMAGE,
            'python3', '-m', 'pytest', '-p', 'no:cacheprovider', '-q',
            '--junitxml=/results/junit.xml', 'tests/']
        with (root / 'started.json').open('x') as stream:
            json.dump(dict(at=datetime.now(timezone.utc).isoformat(), command=command,
                kind='independent_evaluator_control_no_inference',
                source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                source_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest()), stream, indent=2)
        start = time.perf_counter()
        with (root / 'stdout.log').open('xb') as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                code, timed_out = process.wait(timeout=240), False
            except subprocess.TimeoutExpired:
                subprocess.run(docker + ['kill', name], env=env, capture_output=True, timeout=15)
                code, timed_out = process.wait(timeout=15), True
        stats = None
        if (root / 'junit.xml').exists():
            suites = list(ET.parse(root / 'junit.xml').getroot().iter('testsuite'))
            stats = {k: sum(int(s.attrib.get(k, 0)) for s in suites)
                     for k in ('tests', 'failures', 'errors', 'skipped')}
        result = dict(unit=unit, at=datetime.now(timezone.utc).isoformat(), exit_code=code,
            timeout=timed_out, wall_seconds=time.perf_counter() - start, junit=stats,
            reference_pass=entry['phase'] == 'reference' and code == 0 and bool(stats) and stats['tests'] > 0,
            expected_base_failure=entry['phase'] == 'base' and code != 0,
            python_runtime='3.11.18; declared variant from dataset Python3.10', model_calls=0)
        with (root / 'result.json').open('x') as stream:
            json.dump(result, stream, indent=2)
        results.append(result)
        print(json.dumps(result), flush=True)
    with (output / 'summary.json').open('x') as stream:
        json.dump(results, stream, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source_manifest, args.runtime, args.output)
