/** Large evidence selections use a read-only POST to avoid proxy URL limits. */
export function requestRecords(kind: string, search: URLSearchParams, signal: AbortSignal) {
    const endpoint = '/api/records/' + kind, url = endpoint + '?' + search;
    return url.length <= 1800
        ? fetch(url, { signal })
        : fetch(endpoint, { method: 'POST', signal, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.fromEntries(search)) });
}
