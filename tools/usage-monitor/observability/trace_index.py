"""Bounded, deterministic investigations over the existing native evidence ledger.

No source rescans, inference, arbitrary SQL, new storage system or inferred grades.
The same query contract is used by HTTP, MCP and the analyst CLI.
"""
from datetime import datetime, timezone
import json
import re

from capture_proxy import sanitized

VIEWS = ('overview', 'turns', 'tools', 'patterns', 'steps')
SIGNALS = ('tool_failure', 'unknown_tool_outcome', 'repeated_input', 'unassigned')
FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')
LIMITS = [
    'Coverage is the indexed authorized native history, not all agent activity. Missing records do not establish zero usage.',
    'A native turn is an interaction, not necessarily a complete task. Completion markers and recorded task outcomes are not independent benchmark grades.',
    'A tool failure is a recorded unsuccessful operation, not a task failure. Repeated inputs/outputs are investigation leads, not proven retries or waste.',
    'Recorded tool runtime can overlap and include background process lifetime. It is not agent-blocking time or task wall time.',
    'Tokens are native response counters counted once. Cached input is a subset. Cash cost, per-tool model cost and savings are unknown here.',
]


def _date(value):
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError()
        return stamp.astimezone(timezone.utc).isoformat()
    except (ValueError, AttributeError):
        raise ValueError('since/until require an ISO timestamp with timezone') from None


def _select(filters):
    """Select whole turns; model/tool/signal match ANY event in that turn."""
    clauses, args = [], []
    for key, column in dict(project='ta.project_id', task='a.task_id', session='t.session_id',
                            turn='t.turn_id', status='ta.status').items():
        if filters.get(key):
            clauses.append(column + '=?')
            args.append(filters[key])
    for key, op in (('since', '>='), ('until', '<')):
        if filters.get(key):
            clauses.append('julianday(t.start)' + op + 'julianday(?)')
            args.append(_date(filters[key]))
    for key, column, kind in (('tool', 'name', 'tool'), ('model', 'model', 'generation')):
        if filters.get(key):
            clauses.append(f"EXISTS(SELECT 1 FROM events x WHERE x.session_id=t.session_id AND x.turn_id=t.turn_id AND x.kind='{kind}' AND x.{column}=?)")
            args.append(filters[key])
    signal = filters.get('signal')
    if signal:
        if signal not in SIGNALS:
            raise ValueError('Unknown signal')
        if signal == 'unassigned':
            clauses.append('a.task_id IS NULL')
        elif signal == 'repeated_input':
            clauses.append("""EXISTS(SELECT 1 FROM events x JOIN optimization_facts f ON f.event_id=x.id
                WHERE x.session_id=t.session_id AND x.turn_id=t.turn_id AND x.kind='tool' AND f.signature IS NOT NULL
                GROUP BY x.name,f.signature HAVING count(*)>1)""")
        else:
            outcome = 'x.failed=1' if signal == 'tool_failure' else 'x.failed IS NULL'
            clauses.append(f"EXISTS(SELECT 1 FROM events x WHERE x.session_id=t.session_id AND x.turn_id=t.turn_id AND x.kind='tool' AND {outcome})")
    if filters.get('query'):
        # Literal substring, including % and _, rather than an implicit SQL pattern.
        clauses.append("""(instr(lower(coalesce(t.prompt,'')),lower(?))>0 OR
            instr(lower(coalesce(ta.title,'')||' '||coalesce(ta.goal,'')||' '||coalesce(ta.outcome,'')),lower(?))>0 OR
            EXISTS(SELECT 1 FROM events x WHERE x.session_id=t.session_id AND x.turn_id=t.turn_id AND instr(lower(x.name),lower(?))>0))""")
        args.extend([filters['query']] * 3)
    return '''WITH selected AS (
        SELECT t.*,a.task_id,ta.title task_title,ta.status task_status,ta.outcome task_outcome,
               ta.project_id,p.name project_name
        FROM turns t LEFT JOIN assignments a USING(session_id,turn_id)
        LEFT JOIN tasks ta ON ta.id=a.task_id LEFT JOIN projects p ON p.id=ta.project_id
        WHERE ''' + (' AND '.join(clauses) or '1') + '''), evidence AS (
        SELECT e.* FROM events e JOIN selected s USING(session_id,turn_id)) ''', args


