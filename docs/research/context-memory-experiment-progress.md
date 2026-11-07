# Context and memory optimization: experiment progress

Updated: 7 November 2026 (UTC). Owner: active Codex chat. Research schedules remain paused.

The user authorized local authenticated Codex experiments without a spend/runtime
ceiling and publication in the TTGL repository. This is an ongoing research program,
not a claim that memory improves quality or that an optimal system already exists.
Each live block still has a frozen allocation, failure policy and complete accounting.

## Experiment register

| Experiment | Description / comparison | Status | Results / next gate |
| --- | --- | --- | --- |
| progress-replay-001 | First progress-output filtering trial | Complete; preserved | Failed trial; never replace with the revised result. See subsequent report. |
| progress-replay-002 | Revised progress representation versus raw evidence on three matched log investigations | Complete | 45.58% fewer native tokens; all six checks pass. Reused development cases, not coding-task/general savings. [Report](../../tools/usage-monitor/studies/progress-replay-results-002.md). |
| live-harness-001 | Actual code edits/tests with raw versus reviewed Headroom lossless subset | Complete | Four runs, two generated tasks; 10.075% fewer pooled native tokens, all checks pass, no observed speedup. [Report](../../tools/usage-monitor/studies/live-harness-results-001.md). Later recovery made capture/compression opt-in; older default-installation claims are historical. |
| retrieval-guidance-001 | Neutral versus generic discover-then-read instruction | Complete; rejected | Six source investigations pass; candidate uses 11.78% more tokens, only 1/3 pair wins. [Report](../../tools/usage-monitor/studies/harness-optimization-backlog.md). |
| output-audit-001 | Retrospective coverage of existing deterministic transforms | Complete; offline | 6/413 distinct retained outputs changed; byte reductions are not model-token savings. |
| independent-read-batching-001 | Neutral versus batching genuinely independent source reads | Complete; development gate passed | All six checks pass; 308,046 → 265,627 native tokens (13.7703% reduction), 2/3 pair wins. No global adoption or coding-quality claim. Published in TTGL Experiments; six-session Langfuse audit passes. [Protocol](../../tools/usage-monitor/studies/independent-read-batching-protocol-001.json). |
| analyst-context-memory-001 | Existing Codex analyst reviews scoped real evidence for capture gaps and experiment opportunities | Complete; published in TTGL | 74 tool events annotated; parent/child runtime overlap, workspace-root mistakes and selective evidence retrieval identified. Analyst overhead: 178,274 native tokens; proposals are not measured savings. |
| telemetry-readiness-001 | Audit TTGL/Langfuse usage, IDs, capture coverage and immutable receipts | Batching block passes; ongoing per block | All six sessions reconcile exactly between CLI, unique native generations and Langfuse v2 observation IDs/usage (573,673 total native tokens). Old trace/session API routes return404; use v2 with explicit usage fields. No observations re-ingested. |
| observation-masking | Remove older observations with exact recovery | Offline tested; native age gate prepared |8 policy/persistence and4 proxy/CLI contracts pass. Older-shell-mask keeps the newest four; registered two-call native age gate awaits current reuse completion. Actual input reduction and recovery are required, not byte changes. |
| headroom-transfer | Fresh varied coding/long-context tasks, raw versus existing reviewed lossless subset | Planned | Verify live route and cache accounting first; do not rerun/replace live-harness-001. Full old Headroom image remains blocked. |
| reversible-retrieval | Exact content archive, compact handles and agent-selected recovery | Native005 clean mechanism gate passes |001–003 UNAPPLIED,004 requires a repaired recovery command; all preserved.005 actually transforms and recovers exact source through one successful CLI call. Five canaries reconcile native/CLI/Langfuse; mechanism expense, no coding/cost saving claim. |
| hierarchical-context | Exact archive plus summary hierarchy versus native compaction | Planned | Require actual whole-history control, protected-fact checks and separately metered summary inference. Unsupported rewriting is not a completed comparison. |
| chronological-memory-001 / corrected 002 | Fresh-session no memory, full prior history, bounded SQLite FTS retrieval, agent-written notes | 001 configuration failure preserved; 002 complete | First CLI rejected reserved built-in provider override before model invocation. New registered002 removes it and uses native transport defaults; 24 processes across two three-stage generated coding sequences. All six empty controls fail as expected and all six reference/independent controls pass. Three FTS contract tests pass. [Protocol](../../tools/usage-monitor/studies/chronological-memory-protocol-001.json). Unrelated/stale controls and fresh long-horizon benchmarks remain separate pending work. |
| mem0-memory | Pinned stock self-hosted Mem0 versus no memory and raw-history retrieval | Adapted dense development comparison complete | Mem0 2.2.1 + FastEmbed 0.9.1: 50 exact packages, 50/50 OSV queries with no matches, 50 wheel hashes checked; no .pth or installer scripts. Installed only in private experiment target under Codespace incomplete-evidence allowance; not security-cleared. Pinned MIT ONNX embedder loads offline and returns384 dimensions. One local-Codex extraction completed (32,935 native tokens); two facts persisted/retrieved and tenant isolation passed. API search failure preserved and corrected through reads only. Optional NLP/BM25 unavailable in this configuration; not full-feature/default hosted Mem0. Completed long-history002 scores7/7 local checks but cold-start deployment scenario cost88.18% above full history; no cost-gate nomination. |
| letta-memory | Maintained stateful-agent alternative | Discovery | Pin actual runtime and distinguish replacing the agent from changing its memory. Verify current license, dependencies and inference compatibility. |
| graphiti-memory | Temporal graph memory versus flat retrieval of the same corpus | Discovery | Inspect maintained integration, backend requirements, license and complete dependency graph; count extraction/embedding/ranking. |
| mcp-graph-memory-mechanism | Maintained server-memory2.1.0 with an isolated JSONL knowledge graph, no vector DB or model calls | Probe003 passes; efficacy pending | 4 exact packages have no OSV matches; hashes/provenance and mixed Apache/MIT transition recorded.7 protocol/persistence checks pass, including observations/relations and restart. Earlier test-client parser/schema failures001/002 preserved. No global Codex integration or memory-quality result. |
| principles-and-stage | Evidence-backed principles and stage-aware retrieval, each ablated | Planned | Same frozen episodes and equal retrieval budget; stale/contradictory/irrelevant memory controls; no hidden grader information. |
| repository-map | Maintained Aider map versus normal retrieval | Dependency review | Current metadata candidate 0.86.2; complete graph and runtime review pending. Preserve prior 0.86.0 discovery as historical. |
| learned-compression | LLMLingua versus deterministic/raw documentation context | Dependency review | Candidate 0.2.2; model-weight/runtime security, license and factual guards pending. Count compressor compute/inference. |
| local-selection | Lightweight local ranking/summary substitution | Planned | No model install before review; compare exact same pipeline and include local loading/runtime costs. |
| cache-aware-layout | Continued native thread versus stable/changing prefixes, files, FTS and reused Mem0 | Registered reuse001 running |3 corpus sizes ×4 actual questions ×6 arms;75 process maximum includes3 extractions. Native turn allocator validated with actual resumed calls. No partial cost/quality conclusion. |
| verification-selection | Focused initial tests with mandatory full final verification | Planned | Three fresh paired repair tasks; independent final checks in every arm. |
| rtk-output | Maintained output filtering | Security blocked | Prior pinned release has confirmed dependency advisories; no install/execute. A patched candidate needs a new review. |
| longmemeval-local-codex-development-001 | Full-history vs ordinary file-search vs exact FTS excerpts vs adapted Mem0-dense, all with identical raw files | Stopped; failure preserved | 3 readers completed, first memory extraction timed out at300 seconds;0 grades. Extraction usage/cost unknown, not zero. No calls repeated. Original eight cases span all 6 types; first case excluded from continuation without replacement. Each history is about503–520k characters.24 held-out cases reserved and untouched. [Protocol](../../tools/usage-monitor/studies/longmemeval-codex-protocol-001.json). |
| longmemeval-local-codex-development-002 | Same prompts/model and remaining7 originally unstarted cases; memory-extraction timeout1800 seconds | Complete; audited |63 processes,28/28 local rubric passes; all native/CLI/Langfuse usage and IDs reconcile. FTS nominee:82.80% lower scenario cost vs full history,17.15% vs plain search. All extraction counted. No first-case retry/replacement or all-six-type completed claim. [Protocol](../../tools/usage-monitor/studies/longmemeval-codex-protocol-002.json). |
| public-benchmark-screen | Screen SWE-bench and Terminal-Bench for long-horizon/context and memory tracks | In progress; no model runs | Pin dataset/harness/resources, audit empty/reference controls and image security; separate official score from chronological memory extensions. Exclude all reserved routing validation families. |
| heldout-context-memory | Frozen FTS versus plain file search/full history on24 reserved LongMemEval cases | Complete; FTS rejected |144 lineage calls reconcile CLI/native/Langfuse. Original grades full24/files24/FTS23; neutral audit72 calls reconciles and yields24/24/22. FTS costs25.32% less than files but fails frozen no-loss gate under both label sets.61 completed readers reused without repeat after parser repair. |
| scientific-report | Detailed methods, all results/failures, uncertainty, costs and reproduction artifacts | Living scientific-format Markdown published; final pending | Publish Markdown plus self-contained HTML when results exist. No external journal/arXiv submission requested. State best among tested configurations, not universal optimality. |

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
- 7 November: installed isolated Mem0/FastEmbed candidate after dated receipt; all 50 exact OSV queries had no matches and wheel hashes match. Recorded incomplete OS/native/provenance evidence under explicit Codespace allowance. Downloaded pinned MIT ONNX model as data only; local embedding runtime check completed (3 local model inferences, no Codex LLM calls).


