"""Incremental self-hosted task records and fallible evidence-linked notes.

SQLite FTS5 indexes exact source text. Optional local dense index covers explicit
agent notes/instructions, not every transient tool log. No scoring/reflection LLM.
Raw evidence is immutable; notes never become verified facts by assertion.
"""
import array,contextlib,hashlib,json,math,os,re,sqlite3,time,uuid
from pathlib import Path
SCHEMA='''
CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,kind TEXT NOT NULL,body TEXT NOT NULL,sha TEXT NOT NULL,created_ns INTEGER NOT NULL,refs TEXT NOT NULL,supersedes TEXT NOT NULL,active INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS chunks(record_id TEXT NOT NULL,offset INTEGER NOT NULL,body TEXT NOT NULL,sha TEXT NOT NULL,vector BLOB,PRIMARY KEY(record_id,offset));
CREATE VIRTUAL TABLE IF NOT EXISTS words USING fts5(body,record_id UNINDEXED,offset UNINDEXED);
'''
class OnlineMemory:
 def __init__(self,path,embed=None,identity='fts-only'):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700);self.embed=embed
  fd=os.open(self.path,os.O_CREAT|os.O_RDWR,0o600);os.close(fd)
  with self.connection() as db:
   db.executescript(SCHEMA);value=json.dumps(dict(schema=1,embedding_identity=identity,dense=embed is not None,chunk_characters=1200))
   old=db.execute("SELECT value FROM config WHERE key='identity'").fetchone()
   if old and old[0]!=value:raise ValueError('Memory namespace/model configuration mismatch')
   db.execute("INSERT OR IGNORE INTO config VALUES('identity',?)",(value,))
 @contextlib.contextmanager
 def connection(self):
  db=sqlite3.connect(self.path,timeout=20);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON')
  try:
   with db:yield db
  finally:db.close()
 @staticmethod
 def vector(values):
  v=array.array('f',values)
  if not v or any(not math.isfinite(x) for x in v) or sum(x*x for x in v)==0:raise ValueError('Invalid local embedding')
  return v
 def append(self,kind,body,refs=(),supersedes=(),record_id=None):
  if kind not in ('instruction','tool_result','agent_note'):raise ValueError('Unsupported source kind')
  if not isinstance(body,str) or not body or len(body)>1024*1024:raise ValueError('Source size/type invalid')
  refs=list(refs);supersedes=list(supersedes)
  if len(refs)>16 or len(supersedes)>16 or any(not isinstance(x,str) for x in refs+supersedes):raise ValueError('Invalid evidence links')
  ident=record_id or ('record_'+uuid.uuid4().hex);digest=hashlib.sha256(body.encode()).hexdigest()
  with self.connection() as db:
   old=db.execute('SELECT * FROM records WHERE id=?',(ident,)).fetchone()
   if old:
    if (old['kind'],old['body'],json.loads(old['refs']),json.loads(old['supersedes']))!=(kind,body,refs,supersedes):raise ValueError('Record identity collision')
    return self.read(ident)
   for ref in refs+supersedes:
    r=db.execute('SELECT kind FROM records WHERE id=?',(ref,)).fetchone()
    if not r:raise ValueError('Evidence outside this namespace')
    if ref in supersedes and (kind!='agent_note' or r['kind']!='agent_note'):raise ValueError('Cannot supersede raw evidence')
  chunks=[];dims=None;start=time.perf_counter()
  for offset in range(0,len(body),1200):
   text=body[offset:offset+1200];v=None
   if self.embed is not None and kind in ('instruction','agent_note'):
    values=self.vector(self.embed(text));dims=len(values)
    if chunks and any(x[4] is not None and len(x[4])!=len(values.tobytes()) for x in chunks):raise ValueError('Embedding dimensions changed within record')
    v=values.tobytes()
   chunks.append((ident,offset,text,hashlib.sha256(text.encode()).hexdigest(),v))
  with self.connection() as db:
   if dims:
    previous=db.execute("SELECT value FROM config WHERE key='dimensions'").fetchone()
    if previous and int(previous[0])!=dims:raise ValueError('Embedding dimension mismatch')
    db.execute("INSERT OR IGNORE INTO config VALUES('dimensions',?)",(str(dims),))
   db.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,1)',(ident,kind,body,digest,time.time_ns(),json.dumps(refs),json.dumps(supersedes)))
   db.executemany('INSERT INTO chunks VALUES(?,?,?,?,?)',chunks)
   db.executemany('INSERT INTO words VALUES(?,?,?)',[(r[2],r[0],r[1]) for r in chunks])
   for old in supersedes:db.execute('UPDATE records SET active=0 WHERE id=?',(old,))
  result=self.read(ident);result['index_seconds']=time.perf_counter()-start;return result
 def read(self,ident,offset=0,limit=16000):
  if type(offset)is not int or offset<0 or type(limit)is not int or not 1<=limit<=16000:raise ValueError('Invalid source range')
  with self.connection() as db:r=db.execute('SELECT * FROM records WHERE id=?',(ident,)).fetchone()
  if not r:raise ValueError('Record outside this namespace')
  if hashlib.sha256(r['body'].encode()).hexdigest()!=r['sha']:raise ValueError('Raw source corrupted')
  end=min(len(r['body']),offset+limit)
  return dict(id=ident,kind=r['kind'],body=r['body'][offset:end],offset=offset,next_offset=end if end<len(r['body']) else None,total_characters=len(r['body']),sha256=r['sha'],refs=json.loads(r['refs']),supersedes=json.loads(r['supersedes']),active=bool(r['active']),epistemic_status='agent_assertion_not_semantically_verified' if r['kind']=='agent_note' else 'recorded_visible_source_not_a_truth_label')
 def search(self,query,limit=8,budget=12000):
  if not isinstance(query,str) or not query.strip() or len(query)>6000 or type(limit)is not int or not 1<=limit<=8:raise ValueError('Invalid memory query')
  def validate_hit(row):
   exact=self.read(row['record_id'],int(row['offset']),len(row['body']))
   if exact['body']!=row['body']:raise ValueError('Index/source chunk mismatch')
  start=time.perf_counter();terms=list(dict.fromkeys(re.findall(r'\w+',query)))[:24];lex=[];dense=[]
  with self.connection() as db:
   if terms:
    expr=' OR '.join('"'+x.replace('"','""')+'"' for x in terms)
    lex=[dict(r) for r in db.execute('SELECT w.record_id,w.offset,w.body,bm25(words) AS score FROM words w JOIN records r ON r.id=w.record_id WHERE words MATCH ? AND r.active=1 ORDER BY score,w.record_id,w.offset LIMIT ?',(expr,limit))]
   if self.embed:
    q=self.vector(self.embed(query));norm=math.sqrt(sum(x*x for x in q))
    for r in db.execute('SELECT c.* FROM chunks c JOIN records r ON c.record_id=r.id WHERE r.active=1 AND c.vector IS NOT NULL'):
     v=array.array('f');v.frombytes(r['vector'])
     if len(v)!=len(q):raise ValueError('Query/index embedding mismatch')
     score=sum(a*b for a,b in zip(q,v))/(norm*math.sqrt(sum(x*x for x in v)));dense.append(dict(record_id=r['record_id'],offset=r['offset'],body=r['body'],score=score))
  dense.sort(key=lambda r:(-r['score'],r['record_id'],r['offset']))
  ordered=lex if not self.embed else lex[:4]+dense
  hits=[];seen=set();used=0
  for r in ordered:
   key=(r['record_id'],r['offset'])
   if key in seen or used+len(r['body'])>budget:continue
   validate_hit(r);parent=self.read(r['record_id']);seen.add(key);used+=len(r['body']);hits.append(dict(id=key[0],offset=key[1],text=r['body'],sha256=hashlib.sha256(r['body'].encode()).hexdigest(),kind=parent['kind'],epistemic_status=parent['epistemic_status'],refs=parent['refs']))
   if len(hits)==limit:break
  # If dense notes are sparse, exact lexical records fill remaining slots.
  if self.embed and len(hits)<limit:
   for r in lex[4:]:
    key=(r['record_id'],r['offset'])
    if key in seen or used+len(r['body'])>budget:continue
    validate_hit(r);p=self.read(key[0]);hits.append(dict(id=key[0],offset=key[1],text=r['body'],kind=p['kind'],epistemic_status=p['epistemic_status'],refs=p['refs'],sha256=hashlib.sha256(r['body'].encode()).hexdigest()));seen.add(key);used+=len(r['body'])
    if len(hits)==limit:break
  return dict(hits=hits,seconds=time.perf_counter()-start,remote_model_calls=0,raw_access='read_record with the returned source ID and offsets')
