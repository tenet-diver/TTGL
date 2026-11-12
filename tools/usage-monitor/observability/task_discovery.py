"""Idempotent task discovery from recorded session/turn identities, without inference."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


def init(store):
    with store.connection() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS task_discovery_tasks(task_id TEXT PRIMARY KEY REFERENCES tasks(id),session_id TEXT UNIQUE NOT NULL,basis TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS task_discovery_projects(repo TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id));
''')
        c.execute("INSERT OR IGNORE INTO settings VALUES('task_discovery_enabled','false')")


def enabled(store):
    init(store)
    with store.connection() as c:return c.execute("SELECT value FROM settings WHERE key='task_discovery_enabled'").fetchone()[0]=='true'


def configure(store, value):
    if type(value) is not bool:raise ValueError('Discovery enabled must be a boolean')
    init(store)
    with store.connection() as c:
        c.execute("UPDATE settings SET value=? WHERE key='task_discovery_enabled'",(json.dumps(value),))
        store.audit(c,'configure_task_discovery','native_sessions',{'enabled':value})
    return sync(store) if value else {'enabled':False,'created':0,'assigned':0}


def sync(store):
    import task_curation
    if not enabled(store):return {'enabled':False,'created':0,'assigned':0}
    created=assigned=0;stamp=datetime.now(timezone.utc).isoformat()
    with store.connection() as c:
        c.execute('BEGIN IMMEDIATE')
        if c.execute("SELECT value FROM settings WHERE key='collection_enabled'").fetchone()[0]!='true':return {'enabled':True,'paused':True,'created':0,'assigned':0}
        rows=c.execute('''SELECT t.* FROM turns t LEFT JOIN assignments a USING(session_id,turn_id)
WHERE a.task_id IS NULL AND EXISTS(SELECT 1 FROM events e WHERE e.session_id=t.session_id AND e.turn_id=t.turn_id)
ORDER BY t.start,t.session_id,t.turn_id''').fetchall()
        prompts={}
        for row in rows:
            if (row['prompt'] or '').strip():prompts.setdefault(row['session_id'],row['prompt'])
        for turn in rows:
            prompt=prompts.get(turn['session_id'],'')
            source=c.execute('SELECT task_id FROM task_discovery_tasks WHERE session_id=?',(turn['session_id'],)).fetchone()
            if not source:
                if not prompt:continue
                project=c.execute('SELECT project_id FROM task_discovery_projects WHERE repo=?',(turn['repo'],)).fetchone()
                if not project:
                    project_id='logs-'+hashlib.sha256((turn['repo'] or 'unknown').encode()).hexdigest()[:24]
                    c.execute('INSERT OR IGNORE INTO projects VALUES(?,?,?,?,?)',(project_id,'Collected logs · '+(Path(turn['repo']).name or 'Unknown folder'),turn['repo'] or 'unknown','Automatically discovered native sessions; task boundaries are provisional.',stamp))
                    c.execute('INSERT INTO task_discovery_projects VALUES(?,?)',(turn['repo'],project_id))
                else:project_id=project['project_id']
                task_id='native-'+hashlib.sha256(turn['session_id'].encode()).hexdigest()[:32]
                c.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)',(task_id,project_id,task_curation.prompt_title(prompt),prompt[:8000],'','active',turn['start'] or stamp,turn['end'] or stamp,None))
                c.execute('INSERT INTO task_names VALUES(?,?,?,?,?)',(task_id,'prompt',prompt[:12000],None,time.time()))
                c.execute('INSERT INTO task_discovery_tasks VALUES(?,?,?)',(task_id,turn['session_id'],'Recorded conversation; unassigned turns only, provisional task boundary'))
                created+=1
            else:task_id=source['task_id']
            c.execute('INSERT INTO assignments VALUES(?,?,?)',(turn['session_id'],turn['turn_id'],task_id));assigned+=1
            c.execute('UPDATE tasks SET updated=max(updated,?) WHERE id=?',(turn['end'] or turn['start'] or stamp,task_id))
        # Refresh ordering when an already assigned live session gains events. No inferred success.
        c.execute('''UPDATE tasks SET updated=max(updated,coalesce((SELECT max(e.ts) FROM events e JOIN assignments a USING(session_id,turn_id) WHERE a.task_id=tasks.id),updated)) WHERE id IN(SELECT task_id FROM task_discovery_tasks)''')
        if created or assigned:store.audit(c,'discover_logged_tasks','native_sessions',{'created':created,'assigned':assigned,'basis':'session and turn IDs; no model calls; existing assignments preserved'})
    return {'enabled':True,'created':created,'assigned':assigned}
