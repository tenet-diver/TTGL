"""Evidence-first adaptation using existing SQLite FTS5 and local BGE.

Exact source chunks remain authoritative. No importance/reflection model calls;
this is a separate candidate, not the original Smallville ranking.
"""
import hashlib,json,math,sqlite3,time
from pathlib import Path
from memory_retrieval import search
class EvidenceMemory:
 def __init__(self,path,embed):self.path=Path(path);self.embed=embed
 def build(self,episodes):
  start=time.perf_counter()
  if self.path.exists():raise ValueError('Never overwrite a memory index')
  with sqlite3.connect(self.path) as db:
   db.execute('CREATE TABLE records(id TEXT PRIMARY KEY,body TEXT,sha TEXT)')
   db.execute('CREATE TABLE chunks(episode TEXT,offset INTEGER,body TEXT,vector TEXT,sha TEXT)')
   for e in episodes:
    db.execute('INSERT INTO records VALUES(?,?,?)',(e['id'],e['body'],hashlib.sha256(e['body'].encode()).hexdigest()))
    for offset in range(0,len(e['body']),1200):
     body=e['body'][offset:offset+1200];v=self.embed(body)
     db.execute('INSERT INTO chunks VALUES(?,?,?,?,?)',(e['id'],offset,body,json.dumps(v),hashlib.sha256(body.encode()).hexdigest()))
  return dict(seconds=time.perf_counter()-start,records=len(episodes),index_bytes=self.path.stat().st_size,model_calls=0,local_embedding_calls='one per1200-character exact chunk; plus one per query')
 def query(self,question):
  start=time.perf_counter();q=self.embed(question);norm=math.sqrt(sum(x*x for x in q));rank=[]
  with sqlite3.connect(self.path) as db:
   episodes=[dict(id=r[0],body=r[1]) for r in db.execute('SELECT id,body FROM records ORDER BY id')]
   for episode,offset,body,vector,sha in db.execute('SELECT episode,offset,body,vector,sha FROM chunks'):
    v=json.loads(vector);score=sum(a*b for a,b in zip(q,v))/(norm*math.sqrt(sum(x*x for x in v)))
    rank.append(dict(episode=episode,offset=offset,body=body,sha256=sha,score=score,method='dense'))
  lexical=search(episodes,question,limit=4,budget=12000)
  hits=[dict(x,method='fts') for x in lexical];used={(x['episode'],x['offset']) for x in hits}
  for x in sorted(rank,key=lambda x:(-x['score'],x['episode'],x['offset'])):
   if (x['episode'],x['offset']) in used:continue
   hits.append(x);used.add((x['episode'],x['offset']))
   if len(hits)>=8:break
  return dict(hits=hits,seconds=time.perf_counter()-start)
