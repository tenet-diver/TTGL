export function format(value: unknown, type?: string): string {
    if (value == null)
        return '—';
    if (type === 'date') {
        const date = new Date(String(value));
        return Number.isNaN(+date) ? 'Unknown' : new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }).format(date);
    }
    if (type === 'duration') {
        const seconds = Number(value);
        if (!Number.isFinite(seconds))
            return '—';
        return seconds >= 3600 ? `${Math.floor(seconds / 3600)}h ${Math.round(seconds % 3600 / 60)}m` : seconds >= 60 ? `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s` : `${+seconds.toFixed(1)}s`;
    }
    if (type === 'money')
        return '$' + Number(value).toLocaleString('en', { maximumFractionDigits: Math.abs(Number(value)) < .01 ? 5 : 2 });
    if (type === 'percent')
        return (Number(value) * 100).toLocaleString('en', { maximumFractionDigits: 1 }) + '%';
    if (type === 'tokens')
        return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(Number(value));
    if (typeof value === 'number')
        return new Intl.NumberFormat('en', { maximumFractionDigits: 3 }).format(value);
    if (typeof value === 'boolean')
        return value ? 'Yes' : 'No';
    return typeof value === 'object' ? JSON.stringify(value) : String(value);
}
