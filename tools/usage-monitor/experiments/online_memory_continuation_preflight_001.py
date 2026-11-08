#!/usr/bin/env python3
"""Actual reference-fixture and native MCP catalog checks; zero LLM requests."""
import hashlib,json,os,selectors,subprocess,sys
from pathlib import Path
from online_memory_continuation_001 import ROOT
from mcp_memory_probe import Client
from online_native_runtime import HERE,ROOT as GLOBAL

def main():
 out=ROOT/'preflight';out.mkdir();m=json.loads((ROOT/'manifest.json').read_text())
 reference="""import sys,types,unittest
mod=types.ModuleType('labels')
def normalize_labels(items):
 out=[]
 for x in items:
  if not isinstance(x,str):raise ValueError('non-string')
  x=x.strip().lower()
  if x and x not in out:out.append(x)
 return out
mod.normalize_labels=normalize_labels;sys.modules['labels']=mod
suite=unittest.defaultTestLoader.discover('/app/public_tests');r=unittest.TextTestRunner().run(suite);raise SystemExit(not r.wasSuccessful())
"""
 r=subprocess.run(['docker','exec','--user','1000:1000',m['container'],'python3','-c',reference],capture_output=True,text=True,timeout=30)
 (out/'reference.json').write_text(json.dumps(dict(passed=r.returncode==0,stdout=r.stdout,stderr=r.stderr,model_calls=0),indent=2))
 if r.returncode:raise ValueError('Reference fixture failed; no model')
 config=str(ROOT/'server.json');env={'PYTHONPATH':str(HERE)+':'+str(GLOBAL/'memory-runtime'),'HF_HUB_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1'}
 command=['codex','app-server','--listen','stdio://','-c','mcp_servers.ttgl-analyst.enabled=false','-c','mcp_servers.ttgl_task.command='+json.dumps(sys.executable),'-c','mcp_servers.ttgl_task.args='+json.dumps([str(HERE/'task_terminal_mcp_v2.py'),'--config',config]),'-c','mcp_servers.ttgl_task.env={'+','.join(json.dumps(k)+'='+json.dumps(v) for k,v in env.items())+'}','-c','mcp_servers.ttgl_task.startup_timeout_sec=60','-c','mcp_servers.ttgl_task.required=true','-c','features.incremental_tools=false']
 command+=['-c','mcp_servers.ttgl_task.enabled_tools=["terminal","remember","search_records","read_record"]']
 for name in ('terminal','remember','search_records','read_record'):command+=['-c','mcp_servers.ttgl_task.tools.'+name+'.approval_mode="approve"']
 c=Client.__new__(Client);c.err=(out/'catalog-stderr.log').open('x');c.p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=c.err,start_new_session=True);c.selector=selectors.DefaultSelector();c.selector.register(c.p.stdout,selectors.EVENT_READ);c.buffer=b'';c.ident=0;c.calls=[];c.journal=(out/'catalog-rpc.jsonl').open('x')
 try:
  c.request('initialize',dict(clientInfo=dict(name='ttgl_online_catalog',version='1'),capabilities=dict(experimentalApi=False)));c.p.stdin.write(b'{"method":"initialized","params":{}}\n');c.p.stdin.flush();(ROOT/'native-work').mkdir(exist_ok=True)
  thread=c.request('thread/start',dict(cwd=str(ROOT/'native-work'),approvalPolicy='never',sandbox='read-only',ephemeral=True));tid=thread['thread']['id']
  value=c.request('mcpServerStatus/list',dict(threadId=tid,serverName='ttgl_task',detail='toolsAndAuthOnly',limit=10));(out/'catalog.json').write_text(json.dumps(value,indent=2))
  server=next(x for x in value['data'] if x['name']=='ttgl_task');names=list(server.get('tools',{}));expected={'terminal','remember','read_record','search_records'}
  passed=all(any(name.endswith(x) for name in names) for x in expected) and not server.get('toolsError')
  if not passed:raise ValueError('Native MCP catalog incomplete; no inference')
 finally:c.close()
 (out/'complete.json').write_text(json.dumps(dict(passed=True,model_calls=0,reference_fixture=True,native_catalog=True,tools=names,no_turn_start_rpc=True),indent=2));print('Reference fixture and actual native MCP catalog pass;0LLMcalls.',flush=True)
if __name__=='__main__':main()
