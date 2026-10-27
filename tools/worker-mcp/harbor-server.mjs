// Official MCP SDK; all actions go through the assigned Harbor environment API.
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const [port, token] = process.argv.slice(2);
if (!/^\d{1,5}$/.test(port ?? '') || Number(port) < 1 || Number(port) > 65535
    || !/^[a-f0-9]{64}$/.test(token ?? '')) throw new Error('Invalid owned bridge endpoint');
const server = new McpServer({ name: 'ttgl-harbor-worker', version: '1.0.0' });
server.registerTool('shell', {
  description: 'Read/edit the assigned repository and execute public checks inside its Harbor environment. The host workspace has no repository. No host shell or external evaluator access is provided.',
  inputSchema: { command: z.string().min(1).max(50000),
    timeout_seconds: z.number().int().min(1).max(120).default(60) },
}, async ({ command, timeout_seconds }) => {
  const response = await fetch(`http://127.0.0.1:${port}/shell`, {
    method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ command, timeout_seconds }), signal: AbortSignal.timeout((timeout_seconds + 15) * 1000),
  });
  if (!response.ok) throw new Error(`Environment bridge failed (${response.status})`);
  const result = await response.json();
  return { content: [{ type: 'text', text: JSON.stringify(result) }], isError: result.exit_code !== 0 };
});
await server.connect(new StdioServerTransport());
