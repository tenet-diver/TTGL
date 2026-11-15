"""Finite, durable, explicitly started process-analysis queue. No automatic retries."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid

import process_analysis
import task_history as history

ACTIVE = ('queued','running','stopping')
TERMINAL = ('completed','unchanged','failed','unavailable','previous_failed','uncertain','oversized')


def init(store):
    history.init(store)
    with store.connection() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS bulk_analysis_batches(id TEXT PRIMARY KEY,created REAL NOT NULL,updated REAL NOT NULL,status TEXT NOT NULL,model TEXT NOT NULL,engine TEXT NOT NULL,pid INTEGER,protocol TEXT NOT NULL,error TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS bulk_analysis_one_active ON bulk_analysis_batches((1)) WHERE status IN ('queued','running','stopping');
CREATE TABLE IF NOT EXISTS bulk_analysis_items(batch_id TEXT NOT NULL REFERENCES bulk_analysis_batches(id),task_id TEXT NOT NULL REFERENCES tasks(id),position INTEGER NOT NULL,status TEXT NOT NULL,snapshot_hash TEXT NOT NULL,snapshot TEXT NOT NULL,job_id TEXT,error TEXT,PRIMARY KEY(batch_id,task_id));
CREATE INDEX IF NOT EXISTS bulk_analysis_pending ON bulk_analysis_items(batch_id,status,position);
''')


def state(store,batch_id=None,offset=0,limit=20):
    init(store);offset,limit=int(offset),int(limit)
    if offset<0 or not 1<=limit<=100:raise ValueError('Invalid bulk analysis page')
    with store.connection() as c:
        batch=c.execute('SELECT * FROM bulk_analysis_batches '+('WHERE id=?' if batch_id else 'ORDER BY created DESC LIMIT 1'),(batch_id,) if batch_id else ()).fetchone()
        if not batch:return {'batch':None,'protocol':process_analysis.PROTOCOL,'model':os.environ.get('TTGL_TASK_MODEL','gpt-6-luna')}
        batch=dict(batch);ident=batch['id']
        counts={r['status']:r['n'] for r in c.execute('SELECT status,count(*) n FROM bulk_analysis_items WHERE batch_id=? GROUP BY status',(ident,))}
        rows=[dict(r) for r in c.execute('''SELECT i.task_id,t.title,i.status,i.job_id,i.error,j.usage,j.model FROM bulk_analysis_items i JOIN tasks t ON t.id=i.task_id
            LEFT JOIN task_history_jobs j ON j.id=i.job_id WHERE i.batch_id=? ORDER BY i.position LIMIT ? OFFSET ?''',(ident,limit,offset))]
        coverage=c.execute('''SELECT coalesce(sum(json_array_length(i.snapshot,'$.steps')),0),
            coalesce(sum(CASE WHEN i.status IN ('completed','unchanged') THEN json_array_length(i.snapshot,'$.steps') ELSE 0 END),0),
            coalesce(sum(json_extract(j.usage,'$.total_tokens')),0),
            coalesce(sum(i.job_id IS NOT NULL AND j.usage IS NULL),0)
            FROM bulk_analysis_items i LEFT JOIN task_history_jobs j ON j.id=i.job_id WHERE i.batch_id=?''',(ident,)).fetchone()
    for row in rows:row['usage']=json.loads(row['usage']) if row['usage'] else None
    total=sum(counts.values());finished=sum(counts.get(key,0) for key in TERMINAL)
    return dict(batch=batch,counts=counts,total=total,finished=finished,records=rows,
                pagination=dict(total=total,offset=offset,limit=limit,next_offset=offset+limit if offset+limit<total else None),
                coverage=dict(frozen_events=coverage[0],interpreted_events=coverage[1],known_analysis_tokens=coverage[2],jobs_missing_usage=coverage[3]),
                limitations=['One finite frozen corpus snapshot; newly arriving activity is separate. No scheduled inference or automatic retries.',
                'Outcomes, categories and intervention labels are model interpretations of bounded visible evidence, not independent grades. Long tasks use chronological blocks and sampled I/O; coverage limits are retained.',
                'Source-task measured usage stays unchanged. Analysis overhead is separate; missing usage and actual cash expense remain unknown.'])


def start(store,*,launch=True):
    init(store)
    with store.connection() as c:
        active=c.execute("SELECT id FROM bulk_analysis_batches WHERE status IN ('queued','running','stopping') LIMIT 1").fetchone()
        if active:return state(store,active['id'])
        ids=[r[0] for r in c.execute('''SELECT t.id FROM tasks t WHERE EXISTS(SELECT 1 FROM assignments a JOIN events e USING(session_id,turn_id) WHERE a.task_id=t.id) ORDER BY t.updated DESC,t.id''')]
        orphaned=c.execute('''SELECT count(*) FROM turns t WHERE EXISTS(SELECT 1 FROM events e WHERE e.session_id=t.session_id AND e.turn_id=t.turn_id)
            AND NOT EXISTS(SELECT 1 FROM assignments a WHERE a.session_id=t.session_id AND a.turn_id=t.turn_id)''').fetchone()[0]
    if orphaned:raise ValueError(f'{orphaned} unassigned turns require discovery/assignment before all-history analysis')
    if not ids:raise ValueError('No indexed tasks with source events')
    from activity_views import sources_on_disk,source_state
    known=sources_on_disk(store);items=[]
    engine=os.environ.get('TTGL_TASK_ANALYZER','codex');model=os.environ.get('TTGL_TASK_MODEL','gpt-6-luna' if engine=='codex' else '')
    if engine not in ('codex','ollama') or not model:raise ValueError('Configure an existing task analyzer/model')
    for position,task_id in enumerate(ids):
        try:
            body,_=history.snapshot(store,task_id,'all',max_steps=10000)
            body=process_analysis.snapshot(store,body)
            raw=json.dumps(body,sort_keys=True,separators=(',',':'));digest=hashlib.sha256(raw.encode()).hexdigest()
            availability=source_state({step['session_id'] for step in body['steps']},known)
            status='unavailable' if availability=='unavailable' else 'pending';job_id=None;error='Retained transcript sources unavailable' if status=='unavailable' else None
            with store.connection() as c:
                prior=c.execute("SELECT id,status FROM task_history_jobs WHERE task_id=? AND snapshot_hash=? AND operation='process' AND model=? AND engine=? ORDER BY created DESC LIMIT 1",(task_id,digest,model,engine)).fetchone()
            if prior:
                job_id=prior['id'];status='unchanged' if prior['status']=='completed' else 'uncertain' if prior['status'] in ('queued','running') else 'previous_failed'
                error=None if status=='unchanged' else 'Prior attempt retained; no automatic repeat'
        except ValueError as exc:
            body={'steps':[]};raw=json.dumps(body);digest=hashlib.sha256(raw.encode()).hexdigest();status='oversized';error=str(exc);job_id=None
        items.append((task_id,position,status,digest,raw,job_id,error))
    ident=uuid.uuid4().hex;stamp=time.time()
    directory=store.data/'bulk-analysis'/ident;directory.mkdir(parents=True,mode=0o700)
    protocol=dict(id=process_analysis.PROTOCOL,created=stamp,concurrency=2,automatic_retries=0,model=model,engine=engine,tasks=len(items),source_scope='All indexed assigned tasks with events, frozen at explicit start')
    protocol['source_sha256']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('bulk_analysis.py','task_history.py','process_analysis.py')}
    (directory/'protocol.json').write_text(json.dumps(protocol,indent=2))
    with store.connection() as c:
        c.execute('BEGIN IMMEDIATE')
        active=c.execute("SELECT id FROM bulk_analysis_batches WHERE status IN ('queued','running','stopping') LIMIT 1").fetchone()
        if active:raise ValueError('Another bulk batch started while preparing this corpus; refresh its progress')
        c.execute('INSERT INTO bulk_analysis_batches VALUES(?,?,?,?,?,?,?,?,?)',(ident,stamp,stamp,'queued',model,engine,None,json.dumps(protocol),None))
        c.executemany('INSERT INTO bulk_analysis_items VALUES(?,?,?,?,?,?,?,?)',[(ident,*row) for row in items])
        store.audit(c,'start_bulk_analysis',ident,protocol)
    if launch:
        argv=[sys.executable,str(Path(__file__).resolve()),'worker','--data',str(store.data.resolve()),'--codex-root',str(store.root.resolve()),'--batch',ident]
        with (directory/'worker.log').open('ab') as log:
            process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                                     env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','TTGL_TASK_ANALYZER':engine,'TTGL_TASK_MODEL':model})
        with store.connection() as c:c.execute('UPDATE bulk_analysis_batches SET pid=? WHERE id=?',(process.pid,ident))
    return state(store,ident)


def stop(store,batch_id):
    init(store)
    with store.connection() as c:
        c.execute("UPDATE bulk_analysis_batches SET status='stopping',updated=? WHERE id=? AND status IN ('queued','running')",(time.time(),batch_id))
    return state(store,batch_id)


def run_item(store,batch_id,item):
    ident=item['task_id']
    try:
        result=history.start(store,ident,'process',_snapshot=json.loads(item['snapshot']),_launch=False)
        if result['status']=='unchanged':
            with store.connection() as c:c.execute("UPDATE bulk_analysis_items SET status='unchanged' WHERE batch_id=? AND task_id=?",(batch_id,ident))
            return True
        if result.get('existing'):raise ValueError('Pre-existing active job observed; no duplicate execution')
        job_id=result['id']
        # A previously active job is observed, never run a second time.
        with store.connection() as c:
            c.execute("UPDATE bulk_analysis_items SET status='running',job_id=? WHERE batch_id=? AND task_id=?",(job_id,batch_id,ident))
            job=c.execute('SELECT status,snapshot_hash FROM task_history_jobs WHERE id=?',(job_id,)).fetchone()
        if job['status']!='queued' or job['snapshot_hash']!=item['snapshot_hash']:raise ValueError('Uncertain pre-existing analysis; execution stopped without repeat')
        history.run_model(store,job_id)
        with store.connection() as c:
            job=c.execute('SELECT status,error FROM task_history_jobs WHERE id=?',(job_id,)).fetchone()
            status='completed' if job['status']=='completed' else 'failed'
            c.execute('UPDATE bulk_analysis_items SET status=?,error=? WHERE batch_id=? AND task_id=?',(status,job['error'],batch_id,ident))
        return status=='completed'
    except Exception as exc:
        if str(exc).startswith('Two task analyses are already running'):
            # Capacity contention is a preparation wait, before any invocation.
            with store.connection() as c:c.execute("UPDATE bulk_analysis_items SET status='pending',error=NULL WHERE batch_id=? AND task_id=?",(batch_id,ident))
            time.sleep(1)
            return None
        with store.connection() as c:c.execute("UPDATE bulk_analysis_items SET status='failed',error=? WHERE batch_id=? AND task_id=?",(str(exc)[:500],batch_id,ident))
        return False


def worker(store,batch_id):
    init(store)
    with (store.data/'bulk-analysis.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('A bulk worker already owns this database') from None
        return _worker(store,batch_id)


def _worker(store,batch_id):
    with store.connection() as c:
        batch=c.execute('SELECT * FROM bulk_analysis_batches WHERE id=?',(batch_id,)).fetchone()
        if not batch or batch['status'] not in ACTIVE:return
        if batch['status']=='stopping':
            c.execute("UPDATE bulk_analysis_batches SET status='stopped',updated=? WHERE id=?",(time.time(),batch_id));return
        if c.execute("SELECT 1 FROM bulk_analysis_items WHERE batch_id=? AND status IN ('dispatching','running') LIMIT 1",(batch_id,)).fetchone():
            c.execute("UPDATE bulk_analysis_batches SET status='stopped',error='Uncertain prior worker activity; inspect before continuation',updated=? WHERE id=?",(time.time(),batch_id));return
        c.execute("UPDATE bulk_analysis_batches SET status='running',pid=?,updated=? WHERE id=?",(os.getpid(),time.time(),batch_id))
    failures=0;pending={}
    with ThreadPoolExecutor(max_workers=2) as pool:
        while True:
            with store.connection() as c:
                status=c.execute('SELECT status FROM bulk_analysis_batches WHERE id=?',(batch_id,)).fetchone()[0]
                busy=c.execute("SELECT count(*) FROM task_history_jobs WHERE status IN ('queued','running')").fetchone()[0]
                while status=='running' and failures<3 and len(pending)<2 and busy<2:
                    item=c.execute("SELECT * FROM bulk_analysis_items WHERE batch_id=? AND status='pending' ORDER BY position LIMIT 1",(batch_id,)).fetchone()
                    if not item:break
                    c.execute("UPDATE bulk_analysis_items SET status='dispatching' WHERE batch_id=? AND task_id=?",(batch_id,item['task_id']))
                    pending[pool.submit(run_item,store,batch_id,dict(item))]=item['task_id'];busy+=1
            if not pending:
                with store.connection() as c:
                    remaining=c.execute("SELECT count(*) FROM bulk_analysis_items WHERE batch_id=? AND status='pending'",(batch_id,)).fetchone()[0]
                if not remaining or status!='running' or failures>=3:break
                time.sleep(1);continue
            done,_=wait(pending,timeout=1,return_when=FIRST_COMPLETED)
            for future in done:
                ok=future.result()
                if ok is not None:failures=0 if ok else failures+1
                pending.pop(future)
            with store.connection() as c:c.execute('UPDATE bulk_analysis_batches SET updated=? WHERE id=?',(time.time(),batch_id))
    with store.connection() as c:
        states={r[0]:r[1] for r in c.execute('SELECT status,count(*) FROM bulk_analysis_items WHERE batch_id=? GROUP BY status',(batch_id,))}
        status='stopped' if states.get('pending') else 'completed_with_errors' if any(states.get(key) for key in TERMINAL if key not in ('completed','unchanged')) else 'completed'
        error='Stopped after three consecutive failed analyses; attempts retained, no retries' if failures>=3 else None
        c.execute('UPDATE bulk_analysis_batches SET status=?,error=?,updated=? WHERE id=?',(status,error,time.time(),batch_id))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['worker']);parser.add_argument('--data',type=Path,required=True);parser.add_argument('--codex-root',type=Path,required=True);parser.add_argument('--batch',required=True)
    args=parser.parse_args();os.umask(0o077)
    from workspace import Store
    worker(Store(args.data,args.codex_root,'http://localhost:3000'),args.batch)


if __name__=='__main__':main()
