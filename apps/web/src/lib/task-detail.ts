import { context, taskScope, taskFacts } from './repository.ts';
import { nativeEvidence } from './task-evidence.ts';
import { pg, queryCh } from './database.ts';
import { iso } from './domain.ts';
export async function taskDetail(id: string) {
    const c = await context(await taskScope(id)), f = taskFacts(c, id);
    if (!f.task)
        throw Error('Unknown task');
    const [images, jobs] = await Promise.all([pg() `SELECT id,event_id,mime FROM retained_images WHERE task_id=${id}`, pg() `SELECT id,status,error,created_at,model FROM analysis_jobs WHERE task_id=${id} ORDER BY created_at DESC LIMIT 20`]);
    const native = await queryCh<import('./types.ts').NativeEvent>('SELECT id,kind,name,command,payload,failed,event_time,time_known FROM events FINAL WHERE turn_key IN {keys:Array(String)} ORDER BY event_time,id LIMIT 10000', { keys: f.turns.map(t => t.turn_key) });
    const phases = f.groups.map(g => ({ ...g, events: f.events.filter(e => g.event_ids.includes(e.id)).map(e => ({ id: e.id, at: e.time_known ? e.event_time : null, runtime: e.runtime })) }));
    return JSON.parse(JSON.stringify({ task: f.task, metrics: f.metrics, turns: f.turns, groups: phases, notes: [...nativeEvidence(native), ...f.notes], analysis: f.analysis, loops: f.loops, images, jobs, events: f.events.map(e => ({ id: e.id, kind: e.kind, name: e.name, model: e.model, at: e.time_known ? iso(e.event_time) : null, runtime: e.runtime, failed: e.failed, category: c.categories.get(e.id) || 'Unclassified' })), duration: f.duration, complete: f.complete }));
}
