"""One finite, user-requested review of the ten latest tasks. No scheduled inference."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import uuid


def save(store, manifest):
    with store.connection() as c:c.execute("INSERT OR REPLACE INTO settings VALUES('recent_task_review',?)",(json.dumps(manifest),))
    (store.data/'task-reviews'/manifest['id']/'manifest.json').write_text(json.dumps(manifest,indent=2))


def prepare(store, count=10):
    import task_history as h
    if type(count) is not int or not 1<=count<=10:raise ValueError('Review 1..10 tasks at a time')
    h.init(store)
    with store.connection() as c:
        previous=c.execute("SELECT value FROM settings WHERE key='recent_task_review'").fetchone()
        if previous and json.loads(previous['value'])['status']=='running':raise ValueError('A task review is already registered; inspect its manifest before continuing')
        tasks=[dict(r) for r in c.execute('SELECT id,title,updated FROM tasks ORDER BY updated DESC,id LIMIT ?',(count,))]
    manifest={'id':uuid.uuid4().hex,'created':datetime.now(timezone.utc).isoformat(),'scope':'Latest tasks by recorded activity, frozen before inference','status':'running','task_ids':[t['id'] for t in tasks],
              'completed':0,'failed':0,'members':[dict(task_id=t['id'],title=t['title'],last_activity=t['updated'],status='pending',job_id=None) for t in tasks],
              'policy':'At most two concurrent task miners; one attempt per task, no automatic retries; source measurements independent of mining.'}
    directory=store.data/'task-reviews'/manifest['id'];directory.mkdir(parents=True,mode=0o700)
    (directory/'source-manifest.json').write_text(json.dumps({'sources':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('task_history.py','work_analytics.py','task_review.py')}},indent=2))
    save(store,manifest)
    return manifest


def run(store, manifest, progress=lambda value:None):
    import task_history as h
    import threading
    lock=threading.Lock()
    def persist():
        manifest['completed']=sum(m['status']=='completed' for m in manifest['members'])
        manifest['failed']=sum(m['status']=='failed' for m in manifest['members'])
        save(store,manifest);progress({'id':manifest['id'],'completed':manifest['completed'],'failed':manifest['failed']})
    def worker(member):
        try:
            result=h.start(store,member['task_id'],'overview')
            with lock:member.update(job_id=result['id'],status='running');persist()
            if result['status']=='unchanged':
                with store.connection() as c:source_job=c.execute('SELECT job_id FROM task_history_analyses WHERE id=?',(result['id'],)).fetchone()[0]
                with lock:member.update(status='completed',analysis_id=result['id'],job_id=source_job,reused=True);persist()
                return
            while True:
                with store.connection() as c:job=dict(c.execute('SELECT status,error,result,usage FROM task_history_jobs WHERE id=?',(result['id'],)).fetchone())
                if job['status'] not in ('queued','running'):break
                time.sleep(1)
            with lock:
                member.update(status='completed' if job['status']=='completed' else 'failed',analysis_id=job['result'],error=job['error'],usage=json.loads(job['usage']) if job['usage'] else None);persist()
        except Exception as error:
            with lock:member.update(status='failed',error=str(error));persist()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(worker,manifest['members']))
    manifest['status']='completed' if manifest['completed']==len(manifest['members']) else 'needs_review'
    manifest['finished']=datetime.now(timezone.utc).isoformat();save(store,manifest)
    return manifest
