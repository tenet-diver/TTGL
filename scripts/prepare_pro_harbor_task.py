#!/usr/bin/env python3
"""Acquire one reserved official Harbor task outside all solver workspaces.

Copies pinned upstream files unchanged; does not run a model, tests or a grader.
Reference/verifier content remains in this private evaluator directory.
"""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_swe_pro_subset import fetch, REVISION, REPOSITORY

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reservation', type=Path, default=ROOT/'experiments/swe-pro-prompt-001/reservation.json')
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Use a fresh evaluator directory outside the research repository')
    reserved = json.loads(args.reservation.read_text())
    if reserved['revision'] != REVISION:
        raise ValueError('Reservation revision differs from the pinned preparation source')
    selected = [r for r in reserved['development']+reserved['held_out'] if r['instance_id']==args.task_id]
    if len(selected) != 1:
        raise ValueError('Task must belong to exactly one reserved partition')
    inventory = (args.reservation.parent/'upstream-tree.json').read_bytes()
    if hashlib.sha256(inventory).hexdigest() != reserved['inventory_sha256']:
        raise ValueError('Upstream inventory changed')
    entries = json.loads(inventory)['tree']
    prefix = f'v2/tasks/{args.task_id}/'
    files = [r for r in entries if r['type']=='blob' and
             (r['path'].startswith(prefix) or r['path']=='v2/tooling/patch_replay.py')]
    if not any(r['path']==prefix+'tests/test.sh' for r in files):
        raise ValueError('Missing official verifier')
    output.mkdir(parents=True)
    records = []
    for row in files:
        path = Path(row['path'])
        if '..' in path.parts or path.is_absolute() or row['mode'] not in ('100644','100755'):
            raise ValueError('Unsupported upstream file')
        raw = fetch(f'https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/{row["path"]}')
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob != row['sha']:
            raise ValueError('Downloaded file does not match pinned upstream Git blob')
        target = output/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(0o755 if row['mode']=='100755' else 0o644)
        records.append({'path':row['path'], 'git_blob':blob, 'sha256':hashlib.sha256(raw).hexdigest()})
    for name, original in selected[0]['files'].items():
        if hashlib.sha256((output/prefix/name).read_bytes()).hexdigest() != original['sha256']:
            raise ValueError('Task public inputs differ from the reservation')
    receipt = {'status':'prepared_not_controlled_or_scored', 'task_id':args.task_id,
               'revision':REVISION, 'files':records, 'inference_calls':0,
               'reservation_sha256':hashlib.sha256(args.reservation.read_bytes()).hexdigest(),
               'verifier':'Unchanged upstream Harbor task and fresh PatchReplayAgent regrade required',
               'boundary':'Private evaluator files; never mount this directory in an acting model workspace'}
    (output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'task_id':args.task_id,'files':len(records),'inference_calls':0}))


if __name__ == '__main__':
    main()
