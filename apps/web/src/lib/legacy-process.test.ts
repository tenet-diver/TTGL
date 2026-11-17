import { test } from 'node:test';
import assert from 'node:assert/strict';
import { legacyProcessFields } from './legacy-process.ts';
import { price } from './domain.ts';
import { pricingSchema } from './pricing.ts';
const row = { outcome: 'failed', reason: 'The retained verification failed after the repair.', confidence: .9, source_steps: '["step-a"]', source_turns: '[]', intervention: 'unknown' };
test('retained failed work is completed lifecycle with failed outcome, original reason and citations', () => {
    const fields = legacyProcessFields(row, ['step-a']);
    assert.equal(fields.state, 'completed'); assert.equal(fields.outcome, 'failed');
    assert.equal(fields.failure_reason, row.reason); assert.deepEqual(fields.evidence_event_ids, ['step-a']);
    assert.equal(fields.source_protocol, 'task-process-v1');
});
test('legacy uncertainty remains unknown and in-progress work remains working', () => {
    const unknown = legacyProcessFields({ ...row, outcome: 'unknown', reason: 'The final result was not retained.' }, ['step-a']);
    assert.equal(unknown.state, 'unknown'); assert.equal(unknown.outcome, 'unknown'); assert.equal(unknown.failure_reason, null);
    assert.equal(legacyProcessFields({ ...row, outcome: 'in_progress' }, ['step-a']).state, 'working');
});
test('cross-subtask outcome citations and unsupported labels block repair', () => {
    assert.throws(() => legacyProcessFields(row, ['step-b']), /outside/);
    assert.throws(() => legacyProcessFields({ ...row, source_steps: '[]' }, ['step-a']), /no retained evidence/);
    assert.throws(() => legacyProcessFields({ ...row, outcome: 'looks_successful' }, ['step-a']), /Unknown legacy/);
});
test('long-context threshold reprices the full request including cache hits and output', () => {
    const pricing = { unit: 'USD', models: { m: { input: 2, cached: .1, output: 10, long_context: { above_tokens: 272000, input: 4, cached: .2, output: 15 } } } };
    assert.equal(price({ kind: 'generation', model: 'm', input_tokens: 272000, cached_tokens: 200000, output_tokens: 1000 }, pricing), .174);
    assert.equal(price({ kind: 'generation', model: 'm', input_tokens: 272001, cached_tokens: 200000, output_tokens: 1000 }, pricing), .343004);
    assert.equal(price({ kind: 'generation', model: 'unpriced-model', input_tokens: 20, cached_tokens: 10, output_tokens: 1 }, pricing), null);
});
test('pricing editor validation preserves long-context rates, date and scenario provenance', () => {
    const value = { unit: 'USD', as_of: '2026-11-16', scenario_id: 'test', kind: 'api_equivalent', service_tier: 'standard', source_urls: ['https://developers.openai.com/api/docs/pricing'], assumptions: ['Write surcharges unrecorded'], models: { m: { input: 2, cached: .1, output: 10, long_context: { above_tokens: 272000, input: 4, cached: .2, output: 15 } } } };
    assert.deepEqual(pricingSchema.parse(value), value);
});
