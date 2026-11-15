"""Bounded, source-linked task evidence. Never read paths suggested by log text."""
import hashlib
import base64
from collections import OrderedDict
import threading
import json
import re
import time
from urllib.parse import urlparse
import uuid
from datetime import datetime

KINDS=('change','visual_reference','validation','intervention')


def story(task, groups, truncated=False):
    """Summarize retained facts without promoting command success to task success."""
    def timestamp(fact):
        try:
            value = datetime.fromisoformat(fact.get('recorded_at', '').replace('Z', '+00:00'))
            return value.timestamp() if value.tzinfo else None
        except (ValueError, TypeError, AttributeError):
            return None

    changes = [f for f in groups['change'] if f.get('event_id')]
    checks = [f for f in groups['validation'] if f.get('event_id')]
    dated_checks = [(timestamp(f), f) for f in checks if timestamp(f) is not None]
    latest_time = max((t for t, _ in dated_checks), default=None)
    latest = [f for t, f in dated_checks if t == latest_time]
    last_check = latest[0] if len(latest) == 1 and len(dated_checks) == len(checks) else None
    chronology_known = bool(last_check) and all(timestamp(f) is not None for f in changes + checks)
    after = sum(timestamp(f) > latest_time for f in changes) if chronology_known else None
    open_items = []
    if not checks:
        open_items.append('No retained validation command; verification is unknown.')
    elif not chronology_known:
        open_items.append('Latest validation or edit ordering is uncertain.')
    if last_check and last_check['outcome'] == 'command_failed':
        open_items.append('Last recorded validation command failed.')
    elif last_check and last_check['outcome'] != 'command_passed':
        open_items.append('Last recorded validation result is unknown.')
    if after:
        open_items.append(f'{after} recorded file changes followed the last validation command.')
    if chronology_known and any(timestamp(f) == latest_time for f in changes):
        open_items.append('An edit shares the last validation timestamp; their ordering is uncertain.')
    if not task['outcome']:
        open_items.append('Task acceptance has not been recorded.')
    if truncated:
        open_items.append('Evidence coverage is bounded or truncated; this summary may be incomplete.')
    return {
        'request': task['goal'], 'acceptance': task['acceptance'],
        'changed_files': sorted({f['title'] for f in changes}),
        'validation_commands': len(checks),
        'last_validation': last_check,
        'changes_after_last_validation': after,
        'open_items': open_items,
        'basis': 'Retained native facts and explicit task records; command success does not establish task acceptance.'
    }

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


_IMAGE_LOCK=threading.RLock()


def inline_images(item):
    """Only retained inline raster bytes; never open a log-suggested path or URL."""
    content=item.get('content',item.get('images',[]))
    candidates=list(content[:4]) if isinstance(content,list) else []
    if item.get('image_data'):candidates.append({'data':item['image_data']})
    for part in candidates[:4]:
        if not isinstance(part,dict):continue
        source=part.get('source',part)
        if not isinstance(source,dict):continue
        encoded=source.get('data') or part.get('image_url') or part.get('url')
        if isinstance(encoded,dict):encoded=encoded.get('url')
        if not isinstance(encoded,str) or len(encoded)>1400000:continue
        if encoded.startswith('data:image/'):
            header,separator,encoded=encoded.partition(',')
            if not separator or ';base64' not in header:continue
        elif source.get('type') not in (None,'base64'):continue
        try:raw=base64.b64decode(encoded,validate=True)
        except (ValueError,TypeError):continue
        if not 0<len(raw)<=1048576:continue
        mime='image/png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if raw.startswith(b'\xff\xd8\xff') else 'image/webp' if raw.startswith(b'RIFF') and raw[8:12]==b'WEBP' else None
        if mime:yield mime,raw


def remember_image(store,task_id,mime,raw):
    ident=hashlib.sha256(task_id.encode()+raw).hexdigest()
    with _IMAGE_LOCK:
        cache=getattr(store,'_evidence_image_cache',None)
        if cache is None:cache=store._evidence_image_cache=OrderedDict()
        cache[(task_id,ident)]=(mime,raw);cache.move_to_end((task_id,ident))
        while len(cache)>64 or sum(len(v[1]) for v in cache.values())>8*1048576:cache.popitem(last=False)
    return ident


def image(store,task_id,ident):
    if not re.fullmatch('[0-9a-f]{64}',ident):raise ValueError('Unknown retained image')
    with store.connection() as c:
        if not c.execute('SELECT 1 FROM tasks WHERE id=?',(task_id,)).fetchone():raise ValueError('Unknown task')
    with _IMAGE_LOCK:found=getattr(store,'_evidence_image_cache',{}).get((task_id,ident))
    if found:return found
    retained=[]
    packet(store,task_id,_image_sink=lambda key,mime,raw:retained.append((mime,raw)) if key==ident else None)
    if retained:return retained[0]
    with _IMAGE_LOCK:found=getattr(store,'_evidence_image_cache',{}).get((task_id,ident))
    if not found:raise ValueError('No retained inline image bytes for this reference')
    return found


