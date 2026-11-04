import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('monitor',Path(__file__).with_name('server.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AdapterTests(unittest.TestCase):
 def parse(self,rows):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'fixture.jsonl';p.write_text(''.join(json.dumps(r)+'\n' for r in rows));return m.parse(p)
 def test_native_ids_and_parent_exclusion(self):
  meta={'type':'session_meta','payload':{'id':'child','timestamp':'2026-11-04T12:00:00Z'}}
  def event(ident,thread,ts,output):return {'type':'event_msg','timestamp':ts,'payload':{'type':'item_completed','thread_id':thread,'item':{'id':ident,'type':'CommandExecution','aggregated_output':output,'exit_code':0},'started_at_ms':1000,'completed_at_ms':2000}}
  rows=[meta,event('parent','parent','2026-11-04T11:00:00Z','old'),event('own','child','2026-11-04T12:01:00Z','abc'),event('own','child','2026-11-04T12:01:00Z','abc')]
  _,_,tools,bad=self.parse(rows);self.assertEqual(len(tools),1);self.assertEqual(tools[0][4:7],(3,1.0,0));self.assertEqual(bad,0)
 def test_missing_output_and_timing_remain_unknown(self):
  rows=[{'type':'session_meta','payload':{'id':'s'}},{'type':'event_msg','payload':{'type':'item_completed','item':{'id':'i','type':'McpToolCall','server':'x','tool':'y','status':'completed'}}}]
  t=self.parse(rows)[2][0];self.assertIsNone(t[4]);self.assertIsNone(t[5]);self.assertEqual(t[2],'x.y')
 def test_legacy_response_join(self):
  rows=[{'type':'session_meta','payload':{'id':'s'}},{'type':'response_item','payload':{'type':'function_call','call_id':'c','name':'exec_command'}},{'type':'response_item','payload':{'type':'function_call_output','call_id':'c','output':'done'}}]
  t=self.parse(rows)[2][0];self.assertEqual(t[2],'exec_command');self.assertEqual(t[4],4);self.assertIsNone(t[5]);self.assertIsNone(t[6])
 def test_reimport_is_idempotent(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/'m.sqlite';m.init(db)
   with m.connect(db) as c:
    row=('c','s','shell','t',3,None,None,'h',1,'command');c.execute('INSERT OR IGNORE INTO tools VALUES(?,?,?,?,?,?,?,?,?,?)',row);c.execute('INSERT OR IGNORE INTO tools VALUES(?,?,?,?,?,?,?,?,?,?)',row)
    self.assertEqual(c.execute('SELECT count(*) FROM tools').fetchone()[0],1)
class HttpTests(unittest.TestCase):
 def test_mutation_origin_and_idempotency(self):
  import threading,urllib.request,urllib.error
  with tempfile.TemporaryDirectory() as d:
   monitor=m.Monitor(Path(d),Path(d))
   with m.connect(monitor.db) as c:
    c.executemany('INSERT INTO tools VALUES(?,?,?,?,?,?,?,?,?,?)',[(str(i),'s','shell','t',40000,None,None,'h',i,'command') for i in range(3)])
   server=m.ThreadingHTTPServer(('127.0.0.1',0),m.Handler);server.monitor=monitor
   threading.Thread(target=server.serve_forever,daemon=True).start()
   url=f'http://127.0.0.1:{server.server_port}/api/decision';ident=monitor.suggestions()[0]['id']
   body=json.dumps({'id':ident,'choice':'review'}).encode()
   try:
    bad=urllib.request.Request(url,data=body,headers={'Origin':'https://example.invalid'})
    with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(bad)
    self.assertEqual(error.exception.code,403)
    for _ in range(2):
     req=urllib.request.Request(url,data=body,headers={'Origin':f'http://127.0.0.1:{server.server_port}','Content-Type':'application/json'})
     with urllib.request.urlopen(req) as result:self.assertEqual(json.load(result)['implementation'],'not_started')
    with m.connect(monitor.db) as c:self.assertEqual(c.execute('SELECT count(*) FROM events').fetchone()[0],1)
   finally:server.shutdown();server.server_close()
if __name__=='__main__':unittest.main()
