import { z } from 'zod';
import { randomUUID, createHash } from 'node:crypto';
import { pg, queryCh } from './database.ts';
import { parseNative } from './native-parser.ts';
import { ingestEvents, flushOutbox } from './ingest.ts';
import { restoreRaw } from './raw-store.ts';
import { subscriptionBinding, LUNA_MODEL } from './execution-policy.ts';
import { archive, scopedRecord, study, fingerprint, type ExperienceScope } from './experience-store.ts';
import { context } from './repository.ts';
import { analysisSnapshot } from './jobs.ts';
import type { NativeEvent } from './types.ts';
export async function ingestExperienceTrace(scope: ExperienceScope, raw: unknown) {
    const p = z.strictObject({ artifactId: z.string().min(1), taskInstanceId: z.string().min(1), title: z.string().min(1).max(200),
        goal: z.string().max(8000), acceptance: z.string().max(8000), accountHash: z.string().regex(/^[a-f0-9]{64}$/),
        isolationReceiptHash: z.string().regex(/^[a-f0-9]{64}$/) }).parse(raw);
    await study(scope);
    const binding = await subscriptionBinding(process.env.OBS_EXPERIENCE_SOURCE_HOME);
    if (p.accountHash !== binding.account_hash) throw Error('Native trace source does not match the canonical local subscription');
    const manifest = await scopedRecord(scope, 'artifact-manifest', p.artifactId);
    const chunks = manifest.chunks as Array<{ archiveId: string; sha256: string }>;
    const parts: Buffer[] = [];
    for (const c of chunks) parts.push(await restoreRaw(c.archiveId));
    const bytes = Buffer.concat(parts);
    if (bytes.length !== manifest.bytes || createHash('sha256').update(bytes).digest('hex') !== manifest.sha256) throw Error('Native trace archive does not reconcile');
    const parsed = parseNative(bytes.toString('utf8'), 'codex', 'experience/' + scope.experimentId + '/' + p.artifactId);
    if (parsed.malformed || !parsed.events.length || !parsed.turns.length) throw Error('Native source lacks complete event/turn identity');
    const taskId = 'experience:' + fingerprint([scope, p.taskInstanceId]);
    const db = pg();
    await db`INSERT INTO tasks(id,project_id,title,goal,acceptance,source) VALUES(${taskId},${scope.projectId},${p.title},${p.goal},${p.acceptance},${db.json({ experience_study: scope.experimentId, task_instance: p.taskInstanceId, isolation_receipt_hash: p.isolationReceiptHash, raw_artifact_id: p.artifactId })}) ON CONFLICT DO NOTHING`;
    const [owner] = await db`SELECT project_id,source FROM tasks WHERE id=${taskId}`;
    if (owner.project_id !== scope.projectId || owner.source.task_instance !== p.taskInstanceId) throw Error('Task identity conflicts with the retained source owner');
    for (let i = 0; i < parsed.events.length; i += 1000) {
        const result = await ingestEvents(parsed.events.slice(i, i + 1000));
        if (result.conflicts) throw Error('Native usage conflict; trace retained without replacing counters');
    }
    for (const t of parsed.turns) {
        await db.begin(async tx => {
            const [existing] = await tx`SELECT task_id FROM assignments WHERE turn_key=${t.turn_key}`;
            if (existing && existing.task_id !== taskId) {
                const [task] = await tx`SELECT source FROM tasks WHERE id=${existing.task_id}`;
                if (!task?.source?.native_turn) throw Error('Native turn belongs to another explicit task');
            }
            await tx`UPDATE turns SET prompt=${t.prompt},source=${tx.json({ ...t.source, analysis_binding: binding })},completed=${t.completed},finished_at=${t.finished_at} WHERE turn_key=${t.turn_key}`;
            await tx`INSERT INTO assignments(turn_key,task_id) VALUES(${t.turn_key},${taskId}) ON CONFLICT(turn_key) DO UPDATE SET task_id=EXCLUDED.task_id`;
        });
    }
    while (await flushOutbox()) { }
    const c = await context({ project: scope.projectId, workspace: '', range: 'all', timezone: 'UTC', task: taskId });
    const full = await queryCh<NativeEvent>('SELECT * FROM events FINAL WHERE turn_key IN {keys:Array(String)} ORDER BY event_time,id LIMIT 10001', { keys: parsed.turns.map(t => t.turn_key) });
    const base = analysisSnapshot({ ...c, events: full }, taskId);
    const snapshot = { ...base, subscription_binding: binding, prompt_context: base.turns,
        coverage: { sourceComplete: full.every(e => e.command.length <= 2000 && (e.output_chars == null || e.output_chars <= 1500)),
            excerpted: full.some(e => e.command.length > 2000 || (e.output_chars != null && e.output_chars > 1500)), missingRanges: [] } };
    if (Buffer.byteLength(JSON.stringify(snapshot)) > 1000000 || base.turns.length > 200) throw Error('Trace requires registered chronological blocks before model annotation');
    const snapshotHash = fingerprint(snapshot), configurationHash = fingerprint(['experience-base-v2-001', p.isolationReceiptHash]);
    await archive(scope, 'base-analysis-input', snapshotHash, snapshot);
    const id = randomUUID();
    await db.begin(async tx => {
        await tx`SELECT pg_advisory_xact_lock(hashtext(${fingerprint([scope, snapshotHash, configurationHash])}))`;
        const [old] = await tx`SELECT id FROM experience_jobs WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND snapshot_hash=${snapshotHash} AND configuration_hash=${configurationHash}`;
        if (old) return;
        await tx`INSERT INTO analysis_jobs(id,task_id,operation,model,snapshot_hash,snapshot) VALUES(${id},${taskId},'experience-base-v2',${LUNA_MODEL},${snapshotHash},${tx.json(snapshot)})`;
        await tx`INSERT INTO experience_jobs(project_id,experiment_id,id,base_job_id,operation,snapshot_hash,configuration_hash,source_binding,input,invocation_id) VALUES(${scope.projectId},${scope.experimentId},${id},${id},'base-v2',${snapshotHash},${configurationHash},${tx.json(binding)},${tx.json(snapshot)},${id + ':luna'})`;
    });
    const [job] = await db`SELECT id,status FROM experience_jobs WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND snapshot_hash=${snapshotHash} AND configuration_hash=${configurationHash}`;
    return { taskId, jobId: job.id, status: job.status, sourceEvents: full.length, modelCalls: 0 };
}