<!-- current-block-snapshot:start -->
## Current filesystem snapshot

Updated 2026-11-07T21:40:50.171189+00:00. Partial checks are provisional; final usage requires reconciliation.

| Block | Status | Started processes | Graded cells | Passing cells |
|---|---|---:|---:|---:|
| batching-001 | Complete; native counters reconciled | 6 | 6 | 6 |
| chronological-001 | Stopped; preserved preparation failure | 1 | 0 | 0 |
| chronological-002 | Complete; native counters reconciled | 24 | 24 | 24 |
| longmemeval-001 | Stopped; inspect preserved evidence | 4/72 | 0/32 | 0 |
| longmemeval-002 | Complete; reconciled | 63/63 | 28/28 | 28 |
| longmemeval-validation-001 | Stopped; inspect preserved evidence | 0/144 | 0/72 | 0 |
| longmemeval-validation-002 | Stopped; inspect preserved evidence | 61/144 | 0/72 | 0 |
| longmemeval-validation-003 | Complete; reconciled;61 completed reader calls reused, never repeated | 83/83 | 72/72 | 71 |
| longmemeval-neutral-judge-audit-002 | Complete; reconciled | 72/72 | 72/72 | 70 |
| cache-memory-reuse-001 | Complete; reconciled | 75/75 | 72/72 | 72 |
| memory-storage-ablation-001 | Running; includes extraction and local stores | 26/75 (24 readers completed) | 0/72 | 0 |
| coding-context-transfer-001 | Complete; reconciled | 12/12 (12 completed) | 12/12 | 12 |

