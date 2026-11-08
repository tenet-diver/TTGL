import json,tempfile,time,unittest
from pathlib import Path
from task_terminal_mcp_v2 import TaskBridge
class SearchUsability(unittest.TestCase):
 def test_larger_positive_limit_is_bounded_and_source_is_recoverable(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);cfg=p/'config.json';cfg.write_text(json.dumps(dict(records=str(p/'records'),phase_directory=str(p/'phase'),container='unused',mode='files',instruction='Public labels instruction',tool_budget=4,close_at_ns=time.time_ns()+10**12)))
   bridge=TaskBridge(cfg);note=bridge.memory.append('agent_note','labels were normalized; checks are fallible',record_id='note')
   request=dict(id=1,params=dict(name='search_records',arguments=dict(query='labels',limit=20)))
   result=bridge.call(request);self.assertEqual(result['requested_limit'],20);self.assertEqual(result['effective_limit'],8);self.assertLessEqual(len(result['hits']),8);self.assertIn('note',[h['id'] for h in result['hits']]);self.assertEqual(bridge.read('note','body',0,4000)['body'],note['body'])
 def test_empty_query_error_identifies_the_invalid_argument(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);cfg=p/'config.json';cfg.write_text(json.dumps(dict(records=str(p/'records'),phase_directory=str(p/'phase'),container='unused',mode='files',instruction='Public instruction',tool_budget=4,close_at_ns=time.time_ns()+10**12)))
   bridge=TaskBridge(cfg)
   with self.assertRaisesRegex(ValueError,'query must be a nonempty'):bridge.call(dict(id=1,params=dict(name='search_records',arguments=dict(query='',limit=20))))
if __name__=='__main__':unittest.main()
