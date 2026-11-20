# Benchmark, observe, analyze, improve, repeat

15 November 2026 · Proposed study, role clarification · No new benchmark assignments launched

## Research question

Can deterministic trace processing and cheaper model-based organization give a
capable analyst a queryable evidence base from which it can propose changes that
improve an out-of-the-box agent's verified performance, after accounting for
observation, processing, analysis, experimentation and deployment costs?

The analyst may be a large model. The cheaper model's main job is to organize
logs into tasks/subtasks, activities, candidate failure types and searchable
summaries. Parsing, counters and recorded results belong to deterministic code.
Deep diagnosis, prioritization and intervention design belong to the analyst.
These roles and their inference costs are recorded separately.

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
| Process | Deterministic facts plus cheaper-model task/subtask, activity and candidate failure labels | Facts and interpretations remain distinct; every label cites source IDs and records uncertainty |
| Mine / query | Searchable task hierarchy, failure clusters, metrics and progressive source access | Aggregations expose coverage, unknowns and label versions |
| Analyze | A capable, potentially large model investigates and produces a small set of improvement hypotheses | It can query summaries and inspect original evidence; patterns are not causal conclusions |
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

## 4. Trace processing, querying and analyst roles

Use deterministic code for source parsing, identities, counters, timestamps,
recorded tool outcomes and evaluator receipts. Use a pinned cheaper model for
semantic organization. Use a capable analyst model for cross-task investigation
and recommendations; it need not be the same model. A low price does not establish
parameter count or local deployability. Start with the existing activity
vocabulary and source IDs instead of inventing a competing trace format.

### 4.1 Preserve facts and interpretations separately

A registered benchmark task ID is authoritative for the task allocation; native
turn boundaries and model-interpreted subtasks are separate views of that work.
Retain four distinct outcome fields:

- **Operation outcome:** what the tool recorded, including expected nonzero exits.
- **Agent assertion:** what the solving agent claimed it completed or verified.
- **Visible verification:** which checks ran, on which revision, and their results.
- **Independent task outcome:** the benchmark grader's recorded result after sealing.

The cheaper model can mark candidate failure modes and summarize recorded
successes, but cannot invent a pass/fail outcome or replace the grader. Missing,
unavailable, unattempted and inconclusive evidence must remain distinguishable.
Hidden final-evaluation outcomes remain unavailable to tuning and live agents;
permitted development outcomes can be joined after generation for diagnosis.

| Annotation | Example | Guardrail |
| --- | --- | --- |
| Activity | Investigate, plan, implement, test, review, document, operate | Multi-label/unknown where appropriate; categories are interpretations |
| Tool purpose | File discovery, interface lookup, targeted test, broad validation | Actual tool operation and arguments/results remain accessible |
| Candidate failure | Missing prerequisite, incorrect assumption, tool error, integration regression | Cite the decisive evidence; distinguish environment from solution failure |
| Candidate inefficiency | Repeated unchanged reads, broad search, repeated unsuccessful approach | Repetition alone does not establish avoidable work |
| Verification state | Check attempted, check blocked, relevant check passed, acceptance unverified | A command exit and final benchmark success are different facts |
| Opportunity cue | Repeated broad output, missing tool, unresolved check | Processing can flag a cue; the analyst investigates and proposes an intervention |

Tag bounded trace segments with overlap/identity deduplication, then organize the
ordered task trace. Preserve parser omissions and context bounds. Use original
command/results where needed: the current task-history grouping path often sees
operation labels/outcomes rather than full evidence, so those groups alone are
insufficient for confident root-cause diagnosis.

Audit a task-stratified sample independently, including apparent successes,
failures and uncertain cases. Measure agreement, coverage and per-class errors;
audit confidence before treating it as calibrated. Use the same frozen labeler to
compare candidate traces, or reannotate both conditions under a documented version.
Changing the labeler must not manufacture an improvement in reported failure rates.

### 4.2 Make the evidence useful to query

The analyst should start with a compact corpus inventory and progressively query:

| Query layer | Example question | Returned evidence |
| --- | --- | --- |
| Cohort | Which task types have the highest cost or failure rate? | Task counts, denominators, source coverage and aggregate metrics |
| Process | Which investigate/implement/test paths recur, including loops? | Ordered groups with label versions and underlying step IDs |
| Failure | Which tasks share a candidate tool/environment/integration failure? | Cluster members, positive examples, uncertainties and counterexamples |
| Tool use | Which available tools are unused, and where might they help? | Catalog exposure, actual calls/results and relevant task evidence |
| Comparison | What differs between successful and unsuccessful matched attempts? | Matched task/revision/configuration, outcomes and measured buckets |
| Source | What did the agent actually request and observe here? | Bounded exact commands/results, artifact references and truncation status |

Keep source access available even when a summary is wrong or a cluster is empty.
Support pagination and stable identities; expose query result totals and omitted
coverage. Grouping, clustering and apparent rework are interpretations, not
automatic defect verdicts or measured per-tool cost attribution.

