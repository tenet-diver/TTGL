"""Finite queue semantics using fixture model outputs, never real model calls."""
import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import bulk_analysis as bulk
import task_history as history
import test_process_analysis
from workspace import Handler


class BulkAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.f=test_process_analysis.ProcessAnalysisTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.store=self.f.store

    def complete(self,store,job_id):
        with store.connection() as c:body=json.loads(c.execute('SELECT snapshot FROM task_history_jobs WHERE id=?',(job_id,)).fetchone()[0])
        history.publish(store,job_id,self.f.result(body),{'total_tokens':123})

    def test_start_freezes_once_and_worker_publishes_progress_and_usage(self):
        first=bulk.start(self.store,launch=False)
        second=bulk.start(self.store,launch=False)
        self.assertEqual(first['batch']['id'],second['batch']['id'])
        self.assertEqual(first['total'],1)
        self.assertEqual(first['coverage']['frozen_events'],2)
        with patch.object(history,'run_model',side_effect=self.complete) as run:
            bulk.worker(self.store,first['batch']['id'])
        self.assertEqual(run.call_count,1)
        done=bulk.state(self.store)
        self.assertEqual(done['batch']['status'],'completed')
        self.assertEqual(done['counts'],{'completed':1})
        self.assertEqual(done['coverage']['interpreted_events'],2)
        self.assertEqual(done['coverage']['known_analysis_tokens'],123)
        reused=bulk.start(self.store,launch=False)
        self.assertEqual(reused['counts'],{'unchanged':1})
        self.assertEqual(reused['coverage']['known_analysis_tokens'],0)

    def test_failed_attempt_is_retained_without_automatic_retry_or_zero_usage(self):
        first=bulk.start(self.store,launch=False)
        def fail(store,job_id):
            with store.connection() as c:c.execute("UPDATE task_history_jobs SET status='failed',error='Fixture model transport failed' WHERE id=?",(job_id,))
        with patch.object(history,'run_model',side_effect=fail) as run:bulk.worker(self.store,first['batch']['id'])
        self.assertEqual(run.call_count,1)
        done=bulk.state(self.store)
        self.assertEqual(done['batch']['status'],'completed_with_errors')
        self.assertEqual(done['coverage']['jobs_missing_usage'],1)
        next_batch=bulk.start(self.store,launch=False)
        self.assertEqual(next_batch['counts'],{'previous_failed':1})

    def test_uncertain_worker_state_is_not_replayed(self):
        batch=bulk.start(self.store,launch=False)
        with self.store.connection() as c:c.execute("UPDATE bulk_analysis_items SET status='dispatching' WHERE batch_id=?",(batch['batch']['id'],))
        with patch.object(history,'run_model') as run:bulk.worker(self.store,batch['batch']['id'])
        run.assert_not_called()
        self.assertEqual(bulk.state(self.store)['batch']['status'],'stopped')

    def test_stop_prevents_dispatch_and_paging_is_bounded(self):
        batch=bulk.start(self.store,launch=False)
        bulk.stop(self.store,batch['batch']['id'])
        with patch.object(history,'run_model') as run:bulk.worker(self.store,batch['batch']['id'])
        run.assert_not_called()
        self.assertEqual(bulk.state(self.store)['batch']['status'],'stopped')
        with self.assertRaises(ValueError):bulk.state(self.store,limit=101)

    def test_http_start_and_progress_are_explicit_and_do_not_duplicate_workers(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=self.store
        host=f'127.0.0.1:{server.server_port}';origin='http://'+host
        server.allowed_hosts={host};server.allowed_origins={origin}
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        with patch.object(bulk.subprocess,'Popen') as launch:
            launch.return_value.pid=12345
            for _ in range(2):
                request=urllib.request.Request(origin+'/api/bulk-analysis',json.dumps({'action':'start'}).encode(),{'Origin':origin,'Content-Type':'application/json'})
                with urllib.request.urlopen(request) as response:self.assertEqual(json.load(response)['total'],1)
            with urllib.request.urlopen(origin+'/api/bulk-analysis?limit=1') as response:self.assertEqual(len(json.load(response)['records']),1)
            self.assertEqual(launch.call_count,1)
        self.assertTrue((self.store.data/'bulk-analysis').is_dir())


if __name__=='__main__':unittest.main()
