import { glob } from './glob.ts';
import { isValidationCommand } from './validation-command.ts';
import { z } from 'zod';
import { timingSafeEqual } from 'node:crypto';
import { pg } from './database.ts';
import { hash } from './domain.ts';
const inputSchema = z.object({ session_id: z.string().min(1).max(300), event_id: z.string().min(1).max(300), event: z.enum(['start', 'prompt', 'pre_tool', 'post_tool', 'stop']), workspace: z.string().max(3000).default(''), task_id: z.string().max(300).optional(), turn_id: z.string().max(300).optional(), tool: z.string().max(300).default(''), command: z.string().max(16000).default(''), failed: z.boolean().optional(), task_cost_usd: z.number().finite().nonnegative().optional(), session_cost_usd: z.number().finite().nonnegative().optional(), context_tokens: z.number().int().nonnegative().optional(), main_repo: z.boolean().default(false) });
export function tokenMatches(value: string | null) {
    const token = process.env.OBS_INGEST_TOKEN;
    if (!token || !value?.startsWith('Bearer '))
        return false;
    const a = Buffer.from(value.slice(7)), b = Buffer.from(token);
    return a.length === b.length && timingSafeEqual(a, b);
}
const priority: Record<string, number> = { allow: 0, log: 0, warn: 1, ask: 2, block: 3 };
export async function receiveHook(raw: unknown) {
    const input = inputSchema.parse(raw), db = pg(), digest = hash(input), now = new Date(), stamp = +now, eventId = input.session_id + ':' + input.event_id;
    return db.begin(async (tx) => {
        await tx `SELECT pg_advisory_xact_lock(hashtext(${input.session_id}))`;
        const previousEvent = await tx `SELECT payload_hash,response FROM steering_events WHERE id=${eventId}`;
        if (previousEvent.length) {
            if (previousEvent[0].payload_hash !== digest)
                throw Error('Hook event identity conflicts with recorded content');
            return previousEvent[0].response;
        }
        const previous = (await tx `SELECT * FROM live_sessions WHERE id=${input.session_id} FOR UPDATE`)[0];
        const state: Record<string, unknown> = { ...(previous?.state || {}) }, task = input.task_id || input.turn_id || 'session';
        const signature = hash([input.tool, input.command]);
        if (input.event === 'post_tool') {
            if (input.failed === true) {
                state.failures = state.last_signature === signature ? Number(state.failures || 0) + 1 : 1;
                state.last_signature = signature;
            }
            else {
                state.failures = 0;
                state.last_signature = signature;
            }
            if (/edit|write|filechange/i.test(input.tool))
                state.last_edit = stamp;
            if (input.failed === false && !/[;|]/.test(input.command) && isValidationCommand(input.command))
                state.last_check = stamp;
        }
        const day = now.toISOString().slice(0, 10);
        if (state.cost_day !== day) {
            state.cost_day = day;
            state.cost_day_base = input.session_cost_usd ?? null;
        }
        if (input.session_cost_usd != null)
            state.session_cost_usd = input.session_cost_usd;
        const status = previous?.paused ? 'paused' : input.event === 'stop' ? 'waiting' : 'working';
        await tx `INSERT INTO live_sessions(id,workspace,last_seen,status,paused,task_id,task_cost,context_tokens,state) VALUES(${input.session_id},${input.workspace},${now},${status},${previous?.paused || false},${input.task_id || null},${input.task_cost_usd ?? previous?.task_cost ?? null},${input.context_tokens ?? previous?.context_tokens ?? null},${tx.json(state)}) ON CONFLICT(id) DO UPDATE SET workspace=EXCLUDED.workspace,last_seen=EXCLUDED.last_seen,status=EXCLUDED.status,task_id=coalesce(EXCLUDED.task_id,live_sessions.task_id),task_cost=EXCLUDED.task_cost,context_tokens=EXCLUDED.context_tokens,state=EXCLUDED.state`;
        const rules = await tx `SELECT * FROM steering_rules WHERE enabled ORDER BY builtin DESC,id`, messages: {
            rule: string;
            mode: string;
            message: string;
        }[] = [];
        let decision = 'allow';
        if (previous?.paused && input.event === 'pre_tool') {
            decision = 'block';
            messages.push({ rule: 'Session paused', mode: 'block', message: 'This session is paused in Observatory. Resume it before the next tool call.' });
            await tx `INSERT INTO steering_log(id,session_id,at,rule_name,mode,message,workspace,event_id,task_id) VALUES(${hash([eventId, 'pause'])},${input.session_id},${now},'Session paused','block','Session paused in Observatory',${input.workspace},${eventId},${input.task_id || null})`;
        }
        for (const rule of rules) {
            const config = rule.config as Record<string, unknown>, saved = (await tx `SELECT value FROM steering_state WHERE session_id=${input.session_id} AND rule_id=${rule.id}`)[0]?.value || {}, value: Record<string, unknown> = { ...saved };
            let fired = false;
            if (rule.kind === 'break' && input.event === 'prompt' && previous)
                fired = stamp - +new Date(previous.last_seen) >= Number(config.minutes || 60) * 60000;
            if (rule.kind === 'task_budget' && input.task_cost_usd != null) {
                const threshold = Math.floor(input.task_cost_usd / Number(config.amount || 5));
                fired = threshold > 0 && (value.task !== task || threshold > Number(value.threshold || 0));
                if (fired) {
                    value.task = task;
                    value.threshold = threshold;
                }
            }
            if (rule.kind === 'daily_budget' && input.session_cost_usd != null) {
                await tx `SELECT pg_advisory_xact_lock(846205212)`;
                const daily = (await tx `SELECT sum(greatest(0,(state->>'session_cost_usd')::float8-(state->>'cost_day_base')::float8)) AS cost FROM live_sessions WHERE state->>'cost_day'=${day}`)[0]?.cost;
                const global = (await tx `SELECT value FROM steering_state WHERE session_id='__global' AND rule_id=${rule.id}`)[0]?.value || {}, threshold = Math.floor(Number(daily || 0) / Number(config.amount || 100));
                fired = threshold > 0 && (global.day !== day || threshold > Number(global.threshold || 0));
                if (fired)
                    await tx `INSERT INTO steering_state(session_id,rule_id,value) VALUES('__global',${rule.id},${tx.json({ day, threshold })}) ON CONFLICT(session_id,rule_id) DO UPDATE SET value=EXCLUDED.value`;
            }
            if (rule.kind === 'context' && input.context_tokens != null && input.context_tokens >= Number(config.tokens || 200000) && value.task !== task) {
                fired = true;
                value.task = task;
            }
            if (rule.kind === 'failure_loop' && input.event === 'post_tool')
                fired = input.failed === true && Number(state.failures) === Number(config.count || 3);
            if (rule.kind === 'stop_check' && input.event === 'stop')
                fired = Number(state.last_edit || 0) > Number(state.last_check || 0);
            if (rule.kind === 'command' && input.event === 'pre_tool') {
                const check = config.check, cmd = input.command.toLowerCase(), tool = input.tool.toLowerCase();
                fired = check === 'main-checkout' ? input.main_repo && /\bgit\s+(?:-\S+\s+)*(checkout|switch)\b/i.test(input.command) : check === 'public-registry' ? /registry\.npmjs\.org|registry\.yarnpkg\.com/.test(cmd) : check === 'claude-attribution' ? /co-authored-by:.*(claude|anthropic)/i.test(input.command) : check === 'external-writes' ? /servicenow|jira|confluence|salesforce/.test(tool) && /create|update|delete|upload/.test(tool) : check === 'shell-exploration' ? /bash|shell|commandexecution/.test(tool) && /\b(cat|head|tail|sed|find|grep|ls)\b/.test(cmd) : (!config.main_only || input.main_repo) && (!config.workspace || glob(String(config.workspace), input.workspace)) && (!config.tool || glob(String(config.tool), input.tool)) && Boolean(config.pattern) && (config.matcher === 'glob' ? glob(String(config.pattern), input.command) : input.command.includes(String(config.pattern)));
            }
            if (!fired)
                continue;
            const message = String(rule.message || rule.name), mode = String(rule.mode);
            messages.push({ rule: String(rule.name), mode, message });
            if (priority[mode] > priority[decision])
                decision = mode;
            await tx `INSERT INTO steering_state(session_id,rule_id,value) VALUES(${input.session_id},${rule.id},${tx.json(value)}) ON CONFLICT(session_id,rule_id) DO UPDATE SET value=EXCLUDED.value`;
            await tx `INSERT INTO steering_log(id,session_id,at,rule_id,rule_name,mode,message,call,workspace,event_id,task_id) VALUES(${hash([eventId, rule.id])},${input.session_id},${now},${rule.id},${rule.name},${mode},${message},${(input.tool + ' ' + input.command).slice(0, 4000)},${input.workspace},${eventId},${input.task_id || null})`;
        }
        const notes = await tx `UPDATE steering_notes SET delivered_at=${now} WHERE session_id=${input.session_id} AND delivered_at IS NULL RETURNING id,message`;
        for (const note of notes)
            await tx `INSERT INTO steering_log(id,session_id,at,rule_name,mode,message,call,workspace,event_id,task_id) VALUES(${hash([eventId, note.id])},${input.session_id},${now},'Steering note','note',${note.message},'',${input.workspace},${eventId},${input.task_id || null})`;
        const response = { decision, messages, notes: notes.map(n => ({ id: n.id, message: n.message })) };
        await tx `INSERT INTO steering_events(id,session_id,payload_hash,response) VALUES(${eventId},${input.session_id},${digest},${tx.json(response)})`;
        return response;
    });
}
