"""Bounded, source-linked task evidence. Never read paths suggested by log text."""
import hashlib
import json
import re
import time
from urllib.parse import urlparse
import uuid

KINDS=('change','visual_reference','validation','intervention')

def init(store):
    with store.connection() as c:
        c.execute('CREATE TABLE IF NOT EXISTS task_evidence_notes(id TEXT PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks(id),kind TEXT NOT NULL,title TEXT NOT NULL,detail TEXT NOT NULL,reference TEXT NOT NULL,outcome TEXT NOT NULL,created REAL NOT NULL)')


def add(store,task_id,kind,title,detail='',reference='',outcome='unknown'):
    init(store)
    if kind not in KINDS or outcome not in ('unknown','passed','failed','confirmed','not_applicable'):raise ValueError('Invalid evidence kind or outcome')
    if not isinstance(title,str) or not title.strip() or len(title)>200:raise ValueError('Evidence title requires 1..200 characters')
    if any(not isinstance(x,str) for x in (detail,reference)) or len(detail)>8000 or len(reference)>2000:raise ValueError('Evidence too large')
    if reference:
        url=urlparse(reference)
        if url.scheme not in ('https','http') or not url.hostname or url.username or url.password:raise ValueError('Reference must be an HTTP(S) URL without credentials')
    ident=uuid.uuid4().hex
    with store.connection() as c:
        if not c.execute('SELECT 1 FROM tasks WHERE id=?',(task_id,)).fetchone():raise ValueError('Unknown task')
        c.execute('INSERT INTO task_evidence_notes VALUES(?,?,?,?,?,?,?,?)',(ident,task_id,kind,title.strip(),detail,reference,outcome,time.time()))
        store.audit(c,'record_task_evidence',ident,{'task_id':task_id,'kind':kind,'basis':'Explicit user/agent record, not independently verified'})
    return {'id':ident}


