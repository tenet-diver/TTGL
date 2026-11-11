#!/usr/bin/env python3
"""Finish four unstarted cells after auditing a missing child notification.

The twentieth model attempt and artifact are already finished and sealed. No
inference is repeated. Generation/replay behavior stays fixed; audit v2 records
an exact native/capture response prefix when the final RPC tail was not delivered.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from codex_team_probe import save, sha
from codex_team_coding import preflight, run, docker
from codex_team_grade_v2 import grade, audit
from codex_team_queue import archive
from continue_codex_team_scaling_v2 import finish
from resume_codex_team_scaling import compact_archived_databases


def execute(root,protocol_path):
    protocol=json.loads(protocol_path.read_text())
    for path,value in protocol['frozen_sources'].items():
        if sha(path)!=value:raise ValueError('Frozen source changed: '+path)
    stopped=json.loads((root/'storage-continuation-stopped.json').read_text())
    if stopped['completed']!=19 or stopped['error']!="ValueError('RPC/native ordinary usage mismatch')":
        raise ValueError('This continuation only audits the recorded notification gap')
    rows=json.loads((root/'checkpoint-019.json').read_text())['assignments']
    save(root/'final-continuation-started.json',dict(at=datetime.now(timezone.utc).isoformat(),protocol_sha256=sha(protocol_path),automatic_retries=0))
    try:
        twentieth=protocol['assignments'][19];cell=root/twentieth['directory']
        if not (cell/'completed.json').exists() or not (cell/'independent-grade/result.json').exists():
            raise ValueError('Expected preserved twentieth artifact and independent grade')
        audit(cell);rows.append(finish(cell,twentieth))
        save(root/'checkpoint-020.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,amendment=protocol['id']))
        archive(cell);compact_archived_databases(cell)
        for assignment in protocol['assignments'][20:]:
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
                stop=docker(['stop','-t','2',name],capture_output=True,text=True,timeout=20)
                save(cell/'container-stopped.json',dict(exit_code=stop.returncode,stdout=stop.stdout,stderr=stop.stderr))
                if stop.returncode:raise RuntimeError('Artifact seal failed')
            grade(cell);audit(cell);rows.append(finish(cell,assignment))
            save(root/(f'checkpoint-{len(rows):03}.json'),dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,amendment=protocol['id']))
            archive(cell);compact_archived_databases(cell)
            print(json.dumps(dict(completed=len(rows),last=rows[-1])),flush=True)
        save(root/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,amendment=protocol['id']))
    except BaseException as error:
        save(root/'final-continuation-stopped.json',dict(at=datetime.now(timezone.utc).isoformat(),error=repr(error),completed=len(rows),automatic_retries=0));raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True)
    a=p.parse_args();execute(a.root.resolve(),a.protocol.resolve())
