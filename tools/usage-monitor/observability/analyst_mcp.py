#!/usr/bin/env python3
"""Local stdio MCP access to task definitions, native evidence and review states."""
import argparse
import json
from pathlib import Path
import sys

from workspace import Store
from workspace import bridge
from capture_proxy import sanitized
from progress_output import compact
from analyst_experiments import list_experiments, plan_experiment, review_experiment


def schema(properties, required=()):
    return dict(type='object', properties={k: {'type': ['string', 'integer'] if k in ('offset', 'limit') else 'string', 'description': v} for k, v in properties.items()},
                required=list(required), additionalProperties=False)


TOOLS = [
    dict(name='query_activity', description='Query native Codex task/project evidence. Tokens are measured; model latency and cash charges unknown.',
         inputSchema=schema(dict(project='Optional project ID', task='Optional task ID', session='Optional exact native session ID; intersects project/task scope', refresh='true to scan authorized native sources incrementally before query; default false', category='Optional category', section='summary (compact), events, turns, projects, tasks, opportunities, rules, wire_captures, agent_analyses, runtime_accounting, experiments, experiment_accounting or sources', offset='Zero-based events offset (default 0)', limit='Events/turns/tasks page size 1..100 (default 20)', sort='Events sort: ts, runtime or bytes (descending)', kind='Events kind: tool or generation', search='Case-insensitive substring of operation name', detail='summary (default) or full. Turns omit prompts and tasks omit goal/acceptance in summary; full preserves them. Experiments full includes measured cells, sources and reviews'))),
    dict(name='create_project', description='Define a project and repository scope. Does not authorize collection from new sources.',
         inputSchema=schema(dict(name='Project name', repo='Repository path', scope='Analysis scope'), ('name', 'repo'))),
    dict(name='create_task', description='Define intended outcome and acceptance criteria before task efficiency analysis.',
         inputSchema=schema(dict(project_id='Existing project ID', title='Task title', goal='Intended outcome', acceptance='Verification criteria'), ('project_id', 'title', 'goal'))),
    dict(name='assign_turn', description='Associate one collected native turn with a defined task, preserving source identity.',
         inputSchema=schema(dict(session_id='Native session ID', turn_id='Native turn ID', task_id='Defined task ID'), ('session_id', 'turn_id', 'task_id'))),
    dict(name='set_task_status', description='Record active, waiting, completed, cancelled or unresolved. Completion requires outcome evidence.',
         inputSchema=schema(dict(id='Task ID', status='New status', outcome='Verification evidence; not an inferred success'), ('id', 'status'))),
    dict(name='update_category_rule', description='Create or revise a literal operation classification rule. Preserves raw evidence and increments rule version.',
         inputSchema=schema(dict(id='Optional existing rule ID', category='Category name', pattern='Literal substring in native operation name'), ('category', 'pattern'))),
    dict(name='record_opportunity_review', description='Record a proposal decision and separate implementation/evaluation states. Does not execute a change.',
         inputSchema=schema(dict(id='Opportunity ID', decision='review, declined or deferred', implementation='not_started, prepared, applied or reverted',
                                 evaluation='not_measured, trial_planned, in_progress, improved, regressed or inconclusive', notes='Evidence, concrete plan, trial results and rollback notes'), ('id',))),
    dict(name='read_evidence', description='Read one retained native operation or one redacted captured HTTP pair by its evidence ID. Opaque reasoning is omitted. Output is bounded.',
         inputSchema=schema(dict(id='Event ID from query_activity events, or capture ID from wire_captures', offset='Character offset, default 0', limit='Characters 1..16000, default 4000', view='raw (default) or pull_progress; removes only recognized transient Docker progress and preserves raw access', part='For HTTP evidence: record (default), original_request, forwarded_request, response or compression'), ('id',))),
]
TOOLS.append(dict(name='plan_experiment', description='Save a proposed experiment with a frozen assigned-task baseline, measurement plan and quality/rollback guards. List experiments and opportunities first to check for existing proposals. Does not execute anything.', inputSchema=schema(dict(task_id='Assigned baseline task ID', title='Short experiment title', change='One changed harness variable', metrics='Primary metric, comparison design and decision threshold', quality_gate='Acceptance criteria and quality retention threshold', overhead='Account for analyst, implementation and evaluation costs', rollback='When and how to revert'), ('task_id', 'title', 'change', 'metrics', 'quality_gate', 'overhead', 'rollback'))))
TOOLS.append(dict(name='review_experiment', description='Record an evidence-based keep, reject or inconclusive verdict on measured trial results. Measurements cannot be edited by agents. Keep requires the registered acceptance gate to pass.', inputSchema=schema(dict(evaluation_id='Measured evaluation ID from experiments', verdict='keep, reject or inconclusive', notes='Evidence IDs, interpretation, scope, overhead and remaining limitations'), ('evaluation_id', 'verdict', 'notes'))))
TOOLS.append(dict(name='read_compression_source', description='Retrieve retained pre-compression tool text by SHA256 from a live request transform. Retrieval is never re-compressed. Redaction and retention limits still apply.', inputSchema=schema(dict(sha256='64 lowercase hexadecimal SHA256 from a TTGL live presentation marker', offset='Character offset, default 0', limit='Characters 1..16000, default 4000'), ('sha256',))))
TOOLS.extend([
    dict(name='search_task_history', description='Search task goals, outcomes, interpreted subtasks, activity tags and native operation labels. Read-only keyword search by default; semantic mode explicitly invokes the configured local embedding service. Results are summaries; use get_task_history and read_evidence to drill down. Filter status=completed to find completed experiences; completion is user-recorded evidence.', inputSchema=schema(dict(query='Words to search', project='Optional project ID', status='Optional task status, e.g. completed', activity='Optional subtask activity: investigate, plan, implement, test, review, document, operate, other', mode='keyword (default) or semantic (requires configured local embeddings)', limit='1..100, default 20', offset='Zero-based page offset'))),
    dict(name='get_task_history', description='Progressive history retrieval: task and latest subtask summaries, then bounded source steps for one subtask. Stale interpretations are labeled. Use read_evidence with a returned step ID for raw evidence.', inputSchema=schema(dict(task_id='Task ID', subtask_id='Optional subtask ID from this task', limit='1..100 steps, default 20', offset='Zero-based step offset'), ('task_id',))),
    dict(name='analyze_task_history', description='Explicitly start one on-demand small-model subtask analysis of an assigned task. Invokes inference; tracks overhead and failed attempts. Unchanged evidence reuses its analysis. No automatic retries or scheduled inference.', inputSchema=schema(dict(task_id='Task ID'), ('task_id',))),
])
for tool in TOOLS:
    tool['annotations'] = dict(readOnlyHint=tool['name'] in ('query_activity', 'read_evidence', 'read_compression_source', 'search_task_history', 'get_task_history'), destructiveHint=False, openWorldHint=False)

