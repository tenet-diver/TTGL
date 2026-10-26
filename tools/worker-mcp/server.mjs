// The official MCP SDK transports one bounded tool into one unmounted worker.
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execute = promisify(execFile);
const container = process.argv[2];
if (!/^ttgl-worker-[a-f0-9]{24}$/.test(container ?? '')) {
  throw new Error('An owned worker container name is required');
}
const server = new McpServer({ name: 'ttgl-worker', version: '1.0.0' });
server.registerTool('shell', {
  description: 'Run a shell command in the assigned offline Linux repository at /testbed. '
    + 'Read/edit files and run tests here. Python uses the prepared testbed environment. '
    + 'No host files, evaluator tests, credentials, other workers, or network are mounted.',
  inputSchema: {
    command: z.string().min(1).max(50000),
    timeout_seconds: z.number().int().min(1).max(120).default(60),
  },
}, async ({ command, timeout_seconds }) => {
  const args = ['exec', '--workdir', '/testbed', container,
    'timeout', '--signal=KILL', String(timeout_seconds), 'bash', '-lc',
    'export PATH=/opt/miniconda3/envs/testbed/bin:$PATH; ' + command];
  try {
    const { stdout, stderr } = await execute('docker', args, {
      timeout: (timeout_seconds + 5) * 1000, maxBuffer: 8 * 1024 * 1024,
    });
    return { content: [{ type: 'text', text: JSON.stringify({
      exit_code: 0, stdout: stdout.slice(-40000), stderr: stderr.slice(-10000),
    }) }] };
  } catch (error) {
    return { content: [{ type: 'text', text: JSON.stringify({
      exit_code: Number.isInteger(error.code) ? error.code : null,
      timeout: Boolean(error.killed) || error.code === 137,
      stdout: String(error.stdout ?? '').slice(-40000),
      stderr: String(error.stderr ?? error.message).slice(-10000),
    }) }], isError: true };
  }
});
await server.connect(new StdioServerTransport());
