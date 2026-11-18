from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from threading import Event
from unittest.mock import patch

from ttgl.model_delegation.routing import Policy, packet, route
from ttgl.model_delegation.service import DelegationService
from ttgl.model_delegation.mcp import handle, serve


NOW = datetime(2026, 11, 18, 12, tzinfo=timezone.utc)


def query():
    return {'task_id': 'current', 'goal': 'repair pagination cursor', 'project': 'p', 'study': 's', 'arm': 'a',
            'account_hash': 'source', 'parent_model': 'sol', 'rate_scenario': 'frozen', 'watermark': 100,
            'now': NOW.isoformat(), 'category': 'implement', 'subtask_type': 'implementation', 'constraints': [],
            'actions': ['edit', 'test'], 'language': 'python'}


def models():
    return [{'model': name, 'unit_cost': cost, 'rate_scenario': 'frozen', 'account_hash': 'source',
             'available': True, 'qualified': True, 'checked_at': (NOW-timedelta(hours=1)).isoformat(),
             'expires_at': (NOW+timedelta(hours=1)).isoformat(), 'capabilities': ['edit']}
            for name, cost in [('luna', 1), ('sol', 20)]]


def experience(index, age=1, outcome='pass', **changes):
    q = query()
    t = (NOW-timedelta(days=age)).isoformat()
    return {**{k: q[k] for k in ('project', 'study', 'arm', 'account_hash', 'goal', 'category', 'subtask_type', 'constraints', 'actions', 'language')},
            'id': str(index), 'task_id': 'past-'+str(index), 'model': 'luna', 'visibility': 'runtime_public',
            'granularity': 'subtask', 'executor_model': 'luna', 'assistance': 'none',
            'outcome_target': 'public_integrated_completion',
            'guidance_context_ref': 'retained-request-'+str(index) if changes.get('assistance') == 'retrieved_guidance' else None,
            'verified': True, 'verification_ref': 'check-'+str(index), 'source_current': True, 'outcome': outcome,
            'occurred_at': t, 'verified_at': t, 'available_at': t, 'available_sequence': index,
            'procedure': ['Read relevant code', 'Edit and verify'], **changes}


def teacher_guidance():
    return experience(99, model='sol', executor_model='sol', guidance={
        'id': 'procedure-v1', 'supported': True, 'source_model': 'sol',
        'procedure': ['Use a stable cursor comparison', 'Run pagination acceptance checks'],
        'preconditions': [], 'acceptance_criteria': ['No missing or repeated rows'],
        'evidence_refs': ['check-99'], 'target_models': ['luna']})


