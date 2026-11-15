/** Split real elapsed spans at local date/offset boundaries without assuming 24-hour DST days. */
export function turnSegments(start: string, end: string | null, timezone: string) {
    const from = Date.parse(start), to = end ? Date.parse(end) : from;
    if (!Number.isFinite(from) || !Number.isFinite(to) || to < from)
        return [];
    const fmt = new Intl.DateTimeFormat('en-CA', { timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' });
    const local = (ms: number) => { const p = Object.fromEntries(fmt.formatToParts(ms).map(p => [p.type, p.value])); return { date: `${p.year}-${p.month}-${p.day}`, hour: Number(p.hour) + Number(p.minute) / 60 + Number(p.second) / 3600 }; };
    const result: {
        date: string;
        hour: number;
        hours: number;
    }[] = [];
    let cursor = from;
    const until = Math.min(to, from + 31 * 86400000);
    do {
        const next = Math.min(until, Math.floor(cursor / 60000) * 60000 + 60000), point = local(cursor), hours = (next - cursor) / 3600000, previous = result.at(-1);
        if (previous && previous.date === point.date && Math.abs(previous.hour + previous.hours - point.hour) < .0003)
            previous.hours += hours;
        else
            result.push({ ...point, hours });
        if (next === cursor)
            break;
        cursor = next;
    } while (cursor < until);
    return result;
}
