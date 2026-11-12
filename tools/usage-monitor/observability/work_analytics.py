"""Task-centered analytics from retained native counters and evidence identities."""
from collections import defaultdict
from contextlib import nullcontext
from datetime import datetime, timezone
import json
import math

PUBLISHED_SCENARIO={'unit':'USD','as_of':'2026-11-12','name':'API-equivalent Standard token scenario','source':'https://developers.openai.com/api/docs/pricing','basis':'Standard token rates with >272K input premiums. Excludes unrecorded cache-write fees, paid tools, service/region premiums and subscription cash charges. Not an invoice.','long_context':True,'models':{'gpt-6.1-sol':{'input':2,'cached':.1,'output':10},'gpt-6-luna':{'input':.1,'cached':.01,'output':.5}}}

TASK_TYPES=['feature','bugfix','investigation','refactor','testing','documentation','operations','other','unclassified']


def rates(store):
    with store.connection() as c:r=c.execute("SELECT value FROM settings WHERE key='work_cost_rates'").fetchone()
    return json.loads(r['value']) if r else json.loads(json.dumps(PUBLISHED_SCENARIO))


def save_rates(store, value):
    if not isinstance(value,dict) or set(value)-{'unit','as_of','models','name','source','basis','long_context'}:raise ValueError('Invalid rate scenario')
    if value.get('unit') not in ('USD','credits'):raise ValueError('Unit must be USD or credits')
    if not isinstance(value.get('as_of'),str):raise ValueError('A rate date is required')
    datetime.fromisoformat(value['as_of'])
    if any(not isinstance(value[k],str) or len(value[k])>2000 for k in ('name','source','basis') if k in value):raise ValueError('Invalid scenario description')
    if 'long_context' in value and type(value['long_context']) is not bool:raise ValueError('Invalid context pricing option')
    models=value.get('models')
    if not isinstance(models,dict) or len(models)>30:raise ValueError('Configure at most 30 models')
    for name, row in models.items():
        if not isinstance(name,str) or not name.strip() or len(name)>200 or not isinstance(row,dict) or set(row)!={'input','cached','output'}:raise ValueError('Use exact model names and input/cached/output rates per million tokens')
        if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in row.values()):raise ValueError('Rates must be finite nonnegative numbers')
    with store.connection() as c:
        c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('work_cost_rates',json.dumps(value)))
        store.audit(c,'set_work_cost_scenario','rates',value)
    return value


def cost(usage, model, scenario):
    row=scenario['models'].get(model)
    if not row or not isinstance(usage,dict) or any(type(usage.get(k)) not in (int,float) for k in ('input_tokens','cached_input_tokens','output_tokens')):return None
    if any(not math.isfinite(usage[k]) or usage[k]<0 for k in ('input_tokens','cached_input_tokens','output_tokens')):return None
    fresh=usage['input_tokens']-usage['cached_input_tokens']
    if fresh<0:return None
    long=scenario.get('long_context') and model in PUBLISHED_SCENARIO['models'] and usage['input_tokens']>272000
    return ((fresh*row['input']+usage['cached_input_tokens']*row['cached'])*(2 if long else 1)+usage['output_tokens']*row['output']*(1.5 if long else 1))/1e6


def timestamp(value):
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()
    except (ValueError,TypeError,AttributeError):return None


def measurements(events, scenario):
    steps=[e for e in events if e['kind']=='tool'];responses=[e for e in events if e['kind']=='generation']
    usages=[json.loads(e['usage']) if isinstance(e['usage'],str) else e['usage'] for e in responses]
    valid=[u for u in usages if isinstance(u,dict) and type(u.get('total_tokens')) is int]
    priced=[cost(u,e['model'],scenario) for u,e in zip(usages,responses)]
    times=[e['runtime'] for e in steps if e.get('runtime_role')!='background_service_lifetime' if e['runtime'] is not None and math.isfinite(e['runtime']) and e['runtime']>=0]
    anchors=[timestamp(e['ts']) for e in events];anchors=[t for t in anchors if t is not None]
    return {'steps':len(steps),'responses':len(responses),'tokens':sum(u['total_tokens'] for u in valid) if valid and len(valid)==len(responses) else None,
            'known_tokens':sum(u['total_tokens'] for u in valid),'runtime_seconds':sum(times) if times or not steps else None,'timed_steps':len(times),'background_seconds':sum(e['runtime'] or 0 for e in steps if e.get('runtime_role')=='background_service_lifetime'),'unreviewed_steps':sum((e.get('runtime_role') or 'unreviewed') in ('uncertain','unreviewed') for e in steps),
            'activity_span_seconds':max(anchors)-min(anchors) if anchors else None,
            'cost':sum(priced) if priced and all(p is not None for p in priced) else None,
            'known_cost':sum(p for p in priced if p is not None),'priced_responses':sum(p is not None for p in priced),'actual_cost':None}


