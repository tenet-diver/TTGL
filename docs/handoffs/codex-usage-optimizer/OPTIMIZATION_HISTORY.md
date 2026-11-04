# Optimization history, implementation tracking and before/after evaluation
Version 1.1 · 4 November 2026

## 1. Required behavior

Maintain a durable history of every suggestion, revision, user decision, implementation attempt and evaluation. A suggestion accepted today may not be applied until tomorrow, and it may later prove worse. These are separate facts. Rejection is retained with its evidence and optional reason; it is not deletion. Users can browse all changes affecting a tool and compare techniques/versions on the same operation.

For each accepted suggestion the integration agent prepares a **comparison plan and runnable read-only query** before implementation. It links them to the exact patch/scope/version and captures a baseline. After applying the accepted patch, the executor verifies the actual effective configuration, emits an implementation event and begins collecting eligible treatment data. The optimizer updates its view from evidence; an agent's “done” message is insufficient.

The new history UI complements suggestion review. It must answer: What did I accept/decline? What actually changed, when and where? Which tool calls used it? Did payload/time/quality improve? What did technique B do compared with technique A? Can I roll it back? Which conclusions are still pending or confounded?

## 2. Separate decision, implementation and evaluation states

Persist independent dimensions:

- Decision: `pending`, `accepted`, `declined`, `deferred`, `withdrawn`.
- Implementation: `not_started`, `applying`, `applied_unverified`, `implemented`, `failed`, `rolled_back`, `superseded`.
- Evaluation: `not_planned`, `baseline_ready`, `collecting`, `ready`, `complete`, `inconclusive`, `invalidated`.
- Outcome: null until evaluated, then `better`, `worse`, `mixed`, `no_detected_change`, or `inconclusive` under declared criteria.

Examples: accepted/not_started/baseline_ready is waiting for implementation; accepted/implemented/collecting is active but unmeasured; accepted/implemented/complete/worse is a real negative finding. Declined proposals have no treatment exposure and must not acquire measured after-effects. A historical proposal can be superseded without erasing its previous result. Rollback closes its exposure interval and records the resulting effective profile, not an assumption that the original profile was restored exactly.

Keep append-only `optimization_events` and a transactionally updated current-state projection. Each event has ID, proposal ID/version, actor, event type, occurred_at, observed_at, idempotency key, previous state version and payload ref/hash. Optimistic concurrency prevents simultaneous workers advancing stale states. Events include decision_recorded, baseline_frozen, apply_started, patch_written, effective_config_verified, implementation_failed, exposure_started/ended, evaluation_completed/invalidated, rollback_verified and superseded. Out-of-order/duplicate observations are reconciled by identity and causal revision, not ingestion order alone.

## 3. Data model and trace linkage

Extend the MVP SQLite schema with:

| Entity | Required contents |
|---|---|
| `optimization_cases` | Stable suggestion family, proposal versions, recipe IDs, repo/scope, stable target tool/server/operation, current state version and three state dimensions |
| `optimization_events` | Immutable transitions, decision actor/reason, implementation evidence and before/after state; idempotent identity |
| `implementation_revisions` | Accepted proposal/patch hashes, preimage/postimage/effective-config hashes, commit/worktree, file diff, tool/runtime versions, implementation verification, optional external implementation reference |
| `comparison_plans` | Typed cohort selector, baseline/treatment profile hashes, fixed windows or paired tasks, metric definitions, minimum samples/coverage, confound/exclusion rules, quality gates and evaluation horizon |
| `comparison_queries` | Plan ID/version, validated parameterized SQL, hash, bound parameter snapshot, schema/compiler version, read-only constraints and explanation of selected/excluded populations |
| `tool_exposures` | Call/task/session ID, observed effective profile, implementation revision(s), arm/variant, validity and confidence; unknown when activation cannot be proven |
| `comparison_results` | Query/plan/data-snapshot hashes, raw sample counts/coverage, baseline/treatment statistics, signed differences, uncertainty, quality evidence, verdict, as-of time and result revision |
| `rollback_records` | Managed reverse diff, preimage checks, verification, exposure closure and resulting profile hash |

