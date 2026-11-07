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
    for name in ('longmemeval-001','longmemeval-002'):
        root=ROOT/name
        if not root.exists():continue
        readers=[p for case in root.glob('case-*') for p in case.iterdir() if p.is_dir() and p.name in ('full_history','file_search','fts','mem0_dense')]
        extractions=list(root.glob('case-*/mem0-build/extractions/extract-*'))
        judges=[p/'judge' for p in readers if (p/'judge').exists()]
        started=sum((p/'started.json').exists() for p in readers+extractions+judges)
        grades=[json.loads((p/'grade.json').read_text()) for p in readers if (p/'grade.json').exists()]
        status='Complete; reconciled' if (root/'results.json').exists() else 'Complete; audit pending' if (root/'complete.json').exists() else 'Stopped; inspect preserved evidence' if (root/'stopped.json').exists() else 'Started; readers precede all blinded judges'
        maximum=json.loads((root/'protocol.json').read_text())['maximum_model_processes']
        reader_cap=maximum//9*4
        rows.append(f'| {name} | {status} | {started}/{maximum} | {len(grades)}/{reader_cap} | {sum(g["passed"] for g in grades)} |')
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
