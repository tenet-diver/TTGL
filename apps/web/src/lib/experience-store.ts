import type postgres from 'postgres';
import { pg, ch } from './database.ts';
import { retainRaw } from './raw-store.ts';
import { hash } from './domain.ts';
import { scopeSchema } from './experience-contract.ts';
export type ExperienceScope = { projectId: string; experimentId: string };
export type Tx = postgres.TransactionSql;
export function canonical(value: unknown): string {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([k, v]) => JSON.stringify(k) + ':' + canonical(v)).join(',') + '}';
    return JSON.stringify(value);
}
export const fingerprint = (value: unknown) => hash(canonical(value));
export const versionId = (id: string, version: number) => fingerprint([id, version]);
export async function study(scope: ExperienceScope) {
    scopeSchema.parse(scope);
    const [r] = await pg()`SELECT * FROM experience_studies WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId}`;
    if (!r) throw Error('Unknown experience study');
    return r;
}
export async function archive(scope: ExperienceScope, kind: string, id: string, payload: unknown) {
    return retainRaw(Buffer.from(canonical(payload)), 'experience-' + kind, ['experience', scope.projectId, scope.experimentId, kind, id].join('/'));
}
export async function appendRecord(scope: ExperienceScope, kind: string, id: string, payload: Record<string, unknown>) {
    await study(scope);
    const digest = fingerprint(payload), raw = await archive(scope, kind, id, payload);
    return pg().begin(async tx => {
        await tx`SELECT pg_advisory_xact_lock(hashtext(${canonical([scope, kind, id])}))`;
        const [previous] = await tx`SELECT * FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind=${kind} AND id=${id}`;
        if (previous) {
            if (previous.payload_hash !== digest) throw Error('Immutable receipt identity conflict');
            return { id, status: 'retained', payloadHash: digest };
        }
        await tx`INSERT INTO experience_records(project_id,experiment_id,kind,id,payload_hash,payload,raw_archive_id) VALUES(${scope.projectId},${scope.experimentId},${kind},${id},${digest},${tx.json(payload as postgres.JSONValue)},${raw.id})`;
        await enqueueFact(tx, scope, kind, id, payload);
        return { id, status: 'recorded', payloadHash: digest };
    });
}
export async function enqueueFact(tx: Tx, scope: ExperienceScope, kind: string, id: string, payload: unknown) {
    // Derived facts are an alternative representation, never additional native usage.
    await tx`INSERT INTO experience_analytics_outbox(id,project_id,experiment_id,kind,payload) VALUES(${fingerprint([scope, kind, id])},${scope.projectId},${scope.experimentId},${kind},${tx.json({ id, payload, usage_representation: 'derived_not_additive' } as postgres.JSONValue)}) ON CONFLICT DO NOTHING`;
}
export async function flushExperienceOutbox() {
    return pg().begin(async tx => {
        await tx`SELECT pg_advisory_xact_lock(846205230)`;
        const rows = await tx`SELECT * FROM experience_analytics_outbox WHERE delivered_at IS NULL ORDER BY version LIMIT 1000 FOR UPDATE SKIP LOCKED`;
        if (!rows.length) return 0;
        await ch().insert({ table: 'experience_facts', values: rows.map(r => ({ id: r.id, project_id: r.project_id, experiment_id: r.experiment_id, kind: r.kind,
            payload: canonical(r.payload), version: Number(r.version), recorded_at: new Date(r.created_at).toISOString() })), format: 'JSONEachRow' });
        for (const r of rows) await tx`UPDATE experience_analytics_outbox SET delivered_at=now() WHERE id=${r.id} AND version=${r.version}`;
        return rows.length;
    });
}
export async function scopedRecord(scope: ExperienceScope, kind: string, id: string) {
    const [r] = await pg()`SELECT payload FROM experience_records WHERE project_id=${scope.projectId} AND experiment_id=${scope.experimentId} AND kind=${kind} AND id=${id}`;
    if (!r) throw Error('Unknown scoped ' + kind + ' receipt');
    return r.payload as Record<string, unknown>;
}
