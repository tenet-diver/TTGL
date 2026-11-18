import type postgres from 'postgres';
import { z } from 'zod';
import { pg } from './database.ts';
import { restoreRaw } from './raw-store.ts';
import { validateEnvelope, type EnvelopeSource, type Experience } from './experience-contract.ts';
import { archive, study, fingerprint, versionId, enqueueFact, appendRecord, scopedRecord, type ExperienceScope } from './experience-store.ts';
export const studyConfigSchema = z.strictObject({
    schemaVersion: z.literal(1), mode: z.enum(['frozen_memory', 'online', 'exact_repeat_diagnostic']), sourceCommit: z.string().min(1),
    policyVersion: z.string().min(1), allowedArms: z.array(z.string().min(1)).min(1).max(20), allowedSplits: z.array(z.string()).min(1).max(5),
    exclusionRegistryHash: z.string().regex(/^[a-f0-9]{64}$/),
    exclusions: z.strictObject({ taskIds: z.array(z.string()).max(20000), leakageGroups: z.array(z.string()).max(20000) }),
    repositoryCutoffs: z.array(z.strictObject({ repository: z.string(), sourceBaseCommit: z.string(), targetBaseCommit: z.string(), receiptHash: z.string().regex(/^[a-f0-9]{64}$/) })).max(20000),
    maxSnapshotMembers: z.number().int().positive().max(10000),
    publicDependencyEventIds: z.array(z.string()).max(10000),
    embedding: z.strictObject({ modelRevision: z.string().min(1), dimensions: z.number().int().min(1).max(8192), normalization: z.literal('l2'), textVersion: z.string().min(1), reviewReceiptHash: z.string().regex(/^[a-f0-9]{64}$/) }).nullable(),
    retrieval: z.strictObject({ taskPacketTokens: z.number().int().min(100).max(8000), subtaskPacketTokens: z.number().int().min(100).max(8000), candidatesPerGranularity: z.number().int().min(1).max(100), allowCandidates: z.boolean() }),
    modelExecution: z.strictObject({ enabled: z.boolean(), readinessHash: z.string().regex(/^[a-f0-9]{64}$/).nullable(), maximumInvocations: z.number().int().positive(), maximumTokens: z.number().int().positive(), maximumElapsedSeconds: z.number().positive() }),
});
export async function registerStudy(scope: ExperienceScope, input: unknown) {
    const config = studyConfigSchema.parse(input);
    if (config.modelExecution.enabled && !config.modelExecution.readinessHash) throw Error('Model execution requires a frozen readiness receipt');
    if (config.exclusionRegistryHash !== fingerprint(config.exclusions)) throw Error('Exclusion registry hash mismatch');
    if (config.mode === 'frozen_memory' && config.allowedSplits.some(s => !['memory_build', 'router_development'].includes(s))) throw Error('Frozen memory cannot admit held-out or exact-repeat sources');
    const db = pg(), digest = fingerprint(config);
    await db`INSERT INTO experience_studies(project_id,experiment_id,config_hash,config) VALUES(${scope.projectId},${scope.experimentId},${digest},${db.json(config)}) ON CONFLICT DO NOTHING`;
    const existing = await study(scope);
    if (existing.config_hash !== digest) throw Error('Study configuration is frozen; register a new study version');
    return { projectId: scope.projectId, experimentId: scope.experimentId, configHash: digest, modelExecutionEnabled: config.modelExecution.enabled };
}
export async function acceptedSource(scope: ExperienceScope, analysisId: string): Promise<EnvelopeSource & { sourceVersions: Record<string, number>; binding: unknown }> {
    const db = pg();
    const [a] = await db`SELECT a.*,j.snapshot,j.snapshot_hash AS job_snapshot_hash FROM analyses a JOIN tasks t ON t.id=a.task_id LEFT JOIN analysis_jobs j ON j.id=a.job_id WHERE a.id=${analysisId} AND t.project_id=${scope.projectId}`;
    if (!a || a.result.schema_version !== 2 || !a.snapshot || a.snapshot_hash !== a.job_snapshot_hash) throw Error('A source-bound accepted v2 analysis is required');
    const groups = await db`SELECT id,event_ids FROM subtasks WHERE analysis_id=${analysisId} ORDER BY position`;
    const versions = a.result.source_versions as Record<string, number>;
    if (!versions || !Object.keys(versions).length) throw Error('Accepted source versions are unavailable');
    const current = await db`SELECT id,version FROM event_versions WHERE id=ANY(${Object.keys(versions)}::text[])`;
    if (current.length !== Object.keys(versions).length || current.some(r => Number(r.version) !== versions[r.id])) throw Error('Stale source versions cannot publish or retrieve experience');
    const turns = await db`SELECT source FROM turns WHERE turn_key=ANY(${a.snapshot.turns.map((t: { turn_key: string }) => t.turn_key)}::text[])`;
    const attempts = turns.flatMap(t => typeof t.source?.experience_attempt?.attemptId === 'string' ? [t.source.experience_attempt.attemptId] : []);
    const verifications = await db`SELECT id,payload FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='verification' AND payload->>'verdict'='pass' AND payload->>'attemptId'=ANY(${attempts}::text[])`;
    const config = studyConfigSchema.parse((await study(scope)).config);
    return { analysisId, taskId: a.task_id, snapshotHash: a.snapshot_hash, analysis: a.result, eventIds: Object.keys(versions),
        subtaskOwners: Object.fromEntries(groups.map(g => [g.id, g.event_ids])), publicDependencies: config.publicDependencyEventIds,
        verificationIds: verifications.map(v => v.id), publicVerifications: Object.fromEntries(verifications.map(v => [v.id, {workItemId: v.payload.workItemId, attemptId: v.payload.attemptId}])), analyzedTurns: a.snapshot.turns.map((t: { turn_key: string }) => t.turn_key),
        promptContext: a.snapshot.prompt_context || [], coverage: a.snapshot.coverage || { sourceComplete: false, excerpted: true }, sourceVersions: versions, binding: a.snapshot.subscription_binding };
}
async function verifyPublicSupport(scope: ExperienceScope, x: Experience) {
    if (x.admission !== 'publicly_supported') return;
    for (const id of x.publicVerificationIds) {
        const v = await scopedRecord(scope, 'verification', id);
        if (v.verdict !== 'pass' || v.visibility !== 'runtime_public' || !x.sourceWorkItemIds.includes(String(v.workItemId)) || !x.sourceAttemptIds.includes(String(v.attemptId))) throw Error('Public support must verify this work item and attempt');
    }
}
export async function publishEnvelope(scope: ExperienceScope, raw: unknown, extractionConfigurationHash: string) {
    const analysisId = (raw as { baseAnalysisId?: string })?.baseAnalysisId;
    if (!analysisId || !/^[a-f0-9]{64}$/.test(extractionConfigurationHash)) throw Error('Invalid experience extraction identity');
    const source = await acceptedSource(scope, analysisId), e = validateEnvelope(raw, source);
    const [invocation] = await pg()`SELECT * FROM experience_jobs WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND id=${e.analysisRevisionId} AND invocation_id=${e.annotationInvocationId}`;
    const fixture = invocation?.measurement_origin === 'fixture' && process.env.OBS_TESTING === '1';
    if (!invocation || !['running','completed'].includes(invocation.status) || invocation.analysis_id !== e.baseAnalysisId || invocation.configuration_hash !== extractionConfigurationHash ||
        (!fixture && (!invocation.model_invoked || !invocation.usage?.total_tokens)) || !invocation.artifacts['answer.json']) throw Error('Publication requires its retained source-bound Luna invocation and usage receipt');
    const actual = JSON.parse((await restoreRaw(invocation.artifacts['answer.json'])).toString('utf8'));
    if (fingerprint(actual) !== fingerprint(e)) throw Error('Publication differs from the retained model output');
    if (fingerprint(invocation.source_binding) !== fingerprint(source.binding)) throw Error('Extraction changed the canonical source subscription');
    for (const x of e.extensions.experiences) {
        const metadata = invocation.input?.metadata;
        if (metadata && ['sourceRepository','sourceBaseCommit','split','assistance','sourceArm','leakageGroups'].some(k => fingerprint(x[k as keyof typeof x]) !== fingerprint(metadata[k]))) throw Error('Publication changed registered source provenance');
        await verifyPublicSupport(scope, x);
    }
    const retained = await archive(scope, 'envelope', e.analysisRevisionId, e), db = pg();
    return db.begin(async tx => {
        await tx`SELECT pg_advisory_xact_lock(hashtext(${fingerprint([scope, e.sourceSnapshotHash, extractionConfigurationHash])}))`;
        const [old] = await tx`SELECT id,envelope FROM experience_analysis_revisions WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND source_snapshot_hash=${e.sourceSnapshotHash} AND extraction_configuration_hash=${extractionConfigurationHash}`;
        if (old) {
            if (fingerprint(old.envelope) !== fingerprint(e)) throw Error('Extraction identity already has a different retained result');
            return { id: old.id, status: 'retained' };
        }
        await tx`INSERT INTO experience_analysis_revisions(project_id,experiment_id,id,analysis_id,source_snapshot_hash,extraction_configuration_hash,source_versions,envelope,raw_archive_id) VALUES(${scope.projectId},${scope.experimentId},${e.analysisRevisionId},${analysisId},${e.sourceSnapshotHash},${extractionConfigurationHash},${tx.json(source.sourceVersions)},${tx.json(e)},${retained.id})`;
        for (const w of e.extensions.workItems) await tx`INSERT INTO work_item_extensions(project_id,experiment_id,id,revision_id,parent_id,source_task_id,payload) VALUES(${scope.projectId},${scope.experimentId},${w.workItemId},${e.analysisRevisionId},${w.parentWorkItemId},${w.sourceTaskId},${tx.json(w)})`;
        for (const s of e.extensions.supportLinks) await tx`INSERT INTO event_support_links(project_id,experiment_id,id,revision_id,target_id,source_event_id,payload) VALUES(${scope.projectId},${scope.experimentId},${s.supportLinkId},${e.analysisRevisionId},${s.targetWorkItemId},${s.sourceEventId},${tx.json(s)})`;
        for (const [i, p] of e.extensions.outcomePredictions.entries()) await tx`INSERT INTO outcome_predictions(project_id,experiment_id,id,work_item_id,revision_id,label,payload) VALUES(${scope.projectId},${scope.experimentId},${e.analysisRevisionId + ':' + i},${p.workItemId},${e.analysisRevisionId},${p.label},${tx.json(p)})`;
        for (const x of e.extensions.experiences) {
            const id = versionId(x.experienceId, x.version), search = [x.goalSummary, x.abstractIntent, ...x.procedure, ...x.preconditions, ...x.failureConditions].join(' ');
            await tx`INSERT INTO experience_versions(project_id,experiment_id,version_id,experience_id,version,revision_id,granularity,admission,first_available_sequence,source_visibility,payload,search_vector) VALUES(${scope.projectId},${scope.experimentId},${id},${x.experienceId},${x.version},${e.analysisRevisionId},${x.granularity},${x.admission},${x.firstAvailableSequence},'runtime_public',${tx.json(x)},to_tsvector('simple',${search}))`;
            for (const workItem of x.sourceWorkItemIds) await tx`INSERT INTO experience_source_links(project_id,experiment_id,version_id,work_item_id) VALUES(${scope.projectId},${scope.experimentId},${id},${workItem})`;
            await enqueueFact(tx, scope, 'experience', id, { experienceId: x.experienceId, version: x.version, admission: x.admission, granularity: x.granularity });
        }
        return { id: e.analysisRevisionId, status: 'published', experienceVersionIds: e.extensions.experiences.map(x => versionId(x.experienceId, x.version)) };
    });
}
export async function createSnapshot(scope: ExperienceScope, input: { id: string; arm: string; watermark: number; versionIds: string[] }) {
    const s = studyConfigSchema.parse((await study(scope)).config), db = pg();
    if (!s.allowedArms.includes(input.arm) || !Number.isSafeInteger(input.watermark) || input.watermark < 0 || input.versionIds.length > s.maxSnapshotMembers || new Set(input.versionIds).size !== input.versionIds.length) throw Error('Invalid snapshot scope or members');
    const members = await db`SELECT version_id,first_available_sequence,admission,payload FROM experience_versions WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND version_id=ANY(${input.versionIds}::text[])`;
    if (members.length !== input.versionIds.length || members.some(x => Number(x.first_available_sequence) > input.watermark || !['candidate', 'publicly_supported'].includes(x.admission) || !s.allowedSplits.includes(x.payload.split) || (x.payload.sourceArm != null && x.payload.sourceArm !== input.arm))) throw Error('Snapshot includes ineligible, future or wrong-split experience');
    if (s.mode === 'online' && input.watermark > 0) {
        const [barrier] = await db`SELECT id FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='barrier' AND payload->>'arm'=${input.arm} AND (payload->>'sequence')::bigint>=${input.watermark} LIMIT 1`;
        if (!barrier) throw Error('Online snapshots require a terminal public publication barrier');
    }
    const manifest = { ...input, versionIds: input.versionIds.toSorted(), mode: s.mode }, digest = fingerprint(manifest);
    await archive(scope, 'snapshot', input.id, manifest);
    await db.begin(async tx => {
        await tx`SELECT pg_advisory_xact_lock(hashtext(${fingerprint([scope, input.id])}))`;
        await tx`INSERT INTO memory_snapshots(project_id,experiment_id,id,arm,watermark,manifest_hash,payload) VALUES(${scope.projectId},${scope.experimentId},${input.id},${input.arm},${input.watermark},${digest},${tx.json(manifest)}) ON CONFLICT DO NOTHING`;
        const [old] = await tx`SELECT manifest_hash FROM memory_snapshots WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND id=${input.id}`;
        if (old.manifest_hash !== digest) throw Error('Immutable snapshot identity conflict');
        for (const x of input.versionIds) await tx`INSERT INTO memory_snapshot_members(project_id,experiment_id,snapshot_id,version_id) VALUES(${scope.projectId},${scope.experimentId},${input.id},${x}) ON CONFLICT DO NOTHING`;
    });
    return { id: input.id, manifestHash: digest, members: input.versionIds.length };
}
export async function retireExperience(scope: ExperienceScope, version: string, reason: string, sequence: number) {
    if (!reason.trim() || !Number.isSafeInteger(sequence) || sequence < 0) throw Error('Invalid retirement');
    const [old] = await pg()`SELECT version_id FROM experience_versions WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND version_id=${version}`;
    if (!old) throw Error('Unknown scoped experience version');
    const [published] = await pg()`SELECT max(watermark) AS watermark FROM memory_snapshots WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId}`;
    if (published.watermark != null && sequence <= Number(published.watermark)) throw Error('Retirement cannot change an already published snapshot watermark');
    return appendRecord(scope, 'retirement', fingerprint([version, sequence]), { versionId: version, reason, sequence });
}
