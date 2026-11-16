import { context, taskScope, taskFacts, metrics } from './repository.ts';
import { nativeEvidence } from './task-evidence.ts';
import { pg, queryCh } from './database.ts';
import { iso } from './domain.ts';
export async function taskDetail(id: string, subtaskId?: string) {
    const c = await context(await taskScope(id)), f = taskFacts(c, id);
    if (!f.task)
        throw Error('Unknown task');
    const selected = subtaskId ? f.groups.find(g => g.id === subtaskId) : null;
    if (subtaskId && !selected)
        throw Error('Unknown subtask');
    if (selected && !f.complete)
        throw Error('Subtask analysis is stale; analyze the task again before viewing its steps');
    const selectedIds = selected ? new Set(selected.event_ids) : null, events = selectedIds ? f.events.filter(e => selectedIds.has(e.id)) : f.events;
    const turnKeys = new Set(events.map(e => e.turn_key)), turns = selected ? f.turns.filter(t => turnKeys.has(t.turn_key)) : f.turns;
    const [images, jobs] = await Promise.all([pg() `SELECT id,event_id,mime FROM retained_images WHERE task_id=${id} OR event_id=ANY(${f.events.map(e => e.id)}::text[])`, pg() `SELECT id,status,error,created_at,model FROM analysis_jobs WHERE task_id=${id} ORDER BY created_at DESC LIMIT 20`]);
    const native = await queryCh<import('./types.ts').NativeEvent>('SELECT id,kind,name,command,payload,failed,event_time,time_known FROM events FINAL WHERE id IN {ids:Array(String)} ORDER BY event_time,id LIMIT 10000', { ids: events.map(e => e.id) });
    const phases = (selected ? [selected] : f.groups).map(g => ({ ...g, href: '/tasks/' + encodeURIComponent(id) + '/subtasks/' + encodeURIComponent(g.id), state: g.result.state || 'unknown', outcome: g.result.outcome || 'unknown', outcome_reason: g.result.outcome_reason || 'No source-backed outcome interpretation recorded', failure_reason: g.result.failure_reason || '', steps: g.event_ids.length, events: f.events.filter(e => g.event_ids.includes(e.id)).map(e => ({ id: e.id, at: e.time_known ? e.event_time : null, runtime: e.runtime })) }));
    const relationRows = f.complete && Array.isArray(f.analysis?.result.prompt_relations) ? f.analysis.result.prompt_relations : [];
    const relatedKeys = relationRows.flatMap((r: any) => typeof r.related_turn_key === 'string' ? [r.related_turn_key] : []);
    const related = await pg() `SELECT t.turn_key,t.prompt,a.task_id FROM turns t LEFT JOIN assignments a USING(turn_key) WHERE t.turn_key=ANY(${relatedKeys}::text[])`;
    const relations = turns.map(t => { const r = relationRows.find((r: any) => r.turn_key === t.turn_key) as Record<string, unknown> | undefined; const previous = related.find(p => p.turn_key === r?.related_turn_key); return { related_prompt: previous?.prompt || '', href: previous?.task_id ? '/tasks/' + encodeURIComponent(previous.task_id) : null, id: t.turn_key, prompt: t.prompt, started_at: t.started_at, ...(r || { relationship: 'unknown', reason: 'Awaiting Luna prompt classification', confidence: null }) }; });
    const times = events.filter(e => e.time_known).map(e => Date.parse(iso(e.event_time)!));
    return JSON.parse(JSON.stringify({ task: f.task, selected_subtask: selected ? phases[0] : null, relations, metrics: selected ? metrics(events, c.pricing) : f.metrics, turns, groups: phases, notes: [...nativeEvidence(native), ...(selected ? [] : f.notes)], analysis: selected ? { summary: selected.summary, result: selected.result } : f.analysis, loops: selectedIds ? f.loops.filter(l => l.ids.every(id => selectedIds.has(id))) : f.loops, images: images.filter(i => !selectedIds || selectedIds.has(i.event_id)), jobs: selected ? [] : jobs, events: events.map(e => ({ id: e.id, kind: e.kind, name: e.name, model: e.model, at: e.time_known ? iso(e.event_time) : null, runtime: e.runtime, runtime_role: e.runtime_role, command: e.command, failed: e.failed, category: c.categories.get(e.id) || 'Unclassified' })), duration: selected ? (times.length ? (Math.max(...times) - Math.min(...times)) / 1000 : null) : f.duration, complete: f.complete }));
}
