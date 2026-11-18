import { readFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { homedir } from 'node:os';
import { createHash } from 'node:crypto';
export const LUNA_MODEL = 'gpt-6-luna';
export interface SubscriptionBinding {
    codex_home: string;
    account_hash: string;
    auth_mode: 'chatgpt';
}
/** Literal loopback only: no DNS aliases, remote endpoints, credentials, paths or redirects. */
export function localS3Endpoint(value: string) {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol) || !['127.0.0.1', '[::1]'].includes(url.hostname) || url.username || url.password || url.pathname !== '/' || url.search || url.hash)
        throw Error('S3 must use a literal local loopback endpoint, such as http://127.0.0.1:13900');
    return url.origin;
}
// Compatibility for existing local clients; the endpoint policy is independent of S3 vendor.
export const localGarageEndpoint = localS3Endpoint;
export async function subscriptionBinding(home = process.env.CODEX_HOME || path.join(homedir(), '.codex')): Promise<SubscriptionBinding> {
    if (!path.isAbsolute(home))
        throw Error('Codex subscription home must be an absolute local path');
    const codex_home = await realpath(home);
    let auth: Record<string, any>;
    try {
        auth = JSON.parse(await readFile(path.join(codex_home, 'auth.json'), 'utf8'));
    }
    catch {
        throw Error('Sign in to the source Codex home with its ChatGPT subscription before analysis');
    }
    if (auth.auth_mode !== 'chatgpt' || auth.OPENAI_API_KEY || !auth.tokens?.account_id || !auth.tokens?.access_token || !auth.tokens?.refresh_token)
        throw Error('Analysis requires ChatGPT subscription authentication; API-key billing is disabled');
    return { codex_home, account_hash: createHash('sha256').update(String(auth.tokens.account_id)).digest('hex'), auth_mode: 'chatgpt' };
}
export function sharedSubscription(turns: {
    source?: Record<string, unknown>;
}[]): SubscriptionBinding {
    const bindings = turns.map(t => t.source?.analysis_binding as SubscriptionBinding | undefined);
    const missing = bindings.filter(b => !b).length;
    if (missing) throw Error(`${missing} of ${turns.length} turns have no Codex subscription binding. In Data list, configure their original transcript folder and local Codex subscription home, then run the collector to reconcile them.`);
    const first = bindings[0];
    if (!first || bindings.some(b => !b || b.auth_mode !== 'chatgpt' || typeof b.codex_home !== 'string' || !path.isAbsolute(b.codex_home) || !/^[a-f0-9]{64}$/.test(b.account_hash)))
        throw Error('A collected Codex subscription binding is invalid. Reconcile the original source folder in Data list.');
    if (bindings.some(b => b!.account_hash !== first.account_hash)) throw Error('This task includes different Codex subscription accounts. Group its turns by their source subscription before analyzing.');
    return first;
}
export async function resolveSubscription(turns: {source?: Record<string, unknown>}[]) {
    const expected = sharedSubscription(turns), homes = [...new Set(turns.map(t => (t.source!.analysis_binding as SubscriptionBinding).codex_home))];
    for (const home of homes) {
        try { const current = await subscriptionBinding(home); if (current.account_hash === expected.account_hash) return current; }
        catch { /* Try another collected home belonging to the same account. */ }
    }
    throw Error('No collected Codex home is signed in to the source subscription. Sign in with Codex in that home, then run the collector again. API-key billing remains disabled.');
}
export async function subscriptionEnvironment(binding: SubscriptionBinding) {
    if (!binding || binding.auth_mode !== 'chatgpt')
        throw Error('Source Codex subscription binding is missing');
    const current = await subscriptionBinding(binding.codex_home);
    if (current.account_hash !== binding.account_hash)
        throw Error('The source Codex subscription changed; analysis was not invoked');
    const env: NodeJS.ProcessEnv = { NODE_ENV: process.env.NODE_ENV || 'production' };
    for (const key of ['PATH', 'HOME', 'USER', 'LOGNAME', 'LANG', 'LC_ALL', 'TMPDIR', 'TEMP', 'TMP', 'SSL_CERT_FILE', 'SSL_CERT_DIR', 'HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY', 'NO_PROXY', 'https_proxy', 'http_proxy', 'all_proxy', 'no_proxy'])
        if (process.env[key] != null)
            env[key] = process.env[key];
    env.CODEX_HOME = binding.codex_home;
    return env;
}
