import type { Context } from './repository.ts';
import { metrics, taskFacts, groupEvents } from './repository.ts';
import { price, failureLoops, rolling, hash } from './domain.ts';
import type { NativeEvent, Row } from './types.ts';
export const metricDefinitions = [
    { id: 'cost_per_task', title: 'Cost per task', description: 'API-equivalent cost per assigned task first observed in the period', unit: 'money' },
    { id: 'context', title: 'Average context', description: 'Recorded input tokens sent with each model response', unit: 'tokens' },
    { id: 'large_context', title: 'Calls over 200k context', description: 'Share of model responses with more than 200,000 input tokens', unit: 'percent' },
    { id: 'cache_rebuild', title: 'Cache rebuilds after a break', description: 'Share of priced calls writing cache after an observed 5-minute pause', unit: 'percent' },
    { id: 'top_small', title: 'Top-tier model on small turns', description: 'Cost share of configured top-tier models on short retained turns', unit: 'percent' },
    { id: 'shell', title: 'Shell exploration per task', description: 'Shell file-exploration calls per assigned task first observed in the period', unit: undefined },
    { id: 'failures', title: 'Failed tool calls', description: 'Share of tools with an explicit recorded unsuccessful outcome', unit: 'percent' },
    { id: 'needed_fix', title: 'Needed a fix', description: 'Share of assigned tasks with a confirmed intervention note', unit: 'percent' },
    { id: 'cache_5m', title: 'Cache writes with a 5-minute lifetime', description: 'Share of explicit cache-write tokens with a recorded 5-minute TTL', unit: 'percent' },
    { id: 'break_warnings', title: 'Break warnings per task', description: 'Delivered break warnings with an explicit native task identity', unit: undefined },
    { id: 'context_warnings', title: 'Large context warnings per task', description: 'Delivered large-context warnings with an explicit task identity', unit: undefined },
    { id: 'main_top', title: 'Main agent on top-tier models', description: 'Share of explicitly labeled main-agent responses on configured top-tier models', unit: 'percent' },
    { id: 'sub_top', title: 'Subagents on top-tier models', description: 'Share of explicitly labeled subagent responses on configured top-tier models', unit: 'percent' },
    { id: 'explore_expensive', title: 'Explore agent above the small tier', description: 'Explore responses outside the explicitly configured small-model tier', unit: 'percent' },
    { id: 'large_output', title: 'Shell output over 15k characters', description: 'Share of shell calls with retained output longer than 15,000 characters', unit: 'percent' },
    { id: 'shell_again', title: 'Shell file exploration again', description: 'Share of shell exploration calls whose next shell call explores files too', unit: 'percent' },
    { id: 'loops', title: 'Repeat-failure loops per task', description: 'Runs of at least three identical failed tool calls per assigned task', unit: undefined },
] as const;
export type MetricId = typeof metricDefinitions[number]['id'];
export interface Sample {
    numerator: number;
    denominator: number;
    value: number | null;
    unit: string;
}
const isShell = (e: NativeEvent) => /shell|bash|commandexecution|exec_command/i.test(e.name);
const exploration = (e: NativeEvent) => isShell(e) && /\b(cat|head|tail|sed|find|grep|ls)\b/.test(e.command);
export function measure(id: MetricId, c: Context, events: NativeEvent[], options: {
    top?: string[];
    small?: string[];
    logs?: Row[];
} = {}): Sample {
    const gens = events.filter(e => e.kind === 'generation'), tools = events.filter(e => e.kind === 'tool'), tasks = new Set(events.map(e => c.assignments.get(e.turn_key)).filter((v): v is string => Boolean(v)));
    let numerator = 0, denominator = 0, unit = 'observations';
    if (id === 'cost_per_task') {
        const costs = [...tasks].map(task => metrics(events.filter(e => c.assignments.get(e.turn_key) === task), c.pricing).cost).filter((v): v is number => v != null);
        numerator = costs.reduce((s, v) => s + v, 0);
        denominator = costs.length;
        unit = 'priced tasks';
    }
    if (id === 'context' || id === 'large_context') {
        const known = gens.filter(e => e.input_tokens != null);
        numerator = known.reduce((s, e) => s + (id === 'context' ? Number(e.input_tokens) : Number(Number(e.input_tokens) > 200000)), 0);
        denominator = known.length;
        unit = 'API calls';
    }
    if (id === 'failures') {
        const known = tools.filter(e => e.failed != null);
        numerator = known.filter(e => e.failed === 1).length;
        denominator = known.length;
        unit = 'known tool outcomes';
    }
    if (id === 'shell' || id === 'loops') {
        numerator = id === 'shell' ? tools.filter(exploration).length : [...tasks].reduce((s, id) => s + failureLoops(events.filter(e => c.assignments.get(e.turn_key) === id)).length, 0);
        denominator = tasks.size;
        unit = 'tasks';
    }
    if (id === 'needed_fix') {
        const confirmed = new Set(c.notes.filter(n => n.kind === 'intervention' && n.outcome === 'confirmed').map(n => String(n.task_id)));
        numerator = [...tasks].filter(t => confirmed.has(t)).length;
        denominator = tasks.size;
        unit = 'tasks';
    }
    if (id === 'cache_5m') {
        const known = gens.filter(e => e.cache_write_tokens != null && e.cache_5m_tokens != null);
        numerator = known.reduce((s, e) => s + Number(e.cache_5m_tokens), 0);
        denominator = known.reduce((s, e) => s + Number(e.cache_write_tokens), 0);
        unit = 'cache-write tokens';
    }
    if (id === 'large_output') {
        const known = tools.filter(e => isShell(e) && e.output_chars != null);
        numerator = known.filter(e => Number(e.output_chars) > 15000).length;
        denominator = known.length;
        unit = 'shell outputs';
    }
    if (id === 'shell_again') {
        for (const values of groupEvents(tools.filter(isShell), e => e.session_id).values()) {
            for (let i = 0; i < values.length - 1; i++)
                if (exploration(values[i])) {
                    denominator++;
                    if (exploration(values[i + 1]))
                        numerator++;
                }
        }
        unit = 'exploration pairs';
    }
    if (['main_top', 'sub_top', 'explore_expensive'].includes(id)) {
        const known = gens.filter(e => id === 'main_top' ? e.role === 'main' : id === 'sub_top' ? e.role === 'sub' || Boolean(e.agent_type) : e.agent_type.toLowerCase() === 'explore');
        const configured = id === 'explore_expensive' ? options.small : options.top;
        if (configured?.length) {
            denominator = known.length;
            numerator = known.filter(e => id === 'explore_expensive' ? !configured.includes(e.model) : configured.includes(e.model)).length;
        }
        unit = 'identified agent API calls';
    }
    if (id === 'cache_rebuild') {
        for (const list of groupEvents(gens, e => e.session_id).values())
            for (let i = 1; i < list.length; i++) {
                const e = list[i], cost = price(e, c.pricing);
                if (e.cache_write_tokens == null || cost == null)
                    continue;
                denominator += cost;
                if (Number(e.cache_write_tokens) > 0 && +new Date(e.event_time) - +new Date(list[i - 1].event_time) >= 300000)
                    numerator += cost;
            }
        unit = 'priced API-equivalent units';
    }
    if (id === 'break_warnings' || id === 'context_warnings') {
        const logs = (options.logs || []).filter(l => tasks.has(String(l.task_id)) && (id === 'break_warnings' ? /break/i.test(String(l.rule_name)) : /context/i.test(String(l.rule_name))));
        if (logs.length) {
            numerator = logs.length;
            denominator = tasks.size;
        }
        unit = 'tasks with hook coverage';
    }
    // Short-answer classification needs a retained answer length and configured tier.
    if (id === 'top_small' && options.top?.length) {
        for (const list of groupEvents(events, e => e.turn_key).values()) {
            const turn = c.turns.find(t => t.turn_key === list[0].turn_key), source = turn?.source as Record<string, unknown> | undefined;
            const cost = metrics(list, c.pricing).cost;
            if (cost == null || typeof source?.answer_chars !== 'number')
                continue;
            denominator += cost;
            if (list.filter(e => e.kind === 'tool').length <= 2 && source.answer_chars <= 1200 && list.some(e => options.top!.includes(e.model)))
                numerator += cost;
        }
        unit = 'priced turns with retained answers';
    }
    return { numerator, denominator, value: denominator ? numerator / denominator : null, unit };
}
export function interval(before: Sample[], after: Sample[], seed: string) {
    if (before.length < 8 || after.length < 8)
        return null;
    let state = Number.parseInt(hash(seed).slice(0, 8), 16) || 1;
    const random = () => { state = (Math.imul(state, 1664525) + 1013904223) >>> 0; return state / 4294967296; };
    const sample = (clusters: Sample[]) => {
        let n = 0, d = 0;
        for (let i = 0; i < clusters.length; i++) {
            const item = clusters[Math.floor(random() * clusters.length)];
            n += item.numerator;
            d += item.denominator;
        }
        return d ? n / d : null;
    };
    const values: number[] = [];
    for (let i = 0; i < 400; i++) {
        const a = sample(before), b = sample(after);
        if (a != null && b != null)
            values.push(b - a);
    }
    values.sort((a, b) => a - b);
    if (values.length < 380)
        return null;
    return { low: values[Math.floor(values.length * .025)], high: values[Math.min(values.length - 1, Math.floor(values.length * .975))] };
}
export function compareChange(change: Row, c: Context, options: Parameters<typeof measure>[3] = {}) {
    const at = +new Date(String(change.applied_at));
    const select = (from: number, to: number) => c.events.filter(e => {
        const time = +new Date(e.event_time);
        if (!e.time_known || time < from || time >= to)
            return false;
        if (change.workspace && e.workspace !== change.workspace)
            return false;
        if (change.takes_effect === 'new_sessions' && from >= at) {
            const starts = c.turns.filter(t => t.session_id === e.session_id && t.started_at).map(t => +new Date(t.started_at!));
            if (!starts.length || Math.min(...starts) < at)
                return false;
        }
        return true;
    });
    const before = select(at - 14 * 86400000, at), after = select(at, Math.min(Date.now(), at + 14 * 86400000));
    return ((change.metrics as string[]) || ['cost_per_task']).flatMap(id => {
        const definition = metricDefinitions.find(m => m.id === id);
        if (!definition)
            return [];
        const taskUnit = ['cost_per_task', 'shell', 'loops', 'needed_fix'].includes(definition.id);
        const cohort = (period: NativeEvent[], from: number, to: number) => {
            if (!taskUnit)
                return period;
            const first = new Map<string, number>();
            for (const e of c.events) {
                const task = c.assignments.get(e.turn_key);
                if (task && e.time_known)
                    first.set(task, Math.min(first.get(task) ?? Infinity, +new Date(e.event_time)));
            }
            return period.filter(e => { const time = first.get(c.assignments.get(e.turn_key) || ''); return time != null && time >= from && time < to; });
        };
        const leftEvents = cohort(before, at - 14 * 86400000, at), rightEvents = cohort(after, at, at + 14 * 86400000);
        const a = measure(definition.id, c, leftEvents, options), b = measure(definition.id, c, rightEvents, options);
        const cluster = (events: NativeEvent[]) => {
            const first = new Map<string, string>();
            if (taskUnit)
                for (const e of events) {
                    const task = c.assignments.get(e.turn_key);
                    if (task && !first.has(task))
                        first.set(task, e.event_time.slice(0, 13));
                }
            return [...groupEvents(events, e => taskUnit ? (first.get(c.assignments.get(e.turn_key) || '') || e.event_time.slice(0, 13)) : e.event_time.slice(0, 13)).values()].map(rows => measure(definition.id, c, rows, options)).filter(s => s.denominator > 0);
        };
        const left = cluster(leftEvents), right = cluster(rightEvents), min = definition.id === 'cost_per_task' ? 20 : 100, range = a.denominator >= min && b.denominator >= min ? interval(left, right, String(change.id) + id) : null;
        return [{ id: change.id + ':' + id, metric: definition.title, before: a.value, after: b.value, before_count: a.denominator, after_count: b.denominator, sample_unit: a.unit, before_hours: left.length, after_hours: right.length, low: range?.low ?? null, high: range?.high ?? null, change: !range ? 'Insufficient data' : range.high < 0 ? 'Lower' : range.low > 0 ? 'Higher' : 'Inconclusive', format: definition.unit || 'number', uptake: ['cache_5m', 'break_warnings', 'context_warnings', 'main_top', 'sub_top', 'explore_expensive', 'large_output', 'shell_again', 'loops'].includes(definition.id) }];
    });
}