def _metrics(c, base, args):
    row = dict(c.execute(base + '''SELECT count(*) events,
        sum(kind='tool') tool_calls,sum(kind='generation') responses,
        sum(kind='tool' AND failed=1) tool_failures,
        sum(kind='tool' AND failed IS NOT NULL) known_tool_outcomes,
        sum(kind='tool' AND runtime IS NOT NULL) timed_tools,
        sum(CASE WHEN kind='tool' THEN runtime END) recorded_tool_runtime_seconds,
        sum(CASE WHEN kind='tool' THEN bytes END) recorded_output_bytes,
        sum(kind='generation' AND usage IS NOT NULL) metered_responses,
        min(ts) first_event,max(ts) last_event,
        ''' + ','.join(f"sum(CASE WHEN kind='generation' THEN json_extract(usage,'$.{k}') END) {k}" for k in FIELDS)
        + ' FROM evidence', args).fetchone())
    for key in ('tool_calls', 'responses', 'tool_failures', 'known_tool_outcomes', 'timed_tools', 'metered_responses'):
        row[key] = row[key] or 0
    row['unknown_tool_outcomes'] = row['tool_calls'] - row['known_tool_outcomes']
    row['unmetered_responses'] = row['responses'] - row['metered_responses']
    counts = dict(c.execute(base + '''SELECT count(*) turns,count(DISTINCT session_id) sessions,
        count(DISTINCT task_id) tasks,count(task_id) assigned_turns,
        coalesce(sum(completed=1),0) native_completion_markers FROM selected''', args).fetchone())
    return {**row, **counts}


def _page(c, base, sql, args, offset, limit, order):
    count = c.execute(base + 'SELECT count(*) FROM (' + sql + ')', args).fetchone()[0]
    records = [dict(r) for r in c.execute(base + sql + ' ORDER BY ' + order + ' LIMIT ? OFFSET ?', [*args, limit, offset])]
    return records, dict(total=count, offset=offset, limit=limit, next_offset=offset+limit if offset+limit < count else None)


