"""Overall activity and native-turn activity, separate from defined task boundaries."""
from collections import Counter, defaultdict
import hashlib
import json
import math
from zoneinfo import ZoneInfo
import activity_views as views
import optimization
import task_curation
import usage_views as usage
import work_analytics as analytics


def percentile(values, quantile):
    known = sorted(v for v in values if usage.number(v) is not None)
    if not known: return None
    position = (len(known)-1)*quantile
    lo, hi = math.floor(position), math.ceil(position)
    return known[lo]+(known[hi]-known[lo])*(position-lo)


def distribution(values):
    known = [v for v in values if usage.number(v) is not None]
    return {'mean': sum(known)/len(known) if known else None, 'median': percentile(known,.5),
            'p90': percentile(known,.9), 'known': len(known), 'total': len(values)}


def turn_rows(rows, turns, projected, outcomes, scenario, start, now, known_sources):
    by_turn = defaultdict(list)
    for r in rows: by_turn[(r['session_id'],r['turn_id'])].append(r)
    groups = {t['id']: t for t in projected}
    signals = {t['task_id']: t for t in outcomes['tasks']}
    loops = outcomes['loops']
    result = []
    for turn in turns:
        key=(turn['session_id'],turn['turn_id']);items=by_turn[key];event_ids={r['id'] for r in items}
        task=groups.get(turn['task_id']);signal=signals.get(turn['task_id'])
        subgroups=[g for g in task['groups'] if event_ids.intersection(g['event_ids'])] if task else []
        begins,ends=analytics.timestamp(turn['start']),analytics.timestamp(turn['end'])
        valid_span=begins is not None and ends is not None and ends>=begins
        span=max(0,min(ends,now)-max(begins,start)) if valid_span else None
        state='pending' if task and task['classification']=='pending' else 'interpreted' if subgroups else 'stale' if task and task['classification']=='stale' else 'unclassified' if items else 'no_activity'
        result.append({'id':hashlib.sha256(json.dumps(key).encode()).hexdigest()[:24],
            'session_id':key[0],'turn_id':key[1],'task_id':turn['task_id'],'task_title':turn['task_title'],
            'title':task_curation.prompt_title(turn['prompt']) if (turn['prompt'] or '').strip() else 'Turn without retained prompt',
            'prompt':turn['prompt'],'workspace':turn['repo'],'started':begins,'ended':ends,'span':span,
            'clipped':valid_span and (begins<start or ends>now),'completed':bool(turn['completed']),
            'metrics':usage.counters(items,scenario),'interpretation':state,'interpreted':bool(subgroups),
            'coverage_complete':bool(items) and event_ids<={i for g in subgroups for i in g['event_ids']},
            'subtasks':len(subgroups),'categories':sorted({g['type'] for g in subgroups}),
            'source_state':views.source_state({key[0]},known_sources),
            'outcome':signal['status'] if signal else 'unknown',
            'signals':signal['signals'] if signal else [],'outcome_basis':'Outcome signals belong to the assigned defined task, not independently to this turn.',
            'loops':sum(bool(event_ids.intersection(loop['event_ids'])) for loop in loops),
            'models':sorted({r['model'] or 'Unknown model' for r in items if r['kind']=='generation'}),
            'agents':sorted({r['agent_type'] or r['role'] or 'Unknown agent' for r in items}),
            'event_ids':[r['id'] for r in items[:100]],'event_count':len(items)})
    return sorted(result,key=lambda r:r['started'] if r['started'] is not None else float('-inf'),reverse=True)


def defined_tasks(store, projected, selected_turns, rows, scenario, start, now):
    """Separate explicit task records from provisional discovery/model boundaries."""
    with store.connection() as c:
        excluded=set()
        for table in ('task_discovery_tasks','activity_insight_applied'):
            if c.execute('SELECT 1 FROM sqlite_master WHERE name=?',(table,)).fetchone():
                excluded.update(r[0] for r in c.execute('SELECT task_id FROM '+table))
    result=[]
    task_turns=defaultdict(list);task_rows=defaultdict(list)
    for t in selected_turns:task_turns[t['task_id']].append(t)
    for r in rows:task_rows[r['task_id']].append(r)
    for task in projected:
        if task['id'] in excluded:continue
        turns=task_turns[task['id']]
        items=task_rows[task['id']]
        spans=[max(0,min(analytics.timestamp(t['end']),now)-max(analytics.timestamp(t['start']),start)) for t in turns
               if analytics.timestamp(t['end']) is not None and analytics.timestamp(t['start']) is not None and analytics.timestamp(t['end'])>=analytics.timestamp(t['start'])]
        result.append({'id':task['id'],'title':task['title'],'status':task['status'],'categories':sorted({g['type'] for g in task['groups']}),
                       'started':min((analytics.timestamp(t['start']) for t in turns if analytics.timestamp(t['start']) is not None),default=task['start']),
                       'turns':len(turns),'metrics':usage.counters(items,scenario),'span_sum':sum(spans) if len(spans)==len(turns) and spans else None,
                       'basis':'Explicit defined task; turn spans include idle gaps and can overlap.'})
    return result


