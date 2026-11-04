#!/usr/bin/env python3
"""Local Codex usage companion. Originals are read-only; no inference or cloud upload."""
import argparse, collections, hashlib, json, os, re, sqlite3, subprocess, threading, time, contextlib, traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE=Path(__file__).resolve().parent
UUID=re.compile(r'[0-9a-f]{8}-[0-9a-f-]{27,}')
MAX_LINE=32*1024*1024

def now(): return datetime.now(timezone.utc).isoformat()
@contextlib.contextmanager
def connect(path):
 c=sqlite3.connect(path,timeout=30);c.row_factory=sqlite3.Row
 try:
  with c:yield c
 finally:c.close()

def init(path):
 with connect(path) as c:
  c.execute('PRAGMA journal_mode=WAL')
  c.executescript('''CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,project TEXT,cwd TEXT,version TEXT,started TEXT,last TEXT,path TEXT,fork TEXT);
CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY,size INTEGER,mtime INTEGER,error TEXT,scanned TEXT);
CREATE TABLE IF NOT EXISTS tools(id TEXT PRIMARY KEY,sid TEXT,name TEXT,ts TEXT,bytes INTEGER,duration REAL,failed INTEGER,hash TEXT,line INTEGER,family TEXT);
CREATE INDEX IF NOT EXISTS tools_sid ON tools(sid);
CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY,choice TEXT,updated TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,proposal TEXT,choice TEXT,at TEXT);
''')

