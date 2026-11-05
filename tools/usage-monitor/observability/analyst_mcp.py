#!/usr/bin/env python3
"""Local stdio MCP access to task definitions, native evidence and review states."""
import argparse
import json
from pathlib import Path
import sys

from workspace import Store
from workspace import bridge
from capture_proxy import sanitized


def schema(properties, required=()):
    return dict(type='object', properties={k: {'type': 'string', 'description': v} for k, v in properties.items()},
                required=list(required), additionalProperties=False)


TOOLS = [
    dict(name='query_activity', description='Query native Codex task/project evidence. Tokens are measured; model latency and cash charges unknown.',
         inputSchema=schema(dict(project='Optional project ID', task='Optional task ID', category='Optional category', section='all, summary, events, turns, projects, tasks, opportunities, rules, wire_captures, agent_analyses, runtime_accounting or sources'))),
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
         inputSchema=schema(dict(id='Event ID from query_activity events, or capture ID from wire_captures'), ('id',))),
]
ACTION = dict(create_project='project', create_task='task', assign_turn='assign', set_task_status='task_status',
              update_category_rule='rule', record_opportunity_review='decision')


def handle(store, request):
    method = request.get('method')
    params = request.get('params') or {}
    if method == 'initialize':
        supported = ['2024-11-05', '2025-03-26', '2025-06-18']
        version = params.get('protocolVersion')
        return dict(protocolVersion=version if version in supported else supported[-1],
                    capabilities={'tools': {'listChanged': False}}, serverInfo=dict(name='ttgl-codex-analyst', version='1.0.0'))
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
                text = json.dumps(result)
                result = dict(evidence=text[:64000], truncated=len(text) > 64000, source='native or explicit proxy evidence', raw_reasoning_included=False)
            elif name == 'query_activity':
                result = store.report(**{k: arguments[k] for k in ('project', 'task', 'category') if k in arguments})
                section = arguments.get('section', 'summary')
                if section == 'summary':
                    result = {k: result[k] for k in ('usage', 'categories', 'models', 'event_count', 'sources', 'limitations', 'runtime_accounting', 'agent_analyses')}
                elif section != 'all':
                    if section not in ('events', 'turns', 'projects', 'tasks', 'opportunities', 'rules', 'sources', 'wire_captures', 'agent_analyses', 'runtime_accounting'):
                        raise ValueError('Unsupported section')
                    result = {section: result[section]}
                # Bound analyst payload; a section filter avoids oversized context.
                if isinstance(result.get('events'), list):
                    result['events'] = result['events'][-100:]
                    result['events_limit'] = 100
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
