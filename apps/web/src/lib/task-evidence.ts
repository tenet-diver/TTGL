import { isValidationCommand } from './validation-command.ts';
import type { NativeEvent, Row } from './types.ts';
export function nativeEvidence(events: NativeEvent[]) {
    const notes: Row[] = [];
    for (const e of events) {
        if (e.kind === 'tool' && isValidationCommand(e.command))
            notes.push({ id: 'native:' + e.id, kind: 'validation', title: e.command.slice(0, 500), detail: 'Recorded tool outcome; command completion alone does not establish task acceptance.', outcome: /[;|]/.test(e.command) ? 'unknown' : e.failed === 0 ? 'passed' : e.failed === 1 ? 'failed' : 'unknown', event_id: e.id, at: e.time_known ? e.event_time : null });
        if (e.kind === 'tool' && /filechange|file_change/i.test(e.name) && e.failed === 0) {
            let record: Record<string, any> = {};
            try {
                record = JSON.parse(e.payload);
            }
            catch { }
            const changes = record.payload?.item?.changes;
            const paths = Array.isArray(changes) ? changes.map(c => c.path) : changes && typeof changes === 'object' ? Object.entries(changes).map(([key, value]) => (value as Record<string, unknown>)?.path || key) : [];
            notes.push({ id: 'native-change:' + e.id, kind: 'change', title: paths.length ? `${paths.length} files changed` : 'Recorded file change', detail: paths.filter(p => typeof p === 'string').join('\n').slice(0, 8000), outcome: 'confirmed', event_id: e.id, at: e.time_known ? e.event_time : null });
        }
    }
    return notes;
}
