import { test } from 'node:test';
import assert from 'node:assert/strict';
import { apiJson } from './api-response.ts';
test('HTML proxy errors and truncated successful responses produce retryable messages', async () => {
    await assert.rejects(apiJson(new Response('<html>Bad gateway</html>', { status: 502 })), /^Error: The request failed \(HTTP 502\). Please retry\.$/);
    await assert.rejects(apiJson(new Response('{"rows":[')), /^Error: The server returned an incomplete response. Please retry\.$/);
    for (const body of ['null', '[]', '"unexpected"'])
        await assert.rejects(apiJson(new Response(body)), /incomplete response/);
});
test('API errors remain available for removed-column recovery and mutation validation', async () => {
    const body = { error: 'Unknown record column' };
    assert.deepEqual(await apiJson(new Response(JSON.stringify(body), { status: 400 })), body);
    assert.deepEqual(await apiJson(new Response('{"rows":[],"total":0}')), { rows: [], total: 0 });
});
test('cancelled response streams preserve AbortError', async () => {
    const error = new DOMException('Cancelled', 'AbortError');
    const response = new Response(new ReadableStream({ start(controller) { controller.error(error); } }));
    await assert.rejects(apiJson(response), value => value === error);
});
