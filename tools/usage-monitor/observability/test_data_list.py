"""Shared-list architecture and full-scope metadata retrieval contracts."""
from pathlib import Path
import unittest
import test_workspace_browser
import test_work_analytics
import work_analytics
import task_history


class DataListContracts(unittest.TestCase):
    def test_pages_delegate_table_markup_and_controls_to_one_component(self):
        root=Path(__file__).resolve().parent
        owners=[p.name for p in root.glob('*.js') if '<table' in p.read_text()]
        self.assertEqual(owners,['data-list.js'])
        shell=(root/'workspace.js').read_text()
        self.assertNotIn('function table(',shell)
        self.assertNotIn('function refreshTable(',shell)
        self.assertIn("from '/data-list.js'",shell)

    def test_all_mode_keeps_existing_numeric_limits_and_analysis_bound(self):
        self.assertEqual(task_history.page('all',0),(10000,0))
        self.assertEqual(task_history.page(100,0),(100,0))
        with self.assertRaises(ValueError):task_history.page(101,0)
        with self.assertRaises(ValueError):task_history.page('all',1)

    def test_work_metadata_all_mode_includes_rows_beyond_old_first_batch(self):
        fixture=test_work_analytics.WorkAnalyticsTests();fixture.setUp();self.addCleanup(fixture.fixture.tmp.cleanup)
        store=fixture.store
        with store.connection() as c:
            project=c.execute('SELECT project_id FROM tasks WHERE id=?',(fixture.task,)).fetchone()[0]
            for i in range(125):c.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)',('additional-'+str(i),project,'Task '+str(i),'Goal','','active','2026-11-12','2026-11-12',None))
        result=work_analytics.overview(store,limit='all')
        self.assertEqual(len(result['tasks']),126);self.assertIsNone(result['next_offset'])
        self.assertEqual(len(work_analytics.overview(store,limit=100)['tasks']),100)

    def test_source_metadata_all_mode_keeps_all_records_for_list_sorting(self):
        fixture=test_work_analytics.WorkAnalyticsTests();fixture.setUp();self.addCleanup(fixture.fixture.tmp.cleanup)
        with fixture.store.connection() as c:
            for i in range(125):c.execute('INSERT INTO events(id,session_id,turn_id,kind,name,ts) VALUES(?,?,?,?,?,?)',('more-'+str(i),'session','turn','tool','Operation '+str(i),'2026-11-12T01:00:04Z'))
        result=work_analytics.source_steps(fixture.store,fixture.task,limit='all')
        self.assertEqual(len(result['items']),result['total']);self.assertGreater(result['total'],100)
        self.assertIsNone(result['next_offset'])


if __name__=='__main__':unittest.main()
