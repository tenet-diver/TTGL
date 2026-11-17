import { z } from 'zod';
import { pg } from './database.ts';
import { scopeSchema, checkpointSchema, routingSchema, reuseSchema, validatePlan, validateVerification } from './experience-contract.ts';
import { appendRecord, scopedRecord, study, fingerprint, type ExperienceScope } from './experience-store.ts';
import { studyConfigSchema } from './experience-publication.ts';
const id = z.string().min(1).max(512), ids = z.array(id).max(1000);
export const attemptSchema = z.strictObject({ attemptId: id, taskInstanceId: id, planNodeId: id, planRevisionId: id,
    checkpointId: id, executorId: id, arm: id, ordinal: z.number().int().min(0).max(1) });
export const attemptEventSchema = z.strictObject({
    attemptId: id, taskInstanceId: id, arm: id, status: z.enum(['accepted', 'public_failure', 'uncertain']), artifactId: id,
    verificationId: id.nullable(), integrationId: id.nullable(), trigger: z.string().min(1).max(200),
    artifactCheck: z.strictObject({ passed: z.boolean(), changed_paths: ids, invalid_paths: ids,
        repository_state_hash: z.string().regex(/^[a-f0-9]{64}$/), includes_adds_deletes_modes_and_links: z.literal(true) }),
    completionReport: z.strictObject({ summary: z.string().max(8000), changedArtifacts: ids, publicChecks: ids, unresolved: ids, usedExperienceIds: ids, escalate: z.boolean() }).nullable(),
    usageInvocationId: id,
});
export async function recordPlan(scope: ExperienceScope, raw: unknown) {
    const plan = validatePlan(raw);
    if (plan.previousRevisionId) {
        const previous = await scopedRecord(scope, 'plan', plan.previousRevisionId);
        if (previous.taskInstanceId !== plan.taskInstanceId) throw Error('Cross-task plan revision');
    }
    return appendRecord(scope, 'plan', plan.planRevisionId, plan);
}
export async function recordCheckpoint(scope: ExperienceScope, raw: unknown) {
    const cp = checkpointSchema.parse(raw);
    return appendRecord(scope, 'checkpoint', cp.checkpointId, cp);
}
export async function recordRouting(scope: ExperienceScope, raw: unknown) {
    const r = routingSchema.parse(raw), cp = await scopedRecord(scope, 'checkpoint', r.checkpointId);
    if (!r.candidateExecutorIds.includes(r.selectedExecutorId) || cp.taskInstanceId !== r.taskInstanceId || cp.planNodeId !== r.planNodeId ||
        Object.keys(r.predictedSuccess).some(k => !r.candidateExecutorIds.includes(k)) || Object.keys(r.predictedTotalCost).some(k => !r.candidateExecutorIds.includes(k))) throw Error('Routing decision conflicts with its checkpoint or model catalogue');
    const [snapshot] = await pg()`SELECT arm FROM memory_snapshots WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND id=${r.memorySnapshotId}`;
    if (!snapshot) throw Error('Unknown routing memory snapshot');
    return appendRecord(scope, 'routing', r.decisionId, r);
}
export async function recordAttempt(scope: ExperienceScope, raw: unknown) {
    const a = attemptSchema.parse(raw), cp = await scopedRecord(scope, 'checkpoint', a.checkpointId), plan = await scopedRecord(scope, 'plan', a.planRevisionId);
    const config = studyConfigSchema.parse((await study(scope)).config);
    if (!config.allowedArms.includes(a.arm) || cp.taskInstanceId !== a.taskInstanceId || cp.planNodeId !== a.planNodeId || plan.taskInstanceId !== a.taskInstanceId || !(plan.nodes as Array<{ nodeId: string }>).some(n => n.nodeId === a.planNodeId)) throw Error('Attempt crosses task, plan or checkpoint scope');
    const previous = await pg()`SELECT id,payload FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='attempt' AND payload->>'taskInstanceId'=${a.taskInstanceId} AND payload->>'planNodeId'=${a.planNodeId} AND payload->>'arm'=${a.arm} ORDER BY created_at`;
    if (previous.some(p => p.id !== a.attemptId && Number(p.payload.ordinal) === a.ordinal)) throw Error('Attempt ordinal is already owned');
    if (a.ordinal === 1) {
        const initial = previous.find(p => p.payload.ordinal === 0);
        const terminal = initial && await pg()`SELECT payload FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='attempt-event' AND payload->>'attemptId'=${initial.id}`;
        if (!initial || !terminal?.some(t => t.payload.status === 'public_failure') || terminal.some(t => t.payload.status === 'uncertain')) throw Error('Fallback requires a completed public failure, never an uncertain or started invocation');
    }
    return appendRecord(scope, 'attempt', a.attemptId, a);
}
export async function recordAttemptEvent(scope: ExperienceScope, raw: unknown) {
    const event = attemptEventSchema.parse(raw), a = await scopedRecord(scope, 'attempt', event.attemptId);
    if (event.taskInstanceId !== a.taskInstanceId || event.arm !== a.arm) throw Error('Cross-assignment attempt event');
    const prior = await pg()`SELECT payload_hash FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='attempt-event' AND payload->>'attemptId'=${event.attemptId}`;
    if (prior.some(p => p.payload_hash !== fingerprint(event))) throw Error('Terminal attempt event is immutable');
    if (event.status === 'accepted') {
        const artifact = await scopedRecord(scope, 'artifact-manifest', event.artifactId);
        if (artifact.kind !== 'candidate-source' || artifact.identity !== event.attemptId) throw Error('Accepted candidate source must be retained for this attempt');
        const local = await scopedRecord(scope, 'verification', event.verificationId || ''), integrated = await scopedRecord(scope, 'verification', event.integrationId || '');
        if (!event.artifactCheck.passed || local.verdict !== 'pass' || integrated.verdict !== 'pass' || integrated.scope !== 'integration' || local.attemptId !== event.attemptId || integrated.attemptId !== event.attemptId) throw Error('Acceptance requires matching local and integration verification');
    }
    return appendRecord(scope, 'attempt-event', fingerprint(event), event);
}
export async function recordVerification(scope: ExperienceScope, raw: unknown) {
    const v = validateVerification(raw), a = await scopedRecord(scope, 'attempt', v.attemptId), plan = await scopedRecord(scope, 'plan', String(a.planRevisionId));
    const node = (plan.nodes as Array<{ nodeId: string; acceptanceCriteria: Array<{ id: string }> }>).find(n => n.nodeId === a.planNodeId);
    const whole = v.scope === 'whole_task';
    const criteria = whole ? [...new Set((plan.nodes as Array<{ acceptanceCriteria: Array<{ id: string }> }>).flatMap(n => n.acceptanceCriteria.map(c => c.id)))] : node?.acceptanceCriteria.map(c => c.id) || [];
    if (!node || v.contractHash !== fingerprint(whole ? plan : node) || v.workItemId !== (whole ? plan.taskInstanceId : node.nodeId) || v.criterionResults.some(c => !criteria.includes(c.criterionId)) ||
        v.verdict === 'pass' && v.criterionResults.length !== criteria.length) throw Error('Verification must cover its frozen node or whole-task contract');
    for (const c of v.criterionResults) for (const artifact of c.evidenceArtifactRefs) {
        const retained = await scopedRecord(scope, 'artifact-manifest', artifact);
        if (retained.kind !== 'public-verification' || !String(retained.identity).startsWith(v.attemptId + ':')) throw Error('Verification evidence must be a retained check artifact for this attempt');
    }
    return appendRecord(scope, 'verification', v.verificationId, v);
}
export async function recordReuse(scope: ExperienceScope, raw: unknown) {
    const r = reuseSchema.parse(raw), a = await scopedRecord(scope, 'attempt', r.attemptId), integrated = await scopedRecord(scope, 'verification', r.integrationVerificationId);
    if (r.arm !== a.arm || r.executorId !== a.executorId || r.taskInstanceId !== a.taskInstanceId || integrated.attemptId !== r.attemptId || integrated.scope !== 'integration' ||
        (r.outcome === 'pass' && integrated.verdict !== 'pass') || (r.outcome === 'fail' && integrated.verdict !== 'fail')) throw Error('Reuse statistics require terminal public integration evidence');
    for (const v of r.publicVerificationIds) if ((await scopedRecord(scope, 'verification', v)).attemptId !== r.attemptId) throw Error('Cross-attempt reuse verification');
    for (const v of r.experienceVersionIds) {
        const [found] = await pg()`SELECT version_id FROM experience_versions WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND version_id=${v}`;
        if (!found) throw Error('Unknown scoped reused experience');
    }
    return appendRecord(scope, 'reuse', r.reuseId, r);
}
export async function recordBarrier(scope: ExperienceScope, raw: unknown) {
    const r = z.strictObject({ id, arm: id, taskInstanceId: id, sequence: z.number().int().nonnegative(), attemptIds: ids.min(1) }).parse(raw);
    const all = await pg()`SELECT id FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='attempt' AND payload->>'arm'=${r.arm} AND payload->>'taskInstanceId'=${r.taskInstanceId}`;
    if (all.length !== new Set(r.attemptIds).size || all.some(a => !r.attemptIds.includes(a.id))) throw Error('Barrier must cover every assignment attempt');
    for (const attempt of r.attemptIds) {
        const a = await scopedRecord(scope, 'attempt', attempt);
        const [done] = await pg()`SELECT payload FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='attempt-event' AND payload->>'attemptId'=${attempt}`;
        if (a.arm !== r.arm || a.taskInstanceId !== r.taskInstanceId || !done || done.payload.status === 'uncertain') throw Error('Publication barrier requires terminal public attempts in this arm');
    }
    return appendRecord(scope, 'barrier', r.id, r);
}
