#!/usr/bin/env python3
"""Fetch only the previously reviewed SlopCodeBench fixture bytes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "experiments/decision-history-scb-001/source-receipt.json"


def fetch(root, revision, name, expected):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or path.parts[0] not in ("cfgpipe", "l2m"):
        raise ValueError("Unexpected fixture path")
    destination = root / "upstream" / path
    if destination.exists():
        contents = destination.read_bytes()
    else:
        with urlopen(f"https://raw.githubusercontent.com/gabeorlanski/scb-problems/{revision}/{name}", timeout=20) as response:
            contents = response.read(512 * 1024 + 1)
    if len(contents) > 512 * 1024 or hashlib.sha256(contents).hexdigest() != expected:
        raise ValueError(f"Integrity mismatch for {name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with destination.open("xb") as stream:
            stream.write(contents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "work/security/decision-history-scb-001")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_relative_to((ROOT / "work/security").resolve()):
        parser.error("Fixture data belong in work/security")
    data = json.loads(RECEIPT.read_text())
    with ThreadPoolExecutor(max_workers=8) as pool:
        uploads = [pool.submit(fetch, root, data["revision"], name, expected)
                   for name, expected in data["files"].items()]
        for upload in uploads:
            upload.result()
    destination = root / "security-receipt.json"
    if not destination.exists():
        with destination.open("xb") as stream:
            stream.write(RECEIPT.read_bytes())
    print(f"Verified {len(data['files'])} pinned fixture files")


if __name__ == "__main__":
    main()
