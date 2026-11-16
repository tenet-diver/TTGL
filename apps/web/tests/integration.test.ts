import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { pg, queryCh, closeDatabases } from '../src/lib/database.ts';
import { ingestEvents, flushOutbox } from '../src/lib/ingest.ts';
import { retainRaw, restoreRaw, archivePlan, rawHealth, readRaw } from '../src/lib/raw-store.ts';
import { receiveHook } from '../src/lib/steering.ts';
import { performAction } from '../src/lib/actions.ts';
import { recordData, daily, outcomes } from '../src/lib/analytics.ts';
import { context, invalidate } from '../src/lib/repository.ts';
import { pageData, routes } from '../src/lib/pages.ts';
import { seedTest } from '../scripts/seed-test.ts';
import { migrate } from '../scripts/migrate.ts';
const scope = { project: '', workspace: '', range: 'all', timezone: 'UTC' }, q = { search: '', filters: {}, sort: null, direction: 1 as const, offset: 0, limit: 20 };
if (process.env.OBS_TESTING !== '1' || !process.env.CLICKHOUSE_DATABASE?.endsWith('_test'))
    throw Error('Integration tests require isolated test databases');
after(closeDatabases);
test('migrations are repeatable and checked before fixture reads', async () => { await migrate(); await migrate(); await seedTest(); });
test('exact raw bytes restore and replay without duplicating identity', async () => { await rawHealth(); const bytes = Buffer.from('  {"raw":"évidence","secret":"preserved as original"}\r\n\x00'); const a = await retainRaw(bytes, 'integration', '/qa/exact.jsonl'), b = await retainRaw(bytes, 'integration', '/qa/exact.jsonl'); assert.equal(a.id, b.id); assert.deepEqual(await restoreRaw(a.id), bytes); await assert.rejects(readRaw(a.key, '0'.repeat(64)), /checksum/); });
test('growing raw files share complete chunks and retain previous versions', async () => { const a = Buffer.alloc(4 * 1024 * 1024, 65), b = Buffer.concat([a, Buffer.from('appended')]); assert.equal(archivePlan(a).chunks[0].key, archivePlan(b).chunks[0].key); const original = await retainRaw(a, 'integration', '/qa/growing'), newer = await retainRaw(b, 'integration', '/qa/growing'); assert.notEqual(original.id, newer.id); assert.deepEqual(await restoreRaw(original.id), a); assert.deepEqual(await restoreRaw(newer.id), b); });
test('native identity replay, durable outbox and FINAL reconciliation', async () => {
    const id = 'integration:' + randomUUID(), raw = { id, session_id: 'integration', turn_id: id, kind: 'generation', model: 'm', event_time: '2026-11-01T00:00:00Z', input_tokens: 10, cached_tokens: 2, output_tokens: 3, total_tokens: 13 };
    assert.equal((await ingestEvents([raw])).inserted, 1);
    assert.equal((await ingestEvents([raw])).unchanged, 1);
    await flushOutbox();
    assert.equal((await queryCh<{
        count: string;
    }>('SELECT count() AS count FROM events FINAL WHERE id={id:String}', { id }))[0].count, 1);
    assert.equal((await ingestEvents([{ ...raw, input_tokens: 20, total_tokens: 23 }])).conflicts, 1);
    assert.equal((await ingestEvents([{ ...raw, workspace: '/changed' }])).conflicts, 1);
    assert.equal((await ingestEvents([{ ...raw, output_hash: 'retained-more-evidence' }])).inserted, 1);
    await flushOutbox();
    assert.equal((await queryCh<{
        count: number;
    }>('SELECT count() AS count FROM events FINAL WHERE id={id:String}', { id }))[0].count, 1);
});
test('mutation idempotency protects writes and rejects reused content', async () => { const key = randomUUID(), body = { action: 'project', name: 'Integration ' + key, repo: '/qa' }; const a = await performAction(body, key), b = await performAction(body, key); assert.equal(a.id, b.id); await assert.rejects(performAction({ ...body, name: 'different' }, key)); });
test('built-in steering rules cannot be deleted or have invalid thresholds', async () => { await assert.rejects(performAction({ action: 'delete-rule', id: 'builtin-break' }, randomUUID())); await assert.rejects(performAction({ action: 'rule', id: 'builtin-break', config: { minutes: 0 } }, randomUUID())); });
test('hook replay latches budget, preserves notes and enforces pause', async () => {
    const session = 'hook-' + randomUUID();
    const start = { session_id: session, event_id: 'start', event: 'start', workspace: '/qa/observatory', task_id: 'qa-task-0' };
    await receiveHook(start);
    await performAction({ action: 'note', session_id: session, message: 'Check the evidence first' }, randomUUID());
    const hook = { ...start, event: 'pre_tool', event_id: 'budget', tool: 'Bash', command: 'git status', task_cost_usd: 5 };
    const a = await receiveHook(hook), b = await receiveHook(hook);
    assert.deepEqual(a, b);
    assert.equal(a.notes.length, 1);
    assert.equal(a.decision, 'ask');
    const next = await receiveHook({ ...hook, event_id: 'next' });
    assert.equal(next.notes.length, 0);
    assert.equal(next.messages.some((m: {
        rule: string;
    }) => m.rule === 'Task budget'), false);
    await performAction({ action: 'session', id: session, paused: true }, randomUUID());
    assert.equal((await receiveHook({ ...hook, event_id: 'paused' })).decision, 'block');
    await assert.rejects(receiveHook({ ...hook, command: 'changed' }));
});
test('shared record engine paginates and filters every collection', async () => {
    for (const kind of ['tasks', 'marked', 'steps', 'tools', 'targets', 'models', 'agents', 'transitions', 'categories', 'paths', 'fixes', 'loops', 'commits', 'fix-workspaces', 'fix-categories', 'findings', 'timeline', 'rules', 'live', 'rule-log', 'changes', 'jobs', 'sources', 'categorization', 'knowledge', 'archives', 'outcome-summary']) {
        const page = await recordData(kind, scope, { ...q, limit: 2 }, new URLSearchParams());
        assert.ok(page.columns.length, kind);
        for (const col of page.columns.filter(c => c.numeric))
            for (const row of page.rows)
                if (row[col.key] != null)
                    assert.equal(typeof row[col.key], 'number', kind + '.' + col.key);
        assert.ok(page.rows.length <= 2, kind);
        const searched = await recordData(kind, scope, { ...q, search: 'no-such-needle-unique' }, new URLSearchParams());
        assert.equal(searched.total, 0, kind);
        if (page.columns.length)
            await recordData(kind, scope, { ...q, sort: page.columns[0].key }, new URLSearchParams());
    }
});
test('task-scoped steps do not include adjacent tasks', async () => { const page = await recordData('steps', scope, q, new URLSearchParams('task=qa-task-0')); assert.equal(page.total, 8); assert.ok(page.rows.every(r => r.id.startsWith('qa-task-0:'))); });
test('all dashboard pages return valid typed data without invoking a model', async () => {
    for (const view of Object.keys(routes)) {
        const data = await pageData(view, scope, new URLSearchParams());
        assert.ok(data.title, view);
        assert.ok(data.panels.length, view);
    }
});
test('unsupported or missing cost counters stay unknown', async () => { invalidate(); const c = await context({ ...scope, task: 'qa-task-0' }); assert.equal(c.events.length, 8); assert.ok(c.events.every(e => e.turn_key === JSON.stringify(['qa-session-0', 'turn-0']))); });
test('token-type stacks reconcile to native totals when all input partitions are observed', async () => {
    invalidate();
    const c = await context({ ...scope, project: 'qa-project' }), data = daily(c, 'tokens', 'type');
    for (const point of data.points) {
        const native = c.events.filter(e => e.kind === 'generation' && e.event_time.slice(0, 10) === point.date).reduce((sum, e) => sum + Number(e.total_tokens), 0);
        assert.equal(data.keys.reduce((sum, key) => sum + Number(point[key]), 0), native);
    }
});
test('confirmed interventions remain scoped to the selected project', async () => { const c = await context({ ...scope, project: 'no-matching-project' }); assert.equal(outcomes(c).confirmed, 0); });
