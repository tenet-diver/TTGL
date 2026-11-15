"""Source-linked findings, outcomes and intervention comparisons. Stdlib only."""
import builtins
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import random
import re
import time
import uuid
import work_analytics as analytics

METRICS={
 'cost_per_task':('Cost per task','API-equivalent scenario cost per assigned task first observed in the period','cost','tasks','currency'),
 'context':('Average context','Recorded input tokens per model response','input','responses','number'),
 'large_context':('Calls over 200k context','Share of responses with more than 200,000 recorded input tokens','large','responses','percent'),
 'shell':('Shell exploration per task','Recognized shell file-exploration commands per explicitly assigned task','shell','tasks','number'),
 'failed_tools':('Failed tool calls','Share of tool calls with a known nonzero/error outcome','failed','known_tools','percent'),
 'large_output':('Shell output over 15k characters','Share of recognized shell calls with retained output over 15,000 characters','large_output','known_shell_output','percent'),
 'loops':('Repeat-failure loops per task','Runs of at least three identical failed calls per assigned task','loops','tasks','number'),
 'shell_again':('Shell file exploration again','Share of recognized shell explorations followed by another in the same session','shell_again','shell_pairs','percent'),
 'break_warnings':('Break warnings per task','Delivered Prompt after a break firings per assigned task with matched hook coverage','break_warnings','hook_tasks','number'),
 'context_warnings':('Large context warnings per task','Delivered Large context firings per assigned task with matched hook coverage','context_warnings','hook_tasks','number'),
 'needed_fix':('Needed a fix','Share of explicitly assigned tasks with a confirmed intervention record','corrected','tasks','percent'),
 'top_small':('Top-tier model on small turns','Share of priced cost on configured top-tier turns with at most two tools and a short retained answer','top_small_cost','cost','percent'),
 'main_top':('Main agent on top-tier models','Share of known-main-agent responses on a configured top-tier model','main_top','main_responses','percent'),
 'sub_top':('Subagents on top-tier models','Share of known-subagent responses on a configured top-tier model','sub_top','sub_responses','percent'),
 'explore_expensive':('Explore agent above the small tier','Share of explicitly labeled explore-agent responses outside configured small models','explore_expensive','explore_responses','percent'),
 'cache_rebuild':('Cache rebuilds after a break','Share of priced cost on explicit cache-write responses after a 5-minute idle gap','cache_rebuild_cost','cache_known_cost','percent'),
 'cache_5m':('Cache writes with a 5-minute lifetime','Share of explicit cache-write tokens labeled with a 5-minute lifetime','cache_5m','cache_ttl_write','percent'),
}


def init(store):
    with store.connection() as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS optimization_facts(event_id TEXT PRIMARY KEY REFERENCES events(id),command TEXT,signature TEXT,output_chars INTEGER,operation TEXT,commits TEXT,cache_write INTEGER,cache_5m INTEGER);
