#!/usr/bin/env python3
"""Local project/task analysis over native Codex evidence. Python stdlib only."""
import argparse
import base64
import collections
import contextlib
from datetime import datetime, timezone, timedelta
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
from urllib.parse import urlparse, parse_qs, urlencode
import uuid
import urllib.request

import baseline
from analyst_experiments import list_experiments
bridge = baseline.bridge
HERE = Path(__file__).resolve().parent
DEFAULTS = json.loads((HERE.parent / 'config/defaults.json').read_text())


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, data, codex_root, langfuse_url, capture_root=None):
        self.data, self.root, self.langfuse_url = data, codex_root, langfuse_url.rstrip('/')
        self.capture_root = capture_root
        data.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(data, 0o700)
        self.db = data / 'workspace.sqlite'
        with self.connection() as c:
            c.executescript('''
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT NOT NULL,repo TEXT NOT NULL,scope TEXT,created TEXT);
CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,project_id TEXT REFERENCES projects(id),title TEXT,goal TEXT,acceptance TEXT,status TEXT,created TEXT,updated TEXT,outcome TEXT);
CREATE TABLE IF NOT EXISTS assignments(session_id TEXT,turn_id TEXT,task_id TEXT REFERENCES tasks(id),PRIMARY KEY(session_id,turn_id));
CREATE TABLE IF NOT EXISTS turns(session_id TEXT,turn_id TEXT,repo TEXT,prompt TEXT,start TEXT,end TEXT,completed INTEGER,PRIMARY KEY(session_id,turn_id));
CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,session_id TEXT,turn_id TEXT,kind TEXT,name TEXT,ts TEXT,runtime REAL,bytes INTEGER,failed INTEGER,usage TEXT,model TEXT,trace TEXT,span TEXT,source_line INTEGER,output_hash TEXT);
CREATE TABLE IF NOT EXISTS rules(id TEXT PRIMARY KEY,category TEXT,pattern TEXT,version INTEGER,enabled INTEGER);
CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY,decision TEXT,implementation TEXT,evaluation TEXT,notes TEXT,updated TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,at TEXT,action TEXT,entity TEXT,details TEXT);
CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY,size INTEGER,mtime INTEGER,error TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
CREATE TABLE IF NOT EXISTS analyses(id TEXT PRIMARY KEY,created TEXT,model TEXT,snapshot_hash TEXT,report TEXT,overhead TEXT);
CREATE TABLE IF NOT EXISTS agent_annotations(analysis_id TEXT REFERENCES analyses(id),event_id TEXT REFERENCES events(id),category TEXT,runtime_role TEXT,rationale TEXT,confidence TEXT,PRIMARY KEY(analysis_id,event_id));
CREATE INDEX IF NOT EXISTS event_turn ON events(session_id,turn_id);
''')
            c.execute('INSERT OR IGNORE INTO settings VALUES(?,?)', ('collection_enabled', 'true'))
            defaults = [('verification', 'tests'), ('build', 'build'), ('search', 'search'), ('reading', 'file inspection'),
                        ('version control', 'git '), ('setup', 'dependency install'), ('waiting', 'intentional wait'),
                        ('external services', 'network requests'), ('editing', 'FileChange')]
            for index, (category, pattern) in enumerate(defaults):
                c.execute('INSERT OR IGNORE INTO rules VALUES(?,?,?,?,?)', (f'default-{index}', category, pattern, 1, 1))

    @contextlib.contextmanager
    def connection(self):
        c = sqlite3.connect(self.db, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA journal_mode=WAL')
        try:
            with c:
                yield c
        finally:
            c.close()

    def audit(self, c, action, entity, details):
        c.execute('INSERT INTO audit(at,action,entity,details) VALUES(?,?,?,?)', (now(), action, entity, json.dumps(details)))

    def mutate(self, action, values):
        with self.connection() as c:
            ident = values.get('id') or uuid.uuid4().hex
            if action == 'project':
                name, repo = str(values.get('name', '')).strip(), str(values.get('repo', '')).strip()
                if not name or not repo:
                    raise ValueError('Project name and repository path are required')
                c.execute('INSERT INTO projects VALUES(?,?,?,?,?)', (ident, name[:200], repo[:2000], str(values.get('scope', ''))[:4000], now()))
            elif action == 'task':
                title, goal = str(values.get('title', '')).strip(), str(values.get('goal', '')).strip()
                if not title or not goal:
                    raise ValueError('Task title and intended outcome are required')
                c.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)',
                    (ident, values['project_id'], title[:200], goal[:8000], str(values.get('acceptance', ''))[:8000], 'active', now(), now(), None))
            elif action == 'assign':
                ident = values['task_id']
                if not c.execute('SELECT 1 FROM turns WHERE session_id=? AND turn_id=?', (values['session_id'], values['turn_id'])).fetchone():
                    raise ValueError('Unknown turn')
                c.execute('INSERT OR REPLACE INTO assignments VALUES(?,?,?)', (values['session_id'], values['turn_id'], ident))
            elif action == 'task_status':
                status = values['status']
                if status not in ('active', 'waiting', 'completed', 'cancelled', 'unresolved'):
                    raise ValueError('Invalid task status')
                outcome = values.get('outcome')
                if status == 'completed' and not outcome:
                    raise ValueError('Completion requires outcome/verification evidence')
                if not c.execute('UPDATE tasks SET status=?,outcome=?,updated=? WHERE id=?', (status, outcome, now(), ident)).rowcount:
                    raise ValueError('Unknown task')
            elif action == 'rule':
                category, pattern = str(values.get('category', '')).strip(), str(values.get('pattern', '')).strip()
                if not category or not pattern:
                    raise ValueError('Category and a literal operation pattern are required')
                old = c.execute('SELECT version FROM rules WHERE id=?', (ident,)).fetchone()
                c.execute('INSERT OR REPLACE INTO rules VALUES(?,?,?,?,?)', (ident, category[:100], pattern[:200], old['version'] + 1 if old else 1, int(values.get('enabled', True))))
            elif action == 'decision':
                decision = values.get('decision', 'review')
                implementation = values.get('implementation', 'not_started')
                evaluation = values.get('evaluation', 'not_measured')
                if decision not in ('review', 'declined', 'deferred') or implementation not in ('not_started', 'prepared', 'applied', 'reverted') or evaluation not in ('not_measured', 'trial_planned', 'in_progress', 'improved', 'regressed', 'inconclusive'):
                    raise ValueError('Invalid review state')
                if evaluation in ('improved', 'regressed', 'inconclusive') and not str(values.get('notes', '')).strip():
                    raise ValueError('Evaluation requires comparison evidence in the notes')
                c.execute('INSERT OR REPLACE INTO decisions VALUES(?,?,?,?,?,?)', (ident, decision, implementation, evaluation, str(values.get('notes', ''))[:8000], now()))
            elif action == 'collection':
                c.execute('UPDATE settings SET value=? WHERE key=?', (json.dumps(bool(values['enabled'])), 'collection_enabled'))
            else:
                raise ValueError('Unknown action')
            self.audit(c, action, ident, values)
        return {'id': ident, 'ok': True}

    def scan(self):
        with self.connection() as c:
            if c.execute("SELECT value FROM settings WHERE key='collection_enabled'").fetchone()[0] != 'true':
                return
        paths = list(self.root.joinpath('sessions').rglob('*.jsonl')) + list(self.root.joinpath('archived_sessions').rglob('*.jsonl'))
        for path in paths:
            stat = path.stat()
            with self.connection() as c:
                old = c.execute('SELECT * FROM files WHERE path=?', (str(path),)).fetchone()
                if old and old['size'] == stat.st_size and old['mtime'] == stat.st_mtime_ns and not old['error']:
                    continue
            try:
                self.ingest(path)
                error = None
            except Exception as exc:
                error = type(exc).__name__ + ': ' + str(exc)[:200]
            with self.connection() as c:
                c.execute('INSERT OR REPLACE INTO files VALUES(?,?,?,?)', (str(path), stat.st_size, stat.st_mtime_ns, error))

    def publish_analysis(self, analysis, snapshot, metadata):
        expected = {event['id'] for event in snapshot['tools']}
        annotations = analysis.get('annotations', [])
        identities = [item.get('event_id') for item in annotations]
        if set(identities) != expected or len(identities) != len(expected):
            raise ValueError('Agent annotations must cover every frozen tool event exactly once')
        for item in annotations:
            if item.get('runtime_role') not in ('finite_operation', 'background_service_lifetime', 'uncertain') or item.get('confidence') not in ('high', 'medium', 'low'):
                raise ValueError('Invalid agent interpretation')
            if not isinstance(item.get('category'), str) or not 0 < len(item['category']) <= 120 or not item.get('rationale'):
                raise ValueError('Category and evidence rationale are required')
        evidence_ids = expected | {capture['id'] for capture in snapshot.get('capture_summary', [])}
        for finding in analysis.get('findings', []):
            if not finding.get('evidence_ids') or not set(finding['evidence_ids']) <= evidence_ids:
                raise ValueError('Every finding must cite frozen event identities')
        ident = metadata['id']
        with self.connection() as c:
            known = {row['id'] for row in c.execute('SELECT id FROM events')}
            if not expected <= known:
                raise ValueError('Analysis references events outside the ingested source')
            # An analysis is an immutable, versioned interpretation; measurements stay unchanged.
            c.execute('INSERT INTO analyses VALUES(?,?,?,?,?,?)', (ident, now(), metadata['model'], metadata['snapshot_hash'],
                json.dumps(dict(analysis, snapshot_at=snapshot['snapshot_at'], scope=snapshot['scope'], tool_events=len(expected),
                                measured_snapshot_usage=snapshot['usage'])), json.dumps(metadata.get('overhead', {}))))
            for item in annotations:
                c.execute('INSERT INTO agent_annotations(analysis_id,event_id,category,runtime_role,rationale,confidence) VALUES(?,?,?,?,?,?)',
                    (ident, item['event_id'], item['category'], item['runtime_role'], item['rationale'], item['confidence']))
            self.audit(c, 'publish_agent_analysis', ident, dict(snapshot_hash=metadata['snapshot_hash'], tool_events=len(expected), model=metadata['model']))
        return ident

    def ingest(self, path):
        meta, tools, bad = bridge.tool_records(path)
        if bad:
            raise ValueError(f'{bad} malformed or oversized lines')
        sid, repo = meta['id'], meta.get('cwd', '')
        tools = {tool['id']: tool for tool in tools}
        turns, events = {}, {}
        model = None
        for line, record in bridge.monitor.lines(path):
            if not record:
                continue
            p = record.get('payload') or {}
            ts = record.get('timestamp') or meta.get('timestamp')
            if ts < meta.get('timestamp', '') or p.get('thread_id') and p['thread_id'] != sid:
                continue
            if record.get('type') == 'turn_context':
                model = p.get('model')
            turn = p.get('turn_id')
            if not turn:
                continue
            row = turns.setdefault(turn, dict(prompt=[], start=ts, end=ts, completed=0))
            row['end'] = ts
            trace = bridge.digest('native-turn-v1:' + sid + ':' + turn)
            if record.get('type') == 'event_msg':
                if p.get('type') == 'task_complete':
                    row['completed'] = 1
                item = p.get('item') or {}
                if item.get('type') == 'UserMessage':
                    for content in item.get('content') or []:
                        if isinstance(content, dict) and content.get('type') == 'text':
                            row['prompt'].append(content.get('text', '')[:4000])
                ident = item.get('id')
                if p.get('type') == 'item_completed' and ident in tools:
                    tool = tools[ident]
                    output = item.get('aggregated_output', item.get('result'))
                    output_hash = hashlib.sha256(json.dumps(output, sort_keys=True).encode()).hexdigest() if output is not None else None
                    events[sid + ':tool:' + ident] = (sid + ':tool:' + ident, sid, turn, 'tool', tool['operation'], ts,
                        tool['native_runtime_ns'] / 1e9 if tool['native_runtime_ns'] is not None else None,
                        tool['output_bytes'], tool['failed'], None, None, trace,
                        bridge.digest(sid + ':native-content:' + ident, 16), line, output_hash)
            if record.get('type') == 'token_usage_record' and p.get('response_id'):
                ident, usage = p['response_id'], p.get('usage') or {}
                keys = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')
                if any(not isinstance(usage.get(k), int) or usage[k] < 0 for k in keys):
                    raise ValueError('Unsupported response usage')
                if usage['cached_input_tokens'] > usage['input_tokens'] or usage['total_tokens'] != usage['input_tokens'] + usage['output_tokens']:
                    raise ValueError('Non-reconciling response usage')
                key = sid + ':response:' + ident
                event = (key, sid, turn, 'generation', 'Model response', ts, None, None, None, json.dumps(usage), model,
                         trace, bridge.digest(key, 16), line, None)
                if key in events and events[key][9] != event[9]:
                    raise ValueError('Conflicting response usage')
                events[key] = event
        with self.connection() as c:
            for turn, row in turns.items():
                c.execute('INSERT OR REPLACE INTO turns VALUES(?,?,?,?,?,?,?)',
                    (sid, turn, repo, '\n'.join(row['prompt'])[:12000], row['start'], row['end'], row['completed']))
            for event in events.values():
                existing = c.execute('SELECT usage FROM events WHERE id=?', (event[0],)).fetchone()
                if existing and existing['usage'] != event[9]:
                    raise ValueError('Response changed after ingestion; reconciliation required')
                c.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', event)

    def report(self, project=None, task=None, category=None, event_limit=1000):
        with self.connection() as c:
            projects = [dict(r) for r in c.execute('SELECT * FROM projects ORDER BY created')]
            tasks = [dict(r) for r in c.execute('SELECT * FROM tasks ORDER BY created DESC')]
            rules = [dict(r) for r in c.execute('SELECT * FROM rules ORDER BY id')]
            assignments = {(r['session_id'], r['turn_id']): r['task_id'] for r in c.execute('SELECT * FROM assignments')}
            turns = [dict(r) for r in c.execute('SELECT * FROM turns ORDER BY start DESC')]
            rows = [dict(r) for r in c.execute('SELECT * FROM events ORDER BY ts')]
            decisions = {r['id']: dict(r) for r in c.execute('SELECT * FROM decisions')}
            files = [dict(r) for r in c.execute('SELECT * FROM files')]
            enabled = c.execute("SELECT value FROM settings WHERE key='collection_enabled'").fetchone()[0] == 'true'
            audit = [dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 50')]
            analyses = [dict(r) for r in c.execute('SELECT * FROM analyses ORDER BY created DESC')]
            annotation_rows = [dict(r) for r in c.execute('SELECT a.* FROM agent_annotations a JOIN analyses b ON a.analysis_id=b.id ORDER BY b.created')]
        annotations = {row['event_id']: row for row in annotation_rows}
        task_map = {t['id']: t for t in tasks}
        project_map = {p['id']: p for p in projects}
        for turn in turns:
            turn['task_id'] = assignments.get((turn['session_id'], turn['turn_id']))
            turn['project_id'] = task_map.get(turn['task_id'], {}).get('project_id')
            turn['langfuse_url'] = self.langfuse_url + '/project/ttgl-codex/traces/' + bridge.digest('native-turn-v1:' + turn['session_id'] + ':' + turn['turn_id'])
        selected_turns = [t for t in turns if (not task or t['task_id'] == task) and (not project or t['project_id'] == project)]
        selected_ids = {(t['session_id'], t['turn_id']) for t in selected_turns}
        totals = dict(input_tokens=0, cached_input_tokens=0, output_tokens=0, total_tokens=0)
        groups = collections.defaultdict(lambda: dict(count=0, runtime_seconds=0, finite_runtime_seconds=0, background_runtime_seconds=0, unreviewed_runtime_seconds=0, timed=0, bytes=0, failures=0))
        events, models, scope_generations = [], collections.Counter(), []
        all_usage = dict.fromkeys(totals, 0)
        unassigned_usage = dict.fromkeys(totals, 0)
        task_usage = collections.defaultdict(lambda: dict.fromkeys(totals, 0))
        turn_usage = collections.defaultdict(lambda: dict.fromkeys(totals, 0))
        for row in rows:
            if row['usage']:
                usage = json.loads(row['usage'])
                for key in totals:
                    all_usage[key] += usage.get(key, 0)
                    turn_usage[(row['session_id'], row['turn_id'])][key] += usage.get(key, 0)
                    assigned = assignments.get((row['session_id'], row['turn_id']))
                    if assigned:
                        task_usage[assigned][key] += usage.get(key, 0)
                    if (row['session_id'], row['turn_id']) not in assignments:
                        unassigned_usage[key] += usage.get(key, 0)
        for turn in turns:
            turn['usage'] = turn_usage[(turn['session_id'], turn['turn_id'])]
        for defined_task in tasks:
            defined_task['usage'] = task_usage[defined_task['id']]
        for row in rows:
            if (row['session_id'], row['turn_id']) not in selected_ids:
                continue
            row['category'] = 'model inference' if row['kind'] == 'generation' else next((r['category'] for r in rules if r['enabled'] and r['pattern'].lower() in row['name'].lower()), 'other tools')
            annotation = annotations.get(row['id'])
            row['category_basis'] = 'fallback rule'
            row['runtime_role'] = 'unreviewed'
            if annotation:
                row.update(category=annotation['category'], category_basis='Codex agent interpretation',
                           analysis_id=annotation['analysis_id'], category_confidence=annotation['confidence'],
                           category_rationale=annotation['rationale'], runtime_role=annotation['runtime_role'])
            row['task_id'] = assignments.get((row['session_id'], row['turn_id']))
            if row['kind'] == 'generation':
                scope_generations.append(dict(row))
            if category and row['category'] != category:
                continue
            row['usage'] = json.loads(row['usage']) if row['usage'] else None
            row['langfuse_url'] = self.langfuse_url + '/project/ttgl-codex/traces/' + row['trace'] + '?observation=' + row['span']
            if row['usage']:
                for k in totals:
                    totals[k] += row['usage'].get(k, 0)
                models[row['model'] or 'Unknown'] += row['usage']['total_tokens']
            group = groups[row['category']]
            group['count'] += 1
            group['bytes'] += row['bytes'] or 0
            group['failures'] += int(row['failed'] == 1)
            if row['runtime'] is not None:
                group['runtime_seconds'] += row['runtime']
                if row['runtime_role'] == 'finite_operation':
                    group['finite_runtime_seconds'] += row['runtime']
                elif row['runtime_role'] == 'background_service_lifetime':
                    group['background_runtime_seconds'] += row['runtime']
                else:
                    group['unreviewed_runtime_seconds'] += row['runtime']
                group['timed'] += 1
            events.append(row)
        total_runtime = sum(g['runtime_seconds'] for g in groups.values())
        categories = [dict(name=name, **g, runtime_share=g['runtime_seconds'] / total_runtime if total_runtime else None) for name, g in groups.items()]
        categories.sort(key=lambda r: -r['runtime_seconds'])
        accounting = {key: sum(group[key] for group in groups.values()) for key in
                      ('runtime_seconds', 'finite_runtime_seconds', 'background_runtime_seconds', 'unreviewed_runtime_seconds')}
        accounting['reviewed_tool_events'] = sum(e['id'] in annotations for e in events if e['kind'] == 'tool')
        accounting['tool_events'] = sum(e['kind'] == 'tool' for e in events)
        opportunities = []
        large = [e for e in events if e['kind'] == 'tool' and (e['bytes'] or 0) > 32000]
        if large:
            opportunities.append(dict(id='large-output', title='Review large tool results',
                evidence=[e['id'] for e in sorted(large, key=lambda e: -e['bytes'])[:5]],
                observation=f'{len(large)} results exceed 32 KB. These are retained bytes, not attributed tokens.',
                action='Prepare narrower result selection or summaries, preserving needed diagnostics.',
                guardrail='Compare task quality, full model usage, elapsed time and optimization overhead.'))
        repeated = collections.defaultdict(list)
        for e in events:
            if e['output_hash'] and (e['bytes'] or 0) > 8000:
                repeated[(e['session_id'], e['name'], e['output_hash'])].append(e['id'])
        duplicates = [ids for ids in repeated.values() if len(ids) >= 3]
        if duplicates:
            opportunities.append(dict(id='repeated-results', title='Review repeated unchanged results',
                evidence=[ident for ids in duplicates for ident in ids][:10],
                observation=f'{len(duplicates)} groups repeat an identical result at least three times.',
                action='Investigate reusable evidence or a bounded workflow/skill.',
                guardrail='Repeated reads may be necessary polling or revalidation. Verify freshness.'))
        for opportunity in opportunities:
            evidence_fingerprint = hashlib.sha256('|'.join(sorted(opportunity['evidence'])).encode()).hexdigest()[:16]
            opportunity['id'] += ':' + (task or project or 'all') + ':' + evidence_fingerprint
            opportunity['state'] = decisions.get(opportunity['id'], dict(decision='pending', implementation='not_started', evaluation='not_measured'))
        sequences = collections.Counter()
        previous = {}
        for event in events:
            key = (event['session_id'], event['turn_id'])
            if key in previous:
                sequences[(previous[key], event['category'])] += 1
            previous[key] = event['category']
        captures, capture_total = [], 0
        if self.capture_root:
            for path in self.capture_root.glob('*.json'):
                record = json.loads(path.read_text())
                if not record['path'].endswith('/responses'):
                    continue
                capture_total += 1
                response = record.get('response') or {}
                response_ids = set(record.get('response_ids', [])) | {event.get('response', {}).get('id') for event in response.get('sse_events', []) if isinstance(event, dict) and isinstance(event.get('response', {}), dict)}
                matching = next((e for e in scope_generations if any(ident and e['id'].endswith(':' + ident) for ident in response_ids)), None)
                correlation = 'response ID' if matching else 'unmatched'
                request = record.get('request') or {}
                session_id = request.get('prompt_cache_key') if isinstance(request, dict) else None
                if not matching and isinstance(session_id, str):
                    start, end = record['started_ns'], record.get('ended_ns', record['started_ns'])
                    candidates = [e for e in scope_generations if e['session_id'] == session_id and start <= bridge.nanos(e['ts']) <= end + 2_000_000_000]
                    if len(candidates) == 1:
                        matching, correlation = candidates[0], 'session + time (inferred)'
                if (project or task) and not matching:
                    continue
                body_available = record.get('response_body_available', not response.get('unparsed_body', False) and bool(response))
                captures.append(dict(id=record['id'], task_id=matching['task_id'] if matching else None,
                    state=record['state'], status=record.get('status'), request_bytes=record.get('request_bytes'), forwarded_request_bytes=record.get('forwarded_request_bytes',record.get('request_bytes')), compression=record.get('compression',dict(policy='off',changes=[])),
                    response_bytes=record.get('response_bytes'), response_truncated=record.get('response_truncated'),
                    elapsed_seconds=(record['ended_ns'] - record['started_ns']) / 1e9 if record.get('ended_ns') else None,
                    first_body_byte_seconds=(record['first_byte_ns'] - record['started_ns']) / 1e9 if record.get('first_byte_ns') else None,
                    response_body_available=body_available, correlation=correlation,
                    response_body_state=('partial' if record.get('response_truncated') else 'available') if body_available else ('not retained by legacy parser' if record.get('capture_schema', 1) < 2 else 'unsupported response format'),
                    model=request.get('model') if isinstance(request, dict) else None,
                    compression_url=self.langfuse_url + '/project/ttgl-codex/traces/' + bridge.digest('compression-v1:' + record['id']) if record.get('compression', {}).get('changes') else None,
                    started_at=datetime.fromtimestamp(record['started_ns'] / 1e9, timezone.utc).isoformat(),
                    langfuse_url=self.langfuse_url + '/project/ttgl-codex/traces/' + bridge.digest('transport-v1:' + record['id'])))
        selected_events = {e['id'] for e in events} | {capture['id'] for capture in captures}
        agent_reports = []
        for row in analyses:
            result = json.loads(row['report'])
            relevant = [finding for finding in result['findings'] if selected_events.intersection(finding['evidence_ids'])]
            if not relevant:
                continue
            agent_reports.append(dict(id=row['id'], created=row['created'], model=row['model'], snapshot_hash=row['snapshot_hash'],
                summary=result['summary'], findings=relevant, limitations=result['limitations'], scope=result['scope'],
                snapshot_at=result['snapshot_at'], tool_events=result['tool_events'],
                measured_snapshot_usage=result['measured_snapshot_usage'], overhead=json.loads(row['overhead'])))
        install = None
        if self.capture_root and (self.capture_root.parent / 'live-codex-install.json').exists():
            receipt = json.loads((self.capture_root.parent / 'live-codex-install.json').read_text())
            install = {k: receipt[k] for k in ('at','policy','base_url','scope')}
        return dict(projects=projects, tasks=tasks, turns=selected_turns, inbox=[t for t in turns if not t['task_id']],
            usage=totals, models=dict(models), categories=categories, events=events[-event_limit:] if event_limit else events, event_count=len(events),
            sequences=[dict(sequence=list(k), count=v) for k, v in sequences.most_common(20)],
            opportunities=opportunities, rules=rules, decisions=list(decisions.values()), audit=audit,
            wire_captures=captures,
            capture_coverage=dict(total_model_exchanges=capture_total, matched_selection=len(captures),
                selected_with_response_body=sum(c['response_body_available'] for c in captures),
                category_filter_applies=False, note='Task/project filters apply. Tool categories do not filter model HTTP exchanges. Legacy response bodies were not retained and cannot be reconstructed.'),
            usage_scope=dict(project_id=project, task_id=task, category=category, selected=totals,
                all_sources=all_usage, unassigned=unassigned_usage,
                note='Selected scope and all-source totals differ when tasks, projects or categories are filtered. Unassigned turns are included only in all-source totals.'),
            agent_analyses=agent_reports, runtime_accounting=accounting,
            experiments=[{**r, "baseline": {k: v for k, v in r["baseline"].items() if k != "events"}} for r in list_experiments(self, task) if not project or task_map.get(r["task_id"], {}).get("project_id") == project],
            sources=dict(live_compression_install=install, root=str(self.root), collection_enabled=enabled, files=len(files), errors=[dict(file=Path(f['path']).name, error=f['error']) for f in files if f['error']],
                         last_scan=max((f['mtime'] for f in files), default=None)),
            langfuse_url=self.langfuse_url + '/project/ttgl-codex', at=now(),
            limitations=['Native transcripts plus explicitly proxied HTTP/SSE captures; existing chat traffic is not retroactively proxied.', 'Runtime shares describe recorded tool-runtime sums; overlapping work is not task elapsed time.',
                          'Model latency, per-tool token attribution and actual charges are unknown.', 'Agent turn completion is not verified task success.',
                          'Unassigned turns stay in the inbox. History from other machines is not connected.', 'Opportunities are proposals; no automatic changes or savings claims.'])

    def reconcile(self):
        report = self.report()
        if not self.capture_root:
            return dict(status='unavailable', reason='No Langfuse credentials configured')
        try:
            c = json.loads((self.capture_root.parent / 'local-access.json').read_text())
            if c['base_url'] not in ('http://localhost:3000', 'http://127.0.0.1:3000'):
                raise ValueError('Expected loopback Langfuse')
            with self.connection() as db:
                first = db.execute("SELECT min(ts) FROM events WHERE kind='generation'").fetchone()[0]
            query = dict(view='observations', dimensions=[], metrics=[dict(measure='totalTokens', aggregation='sum')],
                filters=[dict(column='environment', operator='=', type='string', value='codex-native'),
                         dict(column='type', operator='any of', type='stringOptions', value=['GENERATION'])],
                # Metrics lower bounds can exclude an observation exactly on the
                # boundary. Include the first retained response with a small margin.
                fromTimestamp=(datetime.fromisoformat(first.replace('Z', '+00:00')) - timedelta(seconds=1)).isoformat() if first else now(), toTimestamp=now())
            auth = base64.b64encode((c['public_key'] + ':' + c['secret_key']).encode()).decode()
            request = urllib.request.Request(c['base_url'] + '/api/public/v2/metrics?' + urlencode({'query': json.dumps(query)}), headers={'Authorization': 'Basic ' + auth})
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.load(response)
            backend = sum(row.get('sum_totalTokens') or 0 for row in data.get('data', []))
            local = report['usage_scope']['all_sources']['total_tokens']
            return dict(status='matched' if backend == local else 'difference', local_all_sources=local,
                        langfuse_native_tokens=backend, difference=local - backend, checked_at=now(),
                        definition='All retained sources; environment codex-native; GENERATION only. Excludes transport observations and analysis snapshot summaries.',
                        note='Active generation and ingestion lag can produce a temporary difference; task filters describe smaller subsets. Persistent differences require source/date/environment reconciliation and are not silently adjusted.')
        except (OSError, ValueError, KeyError) as exc:
            return dict(status='unavailable', reason=type(exc).__name__ + ': ' + str(exc)[:180])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, value, status=200, content='application/json'):
        body = json.dumps(value).encode() if content == 'application/json' else value
        self.send_response(status)
        self.send_header('Content-Type', content)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def valid(self):
        return self.headers.get('Host') in self.server.allowed_hosts

    def do_GET(self):
        if not self.valid():
            return self.send({'error': 'Invalid host'}, 403)
        path = urlparse(self.path)
        if path.path in ('/api/workspace', '/api/agent-context'):
            query = parse_qs(path.query)
            filters = {k: query[k][0] for k in ('project', 'task', 'category') if k in query}
            result = self.server.store.report(**filters)
            return self.send(result)
        if path.path == '/api/health':
            return self.send({'status': 'OK'})
        if path.path == '/api/reconciliation':
            return self.send(self.server.store.reconcile())
        if path.path == '/api/rule-preview':
            pattern = parse_qs(path.query).get('pattern', [''])[0][:200]
            report = self.server.store.report()
            matches = [dict(id=e['id'], operation=e['name'], basis=e['category_basis']) for e in report['events']
                       if e['kind'] == 'tool' and pattern and pattern.lower() in e['name'].lower()]
            return self.send(dict(matches=matches[:10], total=len(matches),
                unreviewed=sum(m['basis'] != 'Codex agent interpretation' for m in matches),
                semantics='Case-insensitive literal substring of the operation label; not regex, not full command search, no LLM call.',
                window=1000))
        design_assets = {'/design-system/styles.css': 'text/css; charset=utf-8',
                         '/design-system/dom.js': 'text/javascript; charset=utf-8',
                         '/design-system/collection.js': 'text/javascript; charset=utf-8'}
        if path.path in design_assets:
            target = HERE.parents[2] / 'work/security/design-system' / path.path.rsplit('/', 1)[-1]
            if not target.exists():
                return self.send({'error': 'Private design-system distribution not synced; see sync_design_system.py'}, 503)
            return self.send(target.read_bytes(), content=design_assets[path.path])
        assets = {'/': ('workspace.html', 'text/html; charset=utf-8'), '/workspace.js': ('workspace.js', 'text/javascript; charset=utf-8'), '/workspace.css': ('workspace.css', 'text/css; charset=utf-8')}
        if path.path in assets:
            name, mime = assets[path.path]
            return self.send((getattr(self.server, 'ui_root', HERE) / name).read_bytes(), content=mime)
        if path.path == '/base.css':
            return self.send((HERE.parent / 'style.css').read_bytes(), content='text/css; charset=utf-8')
        self.send({'error': 'Not found'}, 404)

    def do_POST(self):
        origin = self.headers.get('Origin')
        if not self.valid() or origin not in self.server.allowed_origins:
            return self.send({'error': 'Same-origin request required'}, 403)
        action = self.path.removeprefix('/api/')
        if '/' in action:
            return self.send({'error': 'Not found'}, 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 32768:
                raise ValueError('Invalid request size')
            values = json.loads(self.rfile.read(length))
            if not isinstance(values, dict):
                raise ValueError('Expected an object')
            result = self.server.store.mutate(action, values)
            return self.send(result)
        except (ValueError, KeyError, sqlite3.IntegrityError) as exc:
            return self.send({'error': str(exc)}, 400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--codex-root', type=Path, default=Path.home() / '.codex')
    parser.add_argument('--langfuse-url', default='http://localhost:3000')
    parser.add_argument('--port', type=int, default=DEFAULTS['ports']['workspace'])
    parser.add_argument('--capture-root', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    store = Store(args.data, args.codex_root, args.langfuse_url, args.capture_root)
    store.scan()
    def watch():
        while True:
            try:
                store.scan()
            except Exception as exc:
                print(type(exc).__name__, str(exc)[:200], flush=True)
            time.sleep(DEFAULTS['collection']['workspace_poll_seconds'])
    threading.Thread(target=watch, daemon=True).start()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.store = store
    server.allowed_hosts = {f'127.0.0.1:{args.port}', f'localhost:{args.port}'}
    server.allowed_origins = {'http://' + host for host in server.allowed_hosts}
    if os.environ.get('CODESPACE_NAME'):
        host = f"{os.environ['CODESPACE_NAME']}-{args.port}.{os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'app.github.dev')}"
        server.allowed_hosts.add(host)
        server.allowed_origins.add('https://' + host)
    print(f'Project/task workspace: http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
