import { spawn } from 'node:child_process';
import { readFile } from 'node:fs/promises';
const text = await readFile(new URL('../.env.test.local', import.meta.url), 'utf8');
for (const line of text.split('\n')) {
    const i = line.indexOf('=');
    if (i > 0)
        process.env[line.slice(0, i)] = line.slice(i + 1).replace(/^['"]|['"]$/g, '');
}
const child = spawn(process.execPath, ['node_modules/next/dist/bin/next', process.argv.includes('--dev') ? 'dev' : 'start', 'apps/web', '--hostname', '127.0.0.1', '--port', process.argv.includes('--dev') ? '3533' : '3433'], { stdio: 'inherit', env: process.env });
process.on('SIGINT', () => child.kill('SIGINT'));
process.on('SIGTERM', () => child.kill('SIGTERM'));
child.on('exit', code => process.exitCode = code ?? 1);
