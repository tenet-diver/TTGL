import { LUNA_MODEL, resolveSubscription } from './execution-policy.ts';
export { analysisSchema } from './analysis-contract.ts';
import { randomUUID } from 'node:crypto';
import type postgres from 'postgres';
import { pg, queryCh } from './database.ts';
import { context, taskFacts, type Context } from './repository.ts';
import { hash } from './domain.ts';
import type { Scope, NativeEvent } from './types.ts';
export function analysisSnapshot(c: Context, id: string) {
    const f = taskFacts(c, id);
    if (!f.task)
        throw Error('Unknown task');
    if (!f.events.length)
        throw Error('No recorded events to analyze');
    if (f.events.length > 10000)
        throw Error('Select a smaller task with at most 10,000 source events');
    return { schema_version: 2, task: { id, title: f.task.title, goal: f.task.goal, acceptance: f.task.acceptance }, steps: f.events.map(e => ({ id: e.id, turn_key: e.turn_key, source_version: Number(e.version), kind: e.kind, name: e.name, model: e.model, at: e.time_known ? e.event_time : null, runtime: e.runtime, failed: e.failed, command: e.command.slice(0, 2000), output: e.output_excerpt.slice(0, 1500), input_tokens: e.input_tokens, output_tokens: e.output_tokens, output_hash: e.output_hash })), turns: f.turns.map(t => ({ turn_key: t.turn_key, session_id: t.session_id, started_at: t.started_at, finished_at: t.finished_at, completed: t.completed, signals: t.source?.signals || [], last_message: JSON.stringify(t.source?.last_message || '').slice(0, 4000), prompt: t.prompt.slice(0, 4000) })) };
}
export async function queueTask(tx: postgres.TransactionSql, taskId: string, scope: Scope, batchId: string | null = null) {
    if (process.env.OBS_MODEL && process.env.OBS_MODEL !== LUNA_MODEL)
        throw Error('Only gpt-6-luna via the source Codex subscription is supported');
    const c = await context({ ...scope, range: 'all', task: taskId }), f = taskFacts(c, taskId), full = await queryCh<NativeEvent>('SELECT * FROM events FINAL WHERE turn_key IN {keys:Array(String)} ORDER BY event_time,id LIMIT 10000', { keys: f.turns.map(t => t.turn_key) }), base = analysisSnapshot({ ...c, events: full }, taskId);
    if (f.turns.length > 200) throw Error('Select a task containing at most 200 native prompts');
    const nearby = await tx `SELECT DISTINCT ON (t.turn_key) t.turn_key,t.session_id,t.prompt,t.started_at,t.finished_at,t.completed,t.source FROM turns anchor CROSS JOIN LATERAL (SELECT n.* FROM turns n WHERE n.session_id=anchor.session_id ORDER BY abs(extract(epoch FROM (n.started_at-anchor.started_at))) NULLS LAST,n.turn_key LIMIT 17) t WHERE anchor.turn_key=ANY(${f.turns.map(t=>t.turn_key)}::text[]) ORDER BY t.turn_key LIMIT 3400`;
    const ownKeys = new Set(f.turns.map(t=>t.turn_key)), neighbors = [...f.turns, ...nearby.filter(t=>!ownKeys.has(t.turn_key))].slice(0,200).toSorted((a,b)=>String(a.started_at || '').localeCompare(String(b.started_at || '')) || a.turn_key.localeCompare(b.turn_key));
    const snapshot = { ...base, subscription_binding: await resolveSubscription(f.turns), prompt_context: neighbors.map(t => ({ turn_key: t.turn_key, session_id: t.session_id, prompt: String(t.prompt).slice(0, 4000), started_at: t.started_at, finished_at: t.finished_at, completed: t.completed, signals: t.source?.signals || [], last_message: JSON.stringify(t.source?.last_message || '').slice(0, 4000) })) }, digest = hash(snapshot);
    if (Buffer.byteLength(JSON.stringify(snapshot)) > 1000000)
        throw Error('Task analysis snapshot exceeds 1 MB; split the task into smaller explicit assignments');
    await tx `SELECT pg_advisory_xact_lock(hashtext(${taskId}))`;
    const old = await tx `SELECT id,status,snapshot_hash FROM analysis_jobs WHERE task_id=${taskId} ORDER BY created_at DESC`;
    if (old.some(j => ['running', 'queued', 'legacy_running', 'legacy_queued', 'uncertain'].includes(j.status)))
        return { task_id: taskId, status: 'retained_active_or_uncertain', id: old.find(j => ['running', 'queued', 'legacy_running', 'legacy_queued', 'uncertain'].includes(j.status))!.id };
    if (old.some(j => j.snapshot_hash === digest))
        return { task_id: taskId, status: 'retained_attempt', id: old.find(j => j.snapshot_hash === digest)!.id };
    const id = randomUUID();
    await tx `INSERT INTO analysis_jobs(id,task_id,batch_id,operation,status,model,snapshot_hash,snapshot) VALUES(${id},${taskId},${batchId},'process','queued',${LUNA_MODEL},${digest},${tx.json(snapshot)})`;
    return { id, task_id: taskId, status: 'queued' };
}
export async function queueBatch(tx: postgres.TransactionSql, scope: Scope) {
    const c = await context(scope), ids = c.tasks.map(t => t.id);
    if (ids.length > 10000)
        throw Error('Narrow the scope to 10,000 tasks');
    const id = randomUUID(), digest = hash(ids.toSorted());
    await tx `INSERT INTO analysis_batches(id,corpus_hash,source) VALUES(${id},${digest},${tx.json({ scope, task_ids: ids, automatic_retries: 0 })})`;
    const results = [];
    for (const task of c.tasks) {
        if (!taskFacts(c, task.id).events.length) {
            results.push({ task_id: task.id, status: 'no_source_events' });
            continue;
        }
        results.push(await queueTask(tx, task.id, { ...scope, range: 'all' }, id));
    }
    return { id, results, queued: results.filter(r => r.status === 'queued').length };
}
