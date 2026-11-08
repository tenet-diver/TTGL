import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import online_longhorizon_trial as trial
class ScheduleControls(unittest.TestCase):
 def exercise(self,condition,fail_second=False):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'development-source/public-task';source.mkdir(parents=True);(source/'instruction.md').write_text('Only a public task instruction.');(root/'embedding-model-receipt.json').write_text('{}');clock=[0.0];calls=[];grades=[]
   class Actor:
    def __init__(self,cell):
     self.cell=cell;cell.mkdir(parents=True);self.name='owned';self.history=root/'history';self.history.mkdir()
    def start(self):pass
    def close(self):pass
    def grade(self):grades.append(clock[0]);return dict(reward=1,private_only=True)
   def model(work,cell,config,prompt,*,resume,timeout):
    self.assertNotIn('private_only',prompt);calls.append(dict(resume=resume,at=clock[0],timeout=timeout,config=json.loads(config.read_text()),prompt=prompt))
    if fail_second and len(calls)==2:raise RuntimeError('uncertain started model request')
    return dict(session_id=resume or 'session'+str(len(calls)))
   def sleep(seconds):self.assertLessEqual(seconds,30);clock[0]+=seconds
   spec=dict(id='owned-case',task='fake',source='public-task',condition=condition,horizon_seconds=1800)
   with patch.object(trial,'BASE',root),patch.object(trial,'GLOBAL',root),patch.dict(trial.ADAPTERS,{'fake':Actor}),patch.object(trial,'run',side_effect=model),patch.object(trial.time,'monotonic',side_effect=lambda:clock[0]),patch.object(trial.time,'sleep',side_effect=sleep):
    if fail_second:
     with self.assertRaisesRegex(RuntimeError,'uncertain'):trial.execute_assignment(root,spec)
     self.assertEqual(grades,[]);self.assertTrue((root/'assignments/owned-case/stopped.json').exists());self.assertEqual(len(calls),2)
    else:
     trial.execute_assignment(root,spec);self.assertEqual(grades,[1800]);self.assertEqual([c['at'] for c in calls],[0,900]);self.assertEqual(calls[1]['resume'],'session1' if condition=='continued_records' else None);self.assertTrue((root/'assignments/owned-case/complete.json').exists())
     self.assertEqual(calls[0]['config']['mode'],'memory' if condition=='restarted_memory' else 'files')
     self.assertIn('Only a public task instruction.',calls[0]['prompt'])
     self.assertEqual('Only a public task instruction.' in calls[1]['prompt'],condition!='continued_records')
 def test_continued_thread_keeps_full_horizon_before_grade(self):self.exercise('continued_records')
 def test_restart_records_uses_fresh_thread(self):self.exercise('restarted_records')
 def test_restart_memory_is_only_mode_change(self):self.exercise('restarted_memory')
 def test_uncertain_second_call_stops_without_grading_or_retry(self):self.exercise('restarted_memory',True)
 def test_started_matrix_cannot_be_automatically_replayed(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);pointer=p/'pointer.json';pointer.write_text(json.dumps(dict(root=str(p))));(p/'manifest.json').write_text(json.dumps(dict(sources={})));(p/'started.json').write_text('{}')
   with patch.object(trial,'POINTER',pointer),patch.object(trial,'execute_assignment') as execute:
    with self.assertRaisesRegex(ValueError,'Prior worker started'):trial.trial()
    execute.assert_not_called()
if __name__=='__main__':unittest.main()
