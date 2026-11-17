import { runExtraction } from '../src/lib/experience-extraction.ts';
import { flushExperienceOutbox } from '../src/lib/experience-store.ts';
import { closeDatabases } from '../src/lib/database.ts';
try {
    if (process.argv.includes('--flush')) {
        let count = 0, n; do { n = await flushExperienceOutbox(); count += n; } while (n);
        console.log(JSON.stringify({ delivered: count, modelCalls: 0 }));
    } else {
        const [projectId, experimentId, jobId] = process.argv.slice(2);
        if (!projectId || !experimentId || !jobId) throw Error('Usage: experience-worker.ts PROJECT STUDY JOB, or --flush');
        console.log(JSON.stringify(await runExtraction({ projectId, experimentId }, jobId)));
    }
} finally { await closeDatabases(); }
