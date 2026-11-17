import { writeFile } from 'node:fs/promises';
import { jsonSchemas } from '../src/lib/experience-contract.ts';
const output = new URL('../../../experiments/experience-routing-001/contracts.schema.json', import.meta.url);
await writeFile(output, JSON.stringify(jsonSchemas, null, 2) + '\n');
console.log('Exported experience schemas; no model invocation.');
