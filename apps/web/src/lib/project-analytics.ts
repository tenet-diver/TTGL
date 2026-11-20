import { hash, iso } from './domain.ts';
import { category, groupEvents, metrics, toolName, type Context, type Turn } from './repository.ts';
import type { NativeEvent, Row } from './types.ts';

const dayFormats = new Map<string, Intl.DateTimeFormat>();
export function localDay(stamp: unknown, timezone: string) {
    const time = iso(stamp);
    if (!time) return null;
    let formatter = dayFormats.get(timezone);
    if (!formatter) {
        if (dayFormats.size >= 32) dayFormats.delete(dayFormats.keys().next().value!);
        formatter = new Intl.DateTimeFormat('en-CA', { timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit' });
        dayFormats.set(timezone, formatter);
    }
    const parts = formatter.formatToParts(new Date(time));
    return ['year', 'month', 'day'].map(part => parts.find(value => value.type === part)?.value).join('-');
}

export function dailyRows(rows: Row[], stamp: string, field: string, timezone: string, group?: string) {
    const buckets = new Map<string, Map<string, { total: number; missing: boolean }>>();
    const names = new Set<string>();
    for (const row of rows) {
        const date = localDay(row[stamp], timezone);
        if (!date) continue;
        const name = group ? String(row[group] || 'Unknown') : 'value';
        names.add(name);
        if (!buckets.has(date)) buckets.set(date, new Map());
        const day = buckets.get(date)!;
        const value = day.get(name) || { total: 0, missing: false };
        const amount = field === 'count' ? 1 : row[field];
        if (typeof amount === 'number' && Number.isFinite(amount)) value.total += amount;
        else value.missing = true;
        day.set(name, value);
    }
    const dates = [...buckets.keys()].sort(), keys = [...names];
    if (!dates.length) return { points: [], keys };
    // Preserve calendar gaps so the graph does not imply equally spaced activity.
    const first = Date.parse(dates[0]), last = Date.parse(dates.at(-1)!);
    const days = Math.round((last - first) / 86_400_000) + 1;
    const timeline = days <= 400 ? Array.from({ length: days }, (_, i) => new Date(first + i * 86_400_000).toISOString().slice(0, 10)) : dates;
    return { keys, points: timeline.map(date => ({ date, ...Object.fromEntries(keys.map(name => {
        const value = buckets.get(date)?.get(name);
        return [name, value?.missing ? null : value?.total ?? 0];
    })) })) };
}

export function sessionRows(c: Context) {
    const sessions = new Map<string, Turn[]>();
    const events = groupEvents(c.events, event => event.session_id);
    const tasks = new Map(c.tasks.map(task => [task.id, task]));
    const projects = new Map(c.projects.map(project => [project.id, project.name]));
    for (const turn of c.turns) {
        if (!sessions.has(turn.session_id)) sessions.set(turn.session_id, []);
        sessions.get(turn.session_id)!.push(turn);
    }
    return [...sessions].map(([id, turns]): Row => {
        const native = events.get(id) || [], m = metrics(native, c.pricing);
        const ordered = [...turns].sort((a, b) => (iso(a.started_at) || '').localeCompare(iso(b.started_at) || ''));
        const started = iso(ordered.find(turn => turn.started_at)?.started_at);
        const linked = [...new Set(turns.map(turn => c.assignments.get(turn.turn_key)).filter(Boolean))].map(task => tasks.get(task!)).filter(Boolean);
        const project = [...new Set(linked.map(task => projects.get(task!.project_id)).filter(Boolean))].join(', ');
        const workspace = [...new Set(turns.map(turn => turn.workspace).filter(Boolean))].map(path => path.split('/').filter(Boolean).at(-1) || path).join(', ');
        return { id, title: ordered.find(turn => turn.prompt)?.prompt.split('\n')[0].slice(0, 190) || id,
            href: '/sessions?session=' + encodeURIComponent(id), started, harness: ordered.find(turn => turn.harness !== 'Unknown')?.harness || 'Unknown',
            workspace, project: project || null, work: linked.map(task => task!.title).join(', ') || null,
            turns: turns.length, prompts: turns.filter(turn => turn.prompt).length, tools: m.tools, errors: m.errors,
            cost: m.cost, tokens: m.tokens, runtime: m.timed ? m.known_runtime : null,
            commits: native.filter(event => event.kind === 'tool' && event.failed === 0 && /\bgit\s+commit\b/.test(event.command)).length };
    }).sort((a, b) => String(b.started || '').localeCompare(String(a.started || '')));
}

export function eventRows(events: NativeEvent[], c: Context): Row[] {
    return [...events].reverse().map(event => ({
        id: event.id, event_id: event.id, at: event.time_known ? event.event_time : null, kind: event.kind,
        name: event.kind === 'generation' ? event.model || 'Model response' : toolName(event).name,
        category: category(event, c), workspace: event.workspace, session_id: event.session_id, turn_key: event.turn_key,
        status: event.failed === 1 ? 'Failed' : event.failed === 0 ? 'Completed' : 'Unknown',
        runtime: event.runtime_role === 'background_service_lifetime' ? null : event.runtime,
        tokens: event.total_tokens, cost: metrics([event], c.pricing).cost,
        detail: event.command || null, source_line: event.source_line,
    }));
}

export function signatureRows(events: NativeEvent[]) {
    return [...groupEvents(events, event => event.signature || event.name)].map(([signature, matches]): Row => ({
        id: hash(signature), event_id: matches.at(-1)!.id, name: toolName(matches[0]).name,
        signature, calls: matches.length, sessions: new Set(matches.map(event => event.session_id)).size,
        last_seen: matches.at(-1)!.time_known ? matches.at(-1)!.event_time : null, detail: matches.at(-1)!.command || null,
    })).sort((a, b) => Number(b.calls) - Number(a.calls));
}

export function mcpRows(events: NativeEvent[], c: Context) {
    return [...groupEvents(events.filter(event => event.kind === 'tool' && /^(mcp__|mcp[.:/_-]|McpToolCall$)/i.test(event.name)), event => event.name)].map(([name, matches]): Row => {
        const m = metrics(matches, c.pricing);
        return { id: hash(name), name, event_id: matches.at(-1)!.id, calls: matches.length,
            errors: m.errors, failure_rate: m.known_outcomes ? m.errors / m.known_outcomes : null,
            runtime: m.runtime, sessions: new Set(matches.map(event => event.session_id)).size };
    }).sort((a, b) => Number(b.calls) - Number(a.calls));
}

export function pullRequestOperation(event: NativeEvent) {
    return event.kind === 'tool' ? /\bgh\s+pr\s+([a-z-]+)\b/i.exec(event.command)?.[1]?.toLowerCase() || null : null;
}

export function deliveryTransitions(events: NativeEvent[]) {
    const bySession = groupEvents(events.filter(event => event.time_known && pullRequestOperation(event) !== null), event => event.session_id);
    const counts = new Map<string, { id: string; from: string; to: string; calls: number; sessionIds: Set<string>; event_id: string }>();
    for (const [session, records] of bySession) {
        let previous: string | null = null;
        for (const event of [...records].sort((a, b) => a.event_time.localeCompare(b.event_time))) {
            const operation = pullRequestOperation(event)!;
            if (previous) {
                const key = JSON.stringify([previous, operation]);
                if (!counts.has(key)) counts.set(key, { id: hash(key), from: previous, to: operation, calls: 0, sessionIds: new Set(), event_id: event.id });
                const row = counts.get(key)!;
                row.calls++;
                row.sessionIds.add(session);
            }
            previous = operation;
        }
    }
    return [...counts.values()].map(({ sessionIds, ...row }) => ({ ...row, sessions: sessionIds.size }))
        .sort((a, b) => b.calls - a.calls);
}
