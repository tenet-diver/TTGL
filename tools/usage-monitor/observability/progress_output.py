#!/usr/bin/env python3
"""Conservatively compact plain Docker pull updates, retaining all other lines."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

# Exact plain-mode shapes only. Errors, warnings, unknown formats, ANSI and terminal
# layer/image outcomes remain untouched. No generic truncation or LLM summarization.
PROGRESS = re.compile(r'^\s*[a-f0-9]{12,64}\s+(?:Pulling fs layer|Downloading|Extracting|Waiting)\s+(?:\d+(?:\.\d+)?(?:[kMGTPE]?B)(?:/\d+(?:\.\d+)?[kMGTPE]?B)?)\s*$')


def compact(text):
    kept, removed = [], 0
    for line in text.splitlines(keepends=True):
        if PROGRESS.fullmatch(line.rstrip('\r\n')):
            removed += 1
        else:
            kept.append(line)
    return dict(output=''.join(kept), removed_lines=removed,
                original_bytes=len(text.encode()), retained_bytes=len(''.join(kept).encode()),
                raw_sha256=hashlib.sha256(text.encode()).hexdigest(),
                policy='docker-plain-progress-v1; unknown lines and terminal outcomes preserved')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path, help='Retained raw log; source file is never modified')
    args = parser.parse_args()
    result = compact(args.path.read_bytes().decode('utf-8'))
    result['raw_path'] = str(args.path.resolve())
    print(json.dumps(result))


if __name__ == '__main__':
    main()
