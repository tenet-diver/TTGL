# Context and memory optimization: experiment progress

Updated: 7 November 2026 (UTC). Owner: active Codex chat. Research schedules remain paused.

The user authorized local authenticated Codex experiments without a spend/runtime
ceiling and publication in the TTGL repository. This is an ongoing research program,
not a claim that memory improves quality or that an optimal system already exists.
Each live block still has a frozen allocation, failure policy and complete accounting.

## Experiment register

| Experiment | Description / comparison | Status | Results / next gate |
|---|---|---|---|
| progress-replay-001 | First progress-output filtering trial | Complete; preserved | Failed trial; never replace with the revised result. See subsequent report. |
| progress-replay-002 | Revised progress representation versus raw evidence on three matched log investigations | Complete | 45.58% fewer native tokens; all six checks pass. Reused development cases, not coding-task/general savings. [Report](../../tools/usage-monitor/studies/progress-replay-results-002.md). |
| live-harness-001 | Actual code edits/tests with raw versus reviewed Headroom lossless subset | Complete | Four runs, two generated tasks; 10.075% fewer pooled native tokens, all checks pass, no observed speedup. [Report](../../tools/usage-monitor/studies/live-harness-results-001.md). Later recovery made capture/compression opt-in; older default-installation claims are historical. |
| retrieval-guidance-001 | Neutral versus generic discover-then-read instruction | Complete; rejected | Six source investigations pass; candidate uses 11.78% more tokens, only 1/3 pair wins. [Report](../../tools/usage-monitor/studies/harness-optimization-backlog.md). |
| output-audit-001 | Retrospective coverage of existing deterministic transforms | Complete; offline | 6/413 distinct retained outputs changed; byte reductions are not model-token savings. |
| independent-read-batching-001 | Neutral versus batching genuinely independent source reads | Complete; development gate passed | All six checks pass; 308,046 → 265,627 native tokens (13.7703% reduction), 2/3 pair wins. No global adoption or coding-quality claim. Published in TTGL Experiments; six-session Langfuse audit passes. [Protocol](../../tools/usage-monitor/studies/independent-read-batching-protocol-001.json). |
| analyst-context-memory-001 | Existing Codex analyst reviews scoped real evidence for capture gaps and experiment opportunities | Complete; published in TTGL | 74 tool events annotated; parent/child runtime overlap, workspace-root mistakes and selective evidence retrieval identified. Analyst overhead: 178,274 native tokens; proposals are not measured savings. |
| telemetry-readiness-001 | Audit TTGL/Langfuse usage, IDs, capture coverage and immutable receipts | Batching block passes; ongoing per block | All six sessions reconcile exactly between CLI, unique native generations and Langfuse v2 observation IDs/usage (573,673 total native tokens). Old trace/session API routes return404; use v2 with explicit usage fields. No observations re-ingested. |
| observation-masking | Remove older observations with exact recovery | Planned; mechanism gate required | Earlier prototype gate failed; offline oracle results do not prove a live intervention. Preserve protected instructions/tool pairing. |
| headroom-transfer | Fresh varied coding/long-context tasks, raw versus existing reviewed lossless subset | Planned | Verify live route and cache accounting first; do not rerun/replace live-harness-001. Full old Headroom image remains blocked. |
| reversible-retrieval | Exact content archive, compact handles and agent-selected recovery | Planned | Test round-trip, freshness, namespace isolation and actual model recovery; count retrieval overhead. |
| hierarchical-context | Exact archive plus summary hierarchy versus native compaction | Planned | Require actual whole-history control, protected-fact checks and separately metered summary inference. Unsupported rewriting is not a completed comparison. |
| chronological-memory-001 / corrected 002 | Fresh-session no memory, full prior history, bounded SQLite FTS retrieval, agent-written notes | 001 configuration failure preserved; 002 complete | First CLI rejected reserved built-in provider override before model invocation. New registered002 removes it and uses native transport defaults; 24 processes across two three-stage generated coding sequences. All six empty controls fail as expected and all six reference/independent controls pass. Three FTS contract tests pass. [Protocol](../../tools/usage-monitor/studies/chronological-memory-protocol-001.json). Unrelated/stale controls and fresh long-horizon benchmarks remain separate pending work. |
| mem0-memory | Pinned stock self-hosted Mem0 versus no memory and raw-history retrieval | Dependency review | Mem0 2.2.1 + FastEmbed 0.9.1: 50 exact packages, 50/50 OSV queries with no matches, 50 wheel hashes checked; no .pth or installer scripts. Installed only in private experiment target under Codespace incomplete-evidence allowance; not security-cleared. Pinned MIT ONNX embedder loads offline and returns384 dimensions. One local-Codex extraction completed (32,935 native tokens); two facts persisted/retrieved and tenant isolation passed. API search failure preserved and corrected through reads only. Optional NLP/BM25 unavailable in this configuration; not full-feature/default hosted Mem0. |
| letta-memory | Maintained stateful-agent alternative | Discovery | Pin actual runtime and distinguish replacing the agent from changing its memory. Verify current license, dependencies and inference compatibility. |
| graphiti-memory | Temporal graph memory versus flat retrieval of the same corpus | Discovery | Inspect maintained integration, backend requirements, license and complete dependency graph; count extraction/embedding/ranking. |
| principles-and-stage | Evidence-backed principles and stage-aware retrieval, each ablated | Planned | Same frozen episodes and equal retrieval budget; stale/contradictory/irrelevant memory controls; no hidden grader information. |
| repository-map | Maintained Aider map versus normal retrieval | Dependency review | Current metadata candidate 0.86.2; complete graph and runtime review pending. Preserve prior 0.86.0 discovery as historical. |
| learned-compression | LLMLingua versus deterministic/raw documentation context | Dependency review | Candidate 0.2.2; model-weight/runtime security, license and factual guards pending. Count compressor compute/inference. |
| local-selection | Lightweight local ranking/summary substitution | Planned | No model install before review; compare exact same pipeline and include local loading/runtime costs. |
| cache-aware-layout | Stable prefix/compaction timing with same semantic information | Planned | Measured fresh/cached/output buckets; no cash/quota inference. Shorter context can increase rate-weighted cost. |
| verification-selection | Focused initial tests with mandatory full final verification | Planned | Three fresh paired repair tasks; independent final checks in every arm. |
| rtk-output | Maintained output filtering | Security blocked | Prior pinned release has confirmed dependency advisories; no install/execute. A patched candidate needs a new review. |
| longmemeval-local-codex-development-001 | Full-history vs ordinary file-search vs exact FTS excerpts vs adapted Mem0-dense, all with identical raw files | Running |8 development questions spanning all6 types;72 registered model processes including8 memory extractions and32 blinded judges. Primary criterion is total cost with retained matched successes. Each history is about503–520k characters.24 held-out cases reserved and untouched. [Protocol](../../tools/usage-monitor/studies/longmemeval-codex-protocol-001.json). |
| public-benchmark-screen | Screen SWE-bench and Terminal-Bench for long-horizon/context and memory tracks | In progress; no model runs | Pin dataset/harness/resources, audit empty/reference controls and image security; separate official score from chronological memory extensions. Exclude all reserved routing validation families. |
| heldout-context-memory | Frozen selected configurations on fresh tasks | Planned; untouched | Register selection rule, noninferiority margin, sample size and paired uncertainty before exposure; no tuning/stopping on held-out results. |
| scientific-report | Detailed methods, all results/failures, uncertainty, costs and reproduction artifacts | Planned; repository publication | Publish Markdown plus self-contained HTML when results exist. No external journal/arXiv submission requested. State best among tested configurations, not universal optimality. |

