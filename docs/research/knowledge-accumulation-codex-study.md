# Knowledge accumulation and transfer through native Codex agents

18 November 2026. Preferred research framing for Observatory/TTGL after the
user's topic clarification. This is a proposed bounded study, not a completed
benchmark or an enabled native campaign.

## Research question and relevance

> Does accumulating verified workflows and subtask experience enable a cheaper
> coding model to solve unseen problems more effectively, moving the measured
> quality–cost frontier of a native Codex system?

The topic is “Investigate how knowledge accumulation and generalization
frameworks accelerate effective innovation outcomes.” The operational mapping is:

| Topic | Operational variable |
| --- | --- |
| Knowledge accumulation | Increasing snapshots of reusable workflows, bounded procedures, failure lessons and model-specific verified outcomes |
| Generalization | Applying that knowledge to new issue/fix lineages and new combinations of procedures, without retrieving the evaluated solution |
| Acceleration | Time and total inference resources to independently verified completion; newly solved tasks per fixed budget |
| Effective outcomes | Functional correctness on unseen coding tasks, including regression preservation, failures and unresolved work |

Coding benchmark repair is a **proxy for effective technical problem-solving**.
It does not establish commercial innovation, originality of an invention or
scientific discovery. If those are required outcomes, add a separately designed
feature-creation/novelty assessment later, without relabelling benchmark repair
scores as direct measurements of innovation.

Routing alone cannot answer the topic. The main treatment is accumulated reusable
knowledge; routing is one mechanism through which that knowledge can change
effective capability and resource allocation. Static lookup and chronological
learning must remain distinguishable.

## Our router and published related work

