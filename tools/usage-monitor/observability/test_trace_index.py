"""Native cohort accounting, uncertainty, query boundaries and source drill-down."""
import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import analyst_mcp
import test_workspace
import trace_index
from workspace import Handler


class TraceIndexTests(unittest.TestCase):
    def setUp(self):
        self.f = test_workspace.WorkspaceTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.store = self.f.store
        self.store.scan()
        self.project, self.task = self.f.define_task()
        self.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=self.task))
        with self.store.connection() as c:
            self.tool = c.execute("SELECT name FROM events WHERE kind='tool'").fetchone()[0]

    def clone(self, ident='again', session='s', turn='t', failed=1, runtime=3, output_hash='b'*64):
        with self.store.connection() as c:
            row = dict(c.execute("SELECT * FROM events WHERE kind='tool' LIMIT 1").fetchone())
            row.update(id=ident, session_id=session, turn_id=turn, failed=failed, runtime=runtime, output_hash=output_hash)
            c.execute('INSERT INTO events VALUES(' + ','.join('?'*len(row)) + ')', list(row.values()))
            c.execute('INSERT INTO optimization_facts(event_id,signature) VALUES(?,?)', (ident, 'a'*64))
        return ident

    def test_inventory_reconciles_native_counters_and_preserves_unknowns(self):
        # Repeated native usage/imports must not create another measured response.
        self.store.ingest(self.f.source)
        self.clone(failed=None, runtime=None)
        with patch.object(self.store, 'scan', side_effect=AssertionError('Queries cannot scan')):
            data = trace_index.query(self.store)
        m = data['metrics']
        self.assertEqual((m['events'], m['turns'], m['tasks'], m['sessions']), (3, 1, 1, 1))
        self.assertEqual((m['total_tokens'], m['input_tokens'], m['cached_input_tokens'], m['output_tokens']), (110,100,80,10))
        self.assertEqual((m['tool_calls'], m['known_tool_outcomes'], m['unknown_tool_outcomes'], m['tool_failures']), (2,1,1,0))
        self.assertEqual((m['timed_tools'], m['recorded_tool_runtime_seconds']), (1,2))
        self.assertEqual(data['facets']['models']['records'][0]['count'], 1)
        empty = trace_index.query(self.store, session='missing')['metrics']
        self.assertIsNone(empty['total_tokens'])
        self.assertIsNone(empty['recorded_tool_runtime_seconds'])
        self.assertEqual(empty['turns'], 0)

    def test_tool_and_model_filters_select_complete_turns(self):
        self.clone()
        for args in (dict(tool=self.tool), dict(model='test-model'), dict(signal='tool_failure')):
            result = trace_index.query(self.store, view='turns', **args)
            self.assertEqual(result['pagination']['total'], 1)
            self.assertEqual((result['metrics']['tool_calls'],result['metrics']['total_tokens']), (2,110))
            self.assertEqual(result['records'][0]['tool_failures'],1)
        result=trace_index.query(self.store,view='steps',model='test-model',kind='tool')
        self.assertEqual(len(result['records']),2)
        self.assertEqual(result['metrics']['total_tokens'],110)

    def test_scope_intersections_timezones_and_literal_search(self):
        matched = dict(project=self.project,task=self.task,session='s',turn='t',status='active',
                       since='2026-11-04T23:00:00-01:00',until='2026-11-05T01:00:00Z')
        self.assertEqual(trace_index.query(self.store, **matched)['metrics']['turns'],1)
        for args in (dict(project='other'),dict(turn='other'),dict(status='completed'),
                     dict(since='2026-11-05T00:00:02Z'),dict(until='2026-11-05T00:00:01Z'),
                     dict(query='%'),dict(query="' OR 1=1 --")):
            self.assertEqual(trace_index.query(self.store, **args)['metrics']['turns'],0,args)
        self.assertEqual(trace_index.query(self.store,query='Resolve failure')['metrics']['turns'],1)

    def test_completed_marker_is_not_a_verified_task_outcome(self):
        result=trace_index.query(self.store,view='turns')
        row=result['records'][0]
        self.assertEqual(row['native_completion_marker'],1)
        self.assertEqual(row['task_status'],'active')
        self.assertNotIn('prompt',row)
        self.assertNotIn('task_outcome',row)
        self.assertIn('prompt',trace_index.query(self.store,view='turns',detail='full')['records'][0])
        self.assertEqual(trace_index.query(self.store,signal='unassigned')['metrics']['turns'],0)

    def test_repeated_patterns_are_scoped_and_can_retrieve_all_matching_steps(self):
        with self.store.connection() as c:
            c.execute("UPDATE optimization_facts SET signature=?",('a'*64,))
            c.execute("UPDATE events SET output_hash=? WHERE kind='tool'",('b'*64,))
        self.clone()
        self.clone('third', failed=None)
        for pattern,fingerprint in (('input','a'*64),('output','b'*64)):
            result=trace_index.query(self.store,view='patterns',pattern=pattern)
            self.assertEqual(result['pagination']['total'],1)
            row=result['records'][0]
            self.assertEqual((row['copies'],row['tool_failures']), (3,1))
            steps=trace_index.query(self.store,view='steps',session=row['session_id'],turn=row['turn_id'],pattern=pattern,fingerprint=fingerprint,kind='tool')
            self.assertEqual(steps['pagination']['total'],3)
            self.assertEqual(steps['metrics']['total_tokens'],110)
        self.assertEqual(trace_index.query(self.store,signal='repeated_input')['metrics']['turns'],1)
        with self.store.connection() as c:
            c.execute("INSERT INTO turns VALUES('other','t','/repo','','2026-11-05T00:00:01Z','2026-11-05T00:00:01Z',0)")
        self.clone('foreign',session='other')
        self.assertEqual(trace_index.query(self.store,view='patterns')['pagination']['total'],1)
        self.assertEqual(trace_index.query(self.store,signal='unassigned')['metrics']['turns'],1)

    def test_stable_paging_and_null_metering(self):
        self.clone()
        for view in ('steps','tools','turns','patterns'):
            first=trace_index.query(self.store,view=view,limit=1)
            second=trace_index.query(self.store,view=view,offset=1,limit=1)
            self.assertEqual(first['metrics'],second['metrics'])
            if first['pagination']['next_offset'] is not None:
                self.assertNotEqual(first['records'],second['records'])
        with self.store.connection() as c:
            c.execute("UPDATE events SET usage=NULL WHERE kind='generation'")
        result=trace_index.query(self.store)
        self.assertIsNone(result['metrics']['total_tokens'])
        self.assertEqual(result['metrics']['unmetered_responses'],1)

    def test_invalid_filters_are_rejected(self):
        for args in (dict(view='sql'),dict(sql='SELECT 1'),dict(limit=101),dict(offset=-1),
                     dict(kind='tool'),dict(signal='failed_task'),dict(since='2026-11-05'),
                     dict(since='2026-11-06T00:00:00Z',until='2026-11-05T00:00:00Z'),
                     dict(view='steps',fingerprint='bad'),dict(query='x'*501),dict(view='steps',kind='any')):
            with self.assertRaises((ValueError,TypeError),msg=str(args)):
                trace_index.query(self.store,**args)

    def test_mcp_uses_shared_query_and_is_read_only(self):
        definition=next(t for t in analyst_mcp.TOOLS if t['name']=='query_trace_index')
        self.assertTrue(definition['annotations']['readOnlyHint'])
        args=dict(view='steps',kind='generation',limit=1)
        response=analyst_mcp.handle(self.store,dict(method='tools/call',params=dict(name='query_trace_index',arguments=args)))
        self.assertFalse(response['isError'])
        self.assertEqual(json.loads(response['content'][0]['text']),trace_index.query(self.store,**args))

    def test_raw_evidence_uses_indexed_session_source_only(self):
        unrelated=self.f.source.with_name('unrelated.jsonl')
        unrelated.write_text(self.f.source.read_text().replace('"s"','"different-session"'))
        self.store.ingest(unrelated)
        paths=[]
        original=analyst_mcp.bridge.monitor.lines
        def observe(path):
            paths.append(path)
            return original(path)
        with patch.object(analyst_mcp.bridge.monitor,'lines',side_effect=observe):
            result=analyst_mcp.handle(self.store,dict(method='tools/call',params=dict(name='read_evidence',arguments=dict(id='s:tool:tool',limit=20))))
        self.assertFalse(result['isError'])
        self.assertEqual(paths,[self.f.source])
        data=json.loads(result['content'][0]['text'])
        self.assertEqual(data['next_offset'],20)

    def test_http_supports_same_queries_and_paged_original_evidence(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        server.store=self.store
        host=f'127.0.0.1:{server.server_port}'
        server.allowed_hosts={host}
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        origin='http://'+host
        with urllib.request.urlopen(origin+'/api/trace-index?view=steps&kind=tool&limit=1') as response:
            data=json.load(response)
        self.assertEqual(data['pagination']['total'],1)
        with urllib.request.urlopen(origin+'/api/task-step-evidence?'+urllib.parse.urlencode(dict(id='s:tool:tool',offset=5,limit=20))) as response:
            data=json.loads(json.load(response)['content'][0]['text'])
        self.assertEqual((data['offset'],len(data['evidence'])),(5,20))
        for path in ('/investigate','/trace-explorer.js','/trace-explorer.css'):
            with urllib.request.urlopen(origin+path) as response:
                self.assertEqual(response.status,200)
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(origin+'/api/trace-index?sql=SELECT')
        self.assertEqual(raised.exception.code,400)
        raised.exception.close()

    def test_raw_reader_rejects_stale_line_identity_and_changed_output(self):
        original=self.f.source.read_text()
        # The indexed line now points at a different native item: no wrong record is returned.
        self.f.source.write_text(original.replace('"id": "tool"','"id": "different-item"'))
        request=dict(method='tools/call',params=dict(name='read_evidence',arguments=dict(id='s:tool:tool')))
        self.assertTrue(analyst_mcp.handle(self.store,request)['isError'])
        # The same item ID with different persisted output also fails its retained hash.
        rows=[json.loads(line) for line in original.splitlines()]
        for row in rows:
            item=row.get('payload',{}).get('item',{})
            if item.get('id')=='tool':item['aggregated_output']='Changed after indexing'
        self.f.source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        self.assertTrue(analyst_mcp.handle(self.store,request)['isError'])


if __name__ == '__main__':
    unittest.main()
