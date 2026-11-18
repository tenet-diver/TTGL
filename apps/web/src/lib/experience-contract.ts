import { z } from 'zod';
import { validateAnalysis } from './analysis-contract.ts';

const id = z.string().min(1).max(512), digest = z.string().regex(/^[a-f0-9]{64}$/);
const text = z.string().min(1).max(8000), strings = z.array(z.string().min(1).max(2000)).max(100);
const ids = z.array(id).max(10000), sequence = z.number().int().nonnegative();
const object = z.strictObject;
export const scopeSchema = object({ projectId: id, experimentId: id });
export const coverageSchema = object({ suppliedEventCount: sequence, retainedEventCount: sequence.nullable(), sourceComplete: z.boolean(), excerpted: z.boolean(), missingRanges: strings });
export const workItemSchema = object({
    workItemId: id, sourceTaskId: id, sourceSubtaskId: id.nullable(), parentWorkItemId: id.nullable(),
    granularity: z.enum(['task', 'subtask']), goal: text, codingGoalTags: strings, operationTags: strings,
    languages: strings, frameworks: strings, relevantPaths: strings, relevantSymbols: strings,
    acceptanceCriteria: strings, primaryEventIds: ids, coverage: coverageSchema,
});
export const supportLinkSchema = object({
    supportLinkId: id, analysisRevisionId: id, sourceEventId: id, targetWorkItemId: id,
    relation: z.enum(['supports', 'tests', 'reads_for', 'dependency_context', 'recovery_context', 'contradicts']),
    evidenceScope: z.enum(['same_analysis', 'explicit_public_dependency']), annotationInvocationId: id, confidence: z.number().min(0).max(1),
});
export const outcomePredictionSchema = object({
    workItemId: id, attemptId: id.nullable(), label: z.enum(['successful', 'unsuccessful', 'abstain']), confidence: z.number().min(0).max(1),
    primaryEvidenceEventIds: ids, supportLinkIds: ids, publicVerificationIds: ids, asOfSequence: sequence,
    reason: text, failureCategories: strings, basedOn: z.literal('public_evidence'), annotationInvocationId: id,
});
export const experienceSchema = object({
    experienceId: id, version: z.number().int().positive(), granularity: z.enum(['task', 'subtask']),
    kind: z.enum(['procedure', 'worked_example', 'failure', 'recovery']), sourceWorkItemIds: ids.min(1), sourceTaskIds: ids.min(1), sourceArm: id.nullable(), sourceAttemptIds: ids, sourceAnalysisIds: ids.min(1),
    goalSummary: text, abstractIntent: text, procedure: strings.min(1), preconditions: strings, postconditions: strings,
    requiredTools: strings, languages: strings, frameworkConstraints: strings, repositoryScope: z.enum(['same_repository', 'similar_stack', 'general']),
    concreteExampleEventIds: ids, publicVerificationIds: ids, failureConditions: strings, sourceSnapshotHashes: z.array(digest).min(1).max(100),
    sourceVisibility: z.literal('runtime_public'), firstAvailableSequence: sequence,
    admission: z.enum(['candidate', 'publicly_supported', 'quarantined', 'superseded', 'retired']), extractionPromptVersion: id, embeddingVersion: id.nullable(),
    taxonomyVersion: z.literal('coding-taxonomy-v1'), assistance: z.enum(['autonomous', 'human_assisted', 'unknown']),
    leakageGroups: strings, sourceRepository: id, sourceBaseCommit: id, split: z.enum(['memory_build', 'router_development', 'mechanism_holdout', 'final_holdout', 'exact_repeat_diagnostic']),
});
export const envelopeSchema = object({
    envelopeVersion: z.literal(3), baseContractVersion: z.literal(2), baseAnalysisId: id, sourceSnapshotHash: digest,
    analysisRevisionId: id, annotationInvocationId: id, availableBeforeSequence: sequence,
    extensions: object({ workItems: z.array(workItemSchema).min(1).max(101), supportLinks: z.array(supportLinkSchema).max(1000),
        outcomePredictions: z.array(outcomePredictionSchema).max(101), experiences: z.array(experienceSchema).max(100) }),
});
const criterionSchema = object({ id, description: text, publicCheck: z.string().max(8000).nullable() });
export const planNodeSchema = object({
    nodeId: id, planRevisionId: id, parentWorkItemId: id, goal: text, dependsOn: ids.max(8), preconditions: strings,
    acceptanceCriteria: z.array(criterionSchema).min(1).max(100), relevantPaths: strings, relevantSymbols: strings, allowedWritePaths: strings.min(1),
    expectedArtifacts: strings, publicVerificationCommands: strings, estimatedDifficulty: z.enum(['routine', 'moderate', 'complex', 'unknown']),
    delegationSuitability: z.enum(['bounded', 'coupled', 'unknown']), supersedesNodeIds: ids.max(8),
});
export const planSchema = object({
    planRevisionId: id, taskInstanceId: id, previousRevisionId: id.nullable(), nodes: z.array(planNodeSchema).min(1).max(8),
    continuedNodeIds: ids, cancelledNodeIds: ids, contextHash: digest, plannerInvocationId: id,
});
export const verificationSchema = object({
    verificationId: id, workItemId: id, attemptId: id, scope: z.enum(['subtask', 'integration', 'whole_task']), visibility: z.literal('runtime_public'),
    verdict: z.enum(['pass', 'fail', 'partial', 'inconclusive', 'infrastructure_error']), contractHash: digest, verifierVersion: id, repositoryStateHash: digest,
    criterionResults: z.array(object({ criterionId: id, verdict: z.enum(['pass', 'fail', 'unknown']), evidenceArtifactRefs: ids.min(1) })).max(100),
    observedAt: z.string().datetime({ offset: true }),
});
export const querySchema = object({
    ...scopeSchema.shape, taskInstanceId: id, workItemId: id.nullable(), planRevisionId: id.nullable(), phase: z.enum(['user_task', 'plan_node', 'recovery', 'agent_requested']),
    goal: text, publicContextSummary: z.string().max(16000), languages: strings, frameworkConstraints: strings, relevantPaths: strings, relevantSymbols: strings,
    requiredTools: strings, acceptanceCriteria: strings, errorSignature: z.string().max(4000).nullable(), repositoryStateHash: digest,
    memorySnapshotId: id, availableBeforeSequence: sequence, retrievalPolicyVersion: id, arm: id,
    sourceRepository: id, sourceBaseCommit: id, excludedLeakageGroups: strings, excludedTaskIds: ids,
    mode: z.enum(['frozen_memory', 'online', 'exact_repeat_diagnostic']), retrievalMode: z.enum(['lexical', 'hybrid']),
});
export const routingSchema = object({
    decisionId: id, taskInstanceId: id, planNodeId: id, checkpointId: id, memorySnapshotId: id, policyVersion: id,
    predictionTarget: z.literal('public_integrated_completion'), selectedExecutorId: id, candidateExecutorIds: ids.min(1),
    predictedSuccess: z.record(z.string(), z.number().min(0).max(1).nullable()), predictedTotalCost: z.record(z.string(), z.number().nonnegative().nullable()),
    predictedLatencyMs: z.record(z.string(), z.number().nonnegative().nullable()), experienceVersionIds: ids, reasonCodes: strings,
    assignmentProbability: z.number().positive().max(1), exploration: z.boolean(), publicEvidenceIds: ids,
});
export const checkpointSchema = object({
    checkpointId: id, taskInstanceId: id, planNodeId: id, baseCommit: id, repositoryStateHash: digest,
    contractHash: digest, environmentDigest: id, sourceManifestHash: digest, artifactArchiveId: id,
    dependencyArtifactIds: ids, toolConfigurationHash: digest, visibleContextHash: digest,
});
export const reuseSchema = object({
    reuseId: id, attemptId: id, experienceVersionIds: ids, publicVerificationIds: ids.min(1), integrationVerificationId: id,
    outcome: z.enum(['pass', 'fail', 'inconclusive', 'infrastructure_error']), predictionTarget: z.literal('public_integrated_completion'),
    executorId: id, taskInstanceId: id, family: id, arm: id, terminalSequence: sequence,
    censoring: z.enum(['observed', 'incomplete', 'infrastructure', 'uncertain']), assignmentProbability: z.number().positive().max(1),
});
export const schemas = { envelope: envelopeSchema, experience: experienceSchema, query: querySchema, plan: planSchema,
    verification: verificationSchema, routing: routingSchema, checkpoint: checkpointSchema, reuse: reuseSchema };
