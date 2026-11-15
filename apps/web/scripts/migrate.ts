import { readFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { createClient } from '@clickhouse/client';
import { pg, closeDatabases } from '../src/lib/database.ts';
export async function migrate() {
    const chDatabase = process.env.CLICKHOUSE_DATABASE || 'observatory';
    if (!/^[a-z][a-z0-9_]{0,60}$/.test(chDatabase))
        throw Error('Invalid ClickHouse database identifier');
    const db = pg();
    await db `CREATE SCHEMA IF NOT EXISTS observatory`;
    await db `CREATE TABLE IF NOT EXISTS observatory.schema_migrations(version text PRIMARY KEY,sha256 text NOT NULL,applied_at timestamptz NOT NULL DEFAULT now())`;
    await db.begin(async (tx) => {
        await tx `SELECT pg_advisory_xact_lock(846205211)`;
        for (const file of (await readdir(new URL('../migrations/postgres/', import.meta.url))).filter(f => f.endsWith('.sql')).sort()) {
            const body = await readFile(new URL('../migrations/postgres/' + file, import.meta.url), 'utf8'), sha = createHash('sha256').update(body).digest('hex');
            const previous = await tx `SELECT sha256 FROM observatory.schema_migrations WHERE version=${file}`;
            if (previous.length) {
                if (previous[0].sha256 !== sha)
                    throw Error('Applied PostgreSQL migration changed: ' + file);
                continue;
            }
            await tx.unsafe(body);
            await tx `INSERT INTO observatory.schema_migrations(version,sha256) VALUES(${file},${sha})`;
        }
    });
    const bootstrap = createClient({ url: process.env.CLICKHOUSE_URL, username: process.env.CLICKHOUSE_USER || 'observatory', password: process.env.CLICKHOUSE_PASSWORD || '', database: 'default', clickhouse_settings: { date_time_input_format: 'best_effort' } });
    try {
        await bootstrap.command({ query: 'CREATE DATABASE IF NOT EXISTS ' + chDatabase });
        await bootstrap.command({ query: `CREATE TABLE IF NOT EXISTS ${chDatabase}.schema_migrations(version String, sha256 String, applied_at DateTime64(3,'UTC')) ENGINE=MergeTree ORDER BY version` });
        for (const file of (await readdir(new URL('../migrations/clickhouse/', import.meta.url))).filter(f => f.endsWith('.sql')).sort()) {
            const body = await readFile(new URL('../migrations/clickhouse/' + file, import.meta.url), 'utf8'), sha = createHash('sha256').update(body).digest('hex');
            const result = await bootstrap.query({ query: `SELECT sha256 FROM ${chDatabase}.schema_migrations WHERE version={version:String}`, query_params: { version: file }, format: 'JSONEachRow' }), previous = await result.json<{
                sha256: string;
            }>();
            if (previous.length) {
                if (previous.some(p => p.sha256 !== sha))
                    throw Error('Applied ClickHouse migration changed: ' + file);
                continue;
            }
            for (const statement of body.split(';').map(s => s.trim()).filter(Boolean))
                await bootstrap.command({ query: statement.replaceAll('observatory.', chDatabase + '.') });
            await bootstrap.insert({ table: chDatabase + '.schema_migrations', values: [{ version: file, sha256: sha, applied_at: new Date().toISOString() }], format: 'JSONEachRow' });
        }
    }
    finally {
        await bootstrap.close();
    }
    console.log('PostgreSQL and ClickHouse migrations verified.');
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    try {
        await migrate();
    }
    finally {
        await closeDatabases();
    }
}