## Measurement and fairness rules

- Primary for subsequent blocks: independently verified task success and **total
  rate-weighted model inference cost**, including memory creation/retrieval/integration.
  Report input, cached-input subset, fresh input, writes where observable, output and
  cache-hit ratio separately. Fewer tokens can cost more. Original token-only gates
  stay frozen; the added cost analysis is explicitly post hoc for completed blocks.
- Memory track: include episode extraction, summaries, embeddings, indexing,
  retrieval/ranking, retries, integration and recovery. Report cold-start totals and
  amortized curves separately. Unknown usage remains null, never zero.
- Separate long within-session tasks from chronological cross-session reuse.
  Match personal context and current repository state. Keep future tasks, reference
  patches, hidden tests and grader commentary out of memory ingestion.
- Use immutable attempts and frozen protocols; zero automatic process retries;
  ambiguous started calls stop that block for inspection. Retain expensive failures.
- Record process wall time, finite native tool runtime and service lifetime separately.
  Native token reductions are neither subscription cash nor quota savings.
- Reuse TTGL's native reader and Langfuse deployment. Do not sum daily and session
  usage datasets or duplicate transcript/proxy counters. Raw private evidence stays
  under ignored `work/security/context-memory-20261107/`.
- Known dependency vulnerabilities still block the affected candidate. In this
  Codespace incomplete evidence alone does not constitute a security clearance or
  prevent already-authorized execution; disclose it rather than fabricate a pass.

