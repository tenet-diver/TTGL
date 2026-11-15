"""Cost and tool views over deduplicated native counters. No inference or dependencies."""
from collections import defaultdict
from datetime import datetime
import math
import os
import re
import shlex
from zoneinfo import ZoneInfo
import activity_views as views
import work_analytics as analytics
import optimization


def number(value):
    return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def total(values):
    return sum(values) if values and all(v is not None for v in values) else None


def preview(rows):
    return {'event_ids': [r['id'] for r in rows[:100]], 'event_count': len(rows),
            'task_ids': sorted({r['task_id'] for r in rows if r.get('task_id')})}


def counters(rows, scenario):
    responses = [r for r in rows if r['kind'] == 'generation']
    metrics = views.summary(rows, scenario)
    fields = {'input': [], 'cache_read': [], 'uncached_input': [], 'output': [], 'cache_write': []}
    for r in responses:
        u = r['usage'] or {}
        inp, cached = number(u.get('input_tokens')), number(u.get('cached_input_tokens'))
        fields['input'].append(inp)
        fields['cache_read'].append(cached if inp is not None and cached is not None and cached <= inp else None)
        fields['uncached_input'].append(inp-cached if inp is not None and cached is not None and cached <= inp else None)
        fields['output'].append(number(u.get('output_tokens')))
        fields['cache_write'].append(number(r.get('cache_write')))
    metrics.update({k: total(v) for k, v in fields.items()})
    metrics['average_context'] = metrics['input']/len(responses) if responses and metrics['input'] is not None else None
    metrics['average_latency'] = metrics['model_seconds']/len(responses) if responses and metrics['model_seconds'] is not None else None
    metrics['context_cost'] = None
    return metrics


def costs(rows, scenario, zone):
    responses = [r for r in rows if r['kind'] == 'generation']
    models, days, tasks = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in responses:
        models[r['model'] or 'Unknown model'].append(r)
        days[datetime.fromtimestamp(r['time'], ZoneInfo(zone)).date().isoformat()].append(r)
    for r in rows:
        if r['task_id']: tasks[r['task_id']].append(r)
    metrics = counters(rows, scenario)
    model_rows = []
    for name, items in models.items():
        m = counters(items, scenario)
        model_rows.append({'name': name, **m, **preview(items), 'share': m['cost']/metrics['cost'] if metrics['cost'] and m['cost'] is not None else None,
                           'cost_per_call': m['cost']/m['responses'] if m['cost'] is not None else None})
    daily = []
    for date, items in sorted(days.items()):
        segments = []
        for name in models:
            subset = [r for r in items if (r['model'] or 'Unknown model') == name]
            if subset: segments.append({'name': name, **counters(subset, scenario), **preview(subset)})
        daily.append({'date': date, **counters(items, scenario), **preview(items), 'segments': segments})
    task_rows = [{'id': ident, 'title': items[0]['task_title'], 'metrics': counters(items, scenario), **preview(items)} for ident, items in tasks.items()]
    bands = []
    limits = [(0, .05, '< 0.05'), (.05, .25, '0.05–0.25'), (.25, 1, '0.25–1'), (1, 5, '1–5'), (5, 20, '5–20'), (20, float('inf'), '20+')]
    for lower, upper, name in limits:
        selected = [t for t in task_rows if t['metrics']['cost'] is not None and lower <= t['metrics']['cost'] < upper]
        bands.append({'name': name, 'count': len(selected), 'cost': sum(t['metrics']['cost'] for t in selected), 'task_ids': [t['id'] for t in selected]})
    unknown = [t['id'] for t in task_rows if t['metrics']['cost'] is None]
    bands.append({'name': 'Unknown', 'count': len(unknown), 'cost': None, 'task_ids': unknown})
    return {'metrics': metrics, 'models': sorted(model_rows, key=lambda r: r['known_cost'], reverse=True),
            'days': daily, 'bands': bands, 'tasks': task_rows,
            'unassigned': counters([r for r in responses if not r['task_id']], scenario),
            'chart_days': 365}


def shell_action(command):
    """A conservative lexical primary-program label, never a shell evaluation."""
    # Long multiline scripts are common in coding histories. Recognize compound
    # commands before tokenizing their entire bodies just to discard the tokens.
    if re.search(r'[;&|`\n]|\$\(', command): return 'Compound shell'
    try: words = shlex.split(command)
    except ValueError: return 'Unparsed shell'
    # Compound commands stay compound; do not count every word as a separate call.
    while words and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*', words[0]): words.pop(0)
    if words and words[0] == 'env':
        words.pop(0)
        while words and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*', words[0]): words.pop(0)
    if not words: return 'Unknown program'
    return os.path.basename(words[0])[:100] or 'Unknown program'