Started processes include preserved configuration failures. Missing grades/usage are unknown. This reader does not launch work or alter frozen study sources.
<!-- current-block-snapshot:end -->

- 7 November: chronological002 complete: all 24 task checks pass and all 24 sessions reconcile exactly with Langfuse unique generation IDs and usage. Total native tokens: none 656,584; raw history 541,910 (17.4652% fewer); FTS 650,196 (0.9729% fewer); notes 652,908 (0.5599% fewer). Raw history wins both generated sequences and passes the development nomination gate. FTS was never queried (0calls), so no retrieval efficacy claim. Single replicates and differing stage-one usage limit causal interpretation; no held-out/noninferiority/optimality claim.

- 7 November: published initial scientific-format manuscript at [docs/paper/context-memory/report.md](../paper/context-memory/report.md). It explicitly analyzes stage-one variation before memory exposure, zero FTS use, integration failures and research expense. At15:56:53UTC this active cycle has13,911,128 accrued native tokens (lower bound), with local embedding inferences separate; no net/cash saving claim.
- 7 November: next supplemental memory track selected for preparation: pinned MIT LongMemEval-S, native local-Codex reader/judge adaptation with full-history and file-search controls. No benchmark inference yet. LongMemEval-V2 full distribution is about7.12GB including screenshots, larger than available disk; no full download or image omission presented as an official result. Coding/terminal long-horizon track still pending.

## Cost-aware steering and completed-block audit

User steering on 7 November explicitly prioritizes total cost: fewer tokens can
lose cache reuse and cost more. [Verified rate scenarios](../../tools/usage-monitor/studies/context-memory-pricing-20261107.json)
use per-response native counters; actual account credits/quota and cash remain unknown.
The added audit is post hoc and does not rewrite completed registered token gates.

