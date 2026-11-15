# Benchmark, observe, analyze, improve, repeat

15 November 2026 · Proposed study · No new benchmark assignments launched

## Research question

Can a low-cost model analyze the execution traces of an out-of-the-box coding
agent, propose concrete improvements, and improve verified task performance after
accounting for the observation, analysis, experimentation and deployment costs?

The intervention is an **evidence-backed optimization loop around an existing
agent**. Agent weights remain fixed initially. Prompts, tool interfaces, context
handling, verification policy, resource allocation and later multi-agent
coordination are candidate intervention surfaces. The baseline is the unmodified
agent; a modified condition is explicitly named stock-agent-plus-intervention.

The 100-agent objective becomes a scaling outcome: can improved execution increase
verified throughput at a given concurrency, or sustain more concurrent work within
the same quality, latency and resource limits? A hundred independent benchmark
jobs and a hundred agents collaborating on one artifact remain separate tracks.

This is a design proposal, not a frozen allocation or permission to restart old
studies, access reserved validation, install dependencies or launch a large run.
Existing failed trials and incomplete studies remain unchanged; schedules remain
paused.

## 1. Experimental loop

| Stage | Concrete output | Evidence boundary |
| --- | --- | --- |
| Run | An existing agent attempts a fixed task batch | Pinned agent/model/configuration, isolated task state and exact task revision |
| Monitor | Immutable native operations, usage, timing, artifacts and coverage | Capture/model counters remain distinct; missing evidence stays unknown |
| Tag | Versioned activities, task types and candidate failure/opportunity labels | Every interpretation cites source IDs and records uncertainty |
| Analyze | A small set of evidence-backed improvement hypotheses | Patterns and apparent waste are hypotheses, not causal conclusions |
| Propose | Reviewable patch/configuration change with predicted effect and rollback | One primary mechanism per initial candidate |
| Trial | Fresh registered baseline/candidate attempts with independent grading | Same task information and controlled resource regimes; no hidden feedback to actors |
| Decide | Keep, reject or inconclusive against a predeclared rule | Result records are immutable; interpretation is separate |
| Repeat | A new version tested on development data | Final held-out data remain untouched until the policy is frozen |

Each iteration should explain what was observed, why the proposed change could
help, whether it actually activated, and what the measured comparison showed.
Keep negative results and abandoned candidates rather than replace the history
with the eventual winner.

## 2. Establish an actual out-of-the-box baseline

Choose one existing native coding agent first, with one pinned solver model and
reasoning setting. Record its default prompts/tools, CLI/runtime versions,
authentication route, permissions, context/compaction settings, retry behavior,
task limits and environment. Use an isolated profile/home so personal memories,
TTGL-specific repository guidance and earlier candidate instructions do not enter
the task by accident. Do not change the user's normal configuration.

The baseline can be observed passively, but must not receive optimization advice,
extra memory, custom specialist roles or tools added by the experiment. Validate
that capture does not change model-facing requests. Measure collection overhead
separately; if monitoring itself changes inputs, it is an intervention and needs
a distinct control. Preserve task-access and evaluator boundaries.

Pin the available tool catalog as well as actual invocations. This distinguishes
an unused available tool, a missing tool and a tool that exists but cannot execute
in the task environment. Preserve underlying native operation names; wrappers and
child operations must not be counted twice.

## 3. Task choice and evidence separation

Use an existing benchmark and its maintained evaluator rather than create a new
grading framework. A terminal benchmark is a good primary candidate for varied
tool use; a fresh repository-repair panel can test transfer to ordinary coding.
Select task versions and families from metadata before inspecting outcomes.

