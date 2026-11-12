import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from unittest.mock import patch

from workspace import Store
import task_history as h
import analyst_mcp

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.store=Store(self.root/'data',self.root/'source','http://localhost:3000')
        self.project=self.store.mutate('project',dict(name='Project',repo='/repo'))['id']
        self.task=self.store.mutate('task',dict(project_id=self.project,title='Repair pagination',goal='Fix search cursor',acceptance='Tests pass'))['id']
        with self.store.connection() as c:
            c.execute("INSERT INTO turns VALUES('session','turn','/repo','Repair pagination','2026-11-12','2026-11-12',1)")
            c.execute('INSERT INTO assignments VALUES(?,?,?)',('session','turn',self.task))
            for i,name in enumerate(['rg cursor','pytest pagination']):
                c.execute('INSERT INTO events(id,session_id,turn_id,kind,name,ts,runtime,failed,source_line) VALUES(?,?,?,?,?,?,?,?,?)',(f'step{i}','session','turn','tool',name,f'2026-11-12T01:00:0{i}Z',1,0,i))
        h.init(self.store)
        self.result={'summary':'Investigated cursor behavior and ran focused tests; task success is unverified.', 'subtasks':[
            {'title':'Locate pagination cursor','summary':'Searched source for cursor handling.','activity':'investigate','tags':['pagination','search'],'confidence':0.8,'step_ids':['step0']},
            {'title':'Check pagination tests','summary':'Ran a test operation; retained evidence is needed for assertions.','activity':'test','tags':['regression'],'confidence':0.7,'step_ids':['step1']}]}

    def job(self):
        body,digest=h.snapshot(self.store,self.task)
        ident='job'+str(time.time_ns())
        with self.store.connection() as c:c.execute('INSERT INTO task_history_jobs(id,task_id,snapshot_hash,snapshot,status,created,model) VALUES(?,?,?,?,?,?,?)',(ident,self.task,digest,json.dumps(body),'running',time.time(),'test-model'))
        return ident

    def test_roundtrip_and_progressive_steps(self):
        ident=h.publish(self.store,self.job(),self.result,{'total_tokens':123})
        d=h.detail(self.store,self.task)
        self.assertEqual(d['analysis']['id'],ident);self.assertFalse(d['stale']);self.assertEqual(len(d['subtasks']),2)
        first=h.detail(self.store,self.task,d['subtasks'][0]['id'],limit=1)
        self.assertEqual(first['steps'][0]['id'],'step0');self.assertIsNone(first['next_offset'])
        self.assertEqual(d['jobs'][0]['usage']['total_tokens'],123)
        self.assertNotIn('steps',h.detail(self.store,self.task))

    def test_no_invented_duplicate_or_missing_steps(self):
        body,_=h.snapshot(self.store,self.task)
        for kind in ['unknown','duplicate','omitted','confidence','injection']:
            r=copy.deepcopy(self.result)
            if kind=='unknown':r['subtasks'][0]['step_ids']=['foreign']
            if kind=='duplicate':r['subtasks'][1]['step_ids']=['step0']
            if kind=='omitted':r['subtasks'].pop()
            if kind=='confidence':r['subtasks'][0]['confidence']=float('nan')
            if kind=='injection':r['subtasks'][0]['activity']='run_shell'
            with self.subTest(kind=kind),self.assertRaises(ValueError):h.validate(r,body)

    def test_source_change_retains_prior_analysis(self):
        old=h.publish(self.store,self.job(),self.result)
        job=self.job()
        self.store.mutate('task_status',{'id':self.task,'status':'waiting','outcome':''})
        with self.assertRaisesRegex(ValueError,'changed'):h.publish(self.store,job,self.result)
        self.assertEqual(h.detail(self.store,self.task)['analysis']['id'],old)
        self.assertTrue(h.detail(self.store,self.task)['stale'])

    def test_search_subtasks_tags_goal_and_scope(self):
        h.publish(self.store,self.job(),self.result)
        for word in ['cursor','regression','pagination']:
            self.assertEqual(h.search(self.store,word)['items'][0]['task_id'],self.task)
        self.assertEqual(h.search(self.store,'cursor',project='foreign')['items'],[])
        self.assertEqual(h.search(self.store,'cursor',status='completed')['items'],[])
        self.assertEqual(h.search(self.store,'cursor',activity='document')['items'],[])
        self.assertEqual(h.search(self.store,'" OR *')['items'],[])
        with self.assertRaises(ValueError):h.search(self.store,limit=101)

    def test_unanalyzed_tasks_remain_searchable(self):
        self.assertIsNone(h.search(self.store,'pagination')['items'][0]['analysis_id'])
        self.assertEqual(h.detail(self.store,self.task)['subtasks'],[])

    def test_latest_version_only_in_search_and_foreign_subtask_denied(self):
        h.publish(self.store,self.job(),self.result)
        old=h.detail(self.store,self.task)['subtasks'][0]['id']
        newer=copy.deepcopy(self.result);newer['subtasks'][0]['tags']=['unique_new_tag']
        h.publish(self.store,self.job(),newer)
        self.assertEqual(h.search(self.store,'unique_new_tag')['total'],1)
        with self.assertRaises(ValueError):h.detail(self.store,self.task,old)

    def test_unchanged_analysis_does_not_invoke_model(self):
        h.publish(self.store,self.job(),self.result)
        with patch.object(h,'run_model') as model,patch.dict('os.environ',{'TTGL_TASK_MODEL':'test-model'}):
            self.assertEqual(h.start(self.store,self.task)['status'],'unchanged')
            model.assert_not_called()

    def test_running_job_deduplicated_and_no_silent_retry(self):
        job=self.job()
        self.assertEqual(h.start(self.store,self.task)['id'],job)
        with self.store.connection() as c:c.execute('UPDATE task_history_jobs SET created=? WHERE id=?',(time.time()-300,job))
        self.assertEqual(h.jobs(self.store,self.task)[0]['status'],'interrupted')

    def test_local_semantic_ranking_and_versioned_vectors(self):
        h.publish(self.store,self.job(),self.result)
        with patch.object(h,'embed',return_value=('fixed-model',[1.0,0.0])):
            rows=h.search(self.store,'similar task',mode='semantic')['items']
        self.assertAlmostEqual(rows[0]['similarity'],1)
        with patch.dict('os.environ',{},clear=True),self.assertRaisesRegex(ValueError,'Configure a local'):h.embed('text')

    def test_mcp_contract_and_drill_down(self):
        h.publish(self.store,self.job(),self.result)
        def call(name,args):return analyst_mcp.handle(self.store,dict(method='tools/call',params=dict(name=name,arguments=args)))
        self.assertFalse(call('search_task_history',{'query':'regression'}).get('isError',False))
        self.assertFalse(call('get_task_history',{'task_id':self.task}).get('isError',False))
        self.assertTrue(call('get_task_history',{'task_id':self.task,'subtask_id':'foreign'})['isError'])
        self.assertTrue(call('search_task_history',{'limit':500})['isError'])

    def test_failed_model_keeps_history_and_records_attempt(self):
        old=h.publish(self.store,self.job(),self.result)
        job=self.job()
        with patch.object(h.subprocess,'Popen',side_effect=OSError('Unavailable model')):h.run_model(self.store,job)
        detail=h.detail(self.store,self.task)
        self.assertEqual(detail['analysis']['id'],old)
        self.assertEqual(detail['jobs'][0]['status'],'failed')

    def test_http_origin_and_progressive_routes(self):
        from workspace import Handler
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=self.store
        base=f'http://127.0.0.1:{server.server_port}'
        server.allowed_hosts={f'127.0.0.1:{server.server_port}'};server.allowed_origins={base}
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(base+'/api/task-history?query=pagination') as r:self.assertEqual(json.load(r)['total'],1)
        req=urllib.request.Request(base+'/api/analyze-task',data=json.dumps({'task_id':self.task}).encode(),headers={'Content-Type':'application/json','Origin':'https://foreign.example'})
        with self.assertRaises(urllib.error.HTTPError) as error:opener.open(req)
        self.assertEqual(error.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError):opener.open(base+'/api/task-history?query=x&mode=semantic')
        with patch.object(h,'run_model'):
            req=urllib.request.Request(base+'/api/analyze-task',data=json.dumps({'task_id':self.task}).encode(),headers={'Content-Type':'application/json','Origin':base})
            with opener.open(req) as r:self.assertEqual(json.load(r)['status'],'queued')

    def test_local_model_protocol_and_counted_failure(self):
        outer=self
        class Model(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                outer.assertIn('format',request);outer.assertFalse(request['stream'])
                payload=json.dumps({'done':True,'message':{'content':json.dumps(outer.result)},'prompt_eval_count':30,'eval_count':15}).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
        server=ThreadingHTTPServer(('127.0.0.1',0),Model)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        job=self.job()
        with self.store.connection() as c:c.execute("UPDATE task_history_jobs SET engine='ollama' WHERE id=?",(job,))
        with patch.dict('os.environ',{'TTGL_TASK_ANALYSIS_URL':f'http://127.0.0.1:{server.server_port}/api/chat'}):h.run_model(self.store,job)
        detail=h.detail(self.store,self.task)
        self.assertEqual(detail['jobs'][0]['status'],'completed')
        self.assertEqual(detail['jobs'][0]['usage']['total_tokens'],45)
        # Invalid output must retain consumed inference, not pretend failure was free.
        self.result['subtasks'][0]['step_ids']=['unknown']
        next_job=self.job()
        with self.store.connection() as c:c.execute("UPDATE task_history_jobs SET engine='ollama' WHERE id=?",(next_job,))
        with patch.dict('os.environ',{'TTGL_TASK_ANALYSIS_URL':f'http://127.0.0.1:{server.server_port}/api/chat'}):h.run_model(self.store,next_job)
        detail=h.detail(self.store,self.task)
        self.assertEqual(detail['jobs'][0]['status'],'failed')
        self.assertEqual(detail['jobs'][0]['usage']['total_tokens'],45)
        self.assertIsNotNone(detail['analysis'])

    def test_semantic_dimension_mismatch_and_stale_search(self):
        h.publish(self.store,self.job(),self.result)
        with patch.object(h,'embed',side_effect=[('model',[1.0,0.0]),('model',[1.0])]),self.assertRaisesRegex(ValueError,'dimension'):
            h.search(self.store,'similar',mode='semantic')
        self.store.mutate('task_status',{'id':self.task,'status':'waiting','outcome':''})
        self.assertTrue(h.search(self.store,'regression')['items'][0]['stale'])

    def test_remote_models_and_redirects_denied(self):
        with patch.dict('os.environ',{'TTGL_TASK_ANALYSIS_URL':'https://remote.example/api/chat'}),self.assertRaisesRegex(ValueError,'local HTTP'):h.local_analysis('secret','model')
        with self.assertRaisesRegex(ValueError,'redirects'):h.NoRedirect().redirect_request(None,None,302,'',{},'https://remote.example')

if __name__=='__main__':unittest.main()
