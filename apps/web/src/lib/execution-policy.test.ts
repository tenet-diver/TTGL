import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { tmpdir } from 'node:os';
import { localGarageEndpoint, subscriptionBinding, sharedSubscription, subscriptionEnvironment, resolveSubscription } from './execution-policy.ts';
import { validateAnalysis } from './analysis-contract.ts';
test('raw storage rejects remote, DNS and credential-bearing endpoints', () => {
    for (const url of ['https://s3.amazonaws.com', 'http://garage.local:3900', 'http://localhost:3900', 'http://127.0.0.1.evil.test', 'http://user:secret@127.0.0.1:3900', 'http://127.0.0.1:3900/bucket', 'http://127.0.0.1:3900?redirect=remote', 'file:///tmp/raw'])
        assert.throws(() => localGarageEndpoint(url));
    assert.equal(localGarageEndpoint('http://127.0.0.1:13900'), 'http://127.0.0.1:13900');
    assert.equal(localGarageEndpoint('http://[::1]:13900'), 'http://[::1]:13900');
});
test('source subscription is mandatory, account-bound, and cannot inherit API billing or remote provider settings', async () => {
    const home = await mkdtemp(path.join(tmpdir(), 'observatory-auth-')), auth = path.join(home, 'auth.json');
    const write = (account: string, extra = {}) => writeFile(auth, JSON.stringify({ auth_mode: 'chatgpt', tokens: { account_id: account, access_token: 'synthetic', refresh_token: 'synthetic' }, ...extra }), { mode: 0o600 });
    try {
        await write('source-account');
        const binding = await subscriptionBinding(home);
        assert.equal(sharedSubscription([{ source: { analysis_binding: binding } }]).account_hash, binding.account_hash);
        assert.throws(() => sharedSubscription([{ source: {} }]));
        assert.throws(() => sharedSubscription([{ source: { analysis_binding: binding } }, { source: { analysis_binding: { ...binding, account_hash: '0'.repeat(64) } } }]));
        const saved = process.env.OPENAI_API_KEY;
        process.env.OPENAI_API_KEY = 'synthetic-api-key';
        try {
            const env = await subscriptionEnvironment(binding);
            assert.equal(env.CODEX_HOME, home);
            assert.equal(env.OPENAI_API_KEY, undefined);
            assert.equal(env.CODEX_API_KEY, undefined);
            assert.equal(env.OPENAI_BASE_URL, undefined);
        }
        finally {
            if (saved == null)
                delete process.env.OPENAI_API_KEY;
            else
                process.env.OPENAI_API_KEY = saved;
        }
        await write('different-account');
        await assert.rejects(subscriptionEnvironment(binding), /subscription changed/);
        await write('source-account', { OPENAI_API_KEY: 'synthetic' });
        await assert.rejects(subscriptionBinding(home), /API-key/);
        await write('source-account', { auth_mode: 'apikey' });
        await assert.rejects(subscriptionBinding(home), /subscription/);
    }
    finally {
        await rm(home, { recursive: true, force: true });
    }
});
const base = { schema_version: 2, summary: 'Source-based interpretation', task_type: 'feature', outcome: 'unknown', outcome_reason: 'Acceptance is not recorded', intervention: 'unknown', intervention_reason: 'No confirmation', knowledge: [], subtasks: [{ title: 'Investigate failing check', summary: 'Check did not establish success', category: 'verify', state: 'blocked', outcome: 'failed', outcome_reason: 'The required check failed', failure_reason: 'Missing dependency prevented validation', event_ids: ['e1'], evidence_event_ids: ['e1'], confidence: .8 }], prompt_relations: [{ turn_key: 't2', relationship: 'course_correction', related_turn_key: 't1', reason: 'User corrected the same requested behavior', evidence_event_ids: ['e1'], confidence: .8 }] };
const turns = [{ turn_key: 't1', session_id: 's', started_at: '2026-11-15T10:00:00Z' }, { turn_key: 't2', session_id: 's', started_at: '2026-11-15T10:01:00Z' }];
test('Luna contract retains typed failure reasons and explicit prompt relationships with complete coverage', () => {
    assert.equal(validateAnalysis(base, ['e1'], ['t2'], turns).subtasks[0].failure_reason, base.subtasks[0].failure_reason);
    for (const relationship of ['course_correction', 'continuation', 'interruption'])
        assert.equal(validateAnalysis({ ...base, prompt_relations: [{ ...base.prompt_relations[0], relationship }] }, ['e1'], ['t2'], turns).prompt_relations[0].relationship, relationship);
    assert.equal(validateAnalysis({ ...base, prompt_relations: [{ ...base.prompt_relations[0], relationship: 'new_task', related_turn_key: null }] }, ['e1'], ['t2'], turns).prompt_relations[0].relationship, 'new_task');
    assert.throws(() => validateAnalysis({ ...base, prompt_relations: [] }, ['e1'], ['t2'], turns), /every analyzed/);
    assert.throws(() => validateAnalysis({ ...base, prompt_relations: [{ ...base.prompt_relations[0], related_turn_key: 'missing' }] }, ['e1'], ['t2'], turns), /earlier retained/);
    assert.throws(() => validateAnalysis(base, ['e1'], ['t2'], [turns[0], { ...turns[1], session_id: 'other' }]), /same session/);
    assert.throws(() => validateAnalysis({ ...base, subtasks: [{ ...base.subtasks[0], failure_reason: null }] }, ['e1'], ['t2'], turns), /failure reason/);
    assert.throws(() => validateAnalysis({ ...base, subtasks: [{ ...base.subtasks[0], evidence_event_ids: ['sibling-step'] }] }, ['e1'], ['t2'], turns), /belong/);
});

test('one subscription may use multiple collected homes and missing bindings are actionable',async()=>{
 const home=await mkdtemp(path.join(tmpdir(),'observatory-binding-'));
 try {
  await writeFile(path.join(home,'auth.json'),JSON.stringify({auth_mode:'chatgpt',tokens:{account_id:'same-account',access_token:'synthetic',refresh_token:'synthetic'}}),{mode:0o600});
  const binding=await subscriptionBinding(home), missing={...binding,codex_home:path.join(home,'removed-home')};
  const turns=[{source:{analysis_binding:missing}},{source:{analysis_binding:binding}}];
  assert.equal((await resolveSubscription(turns)).codex_home,home);
  assert.doesNotThrow(()=>sharedSubscription(turns));
  assert.throws(()=>sharedSubscription([{source:{}}]),/Data list/);
  assert.throws(()=>sharedSubscription([{source:{analysis_binding:{auth_mode:'chatgpt'}}}]),/invalid/);
  assert.throws(()=>sharedSubscription([...turns,{source:{analysis_binding:{...binding,account_hash:'0'.repeat(64)}}}]),/different Codex subscription accounts/);
 }finally{await rm(home,{recursive:true,force:true});}
});
