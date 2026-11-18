import { subscriptionBinding } from './execution-policy.ts';
import { z } from 'zod';
import { randomUUID } from 'node:crypto';
import path from 'node:path';
import { pg } from './database.ts';
import { invalidate } from './repository.ts';
import { hash } from './domain.ts';
import { queueTask, queueBatch } from './jobs.ts';
import { metricDefinitions } from './impact.ts';
import { pricingSchema } from './pricing.ts';
const id = z.string().min(1).max(400), name = z.string().trim().min(1).max(200), message = z.string().trim().min(1).max(8000), config = z.record(z.string(), z.json());
const scopeFields = { project: z.string().default(''), workspace: z.string().default(''), range: z.enum(['1d', '7d', '30d', '90d', 'all']).default('all') };
export async function performAction(input: unknown, receiptId: string) {
    z.string().uuid().parse(receiptId);
    const head = z.object({ action: z.string().max(50) }).parse(input), body = input as Record<string, unknown>, db = pg(), digest = hash(body);
    const result = await db.begin(async (tx) => {
        await tx `SELECT pg_advisory_xact_lock(hashtext(${receiptId}))`;
        const saved = (await tx `SELECT request_hash,response FROM mutation_receipts WHERE id=${receiptId}`)[0];
        if (saved) {
            if (saved.request_hash !== digest)
                throw Error('This request identity was already used for different content');
            return saved.response;
        }
        let response: Record<string, unknown> = {};
        let entity = String(body.id || '');
        if (head.action === 'project') {
            const v = z.object({ name, repo: z.string().trim().min(1).max(3000), scope: z.string().max(8000).default('') }).parse(body);
            entity = randomUUID();
            await tx `INSERT INTO projects(id,name,repo,scope) VALUES(${entity},${v.name},${v.repo},${v.scope})`;
            response = { id: entity };
        }
        else if (head.action === 'task') {
            const v = z.object({ title: name, goal: message, acceptance: z.string().max(8000).default(''), project_id: id }).parse(body);
            entity = randomUUID();
            await tx `INSERT INTO tasks(id,project_id,title,goal,acceptance) VALUES(${entity},${v.project_id},${v.title},${v.goal},${v.acceptance})`;
            response = { id: entity };
        }
        else if (head.action === 'assign') {
            const v = z.object({ task_id: id, turn_keys: z.array(id).min(1).max(10000) }).parse(body);
            if (!(await tx `SELECT id FROM tasks WHERE id=${v.task_id}`).length)
                throw Error('Unknown target task');
            for (const key of new Set(v.turn_keys)) {
                if (!(await tx `SELECT turn_key FROM turns WHERE turn_key=${key}`).length)
                    throw Error('Unknown native turn');
                const assigned = (await tx `SELECT task_id FROM assignments WHERE turn_key=${key}`)[0];
                if (assigned && assigned.task_id !== v.task_id) {
                    const [previous] = await tx `SELECT source FROM tasks WHERE id=${assigned.task_id}`;
                    if (!previous?.source?.native_turn)
                        throw Error('A selected turn is already assigned to a different defined task. Reconcile its existing assignment first.');
                    await tx `UPDATE assignments SET task_id=${v.task_id} WHERE turn_key=${key}`;
                    await tx `INSERT INTO audit(action,entity,details) VALUES('native_turn_grouped',${key},${tx.json({ from: assigned.task_id, to: v.task_id })})`;
                }
                await tx `INSERT INTO assignments(turn_key,task_id) VALUES(${key},${v.task_id}) ON CONFLICT DO NOTHING`;
            }
            await tx `UPDATE tasks SET updated_at=now() WHERE id=${v.task_id}`;
            entity = v.task_id;
            response = { assigned: new Set(v.turn_keys).size };
        }
        else if (head.action === 'rule') {
            const v = z.object({ id: id.optional(), name: name.optional(), kind: z.enum(['break', 'task_budget', 'daily_budget', 'context', 'failure_loop', 'stop_check', 'command']).optional(), mode: z.enum(['log', 'warn', 'ask', 'block']).optional(), enabled: z.boolean().optional(), config: config.optional(), message: z.string().max(8000).optional() }).parse(body), previous = v.id ? (await tx `SELECT * FROM steering_rules WHERE id=${v.id} FOR UPDATE`)[0] : null;
            if (v.id && !previous)
                throw Error('Unknown steering rule');
            const record = { ...previous, ...v };
            if (!record.name || !record.kind)
                throw Error('Rule name and trigger are required');
            entity = v.id || randomUUID();
            const cfg = record.config || {};
            for (const key of ['minutes', 'amount', 'tokens', 'count'])
                if (cfg[key] != null && (!(typeof cfg[key] === 'number') || !Number.isFinite(cfg[key]) || cfg[key] <= 0))
                    throw Error('Rule thresholds must be positive numbers');
            if (record.kind === 'command' && !cfg.check && !String(cfg.pattern || '').trim())
                throw Error('A literal command pattern is required');
            await tx `INSERT INTO steering_rules(id,name,kind,mode,enabled,builtin,config,message) VALUES(${entity},${record.name},${record.kind},${record.mode || 'warn'},${record.enabled ?? true},${previous?.builtin || false},${tx.json(cfg)},${record.message || ''}) ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name,kind=EXCLUDED.kind,mode=EXCLUDED.mode,enabled=EXCLUDED.enabled,config=EXCLUDED.config,message=EXCLUDED.message`;
            response = { id: entity };
        }
        else if (head.action === 'delete-rule') {
            const v = z.object({ id }).parse(body);
            const row = (await tx `SELECT * FROM steering_rules WHERE id=${v.id} FOR UPDATE`)[0];
            if (!row)
                throw Error('Unknown rule');
            if (row.builtin)
                throw Error('Built-in rules can be disabled but not deleted');
            await tx `DELETE FROM steering_rules WHERE id=${v.id}`;
            entity = v.id;
            response = { deleted: true };
        }
        else if (head.action === 'categorization') {
            const v = z.object({ id: id.optional(), name, pattern: z.string().min(1).max(1000), category: name, activity_type: z.enum(['productive', 'overhead', 'waiting', 'uncategorized']).default('uncategorized'), priority: z.number().int().min(0).max(100000).default(100), enabled: z.boolean().default(true) }).parse(body);
            entity = v.id || randomUUID();
            await tx `INSERT INTO categorization_rules(id,name,pattern,category,activity_type,priority,enabled) VALUES(${entity},${v.name},${v.pattern},${v.category},${v.activity_type},${v.priority},${v.enabled}) ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name,pattern=EXCLUDED.pattern,category=EXCLUDED.category,activity_type=EXCLUDED.activity_type,priority=EXCLUDED.priority,enabled=EXCLUDED.enabled`;
            response = { id: entity };
        }
        else if (head.action === 'delete-categorization') {
            const v = z.object({ id }).parse(body);
            await tx `DELETE FROM categorization_rules WHERE id=${v.id}`;
            entity = v.id;
            response = { deleted: true };
        }
        else if (head.action === 'change') {
            const v = z.object({ title: name, applied_at: z.iso.datetime(), workspace: z.string().max(3000).default(''), takes_effect: z.enum(['immediate', 'new_sessions']).default('immediate'), metrics: z.array(z.string()).min(1).max(20), notes: z.string().max(8000).default('') }).parse(body);
            if (v.metrics.some(m => !metricDefinitions.some(def => def.id === m)))
                throw Error('Unknown impact metric');
            entity = randomUUID();
            await tx `INSERT INTO applied_changes(id,title,applied_at,workspace,takes_effect,metrics,notes) VALUES(${entity},${v.title},${v.applied_at},${v.workspace},${v.takes_effect},${v.metrics},${v.notes})`;
            response = { id: entity };
        }
        else if (head.action === 'delete-change') {
            const v = z.object({ id }).parse(body);
            await tx `DELETE FROM applied_changes WHERE id=${v.id}`;
            entity = v.id;
            response = { deleted: true };
        }
        else if (head.action === 'note') {
            const v = z.object({ session_id: id, message }).parse(body);
            entity = randomUUID();
            if (!(await tx `SELECT id FROM live_sessions WHERE id=${v.session_id}`).length)
                throw Error('Unknown live session');
            await tx `INSERT INTO steering_notes(id,session_id,message) VALUES(${entity},${v.session_id},${v.message})`;
            response = { id: entity };
        }
        else if (head.action === 'session') {
            const v = z.object({ id, paused: z.boolean() }).parse(body);
            await tx `UPDATE live_sessions SET paused=${v.paused},status=${v.paused ? 'paused' : 'working'} WHERE id=${v.id}`;
            entity = v.id;
            response = { paused: v.paused };
        }
        else if (head.action === 'pricing') {
            const v = z.object({ pricing: pricingSchema, model_tiers: z.object({ top: z.array(z.string()).max(100), small: z.array(z.string()).max(100) }).default({ top: [], small: [] }) }).parse(body);
            await tx `INSERT INTO settings(key,value) VALUES('pricing',${tx.json(v.pricing)}),('model_tiers',${tx.json(v.model_tiers)}) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value,updated_at=now()`;
            response = { saved: true };
        }
        else if (head.action === 'source-root') {
            const v = z.object({ path: z.string().min(1).max(3000), provider: z.enum(['codex', 'claude']), codex_home: z.string().max(3000).optional() }).parse(body);
            if (!path.isAbsolute(v.path))
                throw Error('Choose an absolute source folder path');
            if (v.codex_home && !path.isAbsolute(v.codex_home))
                throw Error('Codex home must be an absolute local path');
            if (v.codex_home) v.codex_home = (await subscriptionBinding(v.codex_home)).codex_home;
            const previous = (await tx `SELECT value FROM settings WHERE key='source_roots' FOR UPDATE`)[0]?.value || [];
            if (previous.length >= 10)
                throw Error('At most ten source folders are supported');
            const roots = [...previous.filter((r: {
                    path: string;
                }) => r.path !== v.path), v];
            await tx `INSERT INTO settings(key,value) VALUES('source_roots',${tx.json(roots)}),('collection_enabled','true') ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value`;
            response = { saved: true };
        }
        else if (head.action === 'analyze') {
            const v = z.object({ task_id: id, ...scopeFields }).parse(body);
            response = await queueTask(tx, v.task_id, { project: v.project, workspace: v.workspace, range: v.range, timezone: 'UTC' });
            entity = v.task_id;
        }
        else if (head.action === 'analysis-batch') {
            const v = z.object(scopeFields).parse(body);
            response = await queueBatch(tx, { ...v, timezone: 'UTC' });
            entity = String(response.id);
        }
        else if (head.action === 'task-status') {
            const v = z.object({ id, status: z.enum(['active', 'waiting', 'completed']), outcome: z.string().max(8000).optional() }).parse(body);
            if (v.status === 'completed' && !v.outcome?.trim())
                throw Error('Record acceptance evidence before marking this task complete');
            const [previous] = await tx `SELECT status,outcome FROM tasks WHERE id=${v.id} FOR UPDATE`;
            if (!previous)
                throw Error('Unknown task');
            await tx `INSERT INTO audit(action,entity,details) VALUES('task_outcome_recorded',${v.id},${tx.json({ before: previous, after: { status: v.status, outcome: v.outcome || null }, basis: 'Explicit user record; not independently verified' })})`;
            await tx `UPDATE tasks SET status=${v.status},outcome=${v.outcome || null},updated_at=now() WHERE id=${v.id}`;
            entity = v.id;
            response = { saved: true };
        }
        else if (head.action === 'evidence') {
            const v = z.object({ task_id: id, kind: z.enum(['change', 'validation', 'visual_reference', 'intervention']), title: name, detail: z.string().max(8000).default(''), outcome: z.enum(['unknown', 'passed', 'failed', 'confirmed', 'not_applicable']).default('unknown'), reference: z.string().max(2000).default('') }).parse(body);
            if (v.reference) {
                const u = new URL(v.reference);
                if (!['http:', 'https:'].includes(u.protocol) || u.username || u.password)
                    throw Error('References must be HTTP(S) URLs without credentials');
            }
            entity = randomUUID();
            await tx `INSERT INTO evidence_notes(id,task_id,kind,title,detail,outcome,reference,source) VALUES(${entity},${v.task_id},${v.kind},${v.title},${v.detail},${v.outcome},${v.reference},'{"basis":"Explicit record; not independently verified"}')`;
            response = { id: entity };
        }
        else
            throw Error('Unknown action');
        await tx `INSERT INTO audit(action,entity,details) VALUES(${head.action},${entity},${tx.json({ request_id: receiptId, ...(head.action === 'note' ? { message_recorded: true } : {}) })})`;
        await tx `INSERT INTO mutation_receipts(id,request_hash,response) VALUES(${receiptId},${digest},${tx.json(response)})`;
        return response;
    });
    invalidate();
    return result;
}