export const jsonSchemas = Object.fromEntries(Object.entries(schemas).map(([name, schema]) => [name, z.toJSONSchema(schema)]));
export type Experience = z.infer<typeof experienceSchema>;
export type ExperienceQuery = z.infer<typeof querySchema>;
export type Envelope = z.infer<typeof envelopeSchema>;

export function validatePlan(raw: unknown) {
    const plan = planSchema.parse(raw), nodes = new Map(plan.nodes.map(n => [n.nodeId, n]));
    if (nodes.size !== plan.nodes.length) throw Error('Duplicate plan node');
    const visiting = new Set<string>(), seen = new Set<string>();
    const visit = (key: string) => {
        if (visiting.has(key)) throw Error('Plan dependency cycle');
        if (seen.has(key)) return;
        const node = nodes.get(key);
        if (!node || node.planRevisionId !== plan.planRevisionId) throw Error('Unknown plan dependency or revision');
        if (new Set(node.acceptanceCriteria.map(c => c.id)).size !== node.acceptanceCriteria.length) throw Error('Duplicate acceptance criterion');
        if (node.allowedWritePaths.some(p => p.startsWith('/') || p.split('/').includes('..') || p.startsWith('.git'))) throw Error('Invalid allowed write path');
        visiting.add(key); node.dependsOn.forEach(visit); visiting.delete(key); seen.add(key);
    };
    nodes.forEach((_, key) => visit(key));
    return plan;
}
export function validateVerification(raw: unknown) {
    const v = verificationSchema.parse(raw);
    if (v.verdict === 'pass' && (!v.criterionResults.length || v.criterionResults.some(c => c.verdict !== 'pass'))) throw Error('Passing verification requires nonempty passing criteria');
    if (new Set(v.criterionResults.map(c => c.criterionId)).size !== v.criterionResults.length) throw Error('Duplicate verification criterion');
    return v;
}
export interface EnvelopeSource {
    analysisId: string; taskId: string; snapshotHash: string; analysis: unknown; eventIds: string[];
    subtaskOwners: Record<string, string[]>; publicDependencies: string[]; verificationIds: string[];
    coverage?: { sourceComplete: boolean; excerpted: boolean };
    analyzedTurns?: string[]; promptContext?: Parameters<typeof validateAnalysis>[3];
    publicVerifications?: Record<string, { workItemId: string; attemptId: string }>;
}
export function validateEnvelope(raw: unknown, source: EnvelopeSource) {
    validateAnalysis(source.analysis, source.eventIds, source.analyzedTurns || [], source.promptContext || []);
    const e = envelopeSchema.parse(raw), items = new Map(e.extensions.workItems.map(w => [w.workItemId, w])), known = new Set(source.eventIds);
    if (e.baseAnalysisId !== source.analysisId || e.sourceSnapshotHash !== source.snapshotHash || items.size !== e.extensions.workItems.length) throw Error('Experience envelope source identity conflict');
    const primaryOwners = new Set<string>();
    for (const w of items.values()) {
        if (w.sourceTaskId !== source.taskId || w.primaryEventIds.some(id => !known.has(id)) || new Set(w.primaryEventIds).size !== w.primaryEventIds.length) throw Error('Invalid work-item source');
        if (w.granularity === 'subtask') {
            if (primaryOwners.has(w.sourceSubtaskId || '')) throw Error('Duplicate primary subtask ownership');
            primaryOwners.add(w.sourceSubtaskId || '');
            const owner = source.subtaskOwners[w.sourceSubtaskId || ''];
            if (!owner || owner.length !== w.primaryEventIds.length || owner.some(id => !w.primaryEventIds.includes(id))) throw Error('Primary ownership must preserve the accepted v2 subtask');
        } else if (w.sourceSubtaskId !== null) throw Error('Task aggregate cannot reassign a primary owner');
        if (w.parentWorkItemId && (!items.has(w.parentWorkItemId) || items.get(w.parentWorkItemId)!.granularity !== 'task' || w.granularity !== 'subtask')) throw Error('Invalid work-item containment');
        if (source.coverage && ((!source.coverage.sourceComplete && w.coverage.sourceComplete) || (source.coverage.excerpted && !w.coverage.excerpted))) throw Error('Work-item coverage exceeds the retained source coverage');
        if (w.coverage.suppliedEventCount !== w.primaryEventIds.length || (w.coverage.sourceComplete && (w.coverage.missingRanges.length > 0 || w.coverage.excerpted || w.coverage.retainedEventCount == null || w.coverage.retainedEventCount < w.primaryEventIds.length))) throw Error('Coverage claim conflicts with supplied evidence');
    }
    if (primaryOwners.size !== Object.keys(source.subtaskOwners).length) throw Error('Experience envelope must preserve every primary v2 owner');
    const links = new Map(e.extensions.supportLinks.map(s => [s.supportLinkId, s]));
    if (links.size !== e.extensions.supportLinks.length) throw Error('Duplicate support link');
    for (const link of links.values())
        if (link.analysisRevisionId !== e.analysisRevisionId || link.annotationInvocationId !== e.annotationInvocationId || !items.has(link.targetWorkItemId) || !(link.evidenceScope === 'same_analysis' ? known.has(link.sourceEventId) : source.publicDependencies.includes(link.sourceEventId))) throw Error('Support link crosses an unauthorized evidence boundary');
    const predicted = new Set<string>();
    for (const p of e.extensions.outcomePredictions) {
        const item = items.get(p.workItemId);
        if (!item || predicted.has(p.workItemId) || p.annotationInvocationId !== e.annotationInvocationId || p.asOfSequence > e.availableBeforeSequence || p.primaryEvidenceEventIds.some(id => !item.primaryEventIds.includes(id)) || p.supportLinkIds.some(id => links.get(id)?.targetWorkItemId !== p.workItemId) || p.publicVerificationIds.some(id => !source.verificationIds.includes(id))) throw Error('Invalid public outcome evidence');
        if (p.label !== 'abstain' && !p.primaryEvidenceEventIds.length && !p.supportLinkIds.length && !p.publicVerificationIds.length) throw Error('Unsupported outcome requires abstention');
        if (source.publicVerifications && p.publicVerificationIds.some(id => {
            const proof = source.publicVerifications![id];
            return !proof || proof.workItemId !== p.workItemId || proof.attemptId !== p.attemptId;
        })) throw Error('Public outcome verification must belong to this work item and attempt');
        predicted.add(p.workItemId);
    }
    if (predicted.size !== items.size) throw Error('Every work item requires an outcome interpretation or abstention');
    const versions = new Set<string>();
    for (const x of e.extensions.experiences) {
        const key = x.experienceId + ':' + x.version;
        if (versions.has(key) || x.sourceWorkItemIds.some(id => !items.has(id)) || x.sourceTaskIds.some(id => id !== source.taskId) || x.sourceAnalysisIds.some(id => id !== source.analysisId) || !x.sourceSnapshotHashes.includes(source.snapshotHash) || x.concreteExampleEventIds.some(id => !known.has(id)) || x.publicVerificationIds.some(id => !source.verificationIds.includes(id)) || x.firstAvailableSequence > e.availableBeforeSequence) throw Error('Invalid experience source or watermark');
        if (x.admission === 'publicly_supported' && (!x.publicVerificationIds.length || x.sourceWorkItemIds.some(id => !items.get(id)!.coverage.sourceComplete))) throw Error('Public support requires complete coverage and host verification');
        versions.add(key);
    }
    return e;
}
