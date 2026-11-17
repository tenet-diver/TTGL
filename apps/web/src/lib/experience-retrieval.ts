import { pg } from './database.ts';
import { querySchema, type Experience, type ExperienceQuery } from './experience-contract.ts';
import { studyConfigSchema } from './experience-publication.ts';
import { study, fingerprint, appendRecord, type ExperienceScope } from './experience-store.ts';
export interface Candidate { versionId: string; experience: Experience; lexicalRank: number | null; vectorRank: number | null; score: number }
export function ineligible(x: Experience, q: ExperienceQuery, allowCandidates: boolean): string | null {
    if (x.sourceVisibility !== 'runtime_public') return 'private_visibility';
    if (!['publicly_supported', ...(allowCandidates ? ['candidate'] : [])].includes(x.admission)) return 'admission';
    if (x.firstAvailableSequence > q.availableBeforeSequence) return 'future';
    if (q.mode !== 'exact_repeat_diagnostic' && x.sourceTaskIds.some(id => q.excludedTaskIds.includes(id) || id === q.taskInstanceId)) return 'same_instance';
    if (x.leakageGroups.some(id => q.excludedLeakageGroups.includes(id))) return 'excluded_lineage';
    if (x.repositoryScope === 'same_repository' && x.sourceRepository !== q.sourceRepository) return 'repository';
    if (x.languages.length && q.languages.length && !x.languages.some(l => q.languages.includes(l))) return 'language';
    if (x.frameworkConstraints.some(f => !q.frameworkConstraints.includes(f))) return 'framework';
    if (x.requiredTools.some(t => !q.requiredTools.includes(t))) return 'tools';
    return null;
}
export function fuse(lexical: Array<{ versionId: string; experience: Experience }>, vector: Array<{ versionId: string; experience: Experience }>) {
    const all = new Map<string, Candidate>();
    for (const [kind, list] of [['lexicalRank', lexical], ['vectorRank', vector]] as const)
        list.forEach((x, index) => {
            const item = all.get(x.versionId) || { ...x, lexicalRank: null, vectorRank: null, score: 0 };
            item[kind] = index + 1; item.score += 1 / (60 + index + 1); all.set(x.versionId, item);
        });
    return [...all.values()].sort((a, b) => b.score - a.score || a.versionId.localeCompare(b.versionId));
}
export function packetFor(candidates: Candidate[], maxTokens: number) {
    const selected: Array<Record<string, unknown>> = [], seen = new Set<string>();
    let bytes = 2, parent = 0, subtask = 0, recovery = 0;
    for (const c of candidates) {
        const x = c.experience, key = x.granularity + ':' + x.sourceAnalysisIds.join(',') + ':' + x.abstractIntent;
        if (seen.has(key) || (['failure', 'recovery'].includes(x.kind) ? recovery >= 1 : x.granularity === 'task' ? parent >= 1 : subtask >= 3)) continue;
        const item = { versionId: c.versionId, experienceId: x.experienceId, version: x.version, admission: x.admission, granularity: x.granularity,
            kind: x.kind, goal: x.goalSummary, procedure: x.procedure, preconditions: x.preconditions, postconditions: x.postconditions,
            requiredTools: x.requiredTools, failureConditions: x.failureConditions, assistance: x.assistance,
            publicVerificationIds: x.publicVerificationIds, sourceWorkItemIds: x.sourceWorkItemIds };
        const size = Buffer.byteLength(JSON.stringify(item)) + 1;
        // UTF-8 bytes are a conservative upper bound on token count. Never report
        // this bound as measured model usage or silently truncate a precondition.
        if (bytes + size > maxTokens) continue;
        selected.push(item); seen.add(key); bytes += size;
        if (['failure', 'recovery'].includes(x.kind)) recovery++; else if (x.granularity === 'task') parent++; else subtask++;
    }
    return { experiences: selected, tokenUpperBound: bytes, tokenCountMethod: 'utf8-byte-upper-bound', budget: maxTokens };
}
async function eligible(scope: ExperienceScope, q: ExperienceQuery) {
    const config = studyConfigSchema.parse((await study(scope)).config), db = pg();
    if (!config.allowedArms.includes(q.arm) || q.mode !== config.mode || q.retrievalPolicyVersion !== config.policyVersion) throw Error('Query does not match the frozen study');
    const [snapshot] = await db`SELECT * FROM memory_snapshots WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND id=${q.memorySnapshotId}`;
    if (!snapshot || snapshot.arm !== q.arm || q.availableBeforeSequence > Number(snapshot.watermark)) throw Error('Wrong-arm snapshot or future publication watermark');
    const records = await db`SELECT v.version_id,v.payload,
        NOT EXISTS (SELECT 1 FROM jsonb_each_text(r.source_versions) AS s(id,version)
          LEFT JOIN event_versions e ON e.id=s.id WHERE e.version IS NULL OR e.version<>s.version::bigint) AS fresh,
        EXISTS (SELECT 1 FROM experience_records retired WHERE retired.project_id=v.project_id AND retired.experiment_id=v.experiment_id
          AND retired.kind='retirement' AND retired.payload->>'versionId'=v.version_id AND (retired.payload->>'sequence')::bigint<=${q.availableBeforeSequence}) AS retired
        FROM memory_snapshot_members m JOIN experience_versions v USING(project_id,experiment_id,version_id)
        JOIN experience_analysis_revisions r ON r.project_id=v.project_id AND r.experiment_id=v.experiment_id AND r.id=v.revision_id
        WHERE m.project_id=${scope.projectId} AND m.experiment_id=${scope.experimentId} AND m.snapshot_id=${q.memorySnapshotId}`;
    if (records.length !== snapshot.payload.versionIds.length) throw Error('Incomplete memory snapshot');
    const exclusions: Record<string, number> = {}, allowed: Array<{ versionId: string; experience: Experience }> = [];
    for (const r of records) {
        const x = r.payload as Experience;
        const excluded = x.sourceTaskIds.some(id => config.exclusions.taskIds.includes(id)) || x.leakageGroups.some(id => config.exclusions.leakageGroups.includes(id));
        const chronology = x.sourceRepository !== q.sourceRepository || x.sourceBaseCommit === q.sourceBaseCommit || config.repositoryCutoffs.some(c => c.repository === q.sourceRepository && c.sourceBaseCommit === x.sourceBaseCommit && c.targetBaseCommit === q.sourceBaseCommit);
        const reason = excluded ? 'registered_exclusion' : !chronology ? 'repository_chronology' : x.sourceArm != null && x.sourceArm !== q.arm ? 'wrong_arm_source' : !r.fresh ? 'stale_source' : r.retired ? 'retired' : !config.allowedSplits.includes(x.split) ? 'split' : ineligible(x, q, config.retrieval.allowCandidates);
        if (reason) exclusions[reason] = (exclusions[reason] || 0) + 1; else allowed.push({ versionId: r.version_id, experience: x });
    }
    return { config, allowed, exclusions, snapshotHash: snapshot.manifest_hash };
}
export async function searchExperience(scope: ExperienceScope, input: unknown, vector: number[] | null = null) {
    const q = querySchema.parse(input), started = performance.now();
    if (q.projectId !== scope.projectId || q.experimentId !== scope.experimentId) throw Error('Cross-project experience query');
    const { config, allowed, exclusions, snapshotHash } = await eligible(scope, q), db = pg();
    const queryText = [q.goal, q.publicContextSummary, ...q.relevantSymbols, ...q.relevantPaths, q.errorSignature || ''].join(' ');
    const lexicalQuery = [...new Set(queryText.match(/[\p{L}\p{N}_]+/gu) || [])].slice(0, 128).map(t => '"' + t + '"').join(' OR ');
    const lexical: Array<{ versionId: string; experience: Experience }> = [], vectors: typeof lexical = [];
    for (const granularity of ['task', 'subtask']) {
        const group = allowed.filter(c => c.experience.granularity === granularity), byId = new Map(group.map(c => [c.versionId, c]));
        if (!group.length) continue;
        const ranked = await db`SELECT version_id,ts_rank_cd(search_vector,websearch_to_tsquery('simple',${lexicalQuery})) AS score FROM experience_versions
          WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND version_id=ANY(${group.map(c => c.versionId)}::text[])
          AND search_vector @@ websearch_to_tsquery('simple',${lexicalQuery}) ORDER BY score DESC,version_id LIMIT ${config.retrieval.candidatesPerGranularity}`;
        lexical.push(...ranked.map(r => byId.get(r.version_id)!));
        if (q.retrievalMode === 'hybrid') {
            const pin = config.embedding;
            if (!pin || !vector || vector.length !== pin.dimensions || vector.some(v => !Number.isFinite(v)) || Math.abs(vector.reduce((s, n) => s + n * n, 0) - 1) > .001) throw Error('Hybrid retrieval requires the pinned normalized query embedding');
            const [installed] = await db`SELECT 1 AS ready FROM pg_extension WHERE extname='vector'`;
            if (!installed) throw Error('pgvector is unavailable; use a separately named lexical configuration');
            const queryVector = '[' + vector.join(',') + ']';
            const rankedVectors = await db.unsafe(`SELECT version_id,min(vector_values::vector <=> $1::vector) AS distance FROM observatory.experience_embeddings
              WHERE project_id=$2 AND experiment_id=$3 AND version_id=ANY($4::text[]) AND model_revision=$5 AND dimensions=$6 AND text_version=$7 AND normalization='l2'
              GROUP BY version_id ORDER BY distance,version_id LIMIT $8`, [queryVector, scope.projectId, scope.experimentId, group.map(c => c.versionId), pin.modelRevision, pin.dimensions, pin.textVersion, config.retrieval.candidatesPerGranularity]);
            vectors.push(...rankedVectors.map(r => byId.get(r.version_id)!));
        }
    }
    const candidates = fuse(lexical, vectors), packet = packetFor(candidates, q.phase === 'user_task' ? config.retrieval.taskPacketTokens : config.retrieval.subtaskPacketTokens);
    const queryHash = fingerprint(q), id = fingerprint([queryHash, snapshotHash, allowed.map(x => x.versionId).toSorted(), exclusions]);
    const [old] = await db`SELECT payload FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind='retrieval' AND id=${id}`;
    if (old) return { ...old.payload, cacheHit: true };
    const receipt = { id, query: q, queryHash, snapshotHash, exclusions, candidates: candidates.map(c => ({ versionId: c.versionId, lexicalRank: c.lexicalRank, vectorRank: c.vectorRank, score: c.score })),
        packet, elapsedMs: performance.now() - started, modelUsage: null, modelCalls: 0, cacheHit: false, applicability: 'not_requested' };
    await appendRecord(scope, 'retrieval', id, receipt);
    return receipt;
}
export async function readExperience(scope: ExperienceScope, query: unknown, versionIds: string[]) {
    const q = querySchema.parse(query);
    if (q.projectId !== scope.projectId || q.experimentId !== scope.experimentId || versionIds.length > 6) throw Error('Invalid scoped experience read');
    const { allowed, config } = await eligible(scope, q), requested = new Set(versionIds), rows = allowed.filter(c => requested.has(c.versionId));
    if (rows.length !== requested.size) throw Error('Experience is unavailable in the authorized snapshot');
    // The same bounded evidence contract applies to follow-up reads.
    return packetFor(rows.map(c => ({ ...c, score: 0, lexicalRank: null, vectorRank: null })), q.phase === 'user_task' ? config.retrieval.taskPacketTokens : config.retrieval.subtaskPacketTokens);
}
