/** S3 protocol fixture, NOT a Garage server or an end-to-end Garage compatibility claim. */
import { createServer } from 'node:http';
import { mkdir, readFile, writeFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
if (process.env.OBS_TESTING !== '1')
    throw Error('Test-only protocol fixture');
const root = path.resolve('work/observatory-s3-test');
await mkdir(root, { recursive: true });
const server = createServer(async (req, res) => {
    try {
        const key = decodeURIComponent(new URL(req.url!, 'http://localhost').pathname);
        if (key.includes('..')) {
            res.writeHead(400).end();
            return;
        }
        if (!req.headers.authorization?.startsWith('AWS4-HMAC-SHA256 ')) {
            res.writeHead(403).end();
            return;
        }
        if (!key.startsWith('/observatory-raw-test')) {
            res.writeHead(403).end();
            return;
        }
        if (key === '/observatory-raw-test/' || key === '/observatory-raw-test') {
            res.writeHead(200).end();
            return;
        }
        const file = path.join(root, createHash('sha256').update(key).digest('hex'));
        let bytes: Buffer | undefined;
        try {
            bytes = await readFile(file);
        }
        catch { }
        if (req.method === 'PUT') {
            if (bytes && req.headers['if-none-match'] === '*') {
                res.writeHead(412, { 'Content-Type': 'application/xml' }).end('<Error><Code>PreconditionFailed</Code></Error>');
                return;
            }
            const chunks = [];
            for await (const b of req)
                chunks.push(b);
            bytes = Buffer.concat(chunks);
            await writeFile(file, bytes, { mode: 0o600 });
            res.writeHead(200, { ETag: '"' + createHash('md5').update(bytes).digest('hex') + '"' }).end();
            return;
        }
        if (!bytes) {
            res.writeHead(404, { 'Content-Type': 'application/xml' }).end('<Error><Code>NoSuchKey</Code></Error>');
            return;
        }
        res.writeHead(200, { 'Content-Length': bytes.length, 'x-amz-meta-sha256': createHash('sha256').update(bytes).digest('hex'), 'Content-Type': 'application/octet-stream' });
        res.end(req.method === 'HEAD' ? undefined : bytes);
    }
    catch {
        res.writeHead(500).end();
    }
});
server.listen(13990, '127.0.0.1', () => console.log('TEST S3 protocol fixture on 13990; this is not Garage.'));
