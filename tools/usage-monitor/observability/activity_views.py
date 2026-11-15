"""Evidence-backed process, agent, timeline and task-outcome projections. Stdlib only."""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import optimization
import work_analytics as analytics

RANGES = ('1d', '7d', '30d', '90d', 'all')
VIEWS = ('process', 'agents', 'timeline', 'outcomes')
CORRECTION = re.compile(r"^\s*(?:no\b|wait\b|that['’]s wrong\b|still broken\b|revert\b)", re.I)


def init(store):
    with store.connection() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS activity_sources(path TEXT PRIMARY KEY,session_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS activity_signals(id TEXT PRIMARY KEY,session_id TEXT NOT NULL,turn_id TEXT NOT NULL,event_id TEXT,kind TEXT NOT NULL,detail TEXT NOT NULL,source_line INTEGER,ts TEXT);
CREATE TABLE IF NOT EXISTS activity_files(event_id TEXT NOT NULL REFERENCES events(id),path TEXT NOT NULL,PRIMARY KEY(event_id,path));
CREATE INDEX IF NOT EXISTS activity_signal_turn ON activity_signals(session_id,turn_id);
''')
        if not c.execute("SELECT 1 FROM settings WHERE key='activity_sources_v1'").fetchone():
            c.execute('UPDATE files SET mtime=NULL')
            c.execute("INSERT INTO settings VALUES('activity_sources_v1','true')")
        if not c.execute("SELECT 1 FROM settings WHERE key='activity_views_v1'").fetchone():
            c.execute('UPDATE files SET mtime=NULL')
            c.execute("INSERT INTO settings VALUES('activity_views_v1','true')")


def native_signals(record, sid, turn, line):
    from capture_proxy import sanitized
    payload = record.get('payload') or {}
    item = payload.get('item') or {}
    kind = None
    if payload.get('type') in ('turn_aborted', 'turn_cancelled', 'task_interrupted', 'interrupt'):
        kind = 'interrupt'
    status = item.get('status')
    if payload.get('type') == 'approval_rejected' or status in ('denied', 'rejected', 'approval_denied'):
        kind = 'rejected'
    if not kind:
        return None
    ident = hashlib.sha256(f'{sid}:{turn}:{line}:{kind}'.encode()).hexdigest()
    event_id = sid + ':tool:' + str(item['id']) if item.get('id') else None
    detail = sanitized(str(payload.get('reason') or item.get('error') or status or payload['type'])[:2000])
    return (ident, sid, turn, event_id, kind, detail, line, record.get('timestamp'))


def changed_files(item, repo):
    if str(item.get('type', '')).lower() not in ('filechange', 'file_change'):
        return []
    if item.get('status') not in ('completed', 'success'):
        return []
    changes = item.get('changes')
    if isinstance(changes, dict):
        paths = [value.get('path', key) if isinstance(value, dict) else key for key, value in changes.items()]
    elif isinstance(changes, list):
        paths = [value.get('path') for value in changes if isinstance(value, dict)]
    else:
        paths = []
    # Compare recorded names only; never inspect files named by a transcript.
    return sorted({os.path.normpath(os.path.join(repo, p)) for p in paths if isinstance(p, str) and 0 < len(p) <= 4000})


def scope(store, project='', workspace='', range='30d', clock=None):
    if range not in RANGES:
        raise ValueError('Invalid date range')
    now = time.time() if clock is None else clock
    data = optimization.dataset(store, project)
    start = now - int(range[:-1]) * 86400 if range != 'all' else float('-inf')
    rows = [r for r in data['rows'] if r['time'] is not None and start <= r['time'] <= now and (not workspace or r['workspace'] == workspace)]
    with store.connection() as c:
        turns = [dict(r) for r in c.execute('SELECT t.*,a.task_id,k.title task_title,k.project_id FROM turns t LEFT JOIN assignments a USING(session_id,turn_id) LEFT JOIN tasks k ON k.id=a.task_id ORDER BY t.start,t.session_id,t.turn_id')
                 if not workspace or r['repo'] == workspace]
        roles={r['event_id']:r['runtime_role'] for r in c.execute('SELECT aa.* FROM agent_annotations aa JOIN analyses an ON an.id=aa.analysis_id ORDER BY an.created')}
    for row in rows:row['runtime_role']=roles.get(row['id'])
    selected_turns = [t for t in turns if analytics.timestamp(t['start']) is not None and analytics.timestamp(t['start']) <= now and (analytics.timestamp(t['end']) or analytics.timestamp(t['start'])) >= start and (not project or t['project_id']==project)]
    ids = {r['task_id'] for r in rows if r['task_id']} | {t['task_id'] for t in selected_turns if t['task_id']}
    if len(ids) > 10000:
        raise ValueError('Narrow the scope to fewer than 10,000 tasks')
    return data, rows, turns, selected_turns, ids, start, now


def summary(rows, scenario):
    result = analytics.measurements(rows, scenario)
    responses = [r for r in rows if r['kind'] == 'generation']
    result['model_seconds'] = sum(r['runtime'] for r in responses) if responses and all(r['runtime'] is not None for r in responses) else None
    result['errors'] = sum(r['failed'] == 1 for r in rows if r['kind'] == 'tool')
    return result


def complete_sum(values):
    return sum(values) if values and all(v is not None for v in values) else None


def sources_on_disk(store):
    with store.connection() as c:paths=c.execute('SELECT path,session_id FROM activity_sources').fetchall()
    known={}
    for path,sid in paths:
        try:present=Path(path).is_file()
        except OSError:present=False
        known[sid]=known.get(sid,False) or present
    return known


def source_state(sessions,known):
    states=[known.get(sid) for sid in sessions]
    if states and all(state is True for state in states):return 'present'
    if any(state is True for state in states):return 'partial'
    if states and all(state is False for state in states):return 'unavailable'
    return 'unknown'


def project_tasks(store, ids, rows, scenario, attribution='measured'):
    import task_history
    task_history.init(store)
    by_task = defaultdict(list)
    for r in rows:
        if r['task_id']:
            by_task[r['task_id']].append(r)
    tasks = [];known_sources=sources_on_disk(store)
    if ids:task_history.jobs(store,next(iter(ids)))
    with store.connection() as c:
        c.execute('BEGIN')
        for ident in sorted(ids):
            task = analytics.task_data(store, ident, attribution, scenario, connection=c)
            events = by_task[ident]
            allowed = {r['id']: r for r in events}
            groups = []
            full_turns=defaultdict(list)
            if attribution=='step_share':
                for record in c.execute('SELECT e.* FROM events e JOIN assignments a USING(session_id,turn_id) WHERE a.task_id=?',(ident,)):
                    full_turns[(record['session_id'],record['turn_id'])].append(dict(record))
            for g in task['subtasks']:
                if g['source'] == 'log' or g['stale']:
                    continue
                members = [allowed[i] for i in g['event_ids'] if i in allowed]
                if not members:
                    continue
                m = summary(members, scenario)
                if g['usage_basis'] == 'step_share':
                    # Allocate only selected tools against each original turn's counters.
                    shares=defaultdict(int)
                    for record in members:
                        if record['kind']=='tool':shares[(record['session_id'],record['turn_id'])]+=1
                    costs=[];tokens=[];known_cost=0
                    for key,count in shares.items():
                        original=full_turns[key];turn_metrics=analytics.measurements(original,scenario)
                        weight=count/sum(r['kind']=='tool' for r in original)
                        costs.append(turn_metrics['cost']*weight if turn_metrics['cost'] is not None else None)
                        tokens.append(turn_metrics['tokens']*weight if turn_metrics['tokens'] is not None else None)
                        known_cost+=turn_metrics['known_cost']*weight
                    m.update(cost=complete_sum(costs),tokens=complete_sum(tokens),known_cost=known_cost)
                elif not any(r['kind'] == 'generation' for r in members):
                    m.update(cost=None, tokens=None, known_cost=0)
                times = [r['time'] for r in members]
                groups.append({'id': g['id'], 'type': g['type'], 'title': g['title'], 'source': g['source'],
                               'event_ids': [r['id'] for r in members], 'start': min(times), 'end': max(times),
                               'span': max(times)-min(times) if len(times) > 1 else None,
                               'metrics': m, 'usage_basis': g['usage_basis']})
            groups.sort(key=lambda g: (g['start'], g['end'], g['id']))
            latest = c.execute("SELECT status FROM task_history_jobs WHERE task_id=? AND operation IN ('subtasks','overview') ORDER BY created DESC LIMIT 1", (ident,)).fetchone()
            state = 'pending' if latest and latest[0] in ('queued', 'running') else 'interpreted' if groups else 'stale' if task['analysis_stale'] else 'unclassified' if events else 'no_activity'
            sessions={r['session_id'] for r in events} or {r[0] for r in c.execute('SELECT DISTINCT session_id FROM assignments WHERE task_id=?',(ident,))}
            availability=source_state(sessions,known_sources)
            locations=sorted({r['workspace'] for r in events if r['workspace']}) or [task['repo']]
            tasks.append({'id': ident, 'title': task['title'], 'workspaces':locations, 'workspace': locations[0] if len(locations)==1 else 'Multiple workspaces', 'status': task['status'],
                          'outcome': task['outcome'], 'groups': groups, 'classification': state, 'source_state':availability,
                          'complete': bool(events) and {i for g in groups for i in g['event_ids']} == set(allowed),
                          'metrics': summary(events, scenario), 'start': min((r['time'] for r in events), default=None),
                          'event_ids': list(allowed)})
    return tasks


def process(tasks):
    explained = [t for t in tasks if t['groups']]
    categories, edges, variants = {}, {}, {}
    rework_tasks = set()
    rework_costs = []
    for task in explained:
        path = [g['type'] for g in task['groups']]
        variant = variants.setdefault(tuple(path), {'path': path, 'task_ids': [], 'costs': [], 'spans': []})
        variant['task_ids'].append(task['id']); variant['costs'].append(task['metrics']['cost'])
        variant['spans'].append(task['metrics']['activity_span_seconds'])
        seen = set(); previous = 'Start'
        for index, group in enumerate(task['groups']):
            name = group['type']; repeated = name in seen
            cat = categories.setdefault(name, {'name': name, 'task_ids': set(), 'subtasks': 0, 'steps': 0, 'tools': 0,
                                               'errors': 0, 'costs': [], 'spans': [], 'positions': []})
            cat['task_ids'].add(task['id']); cat['subtasks'] += 1; cat['steps'] += group['metrics']['total_steps']
            cat['tools'] += group['metrics']['tool_calls']; cat['errors'] += group['metrics']['errors']
            cat['costs'].append(group['metrics']['cost']); cat['spans'].append(group['span']); cat['positions'].append(index)
            edge = edges.setdefault((previous, name), {'from': previous, 'to': name, 'count': 0, 'task_ids': set(), 'rework': 0})
            edge['count'] += 1; edge['task_ids'].add(task['id']); edge['rework'] += repeated
            if repeated:
                rework_tasks.add(task['id']); rework_costs.append(group['metrics']['cost'])
            seen.add(name); previous = name
        edge = edges.setdefault((previous, 'End'), {'from': previous, 'to': 'End', 'count': 0, 'task_ids': set(), 'rework': 0})
        edge['count'] += 1; edge['task_ids'].add(task['id'])
    cats = []
    for cat in categories.values():
        cost = complete_sum(cat.pop('costs')); spans = cat.pop('spans'); positions = cat.pop('positions')
        cat.update(task_ids=sorted(cat['task_ids']), cost=cost, average_cost=cost / cat['subtasks'] if cost is not None else None,
                   time=complete_sum(spans), average_time=complete_sum(spans)/len(spans) if complete_sum(spans) is not None else None,
                   rank=sum(positions)/len(positions),first_position=min(positions))
        cats.append(cat)
    paths = []
    for index, v in enumerate(variants.values()):
        costs=v.pop('costs'); spans=v.pop('spans'); total=complete_sum(costs); span=complete_sum(spans)
        paths.append({**v, 'id': str(index), 'length': len(v['path']), 'tasks': len(v['task_ids']), 'share': len(v['task_ids'])/len(explained),
                      'total_cost': total, 'average_cost': total/len(costs) if total is not None else None,
                      'average_time': span/len(spans) if span is not None else None})
    return {'categories': sorted(cats, key=lambda r: (r['rank'], r['first_position'], r['name'])),
            'transitions': sorted([{**e, 'task_ids': sorted(e['task_ids']), 'tasks': len(e['task_ids'])} for e in edges.values()], key=lambda e: -e['count']),
            'paths': sorted(paths, key=lambda p: -(p['total_cost'] or 0)),
            'metrics': {'subtasks': sum(len(t['groups']) for t in explained), 'paths': len(paths), 'rework_tasks': len(rework_tasks),
                        'rework_rate': len(rework_tasks)/len(explained) if explained else None,
                        'rework_cost': complete_sum(rework_costs) if rework_costs else 0 if explained else None},
            'coverage': {name: sum(t['classification'] == name for t in tasks) for name in ('interpreted', 'pending', 'stale', 'unclassified', 'no_activity')},
            'sources':{state:sum(t['source_state']==state for t in tasks) for state in ('present','partial','unavailable','unknown')},
            'interpreted_tasks': len(explained), 'complete_tasks': sum(t['complete'] for t in tasks),
            'interpreted_spend': complete_sum([t['metrics']['cost'] for t in explained])}


def agents(rows, scenario):
    buckets = defaultdict(list)
    for r in rows:
        name = 'main' if r['role'] == 'main' else r['agent_type'] or 'Subagent (type unknown)' if r['role'] == 'sub' else 'Unknown agent'
        buckets[name].append(r)
    total = summary(rows, scenario)['cost']
    result = []
    for name, events in buckets.items():
        m = summary(events, scenario); sessions = sorted({r['session_id'] for r in events})
        result.append({'name': name, 'models': sorted({r['model'] or 'Unknown model' for r in events if r['kind']=='generation'}),
                       'runs': len(sessions), 'sessions': sessions[:100], 'metrics': m,
                       'share': m['cost']/total if total and m['cost'] is not None else None,
                       'cost_per_run': m['cost']/len(sessions) if m['cost'] is not None else None,
                       'event_ids': [r['id'] for r in events[:100]], 'event_count':len(events)})
    return sorted(result, key=lambda r: -(r['metrics']['cost'] or 0))


def timeline(rows, turns, scenario, zone, window_start=float('-inf'), window_end=float('inf')):
    tz = ZoneInfo(zone); heat = {}; by_turn = defaultdict(list)
    for r in rows:
        by_turn[(r['session_id'], r['turn_id'])].append(r)
        if r['kind'] == 'generation':
            local = datetime.fromtimestamp(r['time'], tz)
            heat.setdefault((local.weekday(), local.hour), []).append(r)
    cells = []
    for day in range(7):
        for hour in range(24):
            events = heat.get((day, hour), [])
            cells.append({'weekday': day, 'hour': hour, 'responses': len(events), 'metrics': summary(events, scenario), 'event_ids': [r['id'] for r in events[:100]], 'event_count':len(events)})
    blocks = []
    for t in turns:
        start = analytics.timestamp(t['start'])
        if start is None:continue
        end = analytics.timestamp(t['end'])
        end = max(start, end) if end is not None else start
        events = by_turn[(t['session_id'], t['turn_id'])]
        local = datetime.fromtimestamp(start, tz)
        segments=[];cursor=max(start,window_start);finish=min(end,window_end)
        while cursor<=finish and len(segments)<366:
            wall=datetime.fromtimestamp(cursor,tz)
            tomorrow=wall.date()+timedelta(days=1)
            midnight=datetime(tomorrow.year,tomorrow.month,tomorrow.day,tzinfo=tz).timestamp()
            stop=min(finish,midnight)
            end_wall=datetime.fromtimestamp(stop,tz)
            hour=wall.hour+wall.minute/60+wall.second/3600
            end_hour=24 if stop==midnight else end_wall.hour+end_wall.minute/60+end_wall.second/3600
            segments.append({'date':wall.date().isoformat(),'hour':hour,'end_hour':max(hour,end_hour)})
            if stop>=finish or stop<=cursor:break
            cursor=stop
        blocks.append({'segments':segments,'id': t['session_id']+':'+t['turn_id'], 'session_id': t['session_id'], 'turn_id': t['turn_id'], 'task_id': t['task_id'],
                       'title': t['task_title'] or (t['prompt'] or 'Unassigned turn')[:200], 'date': local.date().isoformat(),
                       'hour': local.hour+local.minute/60+local.second/3600,
                       'span': end-start, 'start': start, 'end': end,
                       'metrics': summary(events, scenario), 'event_ids': [r['id'] for r in events[:100]], 'event_count':len(events)})
    return {'heatmap': cells, 'turns': sorted(blocks, key=lambda b: b['start'], reverse=True), 'timezone': zone,
            'limits': 'Turn spans include idle gaps and may overlap. Local-hour tracks show wall time; DST repeats can overlap. Duration labels use elapsed seconds. Heatmap usage belongs to response timestamps, not an allocation over the whole span.'}


def outcome_signals(store, tasks, data, rows, turns, start, now, workspace):
    ids = {t['id'] for t in tasks}; task_map = {t['id']: t for t in tasks}
    memberships = {(t['session_id'], t['turn_id']): t['task_id'] for t in turns}
    evidence = defaultdict(list); files = defaultdict(set); row_ids = {r['id'] for r in rows}
    with store.connection() as c:
        signals = [dict(r) for r in c.execute('SELECT * FROM activity_signals')]
        for r in c.execute('SELECT * FROM activity_files'):
            if r['event_id'] in row_ids:files[r['event_id']].add(r['path'])
        notes = [dict(r) for r in c.execute("SELECT * FROM task_evidence_notes WHERE kind='intervention' AND outcome='confirmed'")] if c.execute("SELECT 1 FROM sqlite_master WHERE name='task_evidence_notes'").fetchone() else []
    for note in notes:
        if note['task_id'] in ids:
            evidence[note['task_id']].append({'kind':'confirmed_intervention','label':'Confirmed intervention','basis':'Explicit user/agent record; not independently verified', 'detail':note['title']+'\n'+note['detail'],'note_id':note['id']})
    for signal in signals:
        tid = memberships.get((signal['session_id'],signal['turn_id'])); stamp=analytics.timestamp(signal['ts'])
        if tid in ids and stamp is not None and start<=stamp<=now:
            evidence[tid].append({'kind':signal['kind'],'label':'Interrupted' if signal['kind']=='interrupt' else 'Rejected call', 'basis':'Explicit native event; not proof the task failed', 'detail':signal['detail'],'signal_id':signal['id'],'source_line':signal['source_line']})
    # Only consecutive user messages within the same recorded session can be follow-ups.
    sessions = defaultdict(list)
    for t in turns:
        if (t['prompt'] or '').strip():sessions[t['session_id']].append(t)
    followups = {}
    for sequence in sessions.values():
        sequence.sort(key=lambda t:(analytics.timestamp(t['start']) or 0,t['turn_id']))
        for previous,current in zip(sequence,sequence[1:]):
            tid=previous['task_id']; stamp=analytics.timestamp(current['start'])
            if tid not in ids or stamp is None or not start<=stamp<=now:continue
            if current['project_id'] in (None,previous['project_id']):
                followups[tid]=current['prompt']
                if CORRECTION.search(current['prompt']):
                    evidence[tid].append({'kind':'possible_correction','label':'Possible correction','basis':'Prompt-prefix heuristic; read the source before acting','detail':current['prompt'][:4000], 'session_id':current['session_id'],'turn_id':current['turn_id']})
    task_files = defaultdict(set)
    for r in rows:
        if r['task_id']:task_files[r['task_id']].update(files[r['id']])
    by_workspace = defaultdict(list)
    for t in tasks:
        if t['start'] is not None:
            for location in t['workspaces']:by_workspace[location].append(t)
    for values in by_workspace.values():
        values.sort(key=lambda t:(t['start'],t['id']))
        for previous,current in zip(values,values[1:]):
            overlap=task_files[previous['id']] & task_files[current['id']]
            if overlap:evidence[previous['id']].append({'kind':'same_files','label':'Next task edited the same files','basis':'Warning only; continued work can be intentional','detail':'\n'.join(sorted(overlap))})
    items=[]; workspace_rates={}; category_rates={}
    for task in tasks:
        signals=evidence[task['id']]; fixed=any(s['kind']=='confirmed_intervention' for s in signals)
        item={'task_id':task['id'],'title':task['title'],'workspace':task['workspace'],'started':task['start'],
              'status':'needed_fix' if fixed else 'warning' if signals else 'unknown', 'signals':signals,
              'followup':followups.get(task['id']), 'cost':task['metrics']['cost']}
        items.append(item)
        for name,dest in [*[(location,workspace_rates) for location in task['workspaces']],*[(name,category_rates) for name in {g['type'] for g in task['groups']}]]:
            group=dest.setdefault(name,{'name':name,'tasks':0,'needed_fix':0,'warnings':0,'task_ids':[]})
            group['tasks']+=1;group['needed_fix']+=fixed;group['warnings']+=not fixed and bool(signals);group['task_ids'].append(task['id'])
    for collection in (workspace_rates,category_rates):
        for g in collection.values():g['rate']=g['needed_fix']/g['tasks']
    enriched=optimization.enrich(data)
    loops=[l for l in enriched['loops'] if row_ids.intersection(l['event_ids'])]
    commits=[c for c in enriched['commits'] if c['event_id'] in row_ids]
    for c in commits:c['task_cost']=task_map[c['task_id']]['metrics']['cost'] if c['task_id'] in task_map else None
    return {'tasks':sorted(items,key=lambda t:t['started'] or 0,reverse=True), 'workspace_rates':list(workspace_rates.values()),'category_rates':list(category_rates.values()),
            'loops':loops,'commits':commits, 'metrics':{'tasks':len(tasks),'needed_fix':sum(t['status']=='needed_fix' for t in items),
            'fix_rate':sum(t['status']=='needed_fix' for t in items)/len(tasks) if tasks else None,
            'warnings':sum(t['status']=='warning' for t in items),'stuck':len({l['task_id'] for l in loops if l['task_id']}),
            'commits':len(commits)}}


def signal_detail(store, ident):
    with store.connection() as c:row=c.execute('SELECT * FROM activity_signals WHERE id=?',(ident,)).fetchone()
    if not row:raise ValueError('Unknown signal')
    return dict(row)


def report(store, view, project='', workspace='', range='30d', attribution='measured', zone='Europe/Amsterdam', clock=None):
    init(store)
    if view not in VIEWS or attribution not in ('measured','step_share'):raise ValueError('Invalid analysis view or attribution')
    try:ZoneInfo(zone)
    except (ZoneInfoNotFoundError,ValueError,TypeError):raise ValueError('Unknown timezone')
    data,rows,turns,selected,ids,start,now=scope(store,project,workspace,range,clock)
    common={'view':view,'projects':data['projects'],'workspaces':sorted({r['workspace'] for r in data['rows'] if r['workspace']}),
            'unit':data['scenario']['unit'],'timezone':zone,'attribution':attribution,
            'source_events':len(rows),'limits':['All costs are API-equivalent scenarios, not cash charges.','Semantic groups and fix signals are interpretations or explicit records; absence of a signal does not establish success.','Unknown measurements remain unknown; no per-tool model usage is fabricated.']}
    if view=='agents':return {**common,'agents':agents(rows,data['scenario'])}
    if view=='timeline':return {**common,**timeline(rows,selected,data['scenario'],zone,start,now)}
    tasks=project_tasks(store,ids,rows,data['scenario'],attribution)
    common['tasks']=[{**{k:v for k,v in t.items() if k not in ('groups','event_ids')},'event_ids':t['event_ids'][:100],'event_count':len(t['event_ids'])} for t in tasks]
    if view=='process':return {**common,**process(tasks)}
    return {**common,**outcome_signals(store,tasks,data,rows,turns,start,now,workspace)}


def analyze_selected(store, task_ids):
    import task_history
    if not isinstance(task_ids,list) or not 1<=len(task_ids)<=2 or any(not isinstance(i,str) for i in task_ids) or len(set(task_ids))!=len(task_ids):raise ValueError('Select one or two distinct tasks')
    task_history.init(store)
    known_sources=sources_on_disk(store)
    for ident in task_ids:
        body,_=task_history.snapshot(store,ident,'all')
        if not body['steps']:raise ValueError('Task has no retained steps')
        sessions={s['session_id'] for s in body['steps']}
        if source_state(sessions,known_sources)=='unavailable':raise ValueError('Known transcript sources are unavailable; restore them before analysis')
    results=[]
    for ident in task_ids:
        try:results.append({'task_id':ident,**task_history.start(store,ident,'overview')})
        except ValueError as exc:results.append({'task_id':ident,'status':'not_started','error':str(exc)})
    return {'jobs':results}
