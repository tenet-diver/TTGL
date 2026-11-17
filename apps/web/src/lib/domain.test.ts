import { test } from 'node:test';
import assert from 'node:assert/strict';
import { price, iso, scopeFrom, queryFrom, rolling, turnKey, failureLoops, hash } from './domain.ts';
import { collection, exactFilter } from './record-query.ts';
import { normalizeEvent } from './ingest.ts';
import { parseNative } from './native-parser.ts';
import { turnSegments } from './timeline.ts';
import { validateAnalysis } from './analysis-worker.ts';
const query = { search: '', filters: {}, sort: null, direction: 1 as const, offset: 0, limit: 10 };
const rows = [{ id: '1', name: 'Édit 10', count: 10 }, { id: '2', name: 'edit 2', count: 2 }, { id: '3', name: 'Unknown', count: null }];
test('source keys cannot collide through separators', () => assert.notEqual(turnKey('a:b', 'c'), turnKey('a', 'b:c')));
test('native zero remains known; missing and negative remain unknown', () => { assert.equal(iso(null), null); assert.equal(iso('bad'), null); assert.equal(normalizeEvent({ id: 'a', session_id: 's', turn_id: 't', kind: 'tool', runtime: 0 }).runtime, 0); assert.throws(() => normalizeEvent({ id: 'a', session_id: 's', turn_id: 't', kind: 'tool', runtime: -1 })); });
test('cache is input subset for API-equivalent pricing', () => { const rate = { unit: 'USD', models: { m: { input: 10, cached: 1, output: 20 } } }; assert.equal(price({ kind: 'generation', model: 'm', input_tokens: 100, cached_tokens: 80, output_tokens: 5 }, rate), .00038); assert.equal(price({ kind: 'generation', model: 'm', input_tokens: null, cached_tokens: 0, output_tokens: 0 }, rate), null); });
test('reject inconsistent native counters', () => { assert.throws(() => normalizeEvent({ id: 'a', session_id: 's', turn_id: 't', kind: 'generation', input_tokens: 10, cached_tokens: 11 })); assert.throws(() => normalizeEvent({ id: 'a', session_id: 's', turn_id: 't', kind: 'generation', input_tokens: 10, output_tokens: 2, total_tokens: 20 })); });
test('all configured columns participate in normalized search', () => assert.equal(collection(rows, { ...query, search: 'edit 10' }, ['name', 'count']).rows[0].id, '1'));
test('numeric filter and descending numeric sorting use the full cohort', () => { assert.equal(collection(rows, { ...query, filters: { count: '>= 3' } }, ['name', 'count']).total, 1); assert.deepEqual(collection(rows, { ...query, sort: 'count', direction: -1 }, ['name', 'count']).rows.map(r => r.id), ['1', '2', '3']); });
test('natural column sort and nulls last', () => assert.deepEqual(collection(rows, { ...query, sort: 'name' }, ['name']).rows.map(r => r.id), ['2', '1', '3']));
test('filter deletion clamps to a valid last page', () => assert.equal(collection(rows, { ...query, offset: 100, limit: 2 }, ['name']).offset, 2));
test('unknown columns cannot become arbitrary query identifiers', () => assert.throws(() => collection(rows, { ...query, sort: ';DROP TABLE tasks' }, ['name'])));
test('invalid query sizes, filters and timezone fail validation', () => {
    for (const p of ['limit=1001', 'offset=-1', 'query={"filters":{"x":null}}'])
        assert.throws(() => queryFrom(new URLSearchParams(p)));
    assert.throws(() => scopeFrom(new URLSearchParams('timezone=Invalid')));
    assert.throws(() => scopeFrom(new URLSearchParams('range=2d')));
});
test('malformed JSON and non-object query envelopes return a stable validation error', () => {
    for (const value of ['{broken', 'null', '[]', '"model"', '{"filters":[]}', '{"offset":9007199254740992}'])
        assert.throws(() => queryFrom(new URLSearchParams({ query: value })), /Invalid record (query|page)/, value);
});
test('model exclusion round-trips quoted names through URL and JSON and covers all pages', () => {
    const name = 'provider/model "quoted" \\ cached', items = [{ id: '1', models: name }, { id: '2', models: 'other' }, { id: '3', models: null }];
    for (const op of ['==', '!==']) {
        const original = { ...query, filters: { models: op + JSON.stringify(name) }, limit: 1 };
        const decoded = queryFrom(new URLSearchParams(new URLSearchParams({ query: JSON.stringify(original) }).toString()));
        assert.deepEqual(decoded, original);
        const result = collection(items, decoded, ['models']);
        assert.equal(result.total, op === '==' ? 1 : 2);
        assert.equal(result.rows[0].id, op === '==' ? '1' : '2');
    }
});
test('large compound cell exclusion stays bounded and exact across pagination and scopes', () => {
    const value = [{ model: 'a'.repeat(900), calls: 20 }], items = [{ id: '1', value }, { id: '2', value: [{ model: 'a'.repeat(900), calls: 21 }] }, { id: '3', value: null }];
    const digest = (v: unknown) => hash(JSON.stringify(v ?? null));
    const filter = exactFilter(value, true, digest(value));
    const decoded = queryFrom(new URLSearchParams({ query: JSON.stringify({ ...query, filters: { value: filter }, limit: 1, offset: 1 }) }));
    assert.ok(filter.length < 200);
    assert.equal(collection(items, decoded, ['value'], digest).total, 2);
    assert.equal(collection(items, decoded, ['value'], digest).rows[0].id, '3');
    assert.equal(collection(items.slice(1), { ...decoded, offset: 0 }, ['value'], digest).total, 2);
    assert.equal(collection(items, { ...decoded, filters: { value: exactFilter(value, false, digest(value)) } }, ['value'], digest).rows[0].id, '1');
    assert.equal(collection(items, { ...decoded, filters: { value: '!==#invalid' } }, ['value'], digest).total, 0);
});
test('rolling average weights real denominators and calendar gaps', () => { const points = rolling([{ date: '2026-11-01', numerator: 1, denominator: 1 }, { date: '2026-11-02', numerator: 0, denominator: 9 }, { date: '2026-11-10', numerator: 1, denominator: 2 }]); assert.equal(points[1].average, .1); assert.equal(points[2].average, .5); });
test('native response identities ignore cumulative token defaults', () => { const records = [{ type: 'session_meta', payload: { id: 's', cwd: '/w', source: 'cli' } }, { type: 'event_msg', timestamp: '2026-11-01T00:00:00Z', payload: { turn_id: 't', type: 'token_count', info: { total_token_usage: { total_tokens: 9000 } } } }, { type: 'token_usage_record', timestamp: '2026-11-01T00:00:01Z', payload: { turn_id: 't', response_id: 'r', usage: { input_tokens: 10, cached_input_tokens: 5, output_tokens: 2, total_tokens: 12 } } }]; const p = parseNative(records.map(r => JSON.stringify(r)).join('\n'), 'codex', 'fixture'); assert.equal(p.events.length, 1); assert.equal(p.events[0].id, 's:response:r'); });
test('malformed lines are recorded rather than silently dropped', () => assert.equal(parseNative('{"type":"session_meta","payload":{"id":"s"}}\nbad', 'codex', 'fixture').malformed, 1));
test('Claude tool use/results join native IDs and retain unknown runtime', () => { const source = [{ sessionId: 's', cwd: '/w', type: 'user', uuid: 't', message: { content: 'Fix this' } }, { sessionId: 's', type: 'assistant', message: { id: 'm', model: 'claude', stop_reason: 'tool_use', usage: { input_tokens: 10, cache_read_input_tokens: 20, cache_creation_input_tokens: 5, output_tokens: 2 }, content: [{ type: 'tool_use', id: 'tool1', name: 'Bash', input: { command: 'git status' } }] } }, { sessionId: 's', type: 'user', message: { content: [{ type: 'tool_result', tool_use_id: 'tool1', content: 'done', is_error: false }] } }]; const p = parseNative(source.map(r => JSON.stringify(r)).join('\n'), 'claude', 'fixture'); assert.equal(p.events.length, 2); assert.equal(p.events[0].input_tokens, 35); assert.equal(p.events[1].id, 's:tool:tool1'); assert.equal(p.events[1].failed, 0); });
test('local midnight splits timeline spans', () => { const parts = turnSegments('2026-11-01T23:50:00Z', '2026-11-02T00:10:00Z', 'UTC'); assert.equal(parts.length, 2); assert.equal(parts[1].date, '2026-11-02'); assert.ok(Math.abs(parts.reduce((s, p) => s + p.hours, 0) - 1 / 3) < 1e-8); });
test('DST fall-back retains both real hours as distinct segments', () => { const parts = turnSegments('2026-11-01T05:30:00Z', '2026-11-01T07:30:00Z', 'America/New_York'); assert.equal(parts.length, 2); assert.ok(Math.abs(parts.reduce((s, p) => s + p.hours, 0) - 2) < 1e-8); });
test('analysis publication rejects missing and duplicated evidence coverage', () => { const result = { schema_version: 2, prompt_relations: [], summary: 'a', task_type: 'feature', outcome: 'unknown', outcome_reason: 'a', intervention: 'unknown', intervention_reason: 'a', knowledge: [], subtasks: [{ title: 'a', summary: 'a', category: 'explore', event_ids: ['e1'], confidence: .5, state: 'unknown', outcome: 'unknown', outcome_reason: 'Insufficient evidence', failure_reason: null, evidence_event_ids: [] }] }; assert.throws(() => validateAnalysis(result, ['e1', 'e2'])); assert.throws(() => validateAnalysis({ ...result, subtasks: [result.subtasks[0], result.subtasks[0]] }, ['e1'])); assert.equal(validateAnalysis(result, ['e1']).subtasks.length, 1); });
import { nativeEvidence } from './task-evidence.ts';
test('phrase search does not match a title word and unrelated timestamp fragment', () => { const page = collection([{ id: '1', title: 'flow 31', at: '2026-01-01T00:00:00Z' }, { id: '2', title: 'flow 00', at: '2026-01-01T00:00:00Z' }], { ...query, search: 'flow 00' }, ['title', 'at']); assert.equal(page.total, 1); assert.equal(page.rows[0].id, '2'); });
test('native command success is not promoted across compound shell status ambiguity', () => { const base = normalizeEvent({ id: 'a', session_id: 's', turn_id: 't', kind: 'tool', command: 'npm test; echo done', failed: 0 }); const facts = nativeEvidence([{ ...base, version: 1 }]); assert.equal(facts[0].outcome, 'unknown'); });
test('incomplete Claude streaming usage remains unknown until a final message', () => { const records = [{ sessionId: 's', type: 'user', uuid: 't', message: { content: 'hello' } }, { sessionId: 's', type: 'assistant', message: { id: 'r', model: 'm', usage: { input_tokens: 0, cache_read_input_tokens: 0, cache_creation_input_tokens: 0, output_tokens: 0 }, stop_reason: null, content: [] } }]; const p = parseNative(records.map(r => JSON.stringify(r)).join('\n'), 'claude', 'fixture'); assert.equal(p.events.length, 1); assert.equal(p.events[0].input_tokens, null); });
import { sameOrigin } from './request-guards.ts';
test('same-origin mutations use public Host rather than an internal Next rewrite', () => { assert.equal(sameOrigin('http://127.0.0.1:3433', '127.0.0.1:3433'), true); assert.equal(sameOrigin('https://observatory.example', 'observatory.example'), true); assert.equal(sameOrigin('https://evil.example', 'observatory.example'), false); assert.equal(sameOrigin(null, 'observatory.example'), false); assert.equal(sameOrigin('http://localhost:3333', 'localhost:3433'), false); });
import { analystUsage } from './analyst-usage.ts';
test('analyst overhead rejects missing and upstream all-zero CLI counters', () => { assert.equal(analystUsage({ input_tokens: 0, cached_input_tokens: 0, output_tokens: 0 }), null); assert.equal(analystUsage({ input_tokens: 10, cached_input_tokens: 11, output_tokens: 2 }), null); assert.equal(analystUsage({ input_tokens: 10, cached_input_tokens: 5, output_tokens: 2 })?.total_tokens, 12); });
import { isValidationCommand } from './validation-command.ts';
test('verification evidence requires an executed command and rejects filename/quoted mentions', () => {
    for (const command of ['python3 -m pytest -q', 'npm run typecheck', 'cd app && pnpm test', 'cargo test', './scripts/check.sh'])
        assert.equal(isValidationCommand(command), true, command);
    for (const command of ['cat docs/build.md', 'echo "npm test passed"', 'grep test src/app.ts', 'git commit -m "build: changes"'])
        assert.equal(isValidationCommand(command), false, command);
});
test('exact context filters distinguish literal text and null across a complete collection', () => { const items = [{ id: '1', state: 'Needs a fix' }, { id: '2', state: 'Needs a fix later' }, { id: '3', state: null }]; assert.equal(collection(items, { ...query, filters: { state: '=="Needs a fix"' } }, ['state']).total, 1); assert.equal(collection(items, { ...query, filters: { state: '==null' } }, ['state']).rows[0].id, '3'); assert.deepEqual(collection(items, { ...query, filters: { state: '!==\"Needs a fix\"' } }, ['state']).rows.map(r => r.id), ['2', '3']); assert.equal(collection(items, { ...query, filters: { state: '!==null' } }, ['state']).total, 2); assert.equal(collection(items, { ...query, filters: { state: '!==invalid' } }, ['state']).total, 0); });
import { friction } from './friction.ts';
function measured(id: string, extra: Record<string, unknown> = {}) { return { ...normalizeEvent({ id, session_id: 's', turn_id: 't', kind: 'tool', name: 'Read', event_time: new Date(Date.parse('2026-11-15T10:00:00Z') + Number(id.replace(/\D/g, '')) * 1000).toISOString(), failed: 0, ...extra }), version: 1 }; }
test('friction includes long exploration and native context jumps without cross-turn inference', () => { const reads = Array.from({ length: 22 }, (_, i) => measured('e' + i)); assert.ok(friction(reads).some(r => r.type === 'Long explore before the first edit')); const before = measured('e1', { kind: 'generation', input_tokens: 100000 }), after = measured('e2', { kind: 'generation', input_tokens: 150000 }); assert.ok(friction([before, after]).some(r => r.type === 'Context jumped')); assert.equal(friction([before, { ...after, turn_key: 'other-turn' }]).length, 0); });
test('three unsuccessful edit/check cycles are source-linked and a successful check breaks the chain', () => { const calls = Array.from({ length: 6 }, (_, i) => measured('e' + i, { name: i % 2 ? 'Bash' : 'Edit', command: i % 2 ? 'npm test' : '', failed: i % 2 ? 1 : 0 })); assert.ok(friction(calls).some(r => r.type === 'Edit/check failures repeated')); calls[3].failed = 0; assert.equal(friction(calls).some(r => r.type === 'Edit/check failures repeated'), false); });
test('explicit cache-write pricing needs supported rates and does not double-charge input', () => { const event = { kind: 'generation', model: 'm', input_tokens: 10, cached_tokens: 5, output_tokens: 2, cache_write_tokens: 2, cache_5m_tokens: 1 }; assert.equal(price(event, { unit: 'USD', models: { m: { input: 10, cached: 1, output: 20 } } }), null); const cost = price(event, { unit: 'USD', models: { m: { input: 10, cached: 1, output: 20, write_5m: 12.5, write_1h: 20 } } }); assert.ok(cost != null && Math.abs(cost - .0001075) < 1e-12); });
test('upstream all-zero generation defaults remain unmetered instead of free inference', () => { const event = normalizeEvent({ id: 'r', session_id: 's', turn_id: 't', kind: 'generation', input_tokens: 0, cached_tokens: 0, output_tokens: 0, total_tokens: 0 }); assert.equal(event.input_tokens, null); assert.equal(event.total_tokens, null); });
import { raster } from './raster.ts';
test('raster previews reject SVG, spoofed bytes and oversized images', () => { assert.equal(raster('image/svg+xml', Buffer.from('<svg/>').toString('base64')), null); assert.equal(raster('image/png', Buffer.from('<svg/>').toString('base64')), null); const large = Buffer.alloc(1048577); large.set([137, 80, 78, 71, 13, 10, 26, 10]); assert.equal(raster('image/png', large.toString('base64')), null); });
test('Claude agent role stays unknown when native identity fields are absent', () => { const rows = [{ type: 'user', sessionId: 's', uuid: 't', message: { content: 'hello' } }, { type: 'assistant', sessionId: 's', message: { id: 'r', model: 'm', usage: { input_tokens: 1, cache_read_input_tokens: 0, cache_creation_input_tokens: 0, output_tokens: 1 }, stop_reason: 'end_turn', content: [{ type: 'text', text: 'hello' }] } }]; const source = rows.map(r => JSON.stringify(r)).join('\n'); assert.equal(parseNative(source, 'claude', 'fixture').events[0].role, ''); assert.equal(parseNative(rows.map(r => JSON.stringify({ ...r, isSidechain: false })).join('\n'), 'claude', 'fixture').events[0].role, 'main'); });
import { operationIntervals } from './timeline.ts';
test('finite operation intervals end at their recorded completion and exclude service lifetime', () => { const events = operationIntervals([{ id: 'a', at: '2026-11-15T10:00:05Z', runtime: 5 }, { id: 'b', at: '2026-11-15T10:00:10Z', runtime: 5 }, { id: 'service', at: '2026-11-15T10:00:10Z', runtime: 90000, runtime_role: 'background_service_lifetime' }, { id: 'unknown', at: '2026-11-15T10:00:12Z', runtime: null }]); assert.equal(events.length, 3); assert.equal(events[0].end - events[0].start, 5000); assert.equal(events[1].start, events[0].end); assert.equal(events[2].duration_known, false); });
