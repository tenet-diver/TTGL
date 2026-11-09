# Investigate how knowledge accumulation and generalization frameworks accelerate effective innovation outcomes.

**TTGL research working paper · 9 November 2026 · Version 0.1**  
**Empirical scope:** completed local memory and cost diagnostics; a metadata-audited design for longitudinal repository experiments. The proposed same-repository head-to-head, native-memory comparison, and editable challenge-graph experiment have **not yet produced model-quality results**. This is an interim paper, not a completed comparative benchmark report.

## Abstract

Persistent memory can make a personal coding agent more useful if experience from one task reduces the effort required to complete later tasks. However, storing information, recalling it, and generalizing it into successful action are different achievements. We investigate the relationship through a focused literature review, completed instrumented development experiments, and a prospective evaluation of repeated work in the same repository. The comparison covers ordinary source retrieval, continued conversation, Generative Agents–style memory with cheap-model maintenance, Mem0, Zep's open-source Graphiti engine, TokenEconomizer, native coding-agent memory, and a proposed editable challenge graph. In an eight-function native-interface diagnostic, all conditions pass all checks. Luna-maintained Smallville memory costs 18.43% more than source search in a published-rate model-inference scenario. A TokenEconomizer memory condition costs 12.05% less, but injects no skills and performs no pruning or redirection; the difference cannot establish a memory benefit. Separately, adapted Mem0 passes twelve generated recall checks but costs 271.81% more than continued context, including extraction. These experiments establish neither generalization nor accelerated innovation. We therefore specify a longitudinal extension of VibeMemBench with matched information access, executable verification, memory-on/off controls, graph-versus-flat ablations, and full maintenance accounting. Our conclusion is conditional: accumulated knowledge accelerates useful outcomes only when its reuse changes behavior enough to offset preparation, retrieval, verification, and correction costs without reducing quality.

**Keywords:** agent memory; knowledge accumulation; generalization; coding agents; temporal knowledge graphs; software maintenance; inference economics; innovation measurement.

## 1. Introduction

A coding assistant repeatedly working in one codebase should not have to rediscover its architecture, repeat an unsuccessful installation command, or relearn why an apparently plausible fix violates a repository invariant. This motivates persistent agent memory. The important outcome is not the number of stored facts. It is whether experience helps produce the next verified change with less wasted work and no unacceptable loss of correctness.

Knowledge accumulation offers several possible mechanisms. An agent can remember environment procedures, retrieve earlier investigations, connect a failure to its cause, or abstract a solution into a reusable rule. It can also retain incorrect explanations, overgeneralize a local workaround, or consume more inference maintaining its memory than it saves. Stronger models may already infer the relevant rule from source code; ordinary file search and cached conversation can be competitive controls. A memory system must therefore earn its place against an informed baseline.

We operationalize an **effective innovation outcome** narrowly as a useful, independently verified code change addressing a new task, together with the resources consumed to achieve it. This is a tractable proxy for productive problem solving. It does not measure commercial impact, scientific discovery, human creativity, or novelty to the world. A benchmark improvement cannot establish those broader outcomes.

The research questions are:

1. **Accumulation:** Does access to earlier experience improve verified outcomes or reduce complete task cost relative to matched source access and native memory controls?
2. **Generalization:** Does remembered experience help on a distinct later task, rather than merely reproduce an answer or recall an identifier?
3. **Representation:** Does an editable graph add value beyond the same evidence expressed as flat notes?
4. **Division of labor:** Can a cheap model prepare and maintain useful knowledge while a larger model solves and verifies the task economically?
5. **Mechanism:** Do improvements coincide with observable avoidance of repeated exploration or mistakes, rather than only changes in cache use or response length?

The contribution of this draft is an evidence audit and an explicit evaluation design. Combining models, reflection, retrieval, graphs, and persistent memory is established prior art. We make no first-invention claim for that combination.

## 2. Literature review

### 2.1 Knowledge accumulation and innovation

Cohen and Levinthal describe absorptive capacity as an organization's ability to recognize, assimilate, and apply external knowledge, influenced by prior related knowledge. This motivates testing whether repository experience improves an agent's ability to use a new observation. It does not establish that enlarging an agent's memory causes innovation. [Cohen and Levinthal, 1990](https://doi.org/10.2307/2393553).

Nonaka's account of organizational knowledge creation emphasizes interaction between tacit and explicit knowledge. For coding agents, a limited analogy is the conversion of an observed investigation into an inspectable procedure or explanation. This is an analogy about representation and reuse; model-generated notes are not evidence of human tacit knowledge. [Nonaka, 1994](https://pubsonline.informs.org/doi/abs/10.1287/orsc.5.1.14).

