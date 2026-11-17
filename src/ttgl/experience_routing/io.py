"""Durable immutable receipts and content identities; never overwrite attempts."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value).encode()).hexdigest()


def file_digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    encoded = canonical(value).encode() + b'\n'
    with path.open('xb') as stream:
        os.chmod(path, 0o600)
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def read(path):
    return json.loads(Path(path).read_text())


def append(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        stream.write(canonical(value) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def inside(root, path):
    root = Path(root).resolve()
    path = Path(path)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Artifact path must be relative and confined')
    target = root / path
    if not target.resolve().is_relative_to(root):
        raise ValueError('Artifact path escapes its root')
    return target
