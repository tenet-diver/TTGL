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
        self.assertEqual(len(analyst_mcp.handle(self.store, dict(method='tools/list'))['tools']), 20)
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

    def test_turn_queries_page_and_keep_prompts_opt_in(self):
        self.store.scan()
        def query(**args):
            response = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(name='query_activity', arguments=dict(section='turns', **args))))
            self.assertFalse(response['isError'])
            return json.loads(response['content'][0]['text'])
        compact = query(limit='1')
        self.assertEqual(len(compact['turns']), 1)
        self.assertNotIn('prompt', compact['turns'][0])
        full = query(limit='1', detail='full')
        self.assertIn('prompt', full['turns'][0])
        self.assertEqual(full['turns'][0]['session_id'], compact['turns'][0]['session_id'])
        self.assertEqual(query(offset='100', limit='1')['turns'], [])

    def test_session_query_refreshes_and_intersects_scope_without_duplicate_usage(self):
        def query(**args):
            response = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(name='query_activity', arguments=args)))
            self.assertFalse(response['isError'])
            return json.loads(response['content'][0]['text'])
        self.assertEqual(query(section='events', session='s')['events'], [])
        refreshed = query(section='summary', session='s', refresh='true')
        self.assertEqual(refreshed['usage']['total_tokens'], 110)
        self.assertEqual(refreshed['usage_scope']['session_id'], 's')
        self.assertEqual(query(section='summary', session='s', refresh='true')['usage']['total_tokens'], 110)
        self.assertEqual(query(section='summary', session='missing')['usage']['total_tokens'], 0)
        self.assertEqual(query(section='turns', session='missing')['turns'], [])
        project, task = self.define_task()
        self.assertEqual(query(section='summary', session='s', project=project)['usage']['total_tokens'], 0)
        self.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
        self.assertEqual(query(section='summary', session='s', project=project)['usage']['total_tokens'], 110)
        self.store.mutate('collection', dict(enabled=False))
        other = [dict(r) for r in self.rows]
        other[0] = dict(other[0], payload=dict(other[0]['payload'], id='new'))
        (self.source.parent/'new.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in other))
        self.assertEqual(query(section='turns', session='new', refresh='true')['turns'], [])

    def test_session_task_discovery_is_compact_isolated_and_full_retrievable(self):
        second = json.loads(json.dumps(self.rows).replace('"s"', '"second"'))
        (self.source.parent/'second.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in second))
        self.store.scan()
        project, task = self.define_task()
        other = self.store.mutate('task', dict(project_id=project, title='Other', goal='Other', acceptance='Other'))['id']
        self.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
        self.store.mutate('assign', dict(session_id='second', turn_id='t', task_id=other))
        def query(**args):
            response = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(name='query_activity', arguments=args)))
            self.assertFalse(response['isError'])
            return json.loads(response['content'][0]['text'])
        compact = query(section='tasks', session='s', limit='1')
        self.assertEqual([t['id'] for t in compact['tasks']], [task])
        self.assertNotIn('acceptance', compact['tasks'][0])
        full = query(section='tasks', session='s', detail='full')
        self.assertEqual(full['tasks'][0]['acceptance'], 'Checks pass')
        events = query(section='events', session='second')['events']
        self.assertEqual({e['session_id'] for e in events}, {'second'})
        self.assertEqual(query(section='summary', session='second')['usage']['total_tokens'], 110)
        self.assertEqual(query(section='summary')['usage']['total_tokens'], 220)
        absent = query(section='turns', session='absent')
        self.assertEqual(absent['session_coverage']['indexed_turns'], 0)
        self.assertIn('do not establish zero inference', absent['session_coverage']['note'])
        self.assertEqual(len(query(section='tasks', detail='full')['tasks']), 2)

    def test_pagination_accepts_native_integer_arguments_but_rejects_booleans(self):
        self.store.scan()
        def call(args):
            return analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(name='query_activity', arguments=args)))
        numeric = call(dict(section='turns', limit=1, offset=0))
        text = call(dict(section='turns', limit='1', offset='0'))
        self.assertFalse(numeric['isError'])
        self.assertEqual(numeric, text)
        self.assertTrue(call(dict(section='turns', limit=True))['isError'])
        self.assertTrue(call(dict(section='turns', limit=1.5))['isError'])
        self.assertTrue(call(dict(section='turns', limit=0))['isError'])

    def test_evidence_pages_reconstruct_the_retained_record(self):
        self.store.scan()
        chunks, offset, total = [], 0, None
        while True:
            response = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(
                name='read_evidence', arguments=dict(id='s:tool:tool', offset=str(offset), limit='16000'))))
            self.assertFalse(response['isError'])
            result = json.loads(response['content'][0]['text'])
            chunks.append(result['evidence'])
            total = result['total_characters']
            if result['next_offset'] is None:
                break
            offset = result['next_offset']
        evidence = ''.join(chunks)
        self.assertEqual(len(evidence), total)
        self.assertEqual(json.loads(evidence)['aggregated_output'], 'x' * 40000)

    def test_pagination_reaches_events_older_than_ui_window(self):
        self.store.scan()
        with self.store.connection() as connection:
            template = dict(connection.execute("SELECT * FROM events WHERE kind='tool'").fetchone())
            for index in range(1100):
                row = {**template, 'id': 'extra'+str(index), 'bytes': index}
                connection.execute('INSERT INTO events VALUES('+','.join('?' for _ in row)+')', tuple(row.values()))
        response = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(name='query_activity',
            arguments=dict(section='events', kind='tool', sort='bytes', offset='1000', limit='100'))))
        result = json.loads(response['content'][0]['text'])
        self.assertEqual(len(result['events']), 100)
        self.assertEqual(result['pagination']['matched_in_window'], 1101)
        self.assertEqual(result['pagination']['next_offset'], 1100)

    def test_experiment_freezes_evidence_and_rejects_incomplete_proposals(self):
        from analyst_experiments import plan_experiment, list_experiments
        self.store.scan()
        _, task = self.define_task()
        self.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
        values = dict(task_id=task, title='Compact progress', change='Progress lines only',
                      metrics='Matched full-task tokens', quality_gate='All acceptance checks pass',
                      overhead='Include analyst inference', rollback='Restore original output on regression')
        with self.assertRaises(ValueError):
            plan_experiment(self.store, {**values, 'quality_gate': ''})
        proposal = plan_experiment(self.store, values)
        with self.store.connection() as connection:
            connection.execute('DELETE FROM assignments')
            connection.execute("UPDATE events SET bytes=1 WHERE kind='tool'")
        frozen = list_experiments(self.store)[0]
        self.assertEqual(frozen['baseline']['usage']['total_tokens'], 110)
        self.assertEqual(frozen['baseline']['event_count'], 2)
        self.assertEqual(frozen['baseline_sha256'], proposal['baseline_sha256'])
        self.assertTrue(any(r['bytes'] == 40000 for r in frozen['baseline']['events']))
        self.assertIsNone(frozen['baseline']['cash_cost'])
        self.assertEqual(list_experiments(self.store, project='unrelated'), [])

    def test_compact_evidence_keeps_original_access_and_coverage(self):
        original = ' abcdef012345 Downloading 12B\nError: disk quota\n... command output truncated for persistence ...\n'
        self.rows[4]['payload']['item']['aggregated_output'] = original
        self.source.write_text(''.join(json.dumps(r) + '\n' for r in self.rows))
        before = self.source.read_bytes()
        self.store.scan()
        def read(view):
            response = analyst_mcp.handle(self.store, dict(method='tools/call', params=dict(
                name='read_evidence', arguments=dict(id='s:tool:tool', view=view))))
            self.assertFalse(response['isError'])
            return json.loads(response['content'][0]['text'])
        result = read('pull_progress')
        self.assertTrue(result['retention']['incomplete'])
        self.assertEqual(result['presentation']['removed_lines'], 1)
        self.assertIn('Error: disk quota', result['evidence'])
        self.assertNotIn('Downloading 12B', result['evidence'])
        self.assertEqual(json.loads(read('raw')['evidence'])['aggregated_output'], original)
        self.assertEqual(self.source.read_bytes(), before)

    def test_trial_measurements_are_immutable_and_keep_requires_gate(self):
        from analyst_experiments import plan_experiment, record_evaluation, review_experiment, list_experiments
        self.store.scan()
        _, task = self.define_task()
        self.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
        proposal = plan_experiment(self.store, dict(task_id=task, title='Trial', change='One change',
            metrics='Total tokens', quality_gate='All checks', overhead='Count it', rollback='Restore'))
        evaluation = record_evaluation(self.store, proposal['id'], dict(id='trial'),
            dict(acceptance_passed=False, raw_total_tokens=100, compact_total_tokens=50), 'a'*64)
        with self.assertRaises(ValueError):
            review_experiment(self.store, dict(evaluation_id=evaluation, verdict='keep', notes='Looks cheap'))
        review_experiment(self.store, dict(evaluation_id=evaluation, verdict='inconclusive', notes='Quality failed'))
        result = list_experiments(self.store)[0]
        self.assertFalse(result['evaluations'][0]['measurements']['acceptance_passed'])
        self.assertEqual(result['evaluations'][0]['reviews'][0]['verdict'], 'inconclusive')

    def test_compact_experiment_discovery_keeps_full_measurements_available(self):
        from analyst_experiments import plan_experiment
        self.store.scan();_, task=self.define_task()
        self.store.mutate('assign',dict(session_id='s',turn_id='t',task_id=task))
        proposal=plan_experiment(self.store,dict(task_id=task,title='Trial',change='One change',metrics='Native tokens',
            quality_gate='Checks',overhead='Count it',rollback='Restore'))
        def query(detail):
            response=analyst_mcp.handle(self.store,dict(method='tools/call',params=dict(name='query_activity',arguments=dict(section='experiments',detail=detail))))
            self.assertFalse(response['isError'])
            return json.loads(response['content'][0]['text'])['experiments'][0]
        summary=query('summary');full=query('full')
        self.assertEqual(summary['id'],proposal['id'])
        self.assertNotIn('baseline',summary)
        self.assertEqual(full['baseline']['usage']['total_tokens'],110)

    def test_raw_compression_retrieval_validates_hash_and_is_bounded(self):
        import hashlib
        self.store.capture_root=self.root/'captures'
        directory=self.store.capture_root/'compression_sources';directory.mkdir(parents=True)
        text='retained text'*1000;digest=hashlib.sha256(text.encode()).hexdigest()
        (directory/(digest+'.json')).write_text(json.dumps(dict(content=text,retained_sha256=digest,retention='test')))
        result=analyst_mcp.handle(self.store,dict(method='tools/call',params=dict(name='read_compression_source',arguments=dict(sha256=digest,limit='100'))))
        data=json.loads(result['content'][0]['text'])
        self.assertTrue(data['TTGL_RAW_EVIDENCE'])
        self.assertEqual(len(data['content']),100)
        self.assertEqual(data['next_offset'],100)
        invalid=analyst_mcp.handle(self.store,dict(method='tools/call',params=dict(name='read_compression_source',arguments=dict(sha256='../escape'))))
        self.assertTrue(invalid['isError'])

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
