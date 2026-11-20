import type { Query } from './types.ts';
export const scopeKey = 'observatory-scope:v1';
export const scopeDefaults = { project: '', workspace: '', range: '30d', timezone: 'UTC', scopeModel: '', harness: '', work: '' };
export const scopeKeys = Object.keys(scopeDefaults) as (keyof typeof scopeDefaults)[];
const fallback = new Map<string, string>();
const unsaved = new Set<string>();
export function readLocal(key: string): string | null {
    if (typeof window === 'undefined') return null;
    if (unsaved.has(key)) return fallback.get(key) || null;
    try { return window.localStorage.getItem(key); } catch { return fallback.get(key) || null; }
}
export function writeLocal(key: string, value: string) {
    if (typeof window === 'undefined') return;
    fallback.set(key, value);
    try { window.localStorage.setItem(key, value); unsaved.delete(key); } catch { unsaved.add(key); }
}
export function readJson(key: string): unknown {
    try { const raw = readLocal(key); return raw && raw.length <= 50000 ? JSON.parse(raw) : null; } catch { return null; }
}
const object = (value: unknown): Record<string, unknown> => value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
export function savedScope(raw: unknown): typeof scopeDefaults {
    const value = object(raw), result = { ...scopeDefaults };
    for (const key of ['project', 'workspace', 'scopeModel', 'harness', 'work'] as const)
        if (typeof value[key] === 'string' && value[key].length <= (key === 'project' ? 400 : 3000)) result[key] = value[key];
    if (typeof value.range === 'string' && ['1d', '7d', '30d', '90d', 'all'].includes(value.range)) result.range = value.range;
    if (typeof value.timezone === 'string' && value.timezone.length <= 100) {
        try { new Intl.DateTimeFormat('en', { timeZone: value.timezone }); result.timezone = value.timezone; } catch { }
    }
    return result;
}
export const viewFilterKey = (path: string) => 'observatory-view:v1:' + path;
export function filterKeys(path: string) {
    return path === '/tools' ? ['family', 'action', 'measure', 'model', 'category', 'day'] : ['model', 'category', 'day'];
}
function savedFilters(path: string, raw: unknown) {
    const value = object(raw), result: Record<string, string> = {};
    for (const key of filterKeys(path)) {
        const v = value[key];
        if (typeof v !== 'string' || v.length > 500) continue;
        if (key === 'measure' && !['calls', 'runtime', 'call_cost', 'context_cost'].includes(v)) continue;
        if (key === 'day' && v && !/^\d{4}-\d{2}-\d{2}$/.test(v)) continue;
        result[key] = v;
    }
    return result;
}
/** Only view controls are remembered. Source IDs, selections and open evidence are transient. */
export function restoreView(path: string, query: URLSearchParams, storedScope: unknown, storedFilters: unknown) {
    const scope = savedScope(storedScope), fields = Object.fromEntries(scopeKeys.filter(k => query.has(k)).map(k => [k, query.get(k)]));
    if (!query.has('timezone') && query.has('zone')) fields.timezone = query.get('zone');
    const nextScope = savedScope({ ...scope, ...fields });
    const previousFilters = savedFilters(path, storedFilters);
    const explicitFilters = Object.fromEntries(filterKeys(path).filter(k => query.has(k)).map(k => [k, query.get(k)]));
    if (query.has('family') && query.get('family') !== previousFilters.family && !query.has('action')) previousFilters.action = '';
    const filters = savedFilters(path, { ...previousFilters, ...explicitFilters });
    const next = new URLSearchParams(query);
    for (const key of scopeKeys) next.set(key, nextScope[key]);
    for (const [key, value] of Object.entries(filters)) next.set(key, value);
    return { scope: nextScope, filters, query: next };
}
export const tableDefaults: Query = { search: '', filters: {}, sort: null, direction: 1, offset: 0, limit: 20 };
export function savedTable(raw: unknown) {
    const value = object(raw), q = object(value.query), query = { ...tableDefaults, filters: {} as Record<string, string> };
    if (typeof q.search === 'string' && q.search.length <= 1000) query.search = q.search;
    if (typeof q.sort === 'string' && q.sort.length <= 80) query.sort = q.sort;
    query.direction = q.direction === -1 ? -1 : 1;
    if (typeof q.limit === 'number' && [10, 20, 50, 100].includes(q.limit)) query.limit = q.limit;
    if (Number.isSafeInteger(q.offset) && Number(q.offset) >= 0) query.offset = Number(q.offset);
    query.filters = Object.fromEntries(Object.entries(object(q.filters)).filter(([key, v]) => key.length <= 80 && typeof v === 'string' && v.length <= 200).slice(0, 30)) as Record<string, string>;
    const visibility = Object.fromEntries(Object.entries(object(value.visibility)).filter(([key, v]) => key.length <= 80 && typeof v === 'boolean')) as Record<string, boolean>;
    return { query, visibility, filtersOpen: value.filtersOpen === true };
}
export function queryForColumns(query: Query, keys: string[]): Query {
    const allowed = new Set(keys);
    return { ...query, sort: query.sort && allowed.has(query.sort) ? query.sort : null, filters: Object.fromEntries(Object.entries(query.filters).filter(([key]) => allowed.has(key))) };
}