## Current activity and next actions

1. Completed: batching, analyst review,24 chronological cells and exact Langfuse audits.
2. Complete the Mem0 configuration gates and register the harder memory comparison.
3. Use cost as the primary efficiency metric: preserve the token-only gates already
   run, but apply the dated cost amendment before any new inference.
4. Audit actual transform/capture application, then freeze fresh context/long-horizon
   blocks and separate held-out evaluation.
5. Publish every block, failure, cost/cache breakdown and uncertainty here and in
   the scientific manuscript. Existing routing validation remains untouched.

## Activity log

- 7 November: audited existing plans, historical trials, local login and active
  processes. No pre-existing model trial worker found. Preserved nine pre-existing
  modified source/report files. Registered batching-001 before model inference.
- 7 November: local Codex 0.167.0 reports supported ChatGPT login. TTGL/Langfuse
  HTTP checks pass. Mem0 metadata resolution used pip `--dry-run --only-binary`;
  no downloaded package code or installation scripts were executed.

Source specifications: [ten-idea experiment description](../handoffs/codex-context-experiments/EXPERIMENT_DESCRIPTION.md),
[existing queue](../../tools/usage-monitor/studies/harness-optimization-backlog.md),
[security policy](../security/dependency-security-policy.md).

- 7 November: batching-001 completed all six registered attempts; native generation counters reconcile exactly with CLI counters. All exact source checks pass, including the losing pair. Analyst-001 is running on the prior harness project; no repeat analyst launched.

- 7 November: chronological-memory-001 frozen and started after six empty/reference pairs and independent reference checks pass. Agents see only current tasks, their own earlier visible episodes and evolving code; operator checks are excluded from memory. No held-out or official benchmark result yet.

- 7 November: analyst-001 published with 178,274 native tokens separately metered. chronological001 stopped on an explicit configuration-loader rejection before model invocation; archived exact runner/error and registered002 before corrected execution. No uncertain/model attempt was repeated.

- 7 November: Langfuse v2 read-only audit verifies all six batching sessions, exact unique generation IDs and all cached/fresh/output/total counters. Legacy read404 receipts retained. Added reusable audit/publisher using existing native rows, without duplicating measured usage.
- 7 November: installed isolated Mem0/FastEmbed candidate after dated receipt; all50 exact OSV queries had no matches and wheel hashes match. Recorded incomplete OS/native/provenance evidence under explicit Codespace allowance. Downloaded pinned MIT ONNX model as data only; local embedding runtime check completed (3 local model inferences, no Codex LLM calls).