Existing MCP/CLI tools already provide activity queries, task-history search,
subtask drilldown and raw evidence reads. The table above is the benchmark
analyst's target query contract, not a claim that every cohort/cluster/comparison
query is currently implemented. Extend only missing interfaces after evaluation.

### 4.3 Let the analyst investigate and challenge the processing

The analyst forms hypotheses, requests source evidence, checks counterexamples,
identifies missing coverage and prioritizes changes. It may flag an incorrect
label or boundary through a versioned correction rather than silently changing
raw facts. Its proposal must cite the evidence and state competing explanations,
expected mechanism, concrete change, trial and rollback. Summaries help navigation;
the analyst must be able to verify decisive claims in the original records.

Keep three claims separate:

1. **Processing quality:** deterministic facts reconcile and cheaper-model labels
   identify activities/candidate problems accurately with source coverage.
2. **Analyst effectiveness:** the queryable representation helps the analyst
   investigate correctly and produce useful interventions.
3. **Execution benefit:** the intervention improves independently checked tasks.

A fluent diagnosis can succeed at neither analyst effectiveness nor execution benefit.

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
| Cheaper processing + capable analyst + measured selection | Main proposed loop; processor and analyst are separately pinned and metered |
| Same capable analyst with raw/basic-index evidence | Tests whether the task/subtask and failure representation helps beyond giving the analyst original logs |
| Optional analyst-size comparison, matched search budget | Measures whether a cheaper analyst can substitute; a large analyst is permitted in the main condition |

First compare the same analyst and source corpus with basic deterministic indexes
versus enriched organization, retaining equivalent access to raw evidence. Count
preprocessing, query and analyst costs. Compare validated findings, proposal
quality, investigation latency, missed evidence and eventual intervention results.
This separates the benefit of the representation from changing analyst capability.

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
| Optimization expense | Deterministic processing/compute, cheaper-model organization, large-model analysis, proposals, implementation inference, all trials/rejections, selection and validation; disclosed separately |
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

Run a finite registered development loop: baseline batch → processed/queryable
traces → analyst investigation → candidate → paired trial → decision. Define
iteration/search caps before launching.
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
| `task_history.py`, `activity_insights.py`, `agent_review.py` | Source-linked task/activity interpretations and explicit analysis jobs | Separate processing from capable analyst investigation; add benchmark evidence, label audit and bounded source/query scope |
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
audited cheap trace organization plus capable analyst investigation, general
evidence-backed interventions, complete
optimization accounting, and measured quality/latency/concurrency transfer.
Neither automatic self-improvement nor processing/analyst adequacy is assumed.

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

## 16 November: operational preparation

The machine-readable [loop protocol](../../tools/usage-monitor/studies/observatory-improvement-loop-protocol-001.json)
now records the proposed stages, evidence contracts, bounded pilot, labeling audit,
proposal fields, decision states, overhead and launch gates. It is a registered
design, **not a frozen task allocation or a completed benchmark**. No new model
attempts, harness installation, task downloads or scheduled work were launched.
The application-data gate now passes the reconciled legacy import described below.

Use Harbor's maintained task environments and official verifiers rather than a
new grading framework. Terminal-Bench's current site identifies 4.1; its exact
task/evaluator revision, licenses, container digests and exposure exclusions remain
to be pinned. The initial proposal is six development tasks at concurrency one,
with one inspected task before expanding. Model/time budgets must be registered
before execution. Existing development, Pro, Aider-derived and held-out reservations
remain untouched. A six-task mechanism pilot cannot establish narrow quality
noninferiority or a broad saving.

Keep native Codex JSONL and tool input/result bytes as primary evidence. Harbor
ATIF supplies the portable trajectory and evaluator linkage where supported; its
usage is an alternative representation, never added to native counters. Retain
sealed actor artifacts and separate grader results. A changed verifier produces a
new linked grade of those artifacts, not a replacement actor attempt. Future
hidden outcomes never enter a live actor or development analyst's inputs.

Luna's current source-bound subscription path can organize task/subtask activity,
candidate failure reasons and verification state. Labels cite event IDs and retain
model, prompt/schema versions, snapshot hash and uncertainty. Audit all pilot
tasks and a success/failure/unknown step sample before using labels in comparisons.
Independent grades remain measurements; labels and diagnoses remain interpretations.
The analyst starts with compact inventories, checks original evidence and
counterexamples, and returns at most three deduplicated proposals. Each proposal
needs a concrete change/preimage, activation check, quality risk, finite trial,
stop rule and rollback. Current Observatory execution remains Luna-only; changing
analyst model is a declared amendment.

Reuse `analyst_experiments.py`'s frozen proposals, runner-written measurements,
reviews and overhead records. Decision, implementation, evaluation and verdict
remain independent. The port of those experiment records and controls into the
new PostgreSQL-backed UI is still a delivery gap; the observational Impact chart
does not substitute for a matched trial. Accepted-for-trial does not mean applied
or beneficial. Keep rejected and inconclusive outcomes. Report the baseline and
candidate on identical task information and resource limits, separately counting
the labeler, analyst, implementation, failed trials and recurring monitoring.

