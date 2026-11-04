# Optimizer evidence and action contract

## Evidence ladder

1. Aggregate session/day usage: rank projects/sessions, report cached/input/output totals and missingness. No tool attribution.
2. Tool-call events: group command/server/operation, count repetitions, bytes and duration where recorded.
3. Model-facing serialized result: tokenize the actual presented text; preserve tokenizer/version and whether truncation/compression occurred.
4. Request-level accounting: correlate call IDs/history where available; do not assume a tool body was resent unchanged or uncached.
5. Matched experiment: measure end-to-end cost/time and verified outcome for actual savings claims.

Choose a small bounded raw-evidence sample after aggregate SQL/grouping; do not feed entire private histories to the optimizer. Redact secrets before indexing/export. Null is unknown, not zero. Keep imported/inferred fields distinct from live-observed fields. Cumulative model usage is converted to deltas at one authoritative grain; parent/child and imported/live duplicates are reconciled.

## Estimation

For eligible calls over window W, baseline payload B=sum(model-facing payload token estimates). A local deterministic replay may yield transformed P and overhead H. Replay payload saving=B-P-H. If no faithful replay exists, use explicit lower/upper scenarios (including zero), not an invented confidence interval. An assumed reduction factor is a scenario, not a prediction. Frequency forecast must state population/window/stability assumption; projected exposure=per-call effect×eligible future calls, with non-use and uncertainty visible. Do not multiply by tool frequency twice.

Model-token savings require actual request/history accounting or an experiment. Cache-aware API cost needs reported reads/writes/output and applicable prices; subscription-equivalent cost is modeled. Tool execution time summed across parallel calls is work-time, not user elapsed time. A quieter reporter may reduce payload with unchanged runtime. Avoid savings double counting across recommendations that touch the same calls/prefix/schema; report combined experiments separately.

## Review and execution

Proposal states: draft→needs_evidence or ready_for_review→accepted/declined/deferred. Accepted→preflight→trial_running→measured→adopted or rolled_back/inconclusive. Acceptance is tied to proposal version, patch hash, scope and budget. User can withdraw before trial; cancellation retains evidence/cost. Changed code/config preimages invalidate acceptance of that concrete patch. A successful trial can adopt only the displayed change under the selected scope; no silent global promotion.

Use task-local profiles first. Preserve error output, exit status, final required tests and exact logs. Archive stdout/stderr outside the model response, but do not assume output redirected to disk is still visible to Codex. Include a clear expansion tool/path when needed. Capturing/formatting is distinct from deleting diagnostics.

The analysis agent proposes; deterministic executor applies allowlisted patch types after acceptance and preimage checks. Novel code edits can use an isolated coding worktree, with review of the resulting concrete diff before any shared configuration adoption. Keep reasoning and evidence provenance without storing hidden chain of thought.

History extension v1.1: use history-contract.md for independent decision/implementation/evaluation dimensions and effective-profile comparison plans. The simple proposal workflow above is a review projection; acceptance never substitutes for verified implementation or measured outcome.
