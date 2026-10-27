#!/usr/bin/env python3
"""Probe Docker bridge phase transitions with disposable owned containers."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    raise ValueError('Preserve prior probe evidence; choose a new output')
tag = uuid.uuid4().hex[:10]
network, server, client = (f'ttgl-{kind}-{tag}' for kind in ('net', 'http', 'actor'))
alpine = 'alpine:3.23.4@sha256:5b10f432ef3da1b8d4c7eb6c487f2f5a8f096bc91145e68878dd4a5019afde11'
events, cleanup_errors = [], []
error = None


def run(*command, check=True):
    result = subprocess.run(['docker', *command], capture_output=True, text=True, timeout=20)
    events.append(dict(command=list(command), returncode=result.returncode,
                       stdout=result.stdout, stderr=result.stderr))
    if check and result.returncode:
        raise RuntimeError(result.stderr)
    return result


try:
    # Never pull an unpinned or missing image implicitly in this diagnostic.
    run('image', 'inspect', alpine)
    run('image', 'inspect', 'python:3.12-slim')
    run('network', 'create', network)
    run('run', '-d', '--name', server, '--network', network, 'python:3.12-slim',
        'sh', '-c', 'mkdir /www; echo ttgl-network-witness >/www/index.html; '
        'cd /www; python -m http.server 8080')
    run('run', '-d', '--name', client, '--network', network, alpine, 'sleep', '300')
    url = f'http://{server}:8080'
    deadline = time.monotonic() + 25
    while True:
        response = run('exec', client, 'wget', '-qO-', '-T', '2', url, check=False)
        if response.returncode == 0 and 'ttgl-network-witness' in response.stdout:
            break
        if time.monotonic() > deadline:
            run('logs', server, check=False)
            raise RuntimeError('Positive network/server readiness control failed')
        time.sleep(.2)
    run('network', 'disconnect', network, client)
    state = json.loads(run('inspect', client).stdout)[0]
    if state['NetworkSettings']['Networks']:
        raise RuntimeError('Client retained network attachments')
    if run('exec', client, 'wget', '-qO-', '-T', '3', url, check=False).returncode == 0:
        raise RuntimeError('Disconnected client retained peer reachability')
    run('network', 'connect', network, client)
    response = run('exec', client, 'wget', '-qO-', '-T', '3', url)
    if 'ttgl-network-witness' not in response.stdout:
        raise RuntimeError('Restored network failed positive control')
except Exception as exc:
    error = f'{type(exc).__name__}: {exc}'
finally:
    for command in [('rm', '-f', client), ('rm', '-f', server), ('network', 'rm', network)]:
        try:
            result = run(*command, check=False)
            if result.returncode:
                cleanup_errors.append(result.stderr)
        except Exception as exc:
            cleanup_errors.append(str(exc))
    args.output.write_text(json.dumps(dict(
        status='failed' if error or cleanup_errors else 'docker_network_phase_mechanism_passed',
        error=error, cleanup_errors=cleanup_errors, model_calls=0,
        scope='Owned disposable bridge peer controls only; not Harbor integration, '
              'universal egress proof, or Pro model quality.', events=events), indent=2) + '\n')
if error or cleanup_errors:
    raise SystemExit(error or str(cleanup_errors))
print('Docker network disconnect/reconnect mechanism passed')
