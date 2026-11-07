#!/usr/bin/env python3
"""Refresh a bounded filesystem progress snapshot; no inference or scheduling."""
from datetime import datetime,timezone
import json
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
ROOT=REPO/'work/security/context-memory-20261107'
DOC=REPO/'docs/research/context-memory-experiment-progress.md'
START='<!-- current-block-snapshot:start -->'
END='<!-- current-block-snapshot:end -->'


def main():
    rows=[]
    for name in ('batching-001','chronological-001','chronological-002'):
        root=ROOT/name
        if not root.exists():continue
        cells=list(root.glob('*--*--*')) if name.startswith('chronological') else list(root.glob('*--*'))
        cells=[p for p in cells if p.is_dir()]
        started=sum((p/'started.json').exists() or (p/'agent.jsonl').exists() for p in cells)
        grades=[json.loads((p/'grade.json').read_text()) for p in cells if (p/'grade.json').exists()]
        result=json.loads((root/'results.json').read_text()) if (root/'results.json').exists() else None
        status='Complete; native counters reconciled' if result else 'Complete; final reconciliation pending' if (root/'complete.json').exists() else 'Stopped; preserved preparation failure' if (root/'stopped.json').exists() else 'Running' if (root/'run-started.json').exists() or started else 'Registered'
        rows.append(f'| {name} | {status} | {started} | {len(grades)} | {sum(bool(g.get("passed")) for g in grades)} |')
    for name in ('longmemeval-001','longmemeval-002','longmemeval-validation-001','longmemeval-validation-002','longmemeval-validation-003'):
        root=ROOT/name
        if not root.exists():continue
        readers=[p for case in root.glob('case-*') for p in case.iterdir() if p.is_dir() and p.name in ('full_history','file_search','fts','mem0_dense')]
        extractions=list(root.glob('case-*/mem0-build/extractions/extract-*'))
        judges=[p/'judge' for p in readers if (p/'judge').exists()]
        started=sum((p/'started.json').exists() for p in readers+extractions+judges)
        grades=[json.loads((p/'grade.json').read_text()) for p in readers if (p/'grade.json').exists()]
        status='Complete; reconciled' if (root/'results.json').exists() else 'Complete; audit pending' if (root/'complete.json').exists() else 'Stopped; inspect preserved evidence' if (root/'stopped.json').exists() or (root/'preparation-stopped.json').exists() else 'Started; readers precede all blinded judges' if (root/'started.json').exists() else 'Preparation only'
        protocol=json.loads((root/'protocol.json').read_text());maximum=protocol.get('maximum_new_model_processes',protocol['maximum_model_processes'])
        reservation=json.loads((root/'reservation.json').read_text())
        reader_cap=len(reservation[protocol['split']])*len(protocol['conditions'])
        if name.endswith('validation-003'):status+=';61 completed reader calls reused, never repeated'
        rows.append(f'| {name} | {status} | {started}/{maximum} | {len(grades)}/{reader_cap} | {sum(g["passed"] for g in grades)} |')
    root=ROOT/'longmemeval-neutral-judge-audit-002'
    if root.exists():
        cells=[p for p in root.iterdir() if p.is_dir() and len(p.name)==32]
        grades=[json.loads((p/'grade.json').read_text()) for p in cells if (p/'grade.json').exists()]
        status='Complete; reconciled' if (root/'results.json').exists() else 'Complete; audit pending' if (root/'complete.json').exists() else 'Running' if (root/'started.json').exists() else 'Registered before any validation grades'
        rows.append(f'| {root.name} | {status} | {sum((p/"started.json").exists() for p in cells)}/72 | {len(grades)}/72 | {sum(g["passed"] for g in grades)} |')
    root=ROOT/'cache-memory-reuse-001'
    if root.exists():
        progress=json.loads((root/'progress.json').read_text()) if (root/'progress.json').exists() else {}
        status='Complete; reconciled' if (root/'results.json').exists() else 'Complete; audit pending' if (root/'complete.json').exists() else 'Stopped; inspect preserved evidence' if (root/'stopped.json').exists() else 'Running; quality and cost pending' if (root/'started.json').exists() else 'Prepared'
        result=json.loads((root/'results.json').read_text()) if (root/'results.json').exists() else None
        grade_text='72/72' if result else f'Pending final reconciliation ({len(progress.get("readers",[]))}/72 readers completed)'
        passing=sum(c['grade']['passed'] for c in result['cells'] if c.get('role')=='reader') if result else 'Unknown'
        rows.append(f'| {root.name} | {status} | {progress.get("processes",0)}/75 | {grade_text} | {passing} |')
    stamp=datetime.now(timezone.utc).isoformat()
    block='\n'.join([START,'## Current filesystem snapshot','',f'Updated {stamp}. Partial checks are provisional; final usage requires reconciliation.','',
        '| Block | Status | Started processes | Graded cells | Passing cells |',
        '|---|---|---:|---:|---:|',*rows,'',
        'Started processes include preserved configuration failures. Missing grades/usage are unknown. This reader does not launch work or alter frozen study sources.',END])
    text=DOC.read_text()
    if START in text:
        first=text.index(START);last=text.index(END,first)+len(END)
        text=text[:first]+block+text[last:]
    else:text+='\n\n'+block+'\n'
    DOC.write_text(text)
    print('\n'.join(rows))


if __name__=='__main__':main()
