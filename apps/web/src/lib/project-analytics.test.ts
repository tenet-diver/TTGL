import assert from 'node:assert/strict';
import test from 'node:test';
import { dailyRows, deliveryTransitions } from './project-analytics.ts';
import { scopeFrom } from './domain.ts';
import { restoreView } from './view-preferences.ts';
import type { NativeEvent } from './types.ts';

test('dashboard charts preserve timezone boundaries, empty days, and missing costs', () => {
    const rows = [
        { id: 'a', stamp: '2026-11-20T00:15:00Z', cost: 2 },
        { id: 'b', stamp: '2026-11-20T03:00:00Z', cost: null },
        { id: 'c', stamp: '2026-11-22T18:00:00Z', cost: 0 },
    ];
    assert.deepEqual(dailyRows(rows, 'stamp', 'cost', 'America/New_York').points, [
        { date: '2026-11-19', value: null }, { date: '2026-11-20', value: 0 },
        { date: '2026-11-21', value: 0 }, { date: '2026-11-22', value: 0 },
    ]);
});

test('delivery counts only observed transitions within one native session', () => {
    const event = (id: string, session: string, operation: string, second: number, time_known = 1) => ({
        id, session_id: session, kind: 'tool', command: operation, event_time: `2026-11-20T12:00:0${second}Z`, time_known,
    }) as NativeEvent;
    const transitions = deliveryTransitions([
        event('one', 's1', 'gh pr checks', 2), event('two', 's1', 'gh pr create', 1),
        event('three', 's2', 'gh pr merge', 3), event('four', 's1', 'gh pr view', 4, 0),
    ]);
    assert.deepEqual(transitions.map(({ from, to, calls, sessions }) => ({ from, to, calls, sessions })), [
        { from: 'create', to: 'checks', calls: 1, sessions: 1 },
    ]);
});

test('shared dashboard filters survive navigation and have an explicit clear state', () => {
    const restored = restoreView('/tools', new URLSearchParams('harness=&range=7d'), {
        scopeModel: 'gpt-6-luna', harness: 'Codex', work: 'example-task',
    }, {});
    assert.equal(restored.query.get('harness'), '');
    assert.deepEqual(scopeFrom(restored.query), { workspace: '', project: '', range: '7d', timezone: 'UTC', model: 'gpt-6-luna', task: 'example-task' });
});
