#!/usr/bin/env python3
"""Finish only the ended cell27's grade/audit/archive; never invoke a model."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from codex_team_probe import save, sha
from codex_team_grade_v3 import grade
from codex_team_queue import archive
from resume_codex_team_scaling import compact_archived_databases
from recompress_codex_team_archives import recompress
from audit_team_memory_usage import audit


def finish(root, config_path):
    config=json.loads(config_path.read_text())
    for category in ('frozen_sources','gate_files','runtime_sources'):
        for path,expected in config[category].items():
            if sha(path)!=expected:raise ValueError('Frozen evidence changed: '+path)
    stop=json.loads((root/'stopped.json').read_text())
    if stop['completed']!=26 or 'TimeoutExpired' not in stop['error'] or 'team_memory_text_service_v2.py' not in stop['error']:
        raise ValueError('Not the registered post-generation shutdown failure')
    cell=root/'027-simpy-graphiti_luna-8'
    ended=json.loads((cell/'completed.json').read_text())
    if ended['turn']['status']!='completed' or json.loads((cell/'container-stopped.json').read_text())['exit_code']:
        raise ValueError('Ended native turn and sealed source required')
    service=json.loads((cell/'memory/service-started.json').read_text())
    for pid in (416899,service['pid']):
        if Path(f'/proc/{pid}').exists():raise ValueError('Prior process still present')
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
        try:args=(proc/'cmdline').read_bytes().split(b'\0')
        except OSError:continue
        if any(str(cell).encode() in arg for arg in args):raise ValueError('Cell process still present: '+proc.name)
    graph=cell/'memory/backend/graph-snapshot.json'
    snapshot=json.loads(graph.read_text())
    if not snapshot['nodes'] or not snapshot['edges']:raise ValueError('Graph snapshot missing')
    protocol=json.loads(Path(config['protocol']).read_text())
    rows=json.loads((root/'checkpoint-026.json').read_text())['assignments']
    assignment=protocol['assignments'][26]
    if assignment['directory']!=cell.name or (root/'checkpoint-027.json').exists():raise ValueError('Ambiguous recovery boundary')
    if any((root/a['directory']).exists() for a in protocol['assignments'][27:]):raise ValueError('Future assignment already prepared')
    actor={str(p.relative_to(cell/'actor')):sha(p) for p in (cell/'actor').rglob('*') if p.is_file()}
    if (cell/'independent-grade').exists():raise ValueError('Evaluation already attempted; audit before any repeat')
    save(cell/'post-generation-recovery-started-010.json',dict(at=datetime.now(timezone.utc).isoformat(),model_calls=0,
        task_generation_repeated=False,prior_service_pid=service['pid'],service_exit_code=None,
        graph_snapshot_sha256=sha(graph),shutdown_timed_out=True,
        limitation='Service exit code unobserved. Incomplete publications/maintenance remain unknown; graph export is retained without claiming full completion.'))
    grade(cell)
    metering=audit(cell,Path(config['capture_root']))
    if actor!={str(p.relative_to(cell/'actor')):sha(p) for p in (cell/'actor').rglob('*') if p.is_file()}:
        raise ValueError('Actor changed during read-only replay')
    result=json.loads((cell/'independent-grade/result.json').read_text())
    rows.append(dict(assignment,grade=result,wall_seconds=ended['wall_seconds'],parent_status='completed',generation_error=None,
        inference_accounting_complete=metering['complete'],usage=metering['usage'],usage_by_model=metering['usage_by_model'],
        total_inference_usage=metering['total_inference_usage'],unknown_requests=metering['unknown_requests']))
    save(root/'checkpoint-027.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,
        post_generation_recovery='No model call; source/runtime/graph/unknown usage preserved'))
    archive(cell);compact_archived_databases(cell);recompress(cell)
    save(root/'post-generation-recovery-010.json',dict(at=datetime.now(timezone.utc).isoformat(),passed=True,
        confirmed_model_assignments=27,model_calls=0,prior_queue_pids=[416899],service_exit_code=None,
        next_assignment_directory_absent=True,source_artifact_passed=result['passed'],
        completed_turn_sha256=sha(cell/'completed.json'),graph_snapshot_sha256=sha(graph),
        checkpoint_sha256=sha(root/'checkpoint-027.json'),stop_sha256=sha(root/'stopped.json'),
        archive_sha256=sha(cell/'snapshot.tar.xz'),automatic_retries=0))
    print(json.dumps(dict(finished_cell=cell.name,source_passed=result['passed'],model_calls=0)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--config',type=Path,required=True)
    a=p.parse_args();finish(a.root.resolve(),a.config.resolve())
