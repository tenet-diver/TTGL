#!/usr/bin/env python3
"""Publish an observed analyst's reviews and isolate its native research overhead."""
import argparse
import collections
import json
from pathlib import Path
import sqlite3

from workspace import Store
from analyst_experiments import REVIEW_SCHEMA

REPO=Path(__file__).resolve().parents[3]


def publish(directory):
    if (directory/'published-session.json').exists():
        raise ValueError('Session already published')
    completion=json.loads((directory/'completion.json').read_text())
    if completion.get('exit_code')!=0:
        raise ValueError('Incomplete analyst invocation; preserve without inferring a completed review')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000')
    records=[json.loads(l) for l in (directory/'agent.jsonl').read_text().splitlines() if l.startswith('{')]
    session=next(r['thread_id'] for r in records if r.get('type')=='thread.started')
    with sqlite3.connect(directory/'data/workspace.sqlite') as source:
        source.row_factory=sqlite3.Row
        reviews=source.execute('SELECT * FROM experiment_reviews').fetchall()
        with store.connection() as target:
            target.execute(REVIEW_SCHEMA)
            for review in reviews:
                original=source.execute('SELECT artifact_sha256 FROM experiment_evaluations WHERE id=?',(review['evaluation_id'],)).fetchone()
                existing=target.execute('SELECT artifact_sha256 FROM experiment_evaluations WHERE id=?',(review['evaluation_id'],)).fetchone()
                if not existing or existing['artifact_sha256']!=original['artifact_sha256']:
                    raise ValueError('Review does not reference the same measured evaluation')
                if not target.execute('SELECT 1 FROM experiment_reviews WHERE id=?',(review['id'],)).fetchone():
                    target.execute('INSERT INTO experiment_reviews VALUES(?,?,?,?,?)',tuple(review))
                    store.audit(target,'observed_analyst_review',review['id'],dict(session_id=session))
    store.scan();report=store.report(event_limit=None)
    turns=[t for t in report['turns'] if t['session_id']==session]
    usage=collections.Counter()
    for event in report['events']:
        if event['session_id']==session and event['usage']:
            usage.update({k:event['usage'].get(k,0) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')})
    if not turns or not usage['total_tokens']:
        raise ValueError('Analyst native metering unavailable')
    task=store.mutate('task',dict(project_id=report['projects'][0]['id'],title='Evaluate measured harness improvement: '+directory.name,
        goal='Use the product to inspect registered trial evidence and record an evidence-based verdict.',
        acceptance='Verdict references immutable measurements, quality gates, scope and overhead.'))['id']
    for turn in turns:
        store.mutate('assign',dict(session_id=session,turn_id=turn['turn_id'],task_id=task))
    store.mutate('task_status',dict(id=task,status='completed',outcome='Observed analyst result and native tool evidence retained at '+str(directory)))
    followup=directory/'accounting-followup-completion.json'
    followup_seconds=json.loads(followup.read_text())['elapsed_seconds'] if followup.exists() else 0
    result=dict(session_id=session,task_id=task,usage=dict(usage),wall_seconds=completion['elapsed_seconds'],followup_wall_seconds=followup_seconds)
    (directory/'published-session.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    publish(parser.parse_args().directory.resolve())