| Block/arm | Native token change | Codex Standard credit-rate scenario | Cost change vs matched control |
| --- | ---: | ---: | ---: |
| Batching neutral | Reference | 3.20342 credits | Reference |
| Batching candidate | −13.7703% | 2.66323 credits | −16.8629% |
| Chronological none | Reference | 7.12388 credits | Reference |
| Raw history | −17.4652% | 6.89342 credits | −3.2350% |
| FTS availability | −0.9729% | 7.16256 credits | +0.5430% |
| Agent notes | −0.5599% | 7.12636 credits | +0.0348% |

Raw-history cache-hit ratio falls from86.3244% to81.9619%, and fresh input rises
89,101→97,074 tokens. It passes only the original token nomination gate; it does
**not** meet a10% cost-reduction gate. No memory configuration is selected as the
optimum. FTS has0actual retrievals. Future selection includes all memory-system
inference and quality retention, with cache-price and context-length sensitivity.
Both cost audits are also attached as separate evaluations in TTGL Experiments.

- 7 November: user cost steering implemented through response-level primary Codex credit scenarios, cache break-even/sensitivity and separate API pricing;3 new accounting tests pass. The original token-only gates remain frozen.
- 7 November: LongMemEval-S data pinned/hash checked as JSON-only MIT data; no dataset scripts run. Outcome-independent stratified reservation002 covers all 6 types, excludes shared answer-support sessions and sibling ID families. Three label-boundary/rubric tests pass; eight history schema checks pass. Registered72-process development block started;24 validation questions remain reserved. No official-score or coding-quality claim.

- 7 November: LME001 stopped on first Mem0 extraction timeout300s after3 completed readers. Failed thread has no completed native response counters; usage/cost remains null. Exact failure/source/partial readers retained. New LME002 registered on only the seven originally unstarted cases, longer1800s extraction timeout,63 process cap; first case excluded without replacement. Frozen prompts/models unchanged;24 held-out cases untouched.
- 7 November: existing TTGL subscription collector queried supported per-thread backend estimates for all 6 batching sessions without inference. Backend returned unavailable for every selected thread; actual credits/USD remain null. No account-wide query or inference inferred from missing estimates.

- 7 November: LME002 first long-history extraction completed in 422.939 s, with 238 stored facts; ingestion 464.326 s and retrieval 0.192 s. Native extraction144,291input (12,288cached) +20,685output tokens,11.80212 published scenario credits. These are component measurements, not accuracy/economic conclusions. Stock engine returned 20 hits when limit 10 was requested; actual context/cost retained without mid-run changes.
- 7 November: maintained MCP graph server probe003 passes 7 mechanism/persistence checks with 0 model calls. Two explicit test-client failures remain preserved (multi-text JSON parsing and wrong add-observations argument). Probe003 durably journals each request/response before interpretation, including errors/notices. Security receipt records incomplete evidence and source Apache/MIT licensing transition; no security or efficacy claim.

- 7 November: added only missing archive/history-age policy glue after inspecting maintained Headroom helpers.4 offline contracts pass; recent outputs and instruction/tool metadata preserved, exact recovery contract, partial-write fail-open and raw bypass checked. Stable handles retain prefix equality; aging changes earlier presentation at the boundary. No live deployment, actual cache behavior or efficacy claim. Normal provider/source routes unchanged.

## Completed long-history development block002: cost-aware result

All63 registered processes completed (28 readers,7 memory extractions,28 blinded
judges). All28 reader answers passed the local rubric. Native/CLI counters and
all63 Langfuse session generation identities/counters reconcile exactly.

| Strategy | Correct /7 | Native tokens including extraction | Cached input / input | Published Codex credit-rate scenario | Cost change vs full history |
|---|---:|---:|---:|---:|---:|
| Full history |7|956,509|9.72%|43.47417|reference|
| Plain file search |7|596,083|74.51%|9.02639|−79.24%|
| Exact FTS excerpts plus raw fallback |7|439,966|70.39%|7.47870|−82.80%|
| Adapted Mem0 dense plus raw fallback |7|1,545,363|24.82%|81.80931|+88.18%|

