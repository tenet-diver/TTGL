"""Small JSON-RPC/MCP stdio adapter; no downloaded MCP SDK or auto installs."""
from __future__ import annotations
import json
import sys

REQUEST = {'type': 'object', 'additionalProperties': False, 'required': ['task_id', 'goal'],
           'properties': {'task_id': {'type': 'string'}, 'goal': {'type': 'string'},
                          'category': {'type': 'string'}, 'language': {'type': 'string'}, 'framework': {'type': 'string'},
                          'actions': {'type': 'array', 'items': {'type': 'string'}},
                          'required_capabilities': {'type': 'array', 'items': {'type': 'string'}}}}
TOOLS = [
    {'name': 'route_subtask', 'description': 'Check qualified cheaper executors using eligible action similarity and experience recency; no inference.',
     'inputSchema': REQUEST, 'annotations': {'readOnlyHint': True, 'openWorldHint': False}},
    {'name': 'delegate_subtask', 'description': 'Retain and dispatch one bounded autonomous worker attempt if the host route qualifies; no automatic retries or Sol fallback.',
     'inputSchema': {'type': 'object', 'additionalProperties': False, 'required': ['idempotency_key', 'request', 'contract'],
                     'properties': {'idempotency_key': {'type': 'string'}, 'request': REQUEST,
                                    'contract': {'type': 'object', 'additionalProperties': False,
                                     'required': ['base_checkpoint', 'allowed_write_paths', 'acceptance_checks'],
                                     'properties': {'base_checkpoint': {'type': 'string'},
                                                    'allowed_write_paths': {'type': 'array', 'items': {'type': 'string'}},
                                                    'acceptance_checks': {'type': 'array', 'items': {'type': 'string'}}}}}},
     'annotations': {'readOnlyHint': False, 'destructiveHint': False, 'openWorldHint': False}},
]
for name, description in (
    ('get_delegation', 'Read compact progress or retained terminal outcome for this host-owned attempt.'),
    ('cancel_delegation', 'Request cancellation: queued work will not dispatch; an active bounded native call may finish and its usage/artifacts remain retained.')):
    TOOLS.append({'name': name, 'description': description,
        'inputSchema': {'type': 'object', 'additionalProperties': False, 'required': ['attempt_id'],
                        'properties': {'attempt_id': {'type': 'string'}}},
        'annotations': {'readOnlyHint': name == 'get_delegation', 'openWorldHint': False}})


def handle(service, request):
    method, params = request.get('method'), request.get('params') or {}
    if method == 'initialize':
        versions = ('2024-11-05', '2025-03-26', '2025-06-18')
        return {'protocolVersion': params.get('protocolVersion') if params.get('protocolVersion') in versions else versions[-1],
                'capabilities': {'tools': {'listChanged': False}}, 'serverInfo': {'name': 'observatory-delegation', 'version': '0.1.0'}}
    if method == 'ping':
        return {}
    if method == 'tools/list':
        return {'tools': TOOLS}
    if method == 'tools/call':
        try:
            name, args = params['name'], params.get('arguments', {})
            if name == 'route_subtask':
                result = service.decision(args)
            elif name == 'delegate_subtask':
                result = service.submit(args)
            elif name in ('get_delegation', 'cancel_delegation'):
                if not isinstance(args, dict) or set(args) != {'attempt_id'}:
                    raise ValueError('An owned attempt_id is required')
                result = service.get(args['attempt_id']) if name == 'get_delegation' else service.cancel(args['attempt_id'])
            else:
                raise ValueError('Unknown delegation tool')
            return {'content': [{'type': 'text', 'text': json.dumps(result, allow_nan=False)}], 'isError': False}
        except Exception as error:
            return {'content': [{'type': 'text', 'text': type(error).__name__ + ': ' + str(error)[:500]}], 'isError': True}
    raise ValueError('Unsupported MCP method')


def serve(service, source=sys.stdin, sink=sys.stdout):
    for line in source:
        request = None
        try:
            if len(line.encode()) > 200_000:
                raise ValueError('MCP input exceeds bound')
            request = json.loads(line)
            if not isinstance(request, dict) or request.get('jsonrpc') != '2.0':
                raise ValueError('Invalid JSON-RPC request')
            if 'id' not in request:
                continue  # initialized/cancel notifications never launch a worker
            result = {'jsonrpc': '2.0', 'id': request['id'], 'result': handle(service, request)}
        except Exception as error:
            result = {'jsonrpc': '2.0', 'id': request.get('id') if isinstance(request, dict) else None,
                      'error': {'code': -32602, 'message': type(error).__name__}}
        sink.write(json.dumps(result, allow_nan=False) + '\n')
        sink.flush()
