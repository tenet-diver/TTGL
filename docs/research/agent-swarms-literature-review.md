# Scaling to 100 concurrent agents: knowledge, communication and monitoring

15 November 2026 · Focused literature review and proposed research direction

**Research objective:** make 100 concurrently running agents produce more verified
useful work through effective knowledge sharing, communication and monitoring.
This is a research target, not a demonstrated TTGL capability. The immediate
application is software engineering; research/search and optimization provide
important comparisons with different coordination requirements.

## 1. Main finding and scope

Hundreds of cooperating coding agents are feasible in published research and
engineering demonstrations. The evidence does not establish that one organization
of 100 is generally preferable to smaller teams, independent attempts or a strong
single agent. The useful design depends on what must be shared and integrated.

Three workloads need separate answers:

| Workload | What the agents contribute | What success means |
| --- | --- | --- |
| Independent jobs | Different issues, documents or customer requests | Aggregate verified throughput at acceptable cost and latency |
| Competing solutions | Different attempts at one kernel, proof or optimization task | Best independently scored candidate; implementations need not be merged |
| Shared artifact | Interdependent parts of one repository or investigation | One coherent, integrated, verified deliverable |

This distinction is central to interpreting the large-team results below.
Candidate selection is easier when an executable scorer exists; it does not solve
integration. A fleet with many simultaneous jobs is not evidence that the same
number can collaborate effectively on one job.

The review uses targeted searches, backward references and primary sources,
covering 20 papers/first-party reports from 2024–2026. It is a focused review,
not an exhaustive systematic review or meta-analysis. Full methods/limitations
were inspected for the main scaling, coding and shared-context sources; some
supporting observability papers were screened at abstract level. Reading depth
and versions are recorded in the [source register](agent-swarms-sources.json).
Recent arXiv results remain author-reported preprints unless separately established.
Vendor case studies are useful implementation evidence, not randomized comparisons.

## 2. The most relevant empirical evidence

