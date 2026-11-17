import { retainRasters } from '@/lib/raster';
import { sameOrigin } from '@/lib/request-guards';
import { rawHealth, retainRaw, restoreRaw } from '@/lib/raw-store';
import { NextRequest, NextResponse } from 'next/server';
import { pg, queryCh } from '@/lib/database';
import { scopeFrom, queryFrom } from '@/lib/domain';
import { recordData } from '@/lib/analytics';
import { performAction } from '@/lib/actions';
import { sourceEvent } from '@/lib/repository';
import { receiveHook, tokenMatches } from '@/lib/steering';
import { ingestEvents, flushOutbox } from '@/lib/ingest';
import { ZodError } from 'zod';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
const json = (v: unknown, status = 200) => NextResponse.json(v, { status, headers: { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } });
async function bodyBuffer(req: NextRequest) {
    if (Number(req.headers.get('content-length')) > 2097152)
        throw Error('Request exceeds 2 MB');
    const reader = req.body?.getReader();
    if (!reader)
        return Buffer.alloc(0);
    const parts: Uint8Array[] = [];
    let size = 0;
    while (true) {
        const { done, value } = await reader.read();
        if (done)
            break;
        size += value.length;
        if (size > 2097152) {
            await reader.cancel();
            throw Error('Request exceeds 2 MB');
        }
        parts.push(value);
    }
    return Buffer.concat(parts);
}
async function body(req: NextRequest) { return JSON.parse((await bodyBuffer(req)).toString('utf8')); }
export async function GET(req: NextRequest, { params }: {
    params: Promise<{
        route: string[];
    }>;
}) {
    const r = (await params).route;
    try {
        if (r[0] === 'health') {
            const checks = await Promise.allSettled([pg() `SELECT 1`, queryCh('SELECT 1'), rawHealth()]);
            return json({ postgres: checks[0].status === 'fulfilled', clickhouse: checks[1].status === 'fulfilled', raw_storage: checks[2].status === 'fulfilled', raw_storage_kind: 'local_s3' }, checks.every(c => c.status === 'fulfilled') ? 200 : 503);
        }
        if (r[0] === 'records' && r[1])
            return json(await recordData(r[1], scopeFrom(req.nextUrl.searchParams), queryFrom(req.nextUrl.searchParams), req.nextUrl.searchParams));
        if (r[0] === 'settings') {
            const rows = await pg() `SELECT key,value FROM settings WHERE key IN ('pricing','model_tiers','collection_enabled','source_roots')`;
            return json(Object.fromEntries(rows.map(row => [row.key, row.value])));
        }
        if (r[0] === 'events' && r[1])
            return json(await sourceEvent(r[1]));
        if (r[0] === 'raw' && r[1]) {
            const bytes = await restoreRaw(r[1]);
            return new NextResponse(new Uint8Array(bytes), { headers: { 'Content-Type': 'application/octet-stream', 'Content-Disposition': 'attachment; filename=raw-log.jsonl', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' } });
        }
        if (r[0] === 'images' && r[1]) {
            const [image] = await pg() `SELECT mime,bytes FROM retained_images WHERE id=${r[1]}`;
            if (!image)
                return json({ error: 'Image unavailable' }, 404);
            return new NextResponse(image.bytes, { headers: { 'Content-Type': image.mime, 'Cache-Control': 'private, max-age=300', 'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "default-src 'none'; sandbox" } });
        }
        return json({ error: 'Unknown endpoint' }, 404);
    }
    catch (error) {
        console.error('Observatory read failed', error instanceof Error ? error.message : 'Unknown error');
        return json({ error: error instanceof Error && /Invalid|Unknown|Narrow|unavailable/.test(error.message) ? error.message : 'Data could not be read. Check service health.' }, 400);
    }
}
export async function POST(req: NextRequest, { params }: {
    params: Promise<{
        route: string[];
    }>;
}) {
    const r = (await params).route;
    try {
        if (r[0] === 'ingest') {
            if (!tokenMatches(req.headers.get('authorization')))
                return json({ error: 'Authentication required' }, 401);
            const original = await bodyBuffer(req);
            if (original.length > 2097152)
                throw Error('Request exceeds 2 MB');
            const data = JSON.parse(original.toString('utf8'));
            if (!Array.isArray(data.events))
                return json({ error: 'events array required' }, 400);
            await retainRaw(Buffer.from(original), 'http-ingest', String(data.source || 'authenticated-ingest'));
            const result = await ingestEvents(data.events);
            if (result.conflicts)
                return json({ ...result, error: 'Native identity conflicts require reconciliation' }, 409);
            await retainRasters(data.events.map((e: Record<string, unknown>) => ({ ...e, payload: typeof e.payload === 'string' ? e.payload : JSON.stringify(e.payload || {}) })));
            await flushOutbox();
            return json(result);
        }
        if (r[0] === 'hooks') {
            if (!tokenMatches(req.headers.get('authorization')))
                return json({ error: 'Authentication required' }, 401);
            const original = await bodyBuffer(req);
            if (original.length > 2097152)
                throw Error('Request exceeds 2 MB');
            const input = JSON.parse(original.toString('utf8'));
            await retainRaw(original, 'agent-hook', String(input.session_id || 'unknown'));
            return json(await receiveHook(input));
        }
        const origin = req.headers.get('origin');
        if (!sameOrigin(origin, req.headers.get('host')))
            return json({ error: 'Same-origin request required' }, 403);
        if (r[0] === 'records' && r[1]) {
            const input = await body(req);
            if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).length > 40 || Object.values(input).some(value => typeof value !== 'string'))
                return json({ error: 'Invalid record parameters' }, 400);
            const search = new URLSearchParams(input);
            return json(await recordData(r[1], scopeFrom(search), queryFrom(search), search));
        }
        if (r[0] === 'actions')
            return json(await performAction(await body(req), req.headers.get('idempotency-key') || ''));
        return json({ error: 'Unknown endpoint' }, 404);
    }
    catch (error) {
        const message = error instanceof ZodError ? error.issues.map(i => i.path.join('.') + ': ' + i.message).join('; ') : error instanceof Error ? error.message : 'Invalid request';
        console.error('Observatory mutation failed', message);
        return json({ error: /password|postgres|SQL|syntax|connection|relation/i.test(message) ? 'Change could not be saved; check service health.' : message }, 400);
    }
}
