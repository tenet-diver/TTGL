#!/usr/bin/env python3
"""Run independent official base/gold controls, retaining failed environments.

Only the trusted evaluator receives the private dataset and Docker socket.
No model calls are made. A separate result directory preserves each attempt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl.benchmark import digest, read_tasks, write_new
from ttgl.isolated import docker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tasks', type=Path, default=Path('experiments/swe-bench-verified-001/tasks.json'))
    parser.add_argument('--evaluator-image', default='ttgl-evaluator:20261026-cli')
    parser.add_argument('--resume', action='store_true', help='Verify and retain completed controls; continue only untouched tasks')
    args = parser.parse_args()
    private, output = args.private_root.resolve(), args.output.resolve()
    dataset = private / 'selected.dataset.json'
    public = read_tasks(args.tasks)
    selected = json.loads(dataset.read_text())
    lookup = {row['instance_id']: row for row in selected}
    if set(lookup) != {row['instance_id'] for row in public['tasks']}:
        raise ValueError('Public/private panels differ')
    if output.exists() and not args.resume:
        raise ValueError('Choose a new controls output directory or explicitly resume')
    if args.resume and not (output / 'protocol.json').is_file():
        raise ValueError('Resume requires an existing control protocol')
    output.mkdir(parents=True, exist_ok=args.resume)
    control = ('diff --git a/.ttgl_control b/.ttgl_control\nnew file mode 100644\n'
               'index 0000000..85c3040\n--- /dev/null\n+++ b/.ttgl_control\n'
               '@@ -0,0 +1 @@\n+base control\n')
    predictions = private / (output.name + '-base.jsonl')
    prediction_text = ''.join(json.dumps({'instance_id': task['instance_id'],
        'model_name_or_path': 'base-control', 'model_patch': control}) + '\n' for task in public['tasks'])
    if args.resume:
        if predictions.read_text() != prediction_text:
            raise ValueError('Original control predictions changed')
    else:
        predictions.write_text(prediction_text)
    evaluator = json.loads(docker('image', 'inspect', args.evaluator_image))[0]['Id']
    protocol = {
        'tasks_sha256': digest(args.tasks), 'private_dataset_sha256': digest(dataset),
        'evaluator_image_id': evaluator, 'script_sha256': digest(Path(__file__)),
        'timeout_seconds': 600, 'workers': 1,
        'eligibility_rule': 'gold resolved=true and base resolved=false, with no infrastructure failure',
        'selection': 'all frozen tasks; no replacement based on model outcomes',
        'inference_calls': 0,
    }
    if args.resume:
        original = json.loads((output / 'protocol.json').read_text())
        if {k:v for k,v in original.items() if k != 'script_sha256'} != {k:v for k,v in protocol.items() if k != 'script_sha256'}:
            raise ValueError('Original control settings changed')
        write_new(output / ('resume-' + uuid.uuid4().hex[:12] + '.json'), {
            'protocol_sha256': digest(output / 'protocol.json'), 'source_sha256': digest(Path(__file__)),
            'reason': 'Continue untouched tasks after host free-space guard; no completed control replay',
        })
    else:
        write_new(output / 'protocol.json', protocol)
    rows = []
    for task in public['tasks']:
        instance = task['instance_id']
        recorded = output / (instance + '.json')
        if args.resume and recorded.exists():
            row = json.loads(recorded.read_text())
            for kind, result in row['controls'].items():
                report_path = output / result['report']
                if digest(report_path) != result['report_sha256']:
                    raise ValueError('Completed native control report changed')
                native = json.loads(report_path.read_text())[instance]
                if native.get('infra_failure') is not False or native.get('resolved') != result['resolved']:
                    raise ValueError('Completed control provenance or infrastructure status invalid')
            rows.append(row)
            continue
        if args.resume and any(output.glob(instance + '-*.stdout.txt')):
            raise ValueError('Partial control requires explicit reconciliation; no automatic replay')
        if shutil.disk_usage(private).free < 10 * 1024**3:
            raise RuntimeError('Less than 10 GiB free; preserve completed controls')
        row = {'instance_id': instance, 'controls': {}}
        for kind in ('base', 'gold'):
            run_id = 'ttgl-desktop-' + output.name + '-' + kind + '-' + instance
            command = ['docker', 'run', '--rm', '-v', '/var/run/docker.sock:/var/run/docker.sock',
                       '-v', f'{private}:{private}', '-w', str(private), evaluator,
                       'eval', str(dataset), '--instance', instance,
                       '--run-id', run_id, '--workers', '1', '--timeout', '600']
            command += ['--gold'] if kind == 'gold' else ['--predictions', str(predictions)]
            started = time.monotonic()
            with (output / f'{instance}-{kind}.stdout.txt').open('x') as stream:
                result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
            source = private / 'logs/evaluation' / run_id
            target = output / 'logs' / run_id
            if source.exists():
                shutil.copytree(source, target)
            reports = list(target.glob('**/report.json')) if target.exists() else []
            report = json.loads(reports[0].read_text()).get(instance, {}) if len(reports) == 1 else {}
            row['controls'][kind] = {
                'returncode': result.returncode, 'elapsed_seconds': time.monotonic()-started,
                'report': str(reports[0].relative_to(output)) if len(reports) == 1 else None,
                'resolved': report.get('resolved'), 'infra_failure': report.get('infra_failure'), 'report_sha256': digest(reports[0]) if len(reports)==1 else None,
            }
            print(json.dumps({'instance': instance, 'control': kind, **row['controls'][kind]}), flush=True)
        image = lookup[instance]['image']
        inspected = json.loads(docker('image', 'inspect', image))[0]
        row['image'] = {'reference': inspected['RepoDigests'][0], 'image_id': inspected['Id'],
                        'size_bytes': inspected['Size']}
        row['eligible'] = (row['controls']['base']['resolved'] is False
                           and row['controls']['gold']['resolved'] is True
                           and all(r['infra_failure'] is False for r in row['controls'].values()))
        rows.append(row)
        write_new(output / (instance + '.json'), row)
        # Only this control's benchmark image is removed; no shared caches or
        # other workloads are pruned during execution. Digest enables re-pull.
        docker('image', 'rm', image)
    write_new(output / 'summary.json', {'tasks': rows, 'eligible': [r['instance_id'] for r in rows if r['eligible']]})


if __name__ == '__main__':
    main()
