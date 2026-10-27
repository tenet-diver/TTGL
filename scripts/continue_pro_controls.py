#!/usr/bin/env python3
"""Registered staging-only Pro controls: no model agents and no retries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--protocol', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
protocol = json.loads(args.protocol.read_text())
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)


def write(name, value):
    with (out / name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def verify():
    for name, expected in protocol['source_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Registered staging source changed: ' + name)


def event(value):
    with (out / 'resource-events.jsonl').open('a') as stream:
        stream.write(json.dumps({'epoch': time.time(), **value}) + '\n')


try:
    verify()
    audit = json.loads(Path(protocol['prior_native_audit']).read_text())
    if audit['status'] != 'complete_study_audit' or audit['audited'] != 33 or audit['missing']:
        raise RuntimeError('Require completed independent native study audit')
    if protocol['agents'] != ['nop', 'oracle'] or protocol['model_calls_authorized'] != 0:
        raise RuntimeError('This supervisor supports only model-free official controls')
    env = {**os.environ, 'DOCKER_CONFIG': protocol['docker_config'],
           'PYTHONPATH': str(Path('src').resolve())}
    write('queue.json', {'status': 'registered_staging_only_waiting_for_resources',
                        'protocol_sha256': hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
                        'model_calls_authorized': 0})
    deadline = time.monotonic() + protocol['max_resource_wait_seconds']
    required = protocol['disk_guard_bytes'] + protocol['incoming_image_allowance_bytes']
    while shutil.disk_usage('.').free < required:
        verify()
        event({'event': 'waiting_before_image_pull', 'required_bytes': required,
               'free_bytes': shutil.disk_usage('.').free})
        if time.monotonic() > deadline:
            raise RuntimeError('Resource wait expired before image preparation; no model call')
        time.sleep(30)
    verify()
    write('image-pull-invocation.json', {'reference': protocol['image_pinned'],
                                       'model_calls': 0})
    with (out / 'image-pull.stdout.txt').open('x') as log:
        subprocess.run(['docker', 'pull', protocol['image_pinned']], env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=2400)
    image = json.loads(subprocess.check_output(
        ['docker', 'image', 'inspect', protocol['image_pinned']], env=env, text=True))[0]
    if protocol['image_pinned'].split('@')[1] not in '\n'.join(image.get('RepoDigests', [])):
        raise RuntimeError('Pulled image digest did not match registration')
    subprocess.run(['docker', 'tag', image['Id'], protocol['image_tag']], env=env, check=True)
    write('image-binding.json', {'image_id': image['Id'], 'size_bytes': image['Size'],
                                'pinned': protocol['image_pinned'], 'tag': protocol['image_tag']})
    records = []
    for agent, expected in [('nop', 0), ('oracle', 1)]:
        verify()
        if shutil.disk_usage('.').free < protocol['disk_guard_bytes']:
            raise RuntimeError('Resource reserve unavailable before control; stop without retry')
        current = subprocess.check_output(
            ['docker', 'image', 'inspect', protocol['image_tag'], '--format', '{{.Id}}'],
            env=env, text=True).strip()
        if current != image['Id']:
            raise RuntimeError('Task image changed')
        name = 'pro-' + agent + '-control-003'
        command = [protocol['harbor'], 'run', '-p', protocol['task_directory'],
                   '--environment-import-path', protocol['environment_import_path'],
                   '-a', agent, '-n', '1', '--n-attempts', '1', '--max-retries', '0',
                   '--jobs-dir', str(out / 'jobs'), '--job-name', name]
        write(agent + '-invocation.json', {'command': command, 'model_calls': 0})
        with (out / (agent + '.stdout.txt')).open('x') as log:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=7200)
        paths = list((out / 'jobs' / name).glob('*/result.json'))
        if result.returncode or len(paths) != 1:
            raise RuntimeError('Control failed or native result ambiguous: ' + agent)
        native = json.loads(paths[0].read_text())
        reward = (native.get('verifier_result') or {}).get('rewards', {}).get('reward')
        if native.get('exception_info') or reward != expected:
            raise RuntimeError('Invalid native control grade: ' + agent)
        record = {'agent': agent, 'reward': reward, 'native_result': str(paths[0]),
                  'native_result_sha256': hashlib.sha256(paths[0].read_bytes()).hexdigest()}
        records.append(record)
        write(agent + '-receipt.json', record)
    write('summary.json', {'status': 'one_task_empty_reference_controls_passed',
                           'tasks': 1, 'controls': records, 'model_inference_calls': 0,
                           'model_trials_not_automatically_started': True})
except Exception as exc:
    write('stopped.json', {'status': 'stopped_no_model_calls_authorized',
                          'error': f'{type(exc).__name__}: {exc}'})
    raise