def task_data(store, task_id, attribution='measured', scenario=None, connection=None):
    if attribution not in ('measured','step_share'):raise ValueError('Unknown attribution mode')
    scenario=scenario or rates(store)
    with nullcontext(connection) if connection is not None else store.connection() as c:
        task=c.execute('SELECT t.*,p.name project_name,p.repo FROM tasks t JOIN projects p ON p.id=t.project_id WHERE t.id=?',(task_id,)).fetchone()
        if not task:raise ValueError('Unknown task')
        events=[dict(r) for r in c.execute('SELECT e.*,(SELECT aa.runtime_role FROM agent_annotations aa JOIN analyses an ON an.id=aa.analysis_id WHERE aa.event_id=e.id ORDER BY an.created DESC LIMIT 1) runtime_role FROM events e JOIN assignments a ON a.session_id=e.session_id AND a.turn_id=e.turn_id WHERE a.task_id=? ORDER BY e.ts,e.id',(task_id,))]
        analysis=c.execute('SELECT a.*,j.snapshot FROM task_history_analyses a JOIN task_history_jobs j ON j.id=a.job_id WHERE a.task_id=? ORDER BY a.created DESC LIMIT 1',(task_id,)).fetchone()
        derivation=c.execute('SELECT * FROM task_analysis_derivations WHERE analysis_id=?',(analysis['id'],)).fetchone() if analysis else None
        extra=c.execute('SELECT * FROM task_analysis_details WHERE analysis_id=?',(analysis['id'],)).fetchone() if analysis else None
        native_turns={(r['session_id'],r['turn_id']):dict(r) for r in c.execute('SELECT t.* FROM turns t JOIN assignments a USING(session_id,turn_id) WHERE a.task_id=?',(task_id,))}
        manual=[dict(r) for r in c.execute('SELECT * FROM task_step_groups WHERE task_id=? ORDER BY created,id',(task_id,))]
        model=[dict(r) for r in c.execute('SELECT * FROM task_history_subtasks WHERE analysis_id=? ORDER BY position',(analysis['id'],))] if analysis else []
        job_rows=[dict(r) for r in c.execute('SELECT id,operation,status,model,usage,error,created FROM task_history_jobs WHERE task_id=? ORDER BY created DESC',(task_id,))]
        manual_members={g['id']:[r['event_id'] for r in c.execute('SELECT event_id FROM task_step_group_members WHERE group_id=? ORDER BY position',(g['id'],))] for g in manual}
        model_members={g['id']:[r['event_id'] for r in c.execute('SELECT event_id FROM task_history_steps WHERE subtask_id=? ORDER BY position',(g['id'],))] for g in model}
    task=dict(task);steps={e['id']:e for e in events if e['kind']=='tool'};claimed=set();groups=[]
    saved=json.loads(analysis['snapshot']) if analysis else None
    analysis_stale=bool(saved and (set(s['id'] for s in saved['steps'])!=set(steps) or any(any(steps.get(s['id'],{}).get(k)!=v for k,v in s.items()) for s in saved['steps']) or any(task.get(k)!=v for k,v in saved['task'].items())))
    for source,items,members in [('user',manual,manual_members),('model',model,model_members)]:
        for g in items:
            ids=[i for i in members[g['id']] if i in steps and i not in claimed];claimed.update(ids)
            if not ids:continue
            metrics=measurements([steps[i] for i in ids],scenario)
            metrics.update(tokens=None,cost=None,known_tokens=0,known_cost=0)
            groups.append({'id':g['id'],'title':g['title'],'type':g['activity'],'summary':g['summary'],'source':source,'step_ids':ids,
                           'tags':json.loads(g['tags']) if source=='model' else [],'status':'unverified','stale':analysis_stale if source=='model' else any(any(steps.get(s['id'],{}).get(k)!=v for k,v in s.items()) for s in json.loads(g['snapshot'])),'metrics':metrics})
    turns=defaultdict(list)
    for e in events:turns[(e['session_id'],e['turn_id'])].append(e)
    import task_curation
    for turn,items in turns.items():
        ids=[e['id'] for e in items if e['kind']=='tool' and e['id'] not in claimed]
        turn_steps={e['id'] for e in items if e['kind']=='tool'}
        whole=not bool(turn_steps & claimed)
        if not ids and not (whole and any(e['kind']=='generation' for e in items)):continue
        evidence=items if whole else [steps[i] for i in ids]
        recorded=native_turns.get(turn,{})
        prompt=recorded.get('prompt') or ''
        metrics=measurements(evidence,scenario)
        groups.append({'id':'turn:'+turn[0]+':'+turn[1],'title':task_curation.prompt_title(prompt) if prompt.strip() else 'Recorded turn',
            'type':'unclassified','summary':'Recorded conversation turn. Semantic interpretation is pending.',
            'source':'log','status':'unverified','tags':[],'stale':False,'step_ids':ids,'event_ids':[e['id'] for e in evidence],
            'usage_basis':'native_turn' if whole else 'unattributed','metrics':metrics})
    for g in groups:
        g.setdefault('event_ids',g['step_ids']);g.setdefault('usage_basis','unattributed')
        if g['usage_basis']!='native_turn':g['metrics'].update(tokens=None,cost=None,known_tokens=0,known_cost=0)
    unattributed=0
    if attribution=='step_share':
        for g in groups:
            if g['usage_basis']=='native_turn':continue
            shares=defaultdict(int)
            for i in g['step_ids']:shares[(steps[i]['session_id'],steps[i]['turn_id'])]+=1
            token_sum=price_sum=0;tokens_complete=prices_complete=True
            for turn,n in shares.items():
                items=turns[turn];m=measurements(items,scenario);weight=n/sum(e['kind']=='tool' for e in items)
                tokens_complete &= m['tokens'] is not None;prices_complete &= m['cost'] is not None
                token_sum+=m['known_tokens']*weight;price_sum+=m['known_cost']*weight
            g['usage_basis']='step_share'
            g['metrics'].update(tokens=token_sum if tokens_complete else None,cost=price_sum if prices_complete else None,known_tokens=token_sum,known_cost=price_sum)
    metrics=measurements(events,scenario)
    unattributed=max(0,metrics['known_tokens']-sum(g['metrics']['known_tokens'] for g in groups))
    overhead=[]
    for j in job_rows:
        u=json.loads(j['usage']) if j['usage'] else None
        overhead.append({**j,'usage':u,'cost':cost(u,j['model'],scenario)})
    knowledge=json.loads(extra['knowledge']) if extra else []
    for index,k in enumerate(knowledge):k.update(id=analysis['id']+':'+str(index),task_id=task_id,task_title=task['title'],status='candidate',stale=analysis_stale)
    task.update(analysis_derivation=dict(derivation) if derivation else None,operation_search=' '.join(e['name'] or '' for e in steps.values()),type=extra['task_type'] if extra else 'unclassified',summary=analysis['summary'] if analysis else None,analysis_id=analysis['id'] if analysis else None,
                analysis_stale=analysis_stale,metrics=metrics,subtasks=groups,knowledge=knowledge,jobs=overhead[:10],
                mining_overhead_tokens=sum(j['usage']['total_tokens'] for j in overhead if isinstance(j['usage'],dict) and type(j['usage'].get('total_tokens')) is int),mining_overhead_complete=all(isinstance(j['usage'],dict) and type(j['usage'].get('total_tokens')) is int for j in overhead),
                unattributed_tokens=unattributed,attribution=attribution)
    return task


