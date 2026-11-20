/** Publish an approved native SIM study summary through the Observatory experiment archive. */
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { basename, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { closeDatabases, pg } from '../src/lib/database.ts';
import { rawHealth, restoreRaw, retainRaw } from '../src/lib/raw-store.ts';

const CONDITIONS = ['C0', 'C1', 'C2', 'C3'] as const;
const PROJECT_ID = 'observatory-sim-memory-research';
const projectRoot = fileURLToPath(new URL('../../../', import.meta.url));
const digest = (bytes: Uint8Array) => createHash('sha256').update(bytes).digest('hex');
type Summary = {
    id: string;
    complete: true;
    protocol: { id: string; repetitions: number };
    per_run: { rep: number; condition: string }[];
    stages: object;
    paired_comparisons: object;
};

export function approvedSummary(bytes: Buffer, expectedSha256: string): Summary {
    if (!/^[0-9a-f]{64}$/.test(expectedSha256) || bytes.length > 4 * 1024 * 1024 || digest(bytes) !== expectedSha256)
        throw Error('Summary differs from the approved SHA-256 or exceeds the archive bound');
    const summary = JSON.parse(bytes.toString('utf8'));
    if (summary?.complete !== true || !/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$/.test(summary.id)
        || typeof summary.id !== 'string' || typeof summary.protocol?.id !== 'string'
        || ![1, 5].includes(summary.protocol.repetitions)
        || !summary.stages || typeof summary.stages !== 'object'
        || !summary.paired_comparisons || typeof summary.paired_comparisons !== 'object'
        || !Array.isArray(summary.per_run))
        throw Error('A completed registered SIM summary is required');
    const assignments = new Set(summary.per_run.map((row: Summary['per_run'][number]) => {
        if (!row || !Number.isInteger(row.rep) || row.rep < 1 || row.rep > summary.protocol.repetitions
            || !CONDITIONS.some(condition => row.condition === condition))
            throw Error('Invalid SIM run assignment');
        return row.rep + ':' + row.condition;
    }));
    if (assignments.size !== CONDITIONS.length * summary.protocol.repetitions
        || assignments.size !== summary.per_run.length)
        throw Error('Missing or repeated SIM condition assignment');
    return summary;
}

export async function publish(file: string, expectedSha256: string) {
    if (basename(file) !== 'summary.json')
        throw Error('Provide the completed analysis summary.json');
    const bytes = await readFile(file);
    const summary = approvedSummary(bytes, expectedSha256);
    const db = pg(), source = 'observatory-sim-analysis:' + summary.id;
    const importId = 'native:' + source, taskId = source + ':task';
    const experimentId = source + ':experiment', evaluationId = source + ':evaluation';
    const title = 'Self-improvement memory ablation';
    const link = '/experiments?range=all&project=' + encodeURIComponent(PROJECT_ID);

    await rawHealth();
    return db.begin(async tx => {
        await tx `SELECT pg_advisory_xact_lock(hashtext(${importId}))`;
        const [prior] = await tx`SELECT archive_id, manifest, finished_at FROM migration_manifests WHERE id=${importId}`;
        if (prior) {
            const rows = await tx`SELECT table_name,jsonb_typeof(record) AS value_type
                FROM archived_records WHERE import_id=${importId} ORDER BY table_name`;
            if (rows.length !== 2 || rows.some(row => row.value_type !== 'object'))
                throw Error('SIM publication projection needs repair');
            if (!prior.finished_at || !prior.archive_id || prior.manifest?.sha256 !== expectedSha256
                || !(await restoreRaw(prior.archive_id)).equals(bytes))
                throw Error('Immutable SIM publication conflicts with the approved summary');
            return { status: 'already_published', experimentId, evaluationId, projectId: PROJECT_ID, link,
                archiveId: prior.archive_id, sha256: expectedSha256 };
        }
        const artifact = await retainRaw(bytes, 'observatory-experiment-summary', source);
        if (artifact.sha256 !== expectedSha256 || !(await restoreRaw(artifact.id)).equals(bytes))
            throw Error('Local S3 summary read-back did not match the approved bytes');

        const created = new Date().toISOString();
        const manifest = { kind: 'native-experiment-summary', id: summary.id, sha256: artifact.sha256,
            evaluationId, source: 'Observatory independent SIM analysis' };
        const proposal = { id: experimentId, task_id: taskId, created,
            proposal: { title, change: 'Vary the frozen historical experience projected into the harness optimizer.',
                implementation: 'executed', metrics: 'Binary held-out success and total optimization resources, paired by repetition.',
                decision: 'unrecorded' } };
        const evaluation = { id: evaluationId, experiment_id: experimentId, created, artifact_sha256: artifact.sha256,
            protocol: summary.protocol, measurements: summary };
        await tx `INSERT INTO projects(id,name,repo,scope)
            VALUES(${PROJECT_ID},'Observatory SIM memory ablation',${projectRoot},
                   'Native coding harness optimization and historical memory ablations') ON CONFLICT(id) DO NOTHING`;
        await tx `INSERT INTO tasks(id,project_id,title,goal,acceptance,status,outcome,source)
            VALUES(${taskId},${PROJECT_ID},${title},'Measure the effect of historical experiment memory on held-out repairs.',
                   'All frozen condition assignments complete and independently graded.',
                   'completed','Complete paired aggregate retained in the verified local archive.',
                   ${tx.json({ artifact_id: artifact.id, protocol: summary.protocol.id })})`;
        await tx `INSERT INTO migration_manifests(id,source,finished_at,manifest,archive_id)
            VALUES(${importId},${source},now(),${tx.json(manifest)},${artifact.id})`;
        for (const [table, record] of [['experiments', proposal], ['experiment_evaluations', evaluation]] as const)
            await tx `INSERT INTO archived_records(import_id,table_name,row_number,record)
                VALUES(${importId},${table},0,${tx.json(record)})`;
        await tx `INSERT INTO audit(action,entity,details)
            VALUES('publish-native-experiment',${experimentId},${tx.json(manifest)})`;
        return { status: 'published', experimentId, evaluationId, projectId: PROJECT_ID, link,
            archiveId: artifact.id, sha256: expectedSha256 };
    });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
    const [, , file, sha] = process.argv;
    if (!file || !sha || process.argv.length !== 4) {
        console.error('Usage: publish-sim-analysis.ts /path/to/summary.json APPROVED_SHA256');
        process.exitCode = 2;
    } else {
        try {
            console.log(JSON.stringify(await publish(file, sha)));
        } finally {
            await closeDatabases();
        }
    }
}
