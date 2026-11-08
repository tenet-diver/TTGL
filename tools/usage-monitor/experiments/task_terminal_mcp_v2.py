#!/usr/bin/env python3
"""Trusted stdio bridge: UID1000 container commands and own visible task records.

No host command interpolation, alternate container/user, grader access or LLM
call. Reuses local SQLite/FTS and optional reviewed local note embeddings.
"""
import argparse,hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path
from online_task_memory import OnlineMemory

def tool(name,description,properties,required=()):
 return dict(name=name,description=description,inputSchema=dict(type='object',properties=properties,required=list(required),additionalProperties=False))
TOOLS=[
 tool('terminal','Run a shell command inside this task container as its unprivileged actor. Its task workspace is writable even when the host model sandbox is read-only; determine write outcomes from actual task command results. Exact output is archived; a command exit is not a task-success verdict.',dict(command=dict(type='string'),timeout_seconds=dict(type='integer',minimum=1,maximum=180)),('command',)),
 tool('remember','Store a fallible task note, attempted approach, lesson or uncertainty with source IDs. It never becomes a verified fact merely by assertion. Superseded notes remain readable.',dict(text=dict(type='string'),source_refs=dict(type='array',items=dict(type='string')),supersedes=dict(type='array',items=dict(type='string'))),('text',)),
 tool('search_records','Search your earlier visible task records and notes. Treat matches as fallible evidence; use read_record for full source/context.',dict(query=dict(type='string'),limit=dict(type='integer',minimum=1,maximum=8)),('query',)),
 tool('read_record','Read your own retained source or full archived command stdout/stderr by source ID, with pagination. No arbitrary host paths are accepted.',dict(id=dict(type='string'),part=dict(type='string',enum=['body','stdout','stderr']),offset=dict(type='integer',minimum=0),limit=dict(type='integer',minimum=1,maximum=16000)),('id',))]
