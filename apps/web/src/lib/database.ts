import postgres from 'postgres';
import { createClient } from '@clickhouse/client';
const singleton = globalThis as typeof globalThis & {
    observatoryPg?: ReturnType<typeof postgres>;
    observatoryCh?: ReturnType<typeof createClient>;
};
export function pg() {
    if (!singleton.observatoryPg) {
        if (!process.env.DATABASE_URL)
            throw new Error('DATABASE_URL is required');
        singleton.observatoryPg = postgres(process.env.DATABASE_URL, { max: 10, idle_timeout: 20, connect_timeout: 10, prepare: false, connection: { search_path: 'observatory,public' } });
    }
    return singleton.observatoryPg;
}
export function ch() {
    if (!singleton.observatoryCh) {
        if (!process.env.CLICKHOUSE_URL)
            throw new Error('CLICKHOUSE_URL is required');
        singleton.observatoryCh = createClient({ url: process.env.CLICKHOUSE_URL, username: process.env.CLICKHOUSE_USER || 'observatory', password: process.env.CLICKHOUSE_PASSWORD || '', database: process.env.CLICKHOUSE_DATABASE || 'observatory', request_timeout: 20000, compression: { request: true, response: true }, clickhouse_settings: { date_time_input_format: 'best_effort', max_execution_time: 15, max_result_rows: '100000', result_overflow_mode: 'throw', max_threads: 2, max_block_size: '512' } });
    }
    return singleton.observatoryCh;
}
export async function queryCh<T>(query: string, params: Record<string, unknown> = {}): Promise<T[]> { const result = await ch().query({ query, query_params: params, format: 'JSONEachRow' }); return result.json<T>(); }
export async function closeDatabases() { await Promise.all([singleton.observatoryPg?.end({ timeout: 5 }), singleton.observatoryCh?.close()]); delete singleton.observatoryPg; delete singleton.observatoryCh; }
export async function audit(action: string, entity: string, details: Record<string, unknown> = {}) { await pg() `INSERT INTO audit(action,entity,details) VALUES(${action},${entity},${pg().json(details as postgres.JSONValue)})`; }
