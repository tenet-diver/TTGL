"""User-curated task names, step groups and a bounded evidence timeline. Stdlib."""
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import time
import uuid


def init(store):
    with store.connection() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS task_names(task_id TEXT PRIMARY KEY REFERENCES tasks(id),source TEXT NOT NULL,source_prompt TEXT NOT NULL,model TEXT,updated REAL NOT NULL);
CREATE TABLE IF NOT EXISTS task_step_groups(id TEXT PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks(id),title TEXT NOT NULL,activity TEXT NOT NULL,summary TEXT NOT NULL,snapshot TEXT NOT NULL,snapshot_hash TEXT NOT NULL,created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS task_step_group_members(group_id TEXT NOT NULL REFERENCES task_step_groups(id),event_id TEXT NOT NULL REFERENCES events(id),position INTEGER NOT NULL,PRIMARY KEY(group_id,event_id));
CREATE INDEX IF NOT EXISTS task_step_groups_task ON task_step_groups(task_id);
''')


def prompt_title(prompt):
    text=re.sub(r'\s+', ' ', str(prompt or '')).strip()
    text=re.sub(r'^[#>*\s]+', '', text)
    if not text: raise ValueError('A user request is required to name this task')
    return text if len(text)<=120 else text[:119].rstrip()+'…'


def source_prompt(store, task_id):
    with store.connection() as c:
        task=c.execute('SELECT goal FROM tasks WHERE id=?',(task_id,)).fetchone()
        if not task: raise ValueError('Unknown task')
        turn=c.execute("SELECT t.prompt FROM turns t JOIN assignments a ON a.session_id=t.session_id AND a.turn_id=t.turn_id WHERE a.task_id=? AND trim(t.prompt)!='' ORDER BY t.start,t.session_id,t.turn_id LIMIT 1",(task_id,)).fetchone()
        name=c.execute('SELECT * FROM task_names WHERE task_id=?',(task_id,)).fetchone()
    return (turn['prompt'] if turn else (name['source_prompt'] if name else None)) or task['goal'] or ''


def rename(store, task_id, *, title=None, model=None, connection=None):
    prompt=source_prompt(store,task_id)
    title=prompt_title(prompt) if title is None else str(title).strip()
    if not title or len(title)>200:raise ValueError('Task name must contain 1..200 characters')
    def write(c):
        c.execute('UPDATE tasks SET title=?,updated=? WHERE id=?',(title,datetime.now(timezone.utc).isoformat(),task_id))
        c.execute('INSERT OR REPLACE INTO task_names VALUES(?,?,?,?,?)',(task_id,'model' if model else 'prompt',prompt[:12000],model,time.time()))
        store.audit(c,'name_task',task_id,{'source':'model' if model else 'prompt','model':model,'title':title})
    if connection is not None:write(connection)
    else:
        with store.connection() as c:write(c)
    return {'id':task_id,'title':title,'source':'model' if model else 'prompt'}


def groups(store, task_id, steps):
    current={s['id']:s for s in steps}
    with store.connection() as c:
        rows=[dict(r) for r in c.execute('SELECT * FROM task_step_groups WHERE task_id=? ORDER BY created,id',(task_id,))]
    for row in rows:
        saved=json.loads(row.pop('snapshot'))
        row['step_ids']=[s['id'] for s in saved];row['step_count']=len(saved)
        row['stale']=any(current.get(s['id'])!=s for s in saved)
        row.update(status='unverified',source='user',confidence=None,tags=[])
    return rows


def collect(store, task_id, step_ids, title, activity='other', summary='', expected_snapshot=None):
    import task_history as h
    h.init(store)
    if not isinstance(step_ids,list) or not 1<=len(step_ids)<=200 or any(not isinstance(x,str) for x in step_ids) or len(step_ids)!=len(set(step_ids)):
        raise ValueError('Select 1..200 distinct source steps')
    title=h.bounded(title,200,'subtask name')
    if activity not in h.ACTIVITIES:raise ValueError('Unknown subtask activity')
    if not isinstance(summary,str) or len(summary)>4000:raise ValueError('Invalid subtask description')
    ident=uuid.uuid4().hex
    with store.connection() as c:
        c.execute('BEGIN IMMEDIATE')
        body,current=h.snapshot(store,task_id)
        if expected_snapshot is not None and expected_snapshot!=current:raise ValueError('Task steps changed; refresh the timeline and review your selection')
        selected=[s for s in body['steps'] if s['id'] in set(step_ids)]
        if len(selected)!=len(step_ids):raise ValueError('Every selected step must belong to this task')
        existing=groups(store,task_id,body['steps'])
        if len(existing)>=60:raise ValueError('This task already has 60 collected subtasks')
        if any(set(g['step_ids'])&set(step_ids) for g in existing):raise ValueError('A selected step already belongs to a collected subtask')
        raw=json.dumps(selected,sort_keys=True,separators=(',',':'));digest=hashlib.sha256(raw.encode()).hexdigest()
        c.execute('INSERT INTO task_step_groups VALUES(?,?,?,?,?,?,?,?)',(ident,task_id,title,activity,summary,raw,digest,time.time()))
        c.executemany('INSERT INTO task_step_group_members VALUES(?,?,?)',[(ident,s['id'],i) for i,s in enumerate(selected)])
        text=' '.join([body['task']['title'],title,activity,summary,*[s['name'] for s in selected]])
        c.execute('INSERT INTO task_history_fts VALUES(?,?,?,?)',(task_id,ident,'manual',text))
        store.audit(c,'collect_steps_into_subtask',ident,{'task_id':task_id,'step_ids':step_ids,'snapshot_hash':digest,'source':'user','status':'unverified'})
    return {'id':ident,'task_id':task_id,'step_count':len(selected),'status':'unverified'}


def timeline(store, task_id, limit=100, offset=0, subtask_id=None):
    import task_history as h
    h.init(store);limit,offset=h.page(limit,offset)
    body,digest=h.snapshot(store,task_id);steps=body['steps']
    collected=groups(store,task_id,steps)
    membership={i:g['id'] for g in collected for i in g['step_ids']}
    if subtask_id:
        import work_analytics
        task=work_analytics.task_data(store,task_id)
        group=next((g for g in task['subtasks'] if g['id']==subtask_id),None)
        if not group:raise ValueError('Unknown subtask')
        selected=set(group['step_ids']);steps=[s for s in steps if s['id'] in selected]
    times=[]
    for s in steps:
        try:
            end=datetime.fromisoformat(s['ts'].replace('Z','+00:00'))
            if end.tzinfo is None:end=end.replace(tzinfo=timezone.utc)
            end=end.timestamp()*1000
        except (ValueError,TypeError,AttributeError):continue
        duration=s['runtime'] if isinstance(s['runtime'],(int,float)) and math.isfinite(s['runtime']) and s['runtime']>=0 else 0
        times.extend([end-duration*1000,end])
    result=[dict(s,group_id=membership.get(s['id'])) for s in steps[offset:offset+limit]]
    return {'task_id':task_id,'snapshot_hash':digest,'steps':result,'groups':collected,'total':len(steps),'offset':offset,
            'next_offset':offset+limit if offset+limit<len(steps) else None,'range_start':min(times) if times else None,'range_end':max(times) if times else None,
            'timing_basis':'Positions use recorded completion timestamps. Bar starts are derived from recorded runtime, not separately measured start times. Overlapping runtimes are not elapsed task time.'}