FTS wins all7 paired costs against full history and is the development nominee
under the frozen cost/quality rule; plain file search also qualifies. FTS costs
17.15% less than the stronger plain-file control in aggregate. This is **not** a
held-out result, coding-task result, official LongMemEval score or demonstrated
subscription cash saving. Same-model rubric grading, seven cases across five
types and cold-start memories limit interpretation. Local embedding monetary
cost remains unknown. No query-reuse amortization was measured. The failed001
extraction remains unknown and is not silently zeroed.24 held-out cases remain
untouched pending separately registered frozen validation.

[Aggregate source](../../tools/usage-monitor/studies/longmemeval-codex-development-results-002.json).
The archive integration now passes8 offline policy/persistence checks, including
actual existing MCP source retrieval; no live cache/efficacy claim follows.

- Validation registration: freeze exact FTS nominee against plain file search and
  full history on the24 previously reserved cases,144 processes including judges.
  Primary added-value control is plain search. Require every matched baseline
  success retained, >=10% pooled scenario-cost reduction and >=13/24 paired cost
  wins against each control; otherwise report failure without tuning/replacement.
  First preparation ended before preflight/model invocation; a full-JSON parse
  diagnostic exited143, cause unknown. Preserve that preparation. Validation002
  uses bounded stdlib JSON iteration (3 contract checks) without changing records,
  prompts, allocation or scoring. No validation model calls repeated.

- Long-history002 now appears in TTGL Experiments with distinct reader, extraction
  and evaluation roles; publication links existing unique responses without
  inserting duplicate usage. Research accounting snapshot17:43:20UTC records
  50,808,716 known native tokens /434 unique responses and383.578 published-rate
  scenario credits across supervision, trials and analysis. This is an accrued
  lower bound, not savings or cash expense; the timed-out001 extraction has
  unknown usage/cost, parent implementation continues, and local compute is not
  monetized. Snapshot totals must not be added together.

- Cache-price sensitivity added for completed LME002, holding observed cache
  behavior fixed over cached/fresh price ratios0,0.01,0.05,0.1,0.25,1. FTS remains
  cheaper than both controls throughout this scenario sweep. API sensitivity
  applies long-context thresholds per response, never whole-task totals; no
  response crosses272k input here. This is not recreated provider cache behavior.
  Three role-aware accounting tests pass.
- Experimental archive route passes2 actual HTTP contracts (explicit opt-in,
  model-visible recovery guard, exact persisted source and raw bypass), plus5
  existing proxy checks. A teardown journal race in the test was corrected and
  rerun cleanly. Normal running8317 remains unchanged.
- Live archive canary001 FAILED its mechanism gate: no advertised recovery-tool
  declarations in actual requests, so zero transformations and zero retrievals;
  model reports UNAPPLIED.47,051input (31,744cached)+65output tokens,0.86096
  scenario credits are research expense, not savings. Preserve all evidence.
  Separately registered002 requires the single local MCP tool ready at startup
  using documented configuration; strict recovery guard retained. No claim
  that optional-startup timing is the proven cause. New private port8319 only.

## Validation continuation and grading controls

Validation002 stopped after61 completed readers, before all grading. The cause
is now reproduced: Python str.splitlines() splits literal U+2028 inside valid
JSON strings. Physical LF-delimited parsing preserves the intact native JSONL;
actual truncation still fails. Two parser contracts pass. Every existing reader
now reconciles exact CLI/native/Langfuse counters and identities (61/61).
Original files/parser failure remain unchanged; no call is repeated.

[Continuation003](../../tools/usage-monitor/studies/longmemeval-codex-validation-protocol-003.json)
seals all61 stdout/answer hashes and runs only11 previously unstarted readers
plus72 previously unstarted rubric judges (83 new processes,144 across both
blocks). Methods, model, questions, raw fallback, FTS budgets, rotation and cost
rules remain unchanged; there were zero observed quality grades at registration.

The original rubric prompt omits condition names, but its working directory
contains them. Thus earlier “blinded” language means prompt-blinded only.
[Neutral audit002](../../tools/usage-monitor/studies/longmemeval-neutral-judge-audit-protocol-002.json)
was frozen before any validation grades: all72 answers receive the same rubric
in randomized anonymous directories, with the original anonymous IDs/order
retained from prepared audit001. Original grades stay intact; nomination requires
no observed matched-control successes lost under BOTH grade sets. All additional
judges count as research expense. Same-model judging/style cues still limit
quality conclusions. Audit001 never called a model; a copied-protocol-path
preflight error in the first audit002 preparation was preserved and corrected
before any model invocation, with an identity guard.

