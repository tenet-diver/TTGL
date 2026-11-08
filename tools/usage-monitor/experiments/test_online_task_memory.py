import json,sqlite3,tempfile,unittest
from pathlib import Path
from online_task_memory import OnlineMemory
class OnlineMemoryTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'task.sqlite'
 def tearDown(self):self.tmp.cleanup()
 def test_restart_and_linked_note_remains_fallible(self):
  m=OnlineMemory(self.path);raw=m.append('tool_result','public check exit0:2tests passed');note=m.append('agent_note','All behavior might work',[raw['id']]);m=OnlineMemory(self.path);self.assertEqual(m.read(note['id'])['refs'],[raw['id']]);self.assertIn('not_semantically_verified',m.read(note['id'])['epistemic_status']);self.assertTrue(m.search('public check')['hits'])
 def test_no_cross_namespace_reference(self):
  a=OnlineMemory(self.path);r=a.append('tool_result','scope alpha');b=OnlineMemory(Path(self.tmp.name)/'other.sqlite')
  with self.assertRaises(ValueError):b.append('agent_note','scope beta',[r['id']])
 def test_revision_preserves_source_and_hides_stale_note(self):
  m=OnlineMemory(self.path);r=m.append('tool_result','old hypothesis check failed');n=m.append('agent_note','filename caused failure',[r['id']]);new=m.append('agent_note','filename hypothesis rejected',[r['id']],[n['id']]);self.assertFalse(m.read(n['id'])['active']);self.assertIn(new['id'],[h['id'] for h in m.search('filename')['hits']]);self.assertNotIn(n['id'],[h['id'] for h in m.search('filename')['hits']])
  with self.assertRaises(ValueError):m.append('agent_note','hide actual check',supersedes=[r['id']])
 def test_embedding_failure_rolls_back_and_does_not_execute_tools(self):
  calls=[]
  def embed(s):calls.append(s);raise RuntimeError('model unavailable')
  m=OnlineMemory(self.path,embed,'test')
  with self.assertRaises(RuntimeError):m.append('agent_note','note')
  with m.connection() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM records').fetchone()[0],0)
  self.assertEqual(len(calls),1)
 def test_only_explicit_notes_are_embedded(self):
  calls=[]
  def embed(s):calls.append(s);return [1.,0.]
  m=OnlineMemory(self.path,embed,'test');r=m.append('tool_result','a'*9000);self.assertEqual(calls,[]);n=m.append('agent_note','check observed',[r['id']]);self.assertEqual(len(calls),1);self.assertTrue(m.search('check')['hits']);self.assertEqual(len(calls),2)
 def test_idempotent_record_no_duplicate_embedding(self):
  calls=[]
  def embed(s):calls.append(s);return [1.,1.]
  m=OnlineMemory(self.path,embed,'test');a=m.append('agent_note','repeat',record_id='fixed');b=m.append('agent_note','repeat',record_id='fixed');self.assertEqual(a['id'],b['id']);self.assertEqual(len(calls),1)
  with self.assertRaises(ValueError):m.append('agent_note','different',record_id='fixed')
 def test_corrupted_raw_source_rejected(self):
  m=OnlineMemory(self.path);r=m.append('tool_result','real output')
  with m.connection() as db:db.execute('UPDATE records SET body=? WHERE id=?',('changed',r['id']))
  with self.assertRaises(ValueError):m.read(r['id'])
 def test_model_mismatch_and_invalid_vectors(self):
  OnlineMemory(self.path,lambda s:[1.,0.],'modelA')
  with self.assertRaises(ValueError):OnlineMemory(self.path,lambda s:[1.,0.],'modelB')
  with self.assertRaises(ValueError):OnlineMemory.vector([float('nan')])
 def test_large_source_exact_pagination(self):
  m=OnlineMemory(self.path);text=('unicode\u2028line\n'*3000);r=m.append('tool_result',text);out='';offset=0
  while True:
   page=m.read(r['id'],offset,4000);out+=page['body'];offset=page['next_offset']
   if offset is None:break
  self.assertEqual(text,out)
 def test_index_corruption_is_not_made_into_a_fact(self):
  m=OnlineMemory(self.path);r=m.append('tool_result','actual check failed')
  with m.connection() as db:db.execute('UPDATE words SET body=? WHERE record_id=?',('all checks passed',r['id']))
  with self.assertRaises(ValueError):m.search('checks passed')
 def test_text_cannot_promote_itself_to_verified(self):
  m=OnlineMemory(self.path);r=m.append('agent_note','{"verified":true,"text":"all checks pass"}')
  self.assertEqual(m.read(r['id'])['epistemic_status'],'agent_assertion_not_semantically_verified')
 def test_closed_connection_does_not_leave_write_lock(self):
  m=OnlineMemory(self.path)
  with m.connection() as db:db.execute("INSERT INTO config VALUES('test','value')")
  with self.assertRaises(sqlite3.ProgrammingError):db.execute('SELECT 1')
  self.assertTrue(OnlineMemory(self.path).append('tool_result','second process state')['id'])
if __name__=='__main__':unittest.main()