def report(store, view, project='', workspace='', range='30d', zone='Europe/Amsterdam', clock=None):
    if view not in ('overview','taskactivity'):raise ValueError('Unknown activity dashboard')
    ZoneInfo(zone)
    data,rows,turns,selected,ids,start,now=views.scope(store,project,workspace,range,clock)
    if len(selected)>10000:raise ValueError('Narrow the scope to at most 10,000 native turns')
    projected=views.project_tasks(store,ids,rows,data['scenario'])
    outcomes=views.outcome_signals(store,projected,data,rows,turns,start,now,workspace)
    native=turn_rows(rows,selected,projected,outcomes,data['scenario'],start,now,views.sources_on_disk(store))
    cost=usage.costs(rows,data['scenario'],zone)
    coverage=dict(Counter(t['interpretation'] for t in native))
    source_coverage=dict(Counter(t['source_state'] for t in native))
    interpreted=sum(t['interpreted'] for t in native)
    priced=[t['metrics']['cost'] for t in native if t['interpreted']]
    interpreted_cost=usage.total(priced) if priced else 0
    eligible=[{'id':t['id'],'title':t['title'],'state':t['classification'],'source_state':t['source_state']} for t in projected
              if t['classification'] in ('unclassified','stale') and t['event_ids'] and t['source_state']!='unavailable']
    common={'view':view,'projects':data['projects'],'workspaces':sorted({r['workspace'] for r in data['rows'] if r['workspace']}),
            'unit':data['scenario']['unit'],'timezone':zone,'source_events':len(rows),'metrics':cost['metrics'],
            'turns':native,'coverage':coverage,'source_coverage':source_coverage,'interpreted_turns':interpreted,
            'complete_turns':sum(t['coverage_complete'] for t in native),
            'interpreted_spend_share':interpreted_cost/cost['metrics']['cost'] if interpreted_cost is not None and cost['metrics']['cost'] else None,
            'eligible':eligible,'marked_tasks':defined_tasks(store,projected,selected,rows,data['scenario'],start,now),
            'statistics':{'cost':distribution([t['metrics']['cost'] for t in native]),'duration':distribution([t['span'] for t in native]),
                          'tool_calls':distribution([t['metrics']['tool_calls'] for t in native])},
            'outcomes':{**outcomes['metrics'],'signal_tasks':[t for t in outcomes['tasks'] if t['signals']]},
            'counts':{'turns':len(native),'prompts':sum(bool((t['prompt'] or '').strip()) for t in native),
                      'sessions':len({t['session_id'] for t in native}),'defined_tasks':len(ids)},
            'limits':['Native turns and explicitly defined tasks are separate counting units. A turn is not always a user task; provisional discovery and model-created boundaries are excluded from marked tasks.',
                      'Costs use the existing API-rate scenario. Unknown usage, pricing and model runtime stay unknown. Native input includes cache reads.',
                      'Recorded time is a runtime sum, can overlap and is not active elapsed time. Turn spans include idle gaps and are clipped at the selected date boundary.',
                      'Interpretation coverage counts turns with current interpreted groups; complete source-event coverage is reported separately. Pending refresh jobs may retain a current interpretation.',
                      'Confirmed fix rates use assigned defined tasks, not individual turns. No signal does not mean success. Source absence does not prove deletion.',
                      'Mean, median and 90th percentile use known observations only (linear percentile interpolation); sample counts are shown. No model analysis runs on page load.']}
    if view=='taskactivity':return common
    from datetime import datetime
    day_turns=defaultdict(set)
    for r in rows:
        if r['kind']=='generation':day_turns[datetime.fromtimestamp(r['time'],ZoneInfo(zone)).date().isoformat()].add((r['session_id'],r['turn_id']))
    for day in cost['days']:day['turn_keys']=sorted(day_turns[day['date']])
    tools=usage.tools(store,rows,data['scenario'],'measured',data['rows'],zone)
    labeled=usage.label_tools(store,rows)
    by_category=defaultdict(list);by_role=defaultdict(list)
    for r in labeled:
        by_category[r['category']].append(r)
        by_role[r.get('runtime_role') or 'unreviewed'].append(r)
    categories=[]
    for name,items in by_category.items():
        grouped=defaultdict(list)
        for item in items:grouped[item['label']].append(item)
        category_tools=[{'name':label,'family':values[0]['family'],'action':values[0]['action'],**usage.tool_metrics(values,data['scenario'],{})} for label,values in grouped.items()]
        categories.append({'name':name,**usage.tool_metrics(items,data['scenario'],{}),'tools':category_tools})
    categories.sort(key=lambda r:r['known_runtime'],reverse=True)
    roles=[{'name':name,**usage.tool_metrics(items,data['scenario'],{})} for name,items in by_role.items()]
    roles.insert(0,{'name':'model','runtime':cost['metrics']['model_seconds'],'known_runtime':sum(r['runtime'] for r in rows if r['kind']=='generation' and usage.number(r['runtime']) is not None),**usage.preview([r for r in rows if r['kind']=='generation'])})
    return {**common,'days':cost['days'],'time_by_role':roles,'top_tools':sorted(tools['tools'],key=lambda r:r['known_runtime'],reverse=True)[:7],
            'top_categories':categories[:7],'category_count':len(categories),'tool_count':len(tools['tools']),
            'tools':tools['tools'],'cache_hit_rate':cost['metrics']['cache_read']/cost['metrics']['input'] if cost['metrics']['input'] and cost['metrics']['cache_read'] is not None else None,
            'findings':optimization.source_findings(data,rows)[:3]}