def query(store, view='overview', offset=0, limit=20, sort='recent', detail='summary', pattern='input', **filters):
    allowed = {'project', 'task', 'session', 'turn', 'tool', 'model', 'status', 'since', 'until', 'signal', 'query', 'kind', 'fingerprint', 'operation'}
    if set(filters) - allowed:
        raise ValueError('Unsupported trace filter')
    if view not in VIEWS or sort not in ('recent', 'tokens', 'runtime', 'output', 'failures', 'count'):
        raise ValueError('Invalid trace view or sort')
    if detail not in ('summary', 'full') or pattern not in ('input', 'output'):
        raise ValueError('Invalid detail or pattern')
    if filters.get('kind') not in (None, '', 'tool', 'generation'):
        raise ValueError('kind must be tool or generation')
    if any(filters.get(key) for key in ('kind','fingerprint','operation')) and view != 'steps':
        raise ValueError('kind/fingerprint/operation apply only to steps')
    if filters.get('fingerprint') and not re.fullmatch('[0-9a-f]{64}', filters['fingerprint']):
        raise ValueError('Invalid fingerprint')
    offset, limit = int(offset), int(limit)
    if offset < 0 or not 1 <= limit <= 100:
        raise ValueError('offset must be >=0 and limit 1..100')
    if any(not isinstance(v, str) or len(v) > 500 for v in filters.values()):
        raise ValueError('Trace filters must be strings of at most 500 characters')
    if filters.get('since') and filters.get('until') and _date(filters['since']) >= _date(filters['until']):
        raise ValueError('since must precede until')
    base, args = _select(filters)
    result = dict(schema_version='trace-index-v1', view=view, filters=filters,
                  scope='Whole indexed native turns; since/until select turn START, inclusive/exclusive. Tool/model/signal match any event in the turn.',
                  limitations=LIMITS, navigation='Use steps with session+turn, then read_evidence(id). Assigned tasks also support get_task_history and get_task_evidence.')
    # One read transaction gives counts and pages a consistent snapshot while ingestion continues.
    with store.connection() as c:
        c.execute('BEGIN')
        result['metrics'] = _metrics(c, base, args)
        if view == 'overview':
            facets = {}
            for key, sql in {
                'tools': "SELECT name value,count(*) count FROM evidence WHERE kind='tool' GROUP BY name ORDER BY count DESC,name LIMIT 101",
                'models': "SELECT model value,count(*) count FROM evidence WHERE kind='generation' GROUP BY model ORDER BY count DESC,model LIMIT 101",
                'statuses': 'SELECT task_status value,count(*) count FROM selected GROUP BY task_status ORDER BY count DESC,task_status LIMIT 101',
                'projects': 'SELECT project_id value,project_name name,count(*) count FROM selected GROUP BY project_id,project_name ORDER BY count DESC,project_id LIMIT 101',
            }.items():
                rows = [dict(r) for r in c.execute(base + sql, args)]
                facets[key] = dict(records=rows[:100], truncated=len(rows)>100)
            result['facets'] = facets
            result['source_coverage'] = dict(c.execute('SELECT count(*) indexed_files,coalesce(sum(error IS NOT NULL),0) files_with_errors FROM files').fetchone())
            result['source_coverage']['note'] = 'Global source ledger, not restricted to this cohort. Indexing errors and missing source files require investigation.'
            return result
        if view == 'turns':
            sql = '''SELECT s.session_id,s.turn_id,s.task_id,s.task_title,s.task_status,s.project_id,s.project_name,
                s.start,s.end,s.completed native_completion_marker,count(e.id) events,
                sum(e.kind='tool') tool_calls,sum(e.kind='generation') responses,
                sum(e.kind='tool' AND e.failed=1) tool_failures,
                sum(e.kind='tool' AND e.failed IS NULL) unknown_tool_outcomes,
                sum(e.kind='tool' AND e.runtime IS NOT NULL) timed_tools,
                sum(CASE WHEN e.kind='tool' THEN e.runtime END) recorded_tool_runtime_seconds,
                sum(CASE WHEN e.kind='tool' THEN e.bytes END) recorded_output_bytes,
                sum(CASE WHEN e.kind='generation' THEN json_extract(e.usage,'$.total_tokens') END) total_tokens,
                sum(e.kind='generation' AND e.usage IS NOT NULL) metered_responses,
                group_concat(DISTINCT e.model) models''' + (',s.prompt,s.task_outcome' if detail == 'full' else '') + '''
                FROM selected s LEFT JOIN evidence e USING(session_id,turn_id) GROUP BY s.session_id,s.turn_id'''
            order = dict(recent='s.start DESC', tokens='total_tokens DESC', runtime='recorded_tool_runtime_seconds DESC',
                         output='recorded_output_bytes DESC', failures='tool_failures DESC', count='events DESC')[sort] + ',s.session_id,s.turn_id'
        elif view == 'tools':
            sql = '''SELECT name,count(*) calls,count(DISTINCT json_array(session_id,turn_id)) turns,
                coalesce(sum(failed=1),0) tool_failures,count(failed) known_tool_outcomes,sum(failed IS NULL) unknown_tool_outcomes,
                count(runtime) timed_calls,sum(runtime) recorded_tool_runtime_seconds,
                sum(bytes) recorded_output_bytes,max(ts) last_event,min(id) example_event_id
                FROM evidence WHERE kind='tool' GROUP BY name'''
            order = dict(recent='last_event DESC', tokens='calls DESC', runtime='recorded_tool_runtime_seconds DESC',
                         output='recorded_output_bytes DESC', failures='tool_failures DESC', count='calls DESC')[sort] + ',name'
        elif view == 'patterns':
            fingerprint = 'f.signature' if pattern == 'input' else 'e.output_hash'
            sql = f'''SELECT e.session_id,e.turn_id,e.name,{fingerprint} fingerprint,
                count(*) copies,coalesce(sum(e.failed=1),0) tool_failures,count(e.failed) known_tool_outcomes,count(e.runtime) timed_calls,
                sum(e.runtime) recorded_tool_runtime_seconds,sum(e.bytes) recorded_output_bytes,
                max(e.ts) last_event,min(e.id) example_event_id
                FROM evidence e LEFT JOIN optimization_facts f ON f.event_id=e.id
                WHERE e.kind='tool' AND {fingerprint} IS NOT NULL''' + (" AND e.bytes>0" if pattern == 'output' else '') + f'''
                GROUP BY e.session_id,e.turn_id,e.name,{fingerprint} HAVING count(*)>1'''
            order = dict(recent='last_event DESC', tokens='copies DESC', runtime='recorded_tool_runtime_seconds DESC',
                         output='recorded_output_bytes DESC', failures='tool_failures DESC', count='copies DESC')[sort] + ',e.session_id,e.turn_id,e.name,fingerprint'
            result['pattern_basis'] = 'Exact native input fingerprint within one turn' if pattern == 'input' else 'Exact nonempty retained output fingerprint within one turn'
        else:
            conditions, extras = ['1'], []
            if filters.get('kind'):
                conditions.append('e.kind=?'); extras.append(filters['kind'])
            if filters.get('fingerprint'):
                conditions.append(('f.signature' if pattern == 'input' else 'e.output_hash') + '=?'); extras.append(filters['fingerprint'])
            if filters.get('operation'):
                conditions.append('e.name=?'); extras.append(filters['operation'])
            sql = '''SELECT e.*,s.task_id,s.task_title,s.task_status,s.project_id,f.signature input_fingerprint
                FROM evidence e JOIN selected s USING(session_id,turn_id)
                LEFT JOIN optimization_facts f ON f.event_id=e.id WHERE ''' + ' AND '.join(conditions)
            order = dict(recent='e.ts DESC', tokens="json_extract(e.usage,'$.total_tokens') DESC", runtime='e.runtime DESC',
                         output='e.bytes DESC', failures='e.failed DESC', count='e.ts DESC')[sort] + ',e.id'
            args = [*args, *extras]
        records, result['pagination'] = _page(c, base, sql, args, offset, limit, order)
        for record in records:
            if view == 'turns':
                for key in ('tool_calls', 'responses', 'tool_failures', 'unknown_tool_outcomes', 'metered_responses', 'timed_tools'):
                    record[key] = record[key] or 0
                if detail == 'full':
                    record['prompt'] = sanitized((record.get('prompt') or '')[:2000])
                    record['task_outcome'] = sanitized((record.get('task_outcome') or '')[:2000])
            if view == 'steps':
                record['usage'] = json.loads(record['usage']) if record['usage'] else None
        result['records'] = records
        return result
