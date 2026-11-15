/** CLI upstream zero defaults are not evidence of zero inference. Preserve raw output separately. */
export function analystUsage(raw: unknown) {
    if (!raw || typeof raw !== 'object')
        return null;
    const u = raw as Record<string, unknown>, input = u.input_tokens, cached = u.cached_input_tokens, output = u.output_tokens;
    if (![input, cached, output].every(v => typeof v === 'number' && Number.isSafeInteger(v) && v >= 0) || Number(cached) > Number(input) || Number(input) + Number(output) === 0)
        return null;
    const total = Number(input) + Number(output);
    if (u.total_tokens != null && u.total_tokens !== total)
        return null;
    return { input_tokens: Number(input), cached_input_tokens: Number(cached), output_tokens: Number(output), total_tokens: total };
}
