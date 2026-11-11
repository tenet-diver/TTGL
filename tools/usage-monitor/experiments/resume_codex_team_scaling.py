#!/usr/bin/env python3
"""Continue only unstarted cells after a verified pre-inference storage stop."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from codex_team_probe import save, sha
from codex_team_coding import preflight, run, docker
from codex_team_grade import grade, audit
from codex_team_queue import archive
from continue_codex_team_scaling import finish


def compact_archived_databases(cell):
    receipt=json.loads((cell/'archive.json').read_text())
    if not receipt['verified'] or sha(cell/'snapshot.tar.gz')!=receipt['archive_sha256']:
        raise ValueError('Verified original archive required')
    removed=[]
    for p in (cell/'home').rglob('*'):
        if not p.is_file() or p.is_symlink() or '.sqlite' not in p.name:continue
        relative=str(p.relative_to(cell));expected=receipt['file_hashes'].get(relative)
        if not expected or sha(p)!=expected:
            raise ValueError('Database changed or not archived: '+relative)
        removed.append(dict(path=relative,bytes=p.stat().st_size,sha256=expected));p.unlink()
    save(cell/'storage-compaction-001.json',dict(at=datetime.now(timezone.utc).isoformat(),removed=removed,
        verified_lossless_archive=True,authentication_touched=False,freed_bytes=sum(x['bytes'] for x in removed)))


def execute(root, protocol_path):
    protocol=json.loads(protocol_path.read_text())
    for path,value in protocol['frozen_sources'].items():
        if sha(path)!=value:raise ValueError('Frozen source changed: '+path)
    stop=json.loads((root/'continuation-001-stopped.json').read_text())
    if stop['completed']!=17 or stop['error']!="RuntimeError('Storage reserve reached before inference')":
        raise ValueError('This continuation is only for the verified17-cell storage stop')
    rows=json.loads((root/'checkpoint-017.json').read_text())['assignments']
    if len(rows)!=17:raise ValueError('Expected17preserved completions')
    save(root/'storage-continuation-started.json',dict(at=datetime.now(timezone.utc).isoformat(),protocol_sha256=sha(protocol_path),automatic_retries=0))
    try:
        for row in rows:compact_archived_databases(root/row['directory'])
        for assignment in protocol['assignments'][17:]:
            cell=root/assignment['directory']
            if (cell/'started.json').exists():raise ValueError('Started cell cannot repeat')
            if shutil.disk_usage(root).free<128*1024*1024:raise RuntimeError('Storage reserve reached before inference')
            preflight(cell)
            try:
                try:run(cell)
                except RuntimeError as error:
                    if str(error)!='Observed team token threshold reached; no retry':raise
            finally:
                name=json.loads((cell/'container.json').read_text())['name']
                stopped=docker(['stop','-t','2',name],capture_output=True,text=True,timeout=20)
                save(cell/'container-stopped.json',dict(exit_code=stopped.returncode,stdout=stopped.stdout,stderr=stopped.stderr))
                if stopped.returncode:raise RuntimeError('Artifact seal failed')
            grade(cell);audit(cell);rows.append(finish(cell,assignment))
            save(root/(f'checkpoint-{len(rows):03}.json'),dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,amendment=protocol['id']))
            archive(cell);compact_archived_databases(cell)
            print(json.dumps(dict(completed=len(rows),last=rows[-1])),flush=True)
        save(root/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,amendment=protocol['id']))
    except BaseException as error:
        save(root/'storage-continuation-stopped.json',dict(at=datetime.now(timezone.utc).isoformat(),error=repr(error),completed=len(rows),automatic_retries=0));raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True)
    a=p.parse_args();execute(a.root.resolve(),a.protocol.resolve())
