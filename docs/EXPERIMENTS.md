# Experiments and recorded results

Consolidated repository index, **18 November 2026**. This covers the research
families, their failed predecessors and operational diagnostics. The
[artifact index](EXPERIMENT-ARTIFACTS.md) lists every public study result file
and the protocol locations; it includes software/mechanism records as well as
scored experiments. Papers are indexed [separately](PAPERS.md).

**How to read the numbers:** token counts are measured native counters where
available. Cost percentages retain each study's dated rate scenario, including
recorded controller, expert and maintenance inference. They are not current
price quotes, measured cash/quota savings or full deployment costs. Cached input
is a subset of input. Unknown totals stay unknown; `≥` means a lower bound.
Do not pool overlapping tasks, adaptive policy versions or incomplete subsets.

## Routing and small-model/expert collaboration

| Experiment | Status / scope | Result and evidence |
| --- | --- | --- |
| Model-led tool delegation (`model-led-delegation-001`) | Routing/MCP/worker software validated; native qualification blocked | 22 new + 48 shared tests pass. Eleven-task historical replay: Sol 9/11, always-Luna 7/11; similarity and recency policies abstain to Sol on all tasks. No new model calls or recency benefit established. [Protocol](../experiments/model-led-delegation-001/README.md), [checkpoint](../results/model-led-delegation-001/README.md) |
| RSI-Router Luna/Sol reproduction (`rsi-luna-sol-001`, proposed) | Implementation handover only; no native assignments | Step-routing reproduction, bounded candidate/skill evolution, SWE-bench Verified primary and Terminal-Bench secondary. Protocol design is separate from the existing node-delegation study. [Detailed coding-agent specification](research/rsi-router-luna-sol-spec.md) |
| LiveCodeBench routing replay (`routing-pilot-001`) | Complete; 713 paired published tasks | At 50% remote-call budget, learned routing 29.93% pass@1 versus random 28.35%; difference +1.58 points, 95% CI −1.58 to +4.44. Inconclusive; remote-only 39.37%. [Results](research/results.md), [audit](research/independent-audit.md), [artifacts](../results/routing-pilot-001/) |
| SWE-bench Verified published-run replay (`swe-replay-001`) | Complete; 500 tasks, ten historical model runs, five folds | 46.1% estimated inference saving; success 64.2% versus 72.8%, an 8.6-point loss. Target fails. Cheap strong MiniMax standalone control matters. [Report](../results/swe-replay-001/README.md), [audit](research/swe-replay-audit.md) |
| Initial live Codex pilot (`codex-pilot-001`) | Complete; 16 assignments on four historical tasks | Functional passes Luna 3/4, Sol 4/4, task router 4/4, optional conversation 3/4. Strict artifact-policy acceptance 3/4, 4/4, 2/4, 0/4 respectively. All optional controllers used zero expert calls; usage/cash unknown. [Report](../results/codex-pilot-001/README.md), [summary](../results/codex-pilot-001/analysis/summary.json) |
| Required two-round dialogue | Complete; mechanism diagnostic | Actual clarification exchange passes 30 regression tests. Does not establish autonomous routing or economic benefit. [Transcript](../results/codex-pilot-001/dialogue-transcript.md) |
| Native isolated six-condition study (`codex-isolated-20261026`) | Complete; 72 assignments, 12 tasks | Small 9/12, large 10/12, pre-task router 11/12, one-way 9/12, reset expert 8/12, personal 9/12. Pre-task router scenario saving 31.1%; personal 95.5% with quality loss and zero expert calls. [Final analysis](../results/codex-isolated-20261026/analysis-001/README.md) |
| Adaptive delegation development | Complete; four reused development tasks, three matched arms | Luna 2/4, Sol 4/4, assisted 4/4; one expert call, 87.1% scenario saving. Joint 95/95 target fails. [Comparison](../results/prompt-comparison-001/README.md), [analysis](../results/delegation-development-001/analysis-adaptive-001/README.md) |
| Bounded cheap-first development | Complete; same four tasks, fresh matched controls | Luna 3/4, Sol 4/4, assisted 4/4; one expert call, 89.1% scenario saving. Selected prospectively for held-out study; 95/95 target fails. [Analysis](../results/delegation-development-001/analysis-fallback-001/README.md) |
| Compact context-only expert development | Complete; same four tasks, fresh matched controls | Luna 3/4, Sol 4/4, assisted 3/4; zero expert calls, 95.7% saving with quality loss. Cannot attribute results to expert-interface compaction. [Analysis](../results/delegation-development-001/analysis-compact-001/README.md) |
| Compact expert-interface calibration | Complete; one arithmetic call per interface | 39.0% fewer input tokens and 36.8% lower scenario cost. Interface mechanism only. [Measured analysis](../results/compact-expert-calibration-001/analysis.json) |
| Held-out cheap-first (`delegation-heldout-001/study-002`) | Complete; 33 assignments on 11 eligible tasks | Luna 7/11, Sol 9/11, assisted 8/11; four consultations, one Luna failure recovered, no Luna success lost. 91.45% saving, 88.89% relative retention: 95/95 fails. Invalid twelfth control excluded before inference without replacement. [Final analysis](../results/delegation-heldout-001/analysis-002/README.md); [seven-task interim](../results/delegation-heldout-001/interim-007/README.md) is historical |
| Required native context-only handoff | Complete; diagnostic | Three positively metered calls and useful integration; no benchmark or autonomous-routing claim. [Rescue methods](research/routing-rescue-study.md), [mechanism records](../results/handoff-mechanism-001/) |
| Pro environment/Harbor and first-block attempts | Preparations and stopped attempts preserved | Transport, actor and replay gates are separate from scores. Original four-arm block did not become a completed comparison. [Runbook](research/pro-harbor-runner.md), [attempts](../results/swe-pro-prompt-001/), [reservation](../experiments/swe-pro-prompt-001/README.md) |
| NodeBB010 voluntary router | Complete; selected development episode | Initial/fresh grading pass, zero Sol calls; no delegation-benefit claim. [Audit](../results/router-development-010-analysis/README.md) |
| Ansible012 / Element014 / Tutanota016 | Complete; three sequential adaptive development episodes | All initial/fresh grades pass. First two use zero experts; Tutanota uses one completed consultation, but its pre-handoff patch already passes. No observed rescue. [Series report](../results/router-iterations-20261031/README.md) |
| Teleport018 | Complete; v6 development episode | Initial/fresh grades pass, zero expert calls. Incomplete public verification disclosed; passing grade is not a delegation result. [Audit](../results/router-teleport-20261031/teleport-analysis-018/README.md) |
| Vuls020 | Complete; v6 development episode | Final passes after one consultation; pre-handoff dependency-only patch fails. No useful checked independent attempt or justified early exception: premature delegation, not demonstrated rescue of a checked repair. [Audit and transport correction](../results/router-vuls-20261031/vuls-analysis-020/README.md) |
| Target90 v7: Flipt022 / Navidrome024 / Protonmail026 | Complete; three matched development pairs | Sol 3/3, router 2/3; 96.2821% scenario saving, quality target fails; zero experts. [Pair records](../results/target90-development-20261031/README.md) |
| Target90 v8: Openlibrary028 / Qutebrowser030 | Complete; two matched development pairs | Sol 2/2, router 1/2; missed escalation remains. Zero experts. Same report preserves failures and version boundaries. [Records](../results/target90-development-20261031/README.md) |
| Target90 v9: NodeBB032 | Complete; one matched development pair | Both pass, zero experts. Structured evidence exposes gaps but does not prove calibrated detection. All six adaptive pairs: Sol 6/6, router 4/6, 96.4048% saving: target fails. [Final development checkpoint](../results/target90-development-20261031/README.md) |
| Fixed v9 transfer reservation | Registered; no completed comparison located in public results | New outcome-independent development reservation; no held-out result inferred. [Plan](../experiments/target90-v9-transfer-20261101/plan.json) |
| Aider-derived routing/verification-feedback v3 | Prepared; no scored model-quality result | 12 development / 24 validation tasks; software and framework checks do not establish efficacy or official Aider scores. [Design](research/verification-feedback-study.md), [preflight records](../results/verification-feedback-001/) |

