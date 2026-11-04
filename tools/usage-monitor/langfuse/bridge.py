#!/usr/bin/env python3
"""Metadata-only Codex analytics -> local Langfuse OTLP/JSON. No model calls.

Reuses TTGL's read-only rollout reader. Three disjoint datasets/environments:
usage-tools (actual calls), usage-daily-v3 (day/model increments), usage-sessions-v2
(lifetime session/model counters). Never sum usage-daily and usage-sessions.
"""
import argparse, base64, collections, errno, hashlib, importlib.util, json, os, re
import shlex, sqlite3, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ttgl_monitor',HERE.parent/'server.py')
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)
VERSION='ttgl-analytics-v1'
NATIVE={'CommandExecution','McpToolCall','DynamicToolCall','FileChange','WebSearch','ImageView','Extension'}
SAFE_COMMANDS=set('rg grep find cat sed head tail git pytest python python3 node npm npx pnpm yarn docker swift xcodebuild cargo go curl ls du df zstd codex sleep'.split())
SAFE_ENUM={'view':{'compact','full','summary','evidence'},'format':{'json','text','markdown'},'output_format':{'json','text'}}
SAFE_NUM={'limit','maxResults','max_results','max_output_tokens','timeout_ms','yield_time_ms','offset','page','pageSize'}

def digest(s,n=32):return hashlib.sha256(s.encode()).hexdigest()[:n]
def nanos(s):
 if isinstance(s,(int,float)):return int(s*1_000_000)
 return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()*1_000_000_000)
