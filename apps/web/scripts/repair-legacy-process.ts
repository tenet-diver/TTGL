import { pg, closeDatabases } from '../src/lib/database.ts';
import { repairLegacyProcess } from '../src/lib/legacy-process-store.ts';
import { seedApiPricing } from '../src/lib/pricing.ts';
const apply = process.argv.includes('--apply');
try {
    const result = await pg().begin(async tx => ({
        process: await repairLegacyProcess(tx, apply),
        pricing: apply ? await seedApiPricing(tx) : { status: 'not_changed_in_dry_run' },
    }));
    console.log(JSON.stringify(result, null, 2));
} finally { await closeDatabases(); }
