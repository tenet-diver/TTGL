#!/usr/bin/env python3
"""Sequential registered native-team units; never repeats started assignments."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

from codex_team_probe import save, sha
from codex_team_coding import preflight, run, docker
from codex_team_grade import grade, audit


def archive(root):
    """Verified lossless archive of owned raw evidence; authentication stays local."""
    excluded={'auth.json','snapshot.tar.gz','archive.json'}
    files=[p for p in sorted(root.rglob('*')) if p.is_file() and p.name not in excluded and not p.is_symlink()]
    links=[p for p in sorted(root.rglob('*')) if p.is_symlink()]
    hashes={str(p.relative_to(root)):sha(p) for p in files}
    target=root/'snapshot.tar.gz'
    with target.open('xb') as stream,tarfile.open(fileobj=stream,mode='w:gz',compresslevel=6,dereference=False) as tar:
        for p in files+links:
            tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
    with tarfile.open(target,'r:gz') as tar:
        members=tar.getmembers()
        observed={m.name:hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in members if m.isfile()}
        if observed!=hashes:
            raise ValueError('Archive verification failed; raw evidence retained')
        if {m.name:m.linkname for m in members if m.issym()}!={str(p.relative_to(root)):str(p.readlink()) for p in links}:
            raise ValueError('Archive symlink verification failed; raw evidence retained')
    save(root/'archive.json',dict(at=datetime.now(timezone.utc).isoformat(),archive_sha256=sha(target),
        file_hashes=hashes,symlinks={str(p.relative_to(root)):str(p.readlink()) for p in links},
        verified=True,authentication_excluded=True,reason='Constrained workspace storage; all unique raw evidence preserved losslessly'))
    # Retain summaries and configuration for reporting. Only archived owned raw
    # files are removed, after byte-for-byte verification. No auth file touched.
    prefixes=('actor/','tool-records/','home/sessions/','home/log/','independent-grade/replay/')
    for p in files:
        rel=str(p.relative_to(root))
        if rel.startswith(prefixes) or p.name in ('rpc.jsonl','stderr.log') or (rel.startswith('home/') and p.suffix in ('.sqlite','.db','.sqlite3','.wal','.shm')):
            if sha(p)!=hashes[rel]:
                raise ValueError('File changed during archival; cleanup stopped')
            p.unlink()


def execute(protocol_path, root):
    protocol=json.loads(protocol_path.read_text())
    if (root/'queue-started.json').exists():
        raise ValueError('Queue already started: audit existing state; never restart automatically')
    for path,expected in protocol['frozen_sources'].items():
        if sha(path)!=expected:
            raise ValueError('Frozen queue source changed: '+path)
    save(root/'queue-started.json',dict(at=datetime.now(timezone.utc).isoformat(),protocol_sha256=sha(protocol_path),automatic_retries=0))
    rows=[]
    try:
        for unit in protocol['assignments']:
            cell=root/unit['directory']
            if (cell/'started.json').exists():
                raise ValueError('Assignment already started; audit required, never repeated')
            if shutil.disk_usage(root).free<128*1024*1024:
                raise RuntimeError('Workspace reserve reached before inference')
            preflight(cell)
            try:
                try:
                    run(cell)
                except RuntimeError as error:
                    if str(error)!='Observed team token threshold reached; no retry':
                        raise
            finally:
                # Stops any remaining task process before the artifact is sealed.
                name=json.loads((cell/'container.json').read_text())['name']
                stopped=docker(['stop','-t','2',name],capture_output=True,text=True,timeout=20)
                save(cell/'container-stopped.json',dict(exit_code=stopped.returncode,stdout=stopped.stdout,stderr=stopped.stderr))
                if stopped.returncode:
                    raise RuntimeError('Container seal failed; audit required')
            grade(cell)
            audit(cell)
            checked=json.loads((cell/'usage-audit.json').read_text())
            if not checked['complete']:
                raise RuntimeError('Incomplete inference accounting; audit required')
            result=json.loads((cell/'independent-grade/result.json').read_text())
            row=dict(unit,grade=result,usage=checked['usage'],wall_seconds=checked['runtime_seconds'])
            rows.append(row)
            save(root/(f'checkpoint-{len(rows):03}.json'),dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows))
            archive(cell)
            print(json.dumps(dict(completed=len(rows),assignment=unit,grade=result,usage=checked['usage'],wall_seconds=checked['runtime_seconds'])),flush=True)
        save(root/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows))
    except BaseException as error:
        save(root/'stopped.json',dict(at=datetime.now(timezone.utc).isoformat(),error=repr(error),completed=len(rows),automatic_retries=0,audit_required=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();execute(a.protocol.resolve(),a.root.resolve())