def iso(ns):return datetime.fromtimestamp(ns/1e9,timezone.utc).isoformat()
def jsontext(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def bucket(n):return '0' if not n else '<1KB' if n<1024 else '1-8KB' if n<8192 else '8-32KB' if n<32768 else '32-128KB' if n<131072 else '>=128KB'

def arg_summary(args,command=None):
 """No raw values, paths, queries, source code or credentials leave this function."""
 if isinstance(args,str):
  try:args=json.loads(args)
  except ValueError:args={'opaque_text':args}
 keys=sorted(k for k in (args or {}) if isinstance(k,str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,47}',k))[:24] if isinstance(args,dict) else []
 result={'argument_keys':','.join(keys) or '(none)','argument_bytes_bucket':bucket(len(jsontext(args).encode()) if args is not None else 0)}
 parts=['keys='+result['argument_keys']]
 if isinstance(args,dict):
  for k in keys:
   v=args[k]
   if k in SAFE_ENUM and isinstance(v,str) and v in SAFE_ENUM[k]:parts.append(k+'='+v)
   elif k in SAFE_NUM and isinstance(v,(int,float)) and not isinstance(v,bool) and 0<=v<=1000000:parts.append(k+'='+str(v))
 if command is not None:
  cmd=' '.join(map(str,command)) if isinstance(command,list) else str(command)
  result['command_family']=monitor.family(cmd)
  try:words=shlex.split(cmd)
  except ValueError:words=[]
  # Only emit allowlisted command names; never arbitrary executable paths/values.
  names=[]
  for w in words:
   if w in SAFE_COMMANDS and w not in names:names.append(w)
  result['command_programs']=','.join(names[:8]) or 'other'
  parts.extend(['family='+result['command_family'],'programs='+result['command_programs']])
 result['argument_pattern']='; '.join(parts)[:700]
 return result

def tool_records(path):
 meta=None;native={};fallback={};requests={};native_seen=False;bad=0
 for line,r in monitor.lines(path):
  if not r:bad+=1;continue
  p=r.get('payload') or {};typ=r.get('type');ts=r.get('timestamp','')
  if typ=='session_meta' and meta is None:meta=p;continue
  if not meta:continue
  sid=meta.get('id','');started=meta.get('timestamp','')
  if ts and started and ts<started:continue
  if typ=='event_msg' and p.get('type')=='item_completed':
   if p.get('thread_id') and p['thread_id']!=sid:continue
   i=p.get('item') or {};kind=i.get('type');ident=i.get('id')
   if kind not in NATIVE:continue
   native_seen=True
   if not ident:continue
   name='shell' if kind=='CommandExecution' else (str(i.get('server',''))+'.'+str(i.get('tool',''))).strip('.') if kind=='McpToolCall' else str(i.get('kind') or kind)
   output=i.get('aggregated_output') if kind=='CommandExecution' else i.get('result')
   size,_=monitor.size_text(output)
   a,z=p.get('started_at_ms'),p.get('completed_at_ms')
   known=isinstance(a,(int,float)) and isinstance(z,(int,float)) and z>=a and a>0
   # Unknown duration is a zero-width event, always excluded from timing charts.
   end=nanos(z) if known else nanos(ts or started)
   start=nanos(a) if known else end
   code=i.get('exit_code');status=i.get('status')
   failure=code!=0 if isinstance(code,int) else status in ['failed','error'] if status in ['completed','failed','error'] else None
   if kind=='McpToolCall' and isinstance(output,dict) and output.get('isError') is not None:failure=bool(output['isError'])
   args=i.get('arguments');command=i.get('command') if kind=='CommandExecution' else None
   summary=arg_summary(args,command)
   native[ident]={'id':ident,'sid':sid,'name':name,'start':start,'end':end,'line':line,'timing_known':known,'output_bytes':size,'failed':failure,'kind':kind,**summary}
  if typ=='response_item':
   kind=p.get('type');ident=p.get('call_id')
   if not ident:continue
   if kind in ['function_call','custom_tool_call']:
    requests[ident]=(p.get('name','unknown'),p.get('arguments',p.get('input')),ts)
   elif kind in ['function_call_output','custom_tool_call_output']:
    name,args,start=requests.get(ident,('unknown',None,ts));size,_=monitor.size_text(p.get('output'));end=nanos(ts or started)
    fallback[ident]={'id':ident,'sid':sid,'name':name,'start':end,'end':end,'line':line,'timing_known':False,'output_bytes':size,'failed':None,'kind':'legacy',**arg_summary(args)}
 if not meta:raise ValueError('No session metadata')
 return meta,list(native.values() if native_seen else fallback.values()),bad

def attr(k,v):
 if isinstance(v,bool):value={'boolValue':v}
 elif isinstance(v,int):value={'intValue':str(v)}
 elif isinstance(v,float):value={'doubleValue':v}
 elif isinstance(v,list):value={'arrayValue':{'values':[{'stringValue':str(x)} for x in v]}}
 else:value={'stringValue':str(v)}
 return {'key':k,'value':value}

def span(trace,key,name,typ,start,end,env,metadata,session=None,parent=None,usage=None,model=None):
 attrs={'langfuse.observation.type':typ,'langfuse.environment':env,'langfuse.trace.name':metadata.get('trace_name','Usage analytics'),'langfuse.version':VERSION,'langfuse.trace.tags':['ttgl-analytics',metadata.get('record_kind','unknown')], 'langfuse.user.id':'local-ttgl'}
 if session:attrs['langfuse.session.id']=session
 for k,v in metadata.items():
  if v is not None:attrs['langfuse.observation.metadata.'+k]=v
 if usage is not None:attrs['langfuse.observation.usage_details']=jsontext(usage)
 if model:attrs['langfuse.observation.model.name']=model
 out={'traceId':digest(trace),'spanId':digest(key,16),'name':name,'kind':1,'startTimeUnixNano':str(start),'endTimeUnixNano':str(end),'attributes':[attr(k,v) for k,v in attrs.items()]}
 if parent:out['parentSpanId']=digest(parent,16)
 if metadata.get('failed') is True:out['status']={'code':2,'message':'Recorded tool failure'}
 return out

def tool_spans(meta,records):
 sid=meta['id'];days=collections.defaultdict(list)
 for r in records:days[iso(r['end'])[:10]].append(r)
 for day,rows in days.items():
  trace=VERSION+':tools:'+sid+':'+day;root=trace+':root'
  common={'record_kind':'tool_execution','project':Path(meta.get('cwd','')).name or 'Unknown','trace_name':'Native tool activity','source':'native Codex completion events','token_attribution':'not_measured'}
  for r in rows:
   md={**common,**{k:v for k,v in r.items() if k not in ['id','sid','name','start','end']}}
   yield span(trace,sid+':tool:'+r['id'],r['name'],'tool',r['start'],r['end'],'usage-tools',md,sid,root)
   # A derived zero-duration EVENT makes patterns countable in native charts;
   # metadata can be filtered but is not a group-by dimension in Langfuse v4.
   pattern_name=r['name']+' | '+r['argument_pattern']
   yield span(trace,sid+':pattern:'+r['id'],pattern_name,'event',r['end'],r['end'],'usage-tools',{**md,'record_kind':'argument_pattern','measurement':'derived argument shape, no raw values','timing_known':False},sid,sid+':tool:'+r['id'])
  yield span(trace,root,'Native tool activity','agent',min(r['start'] for r in rows),max(r['end'] for r in rows),'usage-tools',{**common,'record_kind':'tool_activity_root','timing_scope':'first-to-last tool interval; includes gaps; not additive'},sid)

def usage_buckets(row):
 values=[row.get(k,0) for k in ['inputTokens','cacheReadTokens','cacheCreationTokens','outputTokens','reasoningOutputTokens','totalTokens']]
 if any(not isinstance(x,int) or x<0 for x in values):raise ValueError('Invalid usage counters')
 fresh,cached,creation,output,reasoning,total=values
 if fresh+cached+creation+output!=total:raise ValueError('Non-reconciling usage counters')
 result={'input':fresh,'input_cached_tokens':cached,'input_cache_creation_tokens':creation,'output':output,'total':total}
 # Some retained model summaries have inconsistent reasoning subsets. Keep the
 # reconciled output total, omit the invalid split, and flag it in metadata.
 if reasoning<=output:result.update(output=output-reasoning,output_reasoning_tokens=reasoning)
 return result

class Exporter:
 def __init__(self,credentials,state):
  self.config=json.loads(credentials.read_text());url=urllib.parse.urlparse(self.config['base_url'])
  if url.scheme!='http' or url.hostname not in ['localhost','127.0.0.1']:raise ValueError('Only local Langfuse is allowed')
  self.db=sqlite3.connect(state/'export.sqlite',timeout=30)
  self.db.executescript("CREATE TABLE IF NOT EXISTS sent(id TEXT PRIMARY KEY,hash TEXT); CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY,size INTEGER,mtime INTEGER); CREATE TABLE IF NOT EXISTS cursors(id TEXT PRIMARY KEY,counters TEXT); CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY,hash TEXT,span TEXT,cursor TEXT);")
  self.buffer=[];self.pending=[];self.exported=0;self.skipped=0
  if self.db.execute('SELECT count(*) FROM outbox').fetchone()[0]:self.reconcile()
 def request(self,path,data=None):
  auth=base64.b64encode((self.config['public_key']+':'+self.config['secret_key']).encode()).decode()
  req=urllib.request.Request(self.config['base_url']+path,data=jsontext(data).encode() if data is not None else None,headers={'Content-Type':'application/json','Authorization':'Basic '+auth,'x-langfuse-ingestion-version':'4'})
  with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read() or '{}')
 def commit(self,rows):
  with self.db:
   for key,h,raw,cursor in rows:
    self.db.execute('INSERT OR IGNORE INTO sent VALUES(?,?)',(key,h))
    if cursor:
     ident,counters=json.loads(cursor);self.db.execute('INSERT OR REPLACE INTO cursors VALUES(?,?)',(ident,jsontext(counters)))
    self.db.execute('DELETE FROM outbox WHERE id=?',(key,))
 def reconcile(self):
  # A lost HTTP response is not proof of failed ingestion. Check the backend;
  # never replay an uncertain batch into immutable v4 observations.
  rows=self.db.execute('SELECT id,hash,span,cursor FROM outbox').fetchall()
  for i in range(0,len(rows),512):
   batch=rows[i:i+512];spans=[json.loads(r[2]) for r in batch]
   params={'fromStartTime':iso(min(int(s['startTimeUnixNano']) for s in spans)-1000000000),'toStartTime':iso(max(int(s['endTimeUnixNano']) for s in spans)+1000000000),'limit':1000,'filter':jsontext([{'column':'id','type':'stringOptions','operator':'any of','value':[s['spanId'] for s in spans]}])}
   found=self.request('/api/public/v2/observations?'+urllib.parse.urlencode(params)).get('data',[])
   counts=collections.Counter(r['id'] for r in found)
   if any(counts[s['spanId']]!=1 for s in spans):raise RuntimeError('Uncertain prior OTLP batch: backend verification incomplete; automatic replay blocked')
   self.commit(batch)
 def add(self,s,cursor=None):
  key=s['traceId']+s['spanId'];h=digest(json.dumps(s,sort_keys=True))
  # v4 is immutable: even changed attributes must not re-send an existing id.
  if self.db.execute('SELECT 1 FROM sent WHERE id=?',(key,)).fetchone():self.skipped+=1;return
  self.buffer.append(s);self.pending.append((key,h,jsontext(s),jsontext(cursor) if cursor else None))
  if len(self.buffer)>=512:self.flush()
 def flush(self):
  if not self.buffer:return
  data={'resourceSpans':[{'resource':{'attributes':[attr('service.name','ttgl-codex-analytics')]},'scopeSpans':[{'scope':{'name':VERSION},'spans':self.buffer}]}]}
  # Persist intent before network IO. An ambiguous response blocks retries.
  with self.db:self.db.executemany('INSERT INTO outbox VALUES(?,?,?,?)',self.pending)
  try:result=self.request('/api/public/otel/v1/traces',data)
  except urllib.error.URLError as exc:
   # Connection refusal occurs before a request is delivered. Docker may still
   # be starting at login; this definite non-delivery is safe to retry.
   if isinstance(exc.reason,ConnectionRefusedError) or getattr(exc.reason,'errno',None)==errno.ECONNREFUSED:
    with self.db:self.db.executemany('DELETE FROM outbox WHERE id=?',[(row[0],) for row in self.pending])
   raise
  if result.get('partialSuccess',{}).get('rejectedSpans',0) not in [0,'0']:raise ValueError('OTLP partial rejection; batch requires reconciliation')
  self.commit(self.pending)
  self.exported+=len(self.buffer);self.buffer=[];self.pending=[]
  time.sleep(.02)
 def file_done(self,path,stat):
  self.flush()
  with self.db:self.db.execute('INSERT OR REPLACE INTO files VALUES(?,?,?)',(str(path),stat.st_size,stat.st_mtime_ns))
 def unchanged(self,path,stat):
  return self.db.execute('SELECT 1 FROM files WHERE path=? AND size=? AND mtime=?',(str(path),stat.st_size,stat.st_mtime_ns)).fetchone() is not None
 def usage(self,report,kind):
  # Append positive counter increments, never re-send growing snapshots.
  # v2 environments quarantine the initial snapshot canaries from analytics.
  for row in report[kind]:
   sid=None
   if kind=='daily':
    key=row['date'];when=int(datetime.fromisoformat(key).replace(tzinfo=timezone.utc).timestamp()*1e9)
   else:
    match=monitor.UUID.search(row.get('sessionFile',''));sid=match.group() if match else row['sessionId'];key=sid;when=nanos(row['lastActivity'])
   for model,u in row['models'].items():
    usage_buckets(u)
    # Reasoning is an output subset, not another independently increasing bucket.
    counters={'input':u['inputTokens'],'input_cached_tokens':u['cacheReadTokens'],'input_cache_creation_tokens':u.get('cacheCreationTokens',0),'output':u['outputTokens']}
    revision_prefix='usage-v3:' if kind=='daily' else 'usage-v2:'
    ident=revision_prefix+kind+':'+key+':'+model
    old=self.db.execute('SELECT counters FROM cursors WHERE id=?',(ident,)).fetchone();old=json.loads(old[0]) if old else {k:0 for k in counters}
    delta={k:v-old[k] for k,v in counters.items()}
    if any(v<0 for v in delta.values()):raise ValueError('Source counter decrease: reconcile before export')
    if not sum(delta.values()):continue
    delta['total']=sum(delta.values());revision=digest(jsontext(counters));trace=ident+':'+revision
    md={'record_kind':kind+'_usage_delta','source':'ccusage 20.0.48 recorded counters','measurement':'measured_model_usage_increment','time_scope':'Europe/Amsterdam calendar day' if kind=='daily' else 'session lifetime increments; timestamp is last activity','token_attribution':'model_only','trace_name':'Daily measured usage' if kind=='daily' else 'Session lifetime usage','timing_known':False,'reported_reasoning_subset':u.get('reasoningOutputTokens',0),'reasoning_subset_valid':u.get('reasoningOutputTokens',0)<=u['outputTokens'],'pricing':'Langfuse model-price estimate; subscription cash unknown'}
    # A zero-duration generation is a counter record, not a latency sample.
    if kind=='daily':md.update(aggregation_day=key,timestamp_semantics='UTC calendar-date label for Europe/Amsterdam daily bucket; not a model-call timestamp')
    env='usage-daily-v3' if kind=='daily' else 'usage-sessions-v2'
    generation=span(trace,trace,model+' recorded usage increment','generation',when,when,env,md,sid,usage=delta,model=model)
    self.add(generation,(ident,counters))
  self.flush()

def run(args):
 args.state.mkdir(parents=True,exist_ok=True);os.chmod(args.state,0o700)
 exporter=Exporter(args.credentials,args.state);status={'version':VERSION,'started':monitor.now(),'files':0,'changed_files':0,'tool_calls':0,'errors':[]}
 m=monitor.Monitor.__new__(monitor.Monitor);m.root=args.codex_root
 fs=m.discover()
 for idx,path in enumerate(fs):
  stat=path.stat();status['files']+=1
  if exporter.unchanged(path,stat):continue
  try:
   meta,records,bad=tool_records(path)
   if bad:raise ValueError(str(bad)+' malformed or oversize lines')
   for s in tool_spans(meta,records):exporter.add(s)
   exporter.file_done(path,stat);status['changed_files']+=1;status['tool_calls']+=len(records)
  except Exception as e:
   status['errors'].append({'file':path.name,'error':type(e).__name__+': '+str(e)[:120]})
   # A transport failure leaves buffered data unsent; fail instead of mixing receipts.
   if isinstance(e,(urllib.error.URLError,TimeoutError)):raise
  if idx%20==0:print(jsontext({'progress':idx+1,'files':len(fs),'exported':exporter.exported}),flush=True)
 for kind in ['daily','sessions']:
  report=json.loads((args.monitor_data/('ccusage-'+kind+'.json')).read_text())
  rows=report['daily' if kind=='daily' else 'sessions']
  total=sum(row['totalTokens'] for row in rows)
  if total!=report['totals']['totalTokens']:raise ValueError('Report aggregate mismatch')
  # Validate the entire snapshot before sending any of its model counters.
  for row in rows:
   if sum(usage_buckets(u)['total'] for u in row.get('models',{}).values())!=row['totalTokens']:raise ValueError('Report model mismatch')
  exporter.usage(report,kind)
  status[kind]={'rows':len(rows),'total_tokens':total,'source_mtime':datetime.fromtimestamp((args.monitor_data/('ccusage-'+kind+'.json')).stat().st_mtime,timezone.utc).isoformat()}
 status.update(finished=monitor.now(),exported=exporter.exported,unchanged=exporter.skipped)
 (args.state/'status.json').write_text(json.dumps(status,indent=2));(args.state/'error.json').write_text(jsontext({'state':'clear','at':monitor.now()}));print(jsontext(status),flush=True)
 exporter.db.close()
 return status

def main():
 p=argparse.ArgumentParser();p.add_argument('--codex-root',type=Path,default=Path.home()/'.codex');p.add_argument('--monitor-data',type=Path,required=True);p.add_argument('--credentials',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--watch',action='store_true');args=p.parse_args()
 os.umask(0o077)
 # Only one exporter may own receipts, including manual backfills.
 import fcntl
 args.state.mkdir(parents=True,exist_ok=True);lock=(args.state/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while True:
  try:run(args)
  except Exception as e:
   error={'error':type(e).__name__,'detail':str(e)[:300],'at':monitor.now()};(args.state/'error.json').write_text(jsontext(error));print(jsontext(error),flush=True)
   if not args.watch:raise
  if not args.watch:break
  time.sleep(180)
if __name__=='__main__':main()
