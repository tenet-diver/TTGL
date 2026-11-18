/** Private native experiment spool -> existing verified local S3 archive. */
import { readFile } from 'node:fs/promises';
import { retainRaw, rawHealth, rawClient } from '../src/lib/raw-store.ts';
import { pg } from '../src/lib/database.ts';

try {
    const [file, identity] = process.argv.slice(2);
    if (!file || !identity) throw Error('A private evidence file and immutable identity are required');
    await rawHealth();
    const receipt = await retainRaw(await readFile(file), 'observatory-experiment', identity);
    process.stdout.write(JSON.stringify(receipt) + '\n');
} finally {
    rawClient().destroy();
    await pg().end({ timeout: 5 });
}
