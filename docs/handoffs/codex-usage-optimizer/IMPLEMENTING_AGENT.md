# Assignment for the implementing coding agent

Implement the local Codex Usage Optimizer described in IMPLEMENTATION_GUIDE.md. Begin with source capabilities and historical-import reconciliation, then deterministic rollups and the first five detectors. Use the packaged optimizer skill and load matching recipes on demand.

Deliver a small review UI with evidence, concrete scope/diff, grounded estimates and Accept & test / Decline / Later. Do not connect an apply action directly to unconstrained LLM output. Implement versioned decisions, preimage checks, bounded trials, independent quality checks and rollback. Keep proposed, replay-estimated and measured effects distinct.

ccusage is a usage baseline, not a per-tool profiler. Add raw-rollout or observer detail before blaming individual tools. Keep source logs local, immutable and out of exported artifacts by default. No Qdrant/memory system is required for this MVP. Reuse the earlier context-lab experiment harness only where useful; the 100-recipe pack does not justify implementing 100 editors at once.

Validate fixtures and interaction prototype before a real import. Real imports and trials must use the user's selected local sources, concrete repository scope and budget. Record supported versions, coverage, measured overhead and all limitations. Do not invent optimization results or savings percentages.


Version 1.1 adds OPTIMIZATION_HISTORY.md. Implement U13–U17: durable accepted/rejected event history; independent decision/implementation/evaluation states; baseline/query generation; effective-config receipts and per-call exposure; versioned outcomes and per-tool technique comparisons. An agent narrative or accepted button is not implementation proof. Preserve negative results and missingness.
