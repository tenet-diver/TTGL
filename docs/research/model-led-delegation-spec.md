# Model-led Codex delegation: preferred implementation direction

18 November 2026. Observatory / TTGL, branch `work`.

Status: implementation handover supplement; proposed study
`model-led-delegation-001`, no new model execution or benchmark reservation.
The user's latest preference is to rely more on the model. This becomes the
preferred product implementation path. Latest steering selects our independently
implemented Observatory router, with Luna/Sol, FrugalGPT and RouteLLM comparisons.
RSI is related work only; its [earlier proposed reproduction](rsi-router-luna-sol-spec.md)
is superseded and is not an active implementation or runnable baseline.

Latest steering adds explicit **tool-owned cheap-model admission by availability,
similarity to verified prior actions and experience recency**. The initial Python
implementation and four-condition ablation protocol are in
[model-led-delegation-001](../../experiments/model-led-delegation-001/README.md).
The primary still decides what to delegate and integrates results; the tool
decides whether the requested cheaper route has enough eligible evidence.
The [revision 002 protocol](../../experiments/model-led-delegation-001/protocol-002.json)
further requires typed-subtask similarity and model-specific outcome attribution.
Versioned, applicable grounded instructions support guided work; teacher examples
remain distinct from observed successes by the cheaper executor.

The latest topic framing is the
[Observatory knowledge-accumulation Codex study](knowledge-accumulation-codex-study.md):
accumulated workflows are the main treatment, unseen-task transfer is the outcome,
and routing/recency are mechanisms. Reuse this implementation and the official
coding benchmark evaluators, with the
[released-baseline contracts](router-baselines-codex.md). No RSI reproduction is
scheduled; the former design remains historical.

## 1. Model and host responsibilities

Use a native Codex primary agent to understand the request, choose meaningful
subtasks, decide what context a worker needs, request delegation, reassess failures
and integrate results. Start with a pinned Sol primary and Luna workers under
the same registered source subscription. These are draft identities to qualify,
not assumed account capabilities or evidence of relative model size.

Workers are autonomous bounded native agents: they may inspect files, edit, run
public checks and revise their approach within the assigned scope and budget.
The host does not choose every shell action or require a separate classification
call before each step. The primary can also keep work itself when delegation
would add unnecessary overhead. No requirement to offload every trivial action.

The delegation tool retrieves eligible experience, provides relevant evidence
about earlier attempts, starts the requested worker and returns retained outcomes.
Model decisions drive task decomposition, applicability judgments, execution
strategy and whether to ask for help. A deterministic host owns enforceable
boundaries: account identity, scope, artifact custody, budgets, isolation,
idempotency, evidence references and terminal status. Model judgment cannot
override these boundaries or manufacture a passing verification record.

Do not quietly reuse the old DAG router. Implement the explicitly registered
availability/similarity/recency tool rule, with its own decision receipts and
ablation controls. Historical outcome summaries also inform the primary/worker;
similarity and weighted past outcomes are not calibrated success probabilities.
A later model-based routing assessor is optional and must have its own measured
cost. V1 uses the transparent tool rule without an extra assessor invocation.

## 2. Tool interface and lifecycle

Implement a small MCP surface on the existing retained worker infrastructure:

- `delegate_subtask`: accepts a bounded contract and returns an attempt/job ID.
- `get_delegation`: returns compact progress or a terminal result, optionally
  including requested evidence excerpts.
- `cancel_delegation`: stops an owned attempt and retains partial work/usage.
- Reuse existing bounded evidence access for detailed commands/results/patches.

The contract contains the objective, parent/checkpoint identity, allowed paths,
public acceptance criteria/checks, selected executor, relevant context references,
dependency artifacts, an idempotency key and a finite reserved budget. The tool
must not silently reinterpret a parent task as permission to access the whole
host, another account, secret tests or an unrelated repository.

Default worker is Luna. The primary may select another registered permitted
executor explicitly. There is no automatic Sol fallback in v1. If Luna cannot
finish, return `needs_parent` with exact attempts, check results, current patch
and remaining uncertainty. The primary decides whether to revise the task,
continue itself, or request a separate explicitly budgeted attempt. An ambiguous
native call/dispatch is uncertain and stops dependent work; never replay it.

Each attempt uses an isolated owned workspace containing the necessary parent
changes. Return the patch/artifact with its base hash; do not allow concurrent
workers to overwrite the primary's checkout. The primary owns integration and
final acceptance. Host conflict checks and independent replay protect artifact
identity but do not substitute for assessing task correctness.

Result fields include attempt/parent IDs, executor, requested and observed state,
patch/base hashes, verification commands and results, evidence references,
experience IDs, complete usage, failure reasons and unresolved conditions.
Use statuses such as `public_checks_passed`, `public_checks_failed`,
`needs_parent`, `cancelled`, `blocked` and `uncertain`. Never translate a successful
native exit or model completion claim directly into benchmark success.

