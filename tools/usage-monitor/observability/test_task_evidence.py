import json,unittest
import test_workspace as fixtures
import task_evidence as e

class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.WorkspaceTests();self.fixture.setUp();self.addCleanup(self.fixture.directory.cleanup)
  self.store=self.fixture.store;self.fixture.store.scan();_,self.task=self.fixture.define_task();self.store.mutate('assign',dict(session_id='s',turn_id='t',task_id=self.task))
 def test_native_change_validation_and_image_sources(self):
  rows=self.fixture.rows+[
   dict(timestamp='2026-11-05T00:00:02Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='FileChange',id='edit',changes={'src/page.tsx':{'kind':'update','diff':'+button'}},status='completed'))),
   dict(timestamp='2026-11-05T00:00:03Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='CommandExecution',id='tests',command=['pytest','tests'],aggregated_output='2 passed',exit_code=0,duration={'secs':1,'nanos':0}))),
   dict(timestamp='2026-11-05T00:00:04Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='ImageView',id='image',path='/private/not-read.png',status='completed')))]
  self.fixture.source.write_text(''.join(json.dumps(r)+'\n' for r in rows));self.store.ingest(self.fixture.source)
  packet=e.packet(self.store,self.task)
  self.assertTrue(packet['groups']['change'][0]['visual_candidate']);self.assertEqual(packet['groups']['change'][0]['detail'],'+button')
  self.assertEqual(packet['groups']['validation'][0]['outcome'],'command_passed');self.assertEqual(packet['groups']['visual_reference'][0]['outcome'],'reference_only')
  self.assertEqual(packet['groups']['intervention'],[])
 def test_unknowns_are_not_success_or_no_intervention(self):
  packet=e.packet(self.store,self.task)
  self.assertIn('No validation',packet['gaps']['validation']);self.assertIn('No confirmed',packet['gaps']['human_intervention']);self.assertIsNone(packet['task_outcome'])
 def test_manual_reference_and_intervention_keep_provenance(self):
  e.add(self.store,self.task,'intervention','I corrected the acceptance criteria','Explicit user report',outcome='confirmed')
  e.add(self.store,self.task,'visual_reference','After screenshot',reference='https://example.com/screen.png')
  packet=e.packet(self.store,self.task);self.assertIn('not independently verified',packet['groups']['intervention'][0]['basis'])
  self.assertEqual(packet['groups']['visual_reference'][0]['reference'],'https://example.com/screen.png')
  with self.assertRaises(ValueError):e.add(self.store,self.task,'visual_reference','Bad',reference='file:///etc/passwd')
  with self.assertRaises(ValueError):e.add(self.store,self.task,'visual_reference','Bad',reference='https://secret:secret@example.com/a.png')
 def test_user_follow_up_is_not_automatically_interference(self):
  rows=self.fixture.rows+[dict(timestamp='2026-11-05T00:00:02Z',type='event_msg',payload=dict(type='item_completed',turn_id='followup',item=dict(type='UserMessage',content=[dict(type='text',text='Please also check the visual layout')])))]
  self.fixture.source.write_text(''.join(json.dumps(r)+'\n' for r in rows));self.store.ingest(self.fixture.source)
  self.store.mutate('assign',dict(session_id='s',turn_id='followup',task_id=self.task))
  packet=e.packet(self.store,self.task)
  self.assertEqual(len(packet['user_follow_ups']),1);self.assertEqual(packet['groups']['intervention'],[])
 def test_foreign_task_and_unsupported_kind_rejected(self):
  with self.assertRaises(ValueError):e.packet(self.store,'foreign')
  with self.assertRaises(ValueError):e.add(self.store,self.task,'execute','Run command')
 def test_story_reports_failed_last_check_and_later_edit(self):
  groups={kind:[] for kind in e.KINDS}
  groups['validation']=[dict(event_id='check',title='pytest',recorded_at='2026-11-05T00:00:03Z',outcome='command_failed')]
  groups['change']=[dict(event_id='edit',title='page.css',recorded_at='2026-11-05T00:00:04Z')]
  result=e.story(dict(goal='Fix layout',acceptance='Responsive at 390px',outcome=None),groups,True)
  self.assertEqual(result['changes_after_last_validation'],1)
  self.assertEqual(result['changed_files'],['page.css'])
  self.assertIn('Last recorded validation command failed.',result['open_items'])
  self.assertTrue(any('truncated' in gap for gap in result['open_items']))
  self.assertTrue(any('acceptance' in gap for gap in result['open_items']))
 def test_story_never_treats_passed_command_as_task_acceptance(self):
  packet=e.packet(self.store,self.task)
  self.assertEqual(packet['story']['request'],'Resolve failure')
  self.assertEqual(packet['story']['validation_commands'],0)
  groups={kind:[] for kind in e.KINDS}
  groups['validation']=[dict(event_id='check',title='pytest',recorded_at='2026-11-05T00:00:03Z',outcome='command_passed')]
  result=e.story(dict(goal='Fix',acceptance='',outcome=None),groups)
  self.assertIn('Task acceptance has not been recorded.',result['open_items'])
 def test_story_keeps_ambiguous_or_missing_timestamps_unknown(self):
  groups={kind:[] for kind in e.KINDS}
  groups['validation']=[dict(event_id='a',title='pytest',recorded_at='2026-11-05T00:00:03Z',outcome='command_passed'),dict(event_id='b',title='lint',recorded_at='2026-11-05T00:00:03Z',outcome='command_failed')]
  task=dict(goal='Fix',acceptance='',outcome=None)
  result=e.story(task,groups)
  self.assertIsNone(result['last_validation'])
  self.assertIsNone(result['changes_after_last_validation'])
  groups['validation'][1]['recorded_at']='unknown'
  result=e.story(task,groups)
  self.assertIsNone(result['changes_after_last_validation'])
  self.assertTrue(any('ordering is uncertain' in gap for gap in result['open_items']))
if __name__=='__main__':unittest.main()
