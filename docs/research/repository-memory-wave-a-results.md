# Repository memory comparison: first development wave

10 November 2026. Completed generation and independent replay; adapted runtime,
not an official VibeMemBench or SWE-rebench score. Two tasks, four arms, one Sol
attempt per cell. This is frozen prior-history use, not longitudinal learning.

| Arm | Registered exact-match passes | All prescribed tests pass (post-hoc) | Native tokens | Model-rate credits scenario | Change versus fresh |
|---|---:|---:|---:|---:|---:|
| Fresh, no prior history | 0/2 | 1/2 | 727,150 | 6.573420 | reference |
| Raw prior history | 0/2 | 1/2 | 819,082 | 7.030860 | +6.96% |
| Mem0 with Luna maintenance | 0/2 | 1/2 | 1,062,970 | 6.943712 | +5.63% |
| Graphiti with Luna maintenance | 0/2 | 1/2 | 2,428,888 | 9.619914 | +46.35% |

All arms pass the prescribed tests on cfn-lint3342 and fail them on2387.
The registered upstream exact-set matcher counts added passing regression tests
as a mismatch, making all four3342 submissions strict failures. Preserve that
primary result. The separately labeled post-hoc assessment uses the already
recorded parsed outcomes; it adds no model calls or replays. This assessment
is not a policy selected for a held-out test. For the future longitudinal
study, register prescribed-test inclusion before inference and retain other
observed statuses separately. A nonzero command exit alone is not a task verdict.

On2387 all four candidate patches cause genuine output-message regressions in
three integration tests. On3342 every prescribed test passes; candidates add
between two and three passing tests. This distinction is necessary to avoid
confusing a grader artifact with a software failure.

All84 completed native processes (eight solvers and76 maintenance calls) and
200 distinct responses reconcile across native response counters, CLI counters
and capture events. The completed cells total5,038,090 tokens and30.167905
model-rate scenario credits. Cached input is a subset, not extra input. Mem0
maintenance costs0.674602 and Graphiti maintenance3.652784 scenario credits.
The small sample does not establish a cost distribution, significance, or a
causal representation advantage. Neither assessment shows a quality gain.

One distinct native-memory diagnostic background request was cancelled without
usage outside these study cells. Its inference cost remains unknown. Stream-wide
research accounting is therefore incomplete even though the84 completed wave
processes reconcile. Preflight, parent research, implementation and local compute
are separate overhead; these are not net first-use savings. Published Standard
rates verified10November are Sol50/2.5/250 and Luna2.5/0.25/12.5 credits per million
uncached input/cached input/output tokens. Actual cash expense, account credits
and quota saving remain unknown. [Official pricing](https://learn.chatgpt.com/docs/pricing).

Mem0 and Graphiti are self-hosted stock engines with disclosed native-Luna and
local BGE adapters, not hosted Mem0 or Zep service results. Mem0 uses its dense
adaptation without optional spaCy/BM25. Graphiti uses stock RRF and a local
reviewed Neo4j derivative without its excluded affected optional Parquet/GDS
artifacts. No cross-encoder or model-repair fallback is allowed. Complete raw
prior trajectories are equally available to the three history arms; bounded
complete-message ingestion views and losses are recorded. Fresh has no prior
history. Native memories/hooks are disabled in these solvers. Every actor is
fresh, offline and unprivileged. All generation completes before hidden grading.

The patched Python runtime lacks Git and exposes pytest as `python3 -m pytest`.
These are shared environment limitations, not memory-system characteristics.
Empty/reference controls pass in this adapted environment. Do not extrapolate
its token differences to ordinary fully provisioned coding environments.

Private immutable evidence: `work/security/repository-memory-20261110/wave-a-001/`:
`manifest.json`, `complete.json`, `reconciled-results-001.json`,
`assessment-002.json`; grader outputs are in `wave-a-replay/`. Preparation
failures, resource-move overlap audit and all failed submissions are retained.
No assignment is repeated or replaced.