The 95/95 criterion means **95% lower scenario cost and at least 95% relative
accuracy retention**. The later target90 criterion means **at least 90% lower
cost with no observed matched quality loss**. Neither is a guaranteed outcome
or an established final fixed-policy held-out result.

## Observatory, context and verification

| Experiment | Status / scope | Result and evidence |
| --- | --- | --- |
| Offline cloud context adapter | Complete; zero model calls | Identity/shape/immutability checks expose and fix double-encoded JSON text; deterministic spy, not Headroom or token-saving evidence. [Report](research/context-experiment-continuation-20261105.md), [records](../results/context-cloud-20261105/) |
| Analyst usability pilot | Complete; initial failed integration plus two participants and interviews | Revised tool payload 312,034 → 83,026 bytes (73.4% less), but calls/time increase. Native totals include differing interviews; descriptive, not causal savings. [Report](../tools/usage-monitor/studies/agent-usability-results-001.md) |
| `progress-replay-001` | Complete; rejected | Apparent 56.40% token reduction fails quality; retained alongside revision. [Both attempts](../tools/usage-monitor/studies/progress-replay-results-002.md) |
| `progress-replay-002` | Complete; three reused log diagnoses | All six checks pass; 45.58% fewer native tokens. Research overhead unrecovered on first use; no full coding-task claim. [Report](../tools/usage-monitor/studies/progress-replay-results-002.md) |
| `live-harness-001` | Complete; four real code-edit/test runs, two generated tasks | 212,187 → 190,809 pooled tokens (10.075% less), all checks pass, no observed speedup. [Report](../tools/usage-monitor/studies/live-harness-results-001.md) |
| `retrieval-guidance-001` | Complete; rejected | Six correct answers, 11.78% more native tokens, 1/3 pair wins. [Report](../tools/usage-monitor/studies/harness-optimization-backlog.md) |
| `output-audit-001` | Complete; offline | Only 6/413 distinct retained outputs change; repeated presentations differ. Retained-byte reduction is not inference savings. [Audit](../tools/usage-monitor/studies/harness-optimization-backlog.md) |
| `independent-read-batching-001` | Complete; development gate passes | All six checks pass, 308,046 → 265,627 native tokens (13.7703% less), 2/3 pair wins. Added cache-weighted scenario saving 16.8629%. [Results](../tools/usage-monitor/studies/independent-read-batching-results-001.json), [discussion](paper/context-memory/report.md) |
| Chronological memory001 / corrected002 | 001 pre-model configuration failure; 002 complete | Two three-stage generated coding sequences, 24 processes. All checks pass; raw history 17.47% fewer tokens but only 3.24% lower scenario cost; FTS/notes do not improve cost materially. [Results](../tools/usage-monitor/studies/chronological-memory-results-002.json), [report](paper/context-memory/report.md) |
| Reversible archive canaries001–005 | Complete; failures/unapplied attempts preserved | 001–003 unapplied; 004 needs a repaired recovery command; 005 actually transforms and recovers exact source cleanly. Mechanism, not coding savings. [Progress](research/context-memory-experiment-progress.md), [all versions](EXPERIMENT-ARTIFACTS.md) |
| Archive age canary001 | Complete; application gate passes, economic gate fails | Intended older-result boundary applies, but recovery raises whole-invocation scenario cost 17.09%. [Results](../tools/usage-monitor/studies/archive-age-canary-results-001.json) |
| Coding context transfer001 | Complete; three public coding cases × four policies | All 12 checks pass. Headroom and age masking unapplied; reversible handles apply on 3/3 but cost 38.17% more than raw including recovery. [Results](../tools/usage-monitor/studies/coding-context-transfer-results-001.json) |
| Harness instruction-scope001 | Complete; three reused coding cases, six processes | All six pass; task-scoped actors use 25.18% fewer tokens and 10.69% lower scenario cost. No global instruction change or general efficacy claim. [Results](../tools/usage-monitor/studies/harness-scope-results-001.json) |
| Verification selection development001 | Complete; three seeded repair pairs | Both arms 3/3; focused initial tests with full final verification cost 28.61% less. [Results](../tools/usage-monitor/studies/verification-selection-results-001.json) |
| Verification selection validation001 | Complete; rejected | Both arms 12/12; focused arm costs 21.27% more, uses 19.38% more tokens, wins 4/12 costs. Preserve favorable development separately. [Results](../tools/usage-monitor/studies/verification-selection-validation-results-001.json), [adherence audit](../tools/usage-monitor/studies/verification-selection-validation-adherence-results-001.json) |
| On-demand analyst/telemetry readiness | Completed bounded reviews and reconciliation; collection continues only when running | Versioned evidence interpretations and analysis overhead; finite operation runtime distinguished from background lifetimes. Proposals are not measured improvements. [Observatory methods](research/observability-setup.md), [usage work](research/usage-optimizer.md) |

