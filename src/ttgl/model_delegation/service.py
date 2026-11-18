"""Retained routing/dispatch tool. Caller cannot set source, clock or watermark."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import re
from ..experience_routing.io import digest, read, write_new
from .routing import Policy, packet, route


class DelegationService:
    def __init__(self, *, context, experiences, models, output, policy=Policy(), worker=None, clock=None):
        self.context = dict(context)
        self.experiences, self.models = experiences, models
        self.output, self.policy, self.worker = Path(output), policy, worker
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='observatory-delegation')
        self.jobs, self.job_lock = {}, Lock()

    def identity(self, arguments):
        key = arguments.get('idempotency_key') if isinstance(arguments, dict) else None
        if not isinstance(key, str) or not key:
            raise ValueError('Nonempty idempotency key required')
        return digest([self.context, key])

    def submit(self, arguments):
        identity, request_hash = self.identity(arguments), digest(arguments)
        folder = self.output/'jobs'/identity
        with self.job_lock:
            if folder.exists():
                if read(folder/'queued.json')['request_hash'] != request_hash:
                    raise ValueError('Idempotency key reused with different queued work')
                return self.get(identity)
            if sum(not f.done() for f in self.jobs.values()) >= 4:
                raise ValueError('Bounded delegation queue is full')
            folder.mkdir(parents=True, exist_ok=False, mode=0o700)
            write_new(folder/'queued.json', {'attempt_id': identity, 'request_hash': request_hash,
                                            'host_scope_hash': digest(self.context)})
            def run():
                if (folder/'cancel-requested.json').exists():
                    result = {'status': 'cancelled', 'attempt_id': identity, 'dispatched': False}
                else:
                    write_new(folder/'running.json', {'attempt_id': identity})
                    try:
                        result = self.delegate(arguments)
                    except Exception as error:
                        result = {'status': 'uncertain' if (self.output/identity/'uncertain.json').exists() else 'blocked',
                                  'attempt_id': identity, 'reason': type(error).__name__+': '+str(error)[:300]}
                if (folder/'cancel-requested.json').exists() and result['status'] not in ('uncertain', 'blocked', 'cancelled'):
                    result = {**result, 'status': 'cancelled', 'retained_worker_outcome': result['status']}
                write_new(folder/'terminal.json', result)
                return result
            self.jobs[identity] = self.pool.submit(run)
        return {'status': 'queued', 'attempt_id': identity, 'automatic_retry': False}

    def _job_folder(self, identity):
        if not isinstance(identity, str) or not re.fullmatch('[0-9a-f]{64}', identity):
            raise ValueError('Invalid owned delegation identity')
        folder = self.output/'jobs'/identity
        if read(folder/'queued.json')['host_scope_hash'] != digest(self.context):
            raise ValueError('Delegation belongs to another host scope')
        return folder

    def get(self, identity):
        folder = self._job_folder(identity)
        if (folder/'terminal.json').exists():
            return read(folder/'terminal.json')
        if identity not in self.jobs:
            return {'status': 'uncertain', 'attempt_id': identity, 'automatic_retry': False,
                    'reason': 'Worker owner restarted; retained queued/running work is never redispatched automatically'}
        if self.jobs[identity].done():
            return {'status': 'uncertain', 'attempt_id': identity, 'automatic_retry': False,
                    'reason': 'Worker stopped without a durable terminal receipt'}
        return {'status': 'cancellation_requested' if (folder/'cancel-requested.json').exists() else 'running' if (folder/'running.json').exists() else 'queued',
                'attempt_id': identity}

    def cancel(self, identity):
        folder = self._job_folder(identity)
        if (folder/'terminal.json').exists():
            return read(folder/'terminal.json')
        if not (folder/'cancel-requested.json').exists():
            write_new(folder/'cancel-requested.json', {'attempt_id': identity, 'requested_at': self.clock()})
        return {**self.get(identity), 'cancellation_semantics': 'Queued dispatch is prevented. An already running bounded native call may finish; its artifacts and usage are retained. This does not claim immediate process termination.'}

    def close(self):
        self.pool.shutdown(wait=True)

    def decision(self, arguments):
        if not isinstance(arguments, dict) or set(arguments) - {'task_id', 'goal', 'subtask_type', 'constraints', 'category', 'actions', 'language', 'framework', 'required_capabilities'}:
            raise ValueError('Unsupported caller fields; source and scope belong to host')
        query = {**arguments, **self.context, 'now': self.clock()}
        return route(query, self.experiences, self.models, self.policy)

    def delegate(self, arguments):
        if not isinstance(arguments, dict) or set(arguments) != {'idempotency_key', 'request', 'contract'}:
            raise ValueError('Delegation requires idempotency_key, request and contract')
        if not isinstance(arguments['idempotency_key'], str) or not arguments['idempotency_key']:
            raise ValueError('Nonempty idempotency key required')
        contract = arguments['contract']
        if not isinstance(contract, dict) or set(contract) != {'base_checkpoint', 'allowed_write_paths', 'acceptance_checks'}:
            raise ValueError('Bounded delegation contract required')
        if not isinstance(contract['base_checkpoint'], str) or not contract['base_checkpoint']:
            raise ValueError('Base checkpoint is required')
        for field in ('allowed_write_paths', 'acceptance_checks'):
            if not isinstance(contract[field], list) or not contract[field] or any(not isinstance(x, str) or not x for x in contract[field]):
                raise ValueError('Nonempty contract ' + field + ' required')
        for value in contract['allowed_write_paths']:
            p = Path(value)
            if p.is_absolute() or '..' in p.parts or '.git' in p.parts or not p.parts:
                raise ValueError('Unsafe write scope')
        identity = self.identity(arguments)
        folder = self.output / identity
        request_hash = digest(arguments)
        if folder.exists():
            start = read(folder / 'started.json')
            if start['request_hash'] != request_hash:
                raise ValueError('Idempotency key reused with a different contract')
            if (folder / 'result.json').exists():
                return {**read(folder / 'result.json'), 'reused_terminal_receipt': True}
            return {'status': 'uncertain', 'attempt_id': identity, 'automatic_retry': False}
        # mkdir is exclusive across concurrent MCP clients. No second dispatch.
        folder.mkdir(parents=True, exist_ok=False, mode=0o700)
        write_new(folder / 'started.json', {'attempt_id': identity, 'request_hash': request_hash, 'host_scope_hash': digest(self.context)})
        try:
            decision = self.decision(arguments['request'])
            write_new(folder / 'decision.json', decision)
            evidence = packet(decision, self.experiences, self.policy.maximum_packet_bytes)
            if decision['status'] != 'delegate':
                result = {'status': 'needs_parent', 'selected_model': None}
            elif self.worker is None:
                result = {'status': 'blocked', 'reason': 'No qualified native worker attached', 'selected_model': decision['selected_model']}
            else:
                result = self.worker(arguments['request'], contract, decision, evidence, folder)
                if not isinstance(result, dict) or result.get('status') not in ('public_checks_passed', 'public_checks_failed', 'needs_parent', 'blocked', 'uncertain', 'cancelled'):
                    raise ValueError('Worker returned an unknown terminal state')
            result = {**result, 'attempt_id': identity, 'decision_id': decision['decision_id'], 'automatic_retry': False}
            write_new(folder / 'result.json', result)
            return result
        except BaseException as error:
            write_new(folder / 'uncertain.json', {'attempt_id': identity, 'error': type(error).__name__, 'automatic_retry': False})
            raise
