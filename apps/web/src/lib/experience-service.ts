import { createHash } from 'node:crypto';
import { z } from 'zod';
import { pg } from './database.ts';
import { hash } from './domain.ts';
import { scopeSchema } from './experience-contract.ts';
import { experiencePrincipal, authorizeExperience } from './experience-auth.ts';
import { registerStudy, publishEnvelope, createSnapshot, retireExperience, studyConfigSchema } from './experience-publication.ts';
import { searchExperience, readExperience } from './experience-retrieval.ts';
import { recordPlan, recordCheckpoint, recordRouting, recordAttempt, recordAttemptEvent, recordVerification, recordReuse, recordBarrier } from './experience-routing.ts';
import { appendRecord, study, fingerprint, scopedRecord } from './experience-store.ts';
import { retainRaw, rawHealth, restoreRaw } from './raw-store.ts';
import { ingestExperienceTrace } from './experience-ingestion.ts';
import { queueExtraction } from './experience-extraction.ts';
const id = z.string().min(1).max(512), sha = z.string().regex(/^[a-f0-9]{64}$/);
export const serviceRequestSchema = z.strictObject({ apiVersion: z.literal(1), ...scopeSchema.shape, operation: id, payload: z.record(z.string(), z.unknown()) });
export async function experienceService(authorization: string | null, raw: unknown) {
    const request = serviceRequestSchema.parse(raw), scope = { projectId: request.projectId, experimentId: request.experimentId };
    const principal = experiencePrincipal(authorization);
    const payload = request.payload;
    authorizeExperience(principal, request.operation, scope, ['read', 'hybrid-search'].includes(request.operation) ? payload.query as Record<string, unknown> : payload);
    // Resolve ownership from retained identities; omitting arm/task in a payload
    // must never bypass a credential's assignment restriction.
    if (['verification','attempt-event','reuse'].includes(request.operation)) {
        const attempt = await scopedRecord(scope, 'attempt', String(payload.attemptId || ''));
        authorizeExperience(principal, request.operation, scope, attempt);
    }
    if (request.operation === 'routing') {
        const checkpoint = await scopedRecord(scope, 'checkpoint', String(payload.checkpointId || ''));
        const [snapshot] = await pg()`SELECT arm FROM memory_snapshots WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND id=${String(payload.memorySnapshotId || '')}`;
        authorizeExperience(principal, request.operation, scope, { ...checkpoint, arm: snapshot?.arm });
        if (principal.arm && !snapshot) throw Error('Experience access denied');
    }
    let result: unknown;
    switch (request.operation) {
        case 'register-study': result = await registerStudy(scope, payload); break;
        case 'publish': {
            const p = z.strictObject({ envelope: z.unknown(), extractionConfigurationHash: sha }).parse(payload);
            result = await publishEnvelope(scope, p.envelope, p.extractionConfigurationHash); break;
        }
        case 'search': result = await searchExperience(scope, payload); break;
        case 'hybrid-search': {
            const p = z.strictObject({ query: z.unknown(), vector: z.array(z.number().finite()).max(8192) }).parse(payload);
            result = await searchExperience(scope, p.query, p.vector); break;
        }
        case 'read': {
            const p = z.strictObject({ query: z.unknown(), versionIds: z.array(id).max(6) }).parse(payload);
            result = await readExperience(scope, p.query, p.versionIds); break;
        }
        case 'snapshot': result = await createSnapshot(scope, z.strictObject({ id, arm: id, watermark: z.number().int().nonnegative(), versionIds: z.array(id).max(10000) }).parse(payload)); break;
        case 'retire': {
            const p = z.strictObject({ versionId: id, reason: z.string().min(1).max(2000), sequence: z.number().int().nonnegative() }).parse(payload);
            result = await retireExperience(scope, p.versionId, p.reason, p.sequence); break;
        }
        case 'plan': result = await recordPlan(scope, payload); break;
        case 'checkpoint': result = await recordCheckpoint(scope, payload); break;
        case 'routing': result = await recordRouting(scope, payload); break;
        case 'attempt': result = await recordAttempt(scope, payload); break;
        case 'attempt-event': result = await recordAttemptEvent(scope, payload); break;
        case 'verification': result = await recordVerification(scope, payload); break;
        case 'reuse': result = await recordReuse(scope, payload); break;
        case 'barrier': result = await recordBarrier(scope, payload); break;
        case 'queue-extraction': result = await queueExtraction(scope, z.strictObject({ analysisId: id, promptVersion: id, metadata: z.record(z.string(), z.unknown()) }).parse(payload)); break;
        case 'artifact': {
            const p = z.strictObject({ identity: id, kind: id, base64: z.string().max(1000000).regex(/^[A-Za-z0-9+/]*={0,2}$/), sha256: sha }).parse(payload);
            await study(scope);
            const bytes = Buffer.from(p.base64, 'base64');
            if (bytes.toString('base64') !== p.base64 || hash(bytes) !== p.sha256) throw Error('Artifact bytes do not match the declared checksum');
            const retained = await retainRaw(bytes, 'experience-artifact-' + p.kind, [scope.projectId, scope.experimentId, p.identity].join('/'));
            result = { archiveId: retained.id, sha256: retained.sha256, bytes: retained.bytes }; break;
        }
        case 'artifact-manifest': {
            const p = z.strictObject({ artifactId: id, identity: id, kind: id, sha256: sha, bytes: z.number().int().nonnegative().max(268435456),
                chunks: z.array(z.strictObject({ archiveId: id, sha256: sha, bytes: z.number().int().positive().max(700000) })).max(1000) }).parse(payload);
            const checksum = createHash('sha256'); let total = 0;
            for (const c of p.chunks) {
                const [owner] = await pg()`SELECT source_path,provider FROM raw_archives WHERE id=${c.archiveId}`;
                if (!owner || !String(owner.provider).startsWith('experience-artifact-') || !String(owner.source_path).startsWith(scope.projectId + '/' + scope.experimentId + '/')) throw Error('Cross-project artifact chunk');
                const bytes = await restoreRaw(c.archiveId);
                if (hash(bytes) !== c.sha256 || bytes.length !== c.bytes) throw Error('Artifact chunk receipt conflicts');
                checksum.update(bytes); total += bytes.length;
            }
            if (total !== p.bytes || checksum.digest('hex') !== p.sha256) throw Error('Artifact manifest does not reconstruct exact bytes');
            result = await appendRecord(scope, 'artifact-manifest', p.artifactId, p); break;
        }
        case 'embedding': {
            const p = z.strictObject({ versionId: id, textKind: z.enum(['goal', 'procedure']), modelRevision: id, textVersion: id,
                vector: z.array(z.number().finite()).min(1).max(8192) }).parse(payload);
            const config = studyConfigSchema.parse((await study(scope)).config), pin = config.embedding;
            if (!pin || pin.modelRevision !== p.modelRevision || pin.textVersion !== p.textVersion || p.vector.length !== pin.dimensions || Math.abs(p.vector.reduce((s, n) => s + n * n, 0) - 1) > .001) throw Error('Embedding differs from the reviewed model and normalization pin');
            const db = pg(), digest = fingerprint(p);
            await db`INSERT INTO experience_embeddings(project_id,experiment_id,version_id,text_kind,model_revision,dimensions,normalization,text_version,vector_values,payload_hash) VALUES(${scope.projectId},${scope.experimentId},${p.versionId},${p.textKind},${p.modelRevision},${pin.dimensions},'l2',${p.textVersion},${p.vector},${digest}) ON CONFLICT DO NOTHING`;
            const [old] = await db`SELECT payload_hash FROM experience_embeddings WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND version_id=${p.versionId} AND text_kind=${p.textKind} AND model_revision=${p.modelRevision} AND text_version=${p.textVersion}`;
            if (old.payload_hash !== digest) throw Error('Immutable embedding identity conflict');
            result = { versionId: p.versionId, payloadHash: digest }; break;
        }
        case 'evaluation-summary': {
            const p = z.strictObject({ id, title: z.string().min(1).max(300), scope: z.string().min(1).max(1000), summary: z.string().min(1).max(8000), fixtureOnly: z.boolean(), independentReportHash: sha, aggregate: z.record(z.string(), z.unknown()) }).parse(payload);
            result = await appendRecord(scope, 'evaluation-summary', p.id, p); break;
        }
        case 'ingest-native': result = await ingestExperienceTrace(scope, payload); break;
        case 'job-status': {
            const p = z.strictObject({ jobId: id }).parse(payload);
            const [job] = await pg()`SELECT id,operation,status,analysis_id,usage,error,artifacts,invocation_id,model_invoked FROM experience_jobs WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND id=${p.jobId}`;
            if (!job) throw Error('Unknown scoped extraction job');
            result = job; break;
        }
        case 'accounting': {
            result = await pg()`SELECT id,operation,status,usage,invocation_id,model_invoked FROM experience_jobs WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} ORDER BY created_at`;
            break;
        }
        case 'readiness': {
            await rawHealth(); const s = await study(scope);
            const [vector] = await pg()`SELECT 1 AS ready FROM pg_extension WHERE extname='vector'`;
            result = { configHash: s.config_hash, localRawStorage: true, vectorAvailable: Boolean(vector), modelExecutionEnabled: s.config.modelExecution.enabled }; break;
        }
        default: throw Error('Unknown experience operation');
    }
    return { apiVersion: 1, result };
}
