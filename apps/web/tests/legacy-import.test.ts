import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { importLegacy } from '../scripts/import-legacy.ts';
import { pg, queryCh, closeDatabases } from '../src/lib/database.ts';
import { restoreRaw } from '../src/lib/raw-store.ts';
import { hash } from '../src/lib/domain.ts';
if (process.env.OBS_TESTING !== '1' || !process.env.CLICKHOUSE_DATABASE?.endsWith('_test'))
    throw Error('Isolated test databases required');
after(closeDatabases);
test('legacy import preserves originals, archives every table, keeps native IDs and never replays active jobs', async () => {
    const folder = await mkdtemp(path.join(tmpdir(), 'observatory-import-')), file = path.join(folder, 'legacy.sqlite');
    try {
        const made = spawnSync('python3', ['-c', `import sqlite3,sys,json
c=sqlite3.connect(sys.argv[1]);c.executescript('''
CREATE TABLE projects(id,name,repo,scope,created);
CREATE TABLE tasks(id,project_id,title,goal,acceptance,status,created,updated,outcome);
CREATE TABLE turns(session_id,turn_id,repo,prompt,start,end,completed);
CREATE TABLE assignments(session_id,turn_id,task_id);
CREATE TABLE events(id,session_id,turn_id,kind,name,ts,runtime,failed,usage,model,source_line,output_hash);
CREATE TABLE task_history_jobs(id,task_id,snapshot_hash,snapshot,status,created,finished,model,result,error,usage);
CREATE TABLE unknown_legacy_extension(id,details);
CREATE TABLE steering_rules(id,name,kind,mode,enabled,builtin,config,message);
INSERT INTO projects VALUES('legacy-project','Legacy project','/legacy','','2026-11-01T00:00:00Z');
INSERT INTO tasks VALUES('legacy-task','legacy-project','Legacy task','Verify migration','','active','2026-11-01T00:00:00Z','2026-11-01T00:00:00Z',NULL);
INSERT INTO turns VALUES('legacy-session','native-turn','/legacy','Retain raw evidence','2026-11-01T00:00:00Z','2026-11-01T00:00:10Z',1);
INSERT INTO assignments VALUES('legacy-session','native-turn','legacy-task');
INSERT INTO events VALUES('legacy-session:response:r1','legacy-session','native-turn','generation','Model response','2026-11-01T00:00:00Z',NULL,NULL,'{"input_tokens":10,"cached_input_tokens":5,"output_tokens":2,"total_tokens":12}','legacy-model',3,NULL);
INSERT INTO task_history_jobs VALUES('legacy-active','legacy-task','old-hash','{}','running',1793491200,NULL,'old-model',NULL,NULL,NULL);
INSERT INTO unknown_legacy_extension VALUES('extension','Opaque preserved record');
INSERT INTO steering_rules VALUES('break','Prompt after a break','break','warn',1,1,'{"threshold":3600}','Imported break rule');
''');c.commit();c.close()`, file], { encoding: 'utf8' });
        assert.equal(made.status, 0, made.stderr);
        const before = hash(await readFile(file)), a = await importLegacy(file), b = await importLegacy(file);
        assert.equal(b.status, 'already_imported');
        assert.equal(hash(await readFile(file)), before);
        assert.equal((await pg() `SELECT status FROM analysis_jobs WHERE id='legacy-active'`)[0].status, 'legacy_running');
        const archive = (await pg() `SELECT archive_id FROM migration_manifests WHERE id=${a.id}`)[0].archive_id;
        assert.ok((await restoreRaw(archive)).toString().includes('Opaque preserved record'));
        assert.equal((await pg() `SELECT count(*)::integer AS n FROM archived_records WHERE import_id=${a.id}`)[0].n, 8);
        assert.equal((await pg() `SELECT count(*)::integer AS n FROM steering_rules WHERE name='Prompt after a break'`)[0].n, 1);
        assert.equal((await pg() `SELECT config FROM steering_rules WHERE id='builtin-break'`)[0].config.minutes, 60);
        assert.equal((await queryCh<{
            n: number;
        }>("SELECT count() AS n FROM events FINAL WHERE id='legacy-session:response:r1'"))[0].n, 1);
    }
    finally {
        await rm(folder, { recursive: true, force: true });
    }
});
