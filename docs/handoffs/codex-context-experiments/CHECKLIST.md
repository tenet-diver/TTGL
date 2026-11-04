# Implementation and evaluation checklist

## M0 — reuse existing observability

- [ ] Read repository instructions and register accessible/missing research sources.
- [ ] Inventory existing telemetry, cost records, hooks, archives and session joins.
- [ ] Fill observability-map.csv; distinguish missing from zero.
- [ ] Verify CLI/version/auth/model/tool interfaces with harmless canaries.
- [ ] Prove actual transformation coverage; mark unsupported cells explicitly.
- [ ] Reconcile metered charges or label modeled cost; audit cache-write semantics.
- [ ] Produce a joined session → usage → patch → acceptance example.
- [ ] Add only missing tags/events; no new tracing or billing platform.

## M1–M2 — contracts and first four ideas

- [ ] Implement schemas, DAG validator, independent flags and identity control.
- [ ] Protect originals, exact recovery, namespace isolation and atomic writes.
- [ ] Implement masking, output compression, hierarchy and reversible views.
- [ ] Test protocol, opaque-state handling, native compaction and safe fallback.
- [ ] Record assigned/applied treatment and every transformation's provenance.

## M3 — task and pilot readiness

- [ ] Select approximately ten real prompts; lock commits, prompt and environment hashes.
- [ ] Author independent protected graders; validate bad base/reference outcomes.
- [ ] Separate development tasks from frozen evaluation tasks.
- [ ] Freeze budgets, allocation, randomization, analysis and stop gates.
- [ ] Obtain a concrete paid-run budget before execution.
- [ ] Complete replay → shadow → small pilot gates in order.

## M4–M5 — memory, local models and cache

- [ ] Mem0 is a pinned optional adapter; include raw-history search comparator.
- [ ] Principles preserve evidence, applicability, procedures and counterexamples.
- [ ] Stage and graph ranking use equal final retrieval budgets.
- [ ] Freeze training-only memory snapshots; deny test/future/cross-run leakage.
- [ ] Pin local weights/runtime and record CPU/energy/latency and fallback.
- [ ] Validate model-specific cache buckets; test stable-prefix/compaction arms.
- [ ] Account for all construction, extraction, failed and discarded work.

## M6–M7 — execution and reporting

- [ ] Launch isolated sessions with matched settings and independent repeats.
- [ ] Keep every attempt, fallback, interruption, failure and cost.
- [ ] Analyze per-task pairs; cluster uncertainty by task, not turns.
- [ ] Report exact cash, subscription estimates and engineering-inclusive views separately.
- [ ] Treat ten tasks as a pilot; do not infer equivalence from non-significance.
- [ ] Deliver reproducibility manifests, data dictionary, failure catalogue and limitations.
- [ ] Keep Supabase deployment optional and separately scoped.
