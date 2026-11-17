/** Adapt retained process-v1 interpretations without running a model or guessing from prose. */
export function legacyProcessFields(row: Record<string, unknown>, memberIds: string[]) {
    const outcome = String(row.outcome), known = new Set(memberIds);
    if (!['done', 'failed', 'dead_end', 'in_progress', 'cancelled', 'unknown'].includes(outcome))
        throw Error('Unknown legacy process outcome');
    const ids = typeof row.source_steps === 'string' ? JSON.parse(row.source_steps) : row.source_steps;
    if (!Array.isArray(ids) || ids.some(id => typeof id !== 'string' || !known.has(id)) || new Set(ids).size !== ids.length)
        throw Error('Legacy process evidence is outside its interpretation');
    if (outcome !== 'unknown' && !ids.length)
        throw Error('Legacy process outcome has no retained evidence');
    if (typeof row.reason !== 'string' || !row.reason.trim() || typeof row.confidence !== 'number' || row.confidence < 0 || row.confidence > 1)
        throw Error('Legacy process reason/confidence is invalid');
    const state = ({ done: 'completed', failed: 'completed', dead_end: 'completed', in_progress: 'working', cancelled: 'cancelled', unknown: 'unknown' } as Record<string, string>)[outcome];
    return {
        source_protocol: 'task-process-v1', outcome, outcome_reason: row.reason,
        outcome_confidence: row.confidence, evidence_event_ids: ids as string[],
        state, state_basis: 'Lifecycle mapped from the retained process-v1 outcome; not a separately recorded state.',
        failure_reason: ['failed', 'dead_end'].includes(outcome) ? row.reason : null,
        intervention: String(row.intervention || 'unknown'), intervention_reason: String(row.intervention_reason || ''),
        legacy_source_turn_ids: typeof row.source_turns === 'string' ? JSON.parse(row.source_turns) : row.source_turns || [],
        runtime_role: String(row.runtime_role || 'mixed_or_unknown'),
    };
}
