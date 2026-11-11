# Shared knowledge and native Codex team scalability

Working design, 10–11 November 2026. The prospective design below is preserved;
dated continuation entries and the linked frozen pilot protocol record actual
execution. The 24-cell development pilot is running. Research schedules remain
paused.

Paper title requested by the user: **Investigate how knowledge accumulation and
generalization frameworks accelerate effective innovation outcomes.**

## Research question and scope

Do ready-to-use, self-hosted knowledge systems improve the ability of native
Codex teams to complete complex repository tasks correctly, faster, or at lower
total cost? Does their effect change with team size and accumulated experience?

Shared memory communicates knowledge across agents and time. The intervention
is how findings, failed approaches, interface agreements and check evidence are
recorded, retrieved, revised and acted upon. More messages, memory entries or
tool calls are not themselves evidence of useful knowledge or innovation.

The user explicitly prioritizes coding performance, complex work in one
repository, native leading-lab agent systems, and existing OSS knowledge systems.
Energy simulations, cross-team replacement/transfer, a new swarm orchestrator,
and a broad replication of all single-versus-multi-agent comparisons are outside
the main scope. Existing benchmark tasks and independent executable evaluators
should be reused.

## Hypotheses, including adverse outcomes

1. Shared experience can reduce repeated investigation and incompatible
   assumptions, improving verified completion or time to the same checked result.
2. Structured retrieval may help larger teams more than a plain notebook, but
   extraction, retrieval, irrelevant facts, stale claims and coordination can
   outweigh that benefit. No positive effect or monotonic scaling is assumed.
3. Useful knowledge can accumulate during a substantial task. Persistence across
   distinct tasks is a separate comparison and requires compatible source order,
   own preceding visible work, and a reset-memory control.

Single-agent memory benefits must be distinguished from a team-specific effect.
For example, compare the memory-on/off quality difference for four agents with
the corresponding difference for one agent. Report actual observations and
paired uncertainty; do not assume a graph is better than text.

## Existing systems inspected before custom implementation

Inspected public upstream documentation and repository metadata on 10 November.
These are candidate integrations, not security clearance or runtime validation.

| Candidate | Evidence | Decision |
| --- | --- | --- |
| Graphiti official MCP | Apache-2.0 core; repository not archived, pushed 9 November; official MCP exposes episode ingestion, fact/node search and graph operations; MCP described as experimental | Candidate: configure documented shared group and provider; do not replace extraction with our custom Luna adapter and call it out of the box |
| Cognee official MCP | Apache-2.0; repository not archived, pushed 10 November; remember/recall/forget and explicit dataset scoping | Candidate: explicitly share a team dataset, rather than assuming default per-client scoping gives shared memory |
| Mem0 self-hosted server | Apache-2.0; repository not archived, pushed 6 November; active self-hosted REST server | Reserve until a maintained self-hosted Codex integration is verified; a custom REST wrapper would be an adapted condition |
| Old Mem0 OpenMemory/MCP | Archived-component notices in upstream READMEs | Do not use as maintained native integrations; the OpenMemory repository itself being unarchived does not negate its component deprecation notice |
| Plain shared project notebook | Native filesystem tools, explicit evidence and revision references | Essential low-overhead control; no new memory engine required |

Sources:

