"""Authenticated, idempotent local hook decisions; separate from category rules."""
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import time
import uuid

MODES = ('log', 'warn', 'ask', 'block')
KINDS = ('command', 'break', 'task_budget', 'daily_budget', 'context', 'failure_loop', 'stop_check')
EVENTS = ('start', 'prompt', 'pre_tool', 'post_tool', 'stop')
DEFAULTS = [
 ('break','Prompt after a break','break',3600,'warn','Consider a new session or a compact handoff after an idle break.'),
 ('task-budget','Task budget','task_budget',5,'ask','The reported task cost reached its next budget threshold.'),
 ('daily-budget','Daily budget','daily_budget',100,'warn','Reported session costs today reached the next daily budget threshold.'),
 ('main-checkout','No checkout in a main folder','command',0,'warn','Use an isolated worktree before switching branches in a main folder.'),
 ('public-registry','No public npm registry','command',0,'warn','Use the project-approved package registry.'),
 ('attribution','No Claude attribution','command',0,'warn','Review generated commit attribution before committing.'),
 ('external-write','Writes to external records','command',0,'warn','Check the destination and authorization before writing an external record.'),
 ('shell-exploration','Shell file exploration','command',0,'warn','Prefer bounded file reads and targeted search; keep necessary diagnostics.'),
 ('context','Large context','context',200000,'warn','Context reached the configured limit; consider compacting or a focused handoff.'),
 ('failure-loop','Same call keeps failing','failure_loop',3,'warn','The same call failed repeatedly; reassess before retrying.'),
 ('stop-check','Edits after the last check','stop_check',0,'warn','Files changed after the last successful check. Verify the changes before finishing.'),
]


