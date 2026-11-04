#!/usr/bin/env python3
"""Estimated visible-context attribution; measured counters remain authoritative.

No claim of provider-verified cache membership. Visible text is weighted using the
already installed o200k_base tokenizer, suffix-aligned to measured input; unlogged
prefix is a separate unknown bucket. Oversized/inconsistent reconstructions are
unallocated. No raw text or argument values are exported or persisted here.
"""
import argparse,bisect,collections,hashlib,importlib.util,json,math,os,re,sqlite3,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('context_bridge',HERE/'bridge.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
ENCODER="const rl=require('readline').createInterface({input:process.stdin});const e=require('tiktoken').get_encoding('o200k_base');rl.on('line',l=>{try{const s=JSON.parse(l);console.log(JSON.stringify({n:e.encode(s,[],[]).length}))}catch(x){console.log(JSON.stringify({error:'tokenizer_failed'}))}});"
UNKNOWN='Unknown/unlogged prefix (estimated residual)'
UNRESOLVED='Unattributed input (reconstruction unavailable)'
OUTPUT='Model response output (measured)'

class Tokenizer:
 def __init__(self,db):self.db=db;self.proc=None;db.execute('CREATE TABLE IF NOT EXISTS text_weights(hash TEXT PRIMARY KEY,n INTEGER)')
 def count(self,text):
  if not text:return 0
  key=hashlib.sha256(text.encode()).hexdigest();old=self.db.execute('SELECT n FROM text_weights WHERE hash=?',(key,)).fetchone()
  if old:return old[0]
  if self.proc is None:self.proc=subprocess.Popen(['docker','exec','-i','-w','/app/worker','ttgl-langfuse-langfuse-worker-1','node','--max-old-space-size=256','-e',ENCODER],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
  self.proc.stdin.write(json.dumps(text)+'\n');self.proc.stdin.flush();line=self.proc.stdout.readline()
  if not line:raise RuntimeError('Local tokenizer unavailable; no remote fallback')
  value=json.loads(line)
  if 'n' not in value:raise RuntimeError('Local text tokenization failed')
  self.db.execute('INSERT OR IGNORE INTO text_weights VALUES(?,?)',(key,value['n']));return value['n']
 def close(self):
  if self.proc:
   self.proc.stdin.close();self.proc.wait(timeout=15)

class Context:
 def __init__(self):self.length=0;self.parts={};self.totals=collections.Counter()
 def add(self,group,n):
  if n<=0:return
  self.length+=n;self.totals[group]+=n
  ends,sums,lengths=self.parts.setdefault(group,([],[],[]));ends.append(self.length);sums.append(self.totals[group]);lengths.append(n)
 def snapshot(self):return (self,self.length,dict(self.totals))
 def prefix(self,group,q):
  ends,sums,lengths=self.parts[group];idx=bisect.bisect_right(ends,q);total=sums[idx-1] if idx else 0
  if idx<len(ends):total+=max(0,min(lengths[idx],q-(ends[idx]-lengths[idx])))
  return total

def allocate(snapshot,input_tokens,cached_tokens):
 if snapshot is None or snapshot[1]>input_tokens:return {UNRESOLVED:(input_tokens-cached_tokens,cached_tokens)}
 ctx,size,totals=snapshot;head=input_tokens-size;boundary=max(0,cached_tokens-head)
 result={UNKNOWN:(head-min(head,cached_tokens),min(head,cached_tokens))}
 for group,n in totals.items():
  cached=ctx.prefix(group,boundary);result[group]=(n-cached,cached)
 assert sum(x[0] for x in result.values())==input_tokens-cached_tokens
 assert sum(x[1] for x in result.values())==cached_tokens
 return result

def message_text(p):
 content=p.get('content',[])
 if isinstance(content,str):return content
 if isinstance(content,list):return '\n'.join(str(x.get('text','')) for x in content if isinstance(x,dict) and x.get('type') in ['input_text','output_text','text'])
 return ''

def native_source(i):
 if i.get('type')=='CommandExecution':return 'shell / '+b.runtime.shell_operation(i)
 server=str(i.get('server','')).removeprefix('codex_apps.');tool=str(i.get('tool',''));args=i.get('arguments')
 if isinstance(args,str):
  try:args=json.loads(args)
  except ValueError:args={}
 if tool in ['executeRead','executeWrite'] and isinstance(args,dict) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]{0,79}',str(args.get('name',''))):tool=args['name']
 name=(server+'.'+tool).strip('.')
 if isinstance(args,dict) and args.get('view') in ['compact','full','summary','evidence']:name+=' / '+args['view']
 return name or 'unresolved tool'

def declared_source(name,args):
 if name not in ['exec','js','multi_tool_use.parallel']:return 'Tool output / '+name+' (direct)'
 code=args if isinstance(args,str) else json.dumps(args)
 calls=set(re.findall(r'\btools\.([A-Za-z_][A-Za-z0-9_]*)\s*\(',code))
 if len(calls)==1:
  call=next(iter(calls));call='shell / command request' if call=='exec_command' else 'shell / poll or stdin request' if call=='write_stdin' else call.removeprefix('mcp__codex_apps__').removeprefix('mcp__').replace('__','.')
  return 'Tool output / '+call+' (inferred wrapped return)'
 return 'Tool output / mixed or unresolved wrapper'

def fragments(item):
 if item.get('type')=='CommandExecution':return [item.get('aggregated_output')] if isinstance(item.get('aggregated_output'),str) else []
 result=item.get('result') or {};values=[]
 if isinstance(result,dict):
  for part in result.get('content',[]):
   if isinstance(part,dict) and part.get('type')=='text' and isinstance(part.get('text'),str):values.append(part['text'])
 return values

def split_sources(text,candidates):
 # Partition only unique, exactly retained long fragments. Do not apportion a
 # batch by raw child-output size: a caller may print only part of a result.
 owners=collections.defaultdict(set)
 for source,pieces in candidates:
  for piece in pieces:
   if len(piece)>=1024:
    owners[piece].add(source);owners[json.dumps(piece,ensure_ascii=False)[1:-1]].add(source)
 matches=[]
 for piece,sources in owners.items():
  if len(sources)!=1:continue
  start=text.find(piece)
  if start>=0 and text.find(piece,start+1)<0:matches.append((start,start+len(piece),next(iter(sources))))
 selected=[]
 for match in sorted(matches,key=lambda x:-(x[1]-x[0])):
  if all(match[1]<=old[0] or match[0]>=old[1] for old in selected):selected.append(match)
 if not selected:return []
 result=[];pos=0
 for start,end,source in sorted(selected):
  if start>pos:result.append(('Tool output / unmatched wrapper content',text[pos:start]))
  result.append(('Tool output / '+source+' (exact retained fragment)',text[start:end]));pos=end
 if pos<len(text):result.append(('Tool output / unmatched wrapper content',text[pos:]))
 return result

class Parser:
 def __init__(self,tokenizer,expected):
  self.t=tokenizer;self.expected=expected;self.ctx=Context();self.snap=None;self.model=None;self.meta=None;self.prev=None;self.seen=set();self.calls={};self.active=None;self.children=[];self.child_fragments=[];self.active_start=None;self.timestamp=None;self.measured=collections.defaultdict(collections.Counter);self.allocated=collections.defaultdict(lambda:collections.defaultdict(collections.Counter));self.daily=collections.defaultdict(lambda:collections.defaultdict(lambda:collections.defaultdict(collections.Counter)));self.stamp=None;self.metered=0;self.exceeded=0
 def append(self,p,history=False):
  kind=p.get('type');role=p.get('role')
  if not history and (kind in ['function_call','custom_tool_call','reasoning'] or kind=='message' and role=='assistant') and self.snap is None:self.snap=self.ctx.snapshot()
  if kind=='message':
   text=message_text(p)
   if role in ['system','developer']:group='Recorded system/developer instructions (estimated)'
   elif role=='user':group='Recorded injected instructions/environment (estimated)' if any(x in text for x in ['<environment_context>','<user_instructions>','<skills_instructions>','# AGENTS.md']) else 'User conversation (estimated)'
   else:group='Assistant message history (estimated)'
   self.ctx.add(group,self.t.count(text))
  elif kind in ['function_call','custom_tool_call']:
   args=p.get('arguments',p.get('input',''));self.calls[p.get('call_id')]=(p.get('name','unknown'),args);self.active=p.get('call_id');self.active_start=b.nanos(self.timestamp) if self.timestamp else None;self.children=[];self.child_fragments=[]
   self.ctx.add('Tool-call argument history (estimated)',self.t.count(str(p.get('name',''))+' '+(args if isinstance(args,str) else json.dumps(args))))
  elif kind in ['function_call_output','custom_tool_call_output']:
   name,args=self.calls.get(p.get('call_id'),('unknown',''));sources=set(self.children) if p.get('call_id')==self.active else set()
   source='Tool output / '+next(iter(sources))+' (single native child; inferred)' if len(sources)==1 else 'Tool output / mixed native tool batch (unresolved split)' if len(sources)>1 else declared_source(name,args)
   out=p.get('output','');text=out if isinstance(out,str) else json.dumps(out,ensure_ascii=False)
   # Image/blob encodings are not model-facing text tokens.
   if 'data:image/' not in text:
    parts=split_sources(text,self.child_fragments) if p.get('call_id')==self.active else []
    for label,part in parts or [(source,text)]:self.ctx.add(label,self.t.count(part))
   self.active=None;self.children=[];self.child_fragments=[]
 def charge(self,usage,cumulative,ident,eligible):
  if cumulative and cumulative==self.prev:return
  if cumulative:self.prev=cumulative
  if not eligible or ident in self.seen:return
  self.seen.add(ident)
  model=self.model or (next(iter(self.expected['models'])) if len(self.expected['models'])==1 else 'unknown-model')
  I,C,O=usage.get('input_tokens'),usage.get('cached_input_tokens',0),usage.get('output_tokens')
  if not all(isinstance(n,int) and n>=0 for n in [I,C,O]) or C>I:return
  self.measured[model].update(input=I-C,cached=C,output=O)
  allocation=allocate(self.snap,I,C);self.exceeded+=int(self.snap is None or self.snap[1]>I);self.metered+=1
  for group,(fresh,cached) in allocation.items():self.allocated[model][group].update(input=fresh,cached=cached)
  self.allocated[model][OUTPUT].update(output=O)
  stamp=self.stamp or self.expected.get('lastActivity')
  day=datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')).date().isoformat() if stamp else 'unknown-date'
  for group,(fresh,cached) in allocation.items():self.daily[model][day][group].update(input=fresh,cached=cached)
  self.daily[model][day][OUTPUT].update(output=O);self.snap=None
 def parse(self,path):
  cutoff=self.expected.get('lastActivity','')
  for line,r in b.monitor.lines(path):
   if not r:continue
   p=r.get('payload') or {};kind=r.get('type');ts=r.get('timestamp','');self.stamp=ts or self.expected.get('lastActivity')
   if kind=='session_meta' and self.meta is None:self.meta=p;continue
   if not self.meta:continue
   if cutoff and ts and ts>cutoff:continue
   eligible=not ts or not self.meta.get('timestamp') or ts>=self.meta['timestamp']
   if kind=='turn_context':self.model=p.get('model',self.model)
   elif kind=='response_item':self.timestamp=ts;self.append(p)
   elif kind=='compacted':
    self.ctx=Context();self.snap=None
    replacement=p.get('replacement_history')
    if isinstance(replacement,list):
     for item in replacement:self.append(item,True)
    else:self.ctx.add('Compaction summary (estimated)',self.t.count(str(p.get('message',''))))
   elif kind=='event_msg' and p.get('type')=='item_completed' and self.active:
    i=p.get('item') or {}
    if i.get('type') in ['CommandExecution','McpToolCall'] and (not p.get('thread_id') or p['thread_id']==self.meta['id']) and self.active_start is not None and isinstance(p.get('started_at_ms'),(int,float)) and b.nanos(p['started_at_ms'])>=self.active_start-1_000_000_000:
     self.children.append(native_source(i));self.child_fragments.append((native_source(i),fragments(i)))
   elif kind=='token_usage_record':
    if p.get('thread_id') and p['thread_id']!=self.meta['id']:continue
    self.charge(p.get('usage') or {},p.get('thread_token_usage'),p.get('response_id') or 'native:'+str(line),eligible)
   elif kind=='event_msg' and p.get('type')=='token_count':
    info=p.get('info') or {};cum=info.get('total_token_usage')
    if not cum or cum==self.prev:continue
    previous=self.prev or {k:0 for k in cum};delta={k:val-previous.get(k,0) for k,val in cum.items() if isinstance(val,int)}
    if any(delta.get(k,-1)<0 for k in ['input_tokens','cached_input_tokens','output_tokens']):self.prev=cum;self.snap=None;continue
    self.charge(delta,cum,'legacy:'+str(line),eligible)
  return self

def result_rows(parser,policy):
 rows={};reconciled=[]
 for model,u in parser.expected['models'].items():
  expected={'input':u['inputTokens']+u.get('cacheCreationTokens',0),'cached':u['cacheReadTokens'],'output':u['outputTokens']}
  measured=dict(parser.measured.get(model,{}));match=all(measured.get(k,0)==v for k,v in expected.items())
  chosen=policy.get(model)
  if chosen is None:chosen='reconciled' if match else 'unreconciled';policy[model]=chosen
  if chosen=='reconciled' and not match:raise ValueError('Previously reconciled session changed; wait for source/report alignment')
  if chosen=='reconciled':rows[model]={(day,group):counts for day,parts in parser.daily[model].items() for group,counts in parts.items()};reconciled.append(model)
  else:
   day=datetime.fromisoformat(parser.expected['lastActivity'].replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Amsterdam')).date().isoformat()
   day=policy.setdefault('_unreconciled_days',{}).setdefault(model,day)
   rows[model]={(day,UNRESOLVED):collections.Counter(input=expected['input'],cached=expected['cached']),(day,OUTPUT):collections.Counter(output=expected['output'])}
  for bucket,n in expected.items():assert sum(v.get(bucket,0) for v in rows[model].values())==n
 return rows,reconciled

def export_rows(e,sid,row,rows):
 when=b.nanos(row['lastActivity'])
 for model,groups in rows.items():
  for (day,group),counters in groups.items():
   when=int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()*1e9)
   current={k:int(counters.get(k,0)) for k in ['input','cached','output']};ident='context-estimate-v2:'+sid+':'+model+':'+day+':'+group
   old=e.db.execute('SELECT counters FROM cursors WHERE id=?',(ident,)).fetchone();previous=json.loads(old[0]) if old else {k:0 for k in current};delta={k:v-previous[k] for k,v in current.items()}
   if any(v<0 for v in delta.values()):raise ValueError('Attribution revision decreased a bucket; no immutable re-ingestion')
   if not sum(delta.values()):continue
   key=ident+':'+b.digest(b.jsontext(current));usage={'input':delta['input'],'input_cached_tokens':delta['cached'],'output':delta['output'],'total':sum(delta.values())}
   md={'record_kind':'context_contribution_estimate','method':'suffix-aligned visible transcript weighted with o200k_base','measurement':'estimated allocation of measured model counters','confidence':'conditional; provider cache boundaries and exact rendered requests unavailable','source_group':group,'scope':'model-call calendar day (Europe/Amsterdam); unresolved totals use a fixed first-import last-activity day','aggregation_day':day,'model_prices':'Langfuse price scenario; not subscription cash','hidden_context':'unknown residual kept separate','raw_content_exported':False,'trace_name':'Estimated input sources'}
   s=b.span(key,key,group,'generation',when,when,'usage-context-estimates-v2',md,sid,usage=usage,model=model)
   e.add(s,(ident,current))
 e.flush()

def run(args):
 args.state.mkdir(parents=True,exist_ok=True);os.chmod(args.state,0o700);e=b.Exporter(args.credentials,args.state)
 e.db.executescript('CREATE TABLE IF NOT EXISTS context_files_v2(sid TEXT PRIMARY KEY,fingerprint TEXT,policy TEXT,report TEXT);');tokenizer=Tokenizer(e.db)
 source=json.loads((args.monitor_data/'ccusage-sessions.json').read_text());expected={}
 for row in source['sessions']:
  match=b.monitor.UUID.search(row.get('sessionFile',''));expected[match.group() if match else row['sessionId']]=row
 m=b.monitor.Monitor.__new__(b.monitor.Monitor);m.root=args.codex_root;status={'expected_sessions':len(expected),'started':b.monitor.now(),'files_seen':0,'processed':0,'errors':[],'source_total_tokens':source['totals']['totalTokens']}
 try:
  for path in m.discover():
   # Source metadata is already indexed by the primary read-only monitor.
   match=b.monitor.UUID.search(path.name);sid=match.group() if match else None
   if sid not in expected:continue
   status['files_seen']+=1;row=expected[sid];fingerprint=b.digest(json.dumps(row,sort_keys=True));old=e.db.execute('SELECT fingerprint,policy FROM context_files_v2 WHERE sid=?',(sid,)).fetchone()
   if old and old[0]==fingerprint:continue
   try:
    parser=Parser(tokenizer,row).parse(path);policy=json.loads(old[1]) if old else {}
    for model in row['models']:
     if model not in policy.get('_unreconciled_days',{}):
      prefix='context-estimate-v2:'+sid+':'+model+':'
      anchors=[x[0][len(prefix):].split(':',1)[0] for x in e.db.execute('SELECT id FROM cursors WHERE id LIKE ?',(prefix+'%:'+UNRESOLVED,))]
      if anchors:policy.setdefault('_unreconciled_days',{})[model]=min(anchors)
    rows,known=result_rows(parser,policy);export_rows(e,sid,row,rows)
    report={'models_reconciled':known,'metered_responses':parser.metered,'unallocatable_responses':parser.exceeded,'measured':dict(parser.measured)}
    with e.db:e.db.execute('INSERT OR REPLACE INTO context_files_v2 VALUES(?,?,?,?)',(sid,fingerprint,json.dumps(policy),json.dumps(report)))
    status['processed']+=1
   except Exception as ex:
    if isinstance(ex,(BrokenPipeError,ConnectionError,b.urllib.error.URLError)) or 'tokenizer' in str(ex).lower():raise
    status['errors'].append({'session':sid,'error':type(ex).__name__+': '+str(ex)[:160]})
   if status['processed']%10==0:print(b.jsontext({'processed':status['processed'],'files_seen':status['files_seen'],'exported':e.exported}),flush=True)
  status.update(finished=b.monitor.now(),exported=e.exported,represented_sessions=e.db.execute('SELECT count(*) FROM context_files_v2').fetchone()[0])
  dashboard_spec=importlib.util.spec_from_file_location('context_dashboard',HERE/'context_dashboard.py');dashboard=importlib.util.module_from_spec(dashboard_spec);dashboard_spec.loader.exec_module(dashboard)
  dashboard.configure(args.credentials,args.state.parent/'context-widgets.json',{'represented_sessions':status['represented_sessions'],'expected_sessions':len(expected)})
  (args.state/'status.json').write_text(json.dumps(status,indent=2));(args.state/'error.json').unlink(missing_ok=True);print(b.jsontext(status),flush=True)
 finally:tokenizer.close();e.db.close()
 return status

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--codex-root',type=Path,default=Path.home()/'.codex');p.add_argument('--monitor-data',type=Path,required=True);p.add_argument('--credentials',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--watch',action='store_true');a=p.parse_args();os.umask(0o077);a.state.mkdir(parents=True,exist_ok=True)
 import fcntl
 lock=(a.state/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while True:
  try:run(a)
  except Exception as ex:
   error={'error':type(ex).__name__,'detail':str(ex)[:200],'at':b.monitor.now()};(a.state/'error.json').write_text(json.dumps(error));print(b.jsontext(error),flush=True)
   if not a.watch:raise
  if not a.watch:break
  time.sleep(180)