## Retrieval, caching and memory QA

These are adapted local benchmark/development tasks, not official leaderboard
scores or evidence of weight training. Their reader, extraction and judge
budgets differ; use the individual full-cost definitions.

| Experiment | Status / scope | Result and evidence |
| --- | --- | --- |
| Mem0 dense mechanism | Complete; adapted self-hosted engine | Real extraction/persistence/retrieval and tenant isolation; failed obsolete search call retained. No quality gain follows from readiness. [Progress](research/context-memory-experiment-progress.md) |
| LongMemEval-derived development001 | Stopped; failure retained | Three readers finish; memory extraction times out, zero grades. Unknown extraction usage is not zero; no repeated calls. [Progress](research/context-memory-experiment-progress.md) |
| LongMemEval-derived development002 | Complete; seven remaining unstarted cases, 63 processes | All 28 local rubric checks pass. FTS scenario cost 82.80% below full history and 17.15% below files; Mem0 88.18% above full. FTS nominated. [Results](../tools/usage-monitor/studies/longmemeval-codex-development-results-002.json) |
| LongMemEval-derived reserved validation003 | Complete; FTS rejected | Original grades full/files/FTS 24/24, 24/24, 23/24; anonymous audit 24/24, 24/24, 22/24. FTS costs 25.32% less than files but fails no-loss under both rubrics. [Results](../tools/usage-monitor/studies/longmemeval-codex-validation-results-003.json), [report](paper/context-memory/report.md) |
| Actual cache/memory reuse001 | Complete; 72 readers plus three extraction calls | Each arm 12/12 exact checks. Changing-prefix fresh context uses 1.07% fewer tokens but costs 159.86% more than continued context; Mem0 +271.81%. [Results](../tools/usage-monitor/studies/cache-memory-reuse-results-001.json) |
| Raw Mem0 mechanism001 | Complete; no native LLM calls | Exact raw storage, namespace isolation and guarded no-extraction mode observed; not a task-quality comparison. [Results](../tools/usage-monitor/studies/mem0-raw-mechanism-results-001.json) |
| MCP raw graph mechanism003 | Complete; mechanism gate passes | Actual maintained memory server integration; no graph-reasoning advantage established. [Results](../tools/usage-monitor/studies/mcp-memory-mechanism-results-003.json) |
| Memory storage/extraction ablation001 | Complete; 75 calls, 72 exact reader checks | Raw Mem0 cuts modeled LLM cost 59.53% versus extraction but remains 45.72% above continued context. MCP raw graph +14.25%; ordinary files −1.91%. No new default. [Results](../tools/usage-monitor/studies/memory-storage-ablation-results-001.json) |
| Smallville original-style mechanism | Complete; parser failures and deterministic replay retained | 41 actual responses, 421,840 tokens; exact recall. Reflection forced diagnostically, not naturally triggered. Malformed triples corrected by zero-new-call parser replay. [Source fidelity](research/smallville-source-fidelity.md), [results](../tools/usage-monitor/studies/smallville-mechanism-results-001.json) |
| Evidence-first Smallville adaptation development001 | Complete; three reused questions, nine readers and nine judges | All three arms 3/3; adaptation 94.08% lower remote scenario cost than full and 74.26% than files. Cold local embedding/index setup is slower; not original algorithm. [Report](research/smallville-results.md), [results](../tools/usage-monitor/studies/smallville-benchmark-results-001.json) |
| Direct original-style Smallville development001 | Complete; economic gate fails | 3/3, 146 importance ratings, zero natural reflections; 2.3472× full-history cost and 10.2053× file-search cost. [Results](../tools/usage-monitor/studies/smallville-original-results-001.json) |
| Smallville fresh validation001 + anonymous audit002 | Complete; rejected | Primary grades 6/6 all arms; anonymous grades full/files/memory 6/6, 6/6, 5/6. 90.50% saving versus full and 15.88% versus files, but only 3/6 file-cost wins; frozen gate needs 4/6. [Final report](research/smallville-results.md), [audit](../tools/usage-monitor/studies/smallville-neutral-audit-results-002.json) |

