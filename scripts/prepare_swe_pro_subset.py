#!/usr/bin/env python3
"""Reserve small outcome-independent Pro V2 panels; download public inputs only."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

REVISION = '66f92766bba642462d4bbe5479e83f91f9211862'
REPOSITORY = 'scaleapi/SWE-bench_Pro-os'
SEED = 'ttgl-pro-prompt-001'


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'TTGL-research'}), timeout=60) as response:
        return response.read()


def reserve(paths, dev_count=12, held_count=24):
    groups = defaultdict(list)
    for path in paths:
        key = path.split('/')[2]
        match = re.fullmatch(r'instance_(.+)-[0-9a-f]{40}(?:-v.*)?', key)
        if not match:
            raise ValueError('Unrecognized task identity: '+key)
        groups[match.group(1)].append(key)
    for group in groups.values():
        group.sort(key=lambda key: hashlib.sha256((SEED+':'+key).encode()).hexdigest())
    # Round-robin across repositories, with seeded repository order.
    repositories = sorted(groups, key=lambda key: hashlib.sha256((SEED+':repo:'+key).encode()).hexdigest())
    ranked = []
    while len(ranked) < dev_count+held_count:
        added = False
        for repo in repositories:
            if groups[repo]:
                ranked.append({'instance_id': groups[repo].pop(0), 'repository': repo.replace('__', '/', 1)})
                added = True
        if not added:
            raise ValueError('Insufficient tasks')
    return ranked[:dev_count], ranked[dev_count:dev_count+held_count]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Choose a new reservation directory')
    raw = fetch(f'https://api.github.com/repos/{REPOSITORY}/git/trees/{REVISION}?recursive=1')
    tree = json.loads(raw)
    if tree.get('truncated'):
        raise ValueError('Incomplete upstream inventory')
    paths = [r['path'] for r in tree['tree'] if r['path'].startswith('v2/tasks/') and r['path'].endswith('/instruction.md')]
    if len(paths) != 642:
        raise ValueError('Pinned V2 inventory changed')
    dev, held = reserve(paths)
    args.output.mkdir(parents=True)
    (args.output/'upstream-tree.json').write_bytes(raw)
    for row in dev+held:
        public = args.output/'public'/row['instance_id']
        public.mkdir(parents=True)
        row['files'] = {}
        for name in ('instruction.md', 'task.toml', 'environment/Dockerfile'):
            data = fetch(f'https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/v2/tasks/{row["instance_id"]}/{name}')
            target = public/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            row['files'][name] = {'path': str(target), 'sha256': hashlib.sha256(data).hexdigest()}
    manifest = {'status': 'reserved_public_inputs_only_not_executed', 'dataset': 'SWE-bench Pro V2',
                'upstream_repository': REPOSITORY, 'revision': REVISION, 'population_tasks': 642,
                'inventory_sha256': hashlib.sha256(raw).hexdigest(), 'seed': SEED,
                'selection': 'Seeded task order within repository, seeded round-robin across repositories; no outcome selection',
                'development': dev, 'held_out': held,
                'private_tests_or_reference_solutions_downloaded': False,
                'full_population_run_authorized_by_this_manifest': False,
                'inference_calls': 0}
    (args.output/'reservation.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'development': len(dev), 'held_out': len(held), 'inference_calls': 0}))


if __name__ == '__main__':
    main()
