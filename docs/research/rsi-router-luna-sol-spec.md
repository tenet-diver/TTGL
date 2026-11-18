# RSI-Router with Luna and Sol: coding-agent implementation handover

Date: 18 November 2026. Project: **Observatory**, repository/package namespace
**TTGL / `ttgl`**, branch **`work`**.

Status: **implementation specification; no experiment execution authorized by this
file alone**. Implement the software and prepare reviewable registrations. Native
execution requires the existing readiness gates, source binding and resolved
finite budgets. This document neither starts a study nor replaces a frozen study.

## 1. Decision and research question

Implement a separate **paper-based reproduction of RSI-Router adapted to the
subscription-backed Luna/Sol model pair**. First establish whether the method
improves the measured accuracy–cost frontier over matched single-model and simple
routing controls. Additional Observatory experience retrieval is a later extension.

Primary question:

> Can subtask-conditioned model assignments and evolved execution guidance reduce
> inference resources while retaining the performance of a matched Sol-only agent?

Secondary questions: which subtasks can Luna reliably execute; whether skills
help or hurt; what switching and routing consume; whether development gains
transfer to held-out tasks; and how much deployment is needed to recover the
expense of developing the router.

Luna/Sol are opaque hosted model identities, not established parameter counts.
Use “lower-cost” and “stronger” only where the registered rate scenario and
measured controls justify those descriptions. This is an empirical generalization
study, not a claim to invent subtask routing, memory or recursive improvement.
Null and negative results are valid outcomes.

## 2. Upstream reference and fidelity boundary

