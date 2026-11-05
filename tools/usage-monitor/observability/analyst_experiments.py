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
    result = []
    with store.connection() as connection:
        connection.execute(EVALUATION_SCHEMA)
        connection.execute(REVIEW_SCHEMA)
        connection.execute(ACCOUNTING_SCHEMA)
        for row in rows:
            evaluations = []
            for evaluation in connection.execute('SELECT * FROM experiment_evaluations WHERE experiment_id=? ORDER BY created', (row['id'],)):
                reviews = [dict(review) for review in connection.execute('SELECT * FROM experiment_reviews WHERE evaluation_id=? ORDER BY created', (evaluation['id'],))]
                evaluations.append(dict(id=evaluation['id'], created=evaluation['created'],
                    protocol=json.loads(evaluation['protocol']), measurements=json.loads(evaluation['measurements']),
                    artifact_sha256=evaluation['artifact_sha256'], reviews=reviews))
            result.append(dict(id=row['id'], created=row['created'], task_id=row['task_id'],
                proposal=json.loads(row['proposal']), baseline=json.loads(row['baseline']),
                baseline_sha256=row['baseline_sha256'], evaluations=evaluations,
                accounting=[dict(id=a['id'],created=a['created'],payload=json.loads(a['payload']),sha256=a['sha256']) for a in connection.execute('SELECT * FROM experiment_accounting WHERE experiment_id=? ORDER BY created', (row['id'],))],
                state='evaluated' if evaluations else 'proposed'))
    return result


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

EVALUATION_SCHEMA = '''CREATE TABLE IF NOT EXISTS experiment_evaluations(
 id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL REFERENCES experiments(id),
 created TEXT NOT NULL, protocol TEXT NOT NULL, measurements TEXT NOT NULL, artifact_sha256 TEXT NOT NULL);'''
REVIEW_SCHEMA = '''CREATE TABLE IF NOT EXISTS experiment_reviews(
 id TEXT PRIMARY KEY, evaluation_id TEXT NOT NULL REFERENCES experiment_evaluations(id),
 created TEXT NOT NULL, verdict TEXT NOT NULL, notes TEXT NOT NULL);'''


def record_evaluation(store, experiment_id, protocol, measurements, artifact_sha256):
    """Operator/runner path only. MCP agents cannot manufacture measured results."""
    ident = uuid.uuid4().hex
    with store.connection() as connection:
        connection.execute(EVALUATION_SCHEMA)
        connection.execute(REVIEW_SCHEMA)
        if not connection.execute('SELECT 1 FROM experiments WHERE id=?', (experiment_id,)).fetchone():
            raise ValueError('Unknown experiment')
        connection.execute('INSERT INTO experiment_evaluations VALUES(?,?,?,?,?,?)',
                           (ident, experiment_id, datetime.now(timezone.utc).isoformat(),
                            json.dumps(protocol), json.dumps(measurements), artifact_sha256))
        store.audit(connection, 'experiment_evaluated', ident, dict(experiment_id=experiment_id, artifact_sha256=artifact_sha256))
    return ident


def review_experiment(store, values):
    verdict, notes = values.get('verdict'), values.get('notes', '').strip()
    if verdict not in ('keep', 'reject', 'inconclusive') or not notes or len(notes) > 12000:
        raise ValueError('Review requires keep/reject/inconclusive and bounded evidence/limitations notes')
    ident = uuid.uuid4().hex
    with store.connection() as connection:
        connection.execute(EVALUATION_SCHEMA)
        connection.execute(REVIEW_SCHEMA)
        evaluation = connection.execute('SELECT * FROM experiment_evaluations WHERE id=?', (values['evaluation_id'],)).fetchone()
        if not evaluation:
            raise ValueError('Unknown measured evaluation')
        measurements = json.loads(evaluation['measurements'])
        if verdict == 'keep' and not measurements.get('acceptance_passed'):
            raise ValueError('Cannot keep a candidate that did not pass its registered acceptance gate')
        connection.execute('INSERT INTO experiment_reviews VALUES(?,?,?,?,?)',
                           (ident, values['evaluation_id'], datetime.now(timezone.utc).isoformat(), verdict, notes))
        store.audit(connection, 'experiment_reviewed', ident, values)
    return dict(id=ident, verdict=verdict, note='Analyst interpretation recorded separately from immutable measurements. No global harness configuration changed.')

ACCOUNTING_SCHEMA = """CREATE TABLE IF NOT EXISTS experiment_accounting(
 id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL REFERENCES experiments(id),
 created TEXT NOT NULL, payload TEXT NOT NULL, sha256 TEXT NOT NULL);"""


def record_accounting(store, experiment_id, payload):
    encoded = json.dumps(payload, sort_keys=True)
    ident = uuid.uuid4().hex
    with store.connection() as connection:
        connection.execute(ACCOUNTING_SCHEMA)
        connection.execute('INSERT INTO experiment_accounting VALUES(?,?,?,?,?)',
            (ident, experiment_id, datetime.now(timezone.utc).isoformat(), encoded, hashlib.sha256(encoded.encode()).hexdigest()))
        store.audit(connection, 'experiment_accounting', ident, dict(experiment_id=experiment_id))
    return ident
