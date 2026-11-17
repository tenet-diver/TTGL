/** Pure contract fixture, never a model result or automatically published seed. */
import type { EnvelopeSource } from './experience-contract.ts';
export function experienceFixture(prefix = 'fixture') {
    const source: EnvelopeSource = { analysisId: prefix + ':analysis', taskId: prefix + ':task', snapshotHash: 'a'.repeat(64),
        analysis: { schema_version: 2, summary: 'Synthetic procedure', task_type: 'bug_repair', outcome: 'unknown', outcome_reason: 'Fixture only', intervention: 'unknown', intervention_reason: '',
            subtasks: ['implement', 'verify'].map((category, i) => ({ title: category, summary: category, category, state: 'completed', outcome: 'done', outcome_reason: 'Synthetic public evidence',
                failure_reason: null, event_ids: [prefix + ':event' + i], evidence_event_ids: [prefix + ':event' + i], confidence: .5 })), prompt_relations: [], knowledge: [] },
        eventIds: [prefix + ':event0', prefix + ':event1'], subtaskOwners: { [prefix + ':sub0']: [prefix + ':event0'], [prefix + ':sub1']: [prefix + ':event1'] },
        publicDependencies: [], verificationIds: [], coverage: { sourceComplete: true, excerpted: false } };
    const coverage = (count: number) => ({ suppliedEventCount: count, retainedEventCount: count, sourceComplete: true, excerpted: false, missingRanges: [] });
    const items = [null, 0, 1].map(i => ({ workItemId: prefix + ':item' + i, sourceTaskId: source.taskId, sourceSubtaskId: i === null ? null : prefix + ':sub' + i,
        parentWorkItemId: i === null ? null : prefix + ':itemnull', granularity: i === null ? 'task' : 'subtask', goal: 'Repair cancellation propagation',
        codingGoalTags: ['bug_repair'], operationTags: ['async_lifecycle'], languages: ['TypeScript'], frameworks: [], relevantPaths: [], relevantSymbols: [],
        acceptanceCriteria: ['Cancellation reaches the worker'], primaryEventIds: i === null ? source.eventIds : [prefix + ':event' + i], coverage: coverage(i === null ? 2 : 1) }));
    const envelope = { envelopeVersion: 3, baseContractVersion: 2, baseAnalysisId: source.analysisId, sourceSnapshotHash: source.snapshotHash,
        analysisRevisionId: prefix + ':revision', annotationInvocationId: prefix + ':invocation', availableBeforeSequence: 0,
        extensions: { workItems: items, supportLinks: [{ supportLinkId: prefix + ':support', analysisRevisionId: prefix + ':revision', sourceEventId: prefix + ':event1',
            targetWorkItemId: prefix + ':item0', relation: 'tests', evidenceScope: 'same_analysis', annotationInvocationId: prefix + ':invocation', confidence: .5 }],
        outcomePredictions: items.map(w => ({ workItemId: w.workItemId, attemptId: null, label: 'abstain', confidence: .5,
            primaryEvidenceEventIds: [], supportLinkIds: [], publicVerificationIds: [], asOfSequence: 0, reason: 'Fixture interpretation only; no semantic success adjudication',
            failureCategories: [], basedOn: 'public_evidence', annotationInvocationId: prefix + ':invocation' })),
        experiences: [{ experienceId: prefix + ':procedure', version: 1, granularity: 'subtask', kind: 'procedure', sourceWorkItemIds: [prefix + ':item0'], sourceTaskIds: [source.taskId],
            sourceArm: null, sourceAttemptIds: [], sourceAnalysisIds: [source.analysisId], goalSummary: 'Propagate cancellation through an async worker', abstractIntent: 'Cancellation propagation',
            procedure: ['Inspect the public lifecycle contract', 'Propagate cancellation to the worker', 'Check cancellation before and after completion'],
            preconditions: ['An async worker exposes a cancellation contract'], postconditions: ['Public cancellation checks pass'], requiredTools: ['Bash'], languages: ['TypeScript'], frameworkConstraints: [],
            repositoryScope: 'same_repository', concreteExampleEventIds: [prefix + ':event0'], publicVerificationIds: [], failureConditions: ['Worker has no cancellation boundary'],
            sourceSnapshotHashes: [source.snapshotHash], sourceVisibility: 'runtime_public', firstAvailableSequence: 0, admission: 'candidate', extractionPromptVersion: 'experience-envelope-v3-001',
            embeddingVersion: null, taxonomyVersion: 'coding-taxonomy-v1', assistance: 'unknown', leakageGroups: [prefix + ':family'], sourceRepository: 'fixture/repository', sourceBaseCommit: 'fixture-base', split: 'memory_build' }] } };
    return { source, envelope };
}
