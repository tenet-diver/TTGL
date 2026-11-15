import type { Row, Query } from './types.ts';
export const normalize = (value: unknown) => String(value ?? 'Unknown').normalize('NFKD').replace(/\p{M}/gu, '').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
export function collection(rows: Row[], query: Query, keys: string[]) {
    if (query.sort && !keys.includes(query.sort) || Object.keys(query.filters).some(k => !keys.includes(k)))
        throw Error('Unknown record column');
    const needle = normalize(query.search);
    let result = rows.filter(row => {
        const haystack = normalize(keys.map(k => typeof row[k] === 'object' ? JSON.stringify(row[k]) : row[k]).join(' '));
        if (needle && !haystack.includes(needle))
            return false;
        return Object.entries(query.filters).every(([key, input]) => {
            if (input.startsWith('==')) {
                try {
                    return JSON.stringify(row[key] ?? null) === JSON.stringify(JSON.parse(input.slice(2)));
                }
                catch {
                    return false;
                }
            }
            const match = input.trim().match(/^(<=|>=|!=|=|<|>)\s*(-?\d[\d,]*(?:\.\d+)?)$/), value = row[key];
            if (match) {
                const n = Number(match[2].replaceAll(',', ''));
                if (typeof value !== 'number' || !Number.isFinite(value))
                    return false;
                return ({ '<': value < n, '>': value > n, '<=': value <= n, '>=': value >= n, '=': value === n, '!=': value !== n })[match[1]];
            }
            return normalize(value).includes(normalize(input));
        });
    });
    if (query.sort) {
        const key = query.sort;
        result = result.toSorted((a, b) => a[key] == null ? (b[key] == null ? 0 : 1) : b[key] == null ? -1 : query.direction * (typeof a[key] === 'number' && typeof b[key] === 'number' ? a[key] - b[key] : String(a[key]).localeCompare(String(b[key]), 'en', { numeric: true, sensitivity: 'base' })));
    }
    const offset = Math.min(query.offset, Math.max(0, Math.ceil(result.length / query.limit) - 1) * query.limit);
    return { rows: result.slice(offset, offset + query.limit), total: result.length, offset, limit: query.limit };
}
