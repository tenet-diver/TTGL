#!/usr/bin/env python3
"""Reuse independently verified exact-program grades without reusing model attempts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-study', type=Path, required=True)
parser.add_argument('--target-study', type=Path, required=True)
args = parser.parse_args()
source, target = args.source_study.resolve(), args.target_study.resolve()
if list(target.glob('runs/*/*/state.json')) or (target/'grades.json').exists() or (target/'grade-cache.json').exists():
    raise ValueError('Seed only a new scored study before its assignments start')
environments = []
for study in (source,target):
    if benchmark.digest(study/'environment.json') != (study/'environment.sha256').read_text().strip():
        raise ValueError('Frozen grading environment changed')
    environments.append(json.loads((study/'environment.json').read_text()))
fields = ['evaluator_image_id','private_grading_dataset_sha256','grading_timeout_seconds']
if any(environments[0][key] != environments[1][key] for key in fields):
    raise ValueError('Evaluator, full grading dataset or timeout differs; do not reuse grades')
raw = (source/'grade-cache.json').read_bytes()
cache = json.loads(raw)
for row in cache.values():
    if benchmark.digest(Path(row['report'])) != row['report_sha256']:
        raise ValueError('Original official report changed')
snapshot = target/'grade-cache-seed/source-cache.json'
benchmark.write_new(snapshot,cache)
benchmark.write_new(target/'grade-cache-seed/provenance.json',{
    'kind':'seed_exact_program_evaluation_cache_before_new_independent_inference',
    'source_study':str(source),'source_cache_observed_sha256':hashlib.sha256(raw).hexdigest(),
    'snapshot_sha256':benchmark.digest(snapshot),
    'source_environment_sha256':benchmark.digest(source/'environment.json'),
    'target_environment_sha256':benchmark.digest(target/'environment.json'),
    'verified_report_entries':len(cache),'grading_invariants':{key:environments[0][key] for key in fields},
    'model_attempts_reused':False,'new_grading_executions':0,
    'lookup_validation':'Existing evaluator recomputes task/patch/image/dataset/timeout key and verifies original report and exact patch.diff on each hit',
    'script_sha256':benchmark.digest(Path(__file__))})
benchmark.write_new(target/'grade-cache.json',cache)
print(json.dumps({'seeded_reports':len(cache),'model_attempts_reused':False}))
