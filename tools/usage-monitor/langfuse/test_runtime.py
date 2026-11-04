import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('bridge_runtime_test',Path(__file__).with_name('bridge.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);r=b.runtime
class RuntimeTests(unittest.TestCase):
 def test_native_duration_is_distinct_from_event_window(self):
  self.assertEqual(r.native_ns({'secs':357,'nanos':968724629}),357968724629)
  item={'id':'i','sid':'s','name':'shell','start':0,'end':175353470000000,'line':1,'timing_known':True,'native_runtime_ns':357968724629,'operation':'shell / tests (xcodebuild)','failed':True,'argument_pattern':'safe'}
  s=list(r.spans({'id':'s'},[item],b.span))[0];self.assertEqual(int(s['endTimeUnixNano'])-int(s['startTimeUnixNano']),357968724629)
 def test_unknown_units_and_invalid_durations_are_not_guessed(self):
  for v in [None,123,{'secs':-1,'nanos':0},{'secs':1,'nanos':10**9}]:self.assertIsNone(r.native_ns(v))
 def test_command_groups_ignore_embedded_script_body(self):
  self.assertEqual(r.shell_operation({'command':['/bin/bash','-lc',"python3 - <<'PY'\nprint('pytest git cat')\nPY"]}),'python inline scripts')
  self.assertEqual(r.shell_operation({'command':['/bin/bash','-lc','cd /private/project && python3 -m pytest -q']}),'tests (pytest)')
  self.assertEqual(r.shell_operation({'command':['/bin/bash','-lc','npm run dev']}),'dev servers (npm)')
  batch="cat > /private/script.js <<'EOF'\nconsole.log('pytest')\nEOF\nnpm run dev"
  self.assertEqual(r.shell_operation({'command':['/bin/bash','-lc',batch]}),'batch: file writes (cat) + dev servers (npm)')
  self.assertEqual(r.shell_operation({'command':['/bin/bash','-lc','git status && pytest']}),'batch: git status + tests (pytest)')
 def test_runtime_only_does_not_serialize_full_outputs(self):
  import json,tempfile
  from unittest.mock import patch
  rows=[{'type':'session_meta','payload':{'id':'s','timestamp':'2026-11-04T12:00:00Z'}},{'type':'event_msg','timestamp':'2026-11-04T12:00:01Z','payload':{'type':'item_completed','thread_id':'s','started_at_ms':1793793600000,'completed_at_ms':1793793601000,'item':{'type':'CommandExecution','id':'i','command':['/bin/bash','-lc','pytest'],'exit_code':0,'duration':{'secs':1,'nanos':0},'aggregated_output':'large private output'}}}]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.jsonl';p.write_text(''.join(json.dumps(x)+'\n' for x in rows))
   with patch.object(b.monitor,'size_text',side_effect=AssertionError('unnecessary output serialization')):
    _,records,_=b.tool_records(p,runtime_only=True)
   self.assertEqual(records[0]['native_runtime_ns'],10**9);self.assertIsNone(records[0]['output_bytes'])
 def test_outcome_and_chat_operation_are_explicit(self):
  self.assertEqual(r.operation({'type':'McpToolCall'},'codex_app.list_threads'),'Chats / list')
  item={'id':'i','sid':'s','name':'codex_app.list_threads','start':0,'end':4*10**12,'line':1,'timing_known':True,'native_runtime_ns':3600*10**9,'operation':'Chats / list','failed':True,'argument_pattern':'keys=limit; limit=10'}
  span=list(r.spans({'id':'s'},[item],b.span))[0];self.assertEqual(span['name'],'Chats / list · failed');self.assertEqual(span['status']['code'],2)
if __name__=='__main__':unittest.main()
