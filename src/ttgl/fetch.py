"""Retrieve pinned upstream benchmark artifacts with mandatory SHA-256 checks."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

from ttgl.data import SOURCE_COMMIT, SOURCE_HASHES


def fetch(destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    for model, digest in SOURCE_HASHES.items():
        url = (f"https://raw.githubusercontent.com/LiveCodeBench/submissions/{SOURCE_COMMIT}/"
               f"{model}/Scenario.codegeneration_10_0.2_eval_all.json")
        target = destination / f"{model}.json"
        if target.exists():
            content = target.read_bytes()
        else:
            with urllib.request.urlopen(url, timeout=120) as response:
                content = response.read(64 * 1024 * 1024 + 1)
            if len(content) > 64 * 1024 * 1024:
                raise ValueError("Unexpected artifact size")
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError(f"Source checksum mismatch for {model}; existing file left unchanged")
        if not target.exists():
            target.write_bytes(content)
        provenance = {"model": model, "url": url, "pinned_url": url,
                      "source_commit": SOURCE_COMMIT, "sha256": digest,
                      "bytes": len(content), "verified_pinned_sha256": True,
                      "retrieved_at_utc": datetime.now(timezone.utc).isoformat()}
        sidecar = destination / f"{model}.provenance.json"
        if not sidecar.exists():
            sidecar.write_text(json.dumps(provenance, indent=2) + "\n")
        print(f"Verified {model}: {len(content)} bytes, sha256={digest}")
    license_path = destination / "UPSTREAM_LICENSE"
    if not license_path.exists():
        url = f"https://raw.githubusercontent.com/LiveCodeBench/submissions/{SOURCE_COMMIT}/LICENSE"
        with urllib.request.urlopen(url, timeout=30) as response:
            license_path.write_bytes(response.read())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/livecodebench"))
    args = parser.parse_args()
    fetch(args.raw_dir)
