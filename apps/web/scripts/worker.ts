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
                const info = await stat(file), previous = (await pg() `SELECT bytes,mtime_ms FROM source_files WHERE path=${file}`)[0];
                if (previous && Number(previous.bytes) === info.size && Number(previous.mtime_ms) === Math.trunc(info.mtimeMs))
                    continue;
                if (info.size > 268435456)
                    throw Error('Source exceeds 256 MB; split or archive before ingestion');
                const bytes = await readFile(file), archive = await retainRaw(bytes, root.provider, file), text = bytes.toString('utf8'), parsed = parseNative(text, root.provider, file);
                if (parsed.malformed)
                    throw Error(`${parsed.malformed} malformed/oversized source lines; retained source unchanged`);
                for (let offset = 0; offset < parsed.events.length; offset += 1000) {
                    const result = await ingestEvents(parsed.events.slice(offset, offset + 1000));
                    if (result.conflicts)
                        throw Error(`${result.conflicts} native identity conflicts require reconciliation`);
                }
                for (const t of parsed.turns)
                    await pg() `INSERT INTO turns(turn_key,session_id,turn_id,workspace,prompt,started_at,finished_at,completed,role,agent_type,source) VALUES(${t.turn_key},${t.session_id},${t.turn_id},${t.workspace},${t.prompt},${t.started_at},${t.finished_at},${t.completed},${t.role},${t.agent_type},${pg().json(t.source)}) ON CONFLICT(turn_key) DO UPDATE SET prompt=EXCLUDED.prompt,started_at=EXCLUDED.started_at,finished_at=EXCLUDED.finished_at,completed=EXCLUDED.completed,source=EXCLUDED.source`;
                await pg() `INSERT INTO source_files(path,bytes,mtime_ms,sha256,archive_id) VALUES(${file},${info.size},${Math.trunc(info.mtimeMs)},${hash(bytes)},${archive.id}) ON CONFLICT(path) DO UPDATE SET bytes=EXCLUDED.bytes,mtime_ms=EXCLUDED.mtime_ms,sha256=EXCLUDED.sha256,archive_id=EXCLUDED.archive_id,error=NULL,imported_at=now()`;
            }
            catch (e) {
                await recordError(file, e);
            }
        }
    }
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