def init(store):
    with store.connection() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS steering_rules(id TEXT PRIMARY KEY,name TEXT NOT NULL,kind TEXT NOT NULL,mode TEXT NOT NULL,enabled INTEGER NOT NULL,builtin INTEGER NOT NULL,config TEXT NOT NULL,message TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS live_sessions(id TEXT PRIMARY KEY,workspace TEXT NOT NULL,last_seen REAL NOT NULL,status TEXT NOT NULL,paused INTEGER NOT NULL DEFAULT 0,task_id TEXT,task_cost REAL,context_tokens INTEGER,last_prompt REAL,last_edit REAL,last_check REAL,last_call TEXT,failures INTEGER NOT NULL DEFAULT 0,cost_day TEXT,cost_day_base REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS steering_events(id TEXT PRIMARY KEY,session_id TEXT NOT NULL,received REAL NOT NULL,payload_hash TEXT NOT NULL,response TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS steering_log(id TEXT PRIMARY KEY,session_id TEXT NOT NULL,at REAL NOT NULL,rule_id TEXT,rule_name TEXT NOT NULL,mode TEXT NOT NULL,message TEXT NOT NULL,call TEXT NOT NULL,workspace TEXT NOT NULL,event_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS steering_notes(id TEXT PRIMARY KEY,session_id TEXT NOT NULL,message TEXT NOT NULL,created REAL NOT NULL,delivered REAL);
CREATE TABLE IF NOT EXISTS steering_state(session_id TEXT NOT NULL,rule_id TEXT NOT NULL,value TEXT NOT NULL,PRIMARY KEY(session_id,rule_id));
CREATE INDEX IF NOT EXISTS live_log_time ON steering_log(at);
CREATE INDEX IF NOT EXISTS live_log_rule ON steering_log(rule_id,at);
''')
        for ident,name,kind,threshold,mode,message in DEFAULTS:
            c.execute('INSERT OR IGNORE INTO steering_rules VALUES(?,?,?,?,1,1,?,?)',(ident,name,kind,mode,json.dumps({'threshold':threshold}),message))
    target=store.data/'steering-token'
    try:
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        return
    with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(32))


def text(value, maximum, label, empty=False):
    if not isinstance(value,str) or len(value)>maximum or (not empty and not value.strip()):raise ValueError('Invalid '+label)
    return value.strip()


def number(value,label):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise ValueError('Invalid '+label)
    return value


def save_rule(store, v):
    init(store)
    ident=v.get('id') or uuid.uuid4().hex
    with store.connection() as c:
        old=c.execute('SELECT * FROM steering_rules WHERE id=?',(ident,)).fetchone()
        if v.get('delete'):
            if not old or old['builtin']:raise ValueError('Only custom rules can be deleted')
            c.execute('DELETE FROM steering_rules WHERE id=?',(ident,))
        else:
            name=text(v.get('name',old['name'] if old else ''),200,'rule name')
            kind=v.get('kind',old['kind'] if old else 'command');mode=v.get('mode',old['mode'] if old else 'warn')
            enabled=v.get('enabled',bool(old['enabled']) if old else True)
            config=v.get('config',json.loads(old['config']) if old else {})
            message=text(v.get('message',old['message'] if old else ''),2000,'message')
            if kind not in KINDS or mode not in MODES or type(enabled) is not bool or not isinstance(config,dict):raise ValueError('Invalid rule')
            if old and old['builtin'] and kind!=old['kind']:raise ValueError('Built-in rule type cannot change')
            if set(config)-{'threshold','tool','pattern','matcher','workspace','main_only'}:raise ValueError('Unknown rule option')
            if kind!='command':
                if number(config.get('threshold',0),'threshold')<=0 and kind!='stop_check':raise ValueError('Threshold must be positive')
                if kind in ('task_budget','daily_budget') and config.get('threshold',0)<.001:raise ValueError('Budget increment must be at least 0.001 USD')
                if kind=='failure_loop' and type(config.get('threshold')) is not int:raise ValueError('Failure count must be an integer')
            if kind=='command' and not (old and old['builtin']):
                text(config.get('pattern'),500,'pattern');text(config.get('tool','*'),100,'tool pattern')
                if config.get('matcher','contains') not in ('contains','glob'):raise ValueError('Matcher must be contains or glob')
                text(config.get('workspace',''),2000,'workspace',True)
                if type(config.get('main_only',False)) is not bool:raise ValueError('Invalid main-folder option')
            c.execute('INSERT OR REPLACE INTO steering_rules VALUES(?,?,?,?,?,?,?,?)',(ident,name,kind,mode,int(enabled),old['builtin'] if old else 0,json.dumps(config),message))
        c.execute('DELETE FROM steering_state WHERE rule_id=?',(ident,))
        store.audit(c,'steering_rule',ident,{'delete':bool(v.get('delete')),'mode':v.get('mode')})
    return {'id':ident}


def control(store,v):
    init(store);sid=text(v.get('session_id'),200,'session ID')
    with store.connection() as c:
        if not c.execute('SELECT 1 FROM live_sessions WHERE id=?',(sid,)).fetchone():raise ValueError('Unknown live session')
        if 'paused' in v:
            if type(v['paused']) is not bool:raise ValueError('Invalid paused state')
            c.execute('UPDATE live_sessions SET paused=? WHERE id=?',(int(v['paused']),sid))
        if v.get('note'):
            c.execute('INSERT INTO steering_notes VALUES(?,?,?,?,NULL)',(uuid.uuid4().hex,sid,text(v['note'],4000,'note'),time.time()))
        store.audit(c,'live_control',sid,{'pause_changed':'paused' in v,'note_queued':bool(v.get('note'))})
    return {'ok':True}


def command_matches(ident,config,p):
    command=p.get('command','');tool=p.get('tool','')
    if ident=='main-checkout':return p.get('main_folder') is True and bool(re.search(r'\bgit\s+(?:-[^ ]+\s+)*(?:checkout|switch)\b',command))
    if ident=='public-registry':return bool(re.search(r'(registry\.npmjs\.org|registry\.yarnpkg\.com)',command))
    if ident=='attribution':return 'git' in command and bool(re.search(r'Co-Authored-By:.*(?:Claude|Anthropic)',command,re.I))
    if ident=='external-write':return bool(re.search(r'(create|update|delete|upload)',tool,re.I)) and bool(re.search(r'(service.?now|jira|confluence|salesforce)',tool,re.I))
    if ident=='shell-exploration':return bool(re.search(r'(bash|shell|exec_command|CommandExecution)',tool,re.I)) and bool(re.search(r'(?:^|[;&|]\s*|\s)(?:cat|head|tail|sed|find|grep|ls)(?:\s|$)',command))
    if config.get('main_only') and p.get('main_folder') is not True:return False
    if config.get('workspace') and not fnmatch.fnmatchcase(p['workspace'],config['workspace']):return False
    if not fnmatch.fnmatchcase(tool,config.get('tool','*')):return False
    pattern=config.get('pattern','')
    return bool(pattern) and (fnmatch.fnmatchcase(command,pattern) if config.get('matcher')=='glob' else pattern in command)


def receive(store,p,clock=None):
    init(store);now=time.time() if clock is None else clock
    if not isinstance(p,dict):raise ValueError('Expected hook object')
    p=dict(p);sid=text(p.get('session_id'),200,'session ID');eid=text(p.get('event_id'),200,'event ID')
    kind=p.get('event')
    if kind not in EVENTS:raise ValueError('Unsupported hook event')
    p['workspace']=text(p.get('workspace',''),2000,'workspace',True)
    p['tool']=text(p.get('tool',''),200,'tool',True);p['command']=text(p.get('command',''),8000,'command',True)
    for key in ('cost_usd','context_tokens'):
        if key in p and p[key] is not None:number(p[key],key)
    if 'failed' in p and type(p['failed']) is not bool:raise ValueError('Invalid outcome')
    if 'input_hash' in p:text(p['input_hash'],128,'input hash')
    if 'task_id' in p and p['task_id'] is not None:text(p['task_id'],200,'task ID')
    if 'operation' in p and p['operation'] not in ('edit','check','other'):raise ValueError('Invalid operation')
    if 'main_folder' in p and type(p['main_folder']) is not bool:raise ValueError('Invalid main-folder flag')
    fingerprint=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
    # Native token-price scenarios are a fallback only when every response is priced.
    # They are not actual subscription charges; callers may supply a cumulative cost.
    if p.get('cost_usd') is None:
        import work_analytics
        scenario=work_analytics.rates(store)
        with store.connection() as read:
            responses=read.execute("SELECT usage,model FROM events WHERE session_id=? AND kind='generation'",(sid,)).fetchall()
        costs=[work_analytics.cost(json.loads(r['usage']) if r['usage'] else None,r['model'],scenario) for r in responses]
        if scenario['unit']=='USD' and costs and all(v is not None for v in costs):p['cost_usd']=sum(costs)
    event_key=hashlib.sha256((sid+'\0'+eid).encode()).hexdigest()
    day=time.strftime('%Y-%m-%d',time.gmtime(now))
    with store.connection() as c:
        c.execute('BEGIN IMMEDIATE')
        previous=c.execute('SELECT * FROM steering_events WHERE id=?',(event_key,)).fetchone()
        if previous:
            if previous['payload_hash']!=fingerprint:raise ValueError('Event ID reused with different content')
            return json.loads(previous['response'])
        old=c.execute('SELECT * FROM live_sessions WHERE id=?',(sid,)).fetchone()
        session=dict(old) if old else dict(id=sid,workspace=p['workspace'],paused=0,task_id=None,task_cost=None,context_tokens=None,last_prompt=None,last_edit=None,last_check=None,last_call=None,failures=0,cost_day=day,cost_day_base=0)
        if session['cost_day']!=day:session.update(cost_day=day,cost_day_base=session['task_cost'] or 0)
        if p.get('task_id') is not None and p['task_id']!=session['task_id']:
            session.update(task_id=p['task_id'],last_edit=None,last_check=None)
            c.execute('INSERT OR REPLACE INTO steering_state VALUES(?,?,?)',(sid,'task-cost-base',str(p.get('cost_usd') or session['task_cost'] or 0)))
            c.execute("DELETE FROM steering_state WHERE session_id=? AND rule_id IN (SELECT id FROM steering_rules WHERE kind IN ('task_budget','context'))",(sid,))
        # Cost is cumulative per session. Task budget uses deltas since its explicit task boundary.
        if p.get('cost_usd') is not None:
            if session['task_cost'] is not None and p['cost_usd']<session['task_cost']:raise ValueError('Cumulative cost decreased')
            session['task_cost']=p['cost_usd']
        session.update(workspace=p['workspace'],last_seen=now,status='waiting' if kind=='stop' else 'working')
        if p.get('context_tokens') is not None:session['context_tokens']=p['context_tokens']
        signature=hashlib.sha256((p['tool']+'\0'+str(p.get('input_hash') or p['command'])).encode()).hexdigest() if p.get('input_hash') or p['command'] else None
        if kind=='post_tool':
            session['failures']=(session['failures']+1 if signature==session['last_call'] else 1) if p.get('failed') is True and signature is not None else 0
            session['last_call']=signature
            if p.get('operation')=='edit' and p.get('failed') is False:session['last_edit']=now
            if p.get('operation')=='check' and p.get('failed') is False:session['last_check']=now
        daily=c.execute('SELECT SUM(MAX(0,task_cost-cost_day_base)) FROM live_sessions WHERE cost_day=? AND id!=?',(day,sid)).fetchone()[0] or 0
        daily+=max(0,(session['task_cost'] or 0)-session['cost_day_base'])
        fired=[]
        for row in c.execute('SELECT * FROM steering_rules WHERE enabled=1 ORDER BY id').fetchall():
            r=dict(row);cfg=json.loads(r['config']);threshold=cfg.get('threshold',0);hit=False;state=None
            prior=c.execute('SELECT value FROM steering_state WHERE session_id=? AND rule_id=?',(sid,r['id'])).fetchone()
            prior=prior[0] if prior else None
            if r['kind']=='command':hit=kind=='pre_tool' and command_matches(r['id'],cfg,p)
            elif r['kind']=='break':hit=kind=='prompt' and old is not None and now-old['last_seen']>=threshold
            elif r['kind'] in ('task_budget','daily_budget') and kind in ('pre_tool','prompt'):
                base=c.execute("SELECT value FROM steering_state WHERE session_id=? AND rule_id='task-cost-base'",(sid,)).fetchone()
                value=max(0,(session['task_cost'] or 0)-(float(base[0]) if base else 0)) if r['kind']=='task_budget' else daily
                state=str(int((value or 0)//threshold))
                # Daily thresholds share one global state to avoid one firing per session.
                if r['kind']=='daily_budget':
                    previous_day=c.execute('SELECT value FROM steering_state WHERE session_id=? AND rule_id=?',('day:'+day,r['id'])).fetchone();prior=previous_day[0] if previous_day else None
                hit=int(state)>0 and (prior is None or int(state)>int(prior))
            elif r['kind']=='context':state=str(session.get('task_id') or 'session');hit=kind in ('pre_tool','prompt') and (session['context_tokens'] or 0)>=threshold and prior!=state
            elif r['kind']=='failure_loop':hit=kind=='post_tool' and session['failures']>=threshold and session['failures']%threshold==0
            elif r['kind']=='stop_check':hit=kind=='stop' and session['last_edit'] is not None and (session['last_check'] is None or session['last_edit']>session['last_check'])
            if not hit:continue
            message=r['message']
            if r['kind'] in ('task_budget','daily_budget'):message+=f' Reported/API-scenario total: ${value:.2f}; increment: ${threshold:.2f}.'
            if r['kind']=='context':message+=f" Reported context: {session['context_tokens']:,} tokens."
            fired.append({'rule_id':r['id'],'name':r['name'],'mode':r['mode'],'message':message})
            if state is not None:c.execute('INSERT OR REPLACE INTO steering_state VALUES(?,?,?)',('day:'+day if r['kind']=='daily_budget' else sid,r['id'],state))
        notes=c.execute('SELECT * FROM steering_notes WHERE session_id=? AND delivered IS NULL ORDER BY created',(sid,)).fetchall()
        for note in notes:
            fired.append({'rule_id':None,'name':'Session note','mode':'warn','message':note['message']})
            c.execute('UPDATE steering_notes SET delivered=? WHERE id=?',(now,note['id']))
        if kind=='pre_tool' and session['paused']:fired.append({'rule_id':None,'name':'Session paused','mode':'ask','message':'This session is paused; ask for approval for this tool call.'})
        priority={'log':0,'warn':1,'ask':2,'block':3}
        mode=max((x['mode'] for x in fired),key=priority.get,default='log')
        # Post-tool decisions cannot retroactively stop a completed call.
        decision=('block' if mode=='block' else 'ask' if mode=='ask' else 'warn' if mode=='warn' else 'allow') if kind!='post_tool' else ('warn' if any(x['mode']!='log' for x in fired) else 'allow')
        response={'decision':decision,'messages':[x['message'] for x in fired if x['mode']!='log'],'rules':fired,'event_id':eid}
        from capture_proxy import sanitized
        for f in fired:
            delivered_mode='warn' if kind=='post_tool' and f['mode']!='log' else f['mode']
            c.execute('INSERT INTO steering_log VALUES(?,?,?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,sid,now,f['rule_id'],f['name'],delivered_mode,f['message'],sanitized((p['tool']+' '+p['command'])[:2000]),p['workspace'],eid))
        if kind=='prompt':session['last_prompt']=now
        columns=['id','workspace','last_seen','status','paused','task_id','task_cost','context_tokens','last_prompt','last_edit','last_check','last_call','failures','cost_day','cost_day_base']
        c.execute('INSERT OR REPLACE INTO live_sessions('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')',[session[k] for k in columns])
        c.execute('INSERT INTO steering_events VALUES(?,?,?,?,?)',(event_key,sid,now,fingerprint,json.dumps(response)))
    return response


def state(store,workspace='',clock=None):
    init(store);now=time.time() if clock is None else clock
    with store.connection() as c:
        sessions=[dict(r) for r in c.execute('SELECT * FROM live_sessions WHERE last_seen>=? ORDER BY last_seen DESC',(now-86400,)) if not workspace or r['workspace']==workspace]
        logs=[dict(r) for r in c.execute('SELECT * FROM steering_log ORDER BY at DESC LIMIT 2000') if not workspace or r['workspace']==workspace]
        rules=[]
        for row in c.execute('SELECT * FROM steering_rules ORDER BY builtin DESC,name'):
            r=dict(row);r['config']=json.loads(r['config']);r['fired_7d']=c.execute('SELECT COUNT(*) FROM steering_log WHERE rule_id=? AND at>=? AND (length(?)=0 OR workspace=?)',(r['id'],now-7*86400,workspace,workspace)).fetchone()[0];r['last_fired']=c.execute('SELECT MAX(at) FROM steering_log WHERE rule_id=? AND (length(?)=0 OR workspace=?)',(r['id'],workspace,workspace)).fetchone()[0];rules.append(r)
        for s in sessions:
            s['pending_notes']=c.execute('SELECT COUNT(*) FROM steering_notes WHERE session_id=? AND delivered IS NULL',(s['id'],)).fetchone()[0]
            if s['last_seen']<now-600:s['status']='idle'
        recent_counts=c.execute("SELECT COUNT(*),SUM(CASE WHEN mode IN ('ask','block') THEN 1 ELSE 0 END) FROM steering_log WHERE at>=? AND (length(?)=0 OR workspace=?)",(now-86400,workspace,workspace)).fetchone()
        workspaces=[r[0] for r in c.execute('SELECT DISTINCT workspace FROM live_sessions ORDER BY workspace')]
    return {'sessions':sessions,'rules':rules,'log':logs,'workspaces':workspaces,'metrics':{'working':sum(s['status']=='working' for s in sessions),'waiting':sum(s['status']=='waiting' for s in sessions),'fired':recent_counts[0],'asked_blocked':recent_counts[1] or 0},'hook_instructions':'python3 tools/usage-monitor/observability/steering_hook.py status --data <workspace-data>','log_limit':2000}
