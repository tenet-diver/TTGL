/** Observatory's adapter for EVLV reader semantic tokens and its activity palette.
 * Identities, never list positions, select colours. Labels remain the evidence.
 */
export const tones = {
    blue: 'var(--tone-blue)', green: 'var(--tone-green)', yellow: 'var(--tone-yellow)',
    orange: 'var(--tone-orange)', pink: 'var(--tone-pink)', lime: 'var(--tone-lime)',
    violet: 'var(--tone-violet)', teal: 'var(--tone-teal)', red: 'var(--tone-error)',
    warning: 'var(--tone-warning)', neutral: 'var(--tone-neutral)',
} as const;
export type Tone = keyof typeof tones;
export type ColorKind = 'activity' | 'status' | 'relationship' | 'event' | 'model' | 'tool' | 'series';
export const chartPalette = [tones.blue, tones.green, tones.yellow, tones.orange, tones.pink, tones.lime, tones.violet, tones.teal];
const normalize = (value: unknown) => String(value ?? '').trim().toLowerCase().replace(/[\s·-]+/g, '_');
const activityTones: Record<string, Tone> = {
    explore: 'blue', investigate: 'blue', implement: 'green', verify: 'yellow', test: 'yellow', review: 'violet',
    deliver: 'orange', operate: 'orange', document: 'teal', debug: 'pink', coordinate: 'teal', plan: 'lime', research: 'violet',
    other: 'neutral', unknown: 'neutral', unclassified: 'neutral', uncategorized: 'neutral', unreviewed: 'neutral', start: 'neutral', end: 'neutral',
};
export const activityColors: Record<string, string> = Object.fromEntries(Object.entries(activityTones).map(([key, tone]) => [key, tones[tone]]));
export type StatusShape = 'success' | 'error' | 'warning' | 'active' | 'pending' | 'cancelled' | 'unknown';
const statusGroups: Record<StatusShape, string[]> = {
    success: ['completed', 'complete', 'done', 'passed', 'confirmed', 'retained', 'explained', 'succeeded', 'success', 'ok'],
    error: ['failed', 'dead_end', 'error', 'tool_error', 'rejected', 'conflict', 'block'],
    warning: ['blocked', 'warning', 'warning_signs', 'warn', 'ask', 'needed_a_fix', 'paused', 'interrupted', 'uncertain'],
    active: ['active', 'working', 'running', 'in_progress', 'collecting', 'continuation'],
    pending: ['pending', 'queued', 'waiting', 'waiting_for_input'],
    cancelled: ['cancelled', 'canceled', 'skipped', 'not_applicable', 'disabled', 'log'],
    unknown: ['unknown', 'unclassified', 'unverified', 'unmetered', 'unavailable'],
};
const statusTones: Record<StatusShape, Tone> = { success: 'green', error: 'red', warning: 'warning', active: 'blue', pending: 'yellow', cancelled: 'neutral', unknown: 'neutral' };
export function statusShape(value: unknown): StatusShape {
    const key = normalize(value).replace(/^legacy_/, '');
    return (Object.keys(statusGroups) as StatusShape[]).find(shape => statusGroups[shape].includes(key)) || 'unknown';
}
const relationships: Record<string, Tone> = { new_task: 'violet', continuation: 'blue', course_correction: 'warning', interruption: 'pink', unknown: 'neutral' };
const events: Record<string, Tone> = { generation: 'teal', api_call: 'teal', model: 'teal', tool: 'blue', tool_error: 'red', compaction: 'violet', finite_operation: 'blue', agent_blocking: 'blue', background_service_lifetime: 'orange' };
function identityTone(value: unknown): Tone {
    const key = normalize(value);
    if (!key || ['unknown', 'unclassified', 'other', '—'].includes(key)) return 'neutral';
    let hash = 2166136261;
    for (const character of key) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
    return (['blue', 'green', 'yellow', 'orange', 'pink', 'lime', 'violet', 'teal'] as Tone[])[(hash >>> 0) % chartPalette.length];
}
export function toneFor(value: unknown, kind: ColorKind = 'activity'): Tone {
    const key = normalize(value);
    if (kind === 'activity') return activityTones[key] || identityTone(key);
    if (kind === 'status') return statusTones[statusShape(value)];
    if (kind === 'relationship') return relationships[key] || 'neutral';
    if (kind === 'event') return events[key] || 'neutral';
    if (kind === 'series') {
        const tokenTones: Record<string, Tone> = { cache_read: 'teal', cache_write: 'violet', uncached_input: 'blue', other_input: 'blue', output: 'orange', value: 'neutral', average: 'blue' };
        return activityTones[key] || tokenTones[key] || events[key] || identityTone(key);
    }
    return identityTone(key);
}
export const colorFor = (value: unknown, kind: ColorKind = 'activity') => tones[toneFor(value, kind)];
export const colorStyle = (value: unknown, kind: ColorKind = 'activity') => ({ '--semantic-color': colorFor(value, kind) });
export function fieldColorKind(key: string): ColorKind | undefined {
    if (['category', 'categories', 'activity_type', 'task_type', 'from', 'to'].includes(key)) return 'activity';
    if (['status', 'state', 'outcome', 'luna_outcome', 'mode', 'interpretation'].includes(key)) return 'status';
    if (['relationship', 'prompt_relationship'].includes(key)) return 'relationship';
    if (key === 'kind') return 'event';
    if (['model', 'models'].includes(key)) return 'model';
}
