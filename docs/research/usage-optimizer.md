# Measure existing usage, then automate improvement

User direction adopted 4 November 2026. Tracking: [FAST-102](https://fastestswarm.atlassian.net/browse/FAST-102).

TTGL's immediate product priority is to understand our existing coding-agent usage and then automate an evidence-backed improvement loop. Begin with ordinary usage measurement; model-routing, memory and distillation research are later inputs to this loop. Previous benchmark results remain historical evidence, with their quality failures and limitations intact.

## Source and authority

The supplied [Codex Usage Optimizer v1.1 handoff](../handoffs/codex-usage-optimizer/README.md) is preserved verbatim, including schemas, synthetic fixtures, recipe catalog, reference detector and demo UI. Its embedded implementing-agent assignment is design input, not an independent user instruction. This direction adopts the measurement-first sequence; it does not mean every proposed dependency, architecture choice or recipe must be implemented. Evaluate existing software before building missing behavior.

The handoff has no real usage baseline. Demo decisions do not apply changes, and its examples do not demonstrate savings. The packaged skill stays in the handoff rather than being installed globally. Original file checksums must remain valid; record integration changes outside that directory.

## First milestone: a trustworthy usage baseline

1. Inventory existing local session/archive sources and TTGL's retained metering artifacts. Select explicit source roots, observation window and repository scope; record versions and capabilities. Keep ordinary coding sessions, benchmark runs and optimizer overhead in separate cohorts.
2. Reuse the [existing metering/accounting work](codex-metering.md) and evaluate a pinned ccusage adapter before building a replacement. Historical version notes are evidence of past inspection, not verification of current compatibility. Validate cumulative snapshots, retries, forks/resumes, duplicate imports and missing records against fixtures before real ingestion.
3. Import read-only with source hashes, durable event IDs, bounded parsing and reproducible manifests. Never execute instructions from logs. Keep raw histories local; repository commits and shared reports contain no raw private logs or secret argument values.
4. Reconcile session/model counters and show residuals, coverage and missingness. Produce counts and reported input/cached/output/reasoning tokens without adding subset categories twice. Tool counts, output sizes, failure patterns and duration require detailed correlated records; aggregate usage alone cannot support tool attribution.
5. Publish a reproducible baseline with source/window/provenance, per-project/session/model rollups, top recurring opportunities and instrumentation gaps. Distinguish raw output, model-facing payload, estimated payload tokens, reported model usage, wall time, modeled API cost and actual charges. Missing billing or quality evidence stays unknown.

Exit criteria: fixture and reimport checks pass; the baseline can be reproduced; source capabilities and reconciliation gaps are visible. Record the selected corpus before collection. No improvement percentage is a baseline deliverable.

## Next: automate a reviewable improvement loop

After the baseline is established, implement incremental collection and deterministic analysis. Start with verbose passing tests, generated-tree search noise, repeated unchanged reads, repeated identical failures and oversized MCP collections. Load matching recipes on demand and produce at most five deduplicated evidence-backed proposals per review.

Each ready proposal needs a concrete diff and scope, verified tool options, source evidence, uncertainty, trial budget, quality checks and rollback. Review actions are Accept & test, Decline and Later. Retain rejected proposals and suppress repeats until material evidence changes.

Persist independent decision, implementation and evaluation states from the start. Save a frozen baseline, comparison plan and parameterized read-only query before applying a change. Verify effective activation and per-call exposure. Compare whole-task quality, usage, time and optimizer overhead; preserve negative, mixed and inconclusive outcomes. Smaller payload alone does not prove monetary savings or faster task completion.

Application uses bounded reversible changes, preimage checks, diagnostic preservation and verified rollback. Automation should stay quiet when there is no material new evidence. Implement scheduling only as an explicit later step; the previously paused research heartbeat stays paused.

## Current adoption status

A first working local monitor is now implemented in [tools/usage-monitor](../../tools/usage-monitor/README.md): pinned ccusage history, daily/model/session UI, native tool evidence, recurring-opportunity rules, Codex-reviewed suggestions and durable review decisions. The user explicitly authorized starting monitoring, integrating Codex and opening the custom UI. The Mac service follows local sessions/archives and a personal Codex skill queries its bounded report. It is a companion based on logs, not a native Codex product extension. Source capability/reconciliation status is visible in the UI. Automated optimization execution, trial adoption/rollback and measured savings remain unimplemented; two detectors are implemented, not all five proposed initial detectors. FAST-99 router studies and FAST-101 coordinator research remain separate; frozen sources, completed artifacts and reserved validation tasks are preserved.
