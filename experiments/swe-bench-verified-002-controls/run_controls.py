#!/usr/bin/env python3
"""Run official SWE-bench controls sequentially with managed-container CA trust.

This is an environment runner, not a replacement evaluator. Tests, patches and
grading all come from the pinned official SWE-bench harness/task distribution.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
DATASET = Path('/workspace/scratch/ttgl-swe-evaluator/selected.dataset.json')
PYTHON = '/workspace/.tools/ttgl-swebench/bin/python'
CA = '/etc/ssl/certs/ca-certificates.crt'
GIB = 1024 ** 3

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, value): Path(path).write_text(json.dumps(value, indent=2) + '\n')
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def cleanup(instance):
    """Remove only this run's recorded image, after checking container references."""
    state_path = ROOT / f'{instance}.execution.json'
    state = json.loads(state_path.read_text())
    if not state.get('image_owned_by_this_run'):
        raise RuntimeError('Refusing to remove a pre-existing image')
    image = state['image_tag']
    used = subprocess.check_output(['docker', 'ps', '-aq', '--filter', f'ancestor={image}'], text=True).strip()
    if used:
        raise RuntimeError('Image still has containers; leave it for their owner')
    inspected = subprocess.run(['docker', 'image', 'inspect', image], capture_output=True, text=True)
    if inspected.returncode == 0:
        info = json.loads(inspected.stdout)[0]
        if state.get('image_id') and info['Id'] != state['image_id']:
            raise RuntimeError('Image changed after controls; refusing cleanup')
        with (ROOT / f'{instance}.cleanup.log').open('w') as log:
            result = subprocess.run(['docker', 'image', 'rm', image], stdout=log, stderr=subprocess.STDOUT, timeout=180)
        state['cleanup_exit_code'] = result.returncode
    else:
        state['cleanup_exit_code'] = 0
    state['cleanup_at'] = now()
    state['disk_free_after_cleanup_bytes'] = shutil.disk_usage('/workspace').free
    write(state_path, state)
    print(json.dumps({'instance': instance, 'cleanup_exit_code': state['cleanup_exit_code'],
                      'disk_free_after_cleanup_bytes': state['disk_free_after_cleanup_bytes']}), flush=True)

def child(instance, control):
    import docker.models.containers
    from swebench.harness.run_evaluation import main
    original = docker.models.containers.ContainerCollection.create
    def create(collection, *args, **kwargs):
        if not str(kwargs.get('name', '')).startswith('sweb.eval.'):
            raise RuntimeError('Unexpected container name in official control runner')
        volumes = dict(kwargs.pop('volumes', {}) or {})
        volumes[CA] = {'bind': '/run/ttgl-system-ca.pem', 'mode': 'ro'}
        environment = dict(kwargs.pop('environment', {}) or {})
        for name in ('REQUESTS_CA_BUNDLE', 'PIP_CERT', 'SSL_CERT_FILE'):
            environment[name] = '/run/ttgl-system-ca.pem'
        return original(collection, *args, volumes=volumes,
                        environment=environment, **kwargs)
    docker.models.containers.ContainerCollection.create = create
    rid = f'ttgl-verified-002-{control}-{instance}'
    main(dataset_name=str(DATASET), split='test', instance_ids=[instance],
         predictions_path='gold' if control == 'gold' else str(ROOT / f'{instance}.base.jsonl'),
         max_workers=1, open_file_limit=4096, run_id=rid, timeout=600,
         rewrite_reports=False, modal=False, task_repo=None)

