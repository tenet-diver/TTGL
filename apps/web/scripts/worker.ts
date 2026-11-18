import { invalidate } from '../src/lib/repository.ts';
import { subscriptionBinding } from '../src/lib/execution-policy.ts';
import { retainRasters } from '../src/lib/raster.ts';
import { discoverTurn } from '../src/lib/discovery.ts';
import { retainRaw } from '../src/lib/raw-store.ts';
import { readdir, stat, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { pg, closeDatabases } from '../src/lib/database.ts';
import { ingestEvents, flushOutbox } from '../src/lib/ingest.ts';
import { parseNative } from '../src/lib/native-parser.ts';
import { runOneAnalysis } from '../src/lib/analysis-worker.ts';
import { hash } from '../src/lib/domain.ts';
async function recordError(source: string, error: unknown) { await pg() `INSERT INTO source_files(path,bytes,mtime_ms,error) VALUES(${source},0,0,${error instanceof Error ? error.message : 'Collection failed'}) ON CONFLICT(path) DO UPDATE SET error=EXCLUDED.error`; }
export async function collect() {
    const settings = await pg() `SELECT key,value FROM settings WHERE key IN ('source_roots','collection_enabled')`, values = Object.fromEntries(settings.map(r => [r.key, r.value]));
    if (!values.collection_enabled)
        return;
    for (const root of values.source_roots || []) {
        let binding: Awaited<ReturnType<typeof subscriptionBinding>> | undefined;
        const sessionsIndex = path.resolve(root.path).split(path.sep).lastIndexOf('sessions'), parts = path.resolve(root.path).split(path.sep);
        const sourceHome = root.codex_home || (root.provider === 'codex' && sessionsIndex > 0 ? parts.slice(0, sessionsIndex).join(path.sep) : root.provider === 'codex' && path.basename(root.path) === '.codex' ? path.resolve(root.path) : undefined);
        try {
            if (sourceHome) {
                binding = await subscriptionBinding(sourceHome);
                await pg() `UPDATE source_files SET error=NULL WHERE path=${root.path}`;
            } else { await recordError(root.path, new Error('Set the local Codex subscription home for this source folder in Data list to enable analysis')); }
        }
        catch (error) { await recordError(root.path, error); /* Retain logs while making the login problem visible. */ }
        const paths: string[] = [];
        async function walk(folder: string, depth = 0) {
            if (depth > 15)
                throw Error('Source tree exceeds 15 levels; choose narrower folders');
            for (const item of await readdir(folder, { withFileTypes: true })) {
                const file = path.join(folder, item.name);
                if (item.isSymbolicLink())
                    continue;
                if (item.isDirectory())
                    await walk(file, depth + 1);
                else if (item.isFile() && file.endsWith('.jsonl')) {
                    if (paths.length >= 10000)
                        throw Error('Source exceeds 10,000 JSONL files; choose narrower folders');
                    paths.push(file);
                }
            }
        }
        try {
            await walk(root.path);
        }
        catch (e) {
            await recordError(root.path, e);
            continue;
        }
        for (const file of paths) {
            try {
                const info = await stat(file), previous = (await pg() `SELECT bytes,mtime_ms,analysis_binding,sha256,archive_id,EXISTS(SELECT 1 FROM turns WHERE source->>'path'=${file} AND NOT (source ? 'analysis_binding')) AS needs_binding_repair FROM source_files WHERE path=${file}`)[0];
                if (previous?.analysis_binding && binding && JSON.stringify(previous.analysis_binding) !== JSON.stringify(binding) && previous.analysis_binding.account_hash !== binding.account_hash)
                    throw Error('Source subscription changed; existing source ownership was preserved');
                if (previous && (!binding || previous.analysis_binding) && Number(previous.bytes) === info.size && Number(previous.mtime_ms) === Math.trunc(info.mtimeMs)) {
                    if (binding && previous.needs_binding_repair && previous.archive_id && previous.sha256) {
                        const [retained] = await pg() `SELECT content_sha256 FROM raw_archives WHERE id=${previous.archive_id} AND status='retained'`;
                        const bytes = await readFile(file);
                        if (!retained || retained.content_sha256 !== previous.sha256 || hash(bytes) !== previous.sha256) throw Error('Source bytes changed; subscription reconciliation requires a verified retained source');
                        const parsed = parseNative(bytes.toString('utf8'), root.provider, file);
                        if (parsed.malformed) throw Error('Cannot reconcile subscription from malformed source');
                        await pg().begin(async tx => {
                            const keys = parsed.turns.map(t => t.turn_key);
                            const conflicts = await tx `SELECT turn_key FROM turns WHERE turn_key=ANY(${keys}::text[]) AND source->'analysis_binding' IS NOT NULL AND source->'analysis_binding'->>'account_hash'<>${binding.account_hash}`;
                            if (conflicts.length) throw Error('Source turns are already bound to another Codex subscription');
                            const updated = await tx `UPDATE turns SET source=jsonb_set(source,'{analysis_binding}',${tx.json(binding)}::jsonb) WHERE turn_key=ANY(${keys}::text[]) AND NOT (source ? 'analysis_binding') RETURNING turn_key`;
                            if (updated.length) await tx `INSERT INTO audit(action,entity,details) VALUES('subscription_binding_reconciled',${file},${tx.json({turns:updated.length,account_hash:binding.account_hash})})`;
                        });
                    }
                    continue;
                }
                if (info.size > 268435456)
                    throw Error('Source exceeds 256 MB; split or archive before ingestion');
                const bytes = await readFile(file), archive = await retainRaw(bytes, root.provider, file), text = bytes.toString('utf8'), parsed = parseNative(text, root.provider, file);
                if (parsed.malformed)
                    throw Error(`${parsed.malformed} malformed/oversized source lines; retained source unchanged`);
                if (binding) {
                    const conflicts = await pg() `SELECT turn_key FROM turns WHERE turn_key=ANY(${parsed.turns.map(t=>t.turn_key)}::text[]) AND source->'analysis_binding' IS NOT NULL AND source->'analysis_binding'->>'account_hash'<>${binding.account_hash}`;
                    if (conflicts.length) throw Error('Source turns are already bound to another Codex subscription');
                }
                for (let offset = 0; offset < parsed.events.length; offset += 1000) {
                    const result = await ingestEvents(parsed.events.slice(offset, offset + 1000));
                    if (result.conflicts)
                        throw Error(`${result.conflicts} native identity conflicts require reconciliation`);
                }
                for (const t of parsed.turns) {
                    if (binding || previous?.analysis_binding)
                        t.source.analysis_binding = binding || previous.analysis_binding;
                    await pg() `INSERT INTO turns(turn_key,session_id,turn_id,workspace,prompt,started_at,finished_at,completed,role,agent_type,source) VALUES(${t.turn_key},${t.session_id},${t.turn_id},${t.workspace},${t.prompt},${t.started_at},${t.finished_at},${t.completed},${t.role},${t.agent_type},${pg().json(t.source)}) ON CONFLICT(turn_key) DO UPDATE SET prompt=EXCLUDED.prompt,started_at=EXCLUDED.started_at,finished_at=EXCLUDED.finished_at,completed=EXCLUDED.completed,source=CASE WHEN EXCLUDED.source ? 'analysis_binding' THEN EXCLUDED.source ELSE EXCLUDED.source || CASE WHEN turns.source ? 'analysis_binding' THEN jsonb_build_object('analysis_binding',turns.source->'analysis_binding') ELSE '{}'::jsonb END END`;
                }
                for (const turn of parsed.turns)
                    await discoverTurn(turn.turn_key);
                await retainRasters(parsed.events as import('../src/lib/types.ts').NativeEvent[]);
                await pg() `INSERT INTO source_files(path,bytes,mtime_ms,sha256,archive_id,analysis_binding) VALUES(${file},${info.size},${Math.trunc(info.mtimeMs)},${hash(bytes)},${archive.id},${binding ? pg().json(binding) : null}) ON CONFLICT(path) DO UPDATE SET bytes=EXCLUDED.bytes,mtime_ms=EXCLUDED.mtime_ms,sha256=EXCLUDED.sha256,archive_id=EXCLUDED.archive_id,analysis_binding=coalesce(source_files.analysis_binding,EXCLUDED.analysis_binding),error=NULL,imported_at=now()`;
            }
            catch (e) {
                await recordError(file, e);
            }
        }
    }
    invalidate();
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    let stop = false;
    process.on('SIGINT', () => { stop = true; });
    process.on('SIGTERM', () => { stop = true; });
    try {
        do {
            await collect();
            while (await flushOutbox()) { }
            if (process.argv.includes('--analyze'))
                await runOneAnalysis();
            if (process.argv.includes('--once'))
                break;
            await new Promise(resolve => setTimeout(resolve, 5000));
        } while (!stop);
    }
    finally {
        await closeDatabases();
    }
}
