#!/usr/bin/env python3
"""Frozen factorial queue; native Codex supplies all team orchestration.

One invocation per cell. Quality is independently replayed; incomplete native
stream usage stays a lower bound. All original raw evidence is verified before
lossless archival. No inference retry or prompt adaptation.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from codex_team_probe import save, sha
from codex_team_coding_v2 import prepare, preflight, run, docker
from codex_team_grade_v3 import grade, audit
from codex_team_queue import archive
from resume_codex_team_scaling import compact_archived_databases
from recompress_codex_team_archives import recompress
from continue_codex_team_scaling_v2 import finish


def execute(protocol_path, root):
    protocol = json.loads(protocol_path.read_text())
    if (root/'queue-started.json').exists():
        raise ValueError('Inspect existing state; never restart a started queue')
    for path, expected in protocol['frozen_sources'].items():
        if sha(path) != expected:
            raise ValueError('Frozen source changed: '+path)
    save(root/'queue-started.json', dict(at=datetime.now(timezone.utc).isoformat(),
         protocol_sha256=sha(protocol_path), automatic_retries=0))
    rows = []
    try:
        for assignment in protocol['assignments']:
            cell = root/assignment['directory']
            if cell.exists():
                raise ValueError('Cell already prepared or started; audit before continuation')
            if shutil.disk_usage(root).free < protocol['workspace_reserve_bytes']:
                raise RuntimeError('Persistent workspace reserve reached before preparation/inference')
            prepare(cell, Path(protocol['source_manifest']), Path(protocol['runtime']),
                    assignment['total_agent_capacity'], assignment['condition'],
                    protocol['minutes_per_cell'], protocol['terminal_budget_per_cell'],
                    Path(protocol['memory_entry']) if assignment['condition']=='mcp_memory' else None,
                    assignment['task_name'], 'reserved_fixed_policy_factorial',
                    protocol['observed_token_stop_threshold'], assignment['guidance'])
            preflight(cell)
            generation_error = None
            try:
                try:
                    run(cell)
                except Exception as error:
                    # Budget/stream failures retain the current attempt and artifact.
                    # No second turn is invoked. An audit failure stops this queue.
                    if not (cell/'stopped.json').exists():
                        raise
                    generation_error = repr(error)
            finally:
                name = json.loads((cell/'container.json').read_text())['name']
                result = docker(['stop', '-t', '2', name], capture_output=True, text=True, timeout=20)
                save(cell/'container-stopped.json', dict(exit_code=result.returncode,
                     stdout=result.stdout, stderr=result.stderr))
                if result.returncode:
                    raise RuntimeError('Artifact seal failed; preserve and audit')
            grade(cell)
            audit(cell)
            row = finish(cell, assignment)
            row['generation_error'] = generation_error
            if row['wall_seconds'] is None and (cell/'stopped.json').exists():
                row['wall_seconds'] = json.loads((cell/'stopped.json').read_text())['wall_seconds']
            rows.append(row)
            save(root/f'checkpoint-{len(rows):03}.json', dict(
                 at=datetime.now(timezone.utc).isoformat(), assignments=rows))
            archive(cell)
            compact_archived_databases(cell)
            recompress(cell)
            print(json.dumps(dict(completed=len(rows), assignment=assignment,
                  grade=row['grade'], wall_seconds=row['wall_seconds'],
                  accounting_complete=row['inference_accounting_complete'])), flush=True)
        save(root/'completion.json', dict(at=datetime.now(timezone.utc).isoformat(), assignments=rows))
    except BaseException as error:
        save(root/'stopped.json', dict(at=datetime.now(timezone.utc).isoformat(),
             error=repr(error), completed=len(rows), automatic_retries=0))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    execute(args.protocol.resolve(), args.root.resolve())