def execute(instance):
    rows = json.loads(DATASET.read_text())
    row = next(r for r in rows if r['instance_id'] == instance)
    image = row['image']
    marker = 'diff --git a/.ttgl_control b/.ttgl_control\nnew file mode 100644\nindex 0000000..ef8d6a6\n--- /dev/null\n+++ b/.ttgl_control\n@@ -0,0 +1 @@\n+environment control only\n'
    pred = {'instance_id': instance, 'model_name_or_path': 'base-control', 'model_patch': marker}
    (ROOT / f'{instance}.base.jsonl').write_text(json.dumps(pred) + '\n')
    owned = subprocess.run(['docker', 'image', 'inspect', image], capture_output=True).returncode != 0
    state = {'instance_id': instance, 'image_tag': image, 'started_at': now(),
             'image_owned_by_this_run': owned, 'model_inference_calls': 0, 'controls': [],
             'runner_sha256': sha(__file__),
             'disk_free_before_bytes': shutil.disk_usage('/workspace').free}
    state_path = ROOT / f'{instance}.execution.json'
    if state_path.exists(): raise RuntimeError('Preserve existing execution; no implicit replay')
    write(state_path, state)
    if state['disk_free_before_bytes'] < 23 * GIB:
        state['status'] = 'not_started_insufficient_disk'; write(state_path, state); return
    if owned:
        with (ROOT / f'{instance}.pull.log').open('w') as log:
            started = time.monotonic()
            pull = subprocess.Popen(['docker', 'pull', image], stdout=log, stderr=subprocess.STDOUT)
            while pull.poll() is None:
                if shutil.disk_usage('/workspace').free < 4 * GIB or time.monotonic() - started > 900:
                    state['pull_stopped'] = 'disk_below_4gib_or_timeout_900seconds'
                    pull.terminate()
                    try: pull.wait(timeout=60)
                    except subprocess.TimeoutExpired: pull.kill(); pull.wait()
                    break
                time.sleep(2)
        state['pull_exit_code'] = pull.returncode
        if pull.returncode or state.get('pull_stopped'):
            state['status'] = 'image_pull_failed'; write(state_path, state); return
    info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image], text=True))[0]
    state.update(image_id=info['Id'], image_repo_digests=info.get('RepoDigests', []),
                 image_logical_size_bytes=info['Size'], disk_free_after_pull_bytes=shutil.disk_usage('/workspace').free)
    write(state_path, state)
    if state['disk_free_after_pull_bytes'] < max(6 * GIB, 2.5 * info['Size'] + 2 * GIB):
        state['status'] = 'image_pulled_insufficient_container_disk'; write(state_path, state); return
    for control in ('gold', 'base'):
        command = [PYTHON, str(Path(__file__).resolve()), '--child', '--instance', instance, '--control', control]
        env = os.environ.copy()
        for key in ('DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'):
            env.pop(key, None)
        started = time.monotonic()
        timed_out = False
        try:
            with (ROOT / f'{instance}.{control}.stdout.log').open('w') as stream:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=900)
            process_exit_code = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            process_exit_code = None
            # Only this exact official control's container may be removed.
            name = f'sweb.eval.{instance}.ttgl-verified-002-{control}-{instance}'
            with (ROOT / f'{instance}.{control}.timeout_cleanup.log').open('w') as stream:
                subprocess.run(['docker', 'rm', '-f', name], stdout=stream, stderr=subprocess.STDOUT, timeout=180)
        rid = f'ttgl-verified-002-{control}-{instance}'
        model = 'gold' if control == 'gold' else 'base-control'
        report = ROOT / 'logs/evaluation' / rid / model / instance / 'report.json'
        entry = {'control': control, 'run_id': rid, 'process_exit_code': process_exit_code,
                 'process_timed_out': timed_out,
                 'wall_seconds': time.monotonic() - started, 'report': str(report.relative_to(ROOT)),
                 'report_sha256': sha(report) if report.exists() else None}
        if report.exists():
            content = json.loads(report.read_text())[instance]
            entry.update(resolved=content['resolved'], official_infra_failure=content.get('infra_failure'),
                         patch_successfully_applied=content.get('patch_successfully_applied'),
                         tests={k: {a: len(b) for a,b in v.items()} for k,v in content['tests_status'].items()})
        state['controls'].append(entry); write(state_path, state)
        print(json.dumps({'instance': instance, **entry}), flush=True)
    state['status'] = 'controls_complete'
    state['finished_at'] = now()
    write(state_path, state)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', required=True)
    parser.add_argument('--control', choices=('gold','base'))
    parser.add_argument('--child', action='store_true')
    parser.add_argument('--cleanup', action='store_true')
    args = parser.parse_args()
    if args.cleanup: cleanup(args.instance)
    elif args.child: child(args.instance, args.control)
    else: execute(args.instance)
