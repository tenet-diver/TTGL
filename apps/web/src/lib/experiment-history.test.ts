import { test } from 'node:test';
import assert from 'node:assert/strict';
import { historyRows } from './experiment-history.ts';

test('experiment history keeps failed measurements, reviews and overlapping accounting distinct', () => {
    const row = (table_name: string, record: Record<string, unknown>) => ({ table_name, record, import_id: 'retained', row_number: 1 });
    const history = historyRows([
        row('experiments', { id: 'p', task_id: 't', proposal: JSON.stringify({ title: 'A proposal', change: 'one change' }), created: '2026-11-05' }),
        row('experiments', { id: 'unrun', proposal: JSON.stringify({ change: 'long evidence '.repeat(100) }), created: '2026-11-06' }),
        row('experiment_evaluations', { id: 'failed', experiment_id: 'p', protocol: '{"id":"trial-001"}', measurements: '{"acceptance_passed":false,"tokens":100}' }),
        row('experiment_evaluations', { id: 'passed', experiment_id: 'p', protocol: '{"id":"trial-002"}', measurements: '{"acceptance_passed":true,"tokens":50}' }),
        row('experiment_reviews', { id: 'review', evaluation_id: 'failed', verdict: 'inconclusive', notes: 'Keep failed evidence' }),
        row('experiment_accounting', { id: 'a', experiment_id: 'p', payload: '{"tokens":1000}' }),
        row('experiment_accounting', { id: 'b', experiment_id: 'p', payload: '{"tokens":1500}' }),
    ]);
    assert.equal(history.experiments[0].state, 'evaluated');
    assert.equal(history.experiments[0].implementation, 'unrecorded');
    assert.equal(history.experiments[1].state, 'proposed');
    assert.ok(String(history.experiments[1].change).length <= 240);
    assert.equal((history.experiments[1].proposal as Record<string, unknown>).change, 'long evidence '.repeat(100));
    assert.equal(history['experiment-evaluations'][0].acceptance, false);
    assert.equal(history['experiment-evaluations'][1].acceptance, true);
    assert.equal(history['experiment-reviews'][0].evaluation_id, 'failed');
    assert.deepEqual(history['experiment-accounting'].map(r => r.payload), [{ tokens: 1000 }, { tokens: 1500 }]);
    assert.deepEqual(history['experiment-reviews'][0].source, { import_id: 'retained', table: 'experiment_reviews', row: 1 });
});

test('missing gates and malformed retained payloads stay unknown', () => {
    const rows = historyRows([{ table_name: 'experiment_evaluations', record: { id: 'e', measurements: 'invalid', protocol: '{}' }, import_id: 'i', row_number: 0 }]);
    assert.equal(rows['experiment-evaluations'][0].acceptance, null);
    assert.equal(rows['experiment-evaluations'][0].title, 'Unknown proposal');
    assert.deepEqual(rows['experiment-evaluations'][0].measurements, { unavailable: 'Invalid retained JSON', original: 'invalid' });
});
