import { discoverTurn } from './discovery.ts';
import { z } from 'zod';
import { pg, ch } from './database.ts';
import { hash, turnKey, iso } from './domain.ts';
import { invalidate } from './repository.ts';
import type { NativeEvent } from './types.ts';
const counter = z.number().int().nonnegative().nullable().default(null);
const eventSchema = z.object({ id: z.string().min(1).max(1000), session_id: z.string().min(1), turn_id: z.string().min(1), workspace: z.string().default(''), kind: z.enum(['generation', 'tool', 'compaction']), name: z.string().default(''), model: z.string().default(''), event_time: z.string().nullable().default(null), runtime: z.number().finite().nonnegative().nullable().default(null), runtime_role: z.string().default('operation'), failed: z.union([z.literal(0), z.literal(1)]).nullable().default(null), input_tokens: counter, cached_tokens: counter, output_tokens: counter, total_tokens: counter, cache_write_tokens: counter, cache_5m_tokens: counter, command: z.string().default(''), output_excerpt: z.string().default(''), output_chars: counter, output_hash: z.string().default(''), signature: z.string().default(''), role: z.string().default(''), agent_type: z.string().default(''), source_path: z.string().default(''), source_line: z.number().int().nonnegative().default(0), payload: z.string().default('{}') });
export function normalizeEvent(raw: unknown): Omit<NativeEvent, 'version'> {
    const e = eventSchema.parse(raw);
    if (e.cached_tokens != null && e.input_tokens != null && e.cached_tokens > e.input_tokens)
        throw Error('Cached tokens exceed native input');
    if (e.total_tokens != null && e.input_tokens != null && e.output_tokens != null && e.total_tokens !== e.input_tokens + e.output_tokens)
        throw Error('Native total does not match input and output');
    if (e.kind === 'generation' && e.input_tokens === 0 && e.output_tokens === 0 && e.total_tokens === 0) {
        e.input_tokens = null;
        e.cached_tokens = null;
        e.output_tokens = null;
        e.total_tokens = null;
    }
    const at = iso(e.event_time);
    if (e.event_time && !at)
        throw Error('Invalid event time');
    return { ...e, event_time: at || '1970-01-01T00:00:00.000Z', time_known: at ? 1 : 0, turn_key: turnKey(e.session_id, e.turn_id), output_excerpt: e.output_excerpt.slice(0, 64000), signature: e.signature || hash([e.name, e.command]) };
}
export async function ingestEvents(raw: unknown[]) {
    if (raw.length > 10000)
        throw Error('Ingest at most 10,000 events per batch');
    let inserted = 0, unchanged = 0, conflicts = 0;
    const discovered = new Set<string>();
    const normalized = raw.map(normalizeEvent);
    for (const e of normalized) {
        await pg().begin(async (tx) => {
            await tx `SELECT pg_advisory_xact_lock(hashtext(${e.id}))`;
            const digest = hash(e), routing = hash([e.workspace, e.session_id, e.turn_id, e.event_time]);
            const previous = (await tx `SELECT * FROM event_versions WHERE id=${e.id}`)[0];
            if (previous?.payload_hash === digest) {
                unchanged++;
                discovered.add(e.turn_key);
                return;
            }
            if (previous && previous.routing_key !== routing) {
                await tx `INSERT INTO ingest_conflicts(event_id,source_hash,reason) VALUES(${e.id},${digest},'Native identity routing or timestamp changed; retained original')`;
                conflicts++;
                return;
            }
            const usage = hash([e.input_tokens, e.cached_tokens, e.output_tokens, e.total_tokens]);
            if (previous?.usage_hash && previous.usage_hash !== usage) {
                const original = (await tx `SELECT payload FROM event_outbox WHERE event_id=${e.id}`)[0]?.payload;
                if (original && ['input_tokens', 'cached_tokens', 'output_tokens', 'total_tokens'].some(k => original[k] != null && original[k] !== e[k as keyof typeof e])) {
                    await tx `INSERT INTO ingest_conflicts(event_id,source_hash,reason) VALUES(${e.id},${digest},'Conflicting native usage counters; retained original')`;
                    conflicts++;
                    return;
                }
            }
            const [version] = await tx `INSERT INTO event_versions(id,payload_hash,usage_hash,event_time,routing_key) VALUES(${e.id},${digest},${usage},${e.event_time},${routing}) ON CONFLICT(id) DO UPDATE SET version=DEFAULT,payload_hash=EXCLUDED.payload_hash,usage_hash=EXCLUDED.usage_hash,updated_at=now() RETURNING version`;
            const event = { ...e, version: Number(version.version) };
            await tx `INSERT INTO turns(turn_key,session_id,turn_id,workspace,started_at) VALUES(${e.turn_key},${e.session_id},${e.turn_id},${e.workspace},${e.time_known ? e.event_time : null}) ON CONFLICT(turn_key) DO UPDATE SET started_at=least(turns.started_at,EXCLUDED.started_at)`;
            await tx `INSERT INTO event_outbox(event_id,version,payload) VALUES(${e.id},${event.version},${tx.json(event)}) ON CONFLICT(event_id) DO UPDATE SET version=EXCLUDED.version,payload=EXCLUDED.payload,delivered_at=NULL`;
            inserted++;
            discovered.add(e.turn_key);
        });
    }
    for (const key of discovered)
        await discoverTurn(key);
    invalidate();
    return { inserted, unchanged, conflicts };
}
export async function flushOutbox() {
    return pg().begin(async (tx) => {
        await tx `SELECT pg_advisory_xact_lock(846205213)`;
        const rows = await tx `SELECT * FROM event_outbox WHERE delivered_at IS NULL ORDER BY version LIMIT 1000 FOR UPDATE SKIP LOCKED`;
        if (!rows.length)
            return 0;
        await ch().insert({ table: 'events', values: rows.map(r => r.payload), format: 'JSONEachRow' });
        for (const row of rows)
            await tx `UPDATE event_outbox SET delivered_at=now() WHERE event_id=${row.event_id} AND version=${row.version}`;
        invalidate();
        return rows.length;
    });
}
