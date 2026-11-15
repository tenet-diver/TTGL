import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { collect } from '../scripts/worker.ts';
import { pg, queryCh, closeDatabases } from '../src/lib/database.ts';
import { flushOutbox } from '../src/lib/ingest.ts';
import { restoreRaw } from '../src/lib/raw-store.ts';
if (process.env.OBS_TESTING !== '1' || !process.env.CLICKHOUSE_DATABASE?.endsWith('_test'))
    throw Error('Isolated test databases required');
after(closeDatabases);
test('collector archives exact bytes before derived ingestion and does not advance a failed source', async () => {
    const folder = await mkdtemp(path.join(tmpdir(), 'observatory-collect-')), file = path.join(folder, 'native.jsonl'), sid = 'collector-' + randomUUID(), db = pg(), saved = await db `SELECT * FROM settings WHERE key IN ('source_roots','collection_enabled')`;
    const records = [{ type: 'session_meta', payload: { id: sid, cwd: '/qa/collector', source: 'cli' } }, { type: 'token_usage_record', timestamp: '2026-11-15T10:00:00Z', payload: { turn_id: 't', response_id: 'r', usage: { input_tokens: 10, cached_input_tokens: 5, output_tokens: 2, total_tokens: 12 } } }];
    const bytes = Buffer.from(records.map(r => JSON.stringify(r)).join('\r\n') + '\r\n');
    try {
        await writeFile(file, bytes);
        await db `INSERT INTO settings(key,value) VALUES('source_roots',${db.json([{ path: folder, provider: 'codex' }])}),('collection_enabled','true') ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value`;
        await collect();
        while (await flushOutbox()) { }
        const before = (await db `SELECT * FROM source_files WHERE path=${file}`)[0];
        assert.ok(before.archive_id);
        assert.deepEqual(await restoreRaw(before.archive_id), bytes);
        assert.equal((await queryCh<{
            n: number;
        }>('SELECT count() AS n FROM events FINAL WHERE session_id={sid:String}', { sid }))[0].n, 1);
        await writeFile(file, Buffer.concat([bytes, Buffer.from('malformed\n')]));
        await collect();
        const after = (await db `SELECT * FROM source_files WHERE path=${file}`)[0];
        assert.equal(after.archive_id, before.archive_id);
        assert.equal(after.mtime_ms, before.mtime_ms);
        assert.match(after.error, /malformed/);
    }
    finally {
        await db `DELETE FROM settings WHERE key IN ('source_roots','collection_enabled')`;
        for (const r of saved)
            await db `INSERT INTO settings(key,value) VALUES(${r.key},${db.json(r.value)})`;
        await rm(folder, { recursive: true, force: true });
    }
});
