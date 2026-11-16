import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, readFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { tmpdir } from 'node:os';
import { randomUUID } from 'node:crypto';
import { pg, closeDatabases } from '../src/lib/database.ts';
import { ingestEvents, flushOutbox } from '../src/lib/ingest.ts';
import { performAction } from '../src/lib/actions.ts';
import { runOneAnalysis } from '../src/lib/analysis-worker.ts';
import { context, taskScope, taskFacts, invalidate } from '../src/lib/repository.ts';
import { turnKey } from '../src/lib/domain.ts';
if (process.env.OBS_TESTING !== '1' || !process.env.CLICKHOUSE_DATABASE?.endsWith('_test'))
    throw Error('Test-only databases required');
after(closeDatabases);
test('explicit model worker publishes source-bound results with a test double, then preserves uncertainty without retry', async () => {
    const folder = await mkdtemp(path.join(tmpdir(), 'observatory-worker-')), stub = path.join(folder, 'codex-test-double'), counter = path.join(folder, 'calls'), db = pg();
    const env = { bin: process.env.OBS_CODEX_BIN, allow: process.env.OBS_ALLOW_ANALYSIS, dir: process.env.OBS_ANALYSIS_DIR };
    process.env.OBS_CODEX_BIN = stub;
    process.env.OBS_ALLOW_ANALYSIS = '1';
    process.env.OBS_ANALYSIS_DIR = folder;
    // This exact imported ID belongs to the synthetic legacy fixture, never a user queue.
    const old = (await db `SELECT status FROM analysis_jobs WHERE id='legacy-active'`)[0];
    if (old)
        await db `UPDATE analysis_jobs SET status='test_retained' WHERE id='legacy-active'`;
    const taskIds: string[] = [];
    try {
        await writeFile(stub, `#!/usr/bin/env python3
import json,sys,pathlib
pathlib.Path(${JSON.stringify(counter)}).write_text('invoked')
snapshot=json.loads(sys.stdin.read().split('\\n',1)[1]);ids=[s['id'] for s in snapshot['steps']]
result={'summary':'Test double; no model invoked','task_type':'testing','outcome':'unknown','outcome_reason':'Synthetic test','intervention':'unknown','intervention_reason':'Synthetic test','subtasks':[{'title':'Inspect evidence','summary':'Synthetic','category':'verify','event_ids':ids,'confidence':0.5,'outcome':'unknown'}],'knowledge':[]}
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(result))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'cached_input_tokens':4,'output_tokens':2}}))
`, { mode: 0o700 });
        const project = await performAction({ action: 'project', name: 'Worker test', repo: '/qa/worker' }, randomUUID());
        async function queue() { const task = await performAction({ action: 'task', title: 'Synthetic analysis', goal: 'Validate worker; no real model call', project_id: project.id }, randomUUID()), sid = randomUUID(); taskIds.push(String(task.id)); await ingestEvents([{ id: sid + ':response:r', session_id: sid, turn_id: 't', workspace: '/qa/worker', kind: 'generation', event_time: '2026-11-15T10:00:00Z', input_tokens: 10, cached_tokens: 5, output_tokens: 2, total_tokens: 12 }]); await flushOutbox(); await performAction({ action: 'assign', task_id: task.id, turn_keys: [turnKey(sid, 't')] }, randomUUID()); return performAction({ action: 'analyze', task_id: task.id }, randomUUID()); }
        const job = await queue();
        assert.equal(job.status, 'queued');
        await runOneAnalysis();
        assert.equal((await db `SELECT status FROM analysis_jobs WHERE id=${String(job.id)}`)[0].status, 'completed');
        invalidate();
        assert.equal(taskFacts(await context(await taskScope(taskIds[0])), taskIds[0]).complete, true);
        assert.ok((await db `SELECT source FROM analysis_jobs WHERE id=${String(job.id)}`)[0].source.raw_archives['events.jsonl']);
        assert.equal((await db `SELECT usage FROM analysis_jobs WHERE id=${String(job.id)}`)[0].usage.total_tokens, 12);
        await writeFile(stub, '#!/usr/bin/env python3\nimport sys\nsys.stdin.read()\nsys.exit(1)\n', { mode: 0o700 });
        const failed = await queue();
        await runOneAnalysis();
        assert.equal((await db `SELECT status FROM analysis_jobs WHERE id=${String(failed.id)}`)[0].status, 'uncertain');
        assert.equal(await runOneAnalysis(), false);
        assert.equal((await performAction({ action: 'analyze', task_id: taskIds[1] }, randomUUID())).status, 'retained_active_or_uncertain');
    }
    finally {
        for (const task of taskIds)
            await db `UPDATE analysis_jobs SET status='test_retained' WHERE task_id=${task} AND status='uncertain'`;
        if (old)
            await db `UPDATE analysis_jobs SET status=${old.status} WHERE id='legacy-active'`;
        for (const [key, value] of [['OBS_CODEX_BIN', env.bin], ['OBS_ALLOW_ANALYSIS', env.allow], ['OBS_ANALYSIS_DIR', env.dir]])
            if (value == null)
                delete process.env[key!];
            else
                process.env[key!] = value;
        await rm(folder, { recursive: true, force: true });
    }
});