def label_tools(store, rows):
    import process_analysis
    process_labels=process_analysis.labels(store,rows) if any('process_label' not in row for row in rows) else {}
    with store.connection() as c:
        annotations = {r['event_id']: dict(r) for r in c.execute('SELECT aa.* FROM agent_annotations aa JOIN analyses a ON a.id=aa.analysis_id ORDER BY a.created')}
        rules = [dict(r) for r in c.execute('SELECT * FROM rules WHERE enabled=1 ORDER BY id')]
    result = []
    for r in rows:
        if r['kind'] != 'tool': continue
        shell = r['name'] == 'shell' or (r['name'] or '').startswith('shell /')
        family = 'Shell' if shell else r['name'] or 'Unknown tool'
        action = shell_action(r['command'] or '') if shell else family
        annotation = annotations.get(r['id'])
        interpreted=r.get('process_label') or process_labels.get(r['id'])
        category = annotation['category'] if annotation else interpreted['category'] if interpreted else next((rule['category'] for rule in rules if rule['pattern'].lower() in r['name'].lower()), 'other tools')
        result.append({**r, 'family': family, 'action': action, 'label': family+' · '+action if shell else family,
                       'target': r['command'] or 'Inspect retained source for arguments', 'category': category,
                       'category_basis': 'Agent interpretation' if annotation else 'Task-process interpretation' if interpreted else 'Fallback name rule'})
    return result


def tool_metrics(items, scenario, allocations):
    runtimes = [number(r['runtime']) for r in items if r.get('runtime_role') != 'background_service_lifetime']
    known = sum(r['failed'] in (0, 1) for r in items)
    output = [number(r.get('output_chars')) for r in items]
    return {'calls': len(items), 'failed': sum(r['failed'] == 1 for r in items), 'known_outcomes': known,
            'failure_rate': sum(r['failed'] == 1 for r in items)/known if known else None,
            'runtime': total(runtimes), 'known_runtime': sum(t for t in runtimes if t is not None),
            'timed_calls': sum(t is not None for t in runtimes), 'background_calls': sum(r.get('runtime_role') == 'background_service_lifetime' for r in items),
            'call_cost': total([allocations.get(r['id']) for r in items]), 'context_cost': None,
            'output_chars': total(output), 'known_output_chars': sum(v for v in output if v is not None),
            'categories': sorted({r['category'] for r in items}), **preview(items)}


def tools(store, rows, scenario, attribution, all_rows, zone, family='', action='', labeled=None):
    labeled = label_tools(store, rows) if labeled is None else labeled
    allocations = {}
    if attribution == 'step_share':
        # Use full native turns as denominator, even when a date filter clips them.
        turns = defaultdict(list)
        for r in all_rows: turns[(r['session_id'], r['turn_id'])].append(r)
        for items in turns.values():
            selected = [r for r in items if r['kind'] == 'tool']
            m = analytics.measurements(items, scenario)
            if selected and m['cost'] is not None:
                for r in selected: allocations[r['id']] = m['cost']/len(selected)
    families = sorted({r['family'] for r in labeled})
    selected = [r for r in labeled if (not family or r['family'] == family) and (not action or r['action'] == action)]
    groups, targets, days = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in selected:
        groups[r['label']].append(r)
        targets[(r['target'], r['action'])].append(r)
        days[datetime.fromtimestamp(r['time'], ZoneInfo(zone)).date().isoformat()].append(r)
    grouped = []
    for name, items in groups.items():
        grouped.append({'name': name, 'family': items[0]['family'], 'action': items[0]['action'], **tool_metrics(items, scenario, allocations)})
    daily = []
    top = [r['name'] for r in sorted(grouped, key=lambda r: r['calls'], reverse=True)[:7]]
    for date, items in sorted(days.items()):
        buckets = defaultdict(list)
        for r in items: buckets[r['label'] if r['label'] in top else 'Other'].append(r)
        daily.append({'date': date, 'segments': [{'name': name, **tool_metrics(values, scenario, allocations)} for name, values in buckets.items()]})
    return {'tools': sorted(grouped, key=lambda r: r['calls'], reverse=True), 'families': families,
            'targets': [{'target': key[0], 'action': key[1], **tool_metrics(items, scenario, allocations)} for key, items in targets.items()],
            'days': daily, 'metrics': tool_metrics(selected, scenario, allocations) if selected else {'calls': 0},
            'family': family, 'action': action, 'chart_days': 365}