Latest user decision: build **our own Observatory experience router** and compare
it against Luna, Sol and released routing methods. Keep
[RSI-Router](https://arxiv.org/html/2609.34712v1) as related work only. An official
source release was not located; no RSI implementation or reproduction is part of
the active study. The earlier RSI specification is a superseded design record.
SWE-bench Verified and Terminal-Bench remain useful public benchmarks regardless
of whether RSI code is available.

Our independently implemented router uses typed-subtask similarity, versioned
verified workflows, actual model-specific outcomes and experience recency. Reuse the existing
TTGL Codex transport, model-led MCP delegation tool, isolated workers, source
retention, checkpointing, usage reconciliation and independent benchmark grading.
Native models retain autonomous tool loops within bounded assignments.

The small scientific extension is **recency-aware use of accumulated evidence**.
Do not simultaneously introduce a new planner, model trainer, embedding service,
agent framework or benchmark. Availability, subtask compatibility and actual
executor success already have explicit tool contracts in
[protocol 002](../../experiments/model-led-delegation-001/protocol-002.json).
The current accumulation/comparison proposal is [protocol 004](../../experiments/model-led-delegation-001/protocol-004.json).
Earlier proposals remain historical; none authorizes native execution.

Required released baselines are
[FrugalGPT](https://github.com/stanford-futuredata/FrugalGPT) and
[RouteLLM](https://github.com/lm-sys/RouteLLM). Both repositories report Apache-2.0
licensing. Their APIs/embeddings and answer-level methods need explicit native
Codex adaptations; public source availability is not security or compatibility
qualification. See the [baseline implementation contract](router-baselines-codex.md).

Released [SkillOrchestra code](https://github.com/jiayuww/SkillOrchestra) remains
an optional baseline/integration source if an implementation compatible with the
native model boundary is useful. Its skill-conditioned competence is prior art,
not our invention. Do not replace the chosen coding study with its QA datasets
without naming a new study. Agent Memory Distillation is relevant supporting
literature; selecting another framework is not required to test this hypothesis.

## Bounded benchmark pilot

Primary benchmark: [SWE-bench Verified](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified),
using the [prescribed evaluator](https://www.swebench.com/SWE-bench/guides/evaluation/).
Proposed allocation: **12 construction tasks, 12 development tasks and 32 fresh
held-out tasks**. Actual eligibility, precision and budgets must be established
before reserving IDs; these counts are not already available or authorized to
launch automatically. Prior TTGL studies and observed public solutions are
included in the exposure audit.

Choose construction order from public task metadata before results exist. Preserve
issue/fix/base-lineage exclusions across partitions and snapshot prefixes. Related
procedure families may recur, but near-duplicate fixes must not cross into the
holdout. Describe this as unseen-task transfer; cross-repository generalization
requires a separately registered repository-held-out split.

Use both Luna and Sol on the construction tasks under the same public harness,
retaining failures. Source-bound Luna interprets public traces into typed subtasks
and candidate procedures; host checks establish the permitted support. Public
integration outcomes and retained model-context evidence determine cheaper-model
competence. A teacher procedure is knowledge for Luna, not a fabricated Luna
success. No hidden test patch or held-out task's answer/solution material enters
construction, retrieval or live prompting. Public construction-task work remains
available for extracting reusable procedures, with its original provenance.

Count knowledge by prefix of **construction tasks**, not by cherry-picking the
successful tasks or treating every correlated step as an independent example.
Snapshots follow prefixes **0, 4, 8 and 12**. Publish the number of eligible
procedures, failed attempts and supporting parent tasks in each; a failed task
can contribute supported local lessons, but not invented successful execution.
No eligible knowledge after a prefix is a valid observed state.

Secondary benchmark: a small preregistered Terminal-Bench coding/build/debug
subset only after the primary qualification. Pin 2.0 for paper-version comparison
or use maintained 2.1 with an explicit adaptation label; never mix their scores
or put corresponding task versions across construction and evaluation. Actual
IDs/sizes depend on security, resource and reference-control eligibility.

## Conditions and fairness

At each knowledge snapshot compare three fixed system families:

| System | Behavior |
| --- | --- |
| Luna | Native Luna agent with that snapshot's permitted knowledge |
| Sol | Native Sol agent with the **same** permitted knowledge |
| Routed Codex | Pinned Sol primary plans/integrates; the existing tool delegates bounded work to Luna using that snapshot's evidence |

The empty snapshot supplies no experience to any family. Freeze native tools,
actor image, model/effort, context policy and per-parent budgets across knowledge
levels; all delegation work shares parent caps. Compare the routed system to
both standalone models. Giving knowledge only to the routed arm would confound
collaboration with information access.

The same eligible library and packet limits are available to every family; log
actual packets. The primary may select task-relevant context through the existing
bounded retrieval interface. Protocol differences in planner/controller work
remain explicit and fully costed. Keep primary/worker conversations stable where
possible and measure caching; do not assume that thread identity guarantees hits
or that different models share cached computation.

Full pilot matrix: **3 systems × 4 snapshot sizes × 32 tasks = 384 episodes** at
one repeat, before construction, development, interpretation and qualification.
This is a forecast, not permission to consume that volume. Prepare finite stages
and use development measurements to decide whether the complete pilot is viable.
One repeat and 32 tasks do not establish tight noninferiority. A larger fresh
confirmation requires separate precision/budget registration.

For the small recency extension, freeze a similarity-only routed comparator and
a similarity-plus-recency routed comparator at the final snapshot. They share
the same library, worker packet rules, scope and budgets. This adds at most
32 pilot episodes when the final-snapshot routed condition is one comparator.
Development-select a coverage-matched similarity control to distinguish improved
selection from simply declining more cheap work. Natural experience age must
vary; do not fabricate old timestamps to make this factor look effective.

## Other routers and the frontier claim

Luna-only and Sol-only are necessary endpoints, but beating those two endpoints
does not establish superiority over other routing methods. At the final knowledge
snapshot, add a separately costed comparison suite before claiming a router
frontier improvement:

| Comparator | Required interpretation |
| --- | --- |
| Seeded task-level random/mixture | Tests whether ordinary mixing of the standalone models explains the tradeoff; include the endpoint convex mixture envelope |
| Luna-first public-check cascade | One bounded Sol fallback, with shared total caps; hidden grading never triggers fallback |
| Static typed-subtask mapping | Learn exploration/implementation/verification assignments on development and freeze them; no experience-driven updating |
| FrugalGPT | Required learned confidence/quality cascade adapted to native coding episodes; fit scorers and cascade thresholds on development, and charge every candidate/scorer/executor call |
| RouteLLM | Required released routing method with Luna/Sol development calibration; freeze the variant and disclose any encoder/training changes |
| Additional skill-aware method | A released SkillOrchestra adaptation is optional; RSI is related work only and is excluded from the runnable baseline suite |

Fit/select every baseline on construction/development only. An incompatible or
unrun baseline stays an explicit gap, and limits any claim about other routers.
The required named comparison is our router versus Luna, Sol, FrugalGPT and
RouteLLM. Neither required router is silently replaced by the simpler controls.
Task-level and subtask-level methods remain separately labelled. All systems use
the same model pair, eligible knowledge, public task/check access, evaluator and
total resource caps; charge their training, selection and runtime overhead.
Faithful published harness comparisons can be reported separately, without
attributing a harness advantage to the router. Third-party training/embedding
requirements need their own compatible local, reviewed setup; no new remote
provider or account is implicitly approved by naming a baseline.

Preselect cost-oriented, balanced and quality-oriented operating points using
development data and freeze them before test. Report duplicate or infeasible
points rather than manufacture three distinct policies. Compare quality at
matched cost and cost at matched quality against the union of baseline points,
including mixtures; report paired uncertainty and multiplicity/selection rules.
A non-dominated point can extend the observed frontier without improving every
region. A noisy visual crossing is insufficient evidence of a robust improvement.

The earlier **384 episodes cover the core accumulation matrix only**. Extra
router baselines, tradeoff points and ablations require an explicit expanded
assignment/budget manifest before the first held-out call. Do not quietly present
384 as the cost of the complete comparative study or select extra baselines after
seeing held-out outcomes.

## What could be novel

RSI already studies joint evolution of routing and model-specific skills from
accumulated experience, including a better measured frontier. SkillOrchestra
already studies learned skill-conditioned competence and transfer. Merely using
Luna/Sol, moving their methods into Codex, or plotting a new frontier is an
empirical replication/adaptation, not automatically a new algorithm.

The proposed contribution is a controlled empirical extension: measure unseen-task
capability as verified knowledge grows; distinguish knowledge benefit from model
selection using equal-information standalone controls; test recency against
similarity under naturally aged evidence; and include cache/handoff plus
amortized construction costs. Recency weighting itself is established, so do not
claim its formula is novel. A later controlled environment/version-shift study
could test stale guidance directly, but needs its own registration.

Use the claim “extends the observed quality–cost frontier for this model pair,
harness and benchmark subset” only if results support it. Do not claim a global
state of the art or that changing proprietary models establishes parameter-size
generalization. This is a defensible thesis-scale replication and extension;
stronger publication novelty needs a sharper literature comparison and robust
transfer or mechanism evidence, not a promised positive result.

## Two kinds of accumulation evidence

The first study uses nested **frozen construction snapshots** and measures transfer
as the library grows. All evaluated candidates/snapshots are frozen before test
execution, with no test grades revealed until all predeclared cells finish.
Repeated use of the same held-out tasks is a paired learning-curve evaluation;
the snapshots are not independent samples or opportunities to tune on the test.
Memory construction consumes only the disjoint construction partition.

Actual online accumulation is a later named study: each arm sees a fixed stream,
can publish only its own earlier eligible public experience, and cannot query
future tasks or another arm's history. Independent grading remains sealed from
live memory. This later phase can test whether experience from the user's own
workflow improves subsequent work; do not call the frozen-prefix pilot online
learning or pool the two results.

## Measurements and interpretation

Primary outputs are paired verified completion, total native/model resources and
wall time per assigned task at each snapshot. Plot knowledge quantity against
quality and against resources per correct result; show the resulting quality–cost
frontiers with task-cluster uncertainty. Count parent, worker, annotation,
extraction, retrieval, failure, checking and integration inference. Report the
construction cost and amortization break-even alongside deployment-only costs.

Separate native token/cache counters, provider-estimated credits, pricing
scenarios and subscription cash. Missing costs and grades remain unknown, with
assigned denominators intact. Faster failures do not establish acceleration of
effective outcomes. More tokens in memory do not establish useful knowledge.

Evidence relevant to the topic would be improved unseen-task completion or lower
resources at matched quality as knowledge grows, beyond the same-memory Sol/Luna
controls. A stronger result is a new non-dominated operating point after paying
for routing and amortizing construction. It remains a hypothesis; no current
software fixture, eleven-task historical replay or attractive diagram proves it.
No gain, harmful transfer, stale procedures and a routed system that never
delegates are informative results to retain.

## Implementation continuation

1. Reuse existing native Codex and tool adapters; qualify actual parent/worker
   integration, canonical subscription binding and reviewed isolated actors.
2. Register source exclusions, public checks, immutable construction order,
   artifact/rate/model pins and finite qualification/development budgets.
3. Add the prefix snapshot builder and a campaign matrix over existing study
   records. Test snapshot nesting, no held-out publication, equal information
   access, exact artifact replay and all role accounting with fixtures first.
4. Qualify native execution on finite non-held-out microtasks; then construct and
   audit the library. Do not infer successful subtasks from model summaries alone.
5. Freeze the full test matrix and selection rules before its first model call.
   Run it only after budgets and reference controls pass; independently grade and
   report completed, failed, uncertain and unrun assignments.

Existing source-account/actor/live-integration gates are unresolved. This plan
adds no new model invocation, reservation, dependency installation or automatic
inference schedule, and it does not alter frozen earlier experiments.


## Native continuation checkpoint, 18 November

The prefix builder, equal-context native campaign runner, finite source-bound
admission, exact S3 candidate replay, public construction interpreter and
released-method local-feature adapters are implemented. Native subscription,
isolated coding and required parent/worker handoff qualification have executed.
The first matched benchmark qualification has two official failures; public
extraction qualification admits zero supported records. These are preserved in
[the result index](../../results/model-led-delegation-001/README.md).

The main accumulation comparison remains unrun. Preparation017 is qualifying the
metadata-reserved sources. Stage rules020 freeze compatibility-based allocation,
public-evidence and disjoint baseline-sufficiency gates before main inference.
The provisional counts may shrink with environment eligibility, with explicit
scope/uncertainty reporting. Native baseline training, operating-point selection
and the complete heldout manifest remain required. Earlier unresolved-gate prose
above describes the proposal stage; it does not supersede actual continuation
receipts or authorize repeats. Scheduled research remains paused.
