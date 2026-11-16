import { friction } from './friction.ts';
import { pg, queryCh } from './database.ts';
import { finite, iso, price, turnKey, hash, failureLoops } from './domain.ts';
import type { NativeEvent, Pricing, Scope, Row, Column } from './types.ts';
export interface Task extends Row {
    project_id: string;
    title: string;
    goal: string;
    acceptance: string;
    status: string;
    outcome: string | null;
    updated_at: string;
    source: Record<string, unknown>;
}
export interface Turn extends Row {
    turn_key: string;
    session_id: string;
    turn_id: string;
    workspace: string;
    prompt: string;
    started_at: string | null;
    finished_at: string | null;
    completed: boolean;
    role: string | null;
    agent_type: string | null;
}
export interface Analysis extends Row {
    task_id: string;
    snapshot_hash: string;
    summary: string;
    task_type: string;
    result: Record<string, unknown>;
    created_at: string;
}
export interface Subtask extends Row {
    analysis_id: string;
    position: number;
    title: string;
    summary: string;
    category: string;
    event_ids: string[];
    confidence: number | null;
    result: Record<string, unknown>;
}
export interface Context {
    tiers?: {
        top: string[];
        small: string[];
    };
    events: NativeEvent[];
    tasks: Task[];
    turns: Turn[];
    assignments: Map<string, string>;
    analyses: Analysis[];
    subtasks: Subtask[];
    pricing: Pricing;
    rules: Row[];
    notes: Row[];
    projects: {
        id: string;
        name: string;
    }[];
    workspaces: string[];
    categories: Map<string, string>;
}
type ContextCache = Map<string, {
    expires: number;
    value: Promise<Context>;
}>;
const globals = globalThis as typeof globalThis & {
    observatoryContextCache?: ContextCache;
};
const cache = globals.observatoryContextCache ??= new Map();
export function invalidate() { cache.clear(); }
export async function metadata() { const db = pg(); const [projects, workspaces] = await Promise.all([db `SELECT id,name FROM projects ORDER BY name`, db `SELECT DISTINCT workspace FROM turns WHERE workspace<>'' ORDER BY workspace`]); return { projects: projects as unknown as Context['projects'], workspaces: workspaces.map(r => String(r.workspace)) }; }
export async function context(scope: Scope): Promise<Context> {
    const key = JSON.stringify(scope), previous = cache.get(key);
    if (previous && previous.expires > Date.now())
        return previous.value;
    const value = load(scope);
    cache.set(key, { expires: Date.now() + 2000, value });
    if (cache.size > 4)
        cache.delete(cache.keys().next().value!);
    try {
        return await value;
    }
    catch (error) {
        cache.delete(key);
        throw error;
    }
}
async function load(scope: Scope): Promise<Context> {
    const db = pg();
    const since = scope.range === 'all' ? null : new Date(Date.now() - Number.parseInt(scope.range) * 86400000).toISOString();
    const [tasks, turns, assigned, analyses, subtasks, rates, rules, notes, meta] = await Promise.all([
        db `SELECT * FROM tasks WHERE (${scope.project}='' OR project_id=${scope.project}) AND (${scope.task || ''}='' OR id=${scope.task || ''}) ORDER BY updated_at DESC LIMIT 10001`,
        db `SELECT t.* FROM turns t LEFT JOIN assignments a USING(turn_key) LEFT JOIN tasks task ON task.id=a.task_id WHERE (${scope.project}='' OR task.project_id=${scope.project}) AND (${scope.task || ''}='' OR a.task_id=${scope.task || ''}) AND (${scope.workspace}='' OR t.workspace=${scope.workspace}) AND (${since}::timestamptz IS NULL OR t.finished_at>=${since}::timestamptz OR t.started_at>=${since}::timestamptz) ORDER BY t.started_at DESC NULLS LAST LIMIT 10001`,
        db `SELECT a.turn_key,a.task_id FROM assignments a JOIN tasks t ON t.id=a.task_id WHERE (${scope.project}='' OR t.project_id=${scope.project})`,
        db `SELECT DISTINCT ON (a.task_id) a.* FROM analyses a JOIN tasks t ON t.id=a.task_id WHERE (${scope.project}='' OR t.project_id=${scope.project}) ORDER BY a.task_id,a.created_at DESC,a.id DESC`,
        db `SELECT s.* FROM subtasks s JOIN (SELECT DISTINCT ON (task_id) id,task_id FROM analyses ORDER BY task_id,created_at DESC,id DESC) a ON a.id=s.analysis_id JOIN tasks t ON t.id=a.task_id WHERE (${scope.project}='' OR t.project_id=${scope.project}) ORDER BY s.analysis_id,s.position`,
        db `SELECT key,value FROM settings WHERE key IN ('pricing','model_tiers')`, db `SELECT * FROM categorization_rules WHERE enabled ORDER BY priority,id`, db `SELECT * FROM evidence_notes ORDER BY created_at`, metadata()
    ]);
    if (turns.length > 10000 || tasks.length > 10000)
        throw Error('Narrow the workspace/date scope to at most 10,000 tasks or turns.');
    const keys = turns.map(t => String(t.turn_key));
    const events = await queryCh<NativeEvent>(`SELECT * EXCEPT(payload,output_excerpt,command,source_path), '' AS payload, '' AS output_excerpt, substring(command,1,512) AS command, '' AS source_path FROM events FINAL WHERE ({workspace:String}='' OR workspace={workspace:String}) AND ({since:String}='' OR event_time>=parseDateTime64BestEffortOrNull({since:String})) AND ({project:String}='' OR turn_key IN {keys:Array(String)}) ORDER BY event_time,id LIMIT 100001`, { workspace: scope.workspace, since: since || '', project: scope.project || scope.task || '', keys });
    if (events.length > 100000)
        throw Error('Narrow the date or workspace scope to at most 100,000 events for this analysis.');
    const visibleKeys = new Set(events.map(e => e.turn_key));
    const visibleTasks = new Set(assigned.filter(a => visibleKeys.has(String(a.turn_key))).map(a => String(a.task_id)));
    const result: Context = { categories: new Map(), events: events.map(e => ({ ...e, event_time: iso(e.event_time.includes('T') ? e.event_time : e.event_time.replace(' ', 'T') + 'Z') || e.event_time, version: Number(e.version), input_tokens: finite(e.input_tokens == null ? null : Number(e.input_tokens)), cached_tokens: finite(e.cached_tokens == null ? null : Number(e.cached_tokens)), output_tokens: finite(e.output_tokens == null ? null : Number(e.output_tokens)), total_tokens: finite(e.total_tokens == null ? null : Number(e.total_tokens)) })), tasks: tasks.filter(t => (scope.range === 'all' && !scope.workspace || visibleTasks.has(String(t.id))) && (!t.source?.native_turn || visibleTasks.has(String(t.id)))) as unknown as Task[], turns: turns as unknown as Turn[], assignments: new Map(assigned.map(a => [String(a.turn_key), String(a.task_id)])), analyses: analyses as unknown as Analysis[], subtasks: subtasks as unknown as Subtask[], tiers: rates.find(r => r.key === 'model_tiers')?.value || { top: [], small: [] }, pricing: (rates.find(r => r.key === 'pricing')?.value || { unit: 'USD', models: {} }) as Pricing, rules: rules as unknown as Row[], notes: notes as unknown as Row[], ...meta };
    for (const task of result.tasks) {
        const facts = taskFacts(result, task.id);
        if (facts.complete)
            for (const group of facts.groups)
                for (const id of group.event_ids)
                    result.categories.set(id, group.category);
    }
    return result;
}
export function metrics(events: NativeEvent[], pricing: Pricing) {
    const generations = events.filter(e => e.kind === 'generation'), tools = events.filter(e => e.kind === 'tool'), costs = generations.map(e => price(e, pricing));
    const sum = (key: 'input_tokens' | 'cached_tokens' | 'output_tokens' | 'total_tokens' | 'cache_write_tokens') => generations.length && generations.every(e => e[key] != null) ? generations.reduce((s, e) => s + Number(e[key]), 0) : null;
    const runtimes = events.filter(e => e.runtime_role !== 'background_service_lifetime').map(e => e.runtime);
    return { responses: generations.length, tools: tools.length, errors: tools.filter(e => e.failed === 1).length, known_outcomes: tools.filter(e => e.failed != null).length, cost: generations.length && costs.every(v => v != null) ? costs.reduce<number>((s, v) => s + (v || 0), 0) : null, known_cost: costs.reduce<number>((s, v) => s + (v || 0), 0), priced: costs.filter(v => v != null).length, input: sum('input_tokens'), cached: sum('cached_tokens'), output: sum('output_tokens'), tokens: sum('total_tokens'), cache_write: sum('cache_write_tokens'), runtime: runtimes.length && runtimes.every(v => v != null) ? runtimes.reduce<number>((s, v) => s + (v || 0), 0) : null, known_runtime: runtimes.reduce<number>((s, v) => s + (v || 0), 0), timed: runtimes.filter(v => v != null).length };
}
export function groupEvents(events: NativeEvent[], key: (event: NativeEvent) => string) {
    const groups = new Map<string, NativeEvent[]>();
    for (const event of events) {
        const id = key(event);
        if (!groups.has(id))
            groups.set(id, []);
        groups.get(id)!.push(event);
    }
    return groups;
}
export function category(event: NativeEvent, c: Context) {
    const interpreted = c.categories.get(event.id);
    if (interpreted)
        return interpreted;
    const rule = c.rules.find(r => event.name.toLowerCase().includes(String(r.pattern).toLowerCase()));
    return String(rule?.category || 'Uncategorized');
}
export function toolName(e: NativeEvent) {
    if (!/^(bash|shell|commandexecution|exec_command)$/i.test(e.name))
        return { family: e.name, action: e.name, name: e.name };
    const compound = /[;&|`\n]|\$\(/.test(e.command), words = e.command.trim().split(/\s+/).filter(Boolean), action = compound ? 'Compound shell' : (words.find(w => !/^\w+=/.test(w) && w !== 'env') || 'Shell').split('/').at(-1)!;
    return { family: 'Shell', action, name: 'Shell · ' + action };
}
const taskIndexes = new WeakMap<Context, {
    events: Map<string, NativeEvent[]>;
    turns: Map<string, Turn[]>;
    facts: Map<string, ReturnType<typeof computeFacts>>;
}>();
function indexTasks(c: Context) {
    let index = taskIndexes.get(c);
    if (index)
        return index;
    const events = new Map<string, NativeEvent[]>(), turns = new Map<string, Turn[]>();
    for (const e of c.events) {
        const id = c.assignments.get(e.turn_key);
        if (id) {
            if (!events.has(id))
                events.set(id, []);
            events.get(id)!.push(e);
        }
    }
    for (const t of c.turns) {
        const id = c.assignments.get(t.turn_key);
        if (id) {
            if (!turns.has(id))
                turns.set(id, []);
            turns.get(id)!.push(t);
        }
    }
    index = { events, turns, facts: new Map() };
    taskIndexes.set(c, index);
    return index;
}
function computeFacts(c: Context, id: string, events: NativeEvent[], turns: Turn[]) {
    const task = c.tasks.find(t => t.id === id), analysis = c.analyses.find(a => a.task_id === id), groups = analysis ? c.subtasks.filter(s => s.analysis_id === analysis.id) : [], notes = c.notes.filter(n => n.task_id === id);
    const times = turns.flatMap(t => [t.started_at, t.finished_at]).filter(Boolean).map(t => +new Date(t!));
    const checkedIds = new Set(groups.flatMap(g => g.event_ids)), versions = analysis?.result.source_versions as Record<string, number> | undefined, complete = events.length > 0 && checkedIds.size === events.length && events.every(e => checkedIds.has(e.id) && (!versions || versions[e.id] === e.version));
    return { task, events, turns, analysis, groups, notes, metrics: metrics(events, c.pricing), duration: times.length ? (Math.max(...times) - Math.min(...times)) / 1000 : null, complete, loops: friction(events) };
}
export function taskFacts(c: Context, id: string) {
    const index = indexTasks(c);
    let facts = index.facts.get(id);
    if (!facts) {
        facts = computeFacts(c, id, index.events.get(id) || [], index.turns.get(id) || []);
        index.facts.set(id, facts);
    }
    return facts;
}
export function turnRows(c: Context): Row[] { const grouped = groupEvents(c.events, e => e.turn_key); return c.turns.map(t => { const events = grouped.get(t.turn_key) || [], m = metrics(events, c.pricing), taskId = c.assignments.get(t.turn_key), a = c.analyses.find(a => a.task_id === taskId), groupIds = new Set(c.subtasks.filter(s => s.analysis_id === a?.id).flatMap(s => s.event_ids)); return { id: t.turn_key, event_ids: events.map(e => e.id), title: t.prompt || 'No retained prompt', task_id: taskId || null, href: taskId ? '/tasks/' + taskId : null, started: t.started_at, workspace: t.workspace, session_id: t.session_id, turn_id: t.turn_id, cost: m.cost, tokens: m.tokens, duration: t.started_at && t.finished_at ? (+new Date(t.finished_at) - +new Date(t.started_at)) / 1000 : null, responses: m.responses, tools: m.tools, errors: m.errors, loops: friction(events).length, models: [...new Set(events.map(e => e.model).filter(Boolean))].join(', '), agent: t.agent_type || t.role || 'Unknown', categories: [...new Set(c.subtasks.filter(s => s.analysis_id === a?.id).map(s => s.category))].join(', '), interpretation: taskId && taskFacts(c, taskId).complete ? 'Explained' : 'Unclassified' }; }); }
export function taskRows(c: Context): Row[] { return c.tasks.map(task => { const f = taskFacts(c, task.id); return { ...task, href: '/tasks/' + task.id, started: f.turns.map(t => t.started_at).filter(Boolean).sort()[0] || null, duration: f.duration, turns: f.turns.length, cost: f.metrics.cost, tokens: f.metrics.tokens, responses: f.metrics.responses, tools: f.metrics.tools, errors: f.metrics.errors, loops: f.loops.length, categories: [...new Set(f.groups.map(s => s.category))].join(', '), interpretation: f.complete ? 'Explained' : 'Unclassified', outcome: task.outcome || 'Unknown' }; }); }
export async function taskScope(id: string): Promise<Scope> {
    const rows = await pg() `SELECT t.project_id FROM tasks t WHERE t.id=${id}`;
    if (!rows.length)
        throw Error('Unknown task');
    return { project: String(rows[0].project_id || ''), workspace: '', range: 'all', timezone: 'UTC', task: id };
}
export async function sourceEvent(id: string) {
    const rows = await queryCh<NativeEvent>('SELECT * FROM events FINAL WHERE id={id:String} LIMIT 1', { id });
    if (!rows.length)
        throw Error('Source event unavailable');
    return rows[0];
}
export function commonColumns(): Column[] { return [{ key: 'title', label: 'Task', type: 'link' }, { key: 'started', label: 'Started', type: 'date' }, { key: 'cost', label: 'Cost', type: 'money', numeric: true }, { key: 'tokens', label: 'Tokens', type: 'tokens', numeric: true }, { key: 'duration', label: 'Duration', type: 'duration', numeric: true }, { key: 'responses', label: 'API calls', numeric: true }, { key: 'tools', label: 'Tools', numeric: true }, { key: 'errors', label: 'Errors', numeric: true }, { key: 'outcome', label: 'Outcome', type: 'badge' }, { key: 'loops', label: 'Loops', numeric: true }, { key: 'models', label: 'Models' }, { key: 'workspace', label: 'Workspace', hidden: true }, { key: 'session_id', label: 'Session', hidden: true }, { key: 'interpretation', label: 'Explanation', hidden: true }]; }
