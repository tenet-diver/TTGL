import json,tempfile,unittest
from pathlib import Path
from online_native_runtime_v4 import validate_scope
class ToolScope(unittest.TestCase):
 def test_other_server_cannot_hide_behind_an_allowed_tool_name(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)
   for server,tool in [('other_private_server','terminal'),('ttgl_task','read_host_file')]:
    with self.subTest(server=server,tool=tool):
     (p/'agent.jsonl').write_text(json.dumps(dict(type='item.completed',item=dict(type='mcp_tool_call',server=server,tool=tool,status='completed')))+'\n')
     with self.assertRaisesRegex(ValueError,'Unexpected MCP'):validate_scope(p)
 def test_expected_scope_keeps_failed_calls_as_observed_evidence(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'agent.jsonl').write_text(json.dumps(dict(type='item.completed',item=dict(type='mcp_tool_call',server='ttgl_task',tool='terminal',status='failed',error={'message':'requires approval'})))+'\n');result=validate_scope(p);self.assertTrue(result['passed']);self.assertEqual(result['observed_calls'],1)
if __name__=='__main__':unittest.main()