Use stable tool identity across option changes: `pytest + run_tests` remains the operation while `pytest` and `pytest -q` are distinct command/profile hashes. Filtering for the old exact command would incorrectly drop treatment runs. Join exact config/version evidence to each invocation where possible. A file edit alone does not prove a running process reloaded it; verify restart/activation before treatment labeling. A global setting can affect many repositories; a project-only plan must not include other projects implicitly.

Attribution is per effective configuration, not just wall-clock before/after. Preserve unknown/partial exposure when old processes, profiles or caches coexist. Tag combinations with distinct effective profile IDs and parent implementation revisions. Do not credit two simultaneous changes with independent additive savings. Later regression fixes, rollbacks and disabled states remain visible. Distinguish actual tool identity from mutable display names.

## 4. Agent-generated comparison plans and queries

The integration agent creates a typed plan alongside the concrete change:

1. Identify target repository/tool/operation, relevant metrics and available provenance.
2. Choose comparable baseline data and a treatment collection strategy. Prefer identical-task paired trials for causal claims; natural usage windows are observational.
3. Freeze primary metric and quality guardrails, sample/coverage thresholds, window endpoints and exclusions. Defaults are pilot settings, not significance guarantees.
4. Generate parameterized SELECT SQL through a schema-aware builder and validate against the chosen normalized dataset. Save readable SQL, parameters, plan hash and a plain-language explanation in history. LLM-written arbitrary SQL cannot bypass the builder/read-only policy.
5. Run the baseline query, capture source snapshot/watermark and show baseline preview before acceptance/application. A missing baseline is explicit; a new experiment may replay the baseline on an isolated snapshot if authorized.
6. After verified implementation, classify new calls by actual exposure. Once the horizon and sample conditions are met, rerun the saved query against a new pinned data snapshot and append a result revision.

Execute via a read-only SQLite connection/authorizer with SELECT-only allowlist, bounded rows/time and no extension loading, writes, ATTACH, arbitrary file reads or user-controlled SQL interpolation. Names/operators are compiler-allowlisted; values are bound parameters. Generated queries return aggregates and bounded evidence IDs, not secret raw payloads. The example SQL is intentionally a single parameterized SELECT/CTE; no raw log is ever executed as SQL or shell.

Save both query and metric semantics. A future schema migration either preserves an adapter view or creates a new comparison version; never silently alter an old report. Store data hash/watermark because rerunning a historical query later can include delayed records. Finalized endpoints are immutable; the initial ongoing-collection preview can use a declared as-of endpoint.

## 5. Before/after metrics and claims

For each arm show eligible calls, known/missing payload and duration counts, total known payload, mean known payload/call, mean/p50/p95 known duration, failures/timeouts, actual tool versions, period and exposure coverage. Missing values are not zeros. Report both totals and per-call values: totals fall if the tool is used less even when per-call behavior is unchanged. Duration means include failures and timeouts under a stated policy; censored timeouts are not successful fast calls.

Signed reduction = `(before - after) / before`, for comparable means or matched task totals. Preserve negative numbers: -25% is a regression, not zero. If baseline is zero, percentage change is undefined; show the absolute difference. Do not label a payload-token reduction as a model-token, monetary or elapsed-task-time reduction. Model usage, cached token pricing and cost/verified task belong in separate whole-task comparisons with independent provenance.

Outcome is multi-metric: a quieter reporter may save payload but increase repair rounds; show mixed/worse where quality or debugging degrades. Required tests and useful failure diagnostics are hard gates. “Better” requires declared evidence thresholds, not merely a positive point estimate. For small everyday cohorts show descriptive results and inconclusive uncertainty; an insignificant difference is not proof of equality. Pair/cluster inference by task/session and account for repeated calls. Do not treat each line of a verbose output as an independent sample.