## Native archive mechanisms: preserve failures and recovery overhead

| Attempt | Actual transform / recovery | Status | Native tokens | Published-rate scenario credits |
|---|---|---|---:|---:|
|001|No observable recovery declarations; guard passes through|Failed gate; UNAPPLIED|47,116|0.86096|
|002|Required MCP startup still leaves HTTP schemas unobservable|Failed gate; UNAPPLIED|47,116|0.86096|
|003|Explicit profile/nonincremental setting still leaves HTTP schemas unobservable|Failed gate; UNAPPLIED|47,070|0.85406|
|004|3 actual transformed requests; one exact source; raw bypass; first CLI read fails, second repairs relative path|Mechanism applied; clean gate fails|93,010|1.07998|
|005|2 actual transformed requests; one exact source; one successful CLI recovery; raw bypass|Clean mechanism gate passes|69,890|1.54366|

MCP catalog probes without inference confirm the recovery tool loads, including
in a fresh native read-only thread. Missing HTTP schemas do not prove the tool
is unavailable. The shell-based method is separate and requires a completed
native shell call; it reuses existing TTGL read_compression_source CLI with an
explicit archive scope. Raw retrieval now avoids analytics database writes,
which matter inside a read-only agent. A relative-path/space-quoting regression
check protects the absolute command fix.8 policy/persistence contracts plus3
proxy/CLI contracts pass. Defaults and normal running8317 remain unchanged.

All canaries are research expense. Attempts004/005 are different configurations
and cache states, so their token/cost differences are not matched saving evidence.
They also illustrate why per-bucket pricing matters: the shorter005 run costs
more under the published-rate scenario because it has substantially more fresh
input. No cash, quality-transfer or default-adoption claim follows.

- Native-resume-metering001 passes two actual calls on one exact thread. CLI
  input snapshots24,411 then48,852 are cumulative; actual second-turn input24,441.
  Native unique-response total48,866 tokens /0.38498 scenario credits. Never add
  both cumulative snapshots. This is research overhead, not savings. The next
  [reuse comparison design](cache-and-memory-reuse.md) requires a continued native
  full-context cache control and actual repeated questions before claiming Mem0
  extraction amortizes. No scored reuse trials yet.
- Original validation grading completed: full history24/24, plain files24/24,
  FTS23/24. All144 session IDs/counters reconcile CLI/native/Langfuse. Scenario
  deployment credits146.19174 /20.23384 /15.11030 respectively. FTS fails the
  frozen no-loss rule despite lower cost; do not promote it or substitute the
  favorable development subset. Plain files cost86.16% less on this panel but
  are a predeclared control, not a newly validated selected treatment. Neutral
  audit002 is now running all72 registered assessments; both label sets will be
  retained, including disagreement and all judge overhead.
- All five archive canaries now have role-aware TTGL experiment records linked
  to existing native responses. Failed gate versus completed model invocation
  are distinct; no duplicate generation observations inserted. Public receipt
  identity paths are checked against registered study IDs. Owned canary proxies
 8319–8322 are stopped after audits; explicit-only profile003 was archived and
  removed only after exact owned-content verification. Normal services remain.

- Neutral audit002 completed all72 assessments and reconciles native/CLI/Langfuse.
  Full history24/24, plain files24/24, FTS22/24; one judgment differs from original
  (FTS23/24). Both sets remain immutable. The frozen FTS nominee fails under
  both, and no favorable subset/label set replaces either. Additional audit cost
 25.87580 scenario credits is research expense, not deployment cost.
- Cache-memory-reuse001 is prepared before inference:3 fresh corpus sizes ×4
  actual questions ×6 conditions (continued full context, fresh stable versus
  changing-prefix full context, ordinary files, FTS and reused adapted Mem0).
 75 CLI processes maximum including3 extractions; all real extraction/recovery
  cost and observed cached/fresh/output buckets count.12 reference/empty/stale
  oracle controls per type pass without model calls;2 new data/schema checks pass.
  The new per-turn allocator reconciles the existing2-call native-resume preflight
  without repeating inference. No scored reuse result yet. A first zero-model
  preparation and a versioned process-timer preparation amendment are retained.

