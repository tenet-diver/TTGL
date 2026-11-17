import { timingSafeEqual, createHash } from 'node:crypto';
import { z } from 'zod';
export const principalSchema = z.strictObject({ tokenSha256: z.string().regex(/^[a-f0-9]{64}$/), projectId: z.string().min(1), experimentId: z.string().min(1),
    role: z.enum(['operator', 'runner', 'annotator', 'verifier']), arm: z.string().nullable(), taskIds: z.array(z.string()).nullable() });
export type ExperiencePrincipal = z.infer<typeof principalSchema>;
export function experiencePrincipal(authorization: string | null, config = process.env.OBS_EXPERIENCE_PRINCIPALS || '[]'): ExperiencePrincipal {
    if (!authorization?.startsWith('Bearer ') || authorization.length > 8192) throw Error('Experience authentication required');
    const digest = createHash('sha256').update(authorization.slice(7)).digest();
    const principals = z.array(principalSchema).max(100).parse(JSON.parse(config));
    const principal = principals.find(p => timingSafeEqual(Buffer.from(p.tokenSha256, 'hex'), digest));
    if (!principal) throw Error('Experience authentication required');
    return principal;
}
const permissions: Record<ExperiencePrincipal['role'], string[]> = {
    operator: ['ingest-native', 'job-status', 'accounting', 'evaluation-summary', 'register-study', 'publish', 'retire', 'snapshot', 'search', 'hybrid-search', 'read', 'plan', 'checkpoint', 'routing', 'attempt', 'attempt-event', 'verification', 'reuse', 'barrier', 'embedding', 'queue-extraction', 'readiness', 'artifact', 'artifact-manifest'],
    runner: ['ingest-native', 'job-status', 'accounting', 'search', 'hybrid-search', 'read', 'plan', 'checkpoint', 'routing', 'attempt', 'attempt-event', 'readiness', 'artifact', 'artifact-manifest'],
    annotator: ['job-status', 'publish', 'queue-extraction', 'readiness', 'artifact', 'artifact-manifest'], verifier: ['verification', 'reuse', 'barrier', 'readiness', 'artifact', 'artifact-manifest'],
};
export function authorizeExperience(p: ExperiencePrincipal, operation: string, scope: { projectId: string; experimentId: string }, payload: Record<string, unknown>) {
    if (p.projectId !== scope.projectId || p.experimentId !== scope.experimentId || !permissions[p.role].includes(operation)) throw Error('Experience access denied');
    if (p.arm && payload.arm && p.arm !== payload.arm) throw Error('Wrong experiment arm');
    if (p.taskIds && payload.taskInstanceId && !p.taskIds.includes(String(payload.taskInstanceId))) throw Error('Wrong task assignment');
}
