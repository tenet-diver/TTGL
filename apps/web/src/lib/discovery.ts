import { pg } from './database.ts';
import { hash } from './domain.ts';
/** A native turn is an observed boundary, not inferred acceptance or a model label. */
export async function discoverTurn(key: string) {
    return pg().begin(async (tx) => {
        await tx `SELECT pg_advisory_xact_lock(hashtext(${key}))`;
        const [turn] = await tx `SELECT * FROM turns WHERE turn_key=${key}`;
        if (!turn)
            throw Error('Unknown native turn');
        const [assigned] = await tx `SELECT task_id FROM assignments WHERE turn_key=${key}`;
        if (assigned) {
            const [task] = await tx `SELECT source FROM tasks WHERE id=${assigned.task_id}`;
            if (task?.source?.native_turn)
                await tx `UPDATE tasks SET title=${String(turn.prompt || 'Native turn ' + turn.turn_id).replace(/\s+/g, ' ').slice(0, 200)},goal=${turn.prompt || ''} WHERE id=${assigned.task_id}`;
            return String(assigned.task_id);
        }
        const projects = await tx `SELECT id,repo FROM projects ORDER BY length(repo) DESC,id`;
        const project = projects.find(p => Boolean(p.repo) && (turn.workspace === p.repo || turn.workspace.startsWith(String(p.repo).replace(/\/$/, '') + '/')));
        const id = 'native:' + hash(key), title = String(turn.prompt || 'Native turn ' + turn.turn_id).replace(/\s+/g, ' ').slice(0, 200);
        await tx `INSERT INTO tasks(id,project_id,title,goal,acceptance,status,source) VALUES(${id},${project?.id || null},${title},${turn.prompt || ''},'','observed',${tx.json({ native_turn: true, turn_key: key, basis: 'Observed native prompt boundary; acceptance unverified' })}) ON CONFLICT(id) DO UPDATE SET title=EXCLUDED.title,goal=EXCLUDED.goal,updated_at=now()`;
        await tx `INSERT INTO assignments(turn_key,task_id) VALUES(${key},${id}) ON CONFLICT DO NOTHING`;
        return id;
    });
}
