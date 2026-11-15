/** Explicit destructive reset limited to the hard-coded synthetic test databases. */
import { pg, ch, closeDatabases } from '../src/lib/database.ts';
if (!process.argv.includes('--reset') || process.env.OBS_TESTING !== '1' || new URL(process.env.DATABASE_URL!).pathname !== '/observatory_test' || process.env.CLICKHOUSE_DATABASE !== 'observatory_test')
    throw Error('Use --reset with the isolated observatory_test configuration only');
try {
    await pg().unsafe('DROP SCHEMA observatory CASCADE');
    await ch().command({ query: 'DROP DATABASE IF EXISTS observatory_test SYNC' });
    console.log('Only observatory_test synthetic database contents reset.');
}
finally {
    await closeDatabases();
}