## Online coding memory, repository history and teams

| Experiment | Status / scope | Result and evidence |
| --- | --- | --- |
| Online memory canaries001–003 / continuation001 | Complete; failed versions retained | Tool-permission/search/scope failures precede a working restarted-session code/note/source-recheck diagnostic. Eight processes, 633,879 tokens, 7.70659 historical scenario credits. Integration, not long-horizon efficacy. [Report](research/smallville-online-results.md) |
| Long-horizon task controls / nine-assignment online matrix | Controls pass; model matrix operator-discontinued | One completed control reward 0.9913793103448276, partial memory arm, no final matched efficacy result. Do not resume as an ordinary setup step. [Disposition](research/smallville-online-results.md) |
| Luna Smallville maintenance mechanism002–004 | Complete; original prompt failures retained | Storage/recall and deterministic output compatibility observed; forced reflection is diagnostic. [Results and chronology](research/luna-memory-tokeneconomizer.md) |
| Memory-only coding comparison001 | Complete; eight tasks per arm | All arms 8/8; versus source search, Smallville/Luna +26.25% scenario cost, TE/Sol +3.03%, TE/Luna +6.75%. No candidate passes economic gate. [Report](research/luna-memory-tokeneconomizer.md), [results](../tools/usage-monitor/studies/luna-memory-tokeneconomizer-results-001.json) |
| Actual native-hook coding comparison001 | Complete; lifecycle failure and prospective continuation retained | All arms 8/8; Smallville/Luna +18.43%, TE default +6.06%, TE memory-on/Luna −12.05%. TE actually injects zero skills and applies zero pruning/redirects: saving is not causal memory evidence. [Results](../tools/usage-monitor/studies/luna-memory-tokeneconomizer-native-results-001.json) |
| Smallville Sol-maintained coding control001 | Complete; later-period control | 8/8; Sol-maintained Smallville +120.58% versus source-search control. Luna maintenance 93.29% cheaper, total cost 46.31% lower than later Sol-maintained arm, but still above plain search. [Results](../tools/usage-monitor/studies/luna-memory-smallville-sol-control-results-001.json), [limits](research/luna-memory-tokeneconomizer.md) |
| Repository memory wave A | Complete; two tasks × four arms, adapted environment | Registered exact-set success 0/2 per arm; post-hoc prescribed-tests success 1/2 per arm. Raw/Mem0/Graphiti cost +6.96%/+5.63%/+46.35% versus fresh. Added passing tests explain one strict-matcher failure; genuine regressions remain on the other task. [Report](research/repository-memory-wave-a-results.md) |
| Repository longitudinal001 | Partial; 216-assignment registration | Public analysis records 13 finished generations with zero hidden grades at that snapshot; no final quality result. Six arms, 36 tasks over ancestor-ordered repository lineages. Do not infer completion from the plan or old running PID. [Continuation](research/knowledge-accumulation-study.md), [analysis registration](../tools/usage-monitor/studies/repository-memory-longitudinal-analysis-001.json) |
| Repository native-history / additional-backend diagnostics | Mechanism work and separate registrations; no completed matched efficacy panel | Native extraction/injection demonstrated; cancelled background usage remains unknown. Supplemental Smallville/TE/native arms must not be pooled as same-period baselines. [Continuation](research/knowledge-accumulation-study.md), [protocol](../tools/usage-monitor/studies/repository-additional-history-protocol-001.json) |
| Commit0 compatibility / native team readiness | Controls and preflights; not scored efficacy | SimPy/TinyDB adapted-runtime source controls and native team metering support subsequent pilot; rejected providers/dependencies stay visible. [Preparation report](paper/codex-team-knowledge/preparation-results.md) |
| Native Codex team pilot | Complete; 24 cells, two libraries × three knowledge arms × four capacities | 24/24 saved sources pass; 23 normal parents. Native capacity eight 31.3% faster at ≥2.45× single-agent model cost. MCP publishes 91 observations but all four read queries are empty. 17 cells have incomplete usage. [Results](paper/codex-team-knowledge/pilot-results.md) |
| Reserved-library team extension | Interrupted / unfinished; 80 registered assignments | Distinct from 24-cell pilot and 56-cell memory comparison. No completed full-panel result; not resumed here. [Reservation and status](paper/codex-team-knowledge/reserved-extension.md) |
| Memory-aware team extension | Incomplete; seven arms × two libraries × four capacities, 56 planned | Public report refreshed without inference from checkpoint039: 39 recorded, 38 passing sources, 37 normal parents. No live generation/publisher observed on 15 November. Mem0 capacity-eight failure preserved; unknown usage bounds retained. No completed matrix or memory advantage claimed. [Snapshot](paper/codex-team-knowledge/memory-aware-results.md), [methods](research/team-memory-extension.md), [handoff](research/team-memory-handoff-20261112.md), [examples](paper/codex-team-knowledge/appendix.md) |