class TaskBridge:
 def __init__(self,config):
  self.config=json.loads(Path(config).read_text());self.root=Path(self.config['records']);self.root.mkdir(parents=True,exist_ok=True,mode=0o700);self.phase=Path(self.config['phase_directory']);self.phase.mkdir(parents=True,exist_ok=True,mode=0o700);self.raw=self.root/'records';self.raw.mkdir(exist_ok=True,mode=0o755);self.raw.chmod(0o755);self.boot=uuid.uuid4().hex;self.encoder=None
  if self.config['mode'] not in ('files','memory'):raise ValueError('Unregistered memory mode')
  self.memory=OnlineMemory(self.root/'memory.sqlite',self.embed if self.config['mode']=='memory' else None,self.config.get('embedding_identity','fts-only') if self.config['mode']=='memory' else 'fts-only')
 def embed(self,text):
  if self.encoder is None:
   from smallville_local_embeddings import LocalEmbeddings
   self.encoder=LocalEmbeddings(self.config['embedding_root'],self.root/'embedding-inferences.jsonl')
  try:return self.encoder(text)
  except ValueError as error:raise RuntimeError('Reviewed embedding contract failed: '+str(error)) from error
 def bootstrap(self):
  self.memory.append('instruction',self.config['instruction'],record_id='task_instruction')
 def journal(self,record):
  with (self.phase/'rpc.jsonl').open('a') as f:f.write(json.dumps(record)+'\n');f.flush();os.fsync(f.fileno())
 def closed(self):
  if (self.phase/'fatal.json').exists():return True
  counter=self.phase/'counter.json';count=json.loads(counter.read_text())['count'] if counter.exists() else 0
  if count>=self.config.get('tool_budget',40) or time.time_ns()>=self.config['close_at_ns']:return True
  temp=counter.with_suffix('.tmp');temp.write_text(json.dumps(dict(count=count+1)));temp.replace(counter);return False
 def execute(self,ident,command,timeout):
  if not isinstance(command,str) or not command or len(command)>60000:raise ValueError('Invalid command size/type')
  if type(timeout)is not int or not 1<=timeout<=180:raise ValueError('Invalid command timeout')
  start=time.perf_counter();stdout=self.raw/(ident+'.stdout.txt');stderr=self.raw/(ident+'.stderr.txt')
  with stdout.open('xb') as out,stderr.open('xb') as err:
   result=subprocess.run(['docker','exec','--user','1000:1000',self.config['container'],'timeout','-s','TERM','-k','3',str(timeout),'bash','-lc',command],stdout=out,stderr=err,timeout=timeout+15)
  text=stdout.read_text(errors='replace');errors=stderr.read_text(errors='replace')
  if stdout.stat().st_size+stderr.stat().st_size>64*1024*1024:raise RuntimeError('Recorded output quota reached; operation preserved, never retried automatically')
  metadata=dict(id=ident,kind='tool_result',command=command,exit_code=result.returncode,stdout=text[:12000],stderr=errors[:4000],stdout_characters=len(text),stderr_characters=len(errors),stdout_sha256=hashlib.sha256(stdout.read_bytes()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.read_bytes()).hexdigest(),stdout_truncated_for_model=len(text)>12000,stderr_truncated_for_model=len(errors)>4000,seconds=time.perf_counter()-start,verification_scope='Observed command execution only; not a semantic correctness/task-success label',raw_access='read_record id with part=stdout or stderr, or /app/task_history/records files')
  (self.raw/(ident+'.json')).write_text(json.dumps(metadata,indent=2))
  try:record=self.memory.append('tool_result',json.dumps(metadata,ensure_ascii=False),record_id=ident)
  except Exception as error:raise RuntimeError('Command completed; record update failed; raw outputs retained; do not re-execute automatically: '+str(error)) from error
  for p in (stdout,stderr,self.raw/(ident+'.json')):p.chmod(0o644)
  return dict(metadata,record_sha256=record['sha256'])
 def read(self,ident,part,offset,limit):
  record=self.memory.read(ident,offset,limit)
  if part=='body':return record
  if part not in ('stdout','stderr') or record['kind']!='tool_result':raise ValueError('No such raw source part')
  # Validate the full DB source before reading its immutable adjacent raw file.
  pieces=[];position=0
  while True:
   page=self.memory.read(ident,position,16000);pieces.append(page['body']);position=page['next_offset']
   if position is None:break
  meta=json.loads(''.join(pieces));p=self.raw/(ident+'.'+part+'.txt');raw=p.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=meta[part+'_sha256']:raise ValueError('Raw command source corrupted')
  text=raw.decode(errors='replace');end=min(len(text),offset+limit)
  return dict(id=ident,part=part,text=text[offset:end],total_characters=len(text),offset=offset,next_offset=end if end<len(text) else None,sha256=meta[part+'_sha256'],epistemic_status=record['epistemic_status'])
 def call(self,request):
  params=request.get('params') or {};name=params.get('name');arguments=params.get('arguments') or {};definition=next((t for t in TOOLS if t['name']==name),None)
  if not definition or not isinstance(arguments,dict) or set(arguments)-set(definition['inputSchema']['properties']) or any(k not in arguments for k in definition['inputSchema']['required']):raise ValueError('Invalid tool or arguments')
  key=hashlib.sha256(json.dumps(request['id']).encode()).hexdigest()[:24];base=self.phase/(self.boot+'-'+key);intent=base.with_suffix('.intent.json');finished=base.with_suffix('.result.json');fingerprint=hashlib.sha256(json.dumps(params,sort_keys=True).encode()).hexdigest()
  if intent.exists():
   if json.loads(intent.read_text())['request_sha256']!=fingerprint:raise ValueError('RPC identity collision')
   if finished.exists():return json.loads(finished.read_text())
   raise RuntimeError('Prior request started/uncertain; not re-executed')
  if self.closed():return dict(phase_tools_closed=True,action='Return your current evidence-backed status now. Do not retry tool calls; the harness owns the next checkpoint.',task_success_inferred=False)
  with intent.open('x') as f:json.dump(dict(name=name,request_sha256=fingerprint,at_ns=time.time_ns()),f)
  ident='event_'+self.boot+'_'+key
  try:
   self.bootstrap()
   if name=='terminal':result=self.execute(ident,arguments['command'],arguments.get('timeout_seconds',180))
   elif name=='remember':
    if not isinstance(arguments['text'],str) or not 1<=len(arguments['text'])<=6000:raise ValueError('Invalid note size')
    result=self.memory.append('agent_note',arguments['text'],arguments.get('source_refs',[]),arguments.get('supersedes',[]),record_id='note_'+ident)
   elif name=='search_records':
    requested=arguments.get('limit',8)
    if type(requested)is not int or requested<1:raise ValueError('search_records limit must be a positive integer; at most8results are returned')
    if not isinstance(arguments.get('query'),str) or not arguments['query'].strip():raise ValueError('search_records query must be a nonempty text string')
    result=self.memory.search(arguments['query'],min(requested,8));result.update(requested_limit=requested,effective_limit=min(requested,8))
   else:result=self.read(arguments['id'],arguments.get('part','body'),arguments.get('offset',0),arguments.get('limit',4000))
  except (RuntimeError,subprocess.TimeoutExpired) as error:
   (self.phase/'fatal.json').write_text(json.dumps(dict(error=type(error).__name__,message=str(error),request=str(intent),operation_may_have_started=True,no_retry=True)));raise
  with finished.open('x') as f:json.dump(result,f)
  self.journal(dict(id=request['id'],name=name,arguments=arguments,result=result));return result
 def handle(self,request):
  method=request.get('method');params=request.get('params') or {}
  if method=='initialize':return dict(protocolVersion=params.get('protocolVersion','2025-06-18'),capabilities=dict(tools=dict(listChanged=False)),serverInfo=dict(name='ttgl-task-records',version='1'))
  if method=='ping':return {}
  if method=='tools/list':return dict(tools=TOOLS)
  if method=='tools/call':
   try:return dict(content=[dict(type='text',text=json.dumps(self.call(request),ensure_ascii=False))],isError=False)
   except Exception as error:return dict(content=[dict(type='text',text=type(error).__name__+': '+str(error)[:400])],isError=True)
  raise ValueError('Unsupported MCP method')
def main():
 os.umask(0o077);p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);server=TaskBridge(p.parse_args().config)
 for line in sys.stdin:
  try:
   if len(line)>1024*1024:raise ValueError('Oversized MCP request')
   request=json.loads(line)
   if 'id' not in request:continue
   try:response=dict(jsonrpc='2.0',id=request['id'],result=server.handle(request))
   except ValueError as error:response=dict(jsonrpc='2.0',id=request['id'],error=dict(code=-32601,message=str(error)))
  except (ValueError,TypeError):response=dict(jsonrpc='2.0',id=None,error=dict(code=-32700,message='Invalid request'))
  print(json.dumps(response),flush=True)
if __name__=='__main__':main()
