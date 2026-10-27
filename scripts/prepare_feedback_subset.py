#!/usr/bin/env python3
"""Reserve a bounded Aider-derived test-feedback diagnostic, without inference."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

REPOSITORY = 'Aider-AI/polyglot-benchmark'
REVISION = '7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f'
SEED = 'ttgl-verification-feedback-001'
LANGUAGES = ('cpp', 'go', 'java', 'javascript', 'python', 'rust')


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'TTGL-research'}), timeout=60) as response:
        return response.read()


def reserve(tree):
    if tree.get('truncated') or tree.get('sha') != REVISION:
        raise ValueError('Require the complete pinned inventory')
    paths = [r['path'] for r in tree['tree'] if r['path'].endswith('/.docs/instructions.md')]
    if len(paths) != 225 or len(set(paths)) != 225:
        raise ValueError('Unexpected exercise inventory')
    groups = {language: [] for language in LANGUAGES}
    for path in paths:
        parts = path.split('/')
        if len(parts) != 6 or parts[0] not in groups or parts[1:3] != ['exercises', 'practice']:
            raise ValueError('Unexpected exercise path')
        groups[parts[0]].append({'task_id': parts[0] + '/' + parts[3],
                                'language': parts[0], 'exercise_family': parts[3],
                                'instructions_path': path})
    for rows in groups.values():
        rows.sort(key=lambda row: hashlib.sha256((SEED + ':' + row['task_id']).encode()).hexdigest())
    dev = [groups[language][i] for i in range(2) for language in LANGUAGES]
    dev_families = {r['exercise_family'] for r in dev}
    held_groups = {language: [r for r in rows if r['exercise_family'] not in dev_families]
                   for language, rows in groups.items()}
    if any(len(rows) < 4 for rows in held_groups.values()):
        raise ValueError('Insufficient disjoint exercise families')
    held = [held_groups[language][i] for i in range(4) for language in LANGUAGES]
    return dev, held


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--inventory', type=Path, help='Previously fetched exact Git tree, optional')
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Choose a new reservation directory')
    raw = (args.inventory.read_bytes() if args.inventory else
           fetch(f'https://api.github.com/repos/{REPOSITORY}/git/trees/{REVISION}?recursive=1'))
    tree = json.loads(raw)
    dev, held = reserve(tree)
    entries = {r['path']: r for r in tree['tree']}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'upstream-tree.json').write_bytes(raw)
    for row in dev + held:
        data = fetch(f'https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/{row["instructions_path"]}')
        git_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if git_blob != entries[row['instructions_path']]['sha']:
            raise ValueError('Instructions do not match pinned Git blob')
        target = Path('public')/row['task_id']/'instructions.md'
        (args.output/target).parent.mkdir(parents=True, exist_ok=True)
        (args.output/target).write_bytes(data)
        row['instructions'] = {'path': str(target), 'sha256': hashlib.sha256(data).hexdigest(),
                               'git_blob': git_blob}
    manifest = {
        'status': 'reserved_not_executed', 'dataset': 'Aider Polyglot derived feedback diagnostic',
        'repository': REPOSITORY, 'revision': REVISION, 'population_tasks': 225,
        'population_by_language': dict(Counter(p.split('/')[0] for p in entries
                                                if p.endswith('/.docs/instructions.md'))),
        'seed': SEED, 'inventory_sha256': hashlib.sha256(raw).hexdigest(),
        'selection': 'Two development and four validation tasks per language, hash-ranked; exclude every development exercise family across all validation languages',
        'development': dev, 'held_out': held,
        'reference_solutions_downloaded': False, 'test_files_downloaded': False,
        'inference_calls': 0, 'full_population_auto_run': False,
        'claim_scope': 'Custom conversational harness and feedback budget; not an official Aider leaderboard score',
        'licensing': 'Exercise content credited to Exercism; preserve per-track licenses before redistributing source or tests',
    }
    (args.output/'reservation.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'development': len(dev), 'held_out': len(held), 'inference_calls': 0}))


if __name__ == '__main__':
    main()
