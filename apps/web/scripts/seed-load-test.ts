/** Synthetic read-model load fixture; never native usage or a model-quality trial. */
import { pg, ch, closeDatabases } from '../src/lib/database.ts';
import { normalizeEvent } from '../src/lib/ingest.ts';
import { turnKey } from '../src/lib/domain.ts';
import { retainRaw } from '../src/lib/raw-store.ts';
if (process.env.OBS_TESTING !== '1' || new URL(process.env.DATABASE_URL!).pathname !== '/observatory_test' || process.env.CLICKHOUSE_DATABASE !== 'observatory_test')
    throw Error('Synthetic fixture requires isolated observatory_test databases');
try {
    const db = pg();
    const tasks: { id: string; project_id: string; title: string; goal: string; acceptance: string; status: string; source: ReturnType<typeof db.json> }[] = [];
    const turns: { turn_key: string; session_id: string; turn_id: string; workspace: string; prompt: string; started_at: Date; finished_at: Date; completed: boolean; role: string }[] = [];
    const assignments: { turn_key: string; task_id: string }[] = [], events = [];
    await db `INSERT INTO projects(id,name,repo,scope) VALUES('qa-load','Synthetic load fixture','/qa/load','Generated metadata for UI latency checks; not actual usage') ON CONFLICT DO NOTHING`;
    for (let n = 0; n < 1000; n++) {
        const task = 'qa-load-task-' + n, session = 'qa-load-session-' + n, key = turnKey(session, 't'), start = Date.parse('2026-11-01T10:00:00Z') + (n % 28) * 86400000;
        tasks.push({ id: task, project_id: 'qa-load', title: 'Synthetic performance task ' + n, goal: 'Generated metadata only', acceptance: '', status: 'observed', source: db.json({ fixture: 'synthetic_load', native_turn: true, turn_key: key }) });
        turns.push({ turn_key: key, session_id: session, turn_id: 't', workspace: '/qa/load', prompt: 'Synthetic performance task ' + n, started_at: new Date(start), finished_at: new Date(start + 12000), completed: true, role: 'main' });
        assignments.push({ turn_key: key, task_id: task });
        for (let i = 0; i < 12; i++) {
            const gen = i % 3 === 0;
            events.push({ ...normalizeEvent({ id: task + ':' + i, session_id: session, turn_id: 't', workspace: '/qa/load', kind: gen ? 'generation' : 'tool', name: gen ? 'Model response' : 'Bash', model: gen ? 'claude-opus-5-5' : '', event_time: new Date(start + (i + 1) * 1000).toISOString(), runtime: 1, failed: gen ? null : 0, input_tokens: gen ? 100000 : null, cached_tokens: gen ? 80000 : null, output_tokens: gen ? 1000 : null, total_tokens: gen ? 101000 : null, cache_write_tokens: gen ? 0 : null, cache_5m_tokens: gen ? 0 : null, command: gen ? '' : 'git status', role: 'main', payload: '{"fixture":"synthetic_load","not_actual_usage":true}' }), version: 1 });
        }
    }
    const archive = await retainRaw(Buffer.from(JSON.stringify({ fixture: 'synthetic_load', tasks: tasks.length, events })), 'synthetic-load', 'fixture://dashboard/1000-tasks');
    await db.begin(async (tx) => { await tx `INSERT INTO tasks ${db(tasks)} ON CONFLICT DO NOTHING`; await tx `INSERT INTO turns ${db(turns)} ON CONFLICT DO NOTHING`; await tx `INSERT INTO assignments ${db(assignments)} ON CONFLICT DO NOTHING`; await tx `INSERT INTO audit(action,entity,details) VALUES('synthetic_load_fixture','qa-load',${tx.json({ tasks: 1000, events: 12000, archive: archive.id, not_actual_usage: true })})`; });
    await ch().insert({ table: 'events', values: events, format: 'JSONEachRow' });
    console.log('Synthetic read-model fixture: 1,000 turns and 12,000 events in test stores only.');
}
finally {
    await closeDatabases();
}
