"""Native task turns exposing only the trusted task MCP bridge to model tools."""
import json,shutil,sys
from pathlib import Path
from longmemeval_codex_trial import native_command,run_process
from native_jsonl import records,validate_native_completion
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/'work/security/context-memory-20261107'
def command(work,cell,config,*,resume=None,port=8370):
 work=Path(work).resolve();work.mkdir(parents=True,exist_ok=True);cell=Path(cell).resolve();runtime=str(Path(shutil.which('codex')).resolve());cmd=native_command(work,cell,'gpt-6.1-sol');i=cmd.index('-s');del cmd[i:i+2];cmd[-1:-1]=['--ignore-rules']
 for feature in ('multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image','shell_tool','unified_exec','apply_patch_freeform','goals'):cmd[-1:-1]=['--disable',feature]
 settings={'project_doc_max_bytes':0,'features.skip_host_skill_discovery':True,'suppress_unstable_features_warning':True,'features.enable_request_compression':False,'features.incremental_tools':False,'model_provider':'openai','openai_base_url':f'http://127.0.0.1:{port}/backend-api/codex','default_permissions':'ttgl_online','permissions.ttgl_online.filesystem':{':root':'deny',':minimal':'read',str(work):'read',runtime:'read'},'permissions.ttgl_online.network.enabled':False,'web_search':'disabled','mcp_servers.ttgl_task.command':sys.executable,'mcp_servers.ttgl_task.args':[str(HERE/'task_terminal_mcp.py'),'--config',str(Path(config).resolve())],'mcp_servers.ttgl_task.env':{'PYTHONPATH':str(HERE)+':'+str(ROOT/'memory-runtime'),'HF_HUB_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1'},'mcp_servers.ttgl_task.required':True,'mcp_servers.ttgl_task.startup_timeout_sec':60,'mcp_servers.ttgl_task.tool_timeout_sec':240}
 for k,v in settings.items():
  encoded='{'+','.join(json.dumps(a)+'='+json.dumps(b) for a,b in v.items())+'}' if isinstance(v,dict) else json.dumps(v)
  cmd[-1:-1]=['-c',k+'='+encoded]
 if resume:cmd[-1:]=['resume',resume,'-']
 return cmd

def run(work,cell,config,prompt,*,resume=None,timeout=900):
 cell=Path(cell);cell.mkdir();(cell/'prompt.txt').write_text(prompt);cmd=command(work,cell,config,resume=resume);run_process(cmd,prompt,cell,timeout);sid=validate_native_completion(cell)
 if resume and sid!=resume:raise ValueError('Continued condition changed native thread')
 completed=[r['item'] for r in records(cell) if r.get('type')=='item.completed'];unexpected=[r.get('type') for r in completed if r.get('type') not in ('agent_message','reasoning','mcp_tool_call','plan','todo_list','context_compaction')]
 if unexpected:raise ValueError('Unexpected host/tool action:'+str(unexpected))
 result=dict(session_id=sid,mcp_calls=sum(i.get('type')=='mcp_tool_call' for i in completed),tools=[i.get('tool') for i in completed if i.get('type')=='mcp_tool_call'])
 (cell/'complete.json').write_text(json.dumps(result,indent=2));return result
