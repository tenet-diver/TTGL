/** Decode API responses without exposing proxy HTML or truncated JSON as parser errors. */
export async function apiJson<T>(response: Response): Promise<T> {
    try {
        const value: unknown = await response.json();
        if (!value || typeof value !== 'object' || Array.isArray(value))
            throw Error('Invalid API envelope');
        return value as T;
    }
    catch (error) {
        if (error instanceof Error && error.name === 'AbortError') throw error;
        throw Error(response.ok
            ? 'The server returned an incomplete response. Please retry.'
            : `The request failed (HTTP ${response.status}). Please retry.`);
    }
}
