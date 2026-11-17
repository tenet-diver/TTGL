import { turnSegments } from './timeline.ts';
import { colorFor, type ColorKind } from './semantic-colors.ts';
import { pg } from './database.ts';
import { context, metadata, metrics, taskFacts, taskRows, turnRows, groupEvents, toolName, type Context } from './repository.ts';
import { tools, models, process as processMap, outcomes, findings, daily } from './analytics.ts';
import { metricDefinitions, measure, compareChange } from './impact.ts';
import { rolling } from './domain.ts';
import { palette, type Row, type Scope, type PageData, type Panel, type Metric, type ChartSpec } from './types.ts';
export const routes: Record<string, {
    title: string;
    description: string;
    section: string;
}> = {
    overview: { title: 'Overall activity', description: 'Where coding agents spend time and tokens, and how the work turned out.', section: 'Analysis' },
    tasks: { title: 'Task activity', description: 'One row per native turn: a prompt and the work recorded for it, subagents included.', section: 'Analysis' },
    grouping: { title: 'Task grouping', description: 'Explicit tasks, assigned native turns, and source-linked interpretations.', section: 'Analysis' },
    tools: { title: 'Tool usage', description: 'Native tools, actions, targets and recorded operation time. Unknown per-tool model costs stay unknown.', section: 'Analysis' },
    costs: { title: 'Cost & tokens', description: 'API list-price scenarios calculated from recorded counters; subscription cash charges remain unknown.', section: 'Analysis' },
    timeline: { title: 'Activity timeline', description: 'Each block is a native turn placed at its local time of day. Turn spans include idle gaps.', section: 'Analysis' },
    agents: { title: 'Agents', description: 'The main session and explicitly identified subagent types. Runs count distinct native sessions.', section: 'Analysis' },
    process: { title: 'Process map', description: 'How tasks move between interpreted subtask categories. Each explained task is one case.', section: 'Analysis' },
    entities: { title: 'Entities', description: 'Recorded command targets and their native source evidence.', section: 'Analysis' },
    outcomes: { title: 'Outcomes', description: 'Recorded fixes, repeated failures and changes. A missing signal does not establish success.', section: 'Analysis' },
    suggestions: { title: 'Suggestions', description: 'Ways to spend fewer tokens and less time, from source-linked checks and explicit analysis.', section: 'Optimize' },
    impact: { title: 'Impact', description: 'Record what you applied and when. Compare the 14 days before with up to 14 days after; lower is better.', section: 'Optimize' },
    experiences: { title: 'Experiences', description: 'Source-linked procedures, interpreted outcomes and immutable memory snapshots. Interpretations and verified reuse stay separate.', section: 'Optimize' },
    delegation: { title: 'Delegation', description: 'Plans, retrieval, executor choices and public verification. Inspect a receipt to trace its checkpoint and source evidence.', section: 'Optimize' },
    'experience-results': { title: 'Experience results', description: 'Registered experience studies and separately recorded independent evaluations. Fixture checks are not model-quality results.', section: 'Optimize' },
    experiments: { title: 'Experiments', description: 'Retained proposals, registered evaluations, analyst verdicts and research overhead. Inspect a row for its original evidence.', section: 'Optimize' },
    live: { title: 'Live sessions', description: 'Sessions reported to the hooks in the last 24 hours. Send a note or pause a session.', section: 'Steer' },
    rules: { title: 'Steering rules', description: 'Hooks check these rules at tool calls, prompts and stops. Built-ins begin in Warn; change the mode when ready.', section: 'Steer' },
    categorization: { title: 'Categorization', description: 'Ordered literal rules and explicit model interpretations. Native measurements remain unchanged.', section: 'Configure' },
    data: { title: 'Data list', description: 'Registered native source files and retained ingestion errors.', section: 'Configure' },
    jobs: { title: 'Mining jobs', description: 'Source collection and explicit analysis attempts, including failures, unknown usage and legacy records.', section: 'Configure' },
    pricing: { title: 'Pricing', description: 'Editable API-equivalent rates per million tokens. Saving rates recalculates estimates without rewriting native counters.', section: 'Configure' },
    knowledge: { title: 'Knowledge', description: 'Source-linked candidate lessons from interpreted tasks. Candidates remain unverified.', section: 'Analysis' },
};
const list = (id: string, title: string, description?: string): Panel => ({ id, title, list: id, description });
const chart = (id: string, title: string, kind: ChartSpec['kind'], points: Record<string, unknown>[], series: ChartSpec['series'], description?: string): Panel => ({ id, title, chart: { id, title, kind, points, series, description, colorKind: id === 'flow' || id.startsWith('category-') ? 'activity' : ['tool-treemap', 'daily-tools'].includes(id) ? 'tool' : ['overview-cost', 'daily-cost', 'model-cost', 'model-tokens'].includes(id) ? 'model' : id === 'activity' ? 'event' : 'series' } });
const series = (keys: string[], kind: ColorKind = 'series') => keys.map(key => ({ key, name: key, color: colorFor(key, kind) }));
const metric = (label: string, value: Metric['value'], format?: Metric['format'], note?: string, href?: string): Metric => ({ label, value, format, note, href });
const sumKnown = (rows: Row[], key: string) => rows.reduce((s, r) => s + (typeof r[key] === 'number' ? r[key] : 0), 0);
export async function pageData(view: string, scope: Scope, params: URLSearchParams): Promise<PageData> {
    const info = routes[view];
    if (!info)
        throw Error('Unknown page');
    const meta = await metadata();
    const result: PageData = { ...info, ...meta, metrics: [], panels: [], actions: [] };
    if (['experiences', 'delegation', 'experience-results'].includes(view)) {
        result.panels = view === 'experiences' ? [list('experience-versions', 'Procedures and examples'), list('experience-predictions', 'Public outcome interpretations', 'Confidence is an interpretation until calibrated.'), list('experience-snapshots', 'Memory snapshots'), list('experience-jobs', 'Extraction attempts')] : view === 'delegation' ? [list('experience-plans', 'Plan revisions'), list('experience-retrievals', 'Retrieval receipts'), list('experience-routes', 'Routing decisions'), list('experience-attempts', 'Attempt transitions'), list('experience-verifications', 'Public verification')] : [list('experience-studies', 'Registered studies'), list('experience-results', 'Independent evaluation summaries', 'Hidden tests, reference patches and evaluator internals are not exposed here or through the runtime service.')];
        return result;
    }
    if (['experiments', 'rules', 'categorization', 'data', 'jobs', 'knowledge', 'pricing', 'live'].includes(view)) {
        if (view === 'experiments')
            result.panels = [list('experiments', 'Proposals', 'Evaluation, decision and implementation are separate. Unrecorded states remain unrecorded.'), list('experiment-evaluations', 'Measured evaluations', 'Inspect each row for its retained protocol, measurements and artifact hash. Failed trials remain visible.'), list('experiment-reviews', 'Analyst reviews', 'Keep, reject and inconclusive are interpretations of a specific evaluation, not new measurements.'), list('experiment-accounting', 'Research overhead snapshots', 'Snapshots can overlap. Do not add snapshots together or treat gross token reductions as net cash savings.')];
        if (view === 'rules') {
            result.panels = [list('rules', 'Steering rules')];
            result.actions = ['rule'];
        }
        if (view === 'categorization') {
            result.panels = [list('categorization', 'Categorization rules')];
            result.actions = ['categorization'];
        }
        if (view === 'data') {
            result.panels = [list('sources', 'Source files'), list('archives', 'Raw log archives', 'Exact original bytes retained in the configured local S3 bucket; pending archives are not offered as verified downloads.')];
            result.actions = ['source-root', 'project'];
        }
        if (view === 'knowledge')
            result.panels = [list('knowledge', 'Candidate knowledge')];
        if (view === 'pricing')
            result.panels = [{ id: 'pricing', title: 'Model rates and tier configuration' }];
        if (view === 'jobs') {
            result.panels = [list('jobs', 'Analysis attempts'), list('sources', 'Source collection')];
            result.actions = ['analysis-batch'];
            const jobs = await pg() `SELECT status,count(*)::integer AS n FROM analysis_jobs GROUP BY status`;
            result.metrics = ['queued', 'running', 'completed', 'failed'].map(status => metric(status, jobs.find(j => j.status === status)?.n || 0));
        }
        if (view === 'live') {
            const db = pg();
            const [sessions, logs] = await Promise.all([db `SELECT * FROM live_sessions WHERE last_seen>now()-interval '24 hours' AND (${scope.workspace}='' OR workspace=${scope.workspace})`, db `SELECT mode,count(*)::integer AS n FROM steering_log WHERE at>now()-interval '24 hours' AND (${scope.workspace}='' OR workspace=${scope.workspace}) GROUP BY mode`]);
            result.metrics = [metric('Working', sessions.filter(s => s.status === 'working' && +new Date(s.last_seen) > Date.now() - 600000).length, undefined, 'Active in the last 10 min'), metric('Waiting for you', sessions.filter(s => s.status === 'waiting').length, undefined, 'Finished a turn'), metric('Rules fired (24 h)', logs.reduce((s, l) => s + Number(l.n), 0)), metric('Blocked or asked (24 h)', logs.filter(l => ['block', 'ask'].includes(l.mode)).reduce((s, l) => s + Number(l.n), 0))];
            result.panels = [list('live', 'Live sessions', sessions.length ? undefined : 'No session reported in the last 24 hours. Start a connected agent and it will appear here.'), list('rule-log', 'Rule log', 'Every recorded rule firing and delivered note, newest first. Log-only rules appear here.')];
        }
        return result;
    }
    const c = await context(scope), m = metrics(c.events, c.pricing), p = processMap(c), o = outcomes(c), f = findings(c), turns = turnRows(c), tasks = taskRows(c), cost = daily(c), toolRows = tools(c), modelRows = models(c);
    const knownCosts = turns.map(t => t.cost).filter((v): v is number => typeof v === 'number').sort((a, b) => a - b), spans = turns.map(t => t.duration).filter((v): v is number => typeof v === 'number').sort((a, b) => a - b);
    const mean = (values: number[]) => values.length ? values.reduce((s, v) => s + v, 0) / values.length : null;
    const quantile = (values: number[], q: number) => {
        if (!values.length)
            return null;
        const x = (values.length - 1) * q, lo = Math.floor(x), hi = Math.ceil(x);
        return values[lo] + (values[hi] - values[lo]) * (x - lo);
    };
    result.coverage = { complete: p.explained, total: c.tasks.length, pending: 0, unclassified: Math.max(0, c.tasks.length - p.explained) };
    if (view === 'overview') {
        result.actions = ['project'];
        result.metrics = [metric('Cost', m.cost, 'money', `${m.priced}/${m.responses} responses priced`, '/costs'), metric('Tasks', turns.length, undefined, `${c.tasks.length} explicitly assigned tasks`, '/tasks'), metric('Recorded time', m.runtime, 'duration', m.runtime == null ? 'Some runtimes are unrecorded; overlaps remain' : 'Runtime sum, including overlaps', '/timeline'), metric('Tool calls', m.tools, undefined, `${m.errors} known unsuccessful calls`, '/tools'), metric('Cache hit rate', m.input != null && m.cached != null && m.input ? m.cached / m.input : null, 'percent', 'Cache reads are an input subset', '/costs'), metric('Needed a fix', c.tasks.length ? o.confirmed / c.tasks.length : null, 'percent', `${o.confirmed} confirmed task interventions`, '/outcomes')];
        result.panels = [chart('overview-cost', 'Cost per day', 'bar', cost.points, series(cost.keys, 'model'), 'Click a day to see its tasks'), chart('activity', 'Time by activity', 'horizontal', [...groupEvents(c.events, e => e.kind === 'generation' ? 'Model' : e.runtime_role || 'Unreviewed')].map(([name, events]) => ({ name, value: metrics(events, c.pricing).timed ? metrics(events, c.pricing).known_runtime : null, event_ids: events.map(e => e.id) })), [{ key: 'value', name: 'Recorded seconds', color: palette[0] }], 'Model and tool runtime sums; service lifetimes remain separate'), list('tools', 'Top tools'), list('categories', 'Top categories'), list('outcome-summary', 'Outcomes'), list('findings', 'Top suggestions')];
    }
    if (view === 'tasks' || view === 'grouping') {
        result.metrics = [metric('Tasks (turns)', turns.length), metric('Avg cost per task', mean(knownCosts), 'money', 'Known estimates only'), metric('90th pct cost', quantile(knownCosts, .9), 'money'), metric('Avg duration', mean(spans), 'duration'), metric('90th pct duration', quantile(spans, .9), 'duration'), metric('Avg tool calls', turns.length ? m.tools / turns.length : null)];
        result.panels = [{ id: 'coverage', title: 'Explained tasks' }, list('marked', 'All marked tasks', 'Explicit task boundaries and assignments are preserved.'), list('tasks', 'Tasks', 'Native turns and marked tasks are separate counting units.')];
        result.actions = ['analysis-batch', ...(view === 'grouping' ? ['task', 'assign'] : [])];
    }
    if (view === 'tools') {
        const family = params.get('family'), filtered = family ? toolRows.filter(t => t.family === family) : toolRows;
        const measure = params.get('measure') || 'calls';
        if (family)
            result.title = family;
        const calls = daily(c, 'calls', 'tool');
        result.panels = [chart('tool-treemap', family ? 'Actions' : 'Tools', 'treemap', filtered.map(r => ({ ...r, value: r[measure], name: r.name })), [{ key: 'value', name: measure, color: palette[0] }], 'Area follows the selected measure; click to drill in'), family ? list('targets', 'Targets') : chart('daily-tools', 'Tool calls per day', 'bar', calls.points, series(calls.keys, 'tool'), 'Top tool identities; inspect the complete table below'), list('tools', family ? family + ' actions' : 'All tools', 'Call and context costs stay unknown unless an explicit supported allocation is selected.')];
    }
    if (view === 'costs') {
        result.description = `Estimated API-equivalent cost at ${c.pricing.service_tier || 'configured'} rates${c.pricing.as_of ? ' dated ' + c.pricing.as_of : ''}; actual subscription cash and unrecorded cache-write surcharges remain unknown.`;
        result.metrics = [metric('Estimated API cost', m.cost, 'money', `${m.priced}/${m.responses} model calls priced`), metric('Cache hit rate', m.input && m.cached != null ? m.cached / m.input : null, 'percent', 'Observed cached input / input'), metric('Cache read tokens', m.cached, 'tokens'), metric('Cache write tokens', m.cache_write, 'tokens', 'Explicit source counters only'), metric('Output tokens', m.output, 'tokens'), metric('Avg context per call', m.input != null && m.responses ? m.input / m.responses : null, 'tokens')];
        const labels = ['< $0.05', '$0.05–0.25', '$0.25–1', '$1–5', '$5–20', '$20+', 'Unmetered', 'Unpriced'];
        const bounds = [.05, .25, 1, 5, 20, Infinity];
        const bands = labels.map((name, i) => { const matches = turns.filter(t => t.cost == null ? i === (Number(t.responses) > 0 ? 7 : 6) : bounds.findIndex(max => Number(t.cost) < max) === i); return { name, count: matches.length, cost: matches.some(t => t.cost == null) ? null : matches.reduce((s, t) => s + Number(t.cost), 0), turn_keys: matches.map(t => t.id) }; });
        const tokenTypes = daily(c, 'tokens', 'type'), modelTokens = daily(c, 'tokens');
        result.panels = [chart('daily-cost', 'Cost by day', 'bar', cost.points, series(cost.keys, 'model'), 'Observed input/cache/output at dated API rates, including configured long-context premiums. Unreported writes use the ordinary input rate; their separate surcharges are excluded.'), chart('model-cost', 'Cost by model', 'horizontal', modelRows.map(r => ({ name: r.name, value: r.cost, event_ids: c.events.filter(e => e.kind === 'generation' && e.model === r.name).map(e => e.id) })), [{ key: 'value', name: 'Cost', color: palette[0] }]), chart('count-bands', 'Tasks by estimated cost', 'bar', bands.map(r => ({ ...r, date: r.name })), [{ key: 'count', name: 'Tasks', color: palette[0] }]), chart('spend-bands', 'Spend by cost band', 'bar', bands.map(r => ({ ...r, date: r.name })), [{ key: 'cost', name: 'Spend', color: palette[3] }]), chart('token-types', 'Tokens by type', 'bar', tokenTypes.points, series(tokenTypes.keys), 'Input partitions into cache read, recorded cache write and other input. Unreported cache writes remain in other input; no missing counter is treated as measured zero.'), chart('model-tokens', 'Tokens by model', 'bar', modelTokens.points, series(modelTokens.keys, 'model')), list('models', 'Models')];
    }
    if (view === 'agents')
        result.panels = [list('agents', 'Agent comparison', 'Unknown identities remain separate; run counts are explicit native sessions.')];
    if (view === 'process') {
        result.metrics = [metric('Subtasks', p.categories.reduce((s, r) => s + Number(r.subtasks), 0)), metric('Paths', p.paths.length), metric('Tasks with rework', p.explained ? p.reworked / p.explained : null, 'percent'), metric('Cost of rework', null, 'money', 'No causal/per-step cost allocation is recorded')];
        result.panels = [{ id: 'coverage', title: 'Explained tasks' }, chart('flow', 'How tasks flow', 'flow', [...p.categories.map(r => ({ ...r, kind: 'node' })), ...p.transitions.map(r => ({ ...r, kind: 'edge' }))], series(p.categories.map(r => r.name)), 'Click a category or connection to list related tasks'), list('transitions', 'Transitions'), chart('category-cost', 'Cost by subtask category', 'horizontal', p.categories.map(r => ({ name: r.name, value: r.cost, task_ids: r.task_ids })), [{ key: 'value', name: 'Cost', color: palette[0] }]), chart('category-time', 'Time by subtask category', 'horizontal', p.categories.map(r => ({ name: r.name, value: r.time, task_ids: r.task_ids })), [{ key: 'value', name: 'Elapsed seconds', color: palette[1] }]), list('categories', 'Subtask categories'), list('paths', 'Paths')];
        result.actions = ['analysis-batch'];
    }
    if (view === 'timeline') {
        const heat: Array<Record<string, unknown>> = [];
        const formatter = new Intl.DateTimeFormat('en-GB', { timeZone: scope.timezone, weekday: 'short', hour: '2-digit', hourCycle: 'h23' });
        for (const e of c.events.filter(e => e.kind === 'generation' && e.time_known)) {
            const parts = formatter.formatToParts(new Date(e.event_time)), weekday = parts.find(p => p.type === 'weekday')?.value, hour = Number(parts.find(p => p.type === 'hour')?.value);
            let row = heat.find(r => r.day === weekday && r.hour === hour);
            if (!row) {
                row = { day: weekday, hour, value: 0, count: 0, known: 0, event_ids: [] };
                heat.push(row);
            }
            const value = metrics([e], c.pricing).cost;
            row.count = Number(row.count) + 1;
            if (value != null) {
                row.value = Number(row.value) + value;
                row.known = Number(row.known) + 1;
            }
            (row.event_ids as string[]).push(e.id);
        }
        result.panels = [chart('heatmap', 'When you use coding agents', 'heatmap', heat, [{ key: 'value', name: 'API-equivalent cost', color: palette[0] }], `Cost by weekday and hour (${scope.timezone}); unknown measurements remain unknown`), chart('turns', 'Turns by day', 'turns', turns.flatMap(t => t.started ? turnSegments(String(t.started), t.duration == null ? null : new Date(+new Date(String(t.started)) + Number(t.duration) * 1000).toISOString(), scope.timezone).map(s => ({ ...t, display_date: s.date, start_hour: s.hour, span_hours: s.hours })) : []), [{ key: 'duration', name: 'Observed span', color: palette[0] }], 'Turns can include idle gaps and overlap. Click a block to open its task.'), list('timeline', 'Turn records')];
    }
    if (view === 'entities')
        result.panels = [list('targets', 'Recorded targets')];
    if (view === 'outcomes') {
        result.metrics = [metric('Assigned tasks', tasks.length), metric('Needed a fix', tasks.length ? o.confirmed / tasks.length : null, 'percent', `${o.confirmed} confirmed records`), metric('Got stuck', new Set(o.loops.map(l => l.task_id)).size), metric('Commits and PRs', o.commits.length, undefined, 'Retained commands; remote state unverified')];
        result.panels = [list('fix-workspaces', 'Fix rate by workspace'), list('fix-categories', 'Fix rate by subtask category'), list('fixes', 'Tasks you had to fix', 'Confirmed interventions and warning signals are separate. A leading no/wait/that’s wrong/still broken/revert can indicate a correction; read the following prompt before acting.'), list('loops', 'Where it got stuck', 'Identical failed calls, at least three times in a row. Step links retain the native source IDs.'), list('commits', 'Commits and pull requests')];
    }
    if (view === 'suggestions') {
        result.metrics = [metric('Spend in range', m.cost, 'money'), metric('Findings', f.length), metric('Estimated savings', null, 'money', 'Requires a quality-preserving comparison'), metric('Agent runs', c.analyses.length, undefined, 'Recorded, not started by browsing')];
        result.panels = [list('findings', 'Built-in findings'), list('jobs', 'Agent runs')];
        result.actions = ['analysis-batch'];
    }
    if (view === 'impact') {
        const db = pg();
        const [changes, tiers, logs] = await Promise.all([db `SELECT * FROM applied_changes WHERE (${scope.workspace}='' OR workspace=${scope.workspace}) ORDER BY applied_at DESC`, db `SELECT value FROM settings WHERE key='model_tiers'`, db `SELECT * FROM steering_log ORDER BY at`]);
        const options = { ...(tiers[0]?.value || {}), logs: logs as unknown as Row[] };
        result.panels = [list('changes', 'Changes you applied', 'Fixed 14-day before/after windows; confidence intervals require sufficient samples and hourly clusters.')];
        result.actions = ['change'];
        for (const definition of metricDefinitions) {
            const points = [...groupEvents(c.events.filter(e => e.time_known), e => e.event_time.slice(0, 10))].map(([date, events]) => ({ date, ...measure(definition.id, c, events, options) })).sort((a, b) => a.date.localeCompare(b.date));
            const values = rolling(points);
            const p = chart(definition.id, definition.title, 'line', values, [{ key: 'value', name: 'Per day', color: colorFor('value', 'series') }, { key: 'average', name: '7-day average', color: palette[0] }], definition.description);
            p.chart!.last = values.at(-1)?.average ?? null;
            p.chart!.markers = changes.map((r, i) => ({ at: String(r.applied_at), number: changes.length - i, title: String(r.title) }));
            result.panels.push(p);
        }
    }
    return result;
}
export async function changeRows(scope: Scope) { const db = pg(), [rows, c, tiers, logs] = await Promise.all([db `SELECT * FROM applied_changes WHERE (${scope.workspace}='' OR workspace=${scope.workspace}) ORDER BY applied_at DESC`, context({ ...scope, range: 'all' }), db `SELECT value FROM settings WHERE key='model_tiers'`, db `SELECT * FROM steering_log ORDER BY at`]); return rows.map((row, i) => ({ ...row, id: String(row.id), number: rows.length - i, comparison: compareChange(row as Row, c, { ...(tiers[0]?.value || {}), logs: logs as unknown as Row[] }) })); }