The reference is [RSI-Router, arXiv:2609.34712v1](https://arxiv.org/html/2609.34712v1),
28 September 2026. Its method mines subtask definitions, proposes model
assignments, evolves model-specific skills, and selects a performance–cost Pareto
population. A small model identifies the upcoming subtask before each execution
step. Its harness uses mini-SWE-agent; its model pair is DeepSeek-V4.1-Flash and
Qwen3.5-9B. The paper uses six iterations and four candidates per iteration. Its
coding splits are 32/32/32 for SWE-bench Verified and 32/32/25 for Terminal-Bench
2.0, with repeated test evaluation. Its reported small-model price is estimated
using a 1:30 reference ratio. These are upstream facts, not proposed Luna/Sol
prices, required spending, or evidence of our own performance.

An official RSI-Router implementation was **not located** in the 18 November
paper/repository review. Do not claim that none can exist: recheck before coding.
The authors' [LLMRouterBench](https://github.com/ynulihao/LLMRouterBench) announces
the paper but is a separate framework. It is not an interchangeable implementation.

Create `fidelity-matrix.json`, with one row per paper requirement: source section,
implemented behavior, test receipt, unspecified upstream detail, chosen default,
and deviation. Reproduction-critical distinctions:

- **Step** means one host-dispatched environment action, not an entire native
  Codex session and not a retrospectively labelled transcript segment.
- The runtime uses a frozen definition set and assignment table. The optimizer
  can change these only between development iterations.
- Skills are model/subtask-specific instruction text attached to an executor
  request. They do not grant tools, permissions, memory access or success status.
- No extra large-model DAG planner, checkpoint fallback, semantic memory search,
  online test-time learning or expert conversation is added to the reproduction.
- Model pair, transport, context policy, split sizes, execution limits, sampling
  and any inaccessible upstream prompts are declared adaptations.
- If an official release appears, assess its license, exact revision and full
  dependency closure before preferring it to this paper-based implementation.

Preserve the paper's benchmark versions for any historical comparison. Never
call a different model pair, sample or harness an exact numerical replication.

## 3. Read these repository sources first

Read `AGENTS.md`, `docs/research/HANDOVER.md`, ADRs 0006 and 0007,
`docs/paper/README.md`, `docs/research/codex-metering.md`,
`docs/security/dependency-security-policy.md`, `SETUP.md`, and
`docs/research/experience-routing-implementation-status.md`.

The existing `experience-routing-001` implements large-plan/node delegation and
public-outcome-based retrieval. It is **not** RSI-Router. Keep its six arms,
contracts, source hashes, registrations and historical receipts intact. Current
software evidence includes 48 Python and 82 web/database checks; these do not
qualify the new controller or establish model results.

Reuse existing components through narrow adapters:

| Existing component | Reuse | Important boundary |
| --- | --- | --- |
| `src/ttgl/personal.py` | Native transport, event parsing and usage reconciliation | Do not change frozen generation code just to add this study |
| `src/ttgl/experience_routing/backend.py` | Recorded, source-bound calls and artifact retention | Existing whole-attempt executor mode is not a one-step interface |
| `src/ttgl/experience_routing/ledger.py` | Native response deduplication and pricing arithmetic | Add RSI role accounting in the new adapter; do not relabel every call as an executor |
| `src/ttgl/experience_routing/checkpoints.py` | Immutable source snapshots and replay checks | Used for diagnostics/artifact custody, not an unregistered runtime fallback |
| `src/ttgl/experience_routing/benchmarks.py` | Public field projection and evaluator boundaries | Grades stay outside the solving loop |
| `src/ttgl/evaluation.py`, existing isolated workers | Official replay and owned task environments | Qualify actual image/tools; no silent environment substitution |
| Existing experience service and UI | Study scopes, traces and result inspection | Use separate RSI record types; do not pretend every route is a DAG node |

Before importing a shared module, check whether it imports unrelated numerical,
model-serving or benchmark dependencies. Reuse functions without installing the
entire historical research stack. Any necessary shared-code change requires
checking active ownership/frozen hashes and a new versioned implementation path.

## 4. New code and registration layout

Proposed new package: `src/ttgl/rsi_router/`. Proposed registrations:
`experiments/rsi-luna-sol-001/` and `results/rsi-luna-sol-001/`.
These paths are deliverables to implement, not existing commands or results.

| Module | Responsibility |
| --- | --- |
| `contracts.py` | Strict serializable schemas and cross-record invariants |
| `native.py` | Tool-disabled, bounded model decisions through the existing subscription transport |
| `agent.py` | Host-owned one-action loop shared by every scored condition |
| `context.py` | Deterministic router/executor views, skill injection and overflow policy |
| `subtasks.py` | Definition versions, training segmentation and pre-action identification |
| `skills.py` | Scoped skill versions, provenance and bounded proposal admission |
| `evolution.py` | Candidate generation, before/after evaluations and optimizer limits |
| `population.py` | Development Pareto population, dominated archive and deterministic selection |
| `baselines.py` | Single-model, random-step and cascade policies |
| `campaign.py` | Frozen assignments, budgets, ordering, stop/resume and artifact custody |
| `benchmarks.py` | Small adapters to existing benchmark/evaluator code |
| `accounting.py` | RSI role tags, development/deployment totals and cost sensitivities |
| `analysis.py` | Paired estimates, uncertainty and frontier outputs |
| `fixtures.py`, `__main__.py` | Model-free mechanism cases and explicit finite CLI stages |

Add `tests/rsi_router/`; favor tests of boundaries and failure cases over tests
that simply restate an implementation. Reuse maintained JSON Schema/Zod tooling
already reviewed in the repository. Do not introduce a new experiment framework,
agent runtime, optimizer service, vector store or model server by default.

## 5. Model identities, authentication and permissions

Draft role identities:

| Role | Draft model | Allowed information |
| --- | --- | --- |
| Pre-action subtask identifier | `gpt-6-luna` | Public task, definitions, bounded recent public interactions, previous prediction |
| Lower-cost executor | `gpt-6-luna` | Public task and common executor transcript plus applicable skills |
| Strong executor | `gpt-6.1-sol` | Same executor view and tools under the selected condition |
| Research proposal agent | Same pinned Sol | Training evidence and permitted development aggregates |
| Observatory historical/trace annotation | Source-bound Luna | Existing analysis policy; not replaced by Sol |
| Final evaluator | Existing prescribed executable harness | Sealed evaluation resources, no model decision authority |

Resolve model availability, exact returned identity, reasoning effort, service
tier, context/output limits, Codex executable and protocol version before freeze.
Aliases above are proposals, not evidence that an account exposes them. Record
unversioned backend limitations; do not claim pinned weights if the provider
does not expose a snapshot. Detectable identity/capability changes stop a campaign.

Every model invocation, including proposal calls and microchecks, must use the
same registered local collector's Codex ChatGPT subscription/account binding.
Verify the canonical home/account hash before invocation and retain its binding
receipt. No API keys, another account, alternate provider or automatic model
fallback. Source-bound Luna analysis restrictions remain unchanged. Sol's research
optimizer sees this experiment's permitted development evidence, not arbitrary
personal histories or another source's raw logs.

The client holds authentication outside actors. The actor receives no host home,
credentials, database secrets, raw-log bucket credentials, sealed tests, reference
patches, prior study solutions or native persistent memory. Disable native user
configuration, project/skill injection, unrelated MCP tools, apps, web search,
subagents, automatic compaction/context transforms and hidden expert delegation.
Record effective configuration and test actual behavior, rather than assuming a
flag guarantees isolation. Retain only provider-exposed events; do not seek hidden
chain-of-thought or rely on it for handoff.

## 6. The first gate: an observable one-action execution loop

Evaluate a pinned [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent)
loop/model adapter first. Prefer its established action/environment conventions
where compatible with our subscription transport. If its dependency or API
requirements prevent reuse, record why and add only the missing adapter around
TTGL's existing isolated command executor. Do not install it before review.

The preferred native boundary is a tool-disabled structured model response.
The host supplies public state, receives one action, validates it, then dispatches
it to the owned benchmark environment. This avoids handing an uncontrolled native
agent loop the whole task. Reusing a read-only decision path still requires a
canary proving that no native tool action occurred.

Allowed actor response union:

```json
{"kind":"command","command":"python -m pytest public_tests/test_example.py","timeout_seconds":60}
```

or `{"kind":"finish","summary":"..."}`. The field named `summary` is not a
grade. No action arrays, callable code, host paths, environment changes outside
the actor, background work surviving the episode, or additional model calls.
One command may contain ordinary shell syntax; atomicity refers to the host
dispatch, not the number of subprocesses created by that command. Preserve exact
command, exit/timeout status, output bytes and truncation metadata.

For a routed action:

1. Build the pre-action view from already completed public events.
2. Invoke Luna once to classify the upcoming subtask using current definitions.
3. Look up the selected model in the immutable candidate assignment table.
4. Attach only that model/subtask's selected skills, within fixed token limits.
5. Invoke that executor for one action or finish response.
6. Validate and durably retain the decision; execute at most one action.
7. Retain its result and advance the event sequence before the next decision.

Every decision uses the same underlying actor filesystem and a common explicit
public transcript. Switching models must preserve completed changes/results;
it must not give Sol the task's original checkout while Luna's edits disappear.
Fresh native threads per decision are the default adaptation, with explicit
transcript replay for both single-model and routed controls. No private model
reasoning is transferred. An alternative continued-thread transport requires a
new named qualification profile, including cache/accounting equivalence checks.

Router input contains task text, current definition/rules, the previous predicted
label and the last **three completed action/result interactions**. No future action,
eventual grade or retrospective label appears. Executors receive the same public
history policy across conditions, not just those three interactions. Pin the
tokenizer and deterministic truncation/overflow behavior; log omitted-byte hashes.
Do not secretly add a model summarizer. If context cannot fit, terminate with a
registered context-limit outcome rather than invoking an unmetered helper.

The router emits `{definition_version, subtask_id}`. No model probability is
treated as calibrated success confidence. A syntactically valid `unknown` label
maps to Sol without skills in all routed conditions. Malformed output is retained
and terminates the episode as a format failure in v1; no free correction call.
Transport uncertainty stops the campaign. These defaults are declared adaptations
where upstream behavior is unspecified, not claims about the paper's code.

The initial previous-label value is null and recent history is empty. Reset these
at each episode boundary. Every event and context truncation belongs to the
current assignment; switching must not import another task's state. Unexpected
native tool use is an isolation failure that stops the stage, not merely a
low-scoring task to continue past.

Qualification must demonstrate L→S→L and S→L→S source/history continuity, router
timing before every action, exactly one environment dispatch, finish semantics,
tool denial, no persistent memory, usage reconciliation and correct failure
retention. If this fails, stop. A retrospectively annotated full Codex run must
not be reported as the requested reproduction.

## 7. Core data contracts

All records include `schema_version`, `study_id`, immutable record ID, creation
sequence, source-binding hash, source/code hashes and artifact references. Use
strict schemas; reject unexpected fields at public/evaluator projections.

| Record | Required fields beyond the common envelope |
| --- | --- |
| `Task` | Dataset/revision, task ID, split, repository/base commit or environment digest, leakage group, projected public prompt hash, evaluator pin |
| `Assignment` | Task, condition, candidate version, repeat, order block, limits, actor identity, effective model/context/tool profile |
| `SubtaskDefinitions` | Iteration, stable label IDs, definitions, pre-action identification rules, parent/split/merge lineage, allowed evidence IDs |
| `Skill` | Version ID, applicable label IDs, executor identity, instruction text/hash, training provenance, supersession, admission status, token count |
| `Candidate` | Definition version, exhaustive label→model mapping, skill IDs per label/model, parent candidate IDs, iteration, proposal invocation, configuration hash |
| `Decision` | Assignment/action index, input-event watermark/hash, Luna invocation, predicted label, selected executor, applied skills, request/output hashes, actual usage |
| `Action` | Decision ID, proposed command/finish, validation result, dispatch ID, output hashes, exit/timeout, before/after source snapshot references |
| `Invocation` | Role/purpose, requested/returned model, thread/response IDs, usage evidence, latency, source binding, terminal/uncertain status, raw references |
| `DevelopmentEvaluation` | Candidate, train/validation scope, assigned tasks/repeats, successes, unresolved counts, resource totals, permissible feedback projection |
| `PopulationSnapshot` | Iteration, evaluated candidate hashes, non-dominated IDs, dominated archive, tie policy and aggregate evidence references |
| `Grade` | Sealed patch hash, prescribed evaluator revision, nonempty test count, original report hash, pass/fail/invalid/unknown and reason |

Label IDs are local to a version; a split/merge creates a new version, never
reinterprets an earlier decision. A skill cannot refer to future definitions or
another model without a recorded reassessment. Deduplicate repeated instruction
text deterministically. A router that maps every label to Sol is legal and must
be reported as a collapsed/all-large policy, not successful cheap delegation.

Proposed default limits: at most 12 discovered subtask labels plus `unknown`;
at most two skills per selected model/label; combined skill text at most 2,000
tokens per execution request; at most 4,000 tokens for router definitions/rules.
These are engineering defaults to qualify in development and freeze, not paper
hyperparameters. Never truncate an executable action into a different command.

## 8. Development optimizer

Use Sol for optimizer proposals; use source-bound Luna for explicit trace
segmentation/annotation where needed. Charge both. Segmentation is developmental
retrospective interpretation, distinct from the live Luna prediction.

Each iteration follows this registered process:

1. **Definitions:** construct/update a bounded vocabulary from eligible training
   traces. Use labels as reusable objectives, not benchmark IDs or solution
   fingerprints. Audit a fixed training sample for forward-identifiability.
   Allow at most two definition refinement rounds per iteration.
2. **Assignments:** generate the registered number of complete model-assignment
   candidates with inherited applicable skills. Use independent proposal IDs;
   serial execution is acceptable and is not a concurrency result.
3. **Before-skill evaluation:** run candidates on the frozen training/validation
   assignment list. Each episode starts from pristine source, not a predecessor's
   attempted patch.
4. **Skill update:** give the proposal agent each candidate's training evidence
   and the matched Sol training evidence. Propose bounded model/label-specific
   execution guidance. Assign new immutable skill/candidate identities.
5. **After-skill evaluation:** evaluate the updated candidates on the same declared
   development tasks. Keep failed candidates and both evaluation versions.
6. **Population update:** compute the observed development non-dominated set;
   retain dominated candidates as bounded negative experience. Produce a complete
   iteration receipt before proceeding.

The initial population includes all-Luna and all-Sol policies with no skills.
Do not require population members to exceed Sol accuracy: preserve cheaper/lower
accuracy trade-offs for frontier analysis. In development, A dominates B if A has
no lower aggregate success and no higher mean online scenario cost, with at least
one strict inequality. Tie-break equal points by lower routing overhead then
candidate hash; retain membership/selection reasons. This empirical dominance is
not a statistical claim of superiority.

If stored candidates exceed the proposal context allowance, select a deterministic
bounded view using a frozen rule over development metrics, frontier spread,
iteration and hashes. Preserve the full archive separately. Specify that rule
before the first iteration; do not hand-pick anecdotes after seeing test results.

The optimizer receives training public traces and training **scalar final scores**
after episodes are sealed. Validation feedback is aggregate count/cost only, with
no task IDs, task-level grades, traces, failure messages or hidden tests. Test
feedback is inaccessible until all candidates, skills and selection choices are
frozen. No reference patch, grader test content or hidden test-name list enters
any model prompt. A train-only score can guide later training iterations; it
cannot rescue or alter the episode that generated it.

For identical candidate/task/repeat/source/seed/effective-runtime hashes, an
already retained completed evaluation may be reused if this was preregistered.
It is one actual invocation with references, not a newly independent repeat.
Different skill hashes require new assignments. Never automatically repeat an
uncertain or started native assignment to fill an empty cell.

## 9. Experimental conditions

All scored conditions use the same agent loop, public task fields, actor tools,
context/overflow policy, per-episode action limits and final evaluator. Sol-only
must not use a richer native harness than the routed policy.

| ID | Condition | Purpose |
| --- | --- | --- |
| `SOL` | Sol executes every action; no skills and no router calls | Strong matched control |
| `LUNA` | Luna executes every action; no skills and no router calls | Lower-cost standalone control |
| `RANDOM` | Host seeded 50/50 executor choice per action, no skills | Tests learned assignment versus model mixing without inference overhead |
| `CASCADE` | Luna-first episode; one Sol episode from original checkpoint only after a registered public failure | Simple fallback alternative; charge all Luna and Sol work |
| `RSI-CHEAP` | Frozen low-cost candidate selected from development population | Cost-oriented frontier point |
| `RSI-RETAIN` | Frozen candidate selected at 95% of development Sol success | Retention-oriented frontier point |
| `RSI-QUALITY` | Frozen candidate selected at development Sol success | Primary matched-quality point |
| `RSI-NOSKILL` | Exact `RSI-QUALITY` definitions/mapping, with skill context masked | Paired skill-effect ablation |

All routed conditions pay for Luna identification, even when it selects Luna or
Sol repeatedly. `RSI-NOSKILL` still pays identification and uses unchanged label
definitions/mapping; resulting trajectories can diverge naturally.

`CASCADE` has a **shared** episode action/token/time budget across both attempts,
not two full budgets. Reserve a fixed 50% of the total for Sol before launch;
Luna cannot consume that reserve. Its trigger must be a public deterministic
verification failure, explicit unsuccessful finish, or exhaustion of Luna's
allocated budget. The official grade never triggers fallback. A known successful
public check is not an official success and does not suppress independent grading.
An uncertain transport/infrastructure result stops rather than requests Sol.
Record this precise cascade as an Observatory baseline, not an RSI feature.

Freeze selected candidates by validation metrics only: `RSI-CHEAP` minimizes cost
with validation success at least 80% of Sol; `RSI-RETAIN` uses 95%; `RSI-QUALITY`
uses 100%. Minimize mean cost, then maximize success, then tie-break by hash.
Use the same Sol validation denominator. If Sol has zero successes, selection is
undefined and the development gate fails. If a selected candidate is all-Sol or
multiple labels select the same candidate, retain that fact and deduplicate actual
test assignments; do not pretend identical policies are independent evidence.

V1 evaluates the three frozen representatives, not a test-selected winner from
every candidate. An optional full-population test plot must be registered before
test execution and is descriptive; it cannot change the primary candidate.

Do not add Observatory structured experience, the existing large-model planner,
human repair, multiple-expert conversations or weight training to these conditions.
Each later extension gets a separate protocol and matched control.

## 10. Benchmarks and staged campaign

### 10.1 Primary: SWE-bench Verified

Use the official [Verified dataset](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified)
and [containerized evaluator](https://www.swebench.com/SWE-bench/guides/evaluation/).
Pin dataset revision, environment/base commits, harness revision, actor and grader
image digests, prompts and artifact policy. Project only approved public fields;
never hand the actor the original full dataset dictionary. Export standard
instance/model/patch predictions and retain original evaluator reports.

Default proposed stages, subject to actual eligibility and finite budgets:

| Stage | Tasks and settings | Allowed conclusion |
| --- | --- | --- |
| `Q0` qualification | Synthetic fixtures first; then at most 6 native micro-episodes on 2 declared non-held-out tasks, exercising switch/no-switch paths | Transport, boundaries, metering and actual grading work |
| `D1` development pilot | 8 training + 8 validation tasks; 2 iterations × 2 candidates; one episode per candidate/task/variant; no test tasks | Whether implementation and optimization are worth scaling |
| `D2` main development | 32 training + 32 validation tasks, including declared D1 tasks; 6 iterations × 4 candidates; one development repeat as the default adaptation | Frozen candidates and development frontier |
| `T1` held-out evaluation | 100 fresh task IDs fixed before any held-out execution; up to 8 distinct conditions × 3 independent repeats | Paired generalization estimates with uncertainty |

The first predetermined 32 IDs of T1 may be shown as a paper-scale descriptive
slice. They are part of the same frozen 100-task experiment, not a separate
confirmatory replication or an adaptive stopping rule. Do not inspect that slice
and then modify policies before completing the rest. Native sampling settings
and any inability to set seeds are retained; repeats remain clustered by task.

The 100-task allocation is a planning target, **not** a claim that enough eligible
tasks remain or that it can prove a tight noninferiority margin. Produce a
precision/power assessment from development discordance before freeze. If 100
fresh tasks are insufficient or unavailable, register the feasible descriptive
study before test access, disclose the limitation, or propose a new clean
benchmark under a separate protocol. Do not silently expand into reserved tasks
or claim equivalence from a nonsignificant difference.

D1 is an optimizer integration pilot, not a held-out comparison. D2 either starts
clean or inherits D1 under an explicit manifest. The default is a fresh D2
population with D1-informed implementation frozen and D1 traces unavailable as
extra memory except through declared D2 training inputs. Record all D1 research
expense even when its candidates are discarded.

### 10.2 Secondary: terminal operations

For historical paper comparability, prepare a distinct **Terminal-Bench 2.0**
profile with 32 training, 32 validation and 25 held-out tasks and the same method
and controls. This is a secondary phase after the primary harness qualifies.
Freeze actual IDs and check overlap with previous terminal runs. Do not assume
this split is possible after reviewing our exposure and environment constraints.

Also support a separately labelled **Terminal-Bench 2.1 adaptation**, if that is
the maintained and runnable choice. The maintainers report corrections to 28 of
89 tasks in [the 2.1 announcement](https://www.tbench.ai/news/terminal-bench-2-1).
Different benchmark versions are not pooled or compared as identical scores.
Task-family/version aliases must remain in one leakage group across 2.0 and 2.1.
Never train on a 2.0 task and call its corrected 2.1 counterpart unseen transfer.

Reuse the existing reviewed Harbor/evaluator integration where compatible; do
not write replacement success tests. Official verifier files/reward resources
must be absent from actor-visible mounts and injected only in pristine grading.
Honor pinned task CPU/RAM/time constraints equally across arms. If a task needs
network/download behavior that cannot be pinned and reviewed, resolve its
eligibility before selection, not after observing candidate performance.

### 10.3 Later cross-domain replication

ALFWorld, ScienceWorld and WebShop are optional follow-up domains, each with its
own reviewed environment and disjoint split manifest. They are useful for testing
whether gains depend on task structure, but are not prerequisites for the first
coding result. Do not claim a five-domain reproduction from the coding studies.
SWE-Gym, SWE-smith, Commit0 and Pro V2 remain separate studies; do not substitute
them into this reproduction or consume their existing reservations automatically.

## 11. Eligibility, leakage and intervention policy

Before selecting tasks, inventory all historical/reserved native assignments,
published-result replays, analyzed trajectories, reference inspections and task
aliases. Public replay exposure is not automatically a new native attempt, but
must be recorded; inspected solutions cannot become fresh held-out experience.

Build exclusions by instance ID, canonical issue/PR, normalized prompt hash,
reference/source-patch lineage, base-commit relationships and synthetic origin.
Resolve near-duplicate fixes, forward git history, cached solutions and alternative
benchmark versions. A repository may contribute different independent tasks to
multiple splits only after issue/fix-lineage auditing. Do not describe this as
repository-held-out transfer. A later repository-held-out test is a distinct study.

Register task IDs before model calls; seed selection from public metadata, not
observed outcomes. Preserve repository coverage with a deterministic stratified
rule and document all pre-run environment exclusions. Audit all selected tasks
with pristine empty/reference controls in the sealed evaluator. A base checkout
already satisfying all required checks is an invalid task/control, not success.
Zero prescribed tests cannot yield a valid grade. Reference solutions never
enter solver mounts, optimizer prompts or UI evidence available to the solver.

After allocation, retain every missing/failed/invalid assignment in the manifest.
Do not replace tasks after seeing outcomes. Any legitimate pre-inference
replacement uses a preregistered reserve order and an exclusion reason affecting
all arms; after test access, changes require a new labelled analysis/protocol.
No human edits or hints in scored runs. Human-assisted diagnostics are separate.

## 12. Budgets, cost accounting and campaign control

Use one active actor initially. Parallel optimizer candidates can be evaluated
serially. Do not add a background monitor or auto-resume inference schedule.

Proposed per-parent limits for development qualification: 80 external execution
actions, at most 80 identifier calls and 160 total model invocations, 4 million
observed input+output tokens, 45 minutes wall time. Per-command timeout is at most
120 seconds and bounded by remaining time. Per-native-call timeout is at most
180 seconds. These defaults must be tested on development cases, made compatible
with benchmark limits, and frozen equally across conditions. All cascade work
shares these parent limits. Finish requests and malformed/failed calls consume
the invocation/token budgets.

Campaign ceilings must separately bound parent episodes, optimizer calls, all
native invocations, aggregate tokens, elapsed time and scenario expense. Null,
negative, infinite or unresolved caps block enabled execution. Reserve enough
headroom before a call for its configured maximum input/output use; an unknown
usage report stops further calls until reconciled. Quota/reset wait time and
rate-limit failures are recorded, not hidden by retries or account switching.

Zero automatic retries prohibits replaying a started/uncertain model invocation
or environment dispatch. An executor may intentionally repair a known command
failure through a new recorded action within its remaining budget. That is
ordinary agent work, not permission to duplicate a retained native attempt.

Scale estimate, **not a launch authorization**: D2's before/after candidate
evaluations alone are `6 × 4 × 2 × (32 + 32) = 3,072` task episodes at one
development repeat. Initial Luna/Sol controls add 128. Eight distinct T1
conditions over 100 tasks with three repeats add 2,400. Proposals, annotation,
qualification and any extra validation add further expense. Repeated identities
may reduce actual calls only under the declared reuse rule, never create more
independent evidence. Print this forecast before enabling any stage.

Derive positive token/time/scenario ceilings from Q0/D1 measurements and the
remaining approved allocation before D2/T1 freeze. This spec does not invent an
API budget or authorize a large quota-consuming launch. Preparation should
continue without model calls when runtime or budgets remain unresolved.

Keep four cost reports:

1. **Online inference:** executor, identifier, model-request retransmission and
   skill/context tokens, including failures, switching and every billed attempt.
2. **Development:** baseline discovery, segmentation, proposals, candidate search,
   validation and discarded/failed runs, with shared actual invocations counted
   once and logical condition allocations explicitly distinguished.
3. **Amortized system cost:** online mean plus development cost divided by a
   prespecified deployment volume, such as 10, 100, 1,000 and 10,000 future tasks.
4. **Other resources:** command/evaluator compute, storage and researcher work,
   separately measured or marked unknown. Do not turn these into free resources.

Native tokens, provider-estimated credits, API-equivalent scenario USD and actual
subscription cash are different fields. Fixed subscription fees are not reduced
by definition when tokens fall. Record cache reads/writes and whether reasoning
tokens are already included in output. Never add them twice. Reconcile cumulative
thread counters and response identities using existing code; missing/all-zero
defaults remain unknown. Every annotation/proposal call appears in accounting.

Do not transplant the reference paper's model-price ratio to Luna/Sol. Freeze
actual available rate/credit evidence and separate sensitivity scenarios when
prices are not available. Report raw per-model token mixes and an explicitly
labelled relative-price sweep (for example 2, 5, 10, 20, 30 and 50) with the same
tokenization convention. This sweep is a hypothetical sensitivity analysis,
not a newly verified provider quote or a replacement for native credit evidence.

Freeze one primary rate scenario before development selection. Use it consistently
for candidate population updates and the primary held-out comparison. Repricing
the same frozen policies is a sensitivity analysis; selecting a new policy after
seeing its held-out results at another price ratio is not an independent test.

## 13. Statistical analysis and Pareto claims

The independent sampling unit is a task. Repeats, subtasks and decisions within
it are correlated. For each condition, average successes and resource use within
each task, then across the registered task denominator. Report absolute accuracy,
paired accuracy difference, relative retention, mean cost/task, cost/resolved task
when defined, failures, latency and executor/action shares.

Primary comparison: the validation-selected `RSI-QUALITY` versus `SOL` on T1.
Secondary comparisons: the other frontier representatives, cascade, random and
the matched no-skill ablation. Plot raw success against online cost, plus
normalized cost `C_condition / C_SOL` and retention `p_condition / p_SOL` when
denominators are positive. No point is chosen using test success or cost.

Use paired task-cluster bootstrap intervals with a frozen seed/count (default
10,000), retaining all repeats for a sampled task together. Include repository
stratification or a repository-cluster sensitivity analysis; do not pretend
100 tasks represent 100 independent repositories. Use simultaneous intervals
across the three frozen frontier points for joint superiority claims; document
the chosen implementation before unsealing test results. A descriptive empirical
frontier and statistically supported dominance are separate outputs.

Predeclared practical target: at least 10% lower online scenario cost with at
least 95% of matched Sol accuracy. This is a proposed reproduction target,
distinct from older 90%-saving/95–95 project aspirations. Assess retention via
`p_RSI - 0.95 * p_SOL`; do not confuse 95% relative retention with a five-point
absolute margin. Strong target evidence requires the relevant joint lower quality
bound to be nonnegative and upper cost-ratio bound to be at most 0.90. Also report
observed parity and bounds without declaring a target met when underpowered.

Preserve unknown grades and infrastructure failures as unresolved. Report the
entire assigned denominator, conservative success bounds and a preregistered
valid-control sensitivity view. Missing cost is not zero, and a complete-case
subset cannot establish a primary savings claim. Unknowns sufficient to change
the conclusion make the result inconclusive. Never infer equivalence from
overlapping confidence intervals or from failure to reject a difference.

Show the no-skill comparison even if memory hurts. Explain whether savings come
from useful Luna work, fewer execution actions, reduced context, early failure,
weaker checks or omitted accounting. An oracle chosen using held-out grades may
appear only as an unattainable diagnostic bound, never a deployable policy.

Optional secondary frontier statistic: hypervolume using normalized cost,
absolute task accuracy and the frozen reference point `(1.25, 0)`. Report that
choice and sensitivity; do not use the metric to select a test winner. Report
online and amortized frontiers separately. For development cost D and positive
online saving per task s, estimated break-even volume is `D/s`; if s is unknown
or nonpositive, break-even is unknown or unattained, not zero.

## 14. Artifacts, storage and observability

PostgreSQL owns study state, immutable candidate/definition/skill versions,
assignments, provenance, current pointers and transactional outbox entries.
ClickHouse holds deduplicated analytical decisions/events and resource facts.
The approved local S3 provider retains exact request/response/event/action/
checkpoint/evaluation bytes under existing checksummed retention semantics.

Use literal-loopback S3 only. Current SETUP documents the specifically approved
local SILO alternative and the blocked Garage candidate. This study does not
change that approval or permit remote raw-log storage. Retention must succeed
before an action is treated as durably dispatched or an artifact is published.
An ambiguous dispatch remains uncertain; never execute it again automatically.

Suggested registration/artifact tree:

```text
experiments/rsi-luna-sol-001/
  README.md
  config.draft.yaml
  protocol.json
  contracts.schema.json
  fidelity-matrix.json
  model-catalog.json
  source-inventory.json
  exclusion-registry.json
  task-manifest.json
  assignment-manifest.json
  context-policy.json
  selection-rule.json
  rate-scenarios.json
  power-and-precision.json
  runtime-isolation.json
  readiness.json
  source-hashes.json
  prompts/
results/rsi-luna-sol-001/
  software-validation.json
  qualification-summary.json
  development-summary.json
  frozen-selection.json
  heldout-summary.json
  frontier.json
  report.md
```

These are names to implement. Unrun stages have empty manifests/explicit
`not_run` status, never invented passing data. Raw private attempts, credentials,
source traces and benchmark solutions remain in ignored private storage. Public
reports contain sanitized hashes, protocols, eligibility counts and aggregates.
The solver process cannot fetch sealed reports through the app, MCP or S3.

New database tables, if needed, use additive numbered migrations after the actual
latest migration. On this checkpoint 008 is latest; do not assume 009 remains
available when implementation begins. Never rewrite applied migrations. Prefer
existing study/attempt references plus small RSI-specific tables over duplicating
the experience service. Delivery of the core runner must not depend on a UI rewrite.

In the existing desktop dark Experiments/Delegation/Results views, expose study
status, candidate lineage, split-safe aggregate metrics and task→predicted-subtask
segments→exact actions. Repeated labels can produce multiple segments; preserve
pre-action predictions separately from retrospective annotations. Every list uses
the existing shared `apps/web/src/components/data-table.tsx` with its built-in
search/filter/sort/pagination. Reuse existing charts for frontier and cost views.
Show unknown outcomes and historical versus current-host validation explicitly.
No mobile, light-theme or new chart-framework work is required.

## 15. CLI and freeze behavior to implement

Proposed interface, not commands that already exist:

```sh
PYTHONPATH=src python -m ttgl.rsi_router inspect --config experiments/rsi-luna-sol-001/config.draft.yaml
PYTHONPATH=src python -m ttgl.rsi_router inventory --root . --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router prepare --config CONFIG --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router fixture --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router qualify --freeze QUALIFICATION_FREEZE --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router evolve --freeze DEVELOPMENT_FREEZE --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router select --development DEVELOPMENT_RECEIPT --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router freeze --config CONFIG --stage T1 --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router run --freeze TEST_FREEZE --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router grade --manifest SEALED_MANIFEST --output PRIVATE_NEW_PATH
PYTHONPATH=src python -m ttgl.rsi_router report --study STUDY_MANIFEST --output PRIVATE_NEW_PATH
```

`inspect`, `inventory`, `prepare`, `fixture`, `select`, `freeze` and `report` make
no model calls. `freeze` has no installation/download side effects and refuses
missing pins, readiness, binding or finite caps. `qualify`, `evolve` and `run`
require an enabled stage freeze plus an explicit execution environment flag such
as `OBS_ALLOW_RSI_MODELS=1`. This two-part guard prevents accidental model calls;
it is not a new blanket permission requirement for ordinary implementation work.

Each output identity is write-once. Freeze includes exact code/dependency hashes,
task IDs/order, policies, skills, prompts, model/context settings, images,
evaluator, rates, budgets and source binding. Record detected source drift and
stop. Reuse only already completed retained assignments matching all required
identities. A crash between “started” and a verified terminal receipt is uncertain
and requires investigation, never `--retry-all` or deletion of the started marker.
Evaluator-only replays use the same sealed candidate bytes and new evaluation
IDs; they cannot regenerate a model patch.

Draft configuration must default to execution disabled, automatic retries zero,
one worker, empty task lists and unresolved pin/budget fields. The lack of pins
must remain visible as failed readiness, not silently populated from defaults.
All scored conditions are explicit; the default CLI cannot run an entire future
benchmark suite because one development stage finished.

## 16. Required tests and qualification evidence

| Area | Required evidence |
| --- | --- |
| Native action boundary | Unexpected tools rejected; one response dispatches at most one action; finish dispatches none; L/S switching preserves source and explicit history |
| Router chronology | No future action/result or retrospective grade in identifier input; three-interaction view reproducible; unknown/invalid behavior deterministic |
| Skills | Correct version/model/label injection only; mismatches/stale provenance rejected; skill masking leaves mapping intact; instruction text cannot authorize host access |
| Optimizer | Fixed definitions within iteration; bounded refinements; before/after lineage retained; exhaustive assignments; dominated archive and ties reproducible |
| Exposure | Sealed canaries absent from actor/client prompts/MCP/UI; validation projection excludes per-task outcomes; test feedback cannot change selection |
| Accounting | Repeated cumulative events/response IDs not double-counted; cache/reasoning rules; router/optimizer failures charged; unknown usage blocks cost claims |
| Budgets | Parent and stage caps enforced before calls; cascade shares/reserves parent budget; no fresh budget after switching/candidate revision |
| Persistence | Raw-retention failure, partial dispatch, cancellation and last-assignment crash remain explicit; concurrent writers cannot duplicate a dispatch |
| Reproducibility | Candidate/config/source drift rejected; seeded host random policy stable; completed assignment reuse distinct from an independent repeat |
| Benchmarks | Pristine empty/reference controls; nonempty prescribed checks; exact sealed patch replay; timeout/test/infrastructure failures distinguished |
| Analysis | Task-cluster pairing, missing/both-missing assignments, zero-success denominator, duplicate selected candidates and no-skill effect tested on known fixture tables |
| UI | Existing shared list controls and task/step scope exercised in desktop dark; no sealed-test details leaked before unsealing |

Use deterministic fake models and real temporary files/commands for the model-free
suite. Label every synthetic receipt. Add only necessary database/integration
checks for the new records. Before live execution review the exact actor image,
MCP/transport dependencies if used, evaluator environment and any benchmark
packages under the standing security policy. The blocked pnpm assessment is not
permission to install a known-affected tool. Existing SILO's narrow exception does
not waive findings in other packages or images.

Native Q0 receipts are required to claim a working model boundary. Software
fixtures, successful schemas and a UI screenshot cannot establish that Luna/Sol
follow the intended action protocol or that a grader measures the right artifact.

## 17. Implementation work packages and acceptance gates

1. **WP1: inventory and fidelity.** Check current branches/processes/ownership;
   inventory exclusions, dependencies, upstream code availability and paper gaps.
   Deliver the fidelity matrix and an explicit reuse/implementation decision.
2. **WP2: contracts and one-action runner.** Implement schemas, common loop,
   native adapter interface, deterministic fixtures and the single-model controls.
   Gate: complete model-free switching, exposure, budget and retention tests.
3. **WP3: candidate/skill optimizer.** Implement bounded segmentation, definition
   revisions, model mappings, before/after evaluation, archives and selection.
   Gate: a synthetic multi-iteration campaign with reproducible known frontiers.
4. **WP4: benchmark integration and freeze.** Prepare eligible manifests, pinned
   actors/evaluators, sealed controls, role accounting and precision/cost forecasts.
   Gate: actual source binding and all Q0 prerequisites valid.
5. **WP5: native Q0.** Execute only the finite frozen microqualification stage.
   Gate: genuine model/action/usage receipts and independent artifact replay.
6. **WP6: D1 pilot.** Run the registered small development campaign; inspect
   failures, overhead, collapse and skill effect. Fix implementation only between
   versioned units. Gate: updated finite D2/T1 plan based on observed resources.
7. **WP7: main study.** Freeze D2, evolve, select and freeze T1 before test access.
   Complete assignments or publish explicit stopped/incomplete status. Gate:
   independent grade/accounting audit and failure-inclusive paired report.
8. **WP8: integration and documentation.** Inspect retained records through the
   existing UI, validate changed desktop flows, publish sanitized reports and
   update HANDOVER/status docs with exact completed/pending gates and commands.

Implementation may be complete while empirical execution remains gated. Distinguish
“software implemented,” “native-qualified,” “development complete,” “held-out
complete” and “target supported.” Do not declare all functionality validated from
synthetic tests, or declare the research successful from an attractive frontier.

## 18. Expected report and next decision

The report must answer which implementation choices were adapted; whether routing
acted before execution; which labels/models were actually used; what skills changed;
how failures, lost Luna successes and Sol rescues were distributed; whether skills
helped at matched mappings; the selected versus realized frontier; online and total
development economics; uncertainty and exposure limits; and the next experiment
supported by the results. Include failed iterations and candidates.

Only after this reproduction is frozen and evaluated should a new study compare
original skills with Observatory's verified retrieved subtask experience. Keep
models, routing definitions, task splits and resource accounting matched in that
extension. It must not retroactively become part of this baseline.

## 19. Coding-agent starting instruction

> Implement this specification additively on branch `work`. Begin with WP1–WP4
> and model-free fixtures. Reuse TTGL's retained native transport, isolated task
> environments, accounting and official evaluator boundaries. Build a genuine
> host-owned one-action loop and RSI-specific optimizer rather than relabelling
> the existing DAG delegation study. Preserve frozen sources, historical results,
> source-bound subscription ownership and local raw retention. Keep inference
> disabled until the finite stage freeze and actual readiness gates pass. Update
> this document and HANDOVER as decisions and evidence accumulate; commit and
> push authorized implementation work. Do not launch the full evolution/test
> campaign automatically, replace uncertain attempts or claim model-quality
> results from synthetic transport.
