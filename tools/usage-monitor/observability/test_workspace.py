import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
import urllib.parse
from unittest.mock import patch, MagicMock
from http.server import ThreadingHTTPServer

from workspace import Store, Handler
import analyst_mcp


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.store = Store(self.root / 'data', self.root / 'codex', 'http://localhost:3000')
        source = self.root / 'codex/sessions/sample.jsonl'
        source.parent.mkdir(parents=True)
        self.source = source
        rows = [
            dict(type='session_meta', payload=dict(id='s', cwd='/repo', timestamp='2026-11-05T00:00:00Z')),
            dict(type='turn_context', payload=dict(turn_id='t', model='test-model')),
            dict(type='event_msg', payload=dict(type='task_started', turn_id='t')),
            dict(type='event_msg', payload=dict(type='item_completed', turn_id='t', item=dict(type='UserMessage', content=[dict(type='text', text='Fix the problem')]))),
            dict(type='event_msg', payload=dict(type='item_completed', thread_id='s', turn_id='t', item=dict(type='CommandExecution', id='tool', command=['rg', 'foo'], aggregated_output='x' * 40000, exit_code=0, duration=dict(secs=2, nanos=0)))),
            dict(type='token_usage_record', payload=dict(thread_id='s', turn_id='t', response_id='r', usage=dict(input_tokens=100, cached_input_tokens=80, output_tokens=10, total_tokens=110))),
            dict(type='token_usage_record', payload=dict(thread_id='s', turn_id='t', response_id='r', usage=dict(input_tokens=100, cached_input_tokens=80, output_tokens=10, total_tokens=110))),
            dict(type='token_usage_record', payload=dict(thread_id='foreign', turn_id='other', response_id='foreign', usage=dict(input_tokens=1000, cached_input_tokens=0, output_tokens=10, total_tokens=1010))),
            dict(type='event_msg', payload=dict(type='task_complete', turn_id='t')),
        ]
        self.rows = [dict(r, timestamp='2026-11-05T00:00:01Z') for r in rows]
        self.source.write_text(''.join(json.dumps(r) + '\n' for r in self.rows))

    def define_task(self):
        project = self.store.mutate('project', dict(name='Test', repo='/repo'))['id']
        task = self.store.mutate('task', dict(project_id=project, title='Fix', goal='Resolve failure', acceptance='Checks pass'))['id']
        return project, task

    def test_idempotent_import_reconciled_usage_and_native_runtime(self):
        self.store.scan()
        self.store.ingest(self.source)
        report = self.store.report()
        self.assertEqual(report['event_count'], 2)
        self.assertEqual(report['usage']['total_tokens'], 110)
        self.assertEqual(len(report['inbox']), 1)
        self.assertEqual(report['categories'][0]['name'], 'search')
        self.assertEqual(report['categories'][0]['runtime_seconds'], 2)
        self.assertIsNone(next(e for e in report['events'] if e['kind'] == 'generation')['runtime'])

    def test_assignment_and_project_task_category_filters(self):
        self.store.scan()
        project, task = self.define_task()
        self.assertEqual(self.store.report(task=task)['event_count'], 0)
        self.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
        self.assertEqual(self.store.report(project=project)['event_count'], 2)
        self.assertEqual(self.store.report(task=task, category='search')['usage']['total_tokens'], 0)
        self.assertEqual(self.store.report(task=task, category='model inference')['usage']['total_tokens'], 110)
        self.assertEqual(self.store.report()['inbox'], [])

    def test_completion_requires_verification_and_review_states_are_separate(self):
        _, task = self.define_task()
        with self.assertRaises(ValueError):
            self.store.mutate('task_status', dict(id=task, status='completed'))
        self.store.mutate('task_status', dict(id=task, status='completed', outcome='Verified checks'))
        self.store.mutate('decision', dict(id='opportunity', decision='review'))
        state = self.store.report()['decisions'][0]
        self.assertEqual(state['implementation'], 'not_started')
        self.assertEqual(state['evaluation'], 'not_measured')

    def test_rules_version_without_mutating_evidence(self):
        self.store.scan()
        before = self.source.read_bytes()
        self.store.mutate('rule', dict(id='default-2', category='investigation', pattern='search'))
        report = self.store.report()
        self.assertEqual(report['categories'][0]['name'], 'investigation')
        self.assertEqual(next(r for r in report['rules'] if r['id'] == 'default-2')['version'], 2)
        self.assertEqual(self.source.read_bytes(), before)

    def test_pause_prevents_ingestion(self):
        self.store.mutate('collection', dict(enabled=False))
        self.store.scan()
        self.assertEqual(self.store.report()['event_count'], 0)

    def test_mcp_task_creation_and_bounded_queries(self):
        self.store.scan()
        response = analyst_mcp.handle(self.store, dict(method='initialize', params={'protocolVersion': '2025-06-18'}))
        self.assertEqual(response['protocolVersion'], '2025-06-18')
        self.assertEqual(len(analyst_mcp.handle(self.store, dict(method='tools/list'))['tools']), 8)
        result = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(name='query_activity', arguments={'section': 'summary'})))
        self.assertFalse(result['isError'])
        data = json.loads(result['content'][0]['text'])
        self.assertEqual(data['usage']['total_tokens'], 110)
        self.assertNotIn('events', data)
        invalid = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(name='query_activity', arguments={'sql': 'SELECT *'})))
        self.assertTrue(invalid['isError'])
        evidence = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(name='read_evidence', arguments={'id': 's:tool:tool'})))
        self.assertFalse(evidence['isError'])
        self.assertIn('CommandExecution', evidence['content'][0]['text'])

    def test_conflicting_usage_is_not_silently_overwritten(self):
        self.store.scan()
        changed = json.loads(json.dumps(self.rows))
        for row in changed:
            if row['type'] == 'token_usage_record' and row['payload'].get('thread_id') == 's':
                row['payload']['usage'].update(input_tokens=101, total_tokens=111)
        self.source.write_text(''.join(json.dumps(r) + '\n' for r in changed))
        self.store.scan()
        report = self.store.report()
        self.assertEqual(report['usage']['total_tokens'], 110)
        self.assertEqual(len(report['sources']['errors']), 1)

    def test_http_mutations_require_valid_host_and_origin(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        host = f'127.0.0.1:{server.server_port}'
        origin = 'http://' + host
        server.allowed_hosts = {host}
        server.allowed_origins = {origin}
        server.store = self.store
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        body = json.dumps(dict(name='Project', repo='/repo')).encode()
        request = urllib.request.Request(origin + '/api/project', data=body, headers={'Content-Type': 'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as failure:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(failure.exception.code, 403)
        failure.exception.close()
        request.add_header('Origin', origin)
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertTrue(json.load(response)['ok'])
        hostile = urllib.request.Request(origin + '/api/workspace', headers={'Host': 'attacker.invalid'})
        with self.assertRaises(urllib.error.HTTPError) as failure:
            urllib.request.urlopen(hostile, timeout=5)
        self.assertEqual(failure.exception.code, 403)
        failure.exception.close()

    def analysis_fixture(self, role='background_service_lifetime'):
        self.store.scan()
        report = self.store.report()
        evidence = dict(tools=[e for e in report['events'] if e['kind'] == 'tool'],
                        snapshot_at='2026-11-05T00:00:01Z', scope='Fixture only', usage=report['usage'])
        analysis = dict(summary='Fixture review', findings=[dict(title='Separate process lifetime', observation='Recorded process duration',
            evidence_ids=['s:tool:tool'], recommended_action='Keep lifetime separate', verification_plan='Check accounting', confidence='high')],
            annotations=[dict(event_id='s:tool:tool', category='service operation', runtime_role=role, rationale='Reviewed command evidence', confidence='high')],
            limitations=['No savings measured'])
        return evidence, analysis

    def test_agent_categories_preserve_measurements_and_separate_background_runtime(self):
        evidence, analysis = self.analysis_fixture()
        before = self.source.read_bytes()
        self.store.publish_analysis(analysis, evidence, dict(id='review-1', model='test', snapshot_hash='fixture'))
        report = self.store.report()
        event = next(e for e in report['events'] if e['kind'] == 'tool')
        self.assertEqual(event['category'], 'service operation')
        self.assertEqual(event['category_basis'], 'Codex agent interpretation')
        self.assertEqual(event['runtime'], 2)
        self.assertEqual(report['runtime_accounting']['background_runtime_seconds'], 2)
        self.assertEqual(report['runtime_accounting']['finite_runtime_seconds'], 0)
        self.assertEqual(report['usage']['total_tokens'], 110)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(report['agent_analyses'][0]['id'], 'review-1')

    def test_agent_report_rejects_invented_or_incomplete_evidence(self):
        evidence, analysis = self.analysis_fixture()
        analysis['annotations'] = []
        with self.assertRaises(ValueError):
            self.store.publish_analysis(analysis, evidence, dict(id='review-1', model='test', snapshot_hash='fixture'))
        evidence, analysis = self.analysis_fixture()
        analysis['findings'][0]['evidence_ids'] = ['invented']
        with self.assertRaises(ValueError):
            self.store.publish_analysis(analysis, evidence, dict(id='review-1', model='test', snapshot_hash='fixture'))

    def test_incremental_snapshot_does_not_repeat_reviewed_events(self):
        import agent_review
        evidence, analysis = self.analysis_fixture()
        self.store.publish_analysis(analysis, evidence, dict(id='review-1', model='test', snapshot_hash='fixture'))
        with self.assertRaisesRegex(ValueError, 'No unreviewed tool evidence'):
            agent_review.snapshot(self.store, self.root / 'incremental')
        snapshot = agent_review.snapshot(self.store, self.root / 'full', include_reviewed=True)
        self.assertEqual(len(snapshot['tools']), 1)
        self.assertEqual(snapshot['tools'][0]['id'], 's:tool:tool')

    def test_legacy_capture_links_by_session_time_without_claiming_a_response_body(self):
        self.store.scan()
        project, task = self.define_task()
        self.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
        captures = self.root / 'captures'
        captures.mkdir()
        self.store.capture_root = captures
        from workspace import bridge
        capture = dict(id='a'*32, path='/responses', state='complete', status=200,
            started_ns=bridge.nanos('2026-11-05T00:00:00Z'), ended_ns=bridge.nanos('2026-11-05T00:00:02Z'),
            request=dict(prompt_cache_key='s', model='test-model'), response=dict(unparsed_body=True, bytes=100),
            request_bytes=10, response_bytes=100, response_truncated=False)
        (captures / 'capture.json').write_text(json.dumps(capture))
        report = self.store.report(task=task, category='search')
        self.assertEqual(len(report['wire_captures']), 1)
        row = report['wire_captures'][0]
        self.assertEqual(row['correlation'], 'session + time (inferred)')
        self.assertFalse(row['response_body_available'])
        self.assertEqual(report['usage']['total_tokens'], 0)
        self.assertEqual(report['usage_scope']['all_sources']['total_tokens'], 110)

    def test_task_total_and_unassigned_total_are_explicit_subsets(self):
        self.store.scan()
        _, task = self.define_task()
        report = self.store.report(task=task)
        self.assertEqual(report['usage']['total_tokens'], 0)
        self.assertEqual(report['usage_scope']['all_sources']['total_tokens'], 110)
        self.assertEqual(report['usage_scope']['unassigned']['total_tokens'], 110)

    def test_reconciliation_includes_first_response_at_time_boundary(self):
        self.store.scan()
        self.store.capture_root = self.root / 'stack/captures'
        self.store.capture_root.mkdir(parents=True)
        (self.store.capture_root.parent / 'local-access.json').write_text(json.dumps(dict(base_url='http://localhost:3000', public_key='fixture', secret_key='fixture')))
        response = MagicMock()
        response.read.return_value = b'{"data":[{"sum_totalTokens":110}]}'
        with patch('workspace.urllib.request.urlopen') as opener:
            opener.return_value.__enter__.return_value = response
            result = self.store.reconcile()
            query = json.loads(urllib.parse.parse_qs(urllib.parse.urlparse(opener.call_args.args[0].full_url).query)['query'][0])
        self.assertLess(query['fromTimestamp'], '2026-11-05T00:00:01Z')
        self.assertEqual(result['difference'], 0)
        self.assertEqual(result['status'], 'matched')


if __name__ == '__main__':
    unittest.main()