There is also a separate **read-only application benchmark**:

```sh
python3 apps/web/scripts/benchmark_http.py \
  --base-url http://127.0.0.1:3333 --samples 10 --minimum-turns 1605 \
  --output work/security/observatory-performance/baseline-001.json
```

It uses only the standard library, never invokes a model, and refuses to overwrite
a previous result. It records the first observed request separately from sequential
samples, p50/p95 HTTP response times, response bytes, health, pagination identities
and errors. The completed import restored 1,605 native turns and 1,253 explicit
tasks; these are distinct populations. An empty application, HTTP-200 error page,
unhealthy retention store or changing record page cannot pass readiness. The
first observed request is not claimed as a cold start. These measurements do not
measure browser rendering, whole-agent task time, inference latency or causal
speedup. The separate synthetic load fixture remains labeled as synthetic.

Application readiness and the stock-agent pilot must pass before an improvement
comparison is interpreted. New scheduled inference remains disabled. Raw reports
and traces stay private; publish sanitized protocols, source hashes, aggregate
results, limitations and a full proposal-to-verdict lineage in the study record.

### Observed migration baseline

The completed import reconciles all 14,664 event identities and native token
counters, all 54 source-table counts (69,963 archived rows), 1,258 saved analyses
and 1,930 subtasks. All 1,479 referenced transcript files (437,625,382 bytes) and
the exact legacy JSONL export are retained in real local S3. The original SQLite
source remains unchanged. This restores historical measurements and interpretations;
it does not create new model-quality results or modernize old label semantics.

Private reports remain in `work/security/data-migration-20261116/`. The empty
pre-import benchmark fails readiness. The first post-import report preserves
timeouts observed while archival/cache-copy I/O was active. After that work
finished, `http-benchmark-after-migration-002.json` passes health, full-cohort
counts, stable page identities and all HTTP checks, with three sequential samples
per endpoint and zero model calls. Observed task-page p50/p95 is about 5.44/5.45 s;
the native-turn record endpoint is 10.38/16.15 s. These small observational samples
identify application responsiveness as a follow-up; they are not a causal speedup
comparison or agent benchmark. Preserve both failed and successful reports.

## Coding agents are the primary Observatory users

The agent uses MCP to inspect source-linked history, design a reversible harness
change, run a matched comparison and review the operator-measured result. The
dashboard gives people the same experiment record. A useful evidence item links
the task, verified source event, configuration version and change that made the
decision relevant. Preserve full authorized native sessions locally and present
bounded summaries first. Include explicit rationale, rejected options,
verification and uncertainty. A summary is an attributed interpretation with
links to the retained evidence. Hidden model reasoning is outside this record.

The existing analyst MCP provides task lookup, evidence drill-down, proposal
registration and decisions. Its plan tool records a proposal and its review tool
can interpret a measurement. The new local
`python -m ttgl.experiment_mcp` prototype adds an execution surface for one
versioned prompt-harness setting at a time. Its registered comparison uses the
three existing Observatory Python Repair development tasks, both policies on
the same tasks, a separate offline actor for each attempt, independent grading
and immutable local S3 retention. It records the exact settings and diff,
model and source versions, hypothesis, cited evidence IDs, outcomes and review.
Only a candidate that passes the frozen quality/efficiency rule can receive
a keep decision. The current coding agent's settings are outside the isolated
trial. Start without `--execute` for planning and readback, or use
`--execute` on the host to authorize at most six native calls per requested
trial. Result inspection and repeated launch requests do not start additional
calls. This prototype supports registered planning, verification, tool-use and
completion prompts. Arbitrary plugin installation, tool permissions and
user-wide configuration changes are outside this initial test.

The next coding-memory comparison tests use of past decisions during work
rather than historical feedback in the SIM optimizer. Reserve two small
three-step repository changes with real predecessor sessions and fixed Git
checkpoints. A later step must extend the accepted earlier contract or rule out
an alternative that the earlier work already tested. Use the same issue brief,
source tree, Git history, public checks, model and effort in both arms. One
agent starts with the repository. Its counterpart can use Observatory MCP to
read source-backed summaries by repository, task, commit or PR and open the
relevant transcript evidence. Store exact canonical session and turn IDs,
immutable commit and parent, project-scoped PR number if one exists, and the
visible decision/check references. Admit only records from the registered
predecessors, before the target cutoff. Both arms can discover requirements
through normal repository work. Earlier conversations should explain why an
approach was chosen, without containing the target solution or hidden grader.

Freeze the source sessions and identical base state before the paired
continuations. Use independent tests for verified completion and regressions,
report clock time jointly with success and retain the actual retrieval calls.
Four paired checkpoints are an initial mechanism pilot. Use an additional
summary-only arm later if we need to distinguish summary benefit from trace
access. Model comparisons and cost reduction are a separate follow-up. The
earlier repository-memory development wave gives a related comparison with
two standalone tasks and equal quality. The larger historical longitudinal
run has 20 retained generation receipts of 216 assignments and no official
grades in the retained root. Keep those attempts as historical evidence. They
do not score the new decision-history design.
