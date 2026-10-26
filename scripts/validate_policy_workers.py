#!/usr/bin/env python3
"""Reuse the staged-worker validator with one new repository smoke probe."""
import argparse
from pathlib import Path

import validate_swe_workers as validator
from ttgl import benchmark


if __name__ == '__main__':
    # The new panel includes Pylint. This public parser test was chosen by
    # inspecting its pinned source tree, without reference patches or outcomes.
    validator.SMOKES['pylint-dev/pylint'] = 'python -m pytest -q tests/test_pragma_parser.py'
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output', type=Path)
    args, _ = parser.parse_known_args()
    try:
        validator.main()
    finally:
        if args.output is not None and args.output.is_dir():
            benchmark.write_new(args.output / 'policy-validator-source.json', {
                'driver_sha256': benchmark.digest(Path(__file__)),
                'base_validator_sha256': benchmark.digest(Path(validator.__file__)),
                'public_smoke_commands': validator.SMOKES,
                'inference_calls': 0})
