#!/usr/bin/env python3
"""Seal cell32's existing failed grade and ended model usage. No model calls."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path

from codex_team_probe import save,sha
from codex_team_queue import archive
from resume_codex_team_scaling import compact_archived_databases
from recompress_codex_team_archives import recompress
from audit_team_memory_usage import audit


def finish(root,config_path):
    config=json.loads(config_path.read_text())
    for category in ('frozen_sources','gate_files','runtime_sources'):
        for path,expected in config[category].items():
            if sha(path)!=expected:raise ValueError('Frozen evidence changed: '+path)
    stop=json.loads((root/'stopped.json').read_text())
    if stop['completed']!=31 or stop['error']!="ValueError('Owned maintenance process still active; audit before continuation')":
        raise ValueError('Not the independently observed post-generation audit stop')
    cell=root/'032-tinydb-mem0_luna-8'
    ended=json.loads((cell/'stopped.json').read_text())
    if 'Observed total team+maintenance token threshold' not in ended['error']:
        raise ValueError('Unexpected generation ending')
    if json.loads((cell/'container-stopped.json').read_text())['exit_code'] or json.loads((cell/'memory-service-ended.json').read_text())['exit_code']:
        raise ValueError('Source and memory service must be ended')
    if Path('/proc/503598').exists():raise ValueError('Prior queue still present')
    for path in cell.glob('memory/backend/maintenance/call-*/started.json'):
        pid=json.loads(path.read_text())['pid'];cmd=Path(f'/proc/{pid}/cmdline')
        if cmd.exists() and str(path.parent).encode() in cmd.read_bytes():raise ValueError('Owned maintenance still active')
    submitted=json.loads((cell/'independent-grade/started.json').read_text())['submitted_source_hashes']
    source=cell/'actor/tinydb'
    if submitted!={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}:
        raise ValueError('Source changed after original independent grade')
    result_path=cell/'independent-grade/result.json';grade_sha=sha(result_path)
    result=json.loads(result_path.read_text())
    if result['passed'] or result['junit']!={'tests':201,'failures':1,'errors':0,'skipped':1}:
        raise ValueError('Preserve the observed failing grade exactly')
    protocol=json.loads(Path(config['protocol']).read_text());assignment=protocol['assignments'][31]
    if assignment['directory']!=cell.name or (root/'checkpoint-032.json').exists():raise ValueError('Ambiguous boundary')
    if any((root/a['directory']).exists() for a in protocol['assignments'][32:]):raise ValueError('Future cell prepared')
    save(cell/'post-generation-audit-recovery-started-011.json',dict(at=datetime.now(timezone.utc).isoformat(),
        model_calls=0,grade_repeated=False,original_grade_sha256=grade_sha,maintenance_restart=False,
        scope='Original audit blocked on an in-flight owned maintenance process. It is now absent; missing CLI completion stays unknown.'))
    metering=audit(cell,Path(config['capture_root']))
    if sha(result_path)!=grade_sha:raise ValueError('Original grade changed')
    rows=json.loads((root/'checkpoint-031.json').read_text())['assignments']
    rows.append(dict(assignment,grade=result,wall_seconds=ended['wall_seconds'],parent_status='stopped',generation_error=ended['error'],
        inference_accounting_complete=metering['complete'],usage=metering['usage'],usage_by_model=metering['usage_by_model'],
        total_inference_usage=metering['total_inference_usage'],unknown_requests=metering['unknown_requests']))
    save(root/'checkpoint-032.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,
        post_generation_recovery='Original failed source grade retained; no model or maintenance restart'))
    archive(cell);compact_archived_databases(cell);recompress(cell)
    save(root/'post-generation-recovery-011.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,
        confirmed_model_assignments=32,model_calls=0,prior_queue_pids=[503598],next_assignment_directory_absent=True,
        grade_repeated=False,source_artifact_passed=False,original_grade_sha256=grade_sha,
        checkpoint_sha256=sha(root/'checkpoint-032.json'),stop_sha256=sha(root/'stopped.json'),
        archive_sha256=sha(cell/'snapshot.tar.xz'),automatic_retries=0))
    print(json.dumps(dict(finished_cell=cell.name,source_passed=False,model_calls=0)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--config',type=Path,required=True)
    a=p.parse_args();finish(a.root.resolve(),a.config.resolve())
