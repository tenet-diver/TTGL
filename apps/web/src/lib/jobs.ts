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
    return { task: { id, title: f.task.title, goal: f.task.goal, acceptance: f.task.acceptance }, steps: f.events.map(e => ({ id: e.id, source_version: Number(e.version), kind: e.kind, name: e.name, model: e.model, at: e.time_known ? e.event_time : null, runtime: e.runtime, failed: e.failed, command: e.command.slice(0, 2000), output: e.output_excerpt.slice(0, 1500), input_tokens: e.input_tokens, output_tokens: e.output_tokens, output_hash: e.output_hash })), turns: f.turns.map(t => ({ turn_key: t.turn_key, prompt: t.prompt.slice(0, 2000) })) };
}
export async function queueTask(tx: postgres.TransactionSql, taskId: string, scope: Scope, batchId: string | null = null) {
    const c = await context({ ...scope, range: 'all', task: taskId }), f = taskFacts(c, taskId), full = await queryCh<NativeEvent>('SELECT * FROM events FINAL WHERE turn_key IN {keys:Array(String)} ORDER BY event_time,id LIMIT 10000', { keys: f.turns.map(t => t.turn_key) }), snapshot = analysisSnapshot({ ...c, events: full }, taskId), digest = hash(snapshot);
    if (Buffer.byteLength(JSON.stringify(snapshot)) > 1000000)
        throw Error('Task analysis snapshot exceeds 1 MB; split the task into smaller explicit assignments');
    await tx `SELECT pg_advisory_xact_lock(hashtext(${taskId}))`;
    const old = await tx `SELECT id,status,snapshot_hash FROM analysis_jobs WHERE task_id=${taskId} ORDER BY created_at DESC`;
    if (old.some(j => ['running', 'queued', 'legacy_running', 'legacy_queued', 'uncertain'].includes(j.status)))
        return { task_id: taskId, status: 'retained_active_or_uncertain', id: old.find(j => ['running', 'queued', 'legacy_running', 'legacy_queued', 'uncertain'].includes(j.status))!.id };
    if (old.some(j => j.snapshot_hash === digest))
        return { task_id: taskId, status: 'retained_attempt', id: old.find(j => j.snapshot_hash === digest)!.id };
    const current = taskFacts(c, taskId);
    if (current.complete && current.analysis)
        return { task_id: taskId, status: 'already_explained', id: current.analysis.id };
    const id = randomUUID();
    await tx `INSERT INTO analysis_jobs(id,task_id,batch_id,operation,status,model,snapshot_hash,snapshot) VALUES(${id},${taskId},${batchId},'process','queued',${process.env.OBS_MODEL || 'gpt-6-luna'},${digest},${tx.json(snapshot)})`;
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
export const analysisSchema = { type: 'object', additionalProperties: false, required: ['summary', 'task_type', 'outcome', 'outcome_reason', 'intervention', 'intervention_reason', 'subtasks', 'knowledge'], properties: { summary: { type: 'string', maxLength: 4000 }, task_type: { type: 'string' }, outcome: { type: 'string', enum: ['done', 'failed', 'dead_end', 'in_progress', 'cancelled', 'unknown'] }, outcome_reason: { type: 'string', maxLength: 2000 }, intervention: { type: 'string', enum: ['observed', 'possible', 'none_observed', 'unknown'] }, intervention_reason: { type: 'string', maxLength: 2000 }, subtasks: { type: 'array', minItems: 1, maxItems: 100, items: { type: 'object', additionalProperties: false, required: ['title', 'summary', 'category', 'event_ids', 'confidence', 'outcome'], properties: { title: { type: 'string', maxLength: 200 }, summary: { type: 'string', maxLength: 2000 }, category: { type: 'string', enum: ['explore', 'implement', 'verify', 'deliver', 'debug', 'coordinate', 'research', 'plan', 'other'] }, event_ids: { type: 'array', minItems: 1, items: { type: 'string' } }, confidence: { type: 'number', minimum: 0, maximum: 1 }, outcome: { type: 'string', enum: ['done', 'failed', 'dead_end', 'in_progress', 'cancelled', 'unknown'] } } } }, knowledge: { type: 'array', maxItems: 20, items: { type: 'object', additionalProperties: false, required: ['title', 'statement', 'event_ids'], properties: { title: { type: 'string' }, statement: { type: 'string' }, event_ids: { type: 'array', items: { type: 'string' } } } } } } };
