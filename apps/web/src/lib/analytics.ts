import { pg } from './database.ts';
import { context, metrics, taskFacts, taskRows, turnRows, groupEvents, toolName, category, commonColumns, type Context } from './repository.ts';
import { collection, hash, rolling, iso, failureLoops } from './domain.ts';
import { palette, categoryColors, type NativeEvent, type Row, type Column, type Query, type Scope, type ChartSpec, type PageData, type Panel, type Metric } from './types.ts';
const numeric = (key: string, label: string, type: Column['type'] = undefined): Column => ({ key, label, numeric: true, type });
const text = (key: string, label: string, type: Column['type'] = undefined): Column => ({ key, label, type });
const colors = (keys: string[]) => keys.map((key, i) => ({ key, name: key, color: categoryColors[key.toLowerCase()] || palette[i % palette.length] }));
const ratio = (a: number, b: number) => b ? a / b : null;
const date = (e: NativeEvent) => e.time_known ? e.event_time.slice(0, 10) : 'Unknown';
const list = (id: string, title: string, description?: string): Panel => ({ id, title, list: id, description });
const chart = (id: string, title: string, kind: ChartSpec['kind'], points: Record<string, unknown>[], series: ChartSpec['series'], description?: string): Panel => ({ id, title, chart: { id, title, kind, points, series, description } });
export function tools(c: Context): Row[] { return [...groupEvents(c.events.filter(e => e.kind === 'tool'), e => toolName(e).name)].map(([name, events]) => { const m = metrics(events, c.pricing), identity = toolName(events[0]); return { id: hash(name), ...identity, href: '/tools?family=' + encodeURIComponent(identity.family) + '&action=' + encodeURIComponent(identity.action), category: [...new Set(events.map(e => category(e, c)))].join(', '), calls: events.length, errors: m.errors, failure_rate: ratio(m.errors, m.known_outcomes), runtime: m.runtime, known_runtime: m.known_runtime, call_cost: null, context_cost: null, output_chars: events.every(e => e.output_chars != null) ? events.reduce((s, e) => s + Number(e.output_chars), 0) : null, timed: m.timed }; }).sort((a, b) => b.calls - a.calls); }
export function models(c: Context): Row[] { const total = metrics(c.events, c.pricing).known_cost; return [...groupEvents(c.events.filter(e => e.kind === 'generation'), e => e.model || 'Unknown')].map(([name, events]) => { const m = metrics(events, c.pricing); return { id: name, name, href: '/costs?model=' + encodeURIComponent(name), calls: events.length, cost: m.cost, share: m.cost != null ? ratio(m.cost, total) : null, input: m.input, uncached: m.input != null && m.cached != null && m.cache_write != null && m.input >= m.cached + m.cache_write ? m.input - m.cached - m.cache_write : null, cached: m.cached, cache_write: m.cache_write, output: m.output, cost_per_call: m.cost != null ? m.cost / events.length : null, latency: events.every(e => e.runtime != null) ? events.reduce((s, e) => s + Number(e.runtime), 0) / events.length : null }; }).sort((a, b) => Number(b.cost) - Number(a.cost)); }
export function process(c: Context) {
    const categories = new Map<string, {
        events: Set<string>;
        tasks: Set<string>;
        subtasks: number;
        spans: number[];
        positions: number[];
    }>(), edges = new Map<string, {
        from: string;
        to: string;
        times: number;
        taskIds: Set<string>;
        rework: number;
    }>(), paths = new Map<string, {
        path: string[];
        ids: string[];
    }>();
    let explained = 0, reworked = 0;
    for (const task of c.tasks) {
        const f = taskFacts(c, task.id);
        if (!f.complete)
            continue;
        explained++;
        const path = f.groups.map(g => g.category), visited = new Set<string>();
        let back = false;
        for (const group of f.groups) {
            let item = categories.get(group.category);
            if (!item) {
                item = { events: new Set(), tasks: new Set(), subtasks: 0, spans: [], positions: [] };
                categories.set(group.category, item);
            }
            item.subtasks++;
            item.positions.push(Number(group.position));
            item.tasks.add(task.id);
            group.event_ids.forEach(id => item.events.add(id));
            const times = f.events.filter(e => group.event_ids.includes(e.id) && e.time_known).map(e => +new Date(e.event_time));
            if (times.length)
                item.spans.push((Math.max(...times) - Math.min(...times)) / 1000);
        }
        const all = ['Start', ...path, 'End'];
        for (let i = 1; i < all.length; i++) {
            const key = JSON.stringify([all[i - 1], all[i]]);
            let edge = edges.get(key);
            if (!edge) {
                edge = { from: all[i - 1], to: all[i], times: 0, taskIds: new Set(), rework: 0 };
                edges.set(key, edge);
            }
            edge.times++;
            edge.taskIds.add(task.id);
            if (visited.has(all[i]) && all[i] !== 'End') {
                edge.rework++;
                back = true;
            }
            visited.add(all[i]);
        }
        if (back)
            reworked++;
        const key = JSON.stringify(path);
        if (!paths.has(key))
            paths.set(key, { path, ids: [] });
        paths.get(key)!.ids.push(task.id);
    }
    const categoryRows = [...categories].map(([name, item]) => { const events = c.events.filter(e => item.events.has(e.id)), m = metrics(events, c.pricing); return { id: name, name, rank: item.positions.reduce((a, b) => a + b, 0) / item.positions.length, href: '/tasks?category=' + encodeURIComponent(name), subtasks: item.subtasks, tasks: item.tasks.size, steps: events.length, tools: m.tools, errors: m.errors, time: item.spans.length ? item.spans.reduce((a, b) => a + b, 0) : null, cost: m.cost, avg_cost: m.cost != null ? m.cost / item.subtasks : null, avg_time: item.spans.length ? item.spans.reduce((a, b) => a + b, 0) / item.spans.length : null, task_ids: [...item.tasks] }; }).sort((a, b) => a.rank - b.rank);
    return { explained, reworked, categories: categoryRows, transitions: [...edges].map(([id, e]) => ({ id, from: e.from, to: e.to, times: e.times, tasks: e.taskIds.size, rework: e.rework, task_ids: [...e.taskIds] })).sort((a, b) => b.times - a.times), paths: [...paths].map(([id, p]) => { const events = c.events.filter(e => p.ids.includes(c.assignments.get(e.turn_key) || '')), m = metrics(events, c.pricing); return { id, path: p.path.join(' → '), length: p.path.length, tasks: p.ids.length, share: ratio(p.ids.length, explained), cost: m.cost, avg_cost: m.cost != null ? m.cost / p.ids.length : null, task_ids: p.ids }; }) };
}
export function outcomes(c: Context) {
    const rows = taskRows(c);
    const visible = new Set(c.tasks.map(t => t.id));
    const fixed = new Set(c.notes.filter(n => visible.has(String(n.task_id)) && n.kind === 'intervention' && n.outcome === 'confirmed').map(n => String(n.task_id)));
    const nextTurns = new Map<string, typeof c.turns[number]>(), sessions = new Map<string, typeof c.turns>();
    for (const turn of c.turns) {
        if (!sessions.has(turn.session_id))
            sessions.set(turn.session_id, []);
        sessions.get(turn.session_id)!.push(turn);
    }
    for (const turns of sessions.values()) {
        turns.sort((a, b) => +new Date(a.started_at || 0) - +new Date(b.started_at || 0));
        for (let i = 0; i < turns.length - 1; i++)
            if (turns[i].finished_at && turns[i + 1].started_at && +new Date(turns[i + 1].started_at!) > +new Date(turns[i].finished_at!))
                nextTurns.set(turns[i].turn_key, turns[i + 1]);
    }
    const candidates = new Map<string, {
        signals: string[];
        follow_up: string;
    }>();
    for (const task of c.tasks) {
        const f = taskFacts(c, task.id), signals: string[] = [];
        let follow_up = '';
        for (const turn of f.turns) {
            const source = turn.source as {
                signals?: {
                    kind: string;
                }[];
            } | undefined;
            for (const signal of source?.signals || [])
                if (['interrupt', 'rejected'].includes(signal.kind))
                    signals.push(signal.kind === 'interrupt' ? 'Native interruption recorded' : 'Native approval rejection recorded');
            const next = nextTurns.get(turn.turn_key);
            if (next && /^\s*(?:no\b|wait\b|that['’]s wrong\b|still broken\b|revert\b)/i.test(next.prompt)) {
                signals.push('Possible correction in the following prompt');
                follow_up = next.prompt;
            }
        }
        if (signals.length)
            candidates.set(task.id, { signals: [...new Set(signals)], follow_up });
    }
    const fixRows = rows.filter(r => fixed.has(r.id) || candidates.has(r.id) || String(r.outcome).match(/needed.?fix|warning/i)).map(r => ({ ...r, outcome: fixed.has(r.id) ? 'Needed a fix' : 'Warning signs', signals: fixed.has(r.id) ? 'Confirmed intervention' : candidates.get(r.id)?.signals.join('; ') || 'Recorded outcome; inspect evidence', follow_up: candidates.get(r.id)?.follow_up || c.notes.filter(n => n.task_id === r.id && n.kind === 'intervention').map(n => n.detail).join('; ') }));
    const warned = new Set(fixRows.filter(r => r.outcome === 'Warning signs').map(r => r.id));
    const loops = c.tasks.flatMap(task => taskFacts(c, task.id).loops.map((loop, i) => ({ id: task.id + ':' + i, title: task.title, href: '/tasks/' + task.id + '?steps=' + encodeURIComponent(loop.ids.join(',')), task_id: task.id, loop: loop.type, detail: loop.detail, steps: loop.ids.length, cost: null, event_ids: loop.ids })));
    const workspace = new Map<string, Row>(), categories = new Map<string, Row>();
    for (const task of c.tasks) {
        const f = taskFacts(c, task.id);
        for (const name of [...new Set(f.turns.map(t => t.workspace))]) {
            if (!workspace.has(name))
                workspace.set(name, { id: name, name, tasks: 0, fixed: 0, warnings: 0, rate: null });
            const r = workspace.get(name)!;
            r.tasks = Number(r.tasks) + 1;
            if (warned.has(task.id))
                r.warnings = Number(r.warnings) + 1;
            if (fixed.has(task.id))
                r.fixed = Number(r.fixed) + 1;
            r.rate = ratio(Number(r.fixed), Number(r.tasks));
        }
        if (f.complete)
            for (const name of [...new Set(f.groups.map(g => g.category))]) {
                if (!categories.has(name))
                    categories.set(name, { id: name, name, tasks: 0, fixed: 0, warnings: 0, rate: null });
                const r = categories.get(name)!;
                r.tasks = Number(r.tasks) + 1;
                if (warned.has(task.id))
                    r.warnings = Number(r.warnings) + 1;
                if (fixed.has(task.id))
                    r.fixed = Number(r.fixed) + 1;
                r.rate = ratio(Number(r.fixed), Number(r.tasks));
            }
    }
    const commits = c.events.filter(e => /\bgit\s+(?:commit|push)|\bgh\s+pr\s+create/.test(e.command)).map(e => { const taskId = c.assignments.get(e.turn_key), task = c.tasks.find(t => t.id === taskId); return { id: e.id, change: /\bgh\s+pr/.test(e.command) ? 'Pull request command' : 'Git command', ref: 'Not retained', message: e.command, title: task?.title || 'Unassigned turn', href: task ? '/tasks/' + task.id : null, cost: taskId ? taskFacts(c, taskId).metrics.cost : null, at: e.time_known ? e.event_time : null, event_id: e.id }; });
    return { fixes: fixRows, loops, commits, workspaces: [...workspace.values()], categories: [...categories.values()], confirmed: fixed.size };
}
export function findings(c: Context): Row[] {
    const checks = [{ id: 'context', title: 'Very large contexts', category: 'Context', test: (e: NativeEvent) => e.kind === 'generation' && Number(e.input_tokens) > 250000, action: 'Start a new session when the topic changes, compact earlier, and delegate research with a focused handoff.' }, { id: 'failures', title: 'Tool calls that failed', category: 'Tools', test: (e: NativeEvent) => e.kind === 'tool' && e.failed === 1, action: 'Inspect failed source calls and fix missing paths, permissions or unavailable tools.' }, { id: 'shell', title: 'Shell file exploration', category: 'Workflow', test: (e: NativeEvent) => e.kind === 'tool' && /\b(cat|head|tail|sed|find|grep|ls)\b/.test(e.command), action: 'Use targeted reads and searches; compare verification quality before changing the workflow.' }, { id: 'large-output', title: 'Large tool results', category: 'Context', test: (e: NativeEvent) => e.kind === 'tool' && Number(e.output_chars) > 15000, action: 'Narrow results and preserve complete diagnostics behind a source reference.' }, { id: 'cache', title: 'Explicit 5-minute cache writes', category: 'Cache', test: (e: NativeEvent) => Number(e.cache_5m_tokens) > 0, action: 'Review the recorded cache lifetime against actual return-to-session patterns.' }];
    const afterGaps = new Set<string>();
    for (const values of groupEvents(c.events.filter(e => e.kind === 'generation' && e.time_known), e => e.session_id).values())
        for (let i = 1; i < values.length; i++)
            if (+new Date(values[i].event_time) - +new Date(values[i - 1].event_time) >= 300000 && Number(values[i].cache_write_tokens) > 0)
                afterGaps.add(values[i].id);
    checks.push({ id: 'cache-gap', title: 'Cache writes after idle gaps', category: 'Cache', test: e => afterGaps.has(e.id), action: 'Inspect the retained gap and cache counters. Compare focused sessions or compaction while preserving task quality.' });
    const top = c.tiers?.top || [], small = c.tiers?.small || [], turnGroups = groupEvents(c.events, e => e.turn_key), shortTurns = new Set(c.turns.filter(t => t.completed && typeof (t.source as Record<string, unknown>)?.answer_chars === 'number' && Number((t.source as Record<string, unknown>).answer_chars) <= 1200 && (turnGroups.get(t.turn_key) || []).filter(e => e.kind === 'tool').length <= 2).map(t => t.turn_key));
    checks.push({ id: 'top-small', title: 'Top-tier model on small turns', category: 'Model', test: e => e.kind === 'generation' && top.includes(e.model) && shortTurns.has(e.turn_key), action: 'Compare a configured smaller model on these short turns and verify equivalent quality before changing the default.' });
    checks.push({ id: 'subagent-top', title: 'Subagents on top-tier models', category: 'Model', test: e => e.kind === 'generation' && (e.role === 'sub' || Boolean(e.agent_type)) && top.includes(e.model), action: 'Inspect the delegated work and compare a smaller model with the same evidence and verification checks.' });
    checks.push({ id: 'explore-model', title: 'Explore agent outside the configured small tier', category: 'Model', test: e => e.kind === 'generation' && small.length > 0 && e.agent_type.toLowerCase() === 'explore' && !small.includes(e.model), action: 'Review Explore-agent model selection and validate retrieval quality before changing it.' });
    const repeated = new Set<string>();
    for (const events of turnGroups.values())
        for (const loop of failureLoops(events))
            for (const id of loop.ids)
                repeated.add(id);
    checks.push({ id: 'repeat-loops', title: 'Repeated failed calls', category: 'Workflow', test: e => repeated.has(e.id), action: 'Inspect the identical failed source calls, fix their cause, and verify recovery rather than repeating the same request.' });
    const warningTasks = new Set(outcomes(c).fixes.map(r => r.id));
    checks.push({ id: 'corrections', title: 'Tasks with correction or intervention signals', category: 'Workflow', test: e => warningTasks.has(c.assignments.get(e.turn_key) || ''), action: 'Read the follow-up prompts and native signals. Heuristic corrections can be wrong; confirm the evidence before making a rule.' });
    return checks.flatMap(check => {
        const events = c.events.filter(check.test);
        if (!events.length)
            return [];
        const m = metrics(events, c.pricing);
        return [{ id: check.id, title: check.title, category: check.category, observation: `${events.length} retained source records match this check.`, action: check.action, count: events.length, affected_cost: m.cost, savings: null, event_ids: events.map(e => e.id) }];
    });
}
export function daily(c: Context, measure: 'cost' | 'tokens' | 'calls' = 'cost', by: 'model' | 'tool' | 'type' = 'model') {
    const keys = by === 'type' ? ['Cache read', 'Cache write', 'Uncached input', 'Output'] : [...new Set(c.events.filter(e => by === 'model' ? e.kind === 'generation' : e.kind === 'tool').map(e => by === 'model' ? e.model || 'Unknown' : toolName(e).name))].slice(0, 7);
    const days = [...groupEvents(c.events.filter(e => e.time_known), date)].map(([date, events]) => {
        const point: Record<string, unknown> = { date };
        for (const key of keys) {
            if (by === 'type') {
                const m = metrics(events, c.pricing);
                point[key] = key === 'Cache read' ? m.cached : key === 'Cache write' ? m.cache_write : key === 'Output' ? m.output : m.input != null && m.cached != null && m.cache_write != null && m.input >= m.cached + m.cache_write ? m.input - m.cached - m.cache_write : null;
            }
            else {
                const subset = events.filter(e => (by === 'model' ? e.model || 'Unknown' : toolName(e).name) === key && (by === 'model' ? e.kind === 'generation' : e.kind === 'tool'));
                const m = metrics(subset, c.pricing);
                point[key] = measure === 'calls' ? subset.length : measure === 'tokens' ? m.tokens : m.cost;
            }
        }
        return point;
    }).sort((a, b) => String(a.date).localeCompare(String(b.date)));
    return { keys, points: days };
}
export async function recordData(kind: string, scope: Scope, query: Query, extra: URLSearchParams) {
    let rows: Row[] = [], columns: Column[] = [];
    const db = pg();
    if (['rules', 'live', 'rule-log', 'changes', 'jobs', 'sources', 'categorization', 'knowledge', 'archives'].includes(kind)) {
        if (kind === 'rules') {
            const data = await db `SELECT r.*,count(l.id) FILTER(WHERE l.at>now()-interval '7 days')::integer AS fired,max(l.at) AS last_fired FROM steering_rules r LEFT JOIN steering_log l ON l.rule_id=r.id GROUP BY r.id ORDER BY r.builtin DESC,r.id`;
            rows = data.map(r => ({ ...r, id: String(r.id), fires_when: triggerDescription(r) }));
            columns = [text('name', 'Rule'), text('fires_when', 'Fires when'), text('mode', 'Mode'), text('enabled', 'On'), numeric('fired', 'Fired, 7d'), text('last_fired', 'Last fired', 'date')];
        }
        if (kind === 'live') {
            rows = await db `SELECT * FROM live_sessions WHERE last_seen>now()-interval '24 hours' AND (${scope.workspace}='' OR workspace=${scope.workspace}) ORDER BY last_seen DESC` as unknown as Row[];
            columns = [text('id', 'Session'), text('workspace', 'Workspace'), text('status', 'Status', 'badge'), text('last_seen', 'Last seen', 'date'), numeric('context_tokens', 'Context', 'tokens'), numeric('task_cost', 'Reported cost', 'money'), text('paused', 'Paused')];
        }
        if (kind === 'rule-log') {
            rows = await db `SELECT * FROM steering_log WHERE (${scope.workspace}='' OR workspace=${scope.workspace}) ORDER BY at DESC LIMIT 2000` as unknown as Row[];
            columns = [text('at', 'When', 'date'), text('mode', 'What', 'badge'), text('rule_name', 'Rule'), text('message', 'Message'), text('call', 'Call', 'code'), text('workspace', 'Workspace')];
        }
        if (kind === 'changes') {
            const { changeRows } = await import('./pages.ts');
            rows = await changeRows(scope);
            columns = [text('title', 'Change'), text('comparison', 'Metric comparison')];
        }
        if (kind === 'jobs') {
            rows = await db `SELECT j.id,j.task_id,t.title,j.operation,j.status,j.model,j.usage,j.error,j.created_at,j.finished_at FROM analysis_jobs j LEFT JOIN tasks t ON t.id=j.task_id WHERE (${scope.project}='' OR t.project_id=${scope.project}) ORDER BY j.created_at DESC LIMIT 10000` as unknown as Row[];
            rows = rows.map(r => ({ ...r, tokens: (r.usage as {
                    total_tokens?: number;
                } | null)?.total_tokens ?? null }));
            columns = [text('title', 'Task', 'link'), text('operation', 'Analysis'), text('status', 'Status', 'badge'), text('model', 'Model'), numeric('tokens', 'Analysis tokens', 'tokens'), text('error', 'Details'), text('created_at', 'Queued', 'date')];
        }
        if (kind === 'archives') {
            rows = await db `SELECT id,provider,source_path,bytes,status,content_sha256,verified_at,CASE WHEN status='retained' THEN id ELSE NULL END AS archive_id FROM raw_archives ORDER BY created_at DESC LIMIT 10000` as unknown as Row[];
            columns = [text('source_path', 'Raw source'), text('provider', 'Format'), numeric('bytes', 'Bytes'), text('status', 'Retention', 'badge'), text('verified_at', 'Verified', 'date'), text('archive_id', 'Original bytes'), { key: 'content_sha256', label: 'SHA-256', hidden: true }];
        }
        if (kind === 'sources') {
            rows = await db `SELECT path AS id,path,bytes,error,imported_at,archive_id FROM source_files ORDER BY imported_at DESC LIMIT 10000` as unknown as Row[];
            columns = [text('path', 'Source'), text('archive_id', 'Verified raw archive'), numeric('bytes', 'Bytes', 'tokens'), text('error', 'Error'), text('imported_at', 'Last ingest', 'date')];
        }
        if (kind === 'categorization') {
            rows = await db `SELECT * FROM categorization_rules ORDER BY priority,id` as unknown as Row[];
            columns = [text('name', 'Rule'), numeric('priority', 'Order'), text('pattern', 'Literal pattern'), text('category', 'Category'), text('activity_type', 'Activity type'), text('enabled', 'Enabled')];
        }
        if (kind === 'knowledge') {
            rows = await db `SELECT a.id,a.task_id,t.title AS task_title,a.result FROM analyses a JOIN tasks t ON t.id=a.task_id WHERE (${scope.project}='' OR t.project_id=${scope.project}) ORDER BY a.created_at DESC LIMIT 10000` as unknown as Row[];
            rows = rows.flatMap(r => ((r.result as {
                knowledge?: Record<string, unknown>[];
            }).knowledge || []).map((k, i) => ({ ...k, id: r.id + ':' + i, task_title: r.task_title, href: '/tasks/' + r.task_id, status: 'Candidate; unverified' })));
            columns = [text('title', 'Knowledge'), text('statement', 'Lesson'), text('task_title', 'Source task', 'link'), text('status', 'Status', 'badge'), numeric('confidence', 'Model confidence')];
        }
    }
    else {
        const task = extra.get('task');
        const c = await context({ ...scope, ...(task ? { task, range: 'all' } : {}) });
        const source = (task ? taskFacts(c, task).events : c.events).filter(e => (!extra.get('day') || e.event_time.slice(0, 10) === extra.get('day')) && (!extra.get('model') || e.model === extra.get('model')) && (!extra.get('tool') || toolName(e).name === extra.get('tool')));
        if (kind === 'tasks' || kind === 'marked') {
            rows = kind === 'tasks' ? turnRows(c) : taskRows(c);
            if (kind === 'marked' && !extra.get('task_ids'))
                rows = rows.filter(r => !(r.source as Record<string, unknown>)?.native_turn);
            if (extra.get('day')) {
                const keys = new Set(source.map(e => e.turn_key)), tasks = new Set(source.map(e => c.assignments.get(e.turn_key)));
                rows = rows.filter(r => kind === 'tasks' ? keys.has(r.id) : tasks.has(r.id));
            }
            if (extra.get('category'))
                rows = rows.filter(r => String(r.categories || '').includes(extra.get('category')!));
            columns = commonColumns();
            if (kind === 'marked')
                columns = [...commonColumns().filter(col => !['models', 'session_id', 'workspace'].includes(col.key)), numeric('turns', 'Turns'), text('categories', 'Categories')];
        }
        if (kind === 'steps') {
            rows = source.map((e, i) => ({ id: e.id, sequence: i + 1, at: e.time_known ? e.event_time : null, kind: e.kind === 'generation' ? 'API call' : e.kind === 'compaction' ? 'compaction' : e.failed === 1 ? 'tool · error' : 'tool', name: e.kind === 'generation' ? e.model : e.name, runtime: e.runtime, input: e.input_tokens, output: e.kind === 'tool' ? null : e.output_tokens, cost: metrics([e], c.pricing).cost, context_cost: null, agent: e.agent_type || e.role || 'Unknown', detail: e.command, event_id: e.id }));
            if (extra.get('ids')) {
                const ids = new Set(extra.get('ids')!.split(','));
                rows = rows.filter(r => ids.has(r.id));
            }
            columns = [numeric('sequence', '#'), text('at', 'Time', 'date'), text('kind', 'Type', 'badge'), text('name', 'Step'), numeric('runtime', 'Duration', 'duration'), numeric('input', 'Tokens in', 'tokens'), numeric('output', 'Tokens out', 'tokens'), numeric('cost', 'Cost', 'money'), numeric('context_cost', 'Context cost', 'money'), text('agent', 'Agent'), text('detail', 'Detail', 'code')];
        }
        if (kind === 'tools') {
            rows = tools({ ...c, events: source });
            if (extra.get('family'))
                rows = rows.filter(r => r.family === extra.get('family'));
            columns = [text('name', extra.get('family') ? 'Action' : 'Tool', 'link'), text('category', 'Category'), numeric('calls', 'Calls'), numeric('failure_rate', 'Failed', 'percent'), numeric('runtime', 'Total time', 'duration'), numeric('call_cost', 'Call cost', 'money'), numeric('context_cost', 'Context cost', 'money'), numeric('output_chars', 'Result characters', 'tokens'), numeric('timed', 'Calls with timing')];
        }
        if (kind === 'targets') {
            rows = [...groupEvents(source.filter(e => e.kind === 'tool' && (!extra.get('family') || toolName(e).family === extra.get('family')) && (!extra.get('action') || toolName(e).action === extra.get('action'))), e => e.command || e.name)].map(([target, events]) => ({ id: hash(target), target, action: toolName(events[0]).action, calls: events.length, errors: events.filter(e => e.failed === 1).length, event_ids: events.map(e => e.id) }));
            columns = [text('target', 'Target', 'code'), text('action', 'Action'), numeric('calls', 'Calls'), numeric('errors', 'Failed')];
        }
        if (kind === 'models') {
            rows = models(c);
            columns = [text('name', 'Model'), numeric('calls', 'API calls'), numeric('cost', 'Cost', 'money'), numeric('share', 'Share', 'percent'), numeric('uncached', 'Uncached input', 'tokens'), numeric('cached', 'Cache read', 'tokens'), numeric('cache_write', 'Cache write', 'tokens'), numeric('output', 'Output', 'tokens'), numeric('cost_per_call', 'Cost / call', 'money'), numeric('latency', 'Avg latency', 'duration')];
        }
        if (kind === 'agents') {
            const total = metrics(c.events, c.pricing).known_cost;
            rows = [...groupEvents(c.events, e => e.agent_type || e.role || 'Unknown agent')].map(([name, events]) => { const m = metrics(events, c.pricing); return { id: name, name, models: [...new Set(events.map(e => e.model).filter(Boolean))].join(', '), runs: new Set(events.map(e => e.session_id)).size, calls: m.responses, tools: m.tools, errors: m.errors, time: metrics(events.filter(e => e.kind === 'generation'), c.pricing).runtime, tokens: m.tokens, cost: m.cost, share: m.cost != null ? ratio(m.cost, total) : null, cost_per_run: m.cost != null ? m.cost / new Set(events.map(e => e.session_id)).size : null, event_ids: events.map(e => e.id) }; });
            columns = [text('name', 'Agent'), text('models', 'Models'), numeric('runs', 'Runs'), numeric('calls', 'API calls'), numeric('tools', 'Tool calls'), numeric('errors', 'Errors'), numeric('time', 'Model time', 'duration'), numeric('tokens', 'Tokens', 'tokens'), numeric('cost', 'Cost', 'money'), numeric('share', 'Share', 'percent'), numeric('cost_per_run', 'Cost / run', 'money')];
        }
        if (['transitions', 'categories', 'paths'].includes(kind)) {
            const p = process(c);
            rows = p[kind as 'transitions' | 'categories' | 'paths'];
            columns = kind === 'transitions' ? [text('from', 'From'), text('to', 'To'), numeric('times', 'Times'), numeric('tasks', 'Tasks'), numeric('rework', 'Rework')] : kind === 'paths' ? [text('path', 'Path'), numeric('length', 'Length'), numeric('tasks', 'Tasks'), numeric('share', 'Share of tasks', 'percent'), numeric('avg_cost', 'Avg cost', 'money'), numeric('cost', 'Total cost', 'money')] : [text('name', 'Category', 'link'), numeric('subtasks', 'Subtasks'), numeric('tasks', 'Tasks'), numeric('steps', 'Steps'), numeric('tools', 'Tool calls'), numeric('errors', 'Errors'), numeric('avg_time', 'Avg time', 'duration'), numeric('avg_cost', 'Avg cost', 'money')];
        }
        if (['fixes', 'loops', 'commits', 'fix-workspaces', 'fix-categories'].includes(kind)) {
            const o = outcomes(c);
            if (kind === 'fixes') {
                rows = o.fixes;
                columns = [text('title', 'Task', 'link'), text('outcome', 'Outcome', 'badge'), text('signals', 'Signals'), text('follow_up', 'Your prompt after the task'), text('started', 'Started', 'date'), numeric('cost', 'Cost', 'money')];
            }
            else if (kind === 'loops') {
                rows = o.loops;
                columns = [text('title', 'Task', 'link'), text('loop', 'Loop'), text('detail', 'What happened'), numeric('steps', 'Steps'), numeric('cost', 'Cost in loop', 'money')];
            }
            else if (kind === 'commits') {
                rows = o.commits;
                columns = [text('change', 'Change'), text('ref', 'Ref'), text('message', 'Message'), text('title', 'From task', 'link'), numeric('cost', 'Task cost', 'money'), text('at', 'When', 'date')];
            }
            else {
                rows = kind === 'fix-workspaces' ? o.workspaces : o.categories;
                columns = [text('name', kind === 'fix-workspaces' ? 'Workspace' : 'Category'), numeric('tasks', 'Tasks'), numeric('fixed', 'Needed a fix'), numeric('rate', 'Rate', 'percent'), numeric('warnings', 'Warning signs')];
            }
        }
        if (kind === 'outcome-summary') {
            const o = outcomes(c);
            rows = [{ id: 'fix', name: 'Needed a fix', count: o.confirmed, notes: 'Explicit confirmed interventions' }, { id: 'loops', name: 'Got stuck', count: new Set(o.loops.map(l => l.task_id)).size, notes: 'Repeated failed native calls' }, { id: 'commits', name: 'Commits and PRs', count: o.commits.length, notes: 'Retained commands; remote state unverified' }];
            columns = [text('name', 'Outcome'), numeric('count', 'Tasks / records'), text('notes', 'Evidence')];
        }
        if (kind === 'findings') {
            rows = findings(c);
            columns = [text('title', 'Finding'), text('action', 'What to do'), numeric('count', 'Records'), numeric('affected_cost', 'Affected API estimate', 'money'), numeric('savings', 'Estimated savings', 'money')];
        }
        if (kind === 'timeline') {
            rows = turnRows(c);
            columns = commonColumns().filter(col => ['title', 'started', 'duration', 'cost', 'tokens', 'responses'].includes(col.key));
        }
    }
    if (extra.get('top')) {
        if (kind === 'tools')
            columns = columns.filter(c => ['name', 'calls', 'runtime', 'errors'].includes(c.key));
        if (kind === 'categories')
            columns = columns.filter(c => ['name', 'tools', 'time', 'cost'].includes(c.key));
        rows = rows.slice(0, kind === 'findings' ? 3 : Number(extra.get('top')));
    }
    if (extra.get('turn_keys')) {
        const keys = JSON.parse(extra.get('turn_keys')!);
        if (!Array.isArray(keys) || keys.length > 10000 || keys.some(k => typeof k !== 'string'))
            throw Error('Invalid native turn selection');
        const set = new Set(keys);
        rows = rows.filter(r => set.has(r.id));
    }
    if (extra.get('task_ids')) {
        const ids = new Set(extra.get('task_ids')!.split(','));
        rows = rows.filter(r => ids.has(String(r.task_id || r.id)));
    }
    if (extra.get('day') && !['tasks', 'marked', 'steps', 'tools', 'targets'].includes(kind))
        rows = rows.filter(r => String(r.started || r.at || '').slice(0, 10) === extra.get('day'));
    if (extra.get('model'))
        rows = rows.filter(r => String(r.models || r.name || '').includes(extra.get('model')!));
    rows = rows.map(row => ({ ...row, ...Object.fromEntries(columns.filter(c => c.numeric && typeof row[c.key] === 'string' && /^-?\d+(?:\.\d+)?$/.test(String(row[c.key]))).map(c => [c.key, Number(row[c.key])])) }));
    if (!columns.length)
        throw Error('Unknown record collection');
    return { ...collection(rows, query, columns.map(c => c.key)), columns };
}
export function triggerDescription(rule: Record<string, unknown>) { const config = rule.config as Record<string, unknown> || {}; return ({ break: `A prompt arrives after ${config.minutes || 60}+ minutes without activity`, task_budget: `Reported task cost reaches $${config.amount || 5}, then each further increment`, daily_budget: `Reported daily cost (UTC) reaches $${config.amount || 100}`, context: `Session context reaches ${Number(config.tokens || 200000).toLocaleString()} tokens; once per task`, failure_loop: `The same call fails ${config.count || 3} times in a row`, stop_check: 'The agent stops with edits after the last successful check', command: `Tool ${config.tool || 'any'} matches ${config.pattern || rule.name}` })[String(rule.kind)] || String(rule.name); }
