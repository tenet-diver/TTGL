"""Persist experiment proposals with immutable task baselines; never execute trials."""
import hashlib
import json
import uuid
from datetime import datetime, timezone

SCHEMA = '''CREATE TABLE IF NOT EXISTS experiments(
 id TEXT PRIMARY KEY, created TEXT NOT NULL, task_id TEXT NOT NULL REFERENCES tasks(id),
 proposal TEXT NOT NULL, baseline TEXT NOT NULL, baseline_sha256 TEXT NOT NULL);'''


def list_experiments(store, task=None, project=None):
    with store.connection() as connection:
        connection.execute(SCHEMA)
        rows = connection.execute('''SELECT e.* FROM experiments e JOIN tasks t ON t.id=e.task_id
 WHERE (? IS NULL OR e.task_id=?) AND (? IS NULL OR t.project_id=?) ORDER BY e.created DESC''',
                                  (task, task, project, project)).fetchall()
    return [dict(id=r['id'], created=r['created'], task_id=r['task_id'],
                 proposal=json.loads(r['proposal']), baseline=json.loads(r['baseline']),
                 baseline_sha256=r['baseline_sha256'], state='proposed')
            for r in rows if not task or r['task_id'] == task]


def plan_experiment(store, values):
    required = ('task_id', 'title', 'change', 'metrics', 'quality_gate', 'overhead', 'rollback')
    if any(not isinstance(values.get(k), str) or not values[k].strip() for k in required):
        raise ValueError('Experiment requires task_id, title, one change, metrics, quality_gate, overhead and rollback')
    if any(len(values[k]) > 8000 for k in required):
        raise ValueError('Experiment fields must be at most 8000 characters')
    with store.connection() as connection:
        connection.execute(SCHEMA)
        task = connection.execute('SELECT * FROM tasks WHERE id=?', (values['task_id'],)).fetchone()
        if not task:
            raise ValueError('Unknown baseline task; define and assign a task before planning')
        rows = connection.execute('''SELECT e.* FROM events e JOIN assignments a
 ON e.session_id=a.session_id AND e.turn_id=a.turn_id WHERE a.task_id=? ORDER BY e.ts,e.id''',
                                  (values['task_id'],)).fetchall()
        if not rows:
            raise ValueError('Baseline task has no assigned evidence')
        usage = dict(input_tokens=0, cached_input_tokens=0, output_tokens=0, total_tokens=0)
        for row in rows:
            recorded = json.loads(row['usage']) if row['usage'] else {}
            for key in usage:
                usage[key] += recorded.get(key, 0)
        baseline = dict(task=dict(task), events=[dict(r) for r in rows], usage=usage,
                        first_at=rows[0]['ts'], last_at=rows[-1]['ts'],
                        event_count=len(rows), cash_cost=None, inference_latency=None,
                        note='Frozen recorded task evidence. Tool runtimes may overlap or include background lifetimes. Cached input is a subset of input. No trial has run.')
        encoded = json.dumps(baseline, sort_keys=True)
        fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
        ident = uuid.uuid4().hex
        created = datetime.now(timezone.utc).isoformat()
        connection.execute('INSERT INTO experiments VALUES(?,?,?,?,?,?)',
                           (ident, created, values['task_id'], json.dumps(values), encoded, fingerprint))
        store.audit(connection, 'experiment_proposal', ident, values)
    return dict(id=ident, state='proposed', baseline_sha256=fingerprint,
                baseline_event_count=len(rows), baseline_usage=usage,
                note='Proposal saved; no harness change or benchmark executed. Retrieve with query_activity section=experiments.')
