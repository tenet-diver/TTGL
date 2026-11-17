import { retainRaw } from '../src/lib/raw-store.ts';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';
import { pg, closeDatabases } from '../src/lib/database.ts';
import { ingestEvents, flushOutbox } from '../src/lib/ingest.ts';
import { hash, iso, turnKey } from '../src/lib/domain.ts';
import { repairLegacyProcess } from '../src/lib/legacy-process-store.ts';
import { seedApiPricing } from '../src/lib/pricing.ts';
type R = Record<string, any>;
const ruleIds: Record<string, string> = { break: 'builtin-break', 'task-budget': 'builtin-task-budget', 'daily-budget': 'builtin-daily-budget', 'main-checkout': 'builtin-main-checkout', 'public-registry': 'builtin-public-registry', attribution: 'builtin-attribution', 'external-write': 'builtin-external-writes', 'shell-exploration': 'builtin-shell-exploration', context: 'builtin-context', 'failure-loop': 'builtin-failures', 'stop-check': 'builtin-checks' };
const ruleId = (id: string) => ruleIds[id] || id;
function ruleConfig(row: R) {
    const original = parsed(row.config), config = { ...original };
    if (row.builtin) {
        if (row.kind === 'break')
            config.minutes = Number(config.threshold || 3600) / 60;
        if (['task_budget', 'daily_budget'].includes(row.kind))
            config.amount = config.threshold;
        if (row.kind === 'context')
            config.tokens = config.threshold;
        if (row.kind === 'failure_loop')
            config.count = config.threshold;
        const checks: Record<string, string> = { 'main-checkout': 'main-checkout', 'public-registry': 'public-registry', attribution: 'claude-attribution', 'external-write': 'external-writes', 'shell-exploration': 'shell-exploration' };
        if (checks[row.id])
            config.check = checks[row.id];
    }
    return config;
}
const parsed = (value: any, fallback: any = {}) => {
    try {
        return typeof value === 'string' ? JSON.parse(value) : value ?? fallback;
    }
    catch {
        return fallback;
    }
};
export async function importLegacy(source: string) {
    const db = pg(), tables = new Map<string, R[]>(), counts: Record<string, number> = {}, rawLines: Buffer[] = [];
    let manifest: R = {};
    const child = spawn('python3', [fileURLToPath(new URL('./export-legacy.py', import.meta.url)), source], { stdio: ['ignore', 'pipe', 'pipe'] });
    let stderr = '';
    child.stderr.on('data', b => { stderr += b; });
    const exited = new Promise<void>((resolve, reject) => { child.on('error', reject); child.on('exit', code => code === 0 ? resolve() : reject(Error('Read-only legacy export failed: ' + stderr.slice(0, 2000)))); });
    for await (const line of createInterface({ input: child.stdout })) {
        rawLines.push(Buffer.from(line + '\n'));
        const item = JSON.parse(line);
        if (item.type === 'manifest')
            manifest = item;
        else {
            if (!tables.has(item.table))
                tables.set(item.table, []);
            tables.get(item.table)!.push(item.record);
            counts[item.table] = (counts[item.table] || 0) + 1;
        }
    }
    await exited;
    const archive = await retainRaw(Buffer.concat(rawLines), 'legacy-sqlite-export', source);
    const importId = 'legacy:' + hash([...tables]), already = (await db `SELECT finished_at FROM migration_manifests WHERE id=${importId}`)[0];
    if (already?.finished_at) {
        const process = await db.begin(async tx => { const repaired = await repairLegacyProcess(tx, true); await seedApiPricing(tx); return repaired; });
        return { id: importId, status: 'already_imported', counts, process };
    }
    await db.begin(async (tx) => {
        await tx `SELECT pg_advisory_xact_lock(846205215)`;
        await tx `INSERT INTO migration_manifests(id,source,manifest) VALUES(${importId},${source},${tx.json({ ...manifest, counts, policy: 'read-only export; archive all rows; active attempts never replay' })}) ON CONFLICT DO NOTHING`;
        for (const [table, rows] of tables)
            for (const [number, row] of rows.entries())
                await tx `INSERT INTO archived_records(import_id,table_name,row_number,record) VALUES(${importId},${table},${number},${tx.json(row)}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('projects') || [])
            await tx `INSERT INTO projects(id,name,repo,scope,created_at) VALUES(${r.id},${r.name || 'Imported project'},${r.repo || ''},${r.scope || ''},${iso(r.created) || new Date().toISOString()}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('tasks') || [])
            await tx `INSERT INTO tasks(id,project_id,title,goal,acceptance,status,outcome,source,created_at,updated_at) VALUES(${r.id},${r.project_id || null},${r.title || 'Imported task'},${r.goal || ''},${r.acceptance || ''},${r.status || 'active'},${r.outcome || null},${tx.json({ legacy_import: importId, original: r })},${iso(r.created) || new Date().toISOString()},${iso(r.updated) || new Date().toISOString()}) ON CONFLICT DO NOTHING`;
        const answers = new Map((tables.get('optimization_turns') || []).map(r => [turnKey(r.session_id, r.turn_id), r.answer_chars]));
        const sessions = new Map((tables.get('native_session_facts') || []).map(r => [r.session_id, r]));
        for (const r of tables.get('turns') || []) {
            const s = sessions.get(r.session_id) || {};
            await tx `INSERT INTO turns(turn_key,session_id,turn_id,workspace,prompt,started_at,finished_at,completed,role,agent_type,source) VALUES(${turnKey(r.session_id, r.turn_id)},${r.session_id},${r.turn_id},${r.repo || ''},${r.prompt || ''},${iso(r.start)},${iso(r.end)},${Boolean(r.completed)},${s.role || null},${s.agent_type || null},${tx.json({ legacy_import: importId, original: r, ...(answers.has(turnKey(r.session_id, r.turn_id)) ? { answer_chars: answers.get(turnKey(r.session_id, r.turn_id)) } : {}) })}) ON CONFLICT DO NOTHING`;
        }
        for (const r of tables.get('assignments') || [])
            await tx `INSERT INTO assignments(turn_key,task_id) VALUES(${turnKey(r.session_id, r.turn_id)},${r.task_id}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('settings') || []) {
            if (!['pricing', 'model_tiers'].includes(r.key))
                continue;
            const v = parsed(r.value);
            if (r.key === 'pricing' && (!v.models || v.unit !== 'USD'))
                continue;
            await tx `INSERT INTO settings(key,value) VALUES(${r.key},${tx.json(v)}) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value WHERE settings.value='{"unit":"USD","models":{}}'`;
        }
        for (const r of tables.get('task_evidence_notes') || [])
            await tx `INSERT INTO evidence_notes(id,task_id,kind,title,detail,reference,outcome,created_at,source) VALUES(${r.id},${r.task_id},${r.kind},${r.title},${r.detail || ''},${r.reference || ''},${r.outcome || 'unknown'},${iso(r.created) || new Date().toISOString()},${tx.json({ legacy_import: importId, original: r })}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('steering_state') || [])
            await tx `INSERT INTO steering_state(session_id,rule_id,value) VALUES(${r.session_id},${ruleId(r.rule_id)},${tx.json(parsed(r.value))}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('steering_events') || [])
            await tx `INSERT INTO steering_events(id,session_id,payload_hash,response,created_at) VALUES(${r.id},${r.session_id},${r.payload_hash},${tx.json(parsed(r.response))},${iso(r.received) || new Date().toISOString()}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('steering_rules') || [])
            await tx `INSERT INTO steering_rules(id,name,kind,mode,enabled,builtin,config,message) VALUES(${r.builtin ? ruleId(r.id) : r.id},${r.name},${r.kind},${r.mode},${Boolean(r.enabled)},${Boolean(r.builtin)},${tx.json(ruleConfig(r))},${r.message || ''}) ON CONFLICT(id) DO UPDATE SET mode=EXCLUDED.mode,enabled=EXCLUDED.enabled,config=EXCLUDED.config,message=EXCLUDED.message`;
        for (const r of tables.get('live_sessions') || [])
            await tx `INSERT INTO live_sessions(id,workspace,last_seen,status,paused,task_id,task_cost,context_tokens,state) VALUES(${r.id},${r.workspace || ''},${iso(r.last_seen) || new Date().toISOString()},${r.status || 'waiting'},${Boolean(r.paused)},${r.task_id || null},${r.task_cost ?? null},${r.context_tokens ?? null},${tx.json(r)}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('steering_notes') || [])
            await tx `INSERT INTO steering_notes(id,session_id,message,created_at,delivered_at) VALUES(${r.id},${r.session_id},${r.message},${iso(r.created) || new Date().toISOString()},${iso(r.delivered)}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('steering_log') || [])
            await tx `INSERT INTO steering_log(id,session_id,at,rule_id,rule_name,mode,message,call,workspace,event_id) VALUES(${r.id},${r.session_id},${iso(r.at) || new Date().toISOString()},${r.rule_id ? ruleId(r.rule_id) : null},${r.rule_name},${r.mode},${r.message},${r.call || ''},${r.workspace || ''},${r.event_id || null}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('applied_changes') || [])
            await tx `INSERT INTO applied_changes(id,title,applied_at,workspace,takes_effect,metrics,notes) VALUES(${r.id},${r.title},${iso(r.at) || new Date().toISOString()},${r.workspace || ''},${r.takes_effect === 'new_sessions' ? 'new_sessions' : 'immediate'},${parsed(r.metrics, [])},${r.notes || ''}) ON CONFLICT DO NOTHING`;
        for (const r of tables.get('task_history_jobs') || []) {
            const status = ['running', 'queued'].includes(r.status) ? 'legacy_' + r.status : r.status;
            await tx `INSERT INTO analysis_jobs(id,task_id,operation,status,model,snapshot_hash,snapshot,result,usage,error,source,created_at,finished_at) VALUES(${r.id},${r.task_id},${r.operation || 'overview'},${status},${r.model || 'Unknown'},${r.snapshot_hash || ''},${tx.json(parsed(r.snapshot))},${tx.json(parsed(r.result, null))},${tx.json(parsed(r.usage, null))},${r.error || null},${tx.json({ legacy_import: importId, original: r, automatic_retries: 0 })},${iso(r.created) || new Date().toISOString()},${iso(r.finished)}) ON CONFLICT(id) DO UPDATE SET status=EXCLUDED.status,result=EXCLUDED.result,usage=EXCLUDED.usage,error=EXCLUDED.error,source=EXCLUDED.source,finished_at=EXCLUDED.finished_at WHERE analysis_jobs.source ? 'legacy_import' AND analysis_jobs.status IN ('legacy_running','legacy_queued') AND EXCLUDED.status NOT IN ('legacy_running','legacy_queued')`;
        }
        const details = new Map((tables.get('task_analysis_details') || []).map(r => [r.analysis_id, r]));
        for (const r of tables.get('task_history_analyses') || []) {
            const d = details.get(r.id) || {};
            await tx `INSERT INTO analyses(id,task_id,job_id,snapshot_hash,summary,task_type,result,created_at) VALUES(${r.id},${r.task_id},${r.job_id},${r.snapshot_hash},${r.summary || ''},${d.task_type || 'unclassified'},${tx.json({ legacy_import: importId, knowledge: parsed(d.knowledge, []) })},${iso(r.created) || new Date().toISOString()}) ON CONFLICT DO NOTHING`;
        }
        const links = new Map<string, string[]>();
        for (const r of tables.get('task_history_steps') || []) {
            if (!links.has(r.subtask_id))
                links.set(r.subtask_id, []);
            links.get(r.subtask_id)!.push(r.event_id);
        }
        for (const r of tables.get('task_history_subtasks') || [])
            await tx `INSERT INTO subtasks(id,analysis_id,position,title,summary,category,confidence,event_ids,result) VALUES(${r.id},${r.analysis_id},${r.position},${r.title},${r.summary || ''},${r.activity || 'other'},${r.confidence ?? null},${links.get(r.id) || []},${tx.json({ legacy_import: importId, original: r })}) ON CONFLICT DO NOTHING`;
    });
    const oldAnalyses = new Map((tables.get('analyses') || []).map(r => [r.id, iso(r.created) || ''])), runtimeRoles = new Map<string, R>();
    for (const row of (tables.get('agent_annotations') || []).toSorted((a, b) => String(oldAnalyses.get(a.analysis_id) || '').localeCompare(String(oldAnalyses.get(b.analysis_id) || ''))))
        if (row.runtime_role)
            runtimeRoles.set(row.event_id, row);
    const facts = new Map((tables.get('optimization_facts') || []).map(r => [r.event_id, r])), sessions = new Map((tables.get('native_session_facts') || []).map(r => [r.session_id, r])), turns = new Map((tables.get('turns') || []).map(r => [turnKey(r.session_id, r.turn_id), r]));
    const events = (tables.get('events') || []).map(r => { const u = parsed(r.usage), f = facts.get(r.id) || {}, s = sessions.get(r.session_id) || {}, t = turns.get(turnKey(r.session_id, r.turn_id)); return { id: r.id, session_id: r.session_id, turn_id: r.turn_id, workspace: t?.repo || '', kind: r.kind, name: r.name || '', model: r.model || '', event_time: iso(r.ts), runtime: r.runtime ?? null, runtime_role: runtimeRoles.get(r.id)?.runtime_role || 'operation', failed: r.failed == null ? null : Number(r.failed), input_tokens: u.input_tokens ?? null, cached_tokens: u.cached_input_tokens ?? null, output_tokens: u.output_tokens ?? null, total_tokens: u.total_tokens ?? null, cache_write_tokens: f.cache_write ?? null, cache_5m_tokens: f.cache_5m ?? null, command: f.command || '', signature: f.signature || '', output_chars: f.output_chars ?? null, output_hash: r.output_hash || '', role: s.role || '', agent_type: s.agent_type || '', source_line: r.source_line || 0, payload: JSON.stringify({ legacy_import: importId, original: r }) }; });
    let conflicts = 0;
    for (let i = 0; i < events.length; i += 1000) {
        const result = await ingestEvents(events.slice(i, i + 1000));
        conflicts += result.conflicts;
    }
    while (await flushOutbox()) { }
    if (conflicts)
        throw Error(`${conflicts} native identity conflicts require reconciliation; archive retained, import not marked complete`);
    await db.begin(async tx => { await repairLegacyProcess(tx, true); await seedApiPricing(tx); await tx`UPDATE migration_manifests SET archive_id=${archive.id},finished_at=now() WHERE id=${importId}`; });
    return { id: importId, status: 'imported', counts, events: events.length };
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    try {
        if (!process.argv[2])
            throw Error('Usage: import-legacy.ts /absolute/path/workspace.db');
        console.log(await importLegacy(process.argv[2]));
    }
    finally {
        await closeDatabases();
    }
}
