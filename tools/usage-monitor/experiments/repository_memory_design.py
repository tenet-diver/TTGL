"""Metadata-only reservation for a longitudinal memory experiment.

No downloaded code is executed, no target text or grading fields are read, and
no model is called. This is a design/temporal-boundary audit, not an efficacy
benchmark. The upstream benchmark's ordinal history rule is preserved; issue
numbers must not be misrepresented as verified real-world timestamps.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


FIELDS = {'instance_id', 'repo', 'base_commit', 'language', 'image_name',
          'created_at', 'license'}
LICENSES = {'Apache-2.0', 'MIT', 'MIT-0', 'BSD-2-Clause', 'BSD-3-Clause'}


def issue_number(instance):
    match = re.fullmatch(r'(.+)-(\d+)', instance)
    if not match:
        raise ValueError('Invalid instance identifier')
    return int(match[2])


def validate_targets(rows):
    seen = set()
    for row in rows:
        if (set(row) != FIELDS or any(not isinstance(v, str) or not v
                                     for k, v in row.items() if k != 'license')
                or row['license'] is not None and not isinstance(row['license'], str)):
            raise ValueError('Require the exact metadata allowlist; no task/grading fields')
        if row['instance_id'] in seen:
            raise ValueError('Duplicate target')
        seen.add(row['instance_id'])
        if (row['instance_id'].rsplit('-', 1)[0].casefold()
                != row['repo'].replace('/', '__').casefold()):
            raise ValueError('Repository/target mismatch')
        issue_number(row['instance_id'])
        if not re.fullmatch(r'[0-9a-f]{40}', row['base_commit']):
            raise ValueError('Unpinned base commit')


def earlier_history(target, paths):
    """Strictly earlier, same-repository trajectories; never the target itself."""
    prefix = 'history/' + target['language'] + '/' + target['repo'].replace('/', '__') + '/'
    selected = {}
    for path in paths:
        if not path.startswith(prefix):
            continue
        parts = path[len(prefix):].split('/')
        if len(parts) != 2 or parts[1] != parts[0] + '.traj.json':
            raise ValueError('Unexpected trajectory layout')
        ident = parts[0]
        if ident.rsplit('-', 1)[0].casefold() != target['repo'].replace('/', '__').casefold():
            raise ValueError('History repository mismatch')
        if ident in selected:
            raise ValueError('Duplicate history path')
        if issue_number(ident) < issue_number(target['instance_id']):
            selected[ident] = path
    return [selected[k] for k in sorted(selected, key=issue_number)]


def audit(rows, paths):
    validate_targets(rows)
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate input paths')
    counts = Counter(r['repo'] for r in rows)
    candidates = sorted({r['repo'] for r in rows if r['language'] == 'python'
                         and counts[r['repo']] >= 2
                         and all(t['license'] in LICENSES for t in rows if t['repo'] == r['repo'])},
                        key=lambda repo: (-counts[repo], repo.casefold()))
    if len(candidates) < 2:
        raise ValueError('Need disjoint development and reserved repositories')
    chosen = {}
    for split, repo in zip(('development', 'reserved_validation'), candidates[:2]):
        targets = sorted((r for r in rows if r['repo'] == repo),
                         key=lambda row: issue_number(row['instance_id']))
        chosen[split] = {'repo': repo, 'targets': [dict(r,
            eligible_history_count=len(earlier_history(r, paths)),
            bounded_history_ids=[p.split('/')[-2] for p in earlier_history(r, paths)[-8:]])
            for r in targets]}
    return dict(status='metadata reservation; no new model trials or official scores',
        target_count=len(rows), repository_count=len(counts),
        repeated_python_repositories=sorted([
            {'repo': repo, 'target_count': n} for repo, n in counts.items()
            if n >= 2 and any(r['repo'] == repo and r['language'] == 'python' for r in rows)],
            key=lambda r: (-r['target_count'], r['repo'].casefold())),
        selection_rule='Python; >=2 targets; explicit allowlisted license; descending target count, casefolded repository tie-break. First repository development, second reserved validation. Metadata selection precedes target-content inspection and inference.',
        history_rule='Same repository/language, history issue ordinal strictly less than target ordinal; latest eight eligible histories for bounded development. Ordinals are not verified wall-clock chronology.',
        partitions=chosen, model_calls=0, target_text_inspected=False,
        hidden_grading_fields_used=False, official_benchmark_score=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--targets', type=Path, required=True)
    parser.add_argument('--dataset-metadata', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.targets.read_text())
    metadata = json.loads(args.dataset_metadata.read_text())
    result = audit(rows, [s['rfilename'] for s in metadata['siblings']
                          if s['rfilename'].startswith('history/')])
    result['dataset_repository'] = 'Tongyi-ConvAI/VibeMemBench'
    result['observed_dataset_revision'] = metadata['sha']
    result['metadata_allowlist_sha256'] = hashlib.sha256(args.targets.read_bytes()).hexdigest()
    result['provenance_limit'] = 'Rows obtained from dataset-viewer HTTP responses; exact allowlist bytes sealed. Dataset API revision recorded separately. Pinned Parquet/viewer equivalence remains an execution gate.'
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')


if __name__ == '__main__':
    main()
