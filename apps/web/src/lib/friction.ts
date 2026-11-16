import { failureLoops } from './domain.ts';
import { isValidationCommand } from './validation-command.ts';
import type { NativeEvent } from './types.ts';
export function friction(events: NativeEvent[]) {
    const results = failureLoops(events), turns = new Map<string, NativeEvent[]>();
    for (const e of events) {
        if (!turns.has(e.turn_key))
            turns.set(e.turn_key, []);
        turns.get(e.turn_key)!.push(e);
    }
    for (const values of turns.values()) {
        const ordered = values.filter(e => e.time_known).toSorted((a, b) => a.event_time.localeCompare(b.event_time) || a.source_line - b.source_line);
        const tools = ordered.filter(e => e.kind === 'tool'), firstEdit = tools.findIndex(e => /^(edit|write|filechange|file_change)$/i.test(e.name));
        const before = firstEdit < 0 ? tools : tools.slice(0, firstEdit), reads = before.filter(e => /^(read|grep|glob|websearch)$/i.test(e.name) || /\b(bash|shell|commandexecution|exec_command)\b/i.test(e.name) && /(?:^|&&\s*)(?:cat|head|tail|sed|find|grep|rg|ls)\b/.test(e.command.trim()));
        if (reads.length >= 20)
            results.push({ ids: reads.map(e => e.id), type: 'Long explore before the first edit', detail: `${reads.length} recorded reads/searches before the first recorded edit; task quality remains unverified` });
        const gens = ordered.filter(e => e.kind === 'generation' && e.input_tokens != null);
        for (let i = 1; i < gens.length; i++) {
            const delta = Number(gens[i].input_tokens) - Number(gens[i - 1].input_tokens);
            if (delta >= 40000)
                results.push({ ids: [gens[i - 1].id, gens[i].id], type: 'Context jumped', detail: `Recorded input grew by ${delta.toLocaleString('en')} tokens in one call, to ${Number(gens[i].input_tokens).toLocaleString('en')}` });
        }
        let edited = false, cycles = 0, cycle: NativeEvent[] = [];
        for (const e of tools) {
            const edit = /^(edit|write|filechange|file_change)$/i.test(e.name), check = isValidationCommand(e.command);
            if (edit) {
                edited = true;
                cycle.push(e);
            }
            else if (check && e.failed === 1 && edited) {
                cycle.push(e);
                cycles++;
                edited = false;
                if (cycles === 3)
                    results.push({ ids: cycle.map(e => e.id), type: 'Edit/check failures repeated', detail: 'Three recorded edit → unsuccessful check cycles without a successful check' });
            }
            else if (check && e.failed === 0) {
                cycles = 0;
                edited = false;
                cycle = [];
            }
        }
    }
    return results;
}