class RoutingTests(unittest.TestCase):
    def test_recent_independent_successes_delegate(self):
        r = route(query(), [experience(i) for i in range(3)], models())
        self.assertEqual(r['selected_model'], 'luna')
        self.assertFalse(r['automatic_large_fallback'])

    def test_parent_task_similarity_is_not_subtask_competence(self):
        for changes in ({'granularity': 'task'}, {'subtask_type': 'exploration'}, {'outcome_target': 'model_self_report'}):
            r = route(query(), [experience(i, **changes) for i in range(3)], models())
            self.assertEqual(r['status'], 'needs_parent')
        with self.assertRaises(ValueError):
            route(query(), [], models(), Policy(evidence_profile='whole_task_proxy'))

    def test_assisted_or_misattributed_success_is_not_independent_luna_success(self):
        for changes in ({'assistance': 'expert'}, {'assistance': 'human'}, {'assistance': 'unknown'}, {'executor_model': 'sol'}):
            r = route(query(), [experience(i, **changes) for i in range(3)], models())
            self.assertEqual(r['status'], 'needs_parent')

    def test_teacher_guidance_is_available_without_manufacturing_student_success(self):
        xs = [teacher_guidance()]
        r = route(query(), xs, models())
        self.assertEqual(r['status'], 'needs_parent')
        self.assertEqual(r['candidates'][0]['independent_parents'], 0)
        self.assertTrue(r['candidates'][0]['guided_trial_available'])
        trial = route(query(), xs, models(), Policy(mode='always_cheap'))
        self.assertEqual(packet(trial, xs, 8000)['guidance'][0]['source_model'], 'sol')

    def test_guided_small_model_success_requires_the_same_available_guidance_version(self):
        xs = [experience(i, assistance='retrieved_guidance', guidance_used_ids=['procedure-v1']) for i in range(3)]
        self.assertEqual(route(query(), xs, models())['status'], 'needs_parent')
        xs.append(teacher_guidance())
        r = route(query(), xs, models())
        self.assertEqual(r['selected_model'], 'luna')
        self.assertEqual(r['candidates'][0]['guided_execution_parents'], 3)
        self.assertEqual(r['candidates'][0]['guided_successful_parents'], 3)
        self.assertEqual(r['candidates'][0]['independent_execution_parents'], 0)
        p = packet(r, xs, 8000)
        self.assertEqual(p['guidance'][0]['id'], 'procedure-v1')
        self.assertIn('acceptance_criteria', p['guidance'][0])
        self.assertNotIn('procedure', p['experiences'][0])

    def test_guidance_claim_without_retained_exposure_is_not_success_evidence(self):
        xs = [experience(i, assistance='retrieved_guidance', guidance_used_ids=['procedure-v1'], guidance_context_ref=None) for i in range(3)]
        self.assertEqual(route(query(), xs+[teacher_guidance()], models())['status'], 'needs_parent')

    def test_inapplicable_unlinked_and_oversize_grounding_cannot_support_guided_route(self):
        base = [experience(i, assistance='retrieved_guidance', guidance_used_ids=['procedure-v1']) for i in range(3)]
        for change in ({'preconditions': ['unavailable-api']}, {'evidence_refs': ['unrelated-check']},
                       {'source_model': 'different-model'}, {'target_models': ['other-student']}, {'supported': False}):
            teacher = teacher_guidance(); teacher['guidance'].update(change)
            self.assertEqual(route(query(), base+[teacher], models())['status'], 'needs_parent', change)
        r = route(query(), base+[teacher_guidance()], models(), Policy(maximum_packet_bytes=80))
        self.assertEqual(r['status'], 'needs_parent')
        self.assertFalse(r['candidates'][0]['grounding_fits_packet'])

    def test_missing_guidance_does_not_erase_known_student_failure(self):
        xs = [experience(i) for i in range(3)]
        xs.append(experience(4, outcome='fail', assistance='retrieved_guidance', guidance_used_ids=['unavailable']))
        r = route(query(), xs, models())
        self.assertTrue(any(e['id'] == '4' for e in r['candidates'][0]['evidence']))
        self.assertEqual(r['candidates'][0]['required_guidance_ids'], [])

    def test_similarity_ablation_admits_old_evidence_recency_declines(self):
        xs = [experience(i, age=100) for i in range(3)]
        self.assertEqual(route(query(), xs, models(), Policy(mode='similarity'))['status'], 'delegate')
        self.assertEqual(route(query(), xs, models())['status'], 'needs_parent')

    def test_recent_failures_outweigh_many_old_successes(self):
        xs = [experience(i, age=60) for i in range(8)] + [experience(i, outcome='fail') for i in (8, 9)]
        self.assertEqual(route(query(), xs, models(), Policy(mode='similarity'))['status'], 'delegate')
        self.assertEqual(route(query(), xs, models())['status'], 'needs_parent')

    def test_reimport_does_not_refresh_observed_experience_age(self):
        xs = [experience(i, age=100, available_at=NOW.isoformat()) for i in range(3)]
        r = route(query(), xs, models())
        self.assertEqual(r['status'], 'needs_parent')
        self.assertEqual(r['candidates'][0]['evidence'][0]['age_days'], 100)

    def test_parent_duplicates_cannot_manufacture_support(self):
        xs = [experience(i, task_id='same-parent') for i in range(20)]
        r = route(query(), xs, models())
        self.assertEqual(r['status'], 'needs_parent')
        self.assertEqual(r['candidates'][0]['independent_parents'], 1)

    def test_all_cheap_still_enforces_availability_and_account(self):
        for field, value in [('available', False), ('qualified', False), ('account_hash', 'other'),
                             ('expires_at', NOW.isoformat()), ('unit_cost', 20), ('rate_scenario', 'other')]:
            ms = models(); ms[0][field] = value
            self.assertEqual(route(query(), [], ms, Policy(mode='always_cheap'))['status'], 'needs_parent', field)

    def test_future_scope_private_stale_same_task_and_lineage_rejected(self):
        cases = [{'available_sequence': 101}, {'available_at': (NOW+timedelta(days=1)).isoformat()},
                 {'account_hash': 'other'}, {'study': 'other'}, {'arm': 'other'}, {'visibility': 'sealed'},
                 {'verified': False}, {'source_current': False}, {'task_id': 'current'},
                 {'verification_ref': ''}, {'outcome': 'unknown'}, {'language': 'rust'},
                 {'framework': 'unavailable'}, {'leakage_groups': ['excluded']}]
        for changes in cases:
            q = {**query(), 'excluded_leakage_groups': ['excluded']}
            xs = [experience(i, **changes) for i in range(3)]
            self.assertEqual(route(q, xs, models())['status'], 'needs_parent', changes)

    def test_supported_capabilities_are_required(self):
        q = {**query(), 'required_capabilities': ['browser']}
        self.assertEqual(route(q, [], models(), Policy(mode='always_cheap'))['status'], 'needs_parent')

    def test_packet_is_bounded_and_keeps_evidence_references(self):
        xs = [experience(i) for i in range(3)]
        r = route(query(), xs, models())
        self.assertEqual(packet(r, xs, 2)['experiences'], [])
        p = packet(r, xs, 1000)
        self.assertTrue(p['experiences'])
        self.assertLessEqual(p['bytes_upper_bound'], 1000)
        self.assertIn('verification_ref', p['experiences'][0])

    def test_age_ablation_keeps_worker_packet_identical_when_both_delegate(self):
        xs = [experience(0, age=20)] + [experience(i) for i in (1, 2, 3)]
        a = route(query(), xs, models(), Policy(mode='similarity'))
        b = route(query(), xs, models(), Policy(mode='similarity_recency'))
        self.assertEqual(a['status'], 'delegate'); self.assertEqual(b['status'], 'delegate')
        self.assertEqual(packet(a, xs, 8000), packet(b, xs, 8000))

    def test_invalid_policy_numbers_and_duplicate_ids_rejected(self):
        for changes in [{'half_life_days': 0}, {'half_life_days': float('nan')}, {'minimum_parents': True},
                        {'minimum_similarity': 2}, {'minimum_weight': -1}]:
            with self.assertRaises(ValueError): Policy(**changes)
        with self.assertRaises(ValueError): route(query(), [experience(0), experience(0)], models())
        with self.assertRaises(ValueError): route({**query(), 'now': '2026-11-18T00:00:00'}, [], models())

    def test_future_check_and_malformed_features_do_not_authorize_execution(self):
        future = (NOW+timedelta(days=1)).isoformat()
        xs = [experience(i, verified_at=future, available_at=future) for i in range(3)]
        self.assertEqual(route(query(), xs, models())['status'], 'needs_parent')
        for changes in ({'actions': 'edit'}, {'required_capabilities': [1]}, {'category': []}):
            with self.assertRaises(ValueError): route({**query(), **changes}, [], models())