March distinguishes exploring new possibilities from exploiting established knowledge. Persistent procedural memory could accelerate exploitation while discouraging necessary investigation after an environment changes. We therefore require stale-knowledge cases and retain permission to challenge a remembered rule. [March, 1991](https://pubsonline.informs.org/doi/abs/10.1287/orsc.2.1.71).

These theories supply hypotheses and potential failure mechanisms, not empirical validation of an LLM architecture. Our experiments concern observable agent behavior and executable outcomes.

### 2.2 Retrieval, reflection, and procedural memory

Retrieval-augmented generation combines model parameters with an external information source. Its foundational evaluation concerns knowledge-intensive language tasks, not an agent learning a repository's operational procedures. A lexical or dense retrieval baseline remains essential: a graph must outperform access to the underlying evidence, rather than merely benefit from having evidence that the control lacks. [Lewis et al., 2020](https://arxiv.org/abs/2005.11401).

Generative Agents store observations, retrieve relevant experiences, and synthesize reflections. Their Smallville evaluation concerns believable social behavior. Adapting this architecture to coding requires a different outcome measure and evidence discipline: a plausible reflection about a failed command is not necessarily a correct causal explanation. [Park et al., 2023](https://arxiv.org/abs/2304.03442).

Reflexion uses linguistic feedback and episodic memory to improve subsequent attempts without updating model weights. The distinction between feedback sources matters: public compiler or test output is legitimate learning evidence, whereas a hidden benchmark grade must remain outside the live controller. [Shinn et al., 2023](https://arxiv.org/abs/2303.11366).

Voyager develops reusable executable skills with environment feedback in Minecraft. It demonstrates a form of accumulating procedural capability, but its results do not establish that natural-language graph memory improves repository maintenance. [Wang et al., 2023](https://arxiv.org/abs/2305.16291).

MemGPT manages information across memory tiers and a bounded context window. A-MEM adds dynamically linked notes and memory evolution. Together they show why memory management, retrieval, and editing should be compared separately from any change to the base model's weights. [Packer et al., 2023](https://arxiv.org/abs/2310.08560); [Xu et al., 2025](https://arxiv.org/abs/2502.12110).

### 2.3 Mem0, Zep/Graphiti, and graph-based retrieval

Mem0 extracts, consolidates, and retrieves conversational information; its paper also studies a graph variant. Its reported evaluation uses LoCoMo. Those results motivate a comparison but do not predict coding-task success or the economics of our adapted backend. We distinguish the self-hosted package from its commercial service and distinguish extracted memory from `infer=False` raw storage. [Chhikara et al., 2025](https://arxiv.org/abs/2504.19413).

Zep's paper presents a temporal knowledge-graph architecture built around Graphiti, evaluated on conversational memory tasks including LongMemEval. Our proposed comparison uses self-hosted **Graphiti**, not hosted Zep and not an assertion of feature parity with that service. Temporal validity, entity resolution, and changing relationships are relevant to codebases, but must be tested under repository changes. [Rasmussen et al., 2025](https://arxiv.org/abs/2501.13956).

GraphRAG constructs entity relationships and community summaries for corpus-level question answering. Its global summarization objective differs from remembering a checked command, invalidating an obsolete workaround, or integrating a patch. “Uses a knowledge graph” therefore does not identify a single intervention. [Edge et al., 2024](https://arxiv.org/abs/2404.16130).

Our proposed challenge graph is a controlled extension of these ideas. It represents the current public problem and historical evidence, allows the solver to revise the representation, and distinguishes observations from hypotheses. Whether that structure adds value is an experimental question.

### 2.4 Operational cost control and native memory

TokenEconomizer is particularly relevant because it addresses recurring environment costs across coding tasks through injected operational skills, tool pruning, and intervention in unproductive loops. Its published savings concern its evaluated agent/model configurations. Our local comparison must verify that these mechanisms actually activate before attributing a numerical difference to them. [Li et al., 2026](https://arxiv.org/abs/2610.22732).

Native agent memory is a product-level baseline, not a synonym for an instruction file or a resumed thread. Codex documents a local memory feature with separate generation and use settings. A credible comparison must establish that it learned from eligible experimental sessions and injected memory into later sessions, while measuring background extraction and consolidation. Existing personal memory must not enter either arm. [OpenAI, Memories documentation](https://learn.chatgpt.com/docs/customization/memories).

### 2.5 Benchmarks and the remaining gap

LoCoMo and LongMemEval measure conversational memory, including temporal reasoning and updates. They are useful component tests but do not require executable modifications to a shared repository. [Maharana et al., 2024](https://arxiv.org/abs/2402.17753); [Wu et al., 2024](https://arxiv.org/abs/2410.10813).

SWE-bench evaluates patches for real repository issues; SWE-bench Verified provides a human-validated subset. A random collection of independent issues, however, does not guarantee that earlier experience is useful for later issues. Repository overlap alone is insufficient. [Jimenez et al., 2023](https://arxiv.org/abs/2310.06770); [OpenAI, 2024](https://openai.com/index/introducing-swe-bench-verified/).

SWE-Bench-CL explicitly proposes repository issue sequences and continual-learning metrics. It is a relevant longitudinal alternative; its protocol and code must be assessed before treating it as an interchangeable benchmark implementation. [Joshi et al., 2025](https://arxiv.org/abs/2507.00014).

VibeMemBench directly tests memory for executable repository work: 111 targets, 90 repositories, and 3,634 historical trajectories. Its authors select targets where history improves a reference setting; transferred useful experience helps four of five held-out solvers, while eleven of twelve evaluated memory-system/solver pairings do not beat memory-off. These are **the authors' results**, not our measurements. The selection supplies evidence of learnability in a reference setting, while introducing selection bias and leaving transfer to our solver uncertain. [Fan et al., 2026](https://arxiv.org/abs/2609.23570).

This review is a focused primary-source review, updated on 9 November 2026, not a systematic review or meta-analysis. We selected work that implements persistent retrieval, reflection, temporal or editable memory, procedural reuse, or executable longitudinal evaluation. We do not pool accuracy or cost figures across their incompatible benchmarks.

## 3. Systems and comparison boundaries

Table 1 separates mechanisms, implementation status, and evidence. It is not a ranking.

| System or control | Mechanism and proposed role | Local evidence at this draft |
|---|---|---|
| Fresh Sol; durable memory off | Current issue/source/public checks; no earlier private experience | Source-search coding diagnostic complete; no new repository-sequence result |
| Continued Sol thread | Retained conversation and cache reuse | Generated repeated-recall diagnostic complete; not durable-memory on |
| Native Codex memory | Product's own extraction, consolidation, and injection | Documentation/source inspected; isolated on/off efficacy comparison pending |
| Exact history files / lexical retrieval | Searchable raw experience without model extraction | Completed recall and small coding controls |
| Smallville with Luna maintenance | Observation importance, retrieval, and reflection architecture | Coding diagnostic complete; no natural reflections in those assignments |
| Mem0 OSS, adapted dense configuration | Stock extraction/consolidation/storage/search with local embedding and native Codex transport | Repeated-recall diagnostic complete; coding comparison pending |
| Graphiti OSS, Zep comparison | Temporal graph construction and retrieval | Client import/protocol preparation only; server and efficacy comparison pending |
| TokenEconomizer default / Luna memory enabled | Operational skill selection, tool pruning, loop redirection | Small coding comparison complete; no observed interventions |
| Challenge graph, task only | Luna prepares current-problem graph; Sol can inspect/update; reset after task | Proposed; no model-quality result |
| Persistent challenge/repository graph | Same task graph plus admissible prior experience and retained edits | Proposed; no model-quality result |
| Flat evidence ablation | Same graph facts/provenance rendered as notes without graph traversal | Proposed; no model-quality result |

The reviewed Mem0 package is version 2.2.1 with FastEmbed 0.9.1; the Graphiti client is 0.31.2. TokenEconomizer source is pinned at `264e7a7f32f0112a06aa83a97b9c2c4681563968`. These are study configurations, not claims about the latest or default hosted products. Mem0's package is Apache-2.0 and Graphiti and TokenEconomizer use Apache-2.0; any redistributed dependencies retain their own terms. The comparison selects self-hosted software and has no hosted-memory subscription assumption. Remote model inference and local compute remain costs.

Existing engines should supply storage, extraction, search, and graph operations wherever suitable. The missing product-specific work is the challenge/evidence schema, access boundary, matched experimental adapters, and complete accounting. Reimplementing a general memory database would add a confound and is not the proposed contribution. A simple graph server must never be relabeled Graphiti or Zep.

The November 9 [source audit](../../../tools/usage-monitor/studies/repository-memory-source-audit-001.json) confirms recent repository activity and non-archived status for Mem0, Graphiti, and TokenEconomizer, and records their licenses. Fresh OSV queries for the already resolved 50/29/4-package Mem0/Graphiti/MCP graph configurations return no matches. That is not a complete runtime/OS or supply-chain clearance. Luna and Sol are opaque hosted model labels; we do not infer parameter counts, open weights, or local deployability from their relative prices.

## 4. Experimental methods and completed results

### 4.1 Evidence levels and accounting

We distinguish integration checks, generated recall, function-level coding, and longitudinal repository work. Passing one level does not imply passing the next. Historical runs remain frozen; this paper reanalyzes their published local receipts and does not present them as newly executed repository experiments.

For response \(j\) from model \(m\), let \(I_j\), \(K_j\), and \(O_j\) denote total input, cached-input subset, and output tokens. A published-rate scenario is:

\[
C_j = ((I_j-K_j)r^{in}_m + K_jr^{cache}_m + O_jr^{out}_m)/10^6.
\]

Thus cached tokens are not counted twice. Task/stream model cost includes preparation, extraction, reflection, retrieval calls, solver work, integration, and consolidation. We use response identifiers or validated cumulative-counter deltas, not a sum of repeated thread snapshots. Unknown usage remains unknown, including failed calls without completed counters.

The November 9 native coding scenario uses credits per million tokens of Luna 2.5/0.25/12.5 and Sol 50/2.5/250 for uncached input/cached input/output respectively, as preserved in its accounting receipt. Earlier recall scenarios retain their historical study rates and are not repriced or pooled with this block. These figures are model-inference scenarios, **not measured subscription cash charges, account-credit consumption, quota savings, or full deployment cost**. Local embedding/storage monetary cost is unknown. Research and supervision overhead is separate from deployment task cost and cannot be assumed recovered on first use.

### 4.2 Experiment A: Smallville and TokenEconomizer coding diagnostic

The completed study contains 72 coding assignments across two 32-assignment interface blocks and an eight-assignment later-period maintenance control. They reuse **eight public HumanEval functions**. Consequently 72 is not the number of independent tasks, and these observations are development diagnostics. Sol solves in all conditions. The native-interface block exposes native tools and the pinned TokenEconomizer hooks; a separate block limits the interface to isolate memory behavior.

Table 2 reports the native-interface block and the separate Sol-maintained Smallville control. Every condition passes 8/8 checks. All figures include observed maintenance inference.

| Condition | Solver scenario credits | Maintenance scenario credits | Total | Change vs source search |
|---|---:|---:|---:|---:|
| Source search | 4.409320 | 0 | 4.409320 | reference |
| Smallville, Luna maintenance | 4.838390 | 0.3834605 | 5.2218505 | +18.43% |
| TokenEconomizer default | 4.676670 | 0 | 4.676670 | +6.06% |
| TokenEconomizer, Luna memory enabled | 3.841160 | 0.0369515 | 3.8781115 | −12.05% |
| Smallville, Sol maintenance; later-period control | 4.009540 | 5.716400 | 9.725940 | +120.58% |

Luna maintenance costs 93.29% less than Sol maintenance in the last comparison; complete model cost is 46.31% lower. The control occurs later and is not a simultaneous randomized identical-history replay. It supports a bounded observation about the cost of this maintenance configuration, not a general causal estimate of model substitution.

The diagnostic's most important finding is mechanism absence. All coding arms produce **zero natural reflections**. The TokenEconomizer arms inject **zero skills**, perform **zero pruning actions**, and issue **zero redirects**. Its memory-on condition passes the numerical development cost gate, but that does not identify a memory effect. Cache state, stochastic generation, and output differences remain plausible explanations. A separate forced-reflection diagnostic establishes that Luna can generate and retrieve reflections under the adapted output contract; it does not demonstrate useful reflection on these coding tasks.

Across the complete study, trials and diagnostics account for 494 unique native responses, 270 model-bearing processes, 5,292,938 native tokens, and 49.1993445 scenario credits. Native, CLI, and captured-response records reconcile; Langfuse delivery for this study is not verified. One synchronous session-end wrapper failure is retained. An exact-output recovery restores already completed inference without another model call; the missing child process-lifetime receipt remains missing.

These results do not show memory accelerating innovation. They show that cheap maintenance can reduce one source of overhead, and that a short easy benchmark can produce apparently favorable totals without exercising the proposed mechanism. The [frozen results](../../../tools/usage-monitor/studies/luna-memory-tokeneconomizer-final-results-001.json) and [methods report](../../research/luna-memory-tokeneconomizer.md) provide the underlying receipts.

### 4.3 Experiment B: Mem0 reuse and cache-sensitive recall

A separate completed development experiment uses three generated corpora and four questions per corpus. It compares continued context, fresh full context, files, full-text search, and actual extracted Mem0 memory. It makes 72 reader calls and three extraction calls; all arms pass 12/12 exact field checks. This is factual recall, not repository work or generalization.

| Condition | Native tokens, including extraction | Historical scenario credits | Change vs continued context |
|---|---:|---:|---:|
| Continued full context | 480,951 | 5.46879 | reference |
| Ordinary file search | 572,597 | 5.50505 | +0.66% |
| Fresh full context, stable prefix | 605,027 | 13.72351 | +150.94% |
| Fresh full context, changing prefix | 475,801 | 14.21133 | +159.86% |
| Exact full-text excerpts | 632,529 | 6.59329 | +20.56% |
| Adapted Mem0 dense | 850,894 | 20.33354 | +271.81% |

The adapted Mem0 configuration uses stock memory extraction/storage/search, local pinned BGE embeddings, and a native Codex LLM adapter. This historical extraction configuration uses Sol; it is not the proposed Luna-maintained coding arm and is not hosted Mem0's default configuration. Extraction is charged once per corpus and reused by the four actual queries. No future break-even query count is observed or claimed.

The changing-prefix control consumes slightly fewer tokens than continued context while costing substantially more in the scenario because its cached fraction is lower. Therefore token reduction alone is an inadequate economic outcome. The experiment's 115 unique responses reconcile across native counters, CLI counters, and Langfuse, unlike the separate delivery status of Experiment A. See the [frozen result](../../../tools/usage-monitor/studies/cache-memory-reuse-results-001.json) and [extended discussion](../context-memory/report.md).

### 4.4 Experiment C: repository-sequence feasibility audit

We performed a **zero-model, metadata-only** audit of the released VibeMemBench target list and history filenames. It confirms 111 targets from 90 repositories. Nine Python repositories have multiple targets. A deterministic rule—Python, at least two targets, explicit allowlisted license, descending target count, repository-name tie break—reserves five `aws-cloudformation/cfn-lint` targets for development and four `getmoto/moto` targets for validation. No validation problem statements, patches, or trajectories were inspected for tuning.

| Reserved sequence | Target ordinals | Earlier same-repository history counts |
|---|---|---|
| Development: cfn-lint | 2387, 3342, 3875, 3965, 3972 | 5, 37, 108, 117, 118 |
| Validation: moto | 7035, 7795, 8780, 9005 | 105, 159, 238, 247 |

The strict exclusion removes the target's own trajectory and every larger issue ordinal. The benchmark uses issue ordinals as its temporal proxy; these are not independently verified PR completion timestamps. The bounded development design retrieves at most the eight latest admissible historical episodes per target. That cap may remove useful evidence; it must not be interpreted as reproducing an unrestricted upstream result.

The observed dataset API revision is `11164976b4f920cdb0d0cd570ca572e49acea1e8`; integration code was inspected at `7152cf96809b45343ccc1caf7115a7d3fa43f956`. The allowlisted metadata bytes are sealed separately. Exact equivalence between the dataset-viewer response and pinned Parquet remains a pre-inference gate; recording an API revision alone does not prove that equivalence. The [public audit](../../../tools/usage-monitor/studies/repository-memory-metadata-audit-001.json) is reproducible with the local metadata-audit script. Thirteen software checks cover temporal exclusion, namespace separation, duplicate rejection, hidden-field rejection, and deterministic partitioning. These are harness checks, not quality measurements.

The first development image was inspected without installation or execution. Its manifest contains 643,119,776 compressed layer bytes. A digest-verified base layer contains Python 3.10.19's `email/generator.py`, byte-identical to the upstream 3.10.19 source and different from the security-fixed 3.10.20 source. Python's release notes identify the latter fix as addressing CVE-2024-6923. This is a confirmed vulnerable base-component finding, not a completed final-overlay/OS/package scan. Under the standing execution policy the candidate is blocked, even if a task would not exercise email serialization. No image was run and no solver assignment was started. A patched compatible environment needs its own review and empty/reference verification. [Python Software Foundation, 2026](https://www.python.org/downloads/release/python-31020/).

This audit establishes that a repeated-repository comparison can be specified from existing data. It establishes neither useful-memory transfer to Sol nor success of any memory system. Its concrete execution gaps are retained in the [prospective protocol](../../../tools/usage-monitor/studies/repository-memory-protocol-001.json).

## 5. Proposed system: an editable challenge and repository graph

### 5.1 Representation

We propose a two-layer representation using an existing graph engine. A **challenge layer** describes the current public task: required behavior, relevant components, constraints, open questions, candidate explanations, attempts, and checks. A **repository layer** stores reusable environment procedures, architecture relationships, invariants, and lessons supported by earlier visible evidence. “Test-time graph” means the graph available while solving the current public problem. It never means a graph derived from hidden tests or the reference patch.

Each claim carries a repository namespace, source task, source revision, creation sequence, evidence identifiers, status, and any supersession relationship. Suggested relation types include `depends_on`, `constrained_by`, `attempted_in`, `supported_by`, `contradicted_by`, `checked_by`, and `supersedes`. Graph structure is a hypothesis about useful organization, not proof of factual accuracy.

An observation records what happened: command, exit status, output excerpt, environment, and relevant source hashes. A hypothesis records an explanation. A reusable procedure records its preconditions and the evidence that it worked. A failed command alone does not prove an approach is wrong or the task failed. A passing narrow check does not prove the entire task succeeded. Confidence is an attributed model judgment until calibrated against independent evidence.

### 5.2 Cheap-model preparation

Before the solver starts, Luna receives the current public request, an equal-budget repository inspection bundle, and admissible historical evidence. It prepares a bounded challenge graph with unresolved questions. It must preserve uncertainties, distinguish exact evidence from inference, and avoid inventing causal lessons. A generic preparation policy is shared across tasks; no task identifier, expected patch, hidden-test clue, or task-specific escalation rule belongs in it.

Preparation is not free. All Luna calls, embedding work, source-inspection tools, graph ingestion, and retrieval are recorded. A task-graph-only arm receives the same preparation process but no retained experience, allowing the effect of planning to be separated from accumulation.

### 5.3 Large-model use and editing

Sol receives the current task and the bounded retrieved subgraph with evidence pointers. It can inspect raw source, challenge graph claims, add new observations, revise hypotheses, and propose edits. It must verify an integrated change using available public checks. The controller validates record structure and scope; it does not silently decide that an unverified hypothesis is true.

After the task, eligible memories retain visible attempts, public checks, and the solver's stated uncertainty. Hidden evaluator results stay in a separate sealed store and never influence the next task. The graph does not promote a failed patch to a successful procedure merely because Sol wrote it. Revision-sensitive procedures are marked for rechecking when source or environment changes. Contradictions retain provenance rather than overwriting history without a trace.

The source worktree resets to each target's prescribed base revision. Prior generated patches are not silently applied to the next task. Persistence is through the registered memory channel; changes naturally present in the target's historical base remain legitimate source context.

### 5.4 Generalization versus recall

We distinguish four outcomes:

* **Exact reuse:** recalling a command, path, or previously recorded fact.
* **Within-repository transfer:** applying a checked rule to a distinct later issue.
* **Robustness to change:** recognizing when a formerly useful procedure is stale.
* **Cross-repository transfer:** applying a general procedure to a different repository under a separately registered boundary.

The first is useful but does not establish the others. No weight training is proposed in this experiment. Durable user preferences remain separate from task memory and model parameters. All arms receive the same authorized personal context, preventing a memory advantage from being attributed to model cooperation.

## 6. Prospective longitudinal experiment

### 6.1 Tracks and interventions

We separate two tracks. The **frozen-history track** follows the upstream add/search boundary with an independent memory namespace per repository/target cutoff. The **online track** extends that setup by retaining only an arm's own admissible experience between tasks. Frozen-history performance measures extraction/retrieval from an equal corpus; online performance measures accumulation plus solver interaction. These results must not be merged into a single unnamed treatment.

The upstream integration requires synchronous searchable ingestion, repository/cutoff isolation, ordered retrieval, and a result cap. Its per-target reset does not itself test a graph edited persistently across live target tasks. We preserve that contract for the frozen track and name the online variant explicitly. [VibeMemBench integration contract](https://github.com/AlibabaResearch/DAMO-ConvAI/blob/7152cf96809b45343ccc1caf7115a7d3fa43f956/VibeMemBench/scripts/CONTRACT.md).

The planned arms are:

| Arm | Prior experience | Model-based maintenance | Purpose |
|---|---|---|---|
| Fresh, native durable memory off | None | None | Minimum informed task control |
| Continued thread | Own prior transcript | Normal agent context behavior | Strong conversation/cache control; finite-history limits reported |
| Native durable memory on | Own eligible sessions | Native extraction/consolidation | Product baseline, with actual generation/use demonstrated |
| Exact history retrieval | Same admissible corpus | None | Information-access control |
| Smallville–Luna | Same corpus plus own visible experience | Luna | Reflection/retrieval comparison |
| Mem0–Luna | Same corpus plus own visible experience | Luna via disclosed adapter | Extraction/consolidation comparison |
| Graphiti–Luna | Same corpus plus own visible experience | Luna via disclosed adapter | Temporal graph comparison |
| TokenEconomizer default | Same permitted experience | Pinned default behavior | Operational-controller control |
| TokenEconomizer memory–Luna | Same permitted experience | Luna | Learned operational memory |
| Task-only challenge graph | Current public task only | Luna; Sol edits | Planning/preparation ablation |
| Persistent challenge/repository graph | Same corpus plus own visible experience | Luna; Sol edits | Proposed accumulation condition |
| Flat evidence notes | Same facts and evidence as graph comparison | Matched extraction | Representation ablation |

The flat control needs care because graph and flat solvers diverge after acting. A fixed, pre-task snapshot comparison can use literally identical facts rendered in two formats; a fully online comparison cannot maintain identical facts after divergent experience without copying information between arms. We therefore report a matched-snapshot representation ablation separately from independent online learning curves. Neither control reads the other's live private investigation.

For native memory, “off” must disable both use and generation, and “on” must isolate the experimental store and account for all native maintenance calls. Current source inspection reveals eligibility rules and separate memory endpoints, so the ordinary `codex exec` harness is not yet a validated implementation of this arm. A no-op enabled setting is not a valid positive control. Any changed idle/consolidation cadence must be disclosed as an experimental adaptation.

### 6.2 Information and leakage controls

Every solver receives the same current issue text, base source tree, available tools, public test access, solver model/version, reasoning setting, and resource limits. Memory-enabled conditions share the same admissible historical corpus. The source-retrieval control can search those raw episodes; a separate no-prior-history control quantifies the value of having history at all.

Reference patches, target test patches, fail/pass lists, evaluator logs, and target/future historical trajectories remain outside the actor filesystem, prompt, memory store, retrieval index, and analyst feedback used during generation. Installation metadata is not passed through wholesale: its targeted evaluator commands can disclose hidden test locations. History tool calls/results remain paired, and arbitrary upstream configuration metadata is not forwarded.

The benchmark's offline usefulness construction includes oracle-assisted selection. Published oracle experience is not treated as a deployable retrieval method. A learnability diagnostic may test admissible earlier history under a separately declared injection condition, but must never provide target reference patches or hidden tests to the solver. Selecting further tasks after observing treatment success would invalidate a held-out claim.

### 6.3 Registration, cadence, and development

The metadata reservation fixes repository partitions before new model inference. The first two development targets form an initial feasibility block; the remaining three retain their order. A complete runnable protocol must freeze prompts, adapters, model metadata, rates, history caps, arm order, budgets, and source hashes after all execution gates pass. At this draft that freeze has **not** occurred. There are zero new repository model trials.

Within a block, tasks run in the registered issue-ordinal sequence; arm order rotates deterministically to reduce consistent order effects. No started or uncertain model call is repeated. Preparation errors proven to occur before upstream inference can be amended with an explicit receipt. Timeouts and malformed outputs remain part of the assigned condition, with unknown cost retained where necessary. Infrastructure exclusions must precede outcome inspection and are reported without favorable replacement.

Prompt changes between completed development blocks are versioned. Validation on the reserved repository starts only after a candidate is frozen. Four validation tasks in one repository are a small transfer pilot, not adequate evidence of general coding superiority or population noninferiority. A larger study requires additional disjoint repository sequences and a separately powered analysis; existing unrelated held-out studies remain untouched.

### 6.4 Outcomes and analysis

The primary quality endpoint is verified resolution using the declared evaluator with both target and regression checks, after empty and reference controls pass. Public-test success is a mechanism signal, not a substitute for independent grading. Report successes lost and gained relative to the paired control, not only the pooled rate.

The economic endpoint is complete measured stream model cost and cost per verified resolution. If \(S_a\) tasks resolve under arm \(a\), then:

\[
CPR_a = \frac{C_{initialization,a}+\sum_t C_{preparation+retrieval+solver+integration+update,a,t}}{S_a}.
\]

When no task resolves, cost per resolution is undefined, not zero. Cumulative and marginal curves after each task expose whether initialization amortizes over actual observed reuse. Hypothetical future reuse is a sensitivity analysis, not an observed break-even result. Local runtime, storage, and service deployment costs are reported separately until a defensible monetary measurement exists.

Secondary outcomes include native/tool call counts, uncached/cached/output tokens, finite operation time, task elapsed time, repeated investigation, stale-memory use, contradiction correction, and retrieval-to-action provenance. Process/service lifetime is not agent-blocking runtime. An identical nonzero exit is only a candidate repetition; analysis must determine whether a recheck had a useful changed hypothesis or environment.

For inference about a wider task population, use paired outcome differences and uncertainty clustered by repository, with model sampling seeds/replications where supported. The five-task development panel and four-task validation panel warrant descriptive paired results, not a bootstrap with one repository masquerading as independent sampling. No confirmatory significance or noninferiority claim is planned from that sample. The project aspiration of substantial savings without observed quality loss remains a target, not a result this design guarantees.

### 6.5 Testing the mechanism

A useful-memory effect should exhibit a chain: an admissible prior experience is stored, retrieved, inspected or acted upon, and contributes to a distinct checked outcome. Tool receipts can show changed behavior; attribution labels must retain evidence and uncertainty. They cannot by themselves prove counterfactual causality. Matched arms supply the counterfactual outcome comparison.

Separately registered ablations should remove prior history, reset memory between targets, compare graph and flat snapshots, suppress updates, and introduce genuinely stale historical procedures where supported by the repository timeline. Randomly unrelated memory can test distraction, but must not replace the natural baseline or manufacture benchmark advantages. A negative result may mean the extraction policy failed, the solver did not use retrieved evidence, useful history was capped out, or the task required no transferable knowledge. These explanations need observable diagnostics rather than post-hoc favorable task selection.

## 7. Discussion

### 7.1 What the evidence currently supports

The completed studies support three limited conclusions. First, model choice for maintenance matters economically: Luna is much cheaper than Sol in the observed Smallville maintenance control. Second, memory can cost more than source retrieval or retained conversation even when every answer is correct. Third, numerical savings are not sufficient evidence of a mechanism: an intervention that never activates cannot explain its arm's apparent advantage without further investigation.

No completed result in this paper establishes that Mem0, Graphiti, Smallville, TokenEconomizer, native memory, or the proposed graph accelerates verified follow-up repository work. There is no local Mem0-versus-Graphiti coding ranking. Conversational recall claims from other papers do not fill that gap.

### 7.2 Why same-environment work is the relevant next test

The strongest opportunity is recurring, costly, task-relevant knowledge: a repository-specific test command, a dependency interaction, an architectural constraint, or a checked reason to avoid a tempting repair. The value should persist across distinct issues but remain revisable as the code changes. This setting makes accumulation measurable and gives stale knowledge a chance to fail visibly.

A benchmark where no treatment uses memory is a poor test of this hypothesis. Conversely, selecting only cases already helped by an oracle overstates ordinary deployment opportunity. VibeMemBench provides a useful screened testbed; a later unscreened repository stream is needed to estimate practical prevalence and average benefit.

### 7.3 Limits and threats to validity

All current local efficacy evidence is development evidence. The eight public coding functions are easy, reused across conditions, and vulnerable to training contamination. The recall corpora are generated and do not represent engineering work. Small samples with all-success outcomes cannot establish quality equivalence. The later maintenance-model control has order and cache confounds. Historical scenarios use frozen rates and exclude unpriced local infrastructure.

The new benchmark is public and could overlap model training data. Its history-usefulness screening and issue-number chronology limit external validity. Temporal ordering must not be claimed more strongly than the released metadata supports. Current infrastructure has not passed all repository, graph-backend, native-memory, and capture gates. A corrected environment may differ from the released image and must be labeled an adapted run, with evaluator and control equivalence tested.

Model-generated memory can preserve prompt injection, false causality, stale rules, and private information. Provenance, namespace checks, evidence retention, and fallible-memory instructions reduce some risks but do not establish semantic truth. No automated abstraction should be treated as verified solely because a model assigned high confidence.

Finally, this paper does not measure broader innovation. It studies productive reuse in software tasks. Claims about scientific or organizational innovation require additional outcomes and human or field evaluation.

## 8. Conclusions

Knowledge accumulation is a plausible way to reduce repeated work, but stored knowledge is not automatically useful knowledge, and useful recall is not automatically generalization. Our completed development experiments reveal maintenance overhead and cache sensitivity rather than a demonstrated acceleration of repository innovation. Cheap maintenance reduces one cost component; it does not guarantee a cheaper or better complete agent.

The next decisive comparison is repeated verified work in the same repository, with equal information access, actual native-memory controls, independently implemented existing systems, and a graph-versus-flat ablation. A cheap model should prepare a revisable problem representation; a stronger solver should use, challenge, and update it; every inference stage should be charged. The proposed representation earns support only if the resulting accumulated experience improves later verified work under those controls. The requested head-to-head remains pending, and this draft makes no claim that the hypothesis has been confirmed.

## References

1. Cohen, W. M., and Levinthal, D. A. (1990). *Absorptive Capacity: A New Perspective on Learning and Innovation.* Administrative Science Quarterly, 35(1), 128–152. [DOI](https://doi.org/10.2307/2393553).
2. Nonaka, I. (1994). *A Dynamic Theory of Organizational Knowledge Creation.* Organization Science, 5(1), 14–37. [DOI](https://doi.org/10.1287/orsc.5.1.14).
3. March, J. G. (1991). *Exploration and Exploitation in Organizational Learning.* Organization Science, 2(1), 71–87. [DOI](https://doi.org/10.1287/orsc.2.1.71).
4. Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS. [Paper](https://arxiv.org/abs/2005.11401).
5. Park, J. S., et al. (2023). *Generative Agents: Interactive Simulacra of Human Behavior.* UIST. [Paper](https://arxiv.org/abs/2304.03442).
6. Shinn, N., et al. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* [Paper](https://arxiv.org/abs/2303.11366).
7. Wang, G., et al. (2023). *Voyager: An Open-Ended Embodied Agent with Large Language Models.* [Paper](https://arxiv.org/abs/2305.16291).
8. Packer, C., et al. (2023). *MemGPT: Towards LLMs as Operating Systems.* [Paper](https://arxiv.org/abs/2310.08560).
9. Xu, W., et al. (2025). *A-MEM: Agentic Memory for LLM Agents.* NeurIPS. [Paper](https://arxiv.org/abs/2502.12110).
10. Chhikara, P., et al. (2025). *Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory.* [Paper](https://arxiv.org/abs/2504.19413); [source](https://github.com/mem0ai/mem0).
11. Rasmussen, P., et al. (2025). *Zep: A Temporal Knowledge Graph Architecture for Agent Memory.* [Paper](https://arxiv.org/abs/2501.13956); [Graphiti source](https://github.com/getzep/graphiti).
12. Edge, D., et al. (2024). *From Local to Global: A Graph RAG Approach to Query-Focused Summarization.* [Paper](https://arxiv.org/abs/2404.16130).
13. Li, A. J., et al. (2026). *TokenEconomizer: Experience-Driven Black-Box Cost Control for Coding Agents.* [Paper](https://arxiv.org/abs/2610.22732); [source](https://github.com/microsoft/TokenEconomizer).
14. Maharana, A., et al. (2024). *Evaluating Very Long-Term Conversational Memory of LLM Agents.* [Paper](https://arxiv.org/abs/2402.17753).
15. Wu, D., et al. (2024). *LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory.* ICLR 2025. [Paper](https://arxiv.org/abs/2410.10813).
16. Jimenez, C. E., et al. (2023). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR 2024. [Paper](https://arxiv.org/abs/2310.06770).
17. OpenAI (2024). *Introducing SWE-bench Verified.* [Release and evaluation description](https://openai.com/index/introducing-swe-bench-verified/).
18. Joshi, T., Chowdhury, S., and Uysal, F. (2025). *SWE-Bench-CL: Continual Learning for Coding Agents.* [Paper](https://arxiv.org/abs/2507.00014); [author-linked source](https://github.com/thomasjoshi/agents-never-forget).
19. Fan, L., et al. (2026). *VibeMemBench: Evaluating Memory Systems for Coding Agents on Real Repository Coding Tasks.* [Paper](https://arxiv.org/abs/2609.23570); [pinned integration contract](https://github.com/AlibabaResearch/DAMO-ConvAI/blob/7152cf96809b45343ccc1caf7115a7d3fa43f956/VibeMemBench/scripts/CONTRACT.md); [dataset](https://huggingface.co/datasets/Tongyi-ConvAI/VibeMemBench/tree/11164976b4f920cdb0d0cd570ca572e49acea1e8).
20. OpenAI (accessed 9 November 2026). *Memories.* [Documentation](https://learn.chatgpt.com/docs/customization/memories). Source-inspection snapshot: [Codex memory startup](https://github.com/openai/codex/blob/0598a96e9361485fd4cd02f9c287aca627ad6ee1/codex-rs/memories/write/src/start.rs). Snapshot inspection is not proof that an installed binary implements every current-source detail.
21. Python Software Foundation (2026). *Python 3.10.20 security release.* [Release notes](https://www.python.org/downloads/release/python-31020/).

## Appendix A. Reproducibility and evidence availability

Completed results are machine-readable and versioned:

* [Native coding/maintenance accounting](../../../tools/usage-monitor/studies/luna-memory-tokeneconomizer-final-results-001.json).
* [Repeated recall/cache comparison](../../../tools/usage-monitor/studies/cache-memory-reuse-results-001.json).
* [Repository metadata audit and reservation](../../../tools/usage-monitor/studies/repository-memory-metadata-audit-001.json).
* [Prospective repository-memory protocol and execution gates](../../../tools/usage-monitor/studies/repository-memory-protocol-001.json).
* [First image's static security preflight](../../../tools/usage-monitor/studies/repository-memory-image-preflight-001.json).
* [Current source/license status and exact-package advisory recheck](../../../tools/usage-monitor/studies/repository-memory-source-audit-001.json).

Private source captures, native logs, dataset grading material, and security artifacts remain in ignored `work/security/` directories; they are not republished in this paper. Public receipts do not constitute independently audited security clearance. The new metadata audit invokes no models. Native/global agent configuration, personal memory, running observability services, and paused research schedules remain unchanged.

The manuscript must be revised after the registered longitudinal experiment. Missing results must remain missing until measurements exist; literature results, software checks, metadata counts, and prospective methods must not be substituted for that experiment.
