import { createHash } from 'node:crypto';
import type { NativeEvent, Pricing, Scope, Query, Row } from './types.ts';
export const turnKey = (session: string, turn: string) => JSON.stringify([session, turn]);
export const hash = (value: unknown) => createHash('sha256').update(typeof value === 'string' || value instanceof Uint8Array ? value : JSON.stringify(value)).digest('hex');
export function finite(value: unknown): number | null { return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null; }
export function iso(value: unknown): string | null {
    if (value instanceof Date)
        return Number.isNaN(+value) ? null : value.toISOString();
    const stamp = typeof value === 'number' ? value * 1000 : typeof value === 'string' ? value : null;
    if (stamp == null)
        return null;
    const date = new Date(stamp);
    return Number.isNaN(+date) ? null : date.toISOString();
}
export function price(event: Pick<NativeEvent, 'kind' | 'model' | 'input_tokens' | 'cached_tokens' | 'output_tokens'> & Partial<Pick<NativeEvent, 'cache_write_tokens' | 'cache_5m_tokens'>>, pricing: Pricing): number | null {
    if (event.kind !== 'generation')
        return null;
    const base = pricing.models[event.model];
    if (!base || event.input_tokens == null || event.cached_tokens == null || event.output_tokens == null || event.cached_tokens > event.input_tokens)
        return null;
    const rate = base.long_context && event.input_tokens > base.long_context.above_tokens ? base.long_context : base;
    const writes = Number(event.cache_write_tokens || 0), short = event.cache_5m_tokens == null ? null : Number(event.cache_5m_tokens);
    let writeCost = 0;
    if (writes > event.input_tokens - event.cached_tokens)
        return null;
    if (writes > 0) {
        if (short != null && short <= writes && rate.write_5m != null && rate.write_1h != null)
            writeCost = short * rate.write_5m + (writes - short) * rate.write_1h;
        else if (rate.write != null)
            writeCost = writes * rate.write;
        else
            return null;
    }
    return ((event.input_tokens - event.cached_tokens - writes) * rate.input + event.cached_tokens * rate.cached + event.output_tokens * rate.output + writeCost) / 1e6;
}
export function scopeFrom(params: URLSearchParams): Scope {
    const range = params.get('range') || '30d';
    if (!['1d', '7d', '30d', '90d', 'all'].includes(range))
        throw Error('Invalid date range');
    const timezone = params.get('timezone') || params.get('zone') || 'UTC';
    try {
        new Intl.DateTimeFormat('en', { timeZone: timezone });
    }
    catch {
        throw Error('Invalid display timezone');
    }
    return { workspace: params.get('workspace') || '', project: params.get('project') || '', range, timezone,
        ...(params.get('scopeModel') ? { model: params.get('scopeModel')! } : {}),
        ...(params.get('harness') ? { harness: params.get('harness')! } : {}),
        ...(params.get('work') ? { task: params.get('work')! } : {}) };
}
export function queryFrom(params: URLSearchParams): Query {
    const raw = params.get('query');
    let value;
    try { value = raw ? JSON.parse(raw) : {}; }
    catch { throw Error('Invalid record query'); }
    if (!value || typeof value !== 'object' || Array.isArray(value))
        throw Error('Invalid record query');
    const limit = Number(params.get('limit') || value.limit || 20), offset = Number(params.get('offset') || value.offset || 0);
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100 || !Number.isSafeInteger(offset) || offset < 0)
        throw Error('Invalid record page');
    if (typeof (value.search ?? '') !== 'string' || (value.search || '').length > 1000 || typeof (value.filters ?? {}) !== 'object' || value.filters === null || Array.isArray(value.filters) || Object.entries(value.filters ?? {}).some(([k, v]) => k.length > 80 || typeof v !== 'string' || v.length > 200) || Object.keys(value.filters ?? {}).length > 30)
        throw Error('Invalid record query');
    if (value.sort != null && (typeof value.sort !== 'string' || value.sort.length > 80))
        throw Error('Invalid sort');
    return { search: value.search || '', filters: value.filters || {}, sort: value.sort || null, direction: value.direction === -1 ? -1 : 1, limit, offset };
}
export { normalize, collection } from './record-query.ts';
export function rolling(points: {
    date: string;
    numerator: number;
    denominator: number;
}[], days = 7) {
    return points.map(point => { const at = Date.parse(point.date), window = points.filter(p => Date.parse(p.date) > at - days * 86400000 && Date.parse(p.date) <= at), den = window.reduce((s, p) => s + p.denominator, 0); return { ...point, value: point.denominator ? point.numerator / point.denominator : null, average: den ? window.reduce((s, p) => s + p.numerator, 0) / den : null }; });
}
export function failureLoops(events: NativeEvent[]) {
    const loops: {
        ids: string[];
        type: string;
        detail: string;
    }[] = [];
    let chain: NativeEvent[] = [];
    for (const event of events.filter(e => e.kind === 'tool')) {
        if (event.failed === 1 && chain.length && event.turn_key === chain.at(-1)?.turn_key && event.signature === chain.at(-1)?.signature)
            chain.push(event);
        else {
            if (chain.length >= 3)
                loops.push({ ids: chain.map(e => e.id), type: 'Same call keeps failing', detail: `${chain[0].name} failed ${chain.length} times` });
            chain = event.failed === 1 ? [event] : [];
        }
    }
    if (chain.length >= 3)
        loops.push({ ids: chain.map(e => e.id), type: 'Same call keeps failing', detail: `${chain[0].name} failed ${chain.length} times` });
    return loops;
}
