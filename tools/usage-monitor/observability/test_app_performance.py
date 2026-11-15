"""Bounded transport and expensive-work regressions over real fixture projections."""
import gzip
import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import dashboard_views
import test_workspace
import usage_views
from workspace import Handler


class AppPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.f=test_workspace.WorkspaceTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.store=self.f.store;self.store.scan()
        project,self.task=self.f.define_task()
        self.store.mutate('assign',dict(session_id='s',turn_id='t',task_id=self.task))

    def test_compound_scripts_are_not_fully_shell_tokenized(self):
        with patch.object(usage_views.shlex,'split',side_effect=AssertionError('No expensive shell tokenization')):
            self.assertEqual(usage_views.shell_action('python3 - <<\'PY\'\n'+('long_script_body = 1\n'*10000)), 'Compound shell')

    def test_dashboard_pages_preserve_totals_and_fetch_prompts_separately(self):
        with self.store.connection() as c:
            c.execute('UPDATE turns SET prompt=?',('Large retained request '*500,))
            for i in range(4):
                c.execute('INSERT INTO turns VALUES(?,?,?,?,?,?,?)',('s',f'page-{i}','/repo','Another request '*1000,'2026-11-05T00:00:02Z','2026-11-05T00:00:03Z',1))
                c.execute('INSERT INTO assignments VALUES(?,?,?)',('s',f'page-{i}',self.task))
        full=dashboard_views.report(self.store,'taskactivity',range='all')
        first=dashboard_views.page(self.store,'taskactivity',range='all',limit=2)
        second=dashboard_views.page(self.store,'taskactivity',range='all',limit=2,turn_offset=2)
        self.assertEqual(first['metrics'],full['metrics'])
        self.assertEqual(first['counts']['turns'],5)
        self.assertEqual(first['turn_pagination'],dict(total=5,offset=0,limit=2,next_offset=2))
        self.assertEqual(len(first['turns']),2)
        self.assertFalse({t['id'] for t in first['turns']}&{t['id'] for t in second['turns']})
        self.assertTrue(all('prompt' not in t for t in first['turns']))
        self.assertTrue(dashboard_views.turn_prompt(self.store,'s','t')['prompt'].startswith('Large retained'))
        overview=dashboard_views.page(self.store,'overview',range='all')
        self.assertEqual(overview['turns'],[])
        self.assertNotIn('turn_keys',overview['days'][0])
        day=dashboard_views.page(self.store,'taskactivity',range='all',day='2026-11-05',limit=2)
        self.assertEqual(day['turn_pagination']['total'],1)
        self.assertEqual(day['turns'][0]['turn_id'],'t')

    def test_dashboard_queries_filter_before_paging_without_changing_measurements(self):
        with self.store.connection() as c:
            for i in range(12):
                c.execute('INSERT INTO turns VALUES(?,?,?,?,?,?,?)',('s',f'query-{i}','/repo',f'Unique repair {i:02}','2026-11-05T00:00:02Z','2026-11-05T00:00:03Z',1))
        baseline=dashboard_views.page(self.store,'taskactivity',range='all',limit=2)
        result=dashboard_views.page(self.store,'taskactivity',range='all',limit=2,turn_offset=100,turn_query=json.dumps(dict(search='Unique repair',sort='title',direction=-1)))
        self.assertEqual(result['metrics'],baseline['metrics'])
        self.assertEqual(result['turn_pagination']['total'],12)
        self.assertEqual(result['turn_pagination']['offset'],10)
        self.assertEqual([r['title'] for r in result['turns']],['Unique repair 01','Unique repair 00'])
        hidden=dashboard_views.page(self.store,'taskactivity',range='all',limit=2,turn_query=json.dumps(dict(search='repair /repo',filters={'responses':'= 0'})))
        self.assertEqual(hidden['turn_pagination']['total'],12)
        self.assertEqual(len(hidden['turns']),2)

    def test_http_compression_preserves_json_and_paging_validation(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=self.store
        host=f'127.0.0.1:{server.server_port}';server.allowed_hosts={host}
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        url='http://'+host+'/workspace.js'
        with urllib.request.urlopen(url) as response:original=response.read()
        request=urllib.request.Request(url,headers={'Accept-Encoding':'gzip'})
        with urllib.request.urlopen(request) as response:
            compressed=response.read();self.assertEqual(response.headers['Content-Encoding'],'gzip')
            self.assertEqual(int(response.headers['Content-Length']),len(compressed))
        self.assertEqual(gzip.decompress(compressed),original)
        self.assertLess(len(compressed),len(original)/2)
        with self.assertRaises(ValueError):dashboard_views.page(self.store,'overview',limit=101)
        with self.assertRaises(ValueError):dashboard_views.turn_prompt(self.store,'s','unknown')


if __name__=='__main__':unittest.main()
