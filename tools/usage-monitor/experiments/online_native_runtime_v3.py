"""Invocation-local approval for exactly four user-authorized sandbox tools.

No global approval change, sandbox escape, hook-trust bypass, alternate actor UID
or network access. Other tools remain unavailable.001blocked evidence is retained.
"""
import json
from pathlib import Path
import online_native_runtime as previous
from native_jsonl import records,validate_native_completion
from longmemeval_codex_trial import run_process
ALLOWED=('terminal','remember','search_records','read_record')
def command(work,cell,config,*,resume=None,port=8370):
 cmd=previous.command(work,cell,config,port=port)
 cmd=[x.replace("task_terminal_mcp.py","task_terminal_mcp_v2.py") for x in cmd]
 cmd[-1:-1]=['-c','mcp_servers.ttgl_task.enabled_tools='+json.dumps(list(ALLOWED))]
 for name in ALLOWED:cmd[-1:-1]=['-c','mcp_servers.ttgl_task.tools.'+name+'.approval_mode="approve"']
 if resume:cmd[-1:]=['resume',resume,'-']
 return cmd

TASK_SCOPE="The host model filesystem sandbox is read-only. The terminal tool executes in a separate task container with a writable task workspace. Make and verify requested changes there; do not infer that task writes are forbidden from host sandbox mode. Search results are capped at8; use source IDs/read_record to inspect evidence. Notes remain fallible.\n\n"
def run(work,cell,config,prompt,*,resume=None,timeout=900):
 prompt=TASK_SCOPE+prompt
 cell=Path(cell);cell.mkdir();(cell/'prompt.txt').write_text(prompt);run_process(command(work,cell,config,resume=resume),prompt,cell,timeout);sid=validate_native_completion(cell)
 if resume and sid!=resume:raise ValueError('Continued condition changed native thread')
 completed=[r['item'] for r in records(cell) if r.get('type')=='item.completed'];unexpected=[r.get('type') for r in completed if r.get('type') not in ('agent_message','reasoning','mcp_tool_call','plan','todo_list','context_compaction')]
 if unexpected:raise ValueError('Unexpected host/tool action:'+str(unexpected))
 calls=[i for i in completed if i.get('type')=='mcp_tool_call'];failed=[i for i in calls if i.get('error') or i.get('status')=='failed']
 result=dict(session_id=sid,mcp_calls=len(calls),tools=[i.get('tool') for i in calls],failed_mcp_calls=len(failed))
 (cell/'complete.json').write_text(json.dumps(result,indent=2))
 # A policy/transport failure must stop a mechanism unit rather than silently
 # starting its next phase. Ordinary tool-result command exits remain data.
 if any('requires approval' in json.dumps(i.get('error',{})) for i in failed):raise RuntimeError('MCP approval gate blocked; preserve completed inference and stop, no retry')
 return result
