#!/usr/bin/env python3
"""Prepare a frozen SWE-bench Verified sample from its official task repository.

Run with the pinned SWE-bench environment. The task repository is an official
standalone distribution; it reconstructs the dataset without Hugging Face.
Reference patches, test patches and grading scripts remain in the evaluator
directory. Only issue text and repository metadata enter the public manifest.
This script performs no inference and does not create experimental results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from urllib.request import urlopen

TASK_REVISION = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"
TASK_ARCHIVE_SHA256 = "ff31aa1f8d2bb78f16559524264a99b868b7218ca82b390dc750bbc59538aa20"
HARNESS_REVISION = "02e7a74ffd0b707aab73d203fe87bdc7c76afc8e"
HARNESS_ARCHIVE_SHA256 = "d06181d5365b51fc7ff490171581b9ee87d77e19b3a739a8d574bf25d9ef9479"
DATASET = "SWE-bench/SWE-bench_Verified"
SEED = "ttgl-swe-verified-001"
ROOT = Path(__file__).resolve().parents[1]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_once(path: Path, value: dict | list) -> str:
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    if path.exists() and path.read_bytes() != raw:
        raise ValueError(f"refusing to replace a different frozen artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return digest(raw)


def archive(repo: str, revision: str, expected: str, path: Path) -> Path:
    if not path.exists():
        with urlopen(f"https://codeload.github.com/{repo}/tar.gz/{revision}", timeout=90) as response:
            raw = response.read()
        if digest(raw) != expected:
            raise ValueError(f"archive checksum mismatch for {repo}")
        path.write_bytes(raw)
    if digest(path.read_bytes()) != expected:
        raise ValueError(f"cached archive checksum mismatch: {path}")
    target = path.parent / f"{repo.split('/')[-1]}-{revision}"
    if not target.exists():
        with tarfile.open(path) as stream:
            stream.extractall(path.parent, filter="data")
    with tarfile.open(path) as stream:
        for member in stream.getmembers():
            if member.isfile():
                local = path.parent / member.name
                archived = stream.extractfile(member)
                if archived is None or not local.is_file() or digest(local.read_bytes()) != digest(archived.read()):
                    raise ValueError(f"extracted source differs from its verified archive: {local}")
    return target


def prepare(evaluator_root: Path, output: Path, count: int) -> dict:
    import yaml
    from swebench.task.repo import load_task

    if not 1 <= count <= 500:
        raise ValueError("count must be between 1 and 500")
    evaluator_root.mkdir(parents=True, exist_ok=True)
    task_repo = archive("SWE-bench/swe-bench-tasks", TASK_REVISION,
                        TASK_ARCHIVE_SHA256, evaluator_root / "task-repo.tar.gz")
    candidates = []
    for path in (task_repo / "tasks").glob("*/task.yaml"):
        meta = yaml.safe_load(path.read_text())
        if DATASET in meta.get("datasets", []) and meta.get("split") == "test":
            candidates.append(meta)
    if len(candidates) != 500:
        raise ValueError(f"expected 500 Verified tasks; got {len(candidates)}")
    candidates.sort(key=lambda row: digest(f"{SEED}:{row['instance_id']}".encode()))
    selected = candidates[:count]
    public, private, provenance = [], [], []
    for row in selected:
        path = task_repo / "tasks" / row["instance_id"]
        public.append({key: row[key] for key in ("instance_id", "repo", "base_commit")} |
                      {"problem_statement": (path / "problem_statement.md").read_text()})
        private.append(load_task(path))
        provenance.append({"instance_id": row["instance_id"], "image": row["image"],
                           "files_sha256": {p.name: digest(p.read_bytes()) for p in sorted(path.iterdir()) if p.is_file()}})
    manifest = {
        "schema_version": 1, "dataset_id": DATASET,
        "dataset_revision": TASK_REVISION,
        "dataset_revision_kind": "official_task_repository_git_commit",
        "task_repository": "https://github.com/SWE-bench/swe-bench-tasks",
        "harness_commit": HARNESS_REVISION,
        "selection": {"method": "first n after SHA256(seed + ':' + instance_id) ascending",
                      "seed": SEED, "assigned_tasks": count, "population_tasks": 500,
                      "selection_uses_model_outcomes": False},
        "tasks": public,
    }
    public_hash = write_once(output / "tasks.json", manifest)
    private_path = evaluator_root / "selected.dataset.json"
    private_hash = write_once(private_path, private)
    freeze = {
        "schema_version": 1, "experiment_id": "swe-bench-verified-001",
        "status": "prepared_not_executed", "tasks_sha256": public_hash,
        "private_dataset_sha256": private_hash,
        "task_archive_sha256": TASK_ARCHIVE_SHA256,
        "harness_commit": HARNESS_REVISION,
        "harness_archive_sha256": HARNESS_ARCHIVE_SHA256,
        "task_revision": TASK_REVISION,
        "sampling_seed": SEED, "assigned_tasks": count,
        "population_instance_ids_sha256": digest("\n".join(sorted(x["instance_id"] for x in candidates)).encode()),
        "reference_and_test_patches_in_public_tasks": False,
        "provenance": provenance,
    }
    write_once(output / "preparation.json", freeze)
    return {"tasks": str(output / "tasks.json"), "tasks_sha256": public_hash,
            "private_dataset": str(private_path), "task_repo": str(task_repo),
            "assigned_tasks": count, "population_tasks": 500}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/swe-bench-verified-001")
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--install-env", type=Path,
                        help="Create/use this Python environment, install pinned evaluator dependencies, then prepare")
    args = parser.parse_args()
    if args.install_env:
        if sys.version_info < (3, 12):
            raise RuntimeError("Use Python 3.12 or later for the setup bootstrap")
        uv = shutil.which("uv")
        if not uv:
            raise RuntimeError("Install the supported uv CLI before --install-env")
        evaluator_root = args.evaluator_root.resolve()
        evaluator_root.mkdir(parents=True, exist_ok=True)
        source = archive("SWE-bench/SWE-bench", HARNESS_REVISION,
                         HARNESS_ARCHIVE_SHA256, evaluator_root / "harness.tar.gz")
        environment = args.install_env.resolve()
        python = environment / "bin/python"
        uv_command = [uv, "--cache-dir", str(evaluator_root / "uv-cache")]
        if not python.exists():
            subprocess.run(uv_command + ["venv", "--python", sys.executable, str(environment)], check=True)
        subprocess.run(uv_command + ["pip", "sync", "--python", str(python),
                                    str(ROOT / "experiments/swe-bench-verified-001/requirements-evaluator.lock")], check=True)
        subprocess.run(uv_command + ["pip", "install", "--python", str(python), "--no-deps", str(source)], check=True)
        subprocess.run([str(python), str(Path(__file__).resolve()), "--evaluator-root", str(evaluator_root),
                        "--output", str(args.output.resolve()), "--count", str(args.count)], check=True)
        return
    print(json.dumps(prepare(args.evaluator_root.resolve(), args.output.resolve(), args.count), indent=2))


if __name__ == "__main__":
    main()