## Native transport, metering and boundary diagnostics

These validate the instrument, not a task-performance hypothesis. Each result
version is listed in the [artifact index](EXPERIMENT-ARTIFACTS.md).

| Diagnostic | Recorded outcome | Evidence |
| --- | --- | --- |
| Thread/billing introspection001 | Backend usage availability and null cost/quota fields preserved; no cash inference from missing counters | [Record](../tools/usage-monitor/studies/native-thread-billing-results-001.json) |
| Native resume metering001 | Validated per-turn deltas / response deduplication; resumed CLI totals are cumulative | [Record](../tools/usage-monitor/studies/native-resume-metering-results-001.json) |
| Reader boundary001 / 002 | Initial allowed-read path fails before execution, so isolation is unproven; no denied marker leaks. Separately versioned boundary passes | [001](../tools/usage-monitor/studies/native-reader-boundary-results-001.json), [002](../tools/usage-monitor/studies/native-reader-boundary-results-002.json) |
| Explicit compaction002 + measurement correction | Local Responses compaction observed; separately registered remote endpoint gate unexercised; read-only correction preserves original measurement | [Original](../tools/usage-monitor/studies/native-compaction-results-002.json), [correction](../tools/usage-monitor/studies/native-compaction-results-002-measurement-002.json) |
| Large native capture001 | Correct answer but wrapper clips fixture; automatic compaction unexercised, gate fails | [Record](../tools/usage-monitor/studies/native-long-capture-results-001.json) |
| Large native capture002 | Exact 327,917-character input and recall; real in-band automatic compaction. All three responses reconcile at 528,522 tokens, including 189,257 compaction tokens absent from final ordinary CLI snapshot | [Record](../tools/usage-monitor/studies/native-long-capture-results-002.json) |

