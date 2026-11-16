import { localGarageEndpoint } from './execution-policy.ts';
import { S3Client, HeadObjectCommand, PutObjectCommand, GetObjectCommand, HeadBucketCommand } from '@aws-sdk/client-s3';
import { createHash } from 'node:crypto';
import { pg } from './database.ts';
const sha = (bytes: Uint8Array) => createHash('sha256').update(bytes).digest('hex');
let client: S3Client | undefined, clientIdentity = '';
export function rawClient() {
    if (!process.env.S3_ENDPOINT || !process.env.S3_BUCKET || !process.env.S3_ACCESS_KEY_ID || !process.env.S3_SECRET_ACCESS_KEY)
        throw Error('Garage S3 endpoint, bucket and credentials are required for raw-log retention');
    const endpoint = localGarageEndpoint(process.env.S3_ENDPOINT), identity = JSON.stringify([endpoint, process.env.S3_REGION, process.env.S3_ACCESS_KEY_ID, process.env.S3_SECRET_ACCESS_KEY]);
    if (clientIdentity !== identity) {
        client?.destroy();
        client = undefined;
        clientIdentity = identity;
    }
    return client ??= new S3Client({ endpoint, region: process.env.S3_REGION || 'garage', forcePathStyle: true, followRegionRedirects: false, credentials: { accessKeyId: process.env.S3_ACCESS_KEY_ID, secretAccessKey: process.env.S3_SECRET_ACCESS_KEY }, maxAttempts: 3, requestChecksumCalculation: 'WHEN_REQUIRED', responseChecksumValidation: 'WHEN_REQUIRED' });
}
const bucket = () => process.env.S3_BUCKET!;
export async function rawHealth() { await rawClient().send(new HeadBucketCommand({ Bucket: bucket() })); return true; }
export async function readRaw(key: string, expected: string) {
    if (!/^raw\/v1\/(chunks|manifests)\/[a-f0-9]{2}\/[a-f0-9]{64}(\.json)?$/.test(key))
        throw Error('Invalid raw object key');
    const r = await rawClient().send(new GetObjectCommand({ Bucket: bucket(), Key: key }));
    if (!r.Body)
        throw Error('Raw object body missing');
    const bytes = Buffer.from(await r.Body.transformToByteArray());
    if (sha(bytes) !== expected)
        throw Error('Raw object checksum mismatch');
    return bytes;
}
async function retainObject(key: string, bytes: Buffer, contentType: string) {
    const digest = sha(bytes);
    try {
        const head = await rawClient().send(new HeadObjectCommand({ Bucket: bucket(), Key: key }));
        if (head.Metadata?.sha256 !== digest || head.ContentLength !== bytes.length)
            throw Error('Existing raw object metadata conflicts');
        await readRaw(key, digest);
        return;
    }
    catch (e) {
        if ((e as {
            $metadata?: {
                httpStatusCode: number;
            };
        }).$metadata?.httpStatusCode !== 404)
            throw e;
    }
    try {
        await rawClient().send(new PutObjectCommand({ Bucket: bucket(), Key: key, Body: bytes, ContentLength: bytes.length, ContentType: contentType, Metadata: { sha256: digest }, IfNoneMatch: '*' }));
    }
    catch (e) {
        if ((e as {
            $metadata?: {
                httpStatusCode: number;
            };
        }).$metadata?.httpStatusCode !== 412)
            throw e;
    }
    await readRaw(key, digest);
}
export function archivePlan(bytes: Buffer) {
    const chunks: {
        key: string;
        sha256: string;
        bytes: number;
    }[] = [];
    for (let offset = 0; offset < bytes.length; offset += 4 * 1024 * 1024) {
        const data = bytes.subarray(offset, offset + 4 * 1024 * 1024), digest = sha(data);
        chunks.push({ key: `raw/v1/chunks/${digest.slice(0, 2)}/${digest}`, sha256: digest, bytes: data.length });
    }
    const manifest = Buffer.from(JSON.stringify({ version: 1, sha256: sha(bytes), bytes: bytes.length, chunks }));
    const digest = sha(manifest);
    return { sha256: sha(bytes), chunks, manifest, key: `raw/v1/manifests/${digest.slice(0, 2)}/${digest}.json`, id: digest };
}
/** Exact source bytes are retained and verified BEFORE derived ingestion is allowed. */
export async function retainRaw(bytes: Buffer, provider: string, sourcePath: string) {
    const plan = archivePlan(bytes), db = pg(), id = sha(Buffer.from(JSON.stringify([provider, sourcePath, plan.id])));
    await db `INSERT INTO raw_archives(id,provider,source_path,content_sha256,bytes,manifest_key,chunks) VALUES(${id},${provider},${sourcePath},${plan.sha256},${bytes.length},${plan.key},${db.json(plan.chunks)}) ON CONFLICT DO NOTHING`;
    for (const [index, chunk] of plan.chunks.entries())
        await retainObject(chunk.key, bytes.subarray(index * 4 * 1024 * 1024, index * 4 * 1024 * 1024 + chunk.bytes), 'application/octet-stream');
    await retainObject(plan.key, plan.manifest, 'application/json');
    await db `UPDATE raw_archives SET status='retained',verified_at=now() WHERE id=${id}`;
    return { id, key: plan.key, sha256: plan.sha256, bytes: bytes.length };
}
export async function restoreRaw(id: string) {
    const [row] = await pg() `SELECT * FROM raw_archives WHERE id=${id} AND status='retained'`;
    if (!row)
        throw Error('Verified raw archive unavailable');
    const digest = row.manifest_key.split('/').at(-1)!.replace('.json', ''), manifest = JSON.parse((await readRaw(row.manifest_key, digest)).toString('utf8'));
    if (manifest.sha256 !== row.content_sha256 || manifest.bytes !== Number(row.bytes))
        throw Error('Raw archive manifest conflicts');
    const chunks = [];
    for (const item of manifest.chunks)
        chunks.push(await readRaw(item.key, item.sha256));
    const bytes = Buffer.concat(chunks);
    if (sha(bytes) !== row.content_sha256 || bytes.length !== Number(row.bytes))
        throw Error('Restored raw log does not reconcile');
    return bytes;
}
