#!/usr/bin/env python3
"""Assess the 95/95 target using complete, paired official-grade records."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, frontier

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--records', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--reference', default='large')
args = parser.parse_args()
records = json.loads(args.records.read_text())
arms = sorted({row['arm'] for row in records} - {args.reference})
report = {'records_sha256': benchmark.digest(args.records),
          'source_sha256': benchmark.digest(Path(frontier.__file__)),
          'comparisons': [frontier.compare(records, policy=arm, reference=args.reference) for arm in arms],
          'added_value_vs_luna': [frontier.added_value(records,policy=arm,strong=args.reference)
                                  for arm in arms if arm!='small'] if args.reference!='small' else []}
benchmark.write_new(args.output, report)
print(json.dumps(report, indent=2))
