import { fileURLToPath } from 'node:url';
import { pg, closeDatabases } from '../src/lib/database.ts';
import { ingestEvents, flushOutbox } from '../src/lib/ingest.ts';
import { hash, turnKey } from '../src/lib/domain.ts';
export async function seedTest() {
    if (process.env.OBS_TESTING !== '1' || !new URL(process.env.DATABASE_URL!).pathname.endsWith('_test') || !process.env.CLICKHOUSE_DATABASE?.endsWith('_test'))
        throw Error('Fixtures require isolated *_test databases');
    const db = pg();
    await db `INSERT INTO projects(id,name,repo,scope) VALUES('qa-project','Reference validation','/qa/observatory','Synthetic test fixture; never real usage') ON CONFLICT DO NOTHING`;
    const events = [];
    for (let n = 0; n < 32; n++) {
        const id = 'qa-task-' + n, session = 'qa-session-' + Math.floor(n / 4), turn = 'turn-' + n, key = turnKey(session, turn), at = new Date(Date.parse('2026-11-15T12:00:00Z') - (32 - n) * 86400000 / 2);
        await db `INSERT INTO tasks(id,project_id,title,goal,acceptance,status,outcome) VALUES(${id},'qa-project',${'Validate Observatory flow ' + String(n).padStart(2, '0')},'Implement and verify the dashboard workflow','Checks pass and retained evidence matches','active',${n % 7 === 0 ? 'Warning signs' : null}) ON CONFLICT DO NOTHING`;
        await db `INSERT INTO turns(turn_key,session_id,turn_id,workspace,prompt,started_at,finished_at,completed,role,source) VALUES(${key},${session},${turn},'/qa/observatory',${'Please implement and validate flow ' + String(n).padStart(2, '0')},${at},${new Date(+at + 240000)},true,'main','{"answer_chars":800}') ON CONFLICT DO NOTHING`;
        await db `INSERT INTO assignments(turn_key,task_id) VALUES(${key},${id}) ON CONFLICT DO NOTHING`;
        const ids = [];
        for (let i = 0; i < 8; i++) {
            const generation = i % 2 === 0, eid = id + ':' + i;
            ids.push(eid);
            events.push({ id: eid, session_id: session, turn_id: turn, workspace: '/qa/observatory', kind: generation ? 'generation' : 'tool', name: generation ? 'Model response' : 'Bash', model: generation ? n % 3 === 0 ? 'claude-sonnet-5-5' : 'claude-opus-5-5' : '', event_time: new Date(+at + i * 25000).toISOString(), runtime: generation ? 2 : 1.5, failed: generation ? null : n % 5 === 0 ? 1 : 0, input_tokens: generation ? 100000 + n * 10000 : null, cached_tokens: generation ? 80000 : null, output_tokens: generation ? 1000 : null, total_tokens: generation ? 101000 + n * 10000 : null, cache_write_tokens: generation ? 2000 : null, cache_5m_tokens: generation ? 1000 : null, command: generation ? '' : i < 4 ? 'cat src/dashboard.tsx' : 'git status', output_chars: generation ? null : 1000, output_hash: hash([n, i]), signature: generation ? '' : n % 5 === 0 ? 'same-failure' : hash([n, i]), role: n % 4 === 0 ? 'sub' : 'main', agent_type: n % 4 === 0 ? 'Explore' : '', payload: JSON.stringify({ fixture: true, source: 'Synthetic browser validation' }) });
        }
        const aid = 'qa-analysis-' + n;
        await db `INSERT INTO analyses(id,task_id,snapshot_hash,summary,task_type,result) VALUES(${aid},${id},'fixture','Synthetic validated process fixture','feature','{"knowledge":[{"title":"Fixture lesson","statement":"Inspect native source evidence","event_ids":[]}]}') ON CONFLICT DO NOTHING`;
        for (let i = 0; i < 4; i++)
            await db `INSERT INTO subtasks(id,analysis_id,position,title,summary,category,confidence,event_ids,result) VALUES(${aid + ':' + i},${aid},${i},${['Explore', 'Implement', 'Verify', 'Deliver'][i]},'Synthetic interpretation for reference validation',${['explore', 'implement', 'verify', 'deliver'][i]},0.9,${ids.slice(i * 2, i * 2 + 2)},'{}') ON CONFLICT DO NOTHING`;
        if (n % 6 === 0)
            await db `INSERT INTO evidence_notes(id,task_id,kind,title,detail,outcome) VALUES(${id + ':note'},${id},'intervention','Recorded correction','Confirmed synthetic intervention','confirmed') ON CONFLICT DO NOTHING`;
    }
    await ingestEvents(events);
    while (await flushOutbox()) { }
    await db `UPDATE settings SET value='{"unit":"USD","models":{"claude-opus-5-5":{"input":5,"cached":0.5,"output":25},"claude-sonnet-5-5":{"input":3,"cached":0.3,"output":15}}}' WHERE key='pricing'`;
    await db `INSERT INTO settings(key,value) VALUES('model_tiers','{"top":["claude-opus-5-5"],"small":["claude-sonnet-5-5"]}') ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value`;
    await db `INSERT INTO applied_changes(id,title,applied_at,workspace,metrics,notes) VALUES('qa-change','Shell exploration steering rule',now()-interval '4 days','/qa/observatory',ARRAY['cost_per_task','shell','shell_again'],'Synthetic change for screenshot validation') ON CONFLICT DO NOTHING`;
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==', 'base64');
    await db `INSERT INTO retained_images(id,task_id,event_id,mime,bytes) VALUES('qa-image','qa-task-0','qa-task-0:1','image/png',${png}) ON CONFLICT DO NOTHING`;
    console.log('Synthetic test fixture ready: 32 tasks, 256 events, isolated test databases.');
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    try {
        await seedTest();
    }
    finally {
        await closeDatabases();
    }
}
