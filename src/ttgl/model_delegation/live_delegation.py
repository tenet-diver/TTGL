"""Native parent -> evidence route -> isolated worker -> verified integration.

The model chooses whether/what to delegate. The host owns snapshots, actor,
identity, clock and finite caps. No host-selected escalation or hidden feedback.
"""
from __future__ import annotations
import json
import time
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from ..experience_routing.checkpoints import manifest
from ..experience_routing.execution import docker, unpack_public_source, source_tar
from ..experience_routing.io import digest, read, write_new
from .routing import Policy, route, packet

SUBTASK_TYPES = ('implementation', 'exploration', 'verification', 'integration', 'planning')
FEATURES = {'goal': {'type': 'string'}, 'subtask_type': {'type': 'string', 'enum': list(SUBTASK_TYPES)},
            'constraints': {'type': 'array', 'items': {'type': 'string'}},
            'actions': {'type': 'array', 'items': {'type': 'string'}}}
TOOLS = [
    {'name': 'route_subtask', 'description': 'Check eligible cheaper-model availability and verified similar public experience before delegating bounded work. No inference.',
     'inputSchema': {'type': 'object', 'additionalProperties': False, 'properties': FEATURES,
                     'required': ['goal', 'subtask_type']}},
    {'name': 'delegate_subtask', 'description': 'Request one bounded autonomous cheaper worker. Includes your self-contained context/attempts in goal. The host routes, verifies scope/public checks and integrates the exact candidate; you must verify the result. No automatic Sol fallback or retry.',
     'inputSchema': {'type': 'object', 'additionalProperties': False,
                     'properties': {**FEATURES, 'idempotency_key': {'type': 'string'},
                                    'allowed_write_paths': {'type': 'array', 'description': 'Repository-relative paths inside /testbed; must be within the parent write scope.', 'items': {'type': 'string'}}},
                     'required': ['goal', 'subtask_type', 'idempotency_key', 'allowed_write_paths']}}]


def model_decision_view(value):
    """Keep exact host provenance while exposing opaque parent references."""
    public=deepcopy(value)
    for candidate in public.get('candidates',[]):
        for row in candidate.get('evidence',[]):
            if 'task_id' in row:
                row['source_parent_ref']=digest(row.pop('task_id'))
    return public


def decision(config, args):
    if (not isinstance(args, dict) or set(args)-set(FEATURES)-{'idempotency_key', 'allowed_write_paths'}
            or not isinstance(args.get('goal'), str) or not 0 < len(args['goal']) <= 12000
            or args.get('subtask_type') not in SUBTASK_TYPES):
        raise ValueError('Bounded self-contained typed handoff required')
    query = {**config['context'], **{k: v for k, v in args.items() if k in FEATURES},
             'now': config['now'], 'task_id': config['task']['task_id']}
    return route(query, config['experiences'], config['models'], Policy(**config.get('policy', {})))


def delegate(bridge, args):
    config = bridge.config['delegation']
    key = args.get('idempotency_key')
    if not isinstance(key, str) or not key or len(key) > 160:
        raise ValueError('Bounded idempotency identity required')
    folder = bridge.root/'delegations'/digest(key)
    if (folder/'started.json').exists():
        old = read(folder/'started.json')
        if old['arguments_hash'] != digest(args):
            raise ValueError('Conflicting handoff identity')
        if (folder/'completion.json').exists():
            return read(folder/'completion.json')
        raise ValueError('Prior handoff started or uncertain; do not repeat')
    if list((bridge.root/'delegations').glob('*/started.json')):
        raise ValueError('One-worker episode budget exhausted; integration reserved')
    supplied = args.get('allowed_write_paths')
    if not isinstance(supplied, list) or not supplied or any(not isinstance(p, str) for p in supplied):
        raise ValueError('Explicit actor-relative write scope required')
    requested = [p.removeprefix('/testbed/') for p in supplied]
    if any(Path(p).is_absolute() or '..' in Path(p).parts or not p or not any(
        allowed == '.' or p == allowed or p.startswith(allowed.rstrip('/')+'/')
        for allowed in config['task']['allowed_write_paths']) for p in requested):
        raise ValueError('Worker scope exceeds parent contract')
    selection = decision(config, args)
    if not selection['selected_model']:
        return {'status': 'needs_parent', 'decision_id': selection['decision_id'], 'model_call_started': False}
    if time.time()+config['worker_timeout_seconds']+config['integration_reserve_seconds'] > bridge.deadline:
        raise ValueError('Insufficient shared time for worker plus parent integration')
    write_new(folder/'started.json', {'arguments_hash': digest(args), 'decision': selection})
    raw = docker('exec', bridge.container, 'tar', '-cf', '-', '-C', '/testbed', '.')
    scratch = Path(config['worker_scratch_root'])/digest(key) if config.get('worker_scratch_root') else folder
    source = scratch/'source'
    source.mkdir(parents=True, mode=0o700)
    unpack_public_source(raw, source)
    initial = manifest(source)
    task = {**config['task'], 'prompt': args['goal'], 'allowed_write_paths': requested}
    from .episode import run_episode
    result = run_episode(root=bridge.config['repository_root'], output=folder/'worker', source=source,
        source_home=config['source_home'], model=selection['selected_model'], image_review=config['image_review'],
        task=task, packet=packet(selection, config['experiences'], config['maximum_packet_bytes']),
        timeout_seconds=config['worker_timeout_seconds'], maximum_tool_calls=config['worker_maximum_tool_calls'],
        registration=config.get('registration'))
    integrated = False
    if result['status'] == 'completed':
        # Parent state must still equal the handed-off state. No clobbering a
        # concurrent accepted edit while the native worker was running.
        with TemporaryDirectory(prefix='parent-check-', dir=scratch) as directory:
            current = Path(directory)
            unpack_public_source(docker('exec', bridge.container, 'tar', '-cf', '-', '-C', '/testbed', '.'), current)
            if manifest(current) != initial:
                raise ValueError('Parent changed during handoff; integration refused')
        docker('exec', bridge.container, 'sh', '-c', 'find /testbed -mindepth 1 -maxdepth 1 -exec rm -rf {} +')
        docker('exec', '-i', bridge.container, 'sh', '-c', 'umask 000; tar -xpf - -C /testbed', input=source_tar(source))
        integrated = True
    output = {'status': 'integrated_public_candidate' if integrated else 'needs_parent',
              'selected_model': selection['selected_model'], 'decision_id': selection['decision_id'],
              'worker_status': result['status'], 'native_usage': result['native_usage'],
              'candidate_archive': result['candidate_archive'], 'model_report': result['model_report'],
              'parent_must_verify': True, 'automatic_fallback': False}
    write_new(folder/'completion.json', output)
    return output