## Proposed, blocked and unscored work

- **Distillation, LoRA, AI-feedback/RL and GPU arm:** data/dry-run/software
  preparation exists; no trained-model quality result. Runpod was unprovisioned
  in its recorded study. [Methods](research/gpu-training.md),
  [prospective learning study](paper/learning-study.md).
- **Hierarchical context, principles/stage-aware retrieval, local selection,
  Aider repository map, LLMLingua and Letta:** proposals or dependency review,
  not completed comparisons. The ten supplied context ideas are a backlog,
  not ten experiments that ran. [Register](research/context-memory-experiment-progress.md).
- **RTK, full Headroom image and CLIProxyAPI:** historical candidates have
  security blocks. This does not invalidate the separately reviewed stdlib
  Headroom subset; no broad dependency clearance is implied.
  [Security policy](security/dependency-security-policy.md),
  [source/candidate review](research/observability-setup.md).
- **Cognee / original Graphiti local-provider readiness:** failed preparations,
  advisory-matched configurations and model compatibility gaps remain recorded;
  no invented score or zero cost. Graphiti/Luna is a separately admitted later
  configuration. [Preparation](paper/codex-team-knowledge/preparation-results.md),
  [appendix](paper/codex-team-knowledge/appendix.md).
- **Operational audits:** host cleanup, paper preview QA, source restoration,
  runtime security, actor controls and lossless archive checks are supporting
  evidence, not additional model-quality experiments. See [results](../results/)
  and the linked protocols for their immutable receipts.

This index does not launch or resume research. Scheduled monitoring remains
paused. Current process/receipt checks supersede old PID references; a saved
`running` snapshot is not proof of a live worker. Frozen generation sources,
negative results and reserved validation sets remain unchanged.
