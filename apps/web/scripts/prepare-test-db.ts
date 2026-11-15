import { readFile, writeFile } from 'node:fs/promises';
import postgres from 'postgres';
const file = new URL('../.env.local', import.meta.url), raw = await readFile(file, 'utf8'), values = Object.fromEntries(raw.split('\n').filter(l => l.includes('=')).map(l => { const p = l.indexOf('='); return [l.slice(0, p), l.slice(p + 1).replace(/^['"]|['"]$/g, '')]; }));
const db = postgres(values.DATABASE_URL, { max: 1 });
try {
    const existing = await db `SELECT 1 FROM pg_database WHERE datname='observatory_test'`;
    if (!existing.length)
        await db.unsafe('CREATE DATABASE observatory_test');
}
finally {
    await db.end();
}
const url = new URL(values.DATABASE_URL);
url.pathname = '/observatory_test';
await writeFile(new URL('../.env.test.local', import.meta.url), raw.replace(/^DATABASE_URL=.*$/m, 'DATABASE_URL=' + url) + '\nCLICKHOUSE_DATABASE=observatory_test\nOBS_TESTING=1\nNEXT_TELEMETRY_DISABLED=1\nS3_ENDPOINT=http://127.0.0.1:13990\nS3_REGION=garage\nS3_BUCKET=observatory-raw-test\nS3_ACCESS_KEY_ID=GKTESTONLY\nS3_SECRET_ACCESS_KEY=test-only-not-a-real-secret\n', { mode: 0o600 });
console.log('Isolated test database prepared; credentials were not printed.');
