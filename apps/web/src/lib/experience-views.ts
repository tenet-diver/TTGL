import { pg } from './database.ts';
import type { Row, Column, Scope } from './types.ts';
const col = (key: string, label: string, type?: Column['type'], numeric = false): Column => ({ key, label, type, numeric });
export const experienceCollections = ['experience-studies', 'experience-versions', 'experience-predictions', 'experience-snapshots',
    'experience-plans', 'experience-routes', 'experience-attempts', 'experience-verifications', 'experience-retrievals', 'experience-results', 'experience-jobs'];
export async function experienceRows(kind: string, scope: Scope, extra: URLSearchParams): Promise<{ rows: Row[]; columns: Column[] }> {
    if (!experienceCollections.includes(kind)) throw Error('Unknown experience collection');
    const db = pg(), selected = extra.get('study') || '';
    const studies = await db`SELECT s.*,p.name AS project_name FROM experience_studies s JOIN projects p ON p.id=s.project_id
        WHERE (${scope.project}='' OR s.project_id=${scope.project}) AND (${selected}='' OR s.experiment_id=${selected})
        AND (${scope.workspace}='' OR p.repo=${scope.workspace}) ORDER BY s.created_at DESC`;
    const keys = studies.map(s => JSON.stringify([s.project_id, s.experiment_id]));
    const allowed = (r: Record<string, unknown>) => keys.includes(JSON.stringify([r.project_id, r.experiment_id]));
    let rows: Row[] = [], columns: Column[] = [];
    const shared = [col('project', 'Project'), col('study', 'Study')];
    const records = async (recordKind: string) => (await db`SELECT * FROM experience_records WHERE project_id=ANY(${studies.map(s => s.project_id)}::text[]) AND (${selected}='' OR experiment_id=${selected}) AND kind=${recordKind} ORDER BY created_at DESC LIMIT 10001`).filter(allowed);
    const fields = (r: Record<string, unknown>) => ({ project: studies.find(s => s.project_id === r.project_id)?.project_name || String(r.project_id), study: r.experiment_id });
    if (kind === 'experience-studies') {
        rows = studies.map(s => ({ id: JSON.stringify([s.project_id, s.experiment_id]), ...fields(s), mode: s.config.mode,
            policy: s.config.policyVersion, model_execution: s.config.modelExecution.enabled, config_hash: s.config_hash, config: s.config, created: s.created_at }));
        columns = [...shared, col('mode', 'Study mode'), col('policy', 'Policy'), col('model_execution', 'Model execution enabled'), col('created', 'Registered', 'date')];
    } else if (kind === 'experience-versions') {
        const values = (await db`SELECT * FROM experience_versions WHERE project_id=ANY(${studies.map(s => s.project_id)}::text[]) AND (${selected}='' OR experiment_id=${selected}) ORDER BY created_at DESC LIMIT 10001`).filter(allowed);
        rows = values.map(r => ({ id: r.version_id, ...fields(r), goal: r.payload.goalSummary, granularity: r.granularity, kind: r.payload.kind,
            admission: r.admission, version: r.version, first_available: Number(r.first_available_sequence), assistance: r.payload.assistance,
            languages: r.payload.languages.join(', '), source_task: r.payload.sourceTaskIds.join(', '), href: '/tasks/' + encodeURIComponent(r.payload.sourceTaskIds[0]),
            evidence: r.payload, source_revision: r.revision_id }));
        columns = [col('goal', 'Goal and source', 'link'), col('granularity', 'Granularity'), col('kind', 'Experience kind'), col('admission', 'Admission', 'badge'),
            col('version', 'Version', undefined, true), col('languages', 'Languages'), col('assistance', 'Assistance'), col('first_available', 'Publication sequence', undefined, true), ...shared];
    } else if (kind === 'experience-predictions') {
        const values = (await db`SELECT * FROM outcome_predictions WHERE project_id=ANY(${studies.map(s => s.project_id)}::text[]) AND (${selected}='' OR experiment_id=${selected}) ORDER BY id LIMIT 10001`).filter(allowed);
        rows = values.map(r => ({ id: r.id, ...fields(r), work_item: r.work_item_id, label: r.label, confidence: r.payload.confidence,
            reason: r.payload.reason, evidence: r.payload, interpretation: true }));
        columns = [col('work_item', 'Work item'), col('label', 'Interpreted outcome', 'badge'), col('confidence', 'Confidence', 'percent', true), col('reason', 'Public evidence and uncertainty'), ...shared];
    } else if (kind === 'experience-snapshots') {
        const values = (await db`SELECT * FROM memory_snapshots WHERE project_id=ANY(${studies.map(s => s.project_id)}::text[]) AND (${selected}='' OR experiment_id=${selected}) ORDER BY created_at DESC LIMIT 10001`).filter(allowed);
        rows = values.map(r => ({ id: r.id, ...fields(r), arm: r.arm, sequence: Number(r.watermark), members: r.payload.versionIds.length,
            manifest_hash: r.manifest_hash, manifest: r.payload, created: r.created_at }));
        columns = [col('id', 'Snapshot', 'code'), col('arm', 'Arm'), col('sequence', 'Watermark', undefined, true), col('members', 'Experience versions', undefined, true), col('created', 'Published', 'date'), ...shared];
    } else if (kind === 'experience-jobs') {
        const values = (await db`SELECT id,project_id,experiment_id,analysis_id,status,usage,error,artifacts,created_at FROM experience_jobs WHERE project_id=ANY(${studies.map(s => s.project_id)}::text[]) AND (${selected}='' OR experiment_id=${selected}) ORDER BY created_at DESC LIMIT 10001`).filter(allowed);
        rows = values.map(r => ({ id: r.id, ...fields(r), status: r.status, model: 'gpt-6-luna', tokens: r.usage?.total_tokens ?? null, error: r.error, artifacts: r.artifacts, created: r.created_at }));
        columns = [col('id', 'Extraction', 'code'), col('status', 'Status', 'badge'), col('model', 'Model'), col('tokens', 'Measured tokens', 'tokens', true), col('error', 'Failure or uncertainty'), col('created', 'Queued', 'date'), ...shared];
    } else {
        const sourceKind: Record<string, string> = { 'experience-plans': 'plan', 'experience-routes': 'routing', 'experience-attempts': 'attempt-event',
            'experience-verifications': 'verification', 'experience-retrievals': 'retrieval', 'experience-results': 'evaluation-summary' };
        const values = await records(sourceKind[kind]);
        rows = values.map(r => ({ id: r.id, ...fields(r), ...r.payload, retained_record: r.payload, created: r.created_at,
            candidates: r.payload.candidates?.length ?? null, selected: r.payload.packet?.experiences?.length ?? null,
            nodes: r.payload.nodes?.length ?? null, fixture: r.payload.fixtureOnly ?? false }));
        if (kind === 'experience-plans') columns = [col('taskInstanceId', 'Task'), col('planRevisionId', 'Plan revision', 'code'), col('nodes', 'Nodes', undefined, true), col('previousRevisionId', 'Previous revision'), ...shared];
        if (kind === 'experience-routes') columns = [col('taskInstanceId', 'Task'), col('planNodeId', 'Node'), col('selectedExecutorId', 'Executor'), col('reasonCodes', 'Reason'), col('predictionTarget', 'Prediction target'), ...shared];
        if (kind === 'experience-attempts') columns = [col('taskInstanceId', 'Task'), col('attemptId', 'Attempt', 'code'), col('status', 'Public result', 'badge'), col('trigger', 'Transition reason'), col('arm', 'Arm'), ...shared];
        if (kind === 'experience-verifications') columns = [col('workItemId', 'Work item'), col('attemptId', 'Attempt'), col('scope', 'Verification scope'), col('verdict', 'Verdict', 'badge'), col('observedAt', 'Observed', 'date'), ...shared];
        if (kind === 'experience-retrievals') columns = [col('queryHash', 'Query', 'code'), col('candidates', 'Ranked candidates', undefined, true), col('selected', 'Selected experiences', undefined, true), col('elapsedMs', 'Search milliseconds', undefined, true), col('applicability', 'Applicability assessment'), ...shared];
        if (kind === 'experience-results') columns = [col('title', 'Evaluation'), col('scope', 'Evidence scope'), col('fixture', 'Fixture only'), col('summary', 'Result and limitations'), col('created', 'Recorded', 'date'), ...shared];
    }
    if (rows.length > 10000) throw Error('Narrow the experience scope to at most 10,000 records');
    return { rows, columns };
}
