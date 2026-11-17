import { pg } from './database.ts';
import type { Row, Scope } from './types.ts';

type Archived = { table_name: string; record: Record<string, unknown>; import_id: string; row_number: string | number };
const parse = (value: unknown): Record<string, unknown> => {
    if (typeof value === 'string') {
        try { value = JSON.parse(value); } catch { return { unavailable: 'Invalid retained JSON', original: value }; }
    }
    return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
};

/** Read retained records, without turning analyst interpretations into measurements. */
export function historyRows(records: Archived[]) {
    const tables = (name: string) => records.filter(r => r.table_name === name);
    const proposals = new Map(tables('experiments').map(r => [String(r.record.id), r]));
    const evaluations = new Map(tables('experiment_evaluations').map(r => [String(r.record.id), r]));
    const source = (r: Archived) => ({ import_id: r.import_id, table: r.table_name, row: r.row_number });
    const title = (id: unknown) => parse(proposals.get(String(id))?.record.proposal).title || 'Unknown proposal';
    const result: Record<string, Row[]> = {
        experiments: tables('experiments').map(r => {
            const p = parse(r.record.proposal), measured = [...evaluations.values()].filter(e => e.record.experiment_id === r.record.id);
            return { id: String(r.record.id), task_id: r.record.task_id, title: title(r.record.id),
                change: typeof p.change === 'string' && p.change.length > 240 ? p.change.slice(0, 237) + '…' : p.change,
                state: measured.length ? 'evaluated' : 'proposed', evaluations: measured.length,
                decision: p.decision ?? 'unrecorded', implementation: p.implementation ?? 'unrecorded',
                created: r.record.created, baseline_sha256: r.record.baseline_sha256, proposal: p, source: source(r) };
        }),
        'experiment-evaluations': tables('experiment_evaluations').map(r => {
            const protocol = parse(r.record.protocol), measurements = parse(r.record.measurements);
            return { id: String(r.record.id), experiment_id: r.record.experiment_id, title: title(r.record.experiment_id),
                protocol: protocol.id ?? 'Unknown protocol', acceptance: measurements.acceptance_passed ?? null,
                created: r.record.created, artifact_sha256: r.record.artifact_sha256,
                measurements, registered_protocol: protocol, source: source(r) };
        }),
        'experiment-reviews': tables('experiment_reviews').map(r => ({ id: String(r.record.id),
            evaluation_id: r.record.evaluation_id, title: title(evaluations.get(String(r.record.evaluation_id))?.record.experiment_id),
            verdict: r.record.verdict, notes: r.record.notes, created: r.record.created, source: source(r) })),
        'experiment-accounting': tables('experiment_accounting').map(r => ({ id: String(r.record.id),
            experiment_id: r.record.experiment_id, title: title(r.record.experiment_id), created: r.record.created,
            sha256: r.record.sha256, payload: parse(r.record.payload), source: source(r) })),
    };
    return result;
}

export async function experimentHistory(scope: Scope) {
    const since = scope.range === 'all' ? null : new Date(Date.now() - parseInt(scope.range) * 86400000).toISOString();
    const db = pg();
    // Re-imported snapshots retain their provenance but must not multiply results.
    const archived = await db<Archived[]>`SELECT DISTINCT ON (a.table_name,a.record->>'id')
        a.table_name,a.record-'baseline' AS record,a.import_id,a.row_number
        FROM archived_records a JOIN migration_manifests m ON m.id=a.import_id
        WHERE m.finished_at IS NOT NULL AND a.table_name IN
          ('experiments','experiment_evaluations','experiment_reviews','experiment_accounting')
        ORDER BY a.table_name,a.record->>'id',m.started_at DESC,m.id DESC`;
    const visible = await db`SELECT t.id FROM tasks t WHERE
        (${scope.project}='' OR t.project_id=${scope.project}) AND
        (${scope.task || ''}='' OR t.id=${scope.task || ''}) AND
        (${scope.workspace}='' OR EXISTS (SELECT 1 FROM assignments a JOIN turns n USING(turn_key)
          WHERE a.task_id=t.id AND n.workspace=${scope.workspace}))`;
    const taskIds = new Set(visible.map(r => String(r.id)));
    const allowed = new Set(archived.filter(r => r.table_name === 'experiments' && taskIds.has(String(r.record.task_id)) &&
        (!since || String(r.record.created) >= since)).map(r => String(r.record.id)));
    const evaluationIds = new Set(archived.filter(r => r.table_name === 'experiment_evaluations' && allowed.has(String(r.record.experiment_id))).map(r => String(r.record.id)));
    return historyRows(archived.filter(r => r.table_name === 'experiments' ? allowed.has(String(r.record.id)) :
        r.table_name === 'experiment_reviews' ? evaluationIds.has(String(r.record.evaluation_id)) : allowed.has(String(r.record.experiment_id))));
}
