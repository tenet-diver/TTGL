/** Use the received Host header, not Next's internal rewritten request URL. */
export function sameOrigin(origin: string | null, host: string | null) {
    if (!origin || !host)
        return false;
    try {
        const u = new URL(origin);
        return ['http:', 'https:'].includes(u.protocol) && !u.username && !u.password && u.host === host;
    }
    catch {
        return false;
    }
}
