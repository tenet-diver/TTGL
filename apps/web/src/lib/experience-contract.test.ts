import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateEnvelope, validateVerification, jsonSchemas, envelopeSchema } from './experience-contract.ts';
import { experienceFixture } from './experience-fixture.ts';
import { ineligible, fuse, packetFor } from './experience-retrieval.ts';
import { querySchema, experienceSchema } from './experience-contract.ts';
import { fingerprint } from './experience-store.ts';
import { experiencePrincipal, authorizeExperience } from './experience-auth.ts';
import { createHash } from 'node:crypto';
import { traceBlocks } from './experience-extraction.ts';

test('v3 sidecars preserve primary v2 ownership while sharing a verification event', () => {
    const { source, envelope } = experienceFixture();
    const e = validateEnvelope(envelope, source);
    assert.equal(e.extensions.supportLinks[0].sourceEventId, source.eventIds[1]);
    assert.equal(e.extensions.workItems[1].primaryEventIds[0], source.eventIds[0]);
    assert.deepEqual(envelope, experienceFixture().envelope);
});
test('cross-owner, missing, duplicate and unknown evidence fail deterministically', () => {
    for (const mutate of [
        (e: any) => e.extensions.workItems[1].primaryEventIds.push('unknown'),
        (e: any) => e.extensions.workItems[1].primaryEventIds.push(e.extensions.workItems[1].primaryEventIds[0]),
        (e: any) => e.extensions.workItems[2].sourceSubtaskId = e.extensions.workItems[1].sourceSubtaskId,
        (e: any) => e.extensions.supportLinks[0].sourceEventId = 'private',
        (e: any) => e.extensions.supportLinks[0].analysisRevisionId = 'different',
        (e: any) => e.extensions.outcomePredictions[1].primaryEvidenceEventIds = ['fixture:event1'],
        (e: any) => e.extensions.outcomePredictions[1].label = 'successful',
        (e: any) => e.extensions.outcomePredictions.pop(),
        (e: any) => e.extensions.experiences[0].sourceVisibility = 'evaluation_sealed',
    ]) {
        const { source, envelope } = experienceFixture(); mutate(envelope);
        assert.throws(() => validateEnvelope(envelope, source));
    }
});
test('incomplete/excerpted sources cannot claim complete public support', () => {
    const { source, envelope } = experienceFixture(); source.coverage = { sourceComplete: false, excerpted: true };
    assert.throws(() => validateEnvelope(envelope, source), /coverage/);
    envelope.extensions.experiences[0].admission = 'publicly_supported';
    assert.throws(() => validateEnvelope(envelope, experienceFixture().source), /verification/);
});
test('empty test collections cannot produce passing public verification', () => {
    assert.throws(() => validateVerification({ verificationId: 'v', workItemId: 'w', attemptId: 'a', scope: 'subtask', visibility: 'runtime_public',
        verdict: 'pass', contractHash: 'a'.repeat(64), verifierVersion: 'host', repositoryStateHash: 'b'.repeat(64), criterionResults: [], observedAt: new Date().toISOString() }), /nonempty/);
});
test('Python export is identical to the authoritative Zod schemas', async () => {
    const exported = JSON.parse(await readFile(new URL('../../../../experiments/experience-routing-001/contracts.schema.json', import.meta.url), 'utf8'));
    assert.deepEqual(exported, jsonSchemas);
});
test('scoped credentials cannot cross projects, arms, tasks or read evaluation summaries', () => {
    const token = 'test-only', principal = { tokenSha256: createHash('sha256').update(token).digest('hex'), projectId: 'p', experimentId: 's', role: 'runner', arm: 'HRM', taskIds: ['t'] };
    const p = experiencePrincipal('Bearer ' + token, JSON.stringify([principal]));
    authorizeExperience(p, 'search', { projectId: 'p', experimentId: 's' }, { arm: 'HRM', taskInstanceId: 't' });
    assert.throws(() => authorizeExperience(p, 'search', { projectId: 'other', experimentId: 's' }, {}));
    assert.throws(() => authorizeExperience(p, 'search', { projectId: 'p', experimentId: 's' }, { arm: 'LPM' }));
    assert.throws(() => authorizeExperience(p, 'search', { projectId: 'p', experimentId: 's' }, { taskInstanceId: 'other' }));
    assert.throws(() => authorizeExperience(p, 'evaluation-summary', { projectId: 'p', experimentId: 's' }, {}));
    assert.throws(() => experiencePrincipal('Bearer wrong', JSON.stringify([principal])));
});
test('chronological blocks own each event once and keep overlap context-only', () => {
    const steps = Array.from({ length: 7 }, (_, n) => ({ id: String(n), turn_key: 't' }));
    const blocks = traceBlocks(steps, 3);
    assert.deepEqual(blocks.flatMap(b => b.primaryIds), steps.map(s => s.id));
    assert.deepEqual(blocks[1].contextOnlyIds, ['1', '2']);
    assert.throws(() => traceBlocks([steps[0], steps[0]]), /Duplicate/);
});
test('public outcome claims cannot borrow another work item or attempt verification', () => {
    const {source,envelope: raw}=experienceFixture('proof-ownership');
    const envelope=envelopeSchema.parse(raw);
    const prediction=envelope.extensions.outcomePredictions[1];
    prediction.attemptId='owned-attempt';prediction.publicVerificationIds=['proof'];
    const context={...source,verificationIds:['proof'],publicVerifications:{proof:{workItemId:prediction.workItemId,attemptId:'owned-attempt'}}};
    assert.doesNotThrow(()=>validateEnvelope(envelope,context));
    assert.throws(()=>validateEnvelope(envelope,{...context,publicVerifications:{proof:{workItemId:'unrelated-work',attemptId:'owned-attempt'}}}),/this work item and attempt/);
    assert.throws(()=>validateEnvelope(envelope,{...context,publicVerifications:{proof:{workItemId:prediction.workItemId,attemptId:'another-attempt'}}}),/this work item and attempt/);
});