| Work | Result or mechanism | Important limit for the 100-agent goal |
| --- | --- | --- |
| [Agensh, Zhan et al., September 2026](https://arxiv.org/html/2609.26781v1) | Decentralized workers use shared work state, messaging and compact context. Five ProgramBench tasks improve from 19.31% mean test pass at one agent to 28.78% at 128. Pandoc reaches 55.06% at 1,024 versus 33.89% at one. | Six-hour wall budget, not equal total inference cost. Partial test scores, not complete-task success. Activation is staggered; baseline continuation prompts differ. Broad repeated-run uncertainty and a cost frontier are not established. |
| [Parallel Agent Teams, Wang et al., November 2026](https://arxiv.org/html/2611.09798v1) | With a 100-agent budget, teams of ten beat independent agents on 10/12 tasks and one 100-agent team on all four tested large-team tasks. Flat teams exchange experiments and scores. | Twelve-hour, verifier-scored optimization; the best candidate wins. Large-team repetitions are limited and forum visibility changes at 64/100. Not a comparison of ten teams integrating different modules. |
| [CAID, Geng and Neubig, March/July 2026](https://arxiv.org/html/2603.21489v2) | Dependency-aware delegation, asynchronous workers, isolated Git worktrees and tested branch/merge improve repository-development and paper-reproduction scores. | Main comparisons use two engineers, not 100. More workers are not uniformly better; stronger review trades runtime for quality. Evidence for integration discipline, not unlimited central management. |
| [Native dynamic concurrency, Li et al., October 2026](https://arxiv.org/html/2610.10263v1) | Matched concurrency on/off across Codex, Claude Code and Kimi Code: 354 tasks, 2,124 runs. Complementary work, alternatives and validation can help long tasks; tokens increase 1.41–3.31×. | Bounded tasks often gain little or regress. Created-agent count differs from actual overlap. Thirteen concurrency failure subcategories show scheduling and integration remain consequential. |
| [ParallACT, Mediratta et al., October 2026](https://arxiv.org/abs/2611.00314) | Independently requested shared-code changes collide. Peer awareness alone helps little; a communication channel recovers only part of the loss at extra token cost. | Even two agents can fail. Complementary and contradictory requirements differ; genuinely incompatible goals require a decision about intent, not just a better message bus. |
| [DeLM, Mao and Mirhoseini, June 2026](https://arxiv.org/html/2606.10662v1) | A shared task queue and compact, evidence-checked entries let workers reuse findings and failed hypotheses without routing everything through one manager. Detailed evidence can be unfolded. | Favorable SWE-bench/long-context results do not demonstrate 100-agent execution. Checking a summary against evidence is not proof that the evidence establishes general correctness. Current repository and original paper differ. |
| [SEPM, Liu et al., October 2026](https://arxiv.org/html/2610.14515v1) | Shared task graphs connect procedure memory to execution state. Detects goal/plan/state divergence and validates procedural revisions. Positive comparisons on ALFWorld, WebArena and OfficeBench. | Coordination, memory and model work must be separated by ablations. These benchmark improvements are not a 100-agent coding result or proof that arbitrary graph memory helps. |
| [Towards a Science of Scaling Agent Systems, Kim et al., December 2025](https://arxiv.org/html/2512.08296v1) | Across 180 configurations, architecture interacts strongly with task structure. Parallelizable work can improve; sequential planning can deteriorate. | Studied architectures and datasets bound the conclusions. Reported error amplification and architecture-selection accuracy are not universal constants or guarantees at 100 agents. |

These papers favor different organizations because they study different workloads,
models and resource regimes. They do not support a universal rule that centralized
or decentralized agents always win.

## 3. Engineering experience and supporting research

| Source | Useful finding | What it does not establish |
| --- | --- | --- |
| [Cursor: Scaling long-running autonomous coding, January 2026](https://cursor.com/blog/scaling-agents) | A shared coordination file and locks made 20 agents behave like two or three. Planner/worker ownership improved their large-project execution. | A controlled causal effect or a general rule that decentralized coordination fails. More commits/lines are not verified user outcomes. |
| [Cursor: Towards self-driving codebases, February 2026](https://cursor.com/blog/self-driving-codebases) | A later hierarchical design uses continuous handoffs; a single integrator becomes a bottleneck. Full traces help diagnose recurring coordination problems. | Release correctness from commit throughput. Their intentionally imperfect working branch is not a suitable final quality gate. |
| [Anthropic: parallel compiler team, February 2026](https://www.anthropic.com/research/building-c-compiler) | Sixteen agents make substantial progress using isolated checkouts, task claims and tests. A shared kernel-build blocker makes workers duplicate fixes; a decomposable differential harness restores useful parallel work. | A 100-agent controlled scaling curve. The reported roughly $20,000 API spend is one historical project, not a budget quote. |
| [Anthropic: multi-agent research system, June 2025](https://www.anthropic.com/research/multi-agent-research-system) | Broad independent searches benefit from delegated context and bounded handoffs. Internal research evaluation reports a 90.2% improvement over its single-agent comparator. | A coding result or equal-compute gain. Reported 15× token use is versus chat; single agents use about 4× chat, not a 15× multi-versus-single comparison. |
| [MAST, Cemri et al., 2025, v3](https://arxiv.org/abs/2503.13657v3) | More than 1,600 annotated traces; 14 failure modes across system design, inter-agent misalignment and verification. Useful review categories. | Failure detection or repair simply from installing a taxonomy. Automated labels still need evidence, confidence and validation. |
| [AgentPrune, Zhang et al., 2024/2025](https://arxiv.org/abs/2410.02506) | Redundant message edges can be removed while retaining competitive benchmark performance and reducing token overhead. | One optimal sparse topology for dynamic coding. Learned/static communication pruning needs separate transfer checks. |
| [MacNet, Qian et al., ICLR 2025](https://arxiv.org/html/2406.07155v2) | Large DAG-based collaboration propagates refined artifacts instead of whole dialogues; topology changes outcomes. | A thousand logical actor/critic roles are not automatically a thousand simultaneously productive coding workers. Topological dependency order matters. |
| [Agent Forest, Li et al., 2024](https://arxiv.org/abs/2402.05120) | Independent sampling and voting can improve results without elaborate inter-agent communication. | Shared-repository coordination. This is an essential compute-matched baseline, not evidence that every additional sample helps economically. |
| [AgentSight, Zheng et al., 2025](https://arxiv.org/abs/2508.02736) | Correlates model interactions with process/system effects; demonstrates loop and coordination-bottleneck diagnosis. | Correctness inferred from OS activity. Instrumentation coverage and its reported overhead are deployment-specific. |
| [AgentLoupe, Bao et al., October 2026](https://arxiv.org/abs/2610.23233v2) | Tracks causal identity through delayed execution and resources across process lineages. | Perfect semantic causality or a measured team-productivity gain. Relevant when work is handed off through files/services. |
| [Signals, Chen et al., April 2026](https://arxiv.org/abs/2604.00356) | Cheap trajectory signals improve selection of informative traces for review in a controlled annotation study. | An automatic failure verdict or proof that the flagged behavior wasted work. Triage should not become an unvalidated blocking policy. |
| [Anthropic: measuring agent oversight, 2026](https://www.anthropic.com/institute/measuring-pace-of-ai-development) | Reports a large internal fleet and distinguishes monitoring coverage, review latency and escalation rate. | One collaborating swarm, independent efficacy validation, or correctness from high monitoring coverage. Fleet-wide oversight and shared-artifact scaling are separate questions. |

## 4. What the evidence suggests trying

The following are **engineering hypotheses synthesized from the sources**, not
results already demonstrated for TTGL at 100 agents.

### 4.1 Allocate work using explicit dependencies and ownership

Make a work item concrete: goal, acceptance checks, relevant revision, permitted
scope, prerequisites, owner, deadline/budget and expected output. Workers should
be able to say that the contract is incomplete or conflicts with another request.
Keep prerequisite state outside the model's conversational memory.

For a shared repository, try decentralized claims over ready work and a modular
planner/worker hierarchy as competing baselines. Use implementation-enforced
atomic claims and expiring leases; do not ask an LLM to maintain a global lock
correctly for an entire task. A lease expiry alone must not replay an ambiguous
external action or an already-started model call. Reconcile recorded intent,
receipts and actual state before continuation.

A hard problem is not automatically divisible into 100 useful problems. Preserve
capacity for independent investigation, testing and review, but avoid inventing
100 roles merely to occupy 100 slots. Adapt the active worker count to ready work
and downstream integration capacity.

### 4.2 Share evidence and constraints, with exact detail available

Keep four stores conceptually separate, even if an existing database serves them:

| Store | Example | Required property |
| --- | --- | --- |
| Coordination state | Owner, dependency, blocked reason, ready-to-merge status | Atomic/versioned state transitions |
| Artifacts | Patch, test output, interface definition, experimental candidate | Exact identity, revision and access control |
| Reusable findings | Failed approach, confirmed behavior, applicability constraint | Evidence, scope, provenance and invalidation |
| Long-term procedures/preferences | Validated workflow; durable user constraints | Versioned promotion and retention; distinct from model weights |

A useful knowledge entry should identify its author, claim type, source revision,
supporting artifacts/checks, applicable task/environment, remaining uncertainty
and what supersedes it. A failed approach is especially useful when it prevents
the same expensive investigation. It must retain its conditions: new code,
different inputs or new evidence can justify revisiting it.

Make compact notices searchable and allow exact source retrieval. Compare bounded
global context, topic-filtered updates and pull-based retrieval rather than assume
one is best. Sharing every observation with everyone can cause repeated input
cost and correlated errors; excessively short summaries or missed retrieval can
lose essential facts. Model-checked publication and independently executed
verification provide different levels of evidence. Neither is universally true.

A knowledge graph is a storage/representation choice. First establish that workers
actually retrieve relevant knowledge, act on it and improve a verified outcome
over an equal-information notebook or file-search control. Additional extraction,
embedding, ranking and consolidation work belongs in total cost.

### 4.3 Separate notification, durable state and artifact delivery

Messages announce changes or ask precise questions. The task database records
authoritative status. Artifacts carry actual work. This avoids treating a chat
statement such as “done” as a committed, tested implementation.

Use small typed messages: interface change, blocking dependency, conflicting claim,
candidate ready, check failed, counterexample, result superseded. Include task,
revision, evidence reference and expected action. Send urgent interface conflicts
to affected owners. Batch routine updates and make delivery resumable with IDs
and acknowledgements. Event delivery can be retried only with suitable identity
and reconciliation; delivery retries must not duplicate consequential execution.

Decentralized coordination need not mean all-to-all conversation. Conversely,
adding one central summarizer does not eliminate information volume; it can move
the queue to that agent. Keep normal peer progress local to the relevant task or
module and escalate cross-module decisions explicitly.

### 4.4 Give integration and verification their own capacity plan

For coding, use isolated workspaces and explicit, versioned candidate changes.
Check the candidate in isolation and again against the integration revision;
detect semantic/interface conflicts, not only textual merge conflicts. A local
check receipt should identify the exact code it covers.

Do not make one LLM review every detail of every worker output. Compare local
self-checks, independent review of high-impact changes and automated integration
checks. Preserve one authoritative definition of final acceptance even when
implementation/review is distributed. A fast experimental branch can exist, but
only an independently checked integrated artifact counts as delivered success.

Scorer-guided search needs additional protection against optimizing the public
score while breaking unseen behavior. Use separate acceptance checks and retain
failed candidates; no hidden evaluator outcomes should drive live workers.

### 4.5 Preserve diversity while sharing useful discoveries

In optimization/search, early universal sharing can make everyone copy the same
candidate. Test independent small teams with shared findings inside each team
and controlled exchange between teams. Compare this with no exchange and full
exchange; do not infer that team size ten is a universal optimum.

For one repository, module teams must integrate their outputs; for competing
solutions, teams submit alternatives and a verifier selects. These are different
experiments. Heterogeneous specialist models are another independent factor:
measure which model helps which work and include handoff/context costs. A larger
team of weaker agents need not replace a capable worker on the critical path.

## 5. What commonly fails, and the observable symptom

| Failure mechanism | Symptom worth monitoring | Candidate response to test |
| --- | --- | --- |
| Global lock / serial coordinator | Workers ready but blocked; rising assignment/merge wait | Atomic short claims; sharded ownership; asynchronous dispatch |
| Undecomposed common blocker | Many agents repeat the same failing experiment or patch | Identify shared dependency; partition the diagnostic space; assign one owner |
| Context flooding | High coordination input, stale notices and little new checked progress | Topic scoping, bounded notices, exact-source retrieval |
| Unsupported consensus | Many copies of one claim, no independent check or counterexample search | Preserve competing hypotheses; require evidence and revision-aware validation |
| Conflicting specifications | Individually reasonable patches cannot satisfy combined intent | Resolve the contract or escalate intent before more implementation |
| Late integration | Local tests green, integration queue or regressions growing | Shorter integration cycles; interface checks; enough verifier capacity |
| Premature completion | Agent says done before required acceptance is checked | Separate agent completion, artifact submission and independent task outcome |
| Rigid synchronous rounds | Many idle agents waiting for the slowest member | Dependency-aware asynchronous joins and bounded blocked-task handling |
| Wrong/stale procedural memory | Reused workflow violates the current code or environment | Applicability checks; versioning; supersession; reset-memory comparison |
| Excessive monitoring inference | Review workload/cost grows faster than useful throughput | Cheap triage plus sampled evidence-backed analysis; meter analyst overhead |

Symptoms are not automatic verdicts. Repeated commands can be useful verification,
nonzero exits can be expected controls, and a long-lived process can be a service.
Diagnosis needs source evidence and task context.

## 6. Monitor a swarm as a dependency and evidence graph

Extend the existing TTGL evidence model rather than replace it with 100 separate
dashboards. Proposed identity chain:

`project → goal → task → attempt → agent/session → model/tool operation`

Add links for `depends_on`, `delegated_to`, `read_claim`, `produced_artifact`,
`checked_revision`, `supersedes`, and `integrated_into`. These are proposed
extensions, not a claim that all are implemented. Preserve native IDs and exact
source records; inferred relationships retain their evidence and confidence.

| Question | Measurement |
| --- | --- |
| Are 100 agents really concurrent? | Configured cap, created sessions, live sessions, concurrent model requests, active tools and blocked/idle states separately |
| Does the system produce more useful work? | Independently accepted outcomes/hour, verified integrated checkpoints and time to a fixed quality threshold |
| Where is the bottleneck? | Queue wait for models/tools/work/merges/checks, critical-path tasks, stale leases, resource saturation and provider throttling |
| Does knowledge help? | Publication → actual retrieval/exposure → cited use → checked artifact; missed retrievals, stale/conflicting claims and treatment/control outcomes |
| Is communication efficient? | Fanout, coordination tokens, read/replay volume, time to dependency resolution and integration latency |
| Does quality survive scale? | Final acceptance, regressions, false completion, reopened tasks and local-pass/integration-fail gaps |
| Can the monitor be trusted? | Capture coverage, missing IDs, delivery lag, reconciliation gaps, alert precision and review latency |
| What does the swarm cost? | All worker/planner/expert/memory/review/retry inference, failed attempts, local resources and separately recorded research overhead |

Start with deterministic detectors for queue growth, repeated failure signatures,
stale dependencies and missing checks; use them to select traces for inspection.
Have an analyst review selected cases with original evidence and confidence.
Retain a random review sample to estimate what the detectors miss. Measure
false positives and the cost of review before enabling automatic intervention.

For a shared finding, record the producing operation, artifact/revision and
consumer reads. Process parentage alone cannot show how another independently
started worker learned a claim through a shared file or service. Avoid claiming
causal knowledge benefit from this trace chain alone; intervention comparisons
are still needed.

## 7. Simple capacity calculations

These are illustrative engineering calculations, **not measured TTGL results**.

- A 100-member all-to-all topology has 4,950 possible undirected pairs or
  9,900 directed sender/recipient relationships. Actual message volume depends
  on routing and activity; a shared board can still incur repeated per-reader
  input and context replay.
- For fixed work with a 10% serial fraction, the idealized Amdahl speedup at
  100 workers is `1 / (0.10 + 0.90/100) ≈ 9.17`, before communication costs.
  This is not a ceiling on discovery or improved solution quality, which can
  change the work itself.
- If each of 100 workers finishes one candidate every ten minutes, the system
  receives ten candidates/minute. An integration path handling one/minute
  accumulates nine/minute. More workers worsen the queue until integration is
  partitioned, sped up or admission is limited. Variance and bursts need slack.

Provider concurrency, rate limits, model latency, CPU/RAM and test throughput must
be measured before inferring that a scheduled worker corresponds to an active
model stream. No current provider price or free-tier capacity is assumed here.

## 8. Existing software to evaluate before building

This is a **read-only candidate assessment**, not dependency/security clearance
or an installation plan. Repositories were checked on 15 November through GitHub.
Actual source-license files take precedence over repository classifier metadata.

| Candidate | Verified availability / license / activity | Reuse decision |
| --- | --- | --- |
| [Microsoft Agensh](https://github.com/microsoft/Agensh) | MIT; unarchived; pushed 3 November. Reproduction guide provides shared work/context, messaging and event routing; released guide focuses on a single-node team. | Strong first reference implementation for this goal. Audit operational fit before adapting; the paper's multi-node result is not proof of a drop-in 100-worker Codespace install. |
| [DeLM](https://github.com/yuzhenmao/DeLM) | Actual LICENSE is MIT despite GitHub's `NOASSERTION`; unarchived; pushed 9 October. Current README describes two/four-agent native-harness comparisons. | Reuse compact shared-context ideas and inspect its current native integration; do not silently equate current code with original paper experiments. |
| [CAID](https://github.com/JiayiGeng/CAID) | Unarchived; pushed 2 April. GitHub license metadata is null and root listing has no license file. | Reproduce the coordination idea with existing Git primitives; do not assume permission to redistribute its code. |
| [Parallel Agent Teams code link](https://github.com/modal-projects/parallel-agent-teams-scaling) | Paper advertises code, but both connected GitHub and web access returned 404 at inspection. | Paper is usable; implementation availability/license/maintenance unverified. Do not promise a ready installation. |
| Existing TTGL + Langfuse and Git | Existing local evidence capture, accounting, review UI and source-versioning components | Keep these as the measurement/integration foundation. Fleet-wide causal links, distributed ingestion and ownership scheduling still require capability/load assessment. |

Gitea and Mattermost are components used by a studied system, not requirements
to install a duplicate stack here. The current research task needs no package,
image or model download. Before any implementation, check complete pinned
dependencies, advisory findings, licenses, scripts, upstream provenance and
service requirements under the [security policy](../security/dependency-security-policy.md).
Open source does not mean zero infrastructure or model-inference cost.

## 9. How TTGL's evidence changes the proposed experiment

Our [24-cell native team pilot](../paper/codex-team-knowledge/pilot-results.md)
has all saved sources passing, but higher capacity comes with higher minimum
model-rate cost. Native capacity eight uses four or five distinct coding threads;
it is not an observed eight-worker concurrency result. The added MCP memory
receives 91 observations but its four read queries return no entities. Thus the
pilot does not test effective reuse of retrieved peer knowledge.

The [56-cell extension](../paper/codex-team-knowledge/memory-aware-results.md)
is incomplete at the latest published 39-cell snapshot, with 38 source passes
and 37 normal parents. Keep its failures, unknown costs and operational strata.
Do not pool it into a finished scaling result or use it to claim memory wins.
Our [held-out context report](../paper/context-memory/report.md) also shows
that cheaper retrieval can lose quality and that cache behavior can reverse
token-only economic conclusions.

The next question should therefore be **which organization turns additional
concurrency into verified throughput, and what incremental contribution comes
from evidence sharing?** A new 100-agent study must be separately registered;
do not modify or resume the old studies as a shortcut.

## 10. Proposed route to a controlled 100-agent evaluation

This is a design recommendation, **not a frozen protocol or authorized model
launch**. No new inference, installation or schedule is created by this review.

1. **Define two tracks.** One shared-artifact track with genuine module/interface
   dependencies; one scored search track with alternative complete candidates.
   Independent-job throughput is a third operational control if it matters.
2. **Validate the instrument.** Reconcile existing telemetry, native counters,
   all actor roles, auxiliary compaction, rate-limit waits and artifact versions.
   Measure collector overhead without assuming the local polling app scales.
3. **Compare small configurations first.** Use 1, 4, 8 and 16 concurrent agents
   to test decentralized claims/shared evidence against modular delegation and
   independent attempts. Freeze common task information, model/tool access and
   acceptance. Count leaders and reviewers in the total; include auxiliary calls.
4. **Ablate knowledge before scaling its backend.** Keep the same scheduling,
   artifacts and source corpus; compare notebook/files, compact evidence-linked
   sharing, and a richer memory system only if needed. Record actual exposure.
   Use reset/persistent conditions separately for cross-task accumulation.
5. **Test 32, 64 and 100 on preselected development workloads.** Declare launch
   ramp, sustained concurrency target, resource/budget caps and stop rules before
   inference. Preserve every failure and uncertain invocation. Do not manufacture
   utilization by assigning redundant work when the dependency graph is narrow.
6. **Compare topology at the same total budget.** On the search track, include
   100 independent agents, small independent teams and one shared 100-agent
   organization. On the artifact track, compare decentralized workers and
   module teams with explicit integration. A 100-agent flat system is a baseline,
   not the assumed final design. Team counts include their coordinators.
7. **Freeze and evaluate transfer.** Select on development only. Use fresh,
   diverse repositories/tasks and repeated runs; do not tune from reserved
   validation or report a favorable subset as the final result.

Report both fixed-total-inference-budget quality and fixed-deadline quality/cost.
They answer different questions. Predeclare the minimum useful improvement and
acceptable regression margin from development variability, not arbitrary task
counts. Include a capable single-agent control and compute-matched independent
sampling. Measure end-to-end verified completion, not just successful-run speed.

**Candidate research hypothesis:** bounded, evidence-linked sharing plus explicit
work ownership and scalable integration will outperform both isolated workers
and unstructured global conversation on suitable shared-artifact workloads.
For scorer-guided exploration, smaller communicating teams with preserved
between-team diversity are a separate promising hypothesis. The team size,
centralization level and economical operating point remain empirical questions.
