import { hash, iso, turnKey, finite } from './domain.ts';
type Obj = Record<string, any>;
export interface ParsedSource {
    events: Obj[];
    turns: Obj[];
    malformed: number;
}
export function parseNative(text: string, provider: 'codex' | 'claude', source: string): ParsedSource {
    const records: Obj[] = [];
    let malformed = 0;
    for (const [line, raw] of text.split('\n').entries()) {
        if (!raw.trim())
            continue;
        if (Buffer.byteLength(raw) > 8 * 1024 * 1024) {
            malformed++;
            continue;
        }
        try {
            records.push({ ...JSON.parse(raw), _line: line + 1 });
        }
        catch {
            malformed++;
        }
    }
    const events: Obj[] = [], turns = new Map<string, Obj>();
    let sid = '', workspace = '', model = '', currentTurn = '', role = '', agent = '';
    const ensure = (turn: string, at: unknown, prompt = '') => {
        const key = turnKey(sid, turn), time = iso(at);
        let t = turns.get(key);
        if (!t) {
            t = { turn_key: key, session_id: sid, turn_id: turn, workspace, prompt: '', started_at: time, finished_at: time, completed: false, role, agent_type: agent, source: { path: source } };
            turns.set(key, t);
        }
        if (time) {
            if (!t.started_at || time < t.started_at)
                t.started_at = time;
            if (!t.finished_at || time > t.finished_at)
                t.finished_at = time;
        }
        if (prompt && !t.prompt.includes(prompt))
            t.prompt += (t.prompt ? '\n' : '') + prompt;
        return t;
    };
    if (provider === 'codex') {
        const meta = records.find(r => r.type === 'session_meta')?.payload || {};
        sid = meta.id;
        if (!sid)
            throw Error('No native session identity');
        workspace = meta.cwd || '';
        role = typeof meta.source === 'string' && ['cli', 'exec', 'vscode'].includes(meta.source) ? 'main' : meta.source?.subagent ? 'sub' : '';
        agent = meta.source?.subagent?.thread_spawn?.agent_role || '';
        for (const r of records) {
            const p = r.payload || {};
            if (p.thread_id && p.thread_id !== sid)
                continue;
            if (meta.timestamp && r.timestamp < meta.timestamp)
                continue;
            if (r.type === 'turn_context')
                model = p.model || model;
            const turn = p.turn_id;
            if (!turn)
                continue;
            const t = ensure(turn, r.timestamp), item = p.item || {};
            if (item.type === 'UserMessage')
                ensure(turn, r.timestamp, (item.content || []).filter((v: Obj) => v.type === 'text').map((v: Obj) => v.text || '').join('\n'));
            const signal = ['turn_aborted', 'turn_cancelled', 'task_interrupted', 'interrupt'].includes(p.type) ? 'interrupt' : p.type === 'approval_rejected' || ['denied', 'rejected', 'approval_denied'].includes(item.status) ? 'rejected' : null;
            if (signal) {
                t.source.signals ??= [];
                t.source.signals.push({ kind: signal, event_id: item.id ? sid + ':tool:' + item.id : null, detail: String(p.reason || item.error || item.status || p.type).slice(0, 2000) });
            }
            if (p.type === 'task_complete')
                t.completed = true;
            const base = { session_id: sid, turn_id: turn, workspace, event_time: iso(r.timestamp), role, agent_type: agent, source_path: source, source_line: r._line, payload: JSON.stringify(r) };
            if (r.type === 'token_usage_record' && p.response_id) {
                const u = p.usage || {};
                if (!['input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens'].every(k => Number.isInteger(u[k]) && u[k] >= 0))
                    throw Error('Incomplete native response counters');
                events.push({ ...base, id: sid + ':response:' + p.response_id, kind: 'generation', name: 'Model response', model, input_tokens: u.input_tokens, cached_tokens: u.cached_input_tokens, output_tokens: u.output_tokens, total_tokens: u.total_tokens, cache_write_tokens: finite(u.cache_creation_input_tokens), cache_5m_tokens: finite(u.cache_creation_5m_input_tokens) });
            }
            if (p.type === 'item_completed' && ['CommandExecution', 'McpToolCall', 'DynamicToolCall', 'FileChange', 'WebSearch', 'ImageView', 'Extension'].includes(item.type)) {
                const output = item.aggregated_output ?? item.result, serialized = typeof output === 'string' ? output : output == null ? '' : JSON.stringify(output), duration = item.duration;
                const runtime = typeof duration === 'number' ? finite(duration) : duration && typeof duration.secs === 'number' ? duration.secs + (duration.nanos || 0) / 1e9 : null;
                const name = item.type === 'CommandExecution' ? 'Bash' : item.tool || item.name || item.type;
                const failed = typeof item.exit_code === 'number' ? (item.exit_code === 0 ? 0 : 1) : ['failed', 'error'].includes(item.status) ? 1 : ['completed', 'success'].includes(item.status) ? 0 : null;
                events.push({ ...base, id: sid + ':tool:' + item.id, kind: 'tool', name, command: typeof item.command === 'string' ? item.command : Array.isArray(item.command) ? item.command.join(' ') : '', runtime, runtime_role: item.background ? 'background_service_lifetime' : 'operation', failed, output_excerpt: serialized.slice(0, 64000), output_chars: output == null ? null : serialized.length, output_hash: output == null ? '' : hash(serialized) });
            }
            if (['AssistantMessage', 'AgentMessage', 'assistant_message'].includes(item.type) && p.type === 'item_completed') {
                t.source.last_message = item.content ?? item.text ?? '';
                if (item.phase === 'final_answer') {
                    const content = t.source.last_message;
                    if (typeof content === 'string')
                        t.source.answer_chars = content.length;
                    else if (Array.isArray(content) && content.every(v => ['text', 'output_text'].includes(v.type) && typeof v.text === 'string'))
                        t.source.answer_chars = content.reduce((n, v) => n + v.text.length, 0);
                }
            }
        }
    }
    else {
        const meta = records.find(r => r.sessionId);
        sid = meta?.sessionId;
        if (!sid)
            throw Error('No Claude session identity');
        workspace = meta?.cwd || '';
        const toolUses = new Map<string, Obj>();
        for (const r of records) {
            if (r.sessionId && r.sessionId !== sid)
                continue;
            const message = r.message || {}, content = Array.isArray(message.content) ? message.content : [], at = iso(r.timestamp);
            if (r.type === 'user' && typeof message.content === 'string') {
                currentTurn = r.uuid || hash([sid, r._line]);
                ensure(currentTurn, at, message.content);
            }
            if (r.type === 'user' && content.some((b: Obj) => b.type === 'text')) {
                currentTurn = r.uuid || hash([sid, r._line]);
                ensure(currentTurn, at, content.filter((b: Obj) => b.type === 'text').map((b: Obj) => b.text).join('\n'));
            }
            if (!currentTurn)
                currentTurn = 'unattributed';
            const t = ensure(currentTurn, at), base = { session_id: sid, turn_id: currentTurn, workspace, event_time: at, role: r.agentId || r.isSidechain === true ? 'sub' : r.isSidechain === false ? 'main' : '', agent_type: r.agentId ? 'Unknown subagent' : '', source_path: source, source_line: r._line, payload: JSON.stringify(r) };
            if (r.type === 'assistant' && message.id && message.usage) {
                const u = message.stop_reason != null ? message.usage : {}, read = finite(u.cache_read_input_tokens), write = finite(u.cache_creation_input_tokens), input = finite(u.input_tokens), output = finite(u.output_tokens);
                events.push({ ...base, id: sid + ':response:' + message.id, kind: 'generation', name: 'Model response', model: message.model || '', input_tokens: input != null && read != null && write != null ? input + read + write : null, cached_tokens: read, cache_write_tokens: write, cache_5m_tokens: finite(u.cache_creation?.ephemeral_5m_input_tokens), output_tokens: output, total_tokens: input != null && read != null && write != null && output != null ? input + read + write + output : null });
                t.source.last_message = content.filter((v: Obj) => v.type === 'text').map((v: Obj) => v.text).join('\n');
                if (message.stop_reason === 'end_turn') {
                    t.completed = true;
                    if (content.every((v: Obj) => v.type === 'text' && typeof v.text === 'string'))
                        t.source.answer_chars = t.source.last_message.length;
                }
            }
            for (const b of content) {
                if (b.type === 'tool_use')
                    toolUses.set(b.id, { ...base, id: sid + ':tool:' + b.id, kind: 'tool', name: b.name, command: typeof b.input?.command === 'string' ? b.input.command : '', payload: JSON.stringify({ request: r, input: b.input }) });
                if (b.type === 'tool_result' && toolUses.has(b.tool_use_id)) {
                    const use = toolUses.get(b.tool_use_id)!, output = typeof b.content === 'string' ? b.content : JSON.stringify(b.content);
                    events.push({ ...use, payload: JSON.stringify({ request: JSON.parse(use.payload), result: r }), failed: typeof b.is_error === 'boolean' ? Number(b.is_error) : null, output_excerpt: output?.slice(0, 64000) || '', output_chars: output?.length ?? null, output_hash: output == null ? '' : hash(output) });
                }
            }
        }
    }
    const unique = new Map<string, Obj>();
    for (const event of events) {
        const previous = unique.get(event.id);
        if (!previous) {
            unique.set(event.id, event);
            continue;
        }
        if (previous.session_id !== event.session_id || previous.turn_id !== event.turn_id)
            throw Error('Native event identity has conflicting ownership');
        const keys = ['input_tokens', 'cached_tokens', 'output_tokens', 'total_tokens'];
        if (event.kind === 'generation') {
            if (keys.some(k => previous[k] != null && event[k] != null && previous[k] !== event[k]))
                throw Error('Conflicting native response usage');
            if (keys.some(k => previous[k] == null && event[k] != null))
                unique.set(event.id, { ...event, event_time: previous.event_time, source_line: previous.source_line });
        }
    }
    return { events: [...unique.values()], turns: [...turns.values()], malformed };
}