def report(store, view, project='', workspace='', range='30d', attribution='measured', zone='Europe/Amsterdam', family='', action='', clock=None):
    if view not in ('costs', 'tools') or attribution not in ('measured', 'step_share'): raise ValueError('Invalid usage view or attribution')
    if not isinstance(family, str) or len(family)>200 or not isinstance(action, str) or len(action)>200: raise ValueError('Invalid tool filter')
    ZoneInfo(zone)
    data, rows, *_ = views.scope(store, project, workspace, range, clock)
    common = {'view': view, 'projects': data['projects'], 'workspaces': sorted({r['workspace'] for r in data['rows'] if r['workspace']}),
              'unit': data['scenario']['unit'], 'scenario': data['scenario'], 'timezone': zone, 'attribution': attribution,
              'limits': ['API-equivalent estimates are not subscription or cash charges. Unpriced responses remain unknown.',
                         'Native input includes cached input; cached tokens are never added a second time. Cache writes are shown separately when explicitly recorded.',
                         'Tool context-carry costs and result tokens are not recorded by this source. Retained output characters are not token counts.',
                         'Charts show up to 365 observed dates; all selected records contribute to totals and tables. Evidence previews show up to 100 records.']}
    result = costs(rows, data['scenario'], zone) if view == 'costs' else tools(store, rows, data['scenario'], attribution, data['rows'], zone, family, action)
    if view == 'tools':
        labeled=label_tools(store,rows)
        result['classification']={'tools':len(labeled),'interpreted':sum(r['category_basis']!='Fallback name rule' for r in labeled),'fallback':sum(r['category_basis']=='Fallback name rule' for r in labeled),'runtime_reviewed':sum(r.get('runtime_role') is not None for r in labeled)}
        grouped = defaultdict(list)
        for r in rows:
            if r['task_id']: grouped[r['task_id']].append(r)
        result['tasks'] = [{'id': ident, 'title': items[0]['task_title'], 'metrics': counters(items, data['scenario'])} for ident, items in grouped.items()]
    return {**common, **result}


def task_report(store, task_id):
    import task_history
    import task_evidence
    task_history.init(store)
    task = analytics.task_data(store, task_id)
    data, rows, turns, *_ = views.scope(store, project=task['project_id'], range='all', task_id=task_id)
    rows = [r for r in rows if r['task_id'] == task_id]
    tasks = views.project_tasks(store, {task_id}, rows, data['scenario'], prepared={task_id: task})
    outcome = views.outcome_signals(store, tasks, data, rows, turns, float('-inf'), float('inf'), '')
    packet = task_evidence.packet(store, task_id)
    anchors = [r['time'] for r in rows]
    anchors += [r['time']-number(r['runtime']) for r in rows if r.get('runtime_role') != 'background_service_lifetime' and number(r['runtime']) is not None]
    anchors += [analytics.timestamp(t.get(field)) for t in turns if t.get('task_id')==task_id for field in ('start','end')]
    anchors += [analytics.timestamp(f.get('recorded_at')) for values in packet['groups'].values() for f in values]
    anchors = [value for value in anchors if value is not None]
    timeline_range = {'start': min(anchors) if anchors else None, 'end': max(anchors) if anchors else None}
    events = []
    labeled = {r['id']: r for r in label_tools(store, rows)}
    for i, r in enumerate(rows[:1000], 1):
        u = r['usage'] or {}; tool = labeled.get(r['id'], {})
        events.append({'id': r['id'], 'sequence': i, 'ts': r['ts'], 'time': r['time'], 'kind': r['kind'],
                       'name': r['name'], 'model': r['model'], 'runtime': r['runtime'], 'runtime_role': r['runtime_role'],
                       'input': u.get('input_tokens'), 'output': u.get('output_tokens'), 'cached': u.get('cached_input_tokens'),
                       'cost': r['cost'], 'failed': r['failed'], 'agent': r['agent_type'] or r['role'] or 'Unknown agent',
                       'detail': (r['command'] or '')[:200], 'category': tool.get('category')})
    return {'task_id': task_id, 'timeline_range': timeline_range, 'packet': packet, 'outcome': outcome, 'events': events, 'event_count': len(rows),
            'phases': [{k: g[k] for k in ('id','title','type','start','end','event_ids')} for g in tasks[0]['groups']] if tasks else [],
            'metrics': counters(rows, data['scenario']), 'tools': tools(store, rows, data['scenario'], 'measured', data['rows'], 'UTC')['tools'],
            'unit': data['scenario']['unit'], 'agent_types': sorted({r['agent_type'] or r['role'] or 'Unknown agent' for r in rows})}