Cap polling/progress verbosity. Store full worker transcripts outside the parent
context; return compact evidence summaries with progressive access. A worker can
request additional permitted context rather than receiving every historical log.
Experience packets must obey source, task, chronology, study/arm and split rules.
Failures and rejected advice remain available as versioned evidence.

## 3. Context and caching

Keep the primary session stable through planning, delegation and integration.
Each worker keeps a stable native conversation for the duration of its bounded
assignment, instead of restarting model inference for every shell action.
Fixed instructions/tool definitions and append-only interaction history should
remain unchanged where practical. Place changing assignment guidance after
reusable context without rewriting earlier messages. Measure actual rendering
and cached-input counters; do not infer cache behavior from thread identity.

Workers start fresh for unrelated assignments. Persistent native memory, global
skills and previous task histories are disabled unless explicitly registered
and matched across controls. No credentials or hidden grader resources enter
workers. Provider caches are opaque: do not assume cross-model cache sharing,
force cache warm-up with unmeasured calls, or claim cache eviction between arms.
Randomize/balance condition order and retain cold/warm observations.

Measure primary and worker input/output, uncached/cached/cache-write input where
available, retrieval/annotation inference, polling and integration overhead,
latency and total failures. Provider estimates, rate scenarios and subscription
cash remain separate. Unknown usage is not zero. Fewer parent-context tokens
alone do not establish lower total inference use.

## 4. Reuse and implementation scope

Reuse `src/ttgl/personal.py`, recorded subscription-bound transport, existing
worker isolation/MCP, checkpoint/patch custody, experience retrieval, local S3
retention and official grading through new versioned adapters. The existing
node-delegation runner is closer to this product design than a per-action RSI
controller, but its host routing and fixed DAG planning are not requirements.

The primary can express dependencies through tool contracts and revise plans
within the original budget. The host enforces dependency readiness, prevents
cyclic/recursive delegation and counts all child work against parent limits.
V1 workers cannot spawn grandchildren or change their own scope/budget. Begin
with one worker at a time; concurrency is a later distinct extension.

Do not edit frozen studies or relabel them as this experiment. Preserve existing
Luna-only source-history interpretation; Sol's primary coding role does not
authorize a different personal-history analyzer. All new model work remains
bound to the collector's same canonical Codex ChatGPT subscription. No API-key,
remote storage, account or unregistered model fallback.

Keep the current desktop dark UI and shared DataTable. Show parent decisions,
subtask attempts, exact scoped steps, patches, evidence and usage through existing
views. Full browser/worker qualification is required for changed flows; inherited
software receipts are historical rather than evidence that new tools already work.

## 5. Research comparison

Register separate conditions with matched executor models, tools, public task
information, execution environment and overall resource limits:

1. Luna working alone in the native harness.
2. Sol working alone in the native harness.
3. FrugalGPT's learned cascade, explicitly adapted to native coding episodes.
4. A released RouteLLM variant with pair-specific development calibration.
5. Our model-led Sol/Luna delegation with eligible experience retrieval.

Separate no-experience/no-recency ablations isolate the knowledge component.
Standalone and baseline executors receive the same eligible knowledge access.
Use the [baseline contracts](router-baselines-codex.md) and current proposed
protocol004; RSI is related work only, and `rsi-luna-sol-001` is inactive.
Do not pool native and other harness scores as if only routing changed.

Require benchmark eligibility, independent grading, leakage controls,
failure-inclusive task-level analysis and finite budget preparation. Start with
synthetic tool/worker fixtures and native microqualification, then an explicitly
frozen small SWE-bench Verified development pilot. Actual task IDs, training
sufficiency and complete baseline/operating-point budgets remain to be registered.

Primary question: does our full system improve the held-out accuracy–cost frontier
against the union of standalone and router baselines? Record lost solo successes, successful
cheap subtasks, integration failures and occasions where the primary declined
delegation. Include unsuccessful worker attempts and all parent coordination,
retrieval, interpretation and verification inference. Final official grades
remain outside the live model loop. No savings claim follows from architecture.

## 6. First implementation milestone

Produce a model-free end-to-end fixture where the primary-facing tool delegates
a scoped change, retrieves a permitted procedure, retains worker actions, runs
checks and returns a patch that integrates against the expected checkpoint.
Also cover failure/needs-parent, stale base, out-of-scope edits, conflicting
idempotency keys, cancellation/uncertainty, exhausted parent budgets, forbidden
cross-account access and sealed-evidence denial. Then qualify the actual native
primary and worker conversations on finite non-held-out microtasks.

Maintain an explicit status file and dated validation receipts. Keep model calls
disabled until native execution dependencies, source/model pins, isolation,
metering, benchmark controls and finite stage budgets qualify under existing
rules. This document authorizes implementation preparation, not a new automatic
benchmark or background inference schedule.