- Cache-aware continuation update: reuse001 is running its full registered75-call
  maximum, with52/72 readers complete at the latest filesystem snapshot. No
  quality or cost result is inferred from this partial state. Primary efficiency
  compares observed fresh/cached/output cost plus actual memory extraction and
  recovery; cache-hit percentage and token count are explanatory measurements.
  Stable/changing prefixes and a continued-thread control test cache effects.
  Local compute prices and subscription cash/quota impact remain unknown.
- Coding-transfer preparation reviewed pinned MIT Exercism sources for Connect,
  Dominoes and SGF Parsing, excluding all previously reserved exercise families.
  Six empty/reference native controls behave as expected; references pass48
  official tests. Zero coding-transfer model trials have started. These controls
  are neither official benchmark scores nor evidence of agent performance.

## Actual cache and memory reuse: registered block001

All75 calls complete:72 readers and3 actual Mem0 extractions. Every arm passes
12/12 independent exact checks. All115 unique native responses reconcile with
CLI per-turn counters and Langfuse across66 sessions; cumulative resumed-thread
snapshots are never added. These are generated factual-recall diagnostics at
three corpus sizes, not coding tasks or a population-quality validation.

| Condition | Native tokens incl. extraction | Scenario credits | Change vs continued |
|---|---:|---:|---:|
| continued_full | 480,951 | 5.46879 | +0.00% |
| file_search | 572,597 | 5.50505 | +0.66% |
| fresh_full_head | 605,027 | 13.72351 | +150.94% |
| fresh_full_tail | 475,801 | 14.21133 | +159.86% |
| fts | 632,529 | 6.59329 | +20.56% |
| mem0_dense | 850,894 | 20.33354 | +271.81% |

Fresh changing-prefix full context uses1.07% fewer tokens than continued full
context yet costs159.86% more in this scenario. Its observed cached-input fraction
is42.64%, compared with81.52% for the continued control. Thus fewer tokens do not
establish lower cost. Stable-prefix fresh sessions also cost more than continued
context in this finite run; ordering and stochastic/cache-state variation limit
causal attribution to prefix placement alone.

Mem0 includes extraction once per corpus and four actual questions each. Its
pooled model-rate cost is271.81% above the continued control after these queries;
no extrapolated future break-even or optimal reuse count is claimed. Actual
per-corpus curves after1–4 questions remain in the public result. Local embedding,
indexing/loading and retrieval runtime are separate; monetary local cost and
subscription cash/quota remain unknown. FTS passing this generated diagnostic
does not reverse its failed registered LongMemEval validation.


## Actual older-history application gate001

Both registered calls completed and answered correctly. The first old-output
transform reduces native response input by4,494 tokens; corresponding raw input
increases88. The newest four observations remain intact, one archived source is
exact, and one successful CLI retrieval passes through raw. All15 native responses
reconcile CLI; the separate bounded Langfuse audit checks both sessions.
Raw costs1.39721 modeled credits (185,493 tokens); masking plus recovery costs
1.63609 (202,361 tokens),17.09% more. The native history mechanism works but does
not establish cost savings, autonomous recovery or coding-task performance.
Both complete invocations count as research expense. Normal routing is unchanged.

- Native age gate001 Langfuse delivery caught up: receipt002 reconciles all15
  responses across both sessions. Initial lagging receipt001 is preserved; no
  generation re-ingested or repeated. Owned proxy8323 stopped after verification.
- Coding-context-transfer001 registered and prepared before inference: three
  pinned unreserved MIT Exercism exercises × raw/Headroom/reversible/older-mask,
 12 fresh calls maximum. Same48 original tests across tasks; host grades after
  all generation, artifact-policy checks, zero retries, actual transform counts
  and complete inference cost. No official benchmark or long-horizon claim.