ACTION = dict(create_project='project', create_task='task', assign_turn='assign', set_task_status='task_status',
              update_category_rule='rule', record_opportunity_review='decision')


def handle(store, request):
    method = request.get('method')
    params = request.get('params') or {}
    if method == 'initialize':
        supported = ['2024-11-05', '2025-03-26', '2025-06-18']
        version = params.get('protocolVersion')
        return dict(protocolVersion=version if version in supported else supported[-1],
                    capabilities={'tools': {'listChanged': False}}, serverInfo=dict(name='ttgl-codex-analyst', version='1.2.0'))
    if method == 'ping':
        return {}
    if method == 'tools/list':
        return {'tools': TOOLS}
    if method == 'tools/call':
        name, arguments = params.get('name'), params.get('arguments') or {}
        definition = next((t for t in TOOLS if t['name'] == name), None)
        if not definition:
            return dict(isError=True, content=[dict(type='text', text='Unknown tool')])
        try:
            if not isinstance(arguments, dict) or set(arguments) - set(definition['inputSchema']['properties']):
                raise ValueError('Unsupported arguments')
            if any(k not in arguments for k in definition['inputSchema']['required']):
                raise ValueError('Missing required argument')
            if any(not isinstance(v, str) and not (k in ('offset', 'limit') and type(v) is int) for k, v in arguments.items()):
                raise ValueError('Arguments must be strings, or integers for offset/limit')
            arguments = {k: str(v) if type(v) is int else v for k, v in arguments.items()}
            if name in ('search_task_history','get_task_history','analyze_task_history'):
                import task_history
                if name == 'search_task_history':result = task_history.search(store, **arguments)
                elif name == 'get_task_history':result = task_history.detail(store, **arguments)
                else:result = task_history.start(store, arguments['task_id'])
            elif name == 'read_compression_source':
                digest = arguments['sha256']
                if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest) or not store.capture_root:
                    raise ValueError('Invalid SHA256 or no authorized capture source')
                record = json.loads((store.capture_root / 'compression_sources' / (digest + '.json')).read_text())
                offset, limit = int(arguments.get('offset', '0')), int(arguments.get('limit', '4000'))
                if offset < 0 or not 1 <= limit <= 16000:
                    raise ValueError('offset must be >=0 and limit 1..16000')
                text = record['content']; end = min(len(text), offset + limit)
                result = dict(TTGL_RAW_EVIDENCE=True, source_sha256=digest, content=text[offset:end],
                    total_characters=len(text), next_offset=end if end < len(text) else None,
                    retention=record['retention'], retained_sha256=record['retained_sha256'])
            elif name == 'read_evidence':
                ident = arguments['id']
                with store.connection() as c:
                    event = c.execute('SELECT * FROM events WHERE id=?', (ident,)).fetchone()
                    paths = [Path(r['path']) for r in c.execute('SELECT path FROM files')]
                result = None
                if event:
                    for path in paths:
                        meta = None
                        for line, record in bridge.monitor.lines(path):
                            if not record:
                                continue
                            if record.get('type') == 'session_meta':
                                meta = record.get('payload') or {}
                            if meta and meta.get('id') == event['session_id'] and line == event['source_line']:
                                payload = record.get('payload') or {}
                                # Usage records contain no account balances; operation records use the native item only.
                                result = sanitized(payload.get('item') if event['kind'] == 'tool' else payload.get('usage'))
                                break
                        if result is not None:
                            break
                elif store.capture_root and len(ident) == 32 and all(c in '0123456789abcdef' for c in ident):
                    path = store.capture_root / (ident + '.json')
                    if path.exists():
                        record = json.loads(path.read_text())
                        part = arguments.get('part', 'record')
                        keys = dict(original_request='request', forwarded_request='forwarded_request', response='response', compression='compression')
                        if part != 'record' and part not in keys:
                            raise ValueError('Unsupported capture part')
                        result = sanitized(record if part == 'record' else record.get(keys[part], record.get('request') if part == 'forwarded_request' else dict(unavailable=True)))
                if result is None:
                    raise ValueError('Evidence unavailable in this authorized source')
                view = arguments.get('view', 'raw')
                if view not in ('raw', 'pull_progress'):
                    raise ValueError('view must be raw or pull_progress')
                presentation = None
                retention = None
                if isinstance(result, dict) and isinstance(result.get('aggregated_output'), str):
                    retention = dict(incomplete=True if 'command output truncated for persistence' in result['aggregated_output'] else None,
                                     exit_code=result.get('exit_code'), coverage_basis='Known native persistence marker; absence does not prove completeness')
                    if view == 'pull_progress':
                        presentation = compact(result['aggregated_output'])
                        result = {**result, 'aggregated_output': presentation.pop('output')}
                elif view == 'pull_progress':
                    raise ValueError('pull_progress requires native command output; use raw for other evidence')
                text = json.dumps(result)
                offset, limit = int(arguments.get('offset', '0')), int(arguments.get('limit', '4000'))
                if offset < 0 or not 1 <= limit <= 16000:
                    raise ValueError('offset must be >=0 and limit 1..16000')
                end = min(offset + limit, len(text))
                result = dict(id=ident, evidence=text[offset:end], offset=offset, total_characters=len(text),
                              next_offset=end if end < len(text) else None, truncated=end < len(text), source='native or explicit proxy evidence', raw_reasoning_included=False,
                              retention=retention, presentation=presentation, view=view, raw_access='Same ID with view=raw; missing original content cannot be recovered')
            elif name == 'review_experiment':
                result = review_experiment(store, arguments)
            elif name == 'plan_experiment':
                result = plan_experiment(store, arguments)
            elif name == 'query_activity':
                if arguments.get('refresh', 'false') not in ('true', 'false'):
                    raise ValueError('refresh must be true or false')
                if arguments.get('refresh') == 'true':
                    store.scan()
                if arguments.get('section') in ('experiments', 'experiment_accounting'):
                    if arguments.get('session'):
                        raise ValueError('Session filtering is supported for native activity, not experiment records')
                    records = list_experiments(store, arguments.get('task'), arguments.get('project'))
                    if arguments.get('section') == 'experiment_accounting':
                        result = dict(experiment_accounting=[])
                        for record in records:
                            if not record['accounting']:
                                continue
                            latest = record['accounting'][-1]
                            payload = latest['payload']
                            components = {name: {**value, 'native_response_ids': value['native_response_ids'][:1]+value['native_response_ids'][-1:],
                                'native_response_count': len(value['native_response_ids'])} for name, value in payload['components'].items()}
                            result['experiment_accounting'].append(dict(experiment_id=record['id'], **{**latest, 'payload': {**payload, 'components': components}}))
                    else:
                        if arguments.get('detail', 'summary') not in ('summary', 'full'):
                            raise ValueError('detail must be summary or full')
                        if arguments.get('detail', 'summary') == 'full':
                            result = dict(experiments=[{**r, 'baseline': {k: v for k, v in r['baseline'].items() if k != 'events'}} for r in records])
                        else:
                            summaries = []
                            for record in records:
                                latest = record['evaluations'][-1] if record['evaluations'] else None
                                measured = latest['measurements'] if latest else {}
                                summaries.append(dict(id=record['id'], title=record['proposal']['title'], task_id=record['task_id'],
                                    project_id=record['baseline']['task']['project_id'],state=record['state'],
                                    latest_evaluation=dict(id=latest['id'],protocol=latest['protocol']['id'],
                                        **{k: measured.get(k) for k in ('scope','raw_total_tokens','compact_total_tokens','token_reduction_fraction','acceptance_passed')},
                                        latest_verdict=latest['reviews'][-1]['verdict'] if latest['reviews'] else None) if latest else None))
                            result = dict(experiments=summaries, navigation='Request section=experiments, project=PROJECT_ID, detail=full for original measured cells, source IDs and reviews.')
                    return dict(content=[dict(type='text', text=json.dumps(result))], isError=False)
                result = store.report(event_limit=None, **{k: arguments[k] for k in ('project', 'task', 'category', 'session') if k in arguments})
                associated = {t['task_id'] for t in result['turns']}
                scope_count, prior_count = result['event_count'], len(result['agent_analyses'])
                coverage = dict(session_id=arguments.get('session'), indexed_turns=len(result['turns']), indexed_events=scope_count, refresh_requested=arguments.get('refresh') == 'true', note='Indexed authorized native records only; no matches do not establish zero inference. Live completion/usage can lag.')
                timestamps = [e['ts'] for e in result['events'] if e['ts']]
                time_range = dict(first_at=min(timestamps) if timestamps else None, last_at=max(timestamps) if timestamps else None)
                section = arguments.get('section', 'summary')
                if section == 'summary':
                    result = {k: result[k] for k in ('usage', 'categories', 'models', 'event_count', 'sources', 'limitations', 'runtime_accounting', 'usage_scope', 'capture_coverage')}
                    result['time_range'] = time_range
                    result['prior_analysis_count'] = prior_count
                    result['navigation'] = 'List tasks and exact categories first; events supports offset/limit/sort/kind/search. Read original records with read_evidence. Prior interpretations available via agent_analyses. Save trials via plan_experiment.'
                elif section != 'all':
                    if section not in ('events', 'turns', 'projects', 'tasks', 'opportunities', 'rules', 'sources', 'wire_captures', 'agent_analyses', 'runtime_accounting'):
                        raise ValueError('Unsupported section')
                    result = {section: result[section]}
                if section == 'tasks' and arguments.get('session'):
                    result['tasks'] = [t for t in result['tasks'] if t['id'] in associated]
                if section in ('turns', 'tasks'):
                    offset, limit = int(arguments.get('offset', '0')), int(arguments.get('limit', '20'))
                    if offset < 0 or not 1 <= limit <= 100:
                        raise ValueError('offset must be >=0 and limit 1..100')
                    detail = arguments.get('detail', 'summary')
                    if detail not in ('summary', 'full'):
                        raise ValueError('detail must be summary or full')
                    records = result[section]
                    page = records[offset:offset+limit]
                    omitted = ('prompt',) if section == 'turns' else ('goal', 'acceptance', 'outcome')
                    result[section] = page if detail == 'full' else [{k: v for k, v in t.items() if k not in omitted} for t in page]
                    result['pagination'] = dict(offset=offset, limit=limit, matched_in_window=len(records), next_offset=offset+limit if offset+limit < len(records) else None)
                    result['navigation'] = 'Use detail=full for retained prompts or task details, with the same offset/limit.'
                # Bound analyst payload; a section filter avoids oversized context.
                if isinstance(result.get('events'), list):
                    offset, limit = int(arguments.get('offset', '0')), int(arguments.get('limit', '20'))
                    if offset < 0 or not 1 <= limit <= 100:
                        raise ValueError('offset must be >=0 and limit 1..100')
                    sort = arguments.get('sort', 'ts')
                    if sort not in ('ts', 'runtime', 'bytes'):
                        raise ValueError('sort must be ts, runtime or bytes')
                    if arguments.get('kind') not in (None, 'tool', 'generation'):
                        raise ValueError('kind must be tool or generation')
                    events = [e for e in result['events'] if (not arguments.get('kind') or e['kind'] == arguments['kind']) and arguments.get('search', '').lower() in e['name'].lower()]
                    events.sort(key=lambda e: e[sort] or ('' if sort == 'ts' else 0), reverse=True)
                    result['events'] = events[offset:offset+limit]
                    result['pagination'] = dict(offset=offset, limit=limit, matched_in_window=len(events), next_offset=offset+limit if offset+limit < len(events) else None, window_limit=None, scope_event_count=scope_count)
                    if not events:
                        result['hint'] = 'No matches. List tasks and summary categories for exact IDs/names; remove category or search filters. Events are paginated across the full selected scope.'
                if arguments.get('session'):
                    result['session_coverage'] = coverage
            else:
                result = store.mutate(ACTION[name], arguments)
            return dict(content=[dict(type='text', text=json.dumps(result))], isError=False)
        except Exception as exc:
            return dict(content=[dict(type='text', text=type(exc).__name__ + ': ' + str(exc)[:300])], isError=True)
    raise ValueError('Method not found')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--codex-root', type=Path, default=Path.home() / '.codex')
    parser.add_argument('--langfuse-url', default='http://localhost:3000')
    parser.add_argument('--capture-root', type=Path)
    args = parser.parse_args()
    store = Store(args.data, args.codex_root, args.langfuse_url, args.capture_root)
    for line in sys.stdin:
        try:
            if len(line) > 65536:
                raise ValueError('Request too large')
            request = json.loads(line)
            if 'id' not in request:
                continue
            response = dict(jsonrpc='2.0', id=request['id'])
            try:
                response['result'] = handle(store, request)
            except ValueError as exc:
                response['error'] = dict(code=-32601, message=str(exc))
        except (ValueError, TypeError) as exc:
            response = dict(jsonrpc='2.0', id=None, error=dict(code=-32700, message='Invalid JSON-RPC request'))
        print(json.dumps(response), flush=True)


if __name__ == '__main__':
    main()