def aggregate(rows, kind):
    groups={}
    for row in rows:
        name=row['type'];m=row['metrics']
        g=groups.setdefault(name,dict(type=name,count=0,steps=0,runtime_seconds=0,tokens=0,cost=0,tokens_complete=True,cost_complete=True,runtime_complete=True))
        g['count']+=1;g['steps']+=m['steps'];g['runtime_seconds']+=m['runtime_seconds'] or 0
        g['tokens']+=m['tokens'] or 0;g['cost']+=m['cost'] or 0
        g['tokens_complete'] &= m['tokens'] is not None;g['cost_complete'] &= m['cost'] is not None;g['runtime_complete'] &= m['runtime_seconds'] is not None
    for g in groups.values():
        g['known_cost']=g['cost'];g['known_runtime_seconds']=g['runtime_seconds']
        if not g['runtime_complete']:g['runtime_seconds']=None
        if not g['tokens_complete']:g['tokens']=None
        if not g['cost_complete']:g['cost']=None
    return sorted(groups.values(),key=lambda r:r['steps'],reverse=True)


def overview(store, project=None, query='', status=None, task_type=None, attribution='measured', offset=0, limit=40):
    import task_history as h
    import task_discovery
    h.init(store)
    discovery_enabled=task_discovery.enabled(store)
    limit,offset=h.page(limit,offset);scenario=rates(store)
    with store.connection() as c:
        ids=[r['id'] for r in c.execute('SELECT id FROM tasks'+(' WHERE project_id=?' if project else '')+' ORDER BY updated DESC',(project,) if project else ())]
        if len(ids)>10000:raise ValueError('Narrow the project scope to fewer than 10,000 tasks')
        projects=[dict(r) for r in c.execute('SELECT * FROM projects ORDER BY name')]
        undiscovered=c.execute("SELECT count(*) FROM turns t LEFT JOIN assignments a ON a.session_id=t.session_id AND a.turn_id=t.turn_id WHERE a.task_id IS NULL AND trim(t.prompt)!=''").fetchone()[0]
        enabled=json.loads(c.execute("SELECT value FROM settings WHERE key='collection_enabled'").fetchone()[0])
    tasks=[]
    with store.connection() as shared:
        shared.execute('BEGIN')
        for ident in ids:
            row=task_data(store,ident,attribution,scenario,connection=shared)
            if status and row['status']!=status or task_type and row['type']!=task_type:continue
            text=' '.join([row['title'],row['goal'] or '',row['summary'] or '',row['operation_search'],*[g['title']+' '+g['summary']+' '+' '.join(g.get('tags',[])) for g in row['subtasks']],*[k['title']+' '+k['statement'] for k in row['knowledge']]])
            if not all(w.casefold() in text.casefold() for w in query.split()):continue
            tasks.append(row)
    subs=[s for t in tasks for s in t['subtasks']];known=sum(t['metrics']['known_tokens'] for t in tasks)
    summaries=[{k:v for k,v in t.items() if k not in ('subtasks','knowledge','jobs','goal','acceptance','outcome','repo','operation_search')} for t in tasks[offset:offset+limit]]
    return {'tasks':summaries,'total':len(tasks),'offset':offset,'next_offset':offset+limit if offset+limit<len(tasks) else None,'projects':projects,'undiscovered':undiscovered,'collection_enabled':enabled,'discovery_enabled':discovery_enabled,
            'totals':{'tasks':len(tasks),'subtasks':len(subs),'steps':sum(t['metrics']['steps'] for t in tasks),'known_tokens':known,'tasks_missing_tokens':sum(t['metrics']['tokens'] is None for t in tasks),'runtime_seconds':sum(t['metrics']['runtime_seconds'] or 0 for t in tasks) if all(t['metrics']['runtime_seconds'] is not None for t in tasks) else None,
                      'known_cost':sum(t['metrics']['known_cost'] for t in tasks),'tasks_missing_cost':sum(t['metrics']['cost'] is None for t in tasks),
                      'cost':sum(t['metrics']['cost'] for t in tasks) if tasks and all(t['metrics']['cost'] is not None for t in tasks) else None,'mining_overhead_tokens':sum(t['mining_overhead_tokens'] for t in tasks)},
            'task_types':aggregate(tasks,'task'),'subtask_types':aggregate(subs,'subtask'),'knowledge':[k for t in tasks for k in t['knowledge']][:100],
            'cost_scenario':scenario,'attribution':attribution,'limits':{'knowledge':100,'tasks_per_page':limit},
            'measurement_note':'Recorded runtime excludes identified background service lifetimes; unreviewed operations may still contain them. Runtime sums can overlap and are not task elapsed time. Response tokens are measured at task scope. Step-share subtask attribution is an optional estimate. Model-rate scenarios are not actual cash charges. Mining overhead is separate.'}