class ToolTests(unittest.TestCase):
    def service(self, folder, worker=None):
        q = query()
        context = {k: v for k, v in q.items() if k not in ('task_id', 'goal', 'subtask_type', 'constraints', 'category', 'actions', 'language', 'now')}
        return DelegationService(context=context, experiences=[experience(i) for i in range(3)], models=models(),
            output=folder, worker=worker, clock=lambda: NOW.isoformat())

    def arguments(self):
        q = query()
        return {'idempotency_key': 'one', 'request': {k: q[k] for k in ('task_id', 'goal', 'category', 'subtask_type', 'constraints', 'actions', 'language')},
                'contract': {'base_checkpoint': 'base', 'allowed_write_paths': ['src'], 'acceptance_checks': ['pagination']}}

    def test_delegate_worker_uses_selected_model_and_terminal_idempotency(self):
        calls = []
        def worker(request, contract, decision, evidence, folder):
            calls.append(decision['selected_model'])
            return {'status': 'public_checks_passed', 'checks': ['pagination'], 'benchmark_grade': None}
        with tempfile.TemporaryDirectory() as t:
            s = self.service(t, worker)
            first = s.delegate(self.arguments()); second = s.delegate(self.arguments())
            self.assertEqual(calls, ['luna']); self.assertEqual(first['status'], 'public_checks_passed')
            self.assertTrue(second['reused_terminal_receipt'])
            altered = self.arguments(); altered['request']['goal'] = 'different'
            with self.assertRaises(ValueError): s.delegate(altered)

    def test_uncertain_worker_is_not_reexecuted(self):
        calls = []
        def worker(*args): calls.append(1); raise RuntimeError('uncertain native completion')
        with tempfile.TemporaryDirectory() as t:
            s = self.service(t, worker)
            with self.assertRaises(RuntimeError): s.delegate(self.arguments())
            self.assertEqual(s.delegate(self.arguments())['status'], 'uncertain')
            self.assertEqual(calls, [1])

    def test_no_worker_is_blocked_not_success(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(self.service(t).delegate(self.arguments())['status'], 'blocked')

    def test_scope_and_clock_belong_to_host(self):
        with tempfile.TemporaryDirectory() as t:
            s = self.service(t)
            for key in ('account_hash', 'now', 'watermark', 'study'):
                with self.assertRaises(ValueError): s.decision({**self.arguments()['request'], key: 'malicious'})
            for path in ('../secret', '/root', '.git/config', '.'):
                args = self.arguments(); args['contract']['allowed_write_paths'] = [path]
                with self.assertRaises(ValueError): s.delegate(args)

    def test_stdio_mcp_roundtrip_and_invalid_tool_arguments(self):
        with tempfile.TemporaryDirectory() as t:
            s = self.service(t)
            messages = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
                        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                        {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
                        {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'route_subtask', 'arguments': self.arguments()['request']}}]
            out = io.StringIO(); serve(s, io.StringIO('\n'.join(map(json.dumps, messages))), out)
            rows = [json.loads(line) for line in out.getvalue().splitlines()]
            self.assertEqual([r['id'] for r in rows], [1, 2, 3])
            self.assertEqual(json.loads(rows[-1]['result']['content'][0]['text'])['selected_model'], 'luna')
            self.assertTrue(handle(s, {'method': 'tools/call', 'params': {'name': 'route_subtask', 'arguments': {'now': 'fake'}}})['isError'])

    def test_parent_mcp_preview_keeps_full_guidance_out_of_parent_context(self):
        with tempfile.TemporaryDirectory() as t:
            s = self.service(t)
            s.experiences = [experience(i, assistance='retrieved_guidance', guidance_used_ids=['procedure-v1']) for i in range(3)] + [teacher_guidance()]
            result = handle(s, {'method': 'tools/call', 'params': {'name': 'route_subtask', 'arguments': self.arguments()['request']}})
            preview = json.loads(result['content'][0]['text'])
            self.assertEqual(preview['selected_model'], 'luna')
            self.assertEqual(preview['candidates'][0]['guided_successful_parents'], 3)
            self.assertNotIn('Use a stable cursor comparison', result['content'][0]['text'])

    def test_native_worker_cannot_bypass_execution_gate(self):
        from ttgl.model_delegation.native import NativeNodeWorker
        with patch.dict(os.environ, {'OBS_ALLOW_DELEGATION_MODELS': '0'}):
            with self.assertRaises(ValueError): NativeNodeWorker(config={}, client=None, campaign_budget=None)

    def test_native_freeze_drift_is_rejected_before_runtime_setup(self):
        from ttgl.model_delegation.native import worker_from_freeze
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/'freeze.json'; p.write_text('{}')
            with self.assertRaises(ValueError): worker_from_freeze(p, service_config={'native_freeze_sha256': 'different'})

    def test_cli_stdio_server_and_discovery_in_separate_process(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); q = query()
            context = {k: q[k] for k in ('project', 'study', 'arm', 'account_hash', 'parent_model', 'rate_scenario', 'watermark')}
            (root/'experiences.json').write_text('[]'); (root/'models.json').write_text(json.dumps(models()))
            cfg = {'context': context, 'experiences': str(root/'experiences.json'), 'models': str(root/'models.json'), 'output': str(root/'attempts')}
            (root/'host.json').write_text(json.dumps(cfg))
            request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}
            p = subprocess.run([sys.executable, '-m', 'ttgl.model_delegation', 'serve', '--config', str(root/'host.json')],
                input=json.dumps(request)+'\n', capture_output=True, text=True, timeout=10)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual({x['name'] for x in json.loads(p.stdout)['result']['tools']},
                             {'route_subtask', 'delegate_subtask', 'get_delegation', 'cancel_delegation'})

    def test_async_poll_cancel_and_restart_never_duplicate_dispatch(self):
        entered, release, calls = Event(), Event(), []
        def worker(*args):
            calls.append(1); entered.set(); release.wait(timeout=5)
            return {'status': 'public_checks_passed'}
        with tempfile.TemporaryDirectory() as t:
            service = self.service(t, worker)
            try:
                one = service.submit(self.arguments()); self.assertTrue(entered.wait(2))
                self.assertEqual(service.get(one['attempt_id'])['status'], 'running')
                two_args = self.arguments(); two_args['idempotency_key'] = 'two'
                two = service.submit(two_args)
                self.assertEqual(service.cancel(two['attempt_id'])['status'], 'cancellation_requested')
                self.assertEqual(service.cancel(one['attempt_id'])['status'], 'cancellation_requested')
                altered = self.arguments(); altered['request']['goal'] = 'different'
                with self.assertRaises(ValueError): service.submit(altered)
                restarted = self.service(t, worker)
                try:
                    self.assertEqual(restarted.get(one['attempt_id'])['status'], 'uncertain')
                    self.assertEqual(restarted.submit(self.arguments())['status'], 'uncertain')
                finally: restarted.close()
                release.set(); service.close()
                self.assertEqual(calls, [1])
                self.assertEqual(service.get(one['attempt_id'])['retained_worker_outcome'], 'public_checks_passed')
                self.assertFalse(service.get(two['attempt_id'])['dispatched'])
            finally:
                release.set(); service.close()

    def test_native_adapter_with_synthetic_transport_edits_checks_and_retains(self):
        from ttgl.model_delegation.native import NativeNodeWorker
        from ttgl.experience_routing.checkpoints import manifest
        from ttgl.experience_routing.ledger import Budget
        from ttgl.personal import Response
        class FakeActor:
            def __init__(self, **kwargs): pass
            def start(self, workspace): return 'synthetic-owned-actor'
            def before_attempt(self, workspace): pass
            def after_attempt(self, workspace): pass
            def close(self): pass
            def public_check(self, argv, workspace, timeout):
                r = subprocess.run(argv, cwd=workspace, capture_output=True, timeout=timeout)
                return {'returncode': r.returncode, 'output': r.stdout.decode()+r.stderr.decode(), 'infrastructure_error': False}
        retained = []
        class Client:
            def retain_file(self, path, **kwargs):
                self.assertion = Path(path).is_file()
                if not self.assertion: raise ValueError('Missing retained bytes')
                retained.append(str(path)); return {'artifactId': str(len(retained))}
        with tempfile.TemporaryDirectory() as t:
            workspace = Path(t)/'source'; workspace.mkdir(); (workspace/'value.py').write_text('def run(): return 0\n')
            exposed_guidance = []
            class FakeBackend:
                fixture_only = True
                def __init__(self, **kwargs): pass
                def complete(self, request):
                    exposed_guidance.extend(g for g in json.loads(request.prompt)['experiences']['experiences'] if g.get('supportKind') == 'grounded_procedure')
                    (workspace/'value.py').write_text('def run(): return 42\n')
                    return Response(text=json.dumps({'summary': 'Synthetic source edit', 'changedArtifacts': ['value.py'],
                        'publicChecks': [], 'unresolved': [], 'usedExperienceIds': [], 'escalate': False}),
                        thread_id='synthetic', usage={'input_tokens': 10, 'cached_input_tokens': 0, 'output_tokens': 5, 'total_tokens': 15}, elapsed_seconds=.01)
            cfg = {'allow_model_execution': True, 'source_home': '/synthetic', 'account_hash': 'source',
                'workspace': str(workspace), 'image': 'synthetic-image', 'image_review': str(Path(t)/'review.json'), 'base_commit': 'synthetic-base',
                'codex_executable': '/synthetic', 'codex_sha256': 'synthetic', 'node_executable': '/synthetic',
                'models': {'luna': {'reasoning_effort': 'low'}}, 'watermark': 100, 'snapshot_id': 'synthetic-snapshot',
                'rates': {'luna': {'input': 1, 'cached': .1, 'output': 1}},
                'per_attempt': {'maximum_invocations': 2, 'maximum_tokens': 1000, 'maximum_elapsed_seconds': 30},
                'check_catalog': {'pagination': {'argv': [sys.executable, '-B', '-c', 'from value import run; assert run()==42']}}}
            (Path(t)/'review.json').write_text('{}')
            args = self.arguments(); args['contract']['base_checkpoint'] = manifest(workspace)['state_hash']
            args['contract']['allowed_write_paths'] = ['value.py']
            with patch.dict(os.environ, {'OBS_ALLOW_DELEGATION_MODELS': '1'}), \
                 patch('ttgl.experience_routing.backend.source_binding', return_value={'account_hash': 'source'}), \
                 patch('ttgl.experience_routing.backend.RecordedCodexBackend', FakeBackend), \
                 patch('ttgl.experience_routing.execution.DockerWorkspace', FakeActor):
                worker = NativeNodeWorker(config=cfg, client=Client(), campaign_budget=Budget(4, 10000, 60))
                service = self.service(Path(t)/'attempts', worker)
                service.experiences = [experience(i, assistance='retrieved_guidance', guidance_used_ids=['procedure-v1']) for i in range(3)] + [teacher_guidance()]
                result = service.delegate(args)
            self.assertEqual(result['status'], 'public_checks_passed')
            self.assertEqual(result['accounting']['actual_invocations'], 1)
            self.assertIsNone(result['benchmark_grade'])
            self.assertTrue(any('source.tar' in name for name in retained))
            self.assertTrue(any('checks' in name for name in retained))
            self.assertEqual(exposed_guidance[0]['sourceModel'], 'sol')
            self.assertEqual(exposed_guidance[0]['versionId'], 'procedure-v1')


if __name__ == '__main__': unittest.main()