def claims(message,groups,task_story):
    """Conservative lexical claim links, not independent acceptance or visual proof."""
    if not message:return []
    results=[]
    for text in re.split(r'(?<=[.!?])\s+|\n+',message.get('text','')):
        if not text.strip():continue
        kind='validation' if re.search(r'\b(tests?|pytest|unittest|lint|build|type.?check)\b',text,re.I) else 'visual_reference' if re.search(r'\b(screenshots?|visual|images?)\b',text,re.I) else None
        if not kind:continue
        if re.search(r'\b(no tests?|tests? (?:were |was )?not|did(?:n.t| not) (?:run|test|build|lint)|not (?:run|tested|verified))\b',text,re.I):status='No verified result claimed';fact=None
        elif kind=='validation':
            fact=task_story.get('last_validation')
            named=[word for word in ('pytest','unittest','lint','build','typecheck') if re.search(r'\b'+word+r'\b',text,re.I)]
            if fact and named and not any(word in fact['title'].lower() for word in named):fact=None
            if fact and not named and re.search(r'\btests?\b',text,re.I) and not re.search(r'\b(pytest|unittest|jest|vitest|playwright|tests?)\b',fact['title'],re.I):fact=None
            status='Last run failed' if fact and fact['outcome']=='command_failed' else 'Recorded command passed' if fact and fact['outcome']=='command_passed' and task_story.get('changes_after_last_validation')==0 else 'Not backed'
        else:
            fact=next((f for f in groups[kind] if f.get('event_id')),None);status='Reference only' if fact else 'Not backed'
        results.append({'claim':text[:1000],'status':status,'event_id':fact.get('event_id') if fact else None,'basis':'Lexical match to retained evidence; task acceptance and visual correctness remain unverified.'})
        if len(results)>=20:break
    return results


def packet(store,task_id,_image_sink=None):
    from workspace import bridge
    from capture_proxy import sanitized
    from work_analytics import timestamp
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
    facts=[];last_message=None;seen=set();matched_steps=set();scanned=0;truncated=False;max_lines=50000
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
                if typ in ('AssistantMessage','assistant_message') and p.get('type')=='item_completed':
                    content=item.get('content',[])
                    text=content if isinstance(content,str) else '\n'.join(str(part.get('text','')) for part in content if isinstance(part,dict)) if isinstance(content,list) else ''
                    if text:
                        candidate={**base,'text':sanitized(text[:8000]),'truncated':len(text)>8000,'basis':'Retained assistant statement; claims are not independently verified'}
                        message_key=lambda message:(timestamp(message.get('recorded_at')) if timestamp(message.get('recorded_at')) is not None else float('-inf'),message['source_line'])
                        if last_message is None or message_key(candidate)>=message_key(last_message):last_message=candidate
                if typ in ('FileChange','file_change'):
                    changes=item.get('changes',{})
                    if isinstance(changes,list):changes={str(i):v for i,v in enumerate(changes)}
                    if isinstance(changes,dict):
                        for name,value in list(changes.items())[:20]:
                            v=value if isinstance(value,dict) else {'diff':str(value)};diff=str(v.get('diff',v.get('patch','')))
                            file=str(v.get('path',name));facts.append({**base,'kind':'change','title':file[:1000],'detail':sanitized(diff[:5000]),'diff_sha256':hashlib.sha256(diff.encode()).hexdigest() if diff else None,'truncated':len(diff)>5000,'outcome':'change_failed' if str(item.get('status','')).lower() in ('failed','error') else 'change_reported' if str(item.get('status','')).lower() in ('completed','success') else 'change_attempt_unverified','note':'Retained native patch/status, not a current-checkout diff or verified task outcome.','visual_candidate':bool(re.search(r'\.(css|scss|html|tsx|jsx|vue|svelte)$',file))})
                elif typ in ('ImageView','image_view'):
                    ref=item.get('path',item.get('image_path',item.get('url','')))
                    previews=[]
                    for mime,raw in inline_images(item):
                        image_id=remember_image(store,task_id,mime,raw);previews.append(image_id)
                        if _image_sink:_image_sink(image_id,mime,raw)
                    for index,preview in enumerate(previews or [None]):
                        facts.append({**base,'id':base['id'] if not preview else hashlib.sha256((base['id']+str(index)).encode()).hexdigest()[:24],'preview_id':preview,'kind':'visual_reference','title':'Recorded image reference','detail':sanitized(str(ref)[:2000]),'outcome':'reference_failed' if str(item.get('status','')).lower() in ('failed','error') else 'reference_only','note':'An image view does not prove a before/after screenshot or visual correctness.'})
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
    task_story=story(task,groups,truncated)
    return {'last_message':last_message,'claims':claims(last_message,groups,task_story),'story':task_story,'activity_analysis_source':provenance,'task_id':task_id,'task_status':task['status'],'task_outcome':task['outcome'],'groups':groups,'user_follow_ups':followups[:40],
        'coverage':{'retained_records_scanned':scanned,'matched_tool_steps':len(matched_steps),'task_tool_steps':sum(r['kind']=='tool' for r in events.values()),'bounded_or_truncated':truncated,'source_files':len(paths)},
        'gaps':{'visual_proof':'References recorded; inspect before/after coverage' if groups['visual_reference'] else 'No screenshot or visual reference recorded',
                'validation':'Inspect recorded command and coverage; task acceptance remains separate' if groups['validation'] else 'No validation evidence recorded',
                'human_intervention':'Explicit intervention evidence recorded' if groups['intervention'] else 'No confirmed intervention recorded; user follow-ups are not proof of interference'},
        'limits':['No current checkout diff is substituted for historical changes.','No referenced local file or remote URL is read automatically.','Missing evidence means unknown, not passed, unchanged, or no intervention.']}