CREATE TABLE IF NOT EXISTS native_session_facts(session_id TEXT PRIMARY KEY,role TEXT,agent_type TEXT,started REAL);
CREATE TABLE IF NOT EXISTS optimization_turns(session_id TEXT,turn_id TEXT,answer_chars INTEGER,PRIMARY KEY(session_id,turn_id));
CREATE TABLE IF NOT EXISTS applied_changes(id TEXT PRIMARY KEY,title TEXT NOT NULL,at REAL NOT NULL,workspace TEXT NOT NULL,takes_effect TEXT NOT NULL,metrics TEXT NOT NULL,notes TEXT NOT NULL,created REAL NOT NULL);
''')
        if 'started' not in {r['name'] for r in c.execute('PRAGMA table_info(native_session_facts)')}:c.execute('ALTER TABLE native_session_facts ADD COLUMN started REAL')
        if not c.execute("SELECT 1 FROM settings WHERE key='optimization_facts_v1'").fetchone():
            c.execute('UPDATE files SET mtime=NULL')
            c.execute("INSERT INTO settings VALUES('optimization_facts_v1','true')")


def native_fact(item):
    from capture_proxy import sanitized
    command=item.get('command','');command=command if isinstance(command,str) else ' '.join(str(v) for v in command or [])
    arguments=item.get('arguments',item.get('input',{}))
    signature=hashlib.sha256(json.dumps([item.get('type'),command,arguments],sort_keys=True).encode()).hexdigest()
    output=item.get('aggregated_output',item.get('result'))
    output=output if isinstance(output,str) else json.dumps(output) if output is not None else None
    typ=str(item.get('type','')).lower()
    operation='edit' if typ in ('filechange','file_change') else 'check' if re.search(r'\b(pytest|unittest|jest|vitest|playwright|tsc|eslint|test|lint|check|build)\b',command) else 'shell' if re.search(r'(?:^|[;&|]\s*|\s)(cat|head|tail|sed|find|grep|ls)(?:\s|$)',command) else 'other'
    commits=[]
    if item.get('exit_code')==0 and re.search(r'\bgit\s+(?:-[^ ]+\s+)*commit\b',command):
        for match in re.finditer(r'^\[[^\]\n]*?\b([0-9a-f]{7,40})\]\s*(.*)$',(output or '')[:30000],re.M):commits.append({'kind':'Commit','ref':match[1],'message':sanitized(match[2][:1000])})
    if item.get('exit_code')==0 and re.search(r'\b(gh|git)\b',command):
        for url in re.findall(r'https://github\.com/[\w.-]+/[\w.-]+/pull/\d+',output or '')[:10]:commits.append({'kind':'Pull request','ref':url,'message':'Recorded URL; remote status not verified'})
    return (sanitized(command[:8000]),signature,len(output) if output is not None else None,operation,json.dumps(commits))


def model_config(store):
    with store.connection() as c:r=c.execute("SELECT value FROM settings WHERE key='optimization_models'").fetchone()
    return json.loads(r[0]) if r else {'top':['gpt-6.1-sol','opus','fable'],'small':['gpt-6-luna','haiku'],'short_answer':2000}


def save_models(store,v):
    if not isinstance(v,dict) or set(v)!={'top','small','short_answer'}:raise ValueError('Invalid model groups')
    for k in ('top','small'):
        if not isinstance(v[k],list) or not 1<=len(v[k])<=30 or any(not isinstance(x,str) or not x.strip() or len(x)>100 for x in v[k]):raise ValueError('Use 1..30 model-name fragments')
    if type(v['short_answer']) is not int or not 0<v['short_answer']<=20000:raise ValueError('Invalid short-answer length')
    with store.connection() as c:c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('optimization_models',json.dumps(v)));store.audit(c,'optimization_models','models',v)
    return {'ok':True}


def change(store,v):
    init(store)
    with store.connection() as c:
        if v.get('delete'):
            if not c.execute('DELETE FROM applied_changes WHERE id=?',(v.get('id'),)).rowcount:raise ValueError('Unknown change')
            store.audit(c,'delete_applied_change',v['id'],{})
            return {'ok':True}
        title=v.get('title');stamp=analytics.timestamp(v.get('at'));metrics=v.get('metrics');effect=v.get('takes_effect','immediate');workspace=v.get('workspace','');notes=v.get('notes','')
        if not isinstance(title,str) or not 0<len(title.strip())<=200 or stamp is None or stamp>time.time()+60:raise ValueError('A title and valid past application time are required')
        if effect not in ('immediate','new_sessions') or not isinstance(metrics,list) or not metrics or any(k not in METRICS for k in metrics):raise ValueError('Select known metrics and an effect boundary')
        if not isinstance(workspace,str) or len(workspace)>2000 or not isinstance(notes,str) or len(notes)>8000:raise ValueError('Invalid change scope or notes')
        ident=uuid.uuid4().hex
        c.execute('INSERT INTO applied_changes VALUES(?,?,?,?,?,?,?,?)',(ident,title.strip(),stamp,workspace,effect,json.dumps(list(dict.fromkeys(metrics))),notes,time.time()))
        store.audit(c,'record_applied_change',ident,{'title':title,'at':stamp,'takes_effect':effect})
    return {'id':ident}


def dataset(store,project=''):
    init(store)
    with store.connection() as c:
        rows=[dict(r) for r in c.execute('''SELECT e.*,a.task_id,t.title task_title,t.project_id,f.command,f.signature,f.output_chars,f.operation,f.commits,f.cache_write,f.cache_5m,s.role,s.agent_type,ot.answer_chars
