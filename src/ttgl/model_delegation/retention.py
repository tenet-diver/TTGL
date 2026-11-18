"""Reuse Observatory's installed SDK, PostgreSQL index and loopback S3 store."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
from ..experience_routing.io import file_digest, write_new, digest


class LocalS3Retention:
    def __init__(self, root, receipts):
        self.web = Path(root).resolve()/'apps/web'
        self.receipts = Path(receipts)

    def retain_file(self, path, *, kind, identity):
        path = Path(path).resolve(strict=True)
        result = subprocess.run(['node', '--env-file=.env.local', '--experimental-strip-types',
            'scripts/retain-experiment.ts', str(path), kind+':'+identity], cwd=self.web,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        if result.returncode:
            # Errors may contain connection credentials; keep stderr private.
            write_new(self.receipts/('failure-'+digest([kind, identity])+'.json'),
                      {'status': 'retention_failed', 'returncode': result.returncode})
            raise RuntimeError('Local S3 archival failed; native evidence remains in its private spool')
        receipt = json.loads(result.stdout)
        if receipt['sha256'] != file_digest(path) or receipt['bytes'] != path.stat().st_size:
            raise ValueError('Local S3 archive does not reconcile')
        record = {**receipt, 'kind': kind, 'identity': identity, 'artifactId': receipt['id']}
        destination = self.receipts/(digest([kind, identity])+'.json')
        if destination.exists():
            if json.loads(destination.read_text()) != record:
                raise ValueError('Immutable retention receipt conflict')
        else:
            write_new(destination, record)
        return record

    def restore_file(self, receipt, destination):
        destination = Path(destination).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        result = subprocess.run(['node', '--env-file=.env.local', '--experimental-strip-types',
            'scripts/restore-experiment.ts', receipt.get('artifactId') or receipt['id'],
            receipt['sha256'], str(destination)], cwd=self.web,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        if result.returncode or not destination.is_file() or file_digest(destination) != receipt['sha256']:
            raise RuntimeError('Exact local S3 checkpoint restoration failed')
        return destination
