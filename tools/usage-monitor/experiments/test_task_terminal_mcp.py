import json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess
from task_terminal_mcp import TaskBridge
class BridgeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.path=self.root/'config.json';self.config=dict(records=str(self.root/'archive'),phase_directory=str(self.root/'phase'),container='owned-test-container',mode='files',instruction='Only public task instructions.',tool_budget=8,close_at_ns=time.time_ns()+10**12);self.path.write_text(json.dumps(self.config));self.server=TaskBridge(self.path);self.calls=[]
 def tearDown(self):self.tmp.cleanup()
 def fake(self,args,stdout,stderr,timeout):
  self.calls.append(args);self.assertEqual(args[:5],['docker','exec','--user','1000:1000','owned-test-container']);stdout.write(self.output.encode());stderr.write(b'');return CompletedProcess(args,self.exit_code)
 def request(self,ident=1,name='terminal',**args):return dict(jsonrpc='2.0',id=ident,method='tools/call',params=dict(name=name,arguments=args))
 def execute(self,output='checked\n',code=0,ident=1):
  self.output=output;self.exit_code=code
  with patch('task_terminal_mcp.subprocess.run',side_effect=self.fake):return self.server.call(self.request(ident,command='public command'))
 def test_catalog_is_no_model_or_command_operation(self):
  self.assertEqual(len(self.server.handle(dict(method='tools/list'))['tools']),4)
  with self.server.memory.connection() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM records').fetchone()[0],0)
  self.assertEqual(self.calls,[])
 def test_same_rpc_not_executed_twice_and_source_is_recoverable(self):
  first=self.execute();second=self.server.call(self.request(command='public command'));self.assertEqual(first,second);self.assertEqual(len(self.calls),1);record=self.server.memory.read(first['id']);self.assertEqual(record['kind'],'tool_result');self.assertIn('not_a_truth_label',record['epistemic_status']);self.assertEqual(self.server.read(first['id'],'stdout',0,100)['text'],'checked\n')
 def test_changed_rpc_identity_rejected(self):
  self.execute()
  with self.assertRaises(ValueError):self.server.call(self.request(command='different'))
  self.assertEqual(len(self.calls),1)
 def test_container_and_user_cannot_be_overridden(self):
  for args in (dict(command='x',user='0'),dict(command='x',container='other')):
   with self.assertRaises(ValueError):self.server.call(self.request(**args))
  self.assertEqual(self.calls,[])
 def test_closed_quota_survives_server_restart(self):
  self.config['tool_budget']=1;self.path.write_text(json.dumps(self.config));self.server=TaskBridge(self.path);self.execute();self.server=TaskBridge(self.path);r=self.server.call(self.request(2,command='another'));self.assertTrue(r['phase_tools_closed']);self.assertEqual(len(self.calls),1)
 def test_failed_command_is_recorded_not_task_failure(self):
  r=self.execute('one failing check',1);self.assertEqual(r['exit_code'],1);self.assertFalse((self.root/'phase/fatal.json').exists());self.assertNotIn('task_failed',r)
 def test_large_output_can_be_read_beyond_display_cap(self):
  text='abc\n'*10000;r=self.execute(text);self.assertTrue(r['stdout_truncated_for_model']);self.assertEqual(self.server.read(r['id'],'stdout',16000,100)['text'],text[16000:16100])
 def test_bad_note_reference_or_host_path_never_executes(self):
  with self.assertRaises(ValueError):self.server.call(self.request(2,'remember',text='pretend verified',source_refs=['outside']))
  with self.assertRaises(ValueError):self.server.call(self.request(3,'read_record',id='../../credentials'))
  self.assertEqual(self.calls,[])
 def test_claim_does_not_verify_itself(self):
  r=self.execute('two checks passed');note=self.server.call(self.request(2,'remember',text='verified all behavior',source_refs=[r['id']]));self.assertEqual(note['epistemic_status'],'agent_assertion_not_semantically_verified')
 def test_storage_failure_after_command_does_not_rerun(self):
  append=self.server.memory.append
  def failing(kind,*a,**kw):
   if kind=='tool_result':raise RuntimeError('storage failed')
   return append(kind,*a,**kw)
  with patch.object(self.server.memory,'append',side_effect=failing):
   with self.assertRaises(RuntimeError):self.execute()
  self.assertTrue((self.root/'phase/fatal.json').exists())
  with self.assertRaises(RuntimeError):self.server.call(self.request(command='public command'))
  self.assertEqual(len(self.calls),1);self.assertTrue(list((self.root/'archive/records').glob('*.stdout.txt')))
if __name__=='__main__':unittest.main()