<!-- current-block-snapshot:start -->
## Current filesystem snapshot

Updated 2026-11-07T16:00:39.808330+00:00. Partial checks are provisional; final usage requires reconciliation.

| Block | Status | Started processes | Graded cells | Passing cells |
|---|---|---:|---:|---:|
| batching-001 | Complete; native counters reconciled | 6 | 6 | 6 |
| chronological-001 | Stopped; preserved preparation failure | 1 | 0 | 0 |
| chronological-002 | Complete; native counters reconciled | 24 | 24 | 24 |

Started processes include preserved configuration failures. Missing grades/usage are unknown. This reader does not launch work or alter frozen study sources.
<!-- current-block-snapshot:end -->

- 7 November: chronological002 complete: all24 task checks pass and all24 sessions reconcile exactly with Langfuse unique generation IDs and usage. Total native tokens: none656,584; raw history541,910 (17.4652% fewer); FTS650,196 (0.9729% fewer); notes652,908 (0.5599% fewer). Raw history wins both generated sequences and passes the development nomination gate. FTS was never queried (0calls), so no retrieval efficacy claim. Single replicates and differing stage-one usage limit causal interpretation; no held-out/noninferiority/optimality claim.

- 7 November: published initial scientific-format manuscript at [docs/paper/context-memory/report.md](../paper/context-memory/report.md). It explicitly analyzes stage-one variation before memory exposure, zero FTS use, integration failures and research expense. At15:56:53UTC this active cycle has13,911,128 accrued native tokens (lower bound), with local embedding inferences separate; no net/cash saving claim.
- 7 November: next supplemental memory track selected for preparation: pinned MIT LongMemEval-S, native local-Codex reader/judge adaptation with full-history and file-search controls. No benchmark inference yet. LongMemEval-V2 full distribution is about7.12GB including screenshots, larger than available disk; no full download or image omission presented as an official result. Coding/terminal long-horizon track still pending.

## Cost-aware steering and completed-block audit

User steering on7 November explicitly prioritizes total cost: fewer tokens can
lose cache reuse and cost more. [Verified rate scenarios](../../tools/usage-monitor/studies/context-memory-pricing-20261107.json)
use per-response native counters; actual account credits/quota and cash remain unknown.
The added audit is post hoc and does not rewrite completed registered token gates.

| Block/arm | Native token change | Codex Standard credit-rate scenario | Cost change vs matched control |
|---|---:|---:|---:|
| Batching neutral | Reference |3.20342 credits|Reference|
| Batching candidate |−13.7703%|2.66323 credits|−16.8629%|
| Chronological none |Reference|7.12388 credits|Reference|
| Raw history |−17.4652%|6.89342 credits|−3.2350%|
| FTS availability |−0.9729%|7.16256 credits|+0.5430%|
| Agent notes |−0.5599%|7.12636 credits|+0.0348%|

Raw-history cache-hit ratio falls from86.3244% to81.9619%, and fresh input rises
89,101→97,074 tokens. It passes only the original token nomination gate; it does
**not** meet a10%cost-reduction gate. No memory configuration is selected as the
optimum. FTS has0actual retrievals. Future selection includes all memory-system
inference and quality retention, with cache-price and context-length sensitivity.
Both cost audits are also attached as separate evaluations in TTGL Experiments.

- 7 November: user cost steering implemented through response-level primary Codex credit scenarios, cache break-even/sensitivity and separate API pricing;3 new accounting tests pass. The original token-only gates remain frozen.
- 7 November: LongMemEval-S data pinned/hash checked as JSON-only MIT data; no dataset scripts run. Outcome-independent stratified reservation002 covers all6 types, excludes shared answer-support sessions and sibling ID families. Three label-boundary/rubric tests pass; eight history schema checks pass. Registered72-process development block started;24 validation questions remain reserved. No official-score or coding-quality claim.
