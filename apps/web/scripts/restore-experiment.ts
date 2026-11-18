/** Restore an already verified local raw archive to an operator-owned spool. */
import { writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { restoreRaw, rawClient } from '../src/lib/raw-store.ts';
import { pg } from '../src/lib/database.ts';

try {
    const [id, expected, destination] = process.argv.slice(2);
    if (!/^[a-f0-9]{64}$/.test(id || '') || !/^[a-f0-9]{64}$/.test(expected || '') || !destination)
        throw Error('Exact archive identity, digest and private destination required');
    const bytes = await restoreRaw(id), sha256 = createHash('sha256').update(bytes).digest('hex');
    if (sha256 !== expected) throw Error('Restored source archive differs');
    await writeFile(destination, bytes, { flag: 'wx', mode: 0o600 });
    process.stdout.write(JSON.stringify({ id, sha256, bytes: bytes.length }) + '\n');
} finally {
    rawClient().destroy();
    await pg().end({ timeout: 5 });
}