def packet(store,task_id):
    from workspace import bridge
    from capture_proxy import sanitized
    init(store)
    with store.connection() as c:
        task=c.execute('SELECT * FROM tasks WHERE id=?',(task_id,)).fetchone()
        if not task:raise ValueError('Unknown task')
        turns=[dict(r) for r in c.execute('SELECT t.* FROM turns t JOIN assignments a USING(session_id,turn_id) WHERE a.task_id=? ORDER BY t.start,t.session_id,t.turn_id',(task_id,))]
        first_turns={r['session_id']:c.execute('SELECT turn_id FROM turns WHERE session_id=? ORDER BY start,turn_id LIMIT 1',(r['session_id'],)).fetchone()[0] for r in turns}
        events={r['id']:dict(r) for r in c.execute('SELECT e.* FROM events e JOIN assignments a USING(session_id,turn_id) WHERE a.task_id=?',(task_id,))}
        paths=[r['path'] for r in c.execute('SELECT path FROM files')]
        notes=[dict(r) for r in c.execute('SELECT * FROM task_evidence_notes WHERE task_id=? ORDER BY created',(task_id,))]
        provenance=None
        if c.execute("SELECT 1 FROM sqlite_master WHERE name='activity_insight_applied'").fetchone():
            linked=c.execute('SELECT a.job_id,a.proposal,j.model,j.usage FROM activity_insight_applied a JOIN activity_insight_jobs j ON j.id=a.job_id WHERE a.task_id=?',(task_id,)).fetchone()
            if linked:provenance={**dict(linked),'usage':json.loads(linked['usage']) if linked['usage'] else None,'accounting':'Shared activity-review overhead; not independently allocated to each task'}
    selected={(r['session_id'],r['turn_id']) for r in turns};sessions={r['session_id'] for r in turns}
    matching=[path for path in paths if any(sid in __import__('pathlib').Path(path).name for sid in sessions)]
    if sessions and all(any(sid in __import__('pathlib').Path(path).name for path in matching) for sid in sessions):paths=matching
    facts=[];seen=set();matched_steps=set();scanned=0;truncated=False;max_lines=50000
    for path in paths:
        session=None
        if scanned>=max_lines or len(facts)>=120:truncated=True;break
        try:
            for line,record in bridge.monitor.lines(__import__('pathlib').Path(path)):
                scanned+=1
                if scanned>max_lines:truncated=True;break
                if not record:continue
                p=record.get('payload') or {}
                if record.get('type')=='session_meta':session=p.get('id')
                if (session,p.get('turn_id')) not in selected or (p.get('thread_id') and p['thread_id']!=session):continue
                item=p.get('item') or {};typ=item.get('type');event_id=session+':tool:'+str(item.get('id'))
                if event_id in events:matched_steps.add(event_id)
                key=('event',event_id) if event_id in events else (session,line,typ)
                if key in seen:continue
                seen.add(key)
                base={'id':hashlib.sha256((str(key)+task_id).encode()).hexdigest()[:24],'session_id':session,'turn_id':p.get('turn_id'),'source_line':line,'event_id':event_id if event_id in events else None,'recorded_at':record.get('timestamp'),'basis':'retained native record'}
                if typ in ('FileChange','file_change'):
                    changes=item.get('changes',{})
                    if isinstance(changes,list):changes={str(i):v for i,v in enumerate(changes)}
                    if isinstance(changes,dict):
                        for name,value in list(changes.items())[:20]:
                            v=value if isinstance(value,dict) else {'diff':str(value)};diff=str(v.get('diff',v.get('patch','')))
                            file=str(v.get('path',name));facts.append({**base,'kind':'change','title':file[:1000],'detail':sanitized(diff[:5000]),'diff_sha256':hashlib.sha256(diff.encode()).hexdigest() if diff else None,'truncated':len(diff)>5000,'outcome':'change_failed' if str(item.get('status','')).lower() in ('failed','error') else 'change_reported' if str(item.get('status','')).lower() in ('completed','success') else 'change_attempt_unverified','note':'Retained native patch/status, not a current-checkout diff or verified task outcome.','visual_candidate':bool(re.search(r'\.(css|scss|html|tsx|jsx|vue|svelte)$',file))})
                elif typ in ('ImageView','image_view'):
                    ref=item.get('path',item.get('image_path',item.get('url','')))
                    facts.append({**base,'kind':'visual_reference','title':'Recorded image reference','detail':sanitized(str(ref)[:2000]),'outcome':'reference_failed' if str(item.get('status','')).lower() in ('failed','error') else 'reference_only','note':'An image view does not prove a before/after screenshot or visual correctness.'})
                elif typ in ('CommandExecution','command_execution'):
                    command=item.get('command');text=command if isinstance(command,str) else ' '.join(str(v) for v in command or [])
                    if re.search(r'\b(pytest|jest|vitest|playwright|tsc|unittest|test|lint|check)\b',text,re.I):
                        code=item.get('exit_code');output=str(item.get('aggregated_output',''))
                        facts.append({**base,'kind':'validation','title':sanitized(text[:1000]),'detail':sanitized(output[:3000]),'truncated':len(output)>3000,'exit_code':code,'outcome':'command_passed' if type(code) is int and code==0 else 'command_failed' if type(code) is int else 'unknown','note':'Command exit status is recorded; coverage and whole-task acceptance are not inferred.'})
                    refs=re.findall(r'(?:https?://[^\s<>"\']+|(?:\.?\.?/|/)[^\s<>"\']+)\.(?:png|jpe?g|webp)(?:\?[^\s<>"\']*)?',str(item.get('aggregated_output',''))[:16000],re.I)
                    for ref in refs[:3]:facts.append({**base,'kind':'visual_reference','title':'Image path mentioned in retained output','detail':sanitized(ref[:2000]),'outcome':'unverified_reference','note':'Not read from disk or fetched automatically.'})
                if len(facts)>=120:truncated=True;break
        except (OSError,ValueError):continue
    if len(facts)>120:truncated=True;facts=facts[:120]
    followups=[]
    for r in turns:
        if r['turn_id']!=first_turns[r['session_id']] and r.get('prompt'):
            followups.append({'kind':'user_follow_up','session_id':r['session_id'],'turn_id':r['turn_id'],'recorded_at':r['start'],'detail':sanitized((r['prompt'] or '')[:2000]),'basis':'Recorded user message; not automatically classified as intervention'})

    groups={kind:[f for f in facts if f['kind']==kind] for kind in KINDS}
    for note in notes:groups[note['kind']].append({**note,'basis':'Explicit user/agent record; not independently verified'})
    return {'activity_analysis_source':provenance,'task_id':task_id,'task_status':task['status'],'task_outcome':task['outcome'],'groups':groups,'user_follow_ups':followups[:40],
        'coverage':{'retained_records_scanned':scanned,'matched_tool_steps':len(matched_steps),'task_tool_steps':sum(r['kind']=='tool' for r in events.values()),'bounded_or_truncated':truncated,'source_files':len(paths)},
        'gaps':{'visual_proof':'References recorded; inspect before/after coverage' if groups['visual_reference'] else 'No screenshot or visual reference recorded',
                'validation':'Inspect recorded command and coverage; task acceptance remains separate' if groups['validation'] else 'No validation evidence recorded',
                'human_intervention':'Explicit intervention evidence recorded' if groups['intervention'] else 'No confirmed intervention recorded; user follow-ups are not proof of interference'},
        'limits':['No current checkout diff is substituted for historical changes.','No referenced local file or remote URL is read automatically.','Missing evidence means unknown, not passed, unchanged, or no intervention.']}
