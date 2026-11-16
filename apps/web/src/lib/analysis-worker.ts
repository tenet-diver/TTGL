import { appendFileSync } from 'node:fs';
import { retainRaw, rawHealth } from './raw-store.ts';
import { analystUsage } from './analyst-usage.ts';
import { spawn } from 'node:child_process';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { pg } from './database.ts';
import { analysisSchema } from './jobs.ts';
import { invalidate } from './repository.ts';
import { LUNA_MODEL, subscriptionEnvironment } from './execution-policy.ts';
import { validateAnalysis, analysisInstruction } from './analysis-contract.ts';
export { validateAnalysis } from './analysis-contract.ts';
export async function runOneAnalysis() {
    if (process.env.OBS_ALLOW_ANALYSIS !== '1')
        throw Error('Explicit OBS_ALLOW_ANALYSIS=1 is required to execute queued model work');
    await rawHealth();
    const db = pg(), job = await db.begin(async (tx) => {
        await tx `SELECT pg_advisory_xact_lock(846205214)`;
        const active = await tx `SELECT id FROM analysis_jobs WHERE status IN ('running','uncertain','legacy_running','legacy_queued') LIMIT 1`;
        if (active.length)
            return null;
        const [next] = await tx `SELECT * FROM analysis_jobs WHERE status='queued' ORDER BY created_at,id LIMIT 1 FOR UPDATE SKIP LOCKED`;
        if (!next)
            return null;
        await tx `UPDATE analysis_jobs SET status='running',started_at=now() WHERE id=${next.id}`;
        return next;
    });
    if (!job)
        return false;
    const folder = path.resolve(process.env.OBS_ANALYSIS_DIR || 'work/observatory-analysis', job.id);
    await mkdir(folder, { recursive: true, mode: 0o700 });
    const schema = path.join(folder, 'schema.json'), answer = path.join(folder, 'answer.json');
    await writeFile(schema, JSON.stringify(analysisSchema), { mode: 0o600 });
    await writeFile(path.join(folder, 'snapshot.json'), JSON.stringify(job.snapshot), { mode: 0o600 });
    const eventsFile = path.join(folder, 'events.jsonl'), stderrFile = path.join(folder, 'stderr.log');
    await writeFile(eventsFile, '', { mode: 0o600 });
    await writeFile(stderrFile, '', { mode: 0o600 });
    const archives: Record<string, string> = {};
    const archiveFiles = async (names: string[]) => {
        for (const name of names) {
            const file = path.join(folder, name);
            try {
                const bytes = await readFile(file);
                archives[name] = (await retainRaw(bytes, 'analyst-' + name, file)).id;
            }
            catch (e) {
                if ((e as NodeJS.ErrnoException).code === 'ENOENT')
                    continue;
                throw e;
            }
        }
    };
    let stdout = '', stderr = '', invoked = false;
    try {
        if (job.model !== LUNA_MODEL || job.snapshot.schema_version !== 2)
            throw Error('Only Luna subscription analysis with the current evidence schema may execute');
        const executionEnv = await subscriptionEnvironment(job.snapshot.subscription_binding);
        await archiveFiles(['schema.json', 'snapshot.json']);
        const args = ['exec', '--disable', 'shell_tool', '--disable', 'apps', '--disable', 'browser_use', '-c', 'web_search="disabled"', '-c', 'project_doc_max_bytes=0', '--ignore-user-config', '--skip-git-repo-check', '--ephemeral', '-s', 'read-only', '-C', folder, '-m', LUNA_MODEL, '-c', 'model_provider="openai"', '-c', 'forced_login_method="chatgpt"', '-c', 'model_providers.openai.request_max_retries=0', '-c', 'model_providers.openai.stream_max_retries=0', '-c', 'cli_auth_credentials_store="file"', '-c', 'model_reasoning_effort="low"', '--output-schema', schema, '--output-last-message', answer, '--json', '-'];
        await new Promise<void>((resolve, reject) => {
            const child = spawn(process.env.OBS_CODEX_BIN || 'codex', args, { stdio: ['pipe', 'pipe', 'pipe'], detached: true, env: executionEnv });
            const timeout = setTimeout(() => { process.kill(-child.pid!, 'SIGTERM'); reject(Error('Analysis timeout; invocation is uncertain and will not be retried')); }, 600000);
            child.on('spawn', () => { invoked = true; });
            child.stdout.on('data', b => {
                appendFileSync(eventsFile, b);
                stdout += b;
                if (stdout.length > 16e6)
                    child.kill('SIGTERM');
            });
            child.stderr.on('data', b => {
                appendFileSync(stderrFile, b);
                stderr += b;
                if (stderr.length > 2e6)
                    child.kill('SIGTERM');
            });
            child.on('error', e => { clearTimeout(timeout); reject(e); });
            child.on('close', code => { clearTimeout(timeout); code === 0 ? resolve() : reject(Error('Analysis process exited ' + code)); });
            child.stdin.end(analysisInstruction + '\n' + JSON.stringify(job.snapshot));
        });
        await archiveFiles(['events.jsonl', 'stderr.log', 'answer.json']);
        const result = validateAnalysis(JSON.parse(await readFile(answer, 'utf8')), job.snapshot.steps.map((s: {
            id: string;
        }) => s.id), job.snapshot.turns.map((t: {
            turn_key: string;
        }) => t.turn_key), job.snapshot.prompt_context);
        const publication = { ...result, source_versions: Object.fromEntries(job.snapshot.steps.map((s: {
                id: string;
                source_version: number;
            }) => [s.id, s.source_version])) };
        let usage: Record<string, unknown> | null = null;
        for (const line of stdout.split('\n'))
            try {
                const r = JSON.parse(line);
                if (r.usage)
                    usage = analystUsage(r.usage);
            }
            catch { }
        await db.begin(async (tx) => {
            const id = randomUUID();
            await tx `INSERT INTO analyses(id,task_id,job_id,snapshot_hash,summary,task_type,result) VALUES(${id},${job.task_id},${job.id},${job.snapshot_hash},${result.summary},${result.task_type},${tx.json(publication)})`;
            for (const [position, g] of result.subtasks.entries())
                await tx `INSERT INTO subtasks(id,analysis_id,position,title,summary,category,confidence,event_ids,result) VALUES(${randomUUID()},${id},${position},${g.title},${g.summary},${g.category},${g.confidence},${g.event_ids},${tx.json(g)})`;
            await tx `UPDATE analysis_jobs SET status='completed',result=${tx.json(result)},usage=${usage ? tx.json(usage) : null},source=${tx.json({ ...job.source, raw_archives: archives, artifact_directory: folder })},finished_at=now() WHERE id=${job.id}`;
        });
    }
    catch (e) {
        try {
            await archiveFiles(['events.jsonl', 'stderr.log', 'answer.json']);
        }
        catch { }
        await db `UPDATE analysis_jobs SET status=${invoked ? 'uncertain' : 'failed'},error=${e instanceof Error ? e.message : 'Analysis failed'},source=${db.json({ ...job.source, raw_archives: archives, artifact_directory: folder })},finished_at=now() WHERE id=${job.id}`;
    }
    finally {
        invalidate();
    }
    return true;
}