- [Graphiti MCP](https://help.getzep.com/graphiti/getting-started/mcp-server),
  [core/license](https://github.com/getzep/graphiti).
- [Cognee MCP and scoping](https://github.com/topoteretes/cognee/blob/main/cognee-mcp/README.md),
  [core/license](https://github.com/topoteretes/cognee).
- [Mem0 server](https://github.com/mem0ai/mem0/blob/main/server/README.md),
  [OpenMemory archive notice](https://github.com/mem0ai/openmemory/blob/main/openmemory-archive/README.md),
  [old MCP archive notice](https://github.com/mem0ai/mem0-mcp/blob/main/README.md).

Self-hosting storage does not imply free or local inference. Record every
backend's LLM, embedding, reranking and consolidation requirements and calls.
Use supported upstream provider configuration. Provider changes are disclosed
configuration choices; replacing core behavior is an adaptation. No hosted
fallback, automatic package install or unmetered auxiliary inference.

## Proposed development comparison

Keep native Codex delegation and integration; do not implement a new manager.

Conditions:

1. Native Codex with its normal messages and source artifacts, no added
   persistent knowledge service. This is not a no-communication condition.
2. Same system plus a shared evidence-linked project notebook.
3. Same system plus Graphiti through its documented MCP interface.
4. Same system plus Cognee through its documented MCP interface.

The planned comparison crosses total-agent limits 1, 2, 4 and 8 with all four
knowledge conditions. Include the parent in the declared total, validate
installed-version cap semantics, and record actual active agents/concurrency
and serial delegation. Private-versus-shared backend namespaces would be a
separate ablation. This is a proposed panel, not a frozen execution matrix.

Use one pinned Codex build, solver model and reasoning setting, common task
instructions, permissions, source state, machine class and integration policy.
The agent selects subtasks using native delegation. It is allowed to leave
capacity unused; a capacity limit is not a fixed-size team observation.

Use minimal, frozen backend-specific usage guidance necessary for documented
tools. Backend comparisons estimate the effect of the complete integration,
including tool descriptions and maintenance; they do not isolate data structure.
All team members must demonstrably see the intended namespace and the same
supported tools. A same-source, bounded-exposure ablation would be separate.

Native personal memories, prior task solutions, unrelated plugins and automatic
personal project guidance must be excluded using isolated experiment profiles.
Record inherited parent/subagent context, compaction and source-file visibility.
Code, commit messages and test output are additional knowledge channels common
to the conditions, and must not be described as absent in the control.

## Tasks and independent verification

Commit0 repository-scale implementation is the leading candidate. Initially
inspect SimPy, Cookiecutter, TinyDB and Jinja: real library components create
dependencies and enough work for meaningful collaboration. They are development
candidates, not demonstrated solo-solvable tasks or reserved validation cases.

Use the full pinned task contract and tests where feasible. Requests' scoped
AsynCodeBench variant omits some integration tests; do not equate that with full
Requests completion. Any scope restriction must precede inference, be explicit
in the task name, and limit conclusions accordingly. AsynCodeBench dependency
checks are useful diagnostics, but its fixed specialist protocols are not a
native Codex scaling benchmark.

Commit0 harness inspected at `1123db33219ee1bfcc735304cb4308663e329aeb`
(MIT, last commit 24 February 2026; includes history-leak prevention).
AsynCodeBench inspected at `2a639b049f249e79eb2031876bc06a110be9ac3a`
(v0.4.2). Dataset version, task revisions, licenses, runtime and test assets still
need pinning and validation. Do not run upstream installers as setup shortcuts.

Measure initial controls: the incomplete base must fail relevant acceptance and
the independent reference must pass. Keep reference implementations and Git
history exposing solutions outside actor mounts. Preserve tests, run independent
final replay, and distinguish public-test completion from held-out robustness.
No original reference code or hidden evaluator outcomes enter live knowledge.

A development pilot will measure actual single-agent completion and duration.
Do not promise eight-agent acceleration, discard difficult cases after seeing
outcomes, or generalize from a handful of libraries. Reserve later evaluation
tasks/repositories before tuning. Freeze policies and repetitions before that
evaluation; choose sample size from development variability and an explicit
minimum useful effect, not an arbitrary 36-task count.

## Outcomes and knowledge traces

Primary: independently verified complete integrated solution within a declared
deadline/budget. Also report test fraction without calling it full completion.

- End-to-end time includes planning, worker execution, retrieval, integration
  and verification. Report verified completion by time and by expenditure;
  failures/deadlines remain in the denominator. Successful-run latency alone
  can select an easier subset.
- Report all native response tokens and separately priced backend inference,
  embeddings and reranking; count final updates and failed/uncertain requests.
  Deduplicate response IDs and validate thread-counter deltas. Unknown is null,
  not zero. Cost per verified resolution includes unsuccessful expenditure and
  is undefined when zero tasks resolve.
- Published-rate scenarios, provider-estimated charges, subscription cash,
  quota usage, local compute and research overhead remain distinct.
- Record service/operation durations, provider queueing, rate limits, CPU/RAM
  and tool contention separately from model coordination. Equal hardware and
  fixed versus per-agent budgets answer different scaling questions; freeze
  the selected resource regimes before inference.
- Preserve observable write -> retrieval -> action -> check links, authors,
  evidence IDs, source revisions, invalidations and readiness lag. A search hit
  is exposure, not proof that the knowledge caused a correct action.
- Inspect duplicate investigations, contradictory claims, stale reads,
  unanswered dependencies, integration failures and suppressed exploration.
  Labels are evidence-backed interpretations, not automatic waste/failure
  verdicts. Count analyst inference separately.

Randomize or counterbalance condition execution by task and repetition. Analyze
paired task outcomes and size-by-knowledge effects; tasks in one repository are
dependent. Trace correlations motivate mechanisms; matched interventions are
needed for causal claims. Keep failures and all attempted treatments.

## Relationship to prior work

Native multi-agent on/off and team-size effects already have direct precedents:

- [Native concurrency study](https://arxiv.org/html/2610.10263) compares Codex,
  Claude Code and Kimi Code. Do not present our single-agent controls as a new
  discovery that delegation can help or hurt.
- [Vals native team study](https://vals-ai.com/blogs/multi-agent-vibe-code-bench)
  compares quality, cost and time at multiple reasoning efforts.
- [CAID](https://arxiv.org/html/2603.21489) studies repository-scale cooperation
  and isolation; [DeLM](https://yuzhenmao.github.io/DeLM/) uses shared verified
  context; [SEPM](https://arxiv.org/html/2610.14515) evolves shared procedures.
- [Anthropic compiler case](https://www.anthropic.com/research/building-c-compiler)
  demonstrates substantial shared-artifact work with task claims and progress
  notes. It does not isolate the benefit of a knowledge system.

Candidate contribution: comparative evidence about whether maintained,
self-hosted knowledge integrations help native Codex teams turn accumulated
experience into verified software outcomes, and where costs or coordination
failures reverse the benefit. Novelty remains provisional pending a focused
methods-level overlap review. No claim to invent shared memory or team learning.

## Current preparation and execution boundaries

On 10 November, local CLI reports `0.167.0`, `multi_agent` enabled,
`multi_agent_v2` available but disabled, and `agent_message_board` under
development/disabled. Current docs and installed behavior need a positive
compatibility probe before configuration is frozen. No settings were changed.

The older 216-assignment longitudinal experiment has no active worker in this
executor; its preserved progress shows incomplete generation and it has no
completion receipt. Earlier unique `/tmp` resources are absent in this session.
Do not resume it, repeat an uncertain call, infer grades, or repurpose its stores.
It remains a separate historical study requiring its own recovery audit.

Workspace free space is constrained (about 524 MiB observed); `/tmp` has more
space but is not durable across executor replacement. Existing observability
services and source histories must not be deleted to make room. No new packages,
images, knowledge servers, model calls or scheduled jobs were started here.

Before live trials: exact task reservations; source/test provenance and leak
audit; complete pinned dependency review under the standing Codespace policy;
reference/base controls; native delegation/context/namespace and concurrent
read/write tests; all backend-inference metering; host/actor boundary; declared
budgets and immutable attempt manifests. Incomplete security evidence alone has
the user's Codespace exception, but confirmed vulnerability findings still
block affected candidates. No retries of started or uncertain model calls.

## Local-provider investigation, 10 November

The user selected fully local auxiliary inference. Codex remains the solver.
This Codespace has two CPU cores, approximately 8 GB RAM and no GPU; local
provider throughput and contention must be measured. A quantized Qwen3-4B model
was downloaded and hash-verified as data only. No downloaded runtime was executed.
Static review found unresolved llama.cpp parser/sampler advisory applicability,
so the binary remains blocked pending a verified remedy. Ollama also requires
advisory reconciliation. The next candidate is the maintained Hugging Face
Transformers OpenAI-compatible server with a smaller CPU-capable model. These
are feasibility checks, not scored coding assignments or evidence of benefit.
Private dated source and advisory receipts are retained under
`work/security/codex-team-knowledge-20261110/`.

## Observed preparation, 11 November

The [preparation results](../paper/codex-team-knowledge/preparation-results.md)
supersede the earlier inspection-only status. Two development base/reference
controls pass their expected gates. Native delegation, isolated access,
all-member MCP visibility at four total agents, and official MCP storage with
eight processes are demonstrated. A small local Qwen provider and BGE embeddings
are operational; Graphiti schema accuracy and full ingestion readiness remain
separate gates. Confirmed affected llama.cpp code remains unexecuted. Provider
adaptations, failed attempts and unknown usage are preserved explicitly.

The original four-arm matrix is not frozen for scoring. A standalone TinyDB
development feasibility unit is prepared separately, with no assignment retry.
The twelve evaluation libraries remain reserved. No scheduled research was
resumed and unrelated historical studies/services remain untouched.

The independent TinyDB feasibility replay passes 200 tests with one prescribed
skip, 244.42 s and 726,995 fully reconciled native tokens. It is excluded from
the subsequently frozen 24-cell development scaling pilot, whose local
registration is `experiments/codex-team-knowledge-001/scaling-pilot-protocol-002.json`.
The first comparative unit has started; generation/evaluation/queue sources
listed there are frozen. Do not edit them or start a duplicate worker. Original
captures and exact CAS objects are retained per unit before verified lossless
archival. The queue stops on ambiguity and never retries an assignment.