def lines(path):
 proc=None
 if str(path).endswith('.zst'):
  proc=subprocess.Popen(['zstd','-dc','--',str(path)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL);stream=proc.stdout
 else:stream=path.open('rb')
 try:
  n=0
  while True:
   b=stream.readline(MAX_LINE+1)
   if not b: break
   n+=1
   if len(b)>MAX_LINE:
    while b and not b.endswith(b'\n'):b=stream.readline(MAX_LINE+1)
    yield n,None;continue
   if not b.endswith(b'\n'):break # a currently-written tail is retried next scan
   try:yield n,json.loads(b)
   except (ValueError,UnicodeError):yield n,None
 finally:
  stream.close()
  if proc:
   rc=proc.wait()
   if rc:raise ValueError('zstd decompression failed')

def size_text(x):
 if x is None:return None,None
 s=x if isinstance(x,str) else json.dumps(x,ensure_ascii=False)
 b=s.encode();return len(b),hashlib.sha256(b).hexdigest()

def family(command):
 if isinstance(command,list):command=' '.join(str(x) for x in command)
 command=str(command or '')
 for key,pattern in [('tests',r'\b(pytest|jest|vitest|xcodebuild|npm test|swift test|unittest)\b'),('search',r'\b(rg|grep|find)\b'),('read',r'\b(cat|sed|head|tail|read_file)\b'),('git',r'\bgit\b')]:
  if re.search(pattern,command):return key
 return 'command'

def parse(path):
 meta=None;native={};fallback={};requests={};bad=0;last='';native_seen=False
 for line,r in lines(path):
  if not r:bad+=1;continue
  p=r.get('payload') or {};typ=r.get('type');ts=r.get('timestamp','')
  if typ=='session_meta' and meta is None:meta=p;continue
  if not meta:continue
  sid=meta.get('id','');started=meta.get('timestamp','')
  # Replayed parent history must not become child tool work.
  if ts and started and ts<started:continue
  last=max(last,ts)
  if typ=='event_msg' and p.get('type')=='item_completed':
   if p.get('thread_id') and p['thread_id']!=sid:continue
   i=p.get('item') or {};t=i.get('type','');ident=i.get('id')
   if t not in ['CommandExecution','McpToolCall','DynamicToolCall','FileChange','WebSearch','ImageView','Extension']:continue
   native_seen=True
   if not ident:continue
   name=('shell' if t=='CommandExecution' else (str(i.get('server',''))+'.'+str(i.get('tool',''))).strip('.') if t=='McpToolCall' else str(i.get('kind') or t))
   output=i.get('aggregated_output') if t=='CommandExecution' else i.get('result')
   b,h=size_text(output)
   a,z=p.get('started_at_ms'),p.get('completed_at_ms');dur=(z-a)/1000 if isinstance(a,(int,float)) and isinstance(z,(int,float)) and z>=a else None
   code=i.get('exit_code');status=i.get('status');failed=int(code!=0) if isinstance(code,int) else int(status in ['failed','error']) if status in ['completed','failed','error'] else None
   if t=='McpToolCall' and isinstance(output,dict) and output.get('isError') is not None:failed=int(output['isError'])
   native[ident]=(ident,sid,name,ts,b,dur,failed,h,line,family(i.get('command')) if t=='CommandExecution' else 'mcp' if t=='McpToolCall' else 'other')
  if typ=='response_item':
   t=p.get('type');ident=p.get('call_id')
   if not ident:continue
   if t in ['function_call','custom_tool_call']:requests[ident]=(p.get('name','unknown'),ts,p.get('arguments',p.get('input','')))
   elif t in ['function_call_output','custom_tool_call_output']:
    name,start,args=requests.get(ident,('unknown',ts,''));b,h=size_text(p.get('output'))
    fallback[ident]=(ident,sid,name,ts,b,None,None,h,line,'legacy')
 if not meta:raise ValueError('No session metadata')
 return meta,last,list(native.values() if native_seen else fallback.values()),bad

class Monitor:
 def __init__(self,root,data):
  self.root=root;self.data=data;self.db=data/'monitor.sqlite';self.state={'phase':'Starting','done':0,'total':0,'errors':0,'last_scan':None};self.lock=threading.Lock();init(self.db)
  self.ccstatus='Using saved baseline' if (data/'ccusage-sessions.json').exists() else 'Preparing first report';self.report_lock=threading.Lock()
 def discover(self):
  selected={}
  for root in [self.root/'archived_sessions',self.root/'sessions']:
   for f in root.rglob('*.jsonl*'):
    if not (f.name.endswith('.jsonl') or f.name.endswith('.jsonl.zst')):continue
    key=f.name.removesuffix('.zst');old=selected.get(key)
    if old is None or (old.name.endswith('.zst') and f.name.endswith('.jsonl')) or root.name=='sessions' and old.parent!=f.parent:selected[key]=f
  return sorted(selected.values(),key=lambda f:f.stat().st_mtime,reverse=True)
 def scan(self):
  while True:
   try:
    fs=self.discover();self.state.update(phase='Importing tool evidence',total=len(fs),done=0)
    for idx,f in enumerate(fs):
     stat=f.stat()
     with connect(self.db) as c:old=c.execute('SELECT * FROM files WHERE path=?',(str(f),)).fetchone()
     if not old or old['size']!=stat.st_size or old['mtime']!=stat.st_mtime_ns:
      try:
       meta,last,tools,bad=parse(f);sid=meta['id'];cwd=meta.get('cwd','');project=Path(cwd).name or 'Unknown'
       with connect(self.db) as c:
        c.execute('INSERT OR REPLACE INTO sessions VALUES(?,?,?,?,?,?,?,?)',(sid,project,cwd,meta.get('cli_version'),meta.get('timestamp'),last,str(f),str(meta.get('forked_from_id') or '')))
        c.execute('DELETE FROM tools WHERE sid=?',(sid,))
        c.executemany('INSERT OR IGNORE INTO tools VALUES(?,?,?,?,?,?,?,?,?,?)',tools)
        c.execute('INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)',(str(f),stat.st_size,stat.st_mtime_ns,f'{bad} malformed/oversize lines' if bad else None,now()))
      except Exception as e:
       with connect(self.db) as c:c.execute('INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)',(str(f),stat.st_size,stat.st_mtime_ns,type(e).__name__+': '+str(e)[:160],now()))
     self.state['done']=idx+1
    with connect(self.db) as c:self.state['errors']=c.execute('SELECT count(*) FROM files WHERE error IS NOT NULL').fetchone()[0]
    self.state.update(phase='Watching Codex sessions',last_scan=now())
   except Exception as e:
    traceback.print_exc();self.state.update(phase='Scan error: '+type(e).__name__+': '+str(e)[:120])
   time.sleep(20)
 def reports(self):
  while True:
   try:
    for view in ['session','daily']:
     self.ccstatus='Refreshing '+view+' usage'
     cmd=['npx','--no','--offline','ccusage@20.0.48','codex',view,'--json','--offline','--no-cost']
     if view=='daily':cmd+=['--timezone','Europe/Amsterdam']
     # Refuse package installation and network fetching during refresh.
     # The pinned, previously reviewed ccusage must already be present.
     # No credentials are read or changed; only local rollouts are read.
     r=subprocess.run(cmd,capture_output=True,timeout=180,env={**os.environ,'CODEX_HOME':str(self.root)})
     if r.returncode:raise ValueError('ccusage exited '+str(r.returncode))
     obj=json.loads(r.stdout)
     if (view=='session' and 'sessions' not in obj) or (view=='daily' and 'daily' not in obj):raise ValueError('Unsupported ccusage schema')
     dest=self.data/('ccusage-sessions.json' if view=='session' else 'ccusage-daily.json');tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(obj));tmp.replace(dest)
    self.ccstatus='Current · refresh every 3 minutes'
   except Exception as e:self.ccstatus='Report refresh failed: '+str(e)+'; retained last successful report'
   time.sleep(180)
 def report(self):
  p=self.data/'ccusage-sessions.json';d=json.loads(p.read_text()) if p.exists() else {'sessions':[],'totals':{}}
  p2=self.data/'ccusage-daily.json';daily=json.loads(p2.read_text()) if p2.exists() else {}
  with connect(self.db) as c:
   meta={r['id']:dict(r) for r in c.execute('SELECT * FROM sessions')}
   tools=[dict(r) for r in c.execute('SELECT name,count(*) calls,sum(bytes) bytes,avg(duration) duration,sum(failed) failures,count(duration) timed,count(failed) known_outcomes FROM tools GROUP BY name ORDER BY bytes DESC LIMIT 30')]
   decisions={r['id']:dict(r) for r in c.execute('SELECT * FROM decisions')}
   evidence=c.execute('SELECT count(*),sum(bytes),count(bytes),count(duration) FROM tools').fetchone()
   files=c.execute('SELECT count(*),sum(size) FROM files').fetchone()
   history=[dict(r) for r in c.execute('SELECT * FROM events ORDER BY id DESC LIMIT 50')]
  sessions=[];models=collections.defaultdict(lambda:dict(total=0,input=0,cached=0,output=0))
  for row in d.get('sessions',[]):
   match=UUID.search(row.get('sessionFile',''));sid=match.group() if match else row['sessionId'];m=meta.get(sid,{})
   sessions.append({**row,'id':sid,'project':m.get('project','Importing project…'),'cwd':m.get('cwd',''),'version':m.get('version'),'source':Path(m.get('path','')).name,'fork':m.get('fork','')})
   for name,u in row.get('models',{}).items():
    for dest,src in [('total','totalTokens'),('input','inputTokens'),('cached','cacheReadTokens'),('output','outputTokens')]:models[name][dest]+=u.get(src,0)
  sessions.sort(key=lambda x:x.get('lastActivity',''),reverse=True)
  daily_total=sum(x.get('totalTokens',0) for x in daily.get('daily',[]))
  reconciliation={'session_minus_total':sum(x.get('totalTokens',0) for x in sessions)-d.get('totals',{}).get('totalTokens',0),'daily_minus_session':daily_total-d.get('totals',{}).get('totalTokens',0),'note':'Session and daily reports are captured sequentially while Codex remains active. Residuals may reflect observation timing or source/accounting gaps; not silently corrected.'}
  suggestions=self.suggestions()
  for s in suggestions:s['decision']=decisions.get(s['id'],{}).get('choice','pending')
  return dict(reconciliation=reconciliation,daily_asof=datetime.fromtimestamp(p2.stat().st_mtime,timezone.utc).isoformat() if p2.exists() else None,totals=d.get('totals',{}),sessions=sessions,models=[{'name':k,**v} for k,v in sorted(models.items(),key=lambda x:-x[1]['total'])],daily=daily.get('daily',[]),tools=tools,suggestions=suggestions,history=history,state=dict(self.state),report_status=self.ccstatus,report_asof=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat() if p.exists() else None,evidence=dict(calls=evidence[0],bytes=evidence[1],sized=evidence[2],timed=evidence[3],files=files[0],source_bytes=files[1]),capabilities={'adapter':'ccusage 20.0.48 + TTGL local tool adapter v1','roots':[str(self.root/'sessions'),str(self.root/'archived_sessions')],'billing':'Unknown; no charges or savings inferred','suggestion_engine':'Deterministic evidence rules; no background model calls','limitations':['Token reports reconstruct retained logs, not account-wide quota.','Tool output bytes are retained output, not provider tokens or guaranteed model-facing text.','Nested command/MCP executions use native completion IDs; legacy fallback calls lack timing.','Usage refreshes every 3 minutes; tool scans every 20 seconds.','Suggestions are opportunities, not implemented optimizations.']})
 def suggestions(self):
  out=[]
  with connect(self.db) as c:
   # stable fingerprint suppresses a declined recurring opportunity, independently of wording
   groups=list(c.execute('SELECT name,count(*) n,sum(bytes) b FROM tools WHERE bytes>32000 GROUP BY name HAVING count(*)>=3 ORDER BY b DESC LIMIT 4'))
   for r in groups:
    ev=[dict(x) for x in c.execute('SELECT id,sid,line,bytes,ts FROM tools WHERE name=? AND bytes>32000 ORDER BY bytes DESC LIMIT 3',(r['name'],))]
    out.append(dict(id='large-'+hashlib.sha256(r['name'].encode()).hexdigest()[:12],title='Bound large results from '+r['name'],recipe='OPT-031 / OPT-033' if '.' in r['name'] else 'Output scope review',observation=f"{r['n']} completed calls exceed 32 KB; {r['b']:,} retained output bytes in this group.",proposal='Inspect the largest calls, then prepare a tool-specific field selection, range, or result limit. Keep failure diagnostics and required verification visible.',risk='Output trimming can hide relevant evidence. A concrete change and diagnostic checks are needed before testing.',evidence=ev,bytes=r['b'],status='Prepare change',savings=None))
   r=c.execute('SELECT count(*) n,sum(b) b FROM (SELECT hash,count(*) n,max(bytes) b FROM tools WHERE bytes>8000 AND hash IS NOT NULL GROUP BY sid,name,hash HAVING count(*)>=3)').fetchone()
   if r['n']:
    ev=[dict(x) for x in c.execute('SELECT min(id) id,sid,min(line) line,max(bytes) bytes,count(*) repeats FROM tools WHERE bytes>8000 GROUP BY sid,name,hash HAVING count(*)>=3 ORDER BY repeats DESC LIMIT 3')]
    out.append(dict(id='repeated-output-v1',title='Review repeatedly returned identical output',recipe='OPT-045 candidate',observation=f"{r['n']} session/tool/output groups return the same >8 KB result at least three times.",proposal='Inspect repeated results and reuse still-valid evidence where appropriate. Revalidation and deliberate polling may be necessary; identical output alone does not prove a redundant read.',risk='Stale evidence can invalidate conclusions. Verify source changes and freshness requirements.',evidence=ev,bytes=r['b'],status='Investigate',savings=None))
  review_path=self.data/'agent-reviews.json'
  if review_path.exists():
   try:
    reviews=json.loads(review_path.read_text())
    if isinstance(reviews,list):
     ids={r.get('id') for r in reviews if isinstance(r,dict)}
     out=[r for r in reviews if isinstance(r,dict) and all(k in r for k in ['id','title','observation','proposal','risk','evidence','recipe','status'])]+[r for r in out if r['id'] not in ids]
   except (ValueError,OSError):pass
  return out[:5]

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def send(self,obj,status=200,content='application/json'):
  b=(json.dumps(obj).encode() if content=='application/json' else obj);self.send_response(status);self.send_header('Content-Type',content);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'self'");self.end_headers();self.wfile.write(b)
 def valid_host(self):return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
 def do_GET(self):
  if not self.valid_host():return self.send({'error':'Invalid host'},403)
  p=urlparse(self.path).path
  if p in ['/api/report','/api/agent-context']:
   r=self.server.monitor.report()
   if p=='/api/agent-context':r={k:r[k] for k in ['totals','suggestions','evidence','state','capabilities','reconciliation','report_asof']}
   return self.send(r)
  if p in ['/','/app.js','/style.css']:
   name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[p];return self.send((HERE/name).read_bytes(),content={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[p])
  self.send({'error':'Not found'},404)
 def do_POST(self):
  origin=self.headers.get('Origin');expected=[f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']
  if not self.valid_host() or origin not in expected:return self.send({'error':'Same-origin browser request required'},403)
  if self.path!='/api/decision':return self.send({'error':'Not found'},404)
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n>4096:raise ValueError()
   v=json.loads(self.rfile.read(n));ident=v['id'];choice=v['choice']
   if choice not in ['review','declined','deferred'] or ident not in {s['id'] for s in self.server.monitor.suggestions()}:raise ValueError()
   with connect(self.server.monitor.db) as c:
    old=c.execute('SELECT choice FROM decisions WHERE id=?',(ident,)).fetchone()
    if not old or old['choice']!=choice:
     c.execute('INSERT OR REPLACE INTO decisions VALUES(?,?,?)',(ident,choice,now()));c.execute('INSERT INTO events(proposal,choice,at) VALUES(?,?,?)',(ident,choice,now()))
   self.send({'ok':True,'implementation':'not_started'})
  except (ValueError,KeyError):self.send({'error':'Invalid decision'},400)

def main():
 a=argparse.ArgumentParser();a.add_argument('--codex-home',type=Path,default=Path.home()/'.codex');a.add_argument('--data',type=Path,required=True);a.add_argument('--port',type=int,default=8766);v=a.parse_args();v.data.mkdir(parents=True,exist_ok=True);os.chmod(v.data,0o700)
 m=Monitor(v.codex_home,v.data)
 for f in [m.scan,m.reports]:threading.Thread(target=f,daemon=True).start()
 s=ThreadingHTTPServer(('127.0.0.1',v.port),Handler);s.monitor=m;print(f'TTGL Usage Monitor: http://127.0.0.1:{v.port}',flush=True);s.serve_forever()
if __name__=='__main__':main()
