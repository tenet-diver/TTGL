"""Native discovery preserves assignments, source counters and collection permission."""
import json
import unittest
import os
from pathlib import Path
import subprocess
import sys
import task_discovery as d
import work_analytics as w
import test_workspace

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.f=test_workspace.WorkspaceTests();self.f.setUp();self.addCleanup(self.f.directory.cleanup)
        self.store=self.f.store;self.store.scan()

    def test_opt_in_idempotent_discovery_and_live_turn_updates(self):
        self.assertFalse(d.enabled(self.store))
        first=d.configure(self.store,True);self.assertEqual(first['created'],1);self.assertEqual(first['assigned'],1)
        second=d.sync(self.store);self.assertEqual(second['created'],0);self.assertEqual(second['assigned'],0)
        with self.store.connection() as c:
            task=c.execute('SELECT task_id FROM task_discovery_tasks').fetchone()[0]
            self.assertEqual(c.execute('SELECT title FROM tasks WHERE id=?',(task,)).fetchone()[0],'Fix the problem')
            c.execute("INSERT INTO turns VALUES('s','followup','/repo','Check the result','2026-11-06','2026-11-06',1)")
            c.execute("INSERT INTO events(id,session_id,turn_id,kind,name,ts,usage,model) VALUES('r2','s','followup','generation','Response','2026-11-06',?,'gpt-6.1-sol')",(json.dumps(dict(input_tokens=20,cached_input_tokens=0,output_tokens=5,total_tokens=25)),))
        self.assertEqual(d.sync(self.store)['assigned'],1)
        overview=w.overview(self.store);self.assertEqual(overview['total'],1)
        detail=w.task_data(self.store,task)
        self.assertEqual(detail['metrics']['tokens'],135);self.assertEqual(detail['metrics']['steps'],1)
        self.assertEqual(len(detail['subtasks']),2)
        self.assertEqual(sum(s['metrics']['tokens'] for s in detail['subtasks']),135)
        self.assertEqual(detail['unattributed_tokens'],0)
        records=w.source_steps(self.store,task,detail['subtasks'][-1]['id'])
        self.assertEqual(records['total'],1);self.assertEqual(records['items'][0]['tokens'],25)
        self.assertIsNotNone(records['items'][0]['cost'])

    def test_manual_assignments_and_paused_collection_are_preserved(self):
        project,task=self.f.define_task();self.store.mutate('assign',dict(session_id='s',turn_id='t',task_id=task))
        self.assertEqual(d.configure(self.store,True)['assigned'],0)
        with self.store.connection() as c:self.assertEqual(c.execute('SELECT task_id FROM assignments').fetchone()[0],task)
        self.store.mutate('collection',dict(enabled=False));self.assertTrue(d.sync(self.store)['paused'])
        self.assertEqual(d.configure(self.store,False)['enabled'],False)

    def test_analyzer_source_loading_in_a_clean_server_process(self):
        code="""from pathlib import Path
import tempfile
from workspace import Store
import task_history
with tempfile.TemporaryDirectory() as root:
    store=Store(Path(root)/'data',Path(root)/'logs','http://localhost:3000')
    assert task_history.overview_evidence(store,{'steps':[]})['steps']=={}
"""
        subprocess.run([sys.executable,'-c',code],cwd=self.f.root,env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parent)},check=True,capture_output=True,timeout=20)

    def test_published_rates_long_context_and_custom_scenario(self):
        scenario=w.rates(self.store)
        self.assertEqual(scenario['as_of'],'2026-11-12');self.assertIn('Not an invoice',scenario['basis'])
        short=dict(input_tokens=100,cached_input_tokens=20,output_tokens=10)
        self.assertAlmostEqual(w.cost(short,'gpt-6.1-sol',scenario),.000262)
        long=dict(input_tokens=300000,cached_input_tokens=100000,output_tokens=1000)
        self.assertAlmostEqual(w.cost(long,'gpt-6.1-sol',scenario),.835)
        self.assertIsNone(w.cost(short,'unpriced-model',scenario))
        custom=dict(unit='credits',as_of='2026-11-12',models={})
        w.save_rates(self.store,custom);self.assertEqual(w.rates(self.store),custom)

if __name__=='__main__':unittest.main()
