import type postgres from 'postgres';
import { legacyProcessFields } from './legacy-process.ts';
import { hash } from './domain.ts';
export async function repairLegacyProcess(tx: postgres.TransactionSql, apply = false) {
    await tx`SELECT pg_advisory_xact_lock(846205219)`;
    const [analyses, groups, archived, versions] = await Promise.all([
        tx`SELECT id,result FROM analyses WHERE result ? 'legacy_import'`,
        tx`SELECT id,analysis_id,event_ids,result FROM subtasks WHERE result ? 'legacy_import'`,
        tx`SELECT import_id,row_number,record FROM archived_records WHERE table_name='task_process_results'`,
        tx`SELECT id,version FROM event_versions`,
    ]);
    const key = (a: unknown, s: unknown) => JSON.stringify([a, s]);
    const records = new Map(archived.map(r => [key(r.import_id, key(r.record.analysis_id, r.record.subtask_id)), r]));
    const members = new Map<string, string[]>();
    for (const group of groups) members.set(group.analysis_id, [...(members.get(group.analysis_id) || []), ...group.event_ids]);
    const versionMap = new Map(versions.map(r => [String(r.id), Number(r.version)]));
    const changes: { table: 'analyses' | 'subtasks'; id: string; before: any; after: any; origin: any }[] = [];
    let withoutResult = 0;
    for (const [table, rows] of [['analyses', analyses], ['subtasks', groups]] as const) {
        for (const row of rows) {
            if (row.result.schema_version === 2 || row.result.source_protocol === 'task-process-v1') continue;
            const analysisId = table === 'analyses' ? row.id : row.analysis_id;
            const source = records.get(key(row.result.legacy_import, key(analysisId, table === 'analyses' ? '' : row.id)));
            if (!source) { withoutResult++; continue; }
            const ids = table === 'analyses' ? members.get(analysisId) || [] : row.event_ids as string[];
            const fields = legacyProcessFields(source.record, ids);
            const after = { ...row.result, ...fields, ...(table === 'analyses' ? {
                schema_version: 1,
                ...(ids.every((id: string) => versionMap.has(id)) ? { source_versions: Object.fromEntries(ids.map((id: string) => [id, versionMap.get(id)])) } : {}),
            } : {}) };
            changes.push({ table, id: row.id, before: row.result, after, origin: { import_id: source.import_id, table: 'task_process_results', row_number: Number(source.row_number), sha256: hash(source.record) } });
        }
    }
    if (apply) for (const change of changes) {
        const changed = change.table === 'analyses'
            ? await tx`UPDATE analyses SET result=${tx.json(change.after)} WHERE id=${change.id} AND result=${tx.json(change.before)} RETURNING id`
            : await tx`UPDATE subtasks SET result=${tx.json(change.after)} WHERE id=${change.id} AND result=${tx.json(change.before)} RETURNING id`;
        if (changed.length !== 1) throw Error('Interpretation changed during repair; no partial repair committed');
        await tx`INSERT INTO audit(action,entity,details) VALUES('legacy_process_repaired',${change.id},${tx.json({ protocol: 'legacy-process-repair-001', table: change.table, before: change.before, after_sha256: hash(change.after), source: change.origin, new_model_calls: 0 })})`;
    }
    return { applied: apply, analyses: changes.filter(c => c.table === 'analyses').length, subtasks: changes.filter(c => c.table === 'subtasks').length, records_without_process_labels: withoutResult, plan_sha256: hash(changes.map(c => [c.table, c.id, c.after])), new_model_calls: 0 };
}