Compare techniques using the same comparator definition: A=original profile, B=quiet reporter, C=structured wrapper, D=B+C as an explicit combined arm. Sequential B then C measures C versus B unless a matched original baseline is rerun. Natural before/after windows may differ in task difficulty, tool version, cache warmth or failure mix; report these confounds and avoid causal assertions. Preserve held-out tasks when tuning recipes based on prior results.

## 6. Implementation verification and state updates

The executor reports structured receipts, not free-text claims: proposal/version, accepted patch hash, expected/current preimage, resulting files and effective profile, activation time, smoke/diagnostic check outputs, actual tool invocation showing new configuration and optional commit. On success emit effective_config_verified and implementation state `implemented`; then evaluation becomes `collecting`. A patch written but not activated stays `applied_unverified`. An implementation failure records partial changes and starts verified rollback when authorized by the accepted plan.

Support externally implemented changes: import a manual/agent commit/receipt, compare it with the accepted change, inspect effective configuration and run the same verification. A changed patch/scope must be reviewed as a new version. Do not mutate a declined suggestion to implemented just because a similar change appears in the repository. Unknown origin becomes a separate detected-change case until reconciled.

When evaluation completes, attach a result and update evaluation/outcome, while keeping acceptance and implementation unchanged. The agent can suggest rollback after a regression; it only auto-rolls back when the accepted trial explicitly authorized that policy and the managed preimage still matches. Corrective implementation creates a new revision and exposure cohort. Reopened or late-data outcomes get a new result version and a visible reason.

## 7. History UI and endpoints

Add an **Optimization history** view, filters for accepted/rejected/implemented/tool/recipe/repo/outcome and a timeline of decisions, verified activation, data collection, comparison and rollback. Each row shows technique/profile, target tool, decision, implementation status, evaluation status, active period, measured effect or pending reason. Detail shows exact diff, implementation receipt, saved query/parameters, cohort counts, sample coverage, before/after charts and source evidence.

Actions: inspect, run saved comparison, compare techniques, prepare variant, adopt, request rollback and reopen decision. Rejected items remain inspectable and suppressed from repeated suggestions as configured. Show the original forecast next to observed result, not overwritten by it. An accepted suggestion with no implementation evidence says **Accepted · Not implemented**, never “saved 30%.”

Proposed endpoints: `GET /optimizations/history`, `GET /optimizations/:id/timeline`, `POST /optimizations/:id/comparison-plan`, `POST /optimizations/:id/implementation-receipt`, `POST /comparisons/:id/run`, `GET /comparisons/:id/results`. Mutations enforce proposal version, allowed state transitions, actual actor and idempotency. A compare action is read-only analysis, not authorization for a new paid trial.

## 8. Additional backlog and acceptance

U13: append-only history/state projection with independent dimensions and rejection retention. U14: typed comparison/query compiler and saved baselines. U15: implementation receipts/effective-config verification and exposure tagging. U16: result revisions, signed effects and technique comparisons. U17: history UI/timeline/query viewer and re-evaluation. These extend U01–U12.

H01 accepted≠implemented; H02 duplicate receipts/decisions idempotent; H03 rejected history retained; H04 changed command still matches stable tool identity; H05 wrong profile/time/repo excluded; H06 missing metrics remain unknown with coverage; H07 zero baseline yields null percent; H08 regressions remain negative; H09 overlapping changes get explicit combined arm; H10 old running process not treatment; H11 arbitrary SQL/write attempts rejected; H12 no better verdict without quality/sample criteria; H13 late data/new schema yields versioned results; H14 manual implementation verified against approved diff; H15 rollback preserves intervening edits and closes exposure; H16 forecasts remain distinct from observed outcomes.

The included schema.sql/comparison.sql/fixture demonstrate a working parameterized aggregate query over synthetic SQLite data. They are a reference contract, not a deployed optimizer backend or automatic state tracker.
