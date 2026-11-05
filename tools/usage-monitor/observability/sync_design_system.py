#!/usr/bin/env python3
"""Copy the pinned private DOM distribution without running producer code/hooks."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
LOCK = REPO / 'tools/usage-monitor/config/design-system.lock.json'


def sync(source, destination, check=False):
    lock = json.loads(LOCK.read_text())
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, expected in lock['files'].items():
        if check:
            data = (destination / name).read_bytes()
        else:
            data = subprocess.check_output(['git', '-C', str(source), 'show', lock['commit'] + ':dist/' + name])
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Design-system artifact hash mismatch: ' + name)
        if not check:
            (destination / name).write_bytes(data)
    if not check:
        (destination / 'manifest.json').write_text(json.dumps(lock, indent=2) + '\n')
    print('Pinned private design assets verified' if check else 'Pinned private design assets synced; no producer code executed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Authenticated local design-system checkout containing the pinned commit')
    parser.add_argument('--destination', type=Path, default=REPO / 'work/security/design-system')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not args.check and not args.source:
        parser.error('--source is required when syncing')
    sync(args.source, args.destination, args.check)