FROM events e LEFT JOIN assignments a USING(session_id,turn_id) LEFT JOIN tasks t ON t.id=a.task_id LEFT JOIN optimization_facts f ON f.event_id=e.id LEFT JOIN native_session_facts s ON s.session_id=e.session_id LEFT JOIN optimization_turns ot USING(session_id,turn_id) ORDER BY e.ts,e.id''') if not project or r['project_id']==project]
        turns=[dict(r) for r in c.execute('SELECT * FROM turns')]
        known_starts={r['session_id']:r['started'] for r in c.execute('SELECT session_id,started FROM native_session_facts WHERE started IS NOT NULL')}
        projects=[dict(r) for r in c.execute('SELECT id,name,repo FROM projects ORDER BY name')]
        interventions=set()
        if c.execute("SELECT 1 FROM sqlite_master WHERE name='task_evidence_notes'").fetchone():interventions={r[0] for r in c.execute("SELECT DISTINCT task_id FROM task_evidence_notes WHERE kind='intervention' AND outcome='confirmed'")}
        changes=[dict(r) for r in c.execute('SELECT * FROM applied_changes ORDER BY at DESC')]
        hook_sessions={r[0]:(r[1],r[2]) for r in c.execute('SELECT session_id,MIN(received),MAX(received) FROM steering_events GROUP BY session_id')} if c.execute("SELECT 1 FROM sqlite_master WHERE name='steering_events'").fetchone() else {}
        logs=[dict(r) for r in c.execute('SELECT * FROM steering_log')] if c.execute("SELECT 1 FROM sqlite_master WHERE name='steering_log'").fetchone() else []
    session_start={};repos={}
    for r in turns:
        stamp=analytics.timestamp(r['start'])
        if stamp is not None:session_start[r['session_id']]=min(stamp,session_start.get(r['session_id'],stamp))
        repos[r['session_id']]=r['repo']
    scenario=analytics.rates(store);models=model_config(store);task_start={};tool_counts=defaultdict(int)
    for r in rows:
        r['time']=analytics.timestamp(r['ts']);r['workspace']=repos.get(r['session_id'],'');r['cost']=analytics.cost(json.loads(r['usage']) if r['usage'] else None,r['model'],scenario) if r['kind']=='generation' else None
        r['usage']=json.loads(r['usage']) if r['usage'] else None
        if r['task_id'] and r['time'] is not None:task_start[r['task_id']]=min(task_start.get(r['task_id'],r['time']),r['time'])
        if r['kind']=='tool':tool_counts[(r['session_id'],r['turn_id'])]+=1
    rows.sort(key=lambda r:(r['time'] if r['time'] is not None else float('inf'),r['id']))
    return {'hook_sessions':hook_sessions,'rows':rows,'session_start':known_starts,'task_start':task_start,'tool_counts':tool_counts,'models':models,'scenario':scenario,'projects':projects,'interventions':interventions,'changes':changes,'logs':logs}


def enrich(data):
    """Sequence detectors never infer identical inputs from a tool name alone."""
    previous={};runs={};loops=[];commits=[];reads=defaultdict(list);edited=set();context={};check_cycles=defaultdict(list);pending_edit={}
    for r in data['rows']:
        r['loop']=0;r['shell_again']=0;r['shell_pair']=0;r['cache_rebuild']=False
        key=r['session_id'];task=r['task_id'];group=task or key
        if r['kind']=='tool':
            if key in previous:
                prev=previous[key]
                if prev['operation']=='shell':prev['shell_pair']=1;prev['shell_again']=int(r['operation']=='shell')
            previous[key]=r
            last=runs.get(key)
            if r['failed']==1 and r['signature']:
                seq=last+[r] if last and last[-1]['signature']==r['signature'] else [r]
                runs[key]=seq
                if len(seq)==3:
                    r['loop']=1;loops.append({'kind':'Same call keeps failing','task_id':task,'task_title':r['task_title'] or 'Unassigned','message':'Identical input failed at least three times','event_ids':[x['id'] for x in seq]})
                elif len(seq)>3:loops[-1]['event_ids'].append(r['id']) if loops and loops[-1]['event_ids'][-1]==seq[-2]['id'] else None
            else:runs.pop(key,None)
            if r['operation']=='shell' and group not in edited:reads[group].append(r['id'])
            if r['operation']=='edit':
                if group not in edited and len(reads[group])>=20:loops.append({'kind':'Many reads before the first edit','task_id':task,'task_title':r['task_title'] or 'Unassigned','message':str(len(reads[group]))+' recorded shell explorations before the first native edit','event_ids':reads[group]+[r['id']]})
                edited.add(group)
                pending_edit[group]=r['id']
            if r['operation']=='check':
                if r['failed']==1 and group in pending_edit:
                    check_cycles[group].extend([pending_edit.pop(group),r['id']])
                    if len(check_cycles[group])>=6:loops.append({'kind':'Repeated edit and failed check','task_id':task,'task_title':r['task_title'] or 'Unassigned','message':'At least three edit/check failures; inspect the checks and coverage','event_ids':check_cycles[group][:]});check_cycles[group]=[]
                elif r['failed']==0:check_cycles[group]=[];pending_edit.pop(group,None)
            for commit in json.loads(r['commits'] or '[]'):commits.append({**commit,'task_id':task,'task_title':r['task_title'] or 'Unassigned','event_id':r['id'],'at':r['ts']})
        elif r['kind']=='generation':
            prior=context.get(key);usage=r['usage'] or {};current=usage.get('input_tokens')
            if prior and r['time'] is not None and prior['time'] is not None:
                r['cache_rebuild']=r['time']-prior['time']>=300 and bool(r['cache_write'])
                old=(prior['usage'] or {}).get('input_tokens')
                if current is not None and old is not None and current-old>=40000:loops.append({'kind':'Context jumped','task_id':task,'task_title':r['task_title'] or 'Unassigned','message':f'Recorded input grew by {current-old:,} tokens','event_ids':[prior['id'],r['id']]})
            context[key]=r
    data['loops']=loops;data['commits']=commits
    return data


def bucket_rows(data,rows,size,logs=()):
    buckets=defaultdict(lambda:defaultdict(float));task_seen=set()
    for r in rows:
        if r['time'] is None:continue
        b=buckets[int(r['time']//size)*size];b['records']+=1
        hook_window=data['hook_sessions'].get(r['session_id'])
        covered=bool(hook_window and hook_window[0]-5<=r['time']<=hook_window[1]+5)
        if covered:b['hook_known']+=1
        if r['task_id'] and r['task_id'] not in task_seen and r['time']==data['task_start'][r['task_id']]:
            task_seen.add(r['task_id']);b['tasks']+=1;b['hook_tasks']+=covered;b['corrected']+=r['task_id'] in data['interventions']
        if r['kind']=='tool':
            b['tools']+=1;b['known_tools']+=r['failed'] is not None;b['failed']+=r['failed']==1;b['shell']+=r['operation']=='shell';b['loops']+=r['loop'];b['shell_pairs']+=r['shell_pair'];b['shell_again']+=r['shell_again']
            if r['name'].startswith('shell') and r['output_chars'] is not None:b['known_shell_output']+=1;b['large_output']+=r['output_chars']>15000
        elif r['kind']=='generation':
            u=r['usage'] or {};context=u.get('input_tokens');b['generations']+=1
            if context is not None:b['input']+=context;b['responses']+=1;b['large']+=context>200000
            if r['cost'] is None:b['unpriced']+=1
            else:b['cost']+=r['cost']
            top=any(s.lower() in (r['model'] or '').lower() for s in data['models']['top']);small=any(s.lower() in (r['model'] or '').lower() for s in data['models']['small'])
            if r['role'] in ('main','sub'):
                b[r['role']+'_responses']+=1;b[r['role']+'_top']+=top
            if r['agent_type']=='explore':b['explore_responses']+=1;b['explore_expensive']+=not small
            if r['answer_chars'] is not None and r['cost'] is not None and top and data['tool_counts'][(r['session_id'],r['turn_id'])]<=2 and r['answer_chars']<=data['models']['short_answer']:b['top_small_cost']+=r['cost']
            elif r['answer_chars'] is None and top:b['unknown_answer']+=1
            if r['cache_write'] is not None:
                b['cache_write']+=r['cache_write']
                if r['cache_5m'] is not None:b['cache_ttl_write']+=r['cache_write'];b['cache_5m']+=r['cache_5m']
                if r['cost'] is not None:b['cache_known_cost']+=r['cost'];b['cache_rebuild_cost']+=r['cost'] if r['cache_rebuild'] else 0
    for log in logs:
        if log['rule_id'] in ('break','context'):
            b=buckets[int(log['at']//size)*size];b['break_warnings' if log['rule_id']=='break' else 'context_warnings']+=1
    return buckets


def totals(buckets):
    result=defaultdict(float)
    for b in buckets:
        for k,v in b.items():result[k]+=v
    return result


def value(metric,b):
    _,_,num,den,_=METRICS[metric]
    if metric in ('break_warnings','context_warnings') and not b.get('hook_known'):return None
    if metric in ('cost_per_task','top_small') and (b.get('unpriced',0) or not b.get('generations')):return None
    if metric=='top_small' and b.get('unknown_answer'):return None
    return b.get(num,0)/b[den] if b.get(den,0)>0 else None


def comparison(data,change,metric,now):
    at=change['at'];before=[r for r in data['rows'] if r['time'] is not None and at-14*86400<=r['time']<at and (not change['workspace'] or r['workspace']==change['workspace'])]
    after=[r for r in data['rows'] if r['time'] is not None and at<=r['time']<min(now,at+14*86400) and (not change['workspace'] or r['workspace']==change['workspace']) and (change['takes_effect']!='new_sessions' or data['session_start'].get(r['session_id'],-1)>=at)]
    def scoped_logs(start,end,allowed=None):return [l for l in data['logs'] if start<=l['at']<end and (not change['workspace'] or l['workspace']==change['workspace']) and (allowed is None or l['session_id'] in allowed)]
    left=list(bucket_rows(data,before,3600,scoped_logs(at-14*86400,at)).values());right=list(bucket_rows(data,after,3600,scoped_logs(at,min(now,at+14*86400),{r['session_id'] for r in after} if change['takes_effect']=='new_sessions' else None)).values())
    a,b=totals(left),totals(right);av,bv=value(metric,a),value(metric,b);interval=None
    if len(left)>=8 and len(right)>=8 and av is not None and bv is not None:
        rng=random.Random(change['id']+metric);deltas=[]
        for _ in range(400):
            x=value(metric,totals(rng.choices(left,k=len(left))));y=value(metric,totals(rng.choices(right,k=len(right))))
            if x is not None and y is not None:deltas.append(y-x)
        if len(deltas)>=380:
            deltas.sort();interval=[deltas[int(len(deltas)*.025)],deltas[min(len(deltas)-1,int(len(deltas)*.975))]]
    den=METRICS[metric][3]
    return {'metric':metric,'before':av,'after':bv,'before_denominator':a.get(den,0),'after_denominator':b.get(den,0),'before_hours':len(left),'after_hours':len(right),'delta':bv-av if av is not None and bv is not None else None,'interval':interval,'status':'lower' if interval and interval[1]<0 else 'higher' if interval and interval[0]>0 else 'inconclusive' if interval else 'insufficient_data'}


def dashboard(store,project='',range='30d',workspace='',clock=None):
    if range not in ('1d','7d','30d','90d','all'):raise ValueError('Invalid date range')
    now=time.time() if clock is None else clock
    data=enrich(dataset(store,project));start=now-int(range[:-1])*86400 if range!='all' else min((r['time'] for r in data['rows'] if r['time'] is not None),default=now)
    rows=[r for r in data['rows'] if r['time'] is not None and start<=r['time']<=now and (not workspace or r['workspace']==workspace)]
    selected_ids={r['id'] for r in rows};logs=[l for l in data['logs'] if start<=l['at']<=now and (not workspace or l['workspace']==workspace) and (not project or l['session_id'] in {r['session_id'] for r in data['rows']})]
    daily=bucket_rows(data,rows,86400,logs);days=[];day=int(max(start,now-365*86400)//86400)*86400
    while day<=now:days.append(day);day+=86400
    metrics=[]
    for key,(title,description,num,den,unit) in METRICS.items():
        points=[]
        for day in days:
            roll=totals(daily.get(day-i*86400,{}) for i in builtins.range(7))
            points.append({'at':day,'value':value(key,daily.get(day,{})),'average':value(key,roll)})
        last=totals(b for t,b in daily.items() if t>=int(now//86400)*86400-6*86400)
        metrics.append({'id':key,'title':title,'description':description,'unit':unit,'last_7d':value(key,last),'points':points,'numerator':num,'denominator':den})
    changes=[]
    for index,ch in enumerate(reversed(data['changes']),1):
        if workspace and ch['workspace'] and workspace!=ch['workspace']:continue
        if project and ch['workspace'] and ch['workspace'] not in {r['workspace'] for r in data['rows']}:continue
        ch={**ch,'number':index,'metrics':json.loads(ch['metrics'])};ch['comparisons']=[comparison(data,ch,key,now) for key in ch['metrics']];changes.append(ch)
    task_costs=defaultdict(list)
    for record in data['rows']:
        if record['task_id'] and record['kind']=='generation':task_costs[record['task_id']].append(record['cost'])
    priced_tasks={key:sum(values) if all(v is not None for v in values) else None for key,values in task_costs.items()}
    for record in data['commits']:record['task_cost']=priced_tasks.get(record['task_id'])
    known=[r for r in rows if r['kind']=='generation'];cost=sum(r['cost'] or 0 for r in known) if known and all(r['cost'] is not None for r in known) else None
    groups=[('large_context','Very large contexts','Consider a focused session or compact handoff and check retained quality.',[r for r in rows if r['kind']=='generation' and (r['usage'] or {}).get('input_tokens',0)>250000]),('large_output','Large tool results','Narrow reads or preserve diagnostics behind a retrievable reference.',[r for r in rows if r['kind']=='tool' and r['output_chars'] is not None and r['output_chars']>15000]),('failed_tools','Tool calls that failed','Inspect causes before changing permissions, commands or services.',[r for r in rows if r['kind']=='tool' and r['failed']==1]),('shell','Shell file exploration','Compare targeted reads/search with the current workflow.',[r for r in rows if r['operation']=='shell']),('loops','Repeated failing calls','Reassess after repeated identical failures.',[r for r in rows if r['loop']])]
    top=lambda r:any(s.lower() in (r['model'] or '').lower() for s in data['models']['top'])
    small=lambda r:any(s.lower() in (r['model'] or '').lower() for s in data['models']['small'])
    groups += [
        ('top_small','Top-tier model on small turns','Compare a configured smaller model on matched tasks; retain quality and count handoff overhead.',[r for r in rows if r['kind']=='generation' and top(r) and r['answer_chars'] is not None and r['answer_chars']<=data['models']['short_answer'] and data['tool_counts'][(r['session_id'],r['turn_id'])]<=2]),
        ('sub_top','Top-tier subagents','Evaluate a cheaper specialist for these subagent activities.',[r for r in rows if r['kind']=='generation' and r['role']=='sub' and top(r)]),
        ('explore_expensive','Explore agent above the small tier','Evaluate the configured small tier for bounded exploration.',[r for r in rows if r['kind']=='generation' and r['agent_type']=='explore' and not small(r)]),
        ('cache_rebuild','Explicit cache writes after idle gaps','Compare compact or fresh sessions after idle gaps, preserving necessary context.',[r for r in rows if r['cache_rebuild']]),
        ('cache_5m','Explicit 5-minute cache writes','Review cache lifetime against the actual workflow before changing policy.',[r for r in rows if (r['cache_5m'] or 0)>0]),
        ('corrections','Tasks with confirmed interventions','Review the confirmed intervention and turn it into a reusable acceptance check.',[r for r in rows if r['task_id'] in data['interventions']]),
    ]
    findings=[]
    for ident,title,action,items in groups:
        if not items:continue
        affected=sum(r['cost'] or 0 for r in items) if all(r['cost'] is not None for r in items) else None
        findings.append({'id':ident,'title':title,'action':action,'count':len(items),'affected_cost':affected,'estimated_saving':None,'evidence_ids':[r['id'] for r in items[:100]],'evidence_total':len(items),'observation':f'{len(items)} retained source records match this check.','basis':'Measured native counters or retained output/command metadata; not a measured saving.'})
    findings.sort(key=lambda f:-(f['affected_cost'] or 0))
    with store.connection() as c:runs=c.execute('SELECT COUNT(*) FROM analyses').fetchone()[0]
    return {'projects':data['projects'],'workspaces':sorted({r['workspace'] for r in data['rows'] if r['workspace']}),'metrics':metrics,'changes':list(reversed(changes)),'findings':findings,'spend':cost,'unit':data['scenario']['unit'],'models':data['models'],'agent_runs':runs,'loops':[l for l in data['loops'] if selected_ids.intersection(l['event_ids'])],'commits':[r for r in data['commits'] if r['event_id'] in selected_ids],'coverage':{'events':len(rows),'native_details':sum(r['signature'] is not None for r in rows if r['kind']=='tool'),'tools':sum(r['kind']=='tool' for r in rows),'chart_days_limit':365},'limits':['API-equivalent scenarios are not cash or subscription charges. Savings are unknown until a quality-preserving comparison is measured.','Missing metadata stays unknown. Cache-write TTL and agent roles require explicit source fields; cached input is not a cache write.','Needed a fix uses confirmed intervention notes, not automatic classification of follow-up prompts.','Before/after comparisons use fixed 14-day windows independent of the chart range, hourly cluster bootstrap (400 resamples), and at least eight observed hours on each side. Correlation does not establish causation.','UTC chart dates; rolling averages aggregate numerators and denominators over seven calendar days. Empty days are missing observations, not zero rates.']}