The [Terminal-Bench site](https://www.tbench.ai/) currently identifies 4.1. Pin the
actual task/evaluator revision rather than a floating latest label. Its
[benchmark-maintenance study](https://arxiv.org/abs/2611.08417) shows that verifier
repairs and time budgets can materially change conclusions. Empty/reference
controls, environment readiness and task-contract review are required evidence.
No existing prepared image is assumed to remain usable after a host restart.

SWE-bench Verified is useful historical/calibration evidence, but is heavily
observed in TTGL already. [OpenAI's audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
also documents contamination and specification concerns. Do not treat another
score on its reused cases as fresh generalization. Before choosing a new coding
panel, inspect all earlier reservations, task families and attempts, including
the existing Pro and Aider-derived held-out sets. This proposal selects none.

Maintain three distinct evidence pools:

- **Development:** traces and permitted development outcomes used for diagnosis,
  candidate construction and iterative search. Reuse is disclosed as adaptation.
- **Selection:** outcome-independent tasks used under a bounded, predeclared
  candidate-selection rule. Repeated selection still spends information and
  cannot become an unlimited tuning set.
- **Final evaluation:** a reserved fresh panel, accessed only after freezing the
  complete candidate, labeler/proposer policy and evaluation plan.

Only visible task feedback reaches a live solving agent. Independent grading
happens after the artifact is sealed. The optimizer may use permitted development
grades between runs; final hidden outcomes cannot guide live decisions or tuning.
Size the final panel from development variability, desired effect and acceptable
regression margin; a convenient small sample cannot prove narrow noninferiority.

## 4. Small-model tagging and process analysis

Use a pinned cheaper analyst model; a low price does not establish its parameter
count or local deployability. Start with the existing activity vocabulary and
source IDs instead of inventing a competing trace format.

| Annotation | Example | Guardrail |
| --- | --- | --- |
| Activity | Investigate, plan, implement, test, review, document, operate | Multi-label/unknown where appropriate; categories are interpretations |
| Tool purpose | File discovery, interface lookup, targeted test, broad validation | Actual tool operation and arguments/results remain accessible |
| Candidate failure | Missing prerequisite, incorrect assumption, tool error, integration regression | Cite the decisive evidence; distinguish environment from solution failure |
| Candidate inefficiency | Repeated unchanged reads, broad search, repeated unsuccessful approach | Repetition alone does not establish avoidable work |
| Verification state | Check attempted, check blocked, relevant check passed, acceptance unverified | A command exit and final benchmark success are different facts |
| Opportunity | Batch independent reads, improve result pagination, expose a missing capability | Must identify a concrete intervention and falsifiable expected effect |

Tag bounded trace segments with overlap/identity deduplication, then analyze the
ordered task trace. Preserve parser omissions and context bounds. Use original
command/results where needed: the current task-history grouping path often sees
operation labels/outcomes rather than full evidence, so those groups alone are
insufficient for confident root-cause diagnosis.

Audit a task-stratified sample independently, including apparent successes,
failures and uncertain cases. Measure agreement, coverage and per-class errors;
audit confidence before treating it as calibrated. Use the same frozen labeler to
compare candidate traces, or reannotate both conditions under a documented version.
Changing the labeler must not manufacture an improvement in reported failure rates.

Keep three claims separate:

1. **Label quality:** the model identifies activities/problems correctly.
2. **Proposal quality:** its diagnosis produces a useful intervention.
3. **Execution benefit:** the intervention improves independently checked tasks.

A fluent diagnosis can succeed at neither of the latter two.

## 5. What can be changed

| Surface | Candidate changes | Essential comparison |
| --- | --- | --- |
| Prompts / procedures | Clearer completion evidence, less redundant instruction, targeted planning | Same agent/model and task information; verify transfer beyond diagnosed cases |
| Tool presentation | Bounded output, pagination, exact raw retrieval, discoverable schemas | Confirm actual model-visible change and preserve necessary diagnostics |
| Tool availability | Add a useful missing integration or reduce redundant descriptions | Exposure/use and downstream outcome, not frequency alone |
| Verification | Better check selection, available test feedback, integration checks | Independent acceptance; do not save cost by silently dropping correctness |
| Context / knowledge | Reuse validated findings, revision-aware retrieval, handoff records | Equal-information controls; include extraction/retrieval/cache effects |
| Scheduling | Batch independent operations, cap resource-heavy tests, reduce queue contention | Fixed host/provider budget and end-to-end task outcomes |
| Multi-agent organization | Delegation, ownership, communication, review and integration policy | Same total agent/inference budget; count coordinators and reviewers |

Rare tools can be essential on rare tasks. High tool frequency can indicate a
useful capability or a poor interface. A tool is not unnecessary merely because
it did not appear in one small batch. Proposed additions need a concrete eligible
use case and a controlled comparison. Availability, selection and successful use
are separate measurements.

Initially keep solver weights/model choice fixed so the effect comes from the
execution system. Model routing, learned policies or training can become later
separately attributed interventions.

Each candidate record needs: source snapshot, evidence IDs, failure/opportunity,
patch and preimage hashes, changed surface, predicted mechanism, expected
benefit, quality risks, affected tasks, activation check, trial budget, stop rule
and rollback. Apply only within a prepared experimental checkout/configuration;
freeze each tested version and preserve the prior one. A documented permitted
scope can support automatic reversible application without another approval for
every patch; changes outside that scope need separate authorization.

## 6. Comparisons that identify the optimizer's contribution

The main outcome comparison is stock agent versus stock agent plus the selected
optimization. Additional controls answer why it improved:

| Condition | Purpose |
| --- | --- |
| Stock + passive collection | Baseline quality/cost/time on the same native agent |
| Shadow analysis, no application | Label/diagnosis audit and analysis expense; reuse baseline logs where possible rather than rerun solely for labels |
| Simple deterministic suggestions | Tests whether familiar rules or maintained tool options achieve the same benefit without a model analyst |
| Small-model proposals + measured selection | Tests the proposed optimization loop |
| Optional stronger analyst, matched search budget | Estimates whether cheap analysis retains useful proposal quality; not required for the first study |

Test single mechanisms before claiming a cumulative bundle effect. For a kept
bundle, compare against the original stock baseline and the previous frozen
version. Include component-removal ablations when needed to identify contribution.
Equalize candidate-search budget when comparing optimizers: a better outcome after
many more experiments may simply reflect more search expenditure.

Alternate or randomize paired execution order and record host/provider load.
Use predeclared repeated fresh assignments when estimating variance; distinguish
those from automatic retries or replacements. Never repeat an ambiguous or
already-started invocation. Track parent/child sessions and auxiliary inference.

## 7. Performance and economics

| Outcome | Definition |
| --- | --- |
| Task quality | Independent benchmark acceptance, paired successes lost/gained, partial scores separately |
| Model cost | Rate-weighted input/cache/output for every solver, expert, analyst, memory and verification call; unknown totals remain unknown |
| Deployment cost | Per assigned task and per verified resolution, including unsuccessful attempts and recurring runtime analysis |
| Optimization expense | Trace analysis, proposals, implementation inference, all trials/rejections, selection and validation; disclosed separately |
| Time | End-to-end task latency, p50/p95, makespan, queue waits and time to fixed verified quality |
| Throughput | Independently verified resolutions per hour and per resource/cost budget |
| Parallel capacity | Sustainable active work under declared quality/latency limits, not just configured agents or created sessions |
| Detection | Precision/recall, false alarms, missed failures and time to detection against separately established labels |
| Tool utility | Availability → invocation → successful use → supported checked outcome, with intervention comparisons |
| Observability | Coverage, exact identities, reconciliation residuals and collector/analyst overhead |

Cached input is a subset; reasoning is within output where the meter defines it
that way. Native runtime differs from lifecycle duration, background lifetime and
agent-blocking time. Tool output size and estimated token/cost allocations do not
become measured per-tool model charges. Fewer tokens need not mean lower cost.
Published-rate scenarios, account estimates, actual cash and full compute expense
remain separate.

Retrospective diagnosis and online failure detection are different experiments.
For an online detector, freeze a policy over trace prefixes and score whether it
flags the problem before completion; the future grader must not enter its input.
Measure false-positive interventions and their cost as well as rescued failures.

Keep Pareto results when quality/cost/time trade off. A quality-losing candidate
is not an unqualified improvement. Predeclare the primary metric, minimum useful
gain and acceptable quality loss before scoring; if the requirement is no observed
loss, report that point criterion alongside sample size and uncertainty.

For repeated deployment, report both gross per-task gains and net optimization
economics. A useful accounting identity is:

`net gain after N tasks = baseline deployment cost for N tasks
                         − candidate deployment cost for N tasks
                         − optimization/research expense allocated to those tasks`

Include recurring reviews in deployment or explicitly allocated optimization
expense, never omit them or count them twice. Break-even requires a positive
measured cost difference and compatible workload; it is not established by one
favorable example. Cost per resolution is undefined with zero resolutions.

## 8. Iteration and scaling

Run a finite registered development loop: baseline batch → bounded diagnosis →
candidate → paired trial → decision. Define iteration/search caps before launching.
Keep an unchanged contemporaneous control to detect environmental/model drift.
Do not continue testing final held-out cases until a preferred result appears.

First optimize independent single-agent jobs. Then compare baseline and selected
candidate across an initial concurrency ladder such as 1, 4, 8 and 16, subject to
actual resource readiness. This is an illustrative design, not a run allocation.
Advance toward 32/64/100 only with predeclared criteria and a new resource plan.

Run two resource regimes: fixed hardware/provider capacity to measure contention,
and provisioned resources to distinguish bottlenecks from coordination effects.
Record active model requests, tool execution, blocked/idle states, provider
throttling, CPU/RAM, test contention and ingestion lag. More accepted jobs/hour
with retained quality is a scaling result; more simultaneous process IDs is not.
Shared-artifact swarms later add ownership and integration to this design, under
the [separate scaling review](agent-swarms-literature-review.md).

## 9. Reuse and relationship to existing research

| Existing TTGL component | Reuse | Remaining work before this study can run |
| --- | --- | --- |
| Native reader, capture and metering | Source evidence, identities, cumulative-counter reconciliation | Validate capability/coverage for the selected agent and task runner |
| `task_history.py`, `activity_insights.py`, `agent_review.py` | Source-linked task/activity interpretations and explicit analysis jobs | Benchmark trace adapter, full-evidence diagnosis, label audit and bounded analyst scope |
| `analyst_experiments.py` | Frozen proposals, runner-written measurements, keep/reject reviews, accounting | General benchmark trial/execution interface and complete lineage |
| Optimization/Impact/Outcomes views | Inspect trends, source evidence and candidate records | Connect to controlled benchmark results; observational trends are not causal estimates |
| Existing trial runners | Immutable attempts and bounded registered comparisons | Generalize only missing interfaces; do not reuse completed trials as new assignments |

The generic optimization loop has substantial prior art. [GEPA](https://arxiv.org/abs/2507.19457v2)
uses execution traces and reflection to search prompt updates; [ACE](https://arxiv.org/abs/2510.04618v3)
evolves structured contexts; [ADAS](https://arxiv.org/abs/2408.08435) and
[AFlow](https://arxiv.org/abs/2410.10762) search agent/system workflows. Evaluate
these existing methods before implementing a new search algorithm. They are
research precedents, not verified ready integrations or security-cleared installs.

Frame TTGL as replication/controlled extension: native out-of-the-box agents,
audited cheap trace analysis, general evidence-backed interventions, complete
optimization accounting, and measured quality/latency/concurrency transfer.
Neither automatic self-improvement nor cheap-model adequacy is assumed.

Earlier TTGL results already contain small parts of the loop:

- [Progress replay002](../../tools/usage-monitor/studies/progress-replay-results-002.md)
  preserved a failed trial, revised the protocol and found a bounded token gain.
- [Live harness001](../../tools/usage-monitor/studies/live-harness-results-001.md)
  tested actual code edits/checks on two generated tasks, with a limited token
  improvement and no observed speedup.
- [Verification-selection validation](../../tools/usage-monitor/studies/verification-selection-validation-results-001.json)
  rejected a policy that looked favorable on development but cost more on validation.

These studies stay historical; do not repeat them or infer broad benchmark,
cash, net or scaling benefits from them.

## 10. Concrete next deliverable

Prepare a reviewable registration that selects the agent/version, benchmark
revision, fresh task allocation and splits, label audit, candidate surfaces,
resource regime, iteration/search budget, acceptance rule, independent grader,
metering and failure/stop policy. Inventory active queues and old reservations
first. Validate the actual environment and dependency security before execution.

The first new result should answer: **did one proposal derived from audited real
traces improve fresh matched task outcomes, after counting the cost of finding
and applying it?** Only then expand the iterative search and concurrency panel.