def source_steps(store, task_id, subtask_id=None, limit=100, offset=0):
    import task_history as h
    limit,offset=h.page(limit,offset);task=task_data(store,task_id)
    allowed=None
    if subtask_id:
        group=next((g for g in task['subtasks'] if g['id']==subtask_id),None)
        if not group:raise ValueError('Unknown subtask')
        allowed=set(group['event_ids'])
    with store.connection() as c:
        events=[dict(r) for r in c.execute('SELECT e.* FROM events e JOIN assignments a USING(session_id,turn_id) WHERE a.task_id=? ORDER BY e.ts,e.id',(task_id,))]
    events=[e for e in events if allowed is None or e['id'] in allowed];scenario=rates(store);rows=[]
    for i,e in enumerate(events[offset:offset+limit],offset+1):
        usage=json.loads(e['usage']) if e['usage'] else None
        rows.append({'id':e['id'],'sequence':i,'kind':e['kind'],'name':e['name'],'timestamp':e['ts'],'runtime':e['runtime'],'tokens':usage.get('total_tokens') if usage else None,'model':e['model'],'cost':cost(usage,e['model'],scenario),'failed':e['failed']})
    return {'items':rows,'total':len(events),'offset':offset,'next_offset':offset+limit if offset+limit<len(events) else None}
