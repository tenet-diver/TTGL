"""Versioned process interpretations, separate from native facts and task acceptance."""
import copy
import json
import math

OUTCOMES = ['done','failed','dead_end','in_progress','cancelled','unknown']
INTERVENTIONS = ['observed','possible','none_observed','unknown']
RUNTIME_ROLES = ['finite_operation','background_service_lifetime','mixed_or_unknown']
PROTOCOL = 'task-process-v1'


def init(store):
    with store.connection() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS task_process_results(
 analysis_id TEXT NOT NULL REFERENCES task_history_analyses(id),subtask_id TEXT NOT NULL,
 outcome TEXT NOT NULL,reason TEXT NOT NULL,confidence REAL NOT NULL,
 intervention TEXT NOT NULL,intervention_reason TEXT NOT NULL,
 source_steps TEXT NOT NULL,source_turns TEXT NOT NULL,runtime_role TEXT NOT NULL,
 PRIMARY KEY(analysis_id,subtask_id));
CREATE INDEX IF NOT EXISTS task_history_step_event ON task_history_steps(event_id);
''')


def schema(base):
    result=copy.deepcopy(base)
    properties={
        'outcome':{'type':'string','enum':OUTCOMES},
        'outcome_reason':{'type':'string','minLength':1,'maxLength':800},
        'outcome_confidence':{'type':'number','minimum':0,'maximum':1},
        'outcome_step_ids':{'type':'array','items':{'type':'string'}},
        'intervention':{'type':'string','enum':INTERVENTIONS},
        'intervention_reason':{'type':'string','minLength':1,'maxLength':800},
        'intervention_turn_ids':{'type':'array','items':{'type':'string'}},
    }
    result['properties'].update(properties);result['required']+=list(properties)
    group=result['properties']['subtasks']['items']
    additions={k:copy.deepcopy(properties[k]) for k in ('outcome','outcome_reason')}
    additions['runtime_role']={'type':'string','enum':RUNTIME_ROLES}
    group['properties'].update(additions);group['required']+=list(additions)
    return result


def snapshot(store,body):
    """Freeze the user-message evidence along with native event IDs at enqueue time."""
    from capture_proxy import sanitized
    body=copy.deepcopy(body)
    with store.connection() as c:
        rows=c.execute('SELECT t.turn_id,t.prompt FROM turns t JOIN assignments a USING(session_id,turn_id) WHERE a.task_id=? AND trim(t.prompt)!=? ORDER BY t.start,t.session_id,t.turn_id',(body['task']['id'],'')).fetchall()
    sampled=list(rows) if len(rows)<=40 else list(rows[:10])+list(rows[-30:])
    body['process_protocol']=PROTOCOL
    body['requests']=[dict(turn_id=r['turn_id'],prompt=sanitized(r['prompt'])[:2000]) for r in sampled]
    body['request_coverage']=dict(retained=len(rows),included=len(sampled),note='At most 40 user requests (first 10 and last 30 for long tasks), 2000 characters each. Missing context limits failure/intervention judgments.')
    return body


def decode(result,aliases,decoder):
    extras={k:result[k] for k in ('outcome','outcome_reason','outcome_confidence','outcome_step_ids','intervention','intervention_reason','intervention_turn_ids')}
    base={k:v for k,v in result.items() if k not in extras}
    base=decoder(base,aliases)
    ids=extras['outcome_step_ids']
    if not isinstance(ids,list) or any(i not in aliases for i in ids):raise ValueError('Unknown outcome evidence alias')
    extras['outcome_step_ids']=[event for alias in ids for event in (aliases[alias] if isinstance(aliases[alias],list) else [aliases[alias]])]
    return {**base,**extras}


def validate(result,body):
    import task_history as h
    expected={'summary','subtasks','task_type','knowledge','outcome','outcome_reason','outcome_confidence','outcome_step_ids','intervention','intervention_reason','intervention_turn_ids'}
    if not isinstance(result,dict) or set(result)!=expected:raise ValueError('Invalid process analysis')
    events={step['id'] for step in body['steps']};turns={r['turn_id'] for r in body.get('requests',[])}
    if result['outcome'] not in OUTCOMES or result['intervention'] not in INTERVENTIONS:raise ValueError('Unknown process outcome/intervention')
    for key in ('outcome_reason','intervention_reason'):h.bounded(result[key],800,key)
    confidence=result['outcome_confidence']
    if type(confidence) not in (int,float) or not math.isfinite(confidence) or not 0<=confidence<=1:raise ValueError('Invalid outcome confidence')
    for key,allowed in (('outcome_step_ids',events),('intervention_turn_ids',turns)):
        if not isinstance(result[key],list) or any(not isinstance(i,str) or i not in allowed for i in result[key]):raise ValueError('Unknown process evidence ID')
    if result['outcome']!='unknown' and not result['outcome_step_ids']:raise ValueError('Outcome interpretation requires source steps')
    if result['intervention'] in ('observed','possible') and not result['intervention_turn_ids']:raise ValueError('Intervention interpretation requires user-request evidence')
    base={k:copy.deepcopy(result[k]) for k in ('summary','subtasks','task_type','knowledge')}
    groups={}
    for group in base['subtasks']:
        if set(group)!={'title','summary','activity','tags','step_ids','confidence','outcome','outcome_reason','runtime_role'}:raise ValueError('Invalid process subtask')
        if group['outcome'] not in OUTCOMES or group['runtime_role'] not in RUNTIME_ROLES:raise ValueError('Unknown subtask outcome/runtime role')
        h.bounded(group['outcome_reason'],800,'subtask outcome reason')
        groups[tuple(sorted(group['step_ids']))]={k:group.pop(k) for k in ('outcome','outcome_reason','runtime_role')}
    metadata={k:result[k] for k in expected-{'summary','subtasks','task_type','knowledge'}}
    metadata['subtasks']=groups
    return base,metadata


def save(c,analysis_id,metadata,subtask=None):
    if subtask:
        sid,group=subtask;data=metadata['subtasks'][tuple(sorted(group['step_ids']))]
        values=(analysis_id,sid,data['outcome'],data['outcome_reason'],group['confidence'],'unknown','Task-level intervention interpretation is recorded separately.',json.dumps(group['step_ids']),'[]',data['runtime_role'])
    else:
        values=(analysis_id,'',metadata['outcome'],metadata['outcome_reason'],metadata['outcome_confidence'],metadata['intervention'],metadata['intervention_reason'],json.dumps(metadata['outcome_step_ids']),json.dumps(metadata['intervention_turn_ids']),'mixed_or_unknown')
    c.execute('INSERT INTO task_process_results VALUES(?,?,?,?,?,?,?,?,?,?)',values)


def result_rows(c,analysis_id):
    if not analysis_id or not c.execute("SELECT 1 FROM sqlite_master WHERE name='task_process_results'").fetchone():return {}
    result={}
    for row in c.execute('SELECT * FROM task_process_results WHERE analysis_id=?',(analysis_id,)):
        item=dict(row)
        for key in ('source_steps','source_turns'):item[key]=json.loads(item[key])
        item.update(basis='Model interpretation of bounded visible evidence; not independent task acceptance.',protocol=PROTOCOL)
        result[item['subtask_id']]=item
    return result


def labels(store,rows):
    """Use only latest process versions whose cited native facts still match."""
    task_ids=sorted({r.get('task_id') for r in rows if r.get('task_id')})
    if not task_ids:return {}
    with store.connection() as c:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='task_process_results'").fetchone():return {}
        analyses={r['id']:dict(r) for r in c.execute('''SELECT a.id,a.task_id,j.snapshot FROM task_history_analyses a JOIN task_history_jobs j ON j.id=a.job_id
            WHERE a.id=(SELECT x.id FROM task_history_analyses x WHERE x.task_id=a.task_id ORDER BY x.created DESC LIMIT 1) AND j.operation='process'
            AND a.task_id IN ('''+','.join('?' for _ in task_ids)+')',task_ids)}
        if not analyses:return {}
        members=[dict(r) for r in c.execute('''SELECT s.event_id,g.analysis_id,g.activity,p.runtime_role,g.confidence FROM task_history_steps s
            JOIN task_history_subtasks g ON g.id=s.subtask_id JOIN task_process_results p ON p.analysis_id=g.analysis_id AND p.subtask_id=g.id
            WHERE g.analysis_id IN ('''+','.join('?' for _ in analyses)+')',list(analyses))]
    snapshots={aid:{s['id']:s for s in json.loads(a['snapshot'])['steps']} for aid,a in analyses.items()}
    current={r['id']:r for r in rows};result={}
    for member in members:
        aid=member['analysis_id'];event=current.get(member['event_id']);saved=snapshots.get(aid,{}).get(member['event_id'])
        if not event or not saved or event.get('task_id')!=analyses[aid]['task_id']:continue
        if any(event.get(k)!=saved.get(k) for k in ('session_id','turn_id','name','ts','runtime','failed','source_line','output_hash')):continue
        result[event['id']]=dict(category=member['activity'],runtime_role=member['runtime_role'] if member['runtime_role']!='mixed_or_unknown' else None,
                                 confidence=member['confidence'],analysis_id=aid,basis='Task-process interpretation')
    return result