- Graphiti0.31.2 embedded-backend review: exact28-package Kuzu candidate resolves,
  all28 OSV queries show no matches, and28 downloaded wheels match registry hashes
  with no automatic scripts. Nothing installed/executed. Rejected this backend
  on maintenance grounds: [Graphiti](https://github.com/getzep/graphiti) deprecates
  Kuzu and [upstream Kuzu](https://github.com/kuzudb/kuzu) is archived. This is not
  a vulnerability finding against the selected Graphiti version; the historical
  [Cypher advisory](https://github.com/advisories/GHSA-gg5m-55jj-8m5g) affects earlier
  versions. Reviewing the supported FalkorDB Lite alternative before installation.
- FalkorDB Lite candidate is blocked before installation/execution:35 Python
  packages have no OSV matches, but wheel metadata and its pinned build source
  identify bundled Redis8.10.2, while [upstream8.10.3](https://github.com/redis/redis/releases/tag/8.10.3)
  fixes a heap-overflow issue. This is a component finding, not a claim that a
  Python package scan found it. Scope/isolation does not waive the standing
  confirmed-vulnerability rule. OpenSSL's Ubuntu backports were distinguished
  from its upstream version string. Continue Graphiti review with a patched
  maintained backend; neither rejected backend was installed or executed.
- LHTB2 source is pinned at7ca0cacea9bf6a0694eaad7306bed794eaaaabce
  (Apache-2.0,77 task configs; metadata/README/license/declarations only).
  First fork runtime resolves102 packages; OSV finds13 advisories on filelock3.32.7
  selected by LiteLLM's filelock<4 constraint. That candidate is blocked before
  install/execute; no incompatible dependency override. Existing reviewed Mem0
  uses filelock4.2.9 and is a different graph. See
  [long-horizon readiness](long-horizon-context-memory.md). No LHTB score exists.

## Fresh public coding transfer001

The complete12-run panel passes all sealed original tests and protected-file
checks on Connect, Dominoes and SGF Parsing. All60 unique native responses
reconcile with CLI counters; Langfuse auditing is separate. Three tasks share
public48-test suites, with actor self-validation and fresh host execution.
These public exercises may be familiar to pretrained models; this is a small
development transfer diagnostic, not an official benchmark or long-horizon study.

| Condition | Passing tasks | Applied tasks | Native tokens | Modeled credits |
|---|---:|---:|---:|---:|
| headroom-lossless | 3/3 | 0/3 | 341,896 | 3.83520 |
| off | 3/3 | 0/3 | 315,134 | 3.68218 |
| older-shell-mask | 3/3 | 0/3 | 369,345 | 4.15041 |
| reversible-shell-handles | 3/3 | 3/3 | 443,592 | 5.08760 |

Reversible handles apply on3/3 tasks but cost38.17% more in aggregate, including all actual recovery inference.
Exact retained-source hashes are verified. Headroom and age masking have zero
transformations on these actual tasks: their contrasts are UNAPPLIED and cannot
establish a compression effect. Their differing action sequences and token/cost
totals remain visible, rather than being presented as savings or removed.
No candidate is promoted from this panel. Cash/quota impact remains unknown.

- Coding-transfer001 all60 native responses reconcile Langfuse across12sessions;
  TTGL experiment4d3cf1dd3f9442328da6d46b798168b6. Owned8324 proxy stopped.
- Mem0 infer=False raw-record mechanism passes exact retention, latest-record
  retrieval and tenant separation with0 LLM calls. First process exits0 but emits
  a Qdrant shutdown-destructor warning; preserved. A read-only reopen verifies
  all3 records and explicit close with0 embeddings/LLM calls; only an ONNX PCI-discovery warning remains.
  No agent-quality or cost-saving result follows; a fresh matched comparison
  remains necessary. Existing reviewed runtime and pinned local encoder only.

- Memory-storage-ablation001 prepared before inference:3 fresh corpora in the
  reused generator family ×4 actual questions ×6 arms (continued full context,
  ordinary files, FTS, extracted Mem0, Mem0 infer=False and maintained MCP graph
  raw records).75 native calls maximum incl3 extractions. Same raw files and
  exact latest-record oracle; no model rubric, no held-out or coding claim.
  Actual raw storage/query mechanisms use existing reviewed installations.
  First zero-LLM helper preflight preserved an MCP wrapper-count parsing error;
  corrected fresh preflight002 stores3 records and retrieves the latest fact.
  No model invocation was repeated. Complete model-cost and local-runtime
  accounting remains required before interpreting any reader result.
- Native long-horizon readiness: versioned TTGL Docker/MCP stdio port reuses
  existing reviewed server2.4.0 runtime. Two catalog/error/name checks pass with
 0 models,0 containers and0 image executions; real actor isolation still gated.
  Old SDK95-package graph OSV0/tarball-hash95/95, not installed; open unscored
  OAuth report retained, modern server chosen without legacy OAuth package.
  Public readiness pool reserves3 development/6 validation tasks from pinned
  metadata before task-source inspection. Development metadata/Dockerfiles match
  Git blob hashes; Python3.11 base manifest pinned, no image pull/build/run.
