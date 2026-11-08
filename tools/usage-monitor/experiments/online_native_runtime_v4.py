"""Same tested native generation command; strictly validate owned MCP scope."""
import json
from pathlib import Path
import online_native_runtime_v3 as previous
from native_jsonl import records
command=previous.command
def validate_scope(cell):
 calls=[r['item'] for r in records(Path(cell)) if r.get('type')=='item.completed' and r.get('item',{}).get('type')=='mcp_tool_call']
 if any(i.get('server')!='ttgl_task' or i.get('tool') not in previous.ALLOWED for i in calls):raise ValueError('Unexpected MCP server/tool; preserve inference and stop without retry')
 return dict(passed=True,allowed_server='ttgl_task',allowed_tools=list(previous.ALLOWED),observed_calls=len(calls))
def run(work,cell,config,prompt,*,resume=None,timeout=900):
 result=previous.run(work,cell,config,prompt,resume=resume,timeout=timeout);scope=validate_scope(cell)
 with (Path(cell)/'tool-scope-verified.json').open('x') as f:json.dump(scope,f,indent=2)
 return result
