import { z } from 'zod';
import { readFile } from 'node:fs/promises';
import type postgres from 'postgres';
const amount = z.number().finite().nonnegative();
const fields = { input: amount, cached: amount, output: amount, write: amount.optional(), write_5m: amount.optional(), write_1h: amount.optional() };
export const pricingSchema = z.object({
    unit: z.literal('USD'), models: z.record(z.string().min(1).max(200), z.object({ ...fields, long_context: z.object({ ...fields, above_tokens: z.number().int().positive() }).optional() })),
    as_of: z.string().max(100).optional(), scenario_id: z.string().max(200).optional(), kind: z.literal('api_equivalent').optional(),
    service_tier: z.string().max(100).optional(), source_urls: z.array(z.string().url()).max(20).optional(), assumptions: z.array(z.string().max(2000)).max(20).optional(),
});
/** Fill only the pristine empty setting. Never replace a user's configured rates. */
export async function seedApiPricing(tx: postgres.TransactionSql) {
    const pricing = pricingSchema.parse(JSON.parse(await readFile(new URL('../../config/api-pricing-20261116.json', import.meta.url), 'utf8')));
    const changed = await tx`INSERT INTO settings(key,value) VALUES('pricing',${tx.json(pricing)}) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value,updated_at=now() WHERE settings.value='{"unit":"USD","models":{}}'::jsonb RETURNING key`;
    if (changed.length) await tx`INSERT INTO audit(action,entity,details) VALUES('api_pricing_seeded','pricing',${tx.json({ scenario_id: pricing.scenario_id, as_of: pricing.as_of, sources: pricing.source_urls, preserve_native_counters: true })})`;
    return { seeded: Boolean(changed.length), scenario_id: pricing.scenario_id };
}
