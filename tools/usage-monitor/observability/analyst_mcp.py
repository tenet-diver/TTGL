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
    return dict(type='object', properties={k: {'type': 'string', 'description': v} for k, v in properties.items()},
                required=list(required), additionalProperties=False)


TOOLS = [
    dict(name='query_activity', description='Query native Codex task/project evidence. Tokens are measured; model latency and cash charges unknown.',
         inputSchema=schema(dict(project='Optional project ID', task='Optional task ID', category='Optional category', section='summary (compact), events, turns, projects, tasks, opportunities, rules, wire_captures, agent_analyses, runtime_accounting, experiments, experiment_accounting or sources', offset='Zero-based events offset (default 0)', limit='Events page size 1..100 (default 20)', sort='Events sort: ts, runtime or bytes (descending)', kind='Events kind: tool or generation', search='Case-insensitive substring of operation name'))),
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
         inputSchema=schema(dict(id='Event ID from query_activity events, or capture ID from wire_captures', offset='Character offset, default 0', limit='Characters 1..16000, default 4000', view='raw (default) or pull_progress; removes only recognized transient Docker progress and preserves raw access'), ('id',))),
]
TOOLS.append(dict(name='plan_experiment', description='Save a proposed experiment with a frozen assigned-task baseline, measurement plan and quality/rollback guards. List experiments and opportunities first to check for existing proposals. Does not execute anything.', inputSchema=schema(dict(task_id='Assigned baseline task ID', title='Short experiment title', change='One changed harness variable', metrics='Primary metric, comparison design and decision threshold', quality_gate='Acceptance criteria and quality retention threshold', overhead='Account for analyst, implementation and evaluation costs', rollback='When and how to revert'), ('task_id', 'title', 'change', 'metrics', 'quality_gate', 'overhead', 'rollback'))))
TOOLS.append(dict(name='review_experiment', description='Record an evidence-based keep, reject or inconclusive verdict on measured trial results. Measurements cannot be edited by agents. Keep requires the registered acceptance gate to pass.', inputSchema=schema(dict(evaluation_id='Measured evaluation ID from experiments', verdict='keep, reject or inconclusive', notes='Evidence IDs, interpretation, scope, overhead and remaining limitations'), ('evaluation_id', 'verdict', 'notes'))))
for tool in TOOLS:
    tool['annotations'] = dict(readOnlyHint=tool['name'] in ('query_activity', 'read_evidence'), destructiveHint=False, openWorldHint=False)

ACTION = dict(create_project='project', create_task='task', assign_turn='assign', set_task_status='task_status',
              update_category_rule='rule', record_opportunity_review='decision')


def handle(store, request):
    method = request.get('method')
    params = request.get('params') or {}
    if method == 'initialize':
        supported = ['2024-11-05', '2025-03-26', '2025-06-18']
        version = params.get('protocolVersion')
        return dict(protocolVersion=version if version in supported else supported[-1],
                    capabilities={'tools': {'listChanged': False}}, serverInfo=dict(name='ttgl-codex-analyst', version='1.1.0'))
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
            if any(not isinstance(v, str) for v in arguments.values()):
                raise ValueError('Arguments must be strings')
            if name == 'read_evidence':
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
                        result = sanitized(json.loads(path.read_text()))
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
                if arguments.get('section') in ('experiments', 'experiment_accounting'):
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
                        result = dict(experiments=[{**r, 'baseline': {k: v for k, v in r['baseline'].items() if k != 'events'}} for r in records])
                    return dict(content=[dict(type='text', text=json.dumps(result))], isError=False)
                result = store.report(event_limit=None, **{k: arguments[k] for k in ('project', 'task', 'category') if k in arguments})
                scope_count, prior_count = result['event_count'], len(result['agent_analyses'])
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
