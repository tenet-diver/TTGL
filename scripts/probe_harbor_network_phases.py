#!/usr/bin/env python3
"""Exercise the custom environment through Harbor's real phase and exec APIs."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import uuid

from harbor.models.task.config import EnvironmentConfig, NetworkMode, NetworkPolicy
from harbor.models.trial.paths import TrialPaths
from ttgl.harbor_docker_network import DetachedNetworkDocker

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    raise ValueError('Choose a fresh receipt path')


async def main():
    root = Path(tempfile.mkdtemp(prefix='ttgl-harbor-network-'))
    definitions = root / 'environment'
    definitions.mkdir()
    (definitions / 'Dockerfile').write_text('FROM python:3.12-slim\n')
    name = 'ttgl-harbor-net-' + uuid.uuid4().hex[:8]
    peer = name + '-peer'
    public = NetworkPolicy(network_mode=NetworkMode.PUBLIC)
    isolated = NetworkPolicy(network_mode=NetworkMode.NO_NETWORK)
    environment = DetachedNetworkDocker(
        environment_dir=definitions, environment_name=name, session_id=name,
        trial_paths=TrialPaths(root / 'trial'),
        task_env_config=EnvironmentConfig(docker_image='python:3.12-slim'),
        network_policy=public, phase_network_policies=[isolated, public])
    evidence, error, cleanup_errors = [], None, []
    try:
        await environment.start(force_build=False)
        actor = (await environment._run_docker_compose_command(['ps', '-q', 'main'])).stdout.strip()
        info = await environment._inspect_actor(actor)
        networks = info['NetworkSettings']['Networks']
        if len(networks) != 1:
            raise RuntimeError('Fixture needs one ordinary bridge')
        network = next(iter(networks))
        await environment._docker('run', '-d', '--name', peer, '--network', network,
                                  'python:3.12-slim', 'python', '-m', 'http.server', '8080')
        url = f'http://{peer}:8080'
        fetch = "python -c " + shlex.quote(
            f'import urllib.request; print(urllib.request.urlopen({url!r}, timeout=2).status)')
        for _ in range(20):
            result = await environment.exec(fetch, timeout_sec=15)
            if result.return_code == 0 and '200' in result.stdout:
                break
            await asyncio.sleep(.2)
        else:
            raise RuntimeError('Public phase positive control failed')
        evidence.append({'phase': 'public', **result.model_dump()})
        # Test the route itself; resolver retries can outlast urllib's timeout.
        peer_info = json.loads(await environment._docker('inspect', peer))[0]
        address = peer_info['NetworkSettings']['Networks'][network]['IPAddress']
        if not address:
            raise RuntimeError('Ready peer has no bridge address')
        fetch = "python -c " + shlex.quote(
            'import urllib.request; print(urllib.request.urlopen('
            f'{("http://" + address + ":8080")!r}, timeout=2).status)')
        await environment.set_network_policy(isolated)
        result = await environment.exec(fetch, timeout_sec=15)
        evidence.append({'phase': 'no-network', **result.model_dump()})
        if result.return_code == 0:
            raise RuntimeError('Isolated phase reached peer')
        await environment.set_network_policy(public)
        result = await environment.exec(fetch, timeout_sec=15)
        evidence.append({'phase': 'restored-public', **result.model_dump()})
        if result.return_code or '200' not in result.stdout:
            raise RuntimeError('Verifier phase did not regain network')
        try:
            environment.validate_network_policy_support(
                NetworkPolicy(network_mode=NetworkMode.ALLOWLIST, allowed_hosts=['example.com']))
        except ValueError:
            evidence.append({'unsupported_allowlist_rejected': True})
        else:
            raise RuntimeError('Unsupported allowlist accepted')
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
    finally:
        result = subprocess.run(['docker', 'rm', '-f', peer], capture_output=True, text=True)
        if result.returncode and 'No such container' not in result.stderr:
            cleanup_errors.append(result.stderr)
        try:
            await environment.stop(delete=True)
        except Exception as exc:
            cleanup_errors.append(str(exc))
        source = Path('src/ttgl/harbor_docker_network.py')
        args.output.write_text(json.dumps(dict(
            status='failed' if error or cleanup_errors else 'real_harbor_phase_fixture_passed',
            error=error, cleanup_errors=cleanup_errors, root=str(root), model_calls=0,
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            transitions=environment.network_transitions, evidence=evidence,
            scope='Real Harbor lifecycle and public/no-network/public peer checks; '
                  'not yet the actual Pro image, official grading or model accuracy.'), indent=2) + '\n')
    if error or cleanup_errors:
        raise SystemExit(error or str(cleanup_errors))
    print('Real Harbor phase fixture passed')


asyncio.run(main())
