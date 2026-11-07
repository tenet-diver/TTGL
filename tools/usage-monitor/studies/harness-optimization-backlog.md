# Harness tools and experiment queue

Updated 7 November 2026. The [machine-readable queue](harness-optimization-backlog.json)
tracks candidates, comparisons, gates and bounded model-process caps. Entries are
proposals unless marked completed. Research schedules remain paused.

Prefer existing tools. TTGL supplies only the missing experiment registration,
native-counter reconciliation and immutable local receipts; it does not implement
a competing search engine, repository mapper or learned compressor.

## What we have actually tested

The first new trial rejected blanket retrieval guidance. Three fresh development
source investigations used identical copies of 80 tracked public application files,
the same native `gpt-6.1-sol` model and normal shell tools. Both arms could read all
source. The candidate added a general discover-files-then-read-definitions instruction;
the baseline was neutral and was not forced to produce oversized results.

| Investigation | Neutral native tokens | Scoped native tokens | Exact facts/source checks |
|---|---:|---:|---|
| Deployment defaults | 72,162 | 124,343 | Both pass |
| Capture guards | 75,276 | 76,464 | Both pass |
| Evidence pagination | 122,132 | 100,519 | Both pass |
| Total | 269,570 | 301,326 | 6/6 pass |

The candidate used **11.78% more total native tokens** and won only one pair,
failing its registered 5% reduction / two-pair-win gate. Retained tool output fell
28,577 → 24,125 bytes, but calls increased 9 → 11. Extra tokens comprise 31,360
cached input, 286 fresh input and 110 output. This is not an 11.78% cash-cost increase.
Both arms already used scoped searches; mandatory discovery added work in the
configuration case. Keep normal guidance. This is a small source-investigation
diagnostic, not a coding benchmark or general quality/latency result.

All six fresh-session CLI usage counters reconcile exactly with native generation
events. Cached input is counted once. There were no process retries or replacement
attempts; native transport retained its own retry defaults. The [protocol](retrieval-guidance-protocol-001.json)
was frozen before inference. The experiment, measured cells, reject verdict and
570,896-token trial-expense ledger are in TTGL's **Experiments** view. Parent
implementation/analysis is additional; there is no demonstrated net research saving.
An accrued 17:25 UTC snapshot records 2,358,148 parent tokens plus 570,896 trial
tokens: **2,929,044 native tokens of research expense**, a lower bound while this
chat remains active. These are measured token counts, not billed cash or quota.

A separate offline audit matched all 683 indexed tool events before registration.
446 had retained native `aggregated_output`, representing 413 distinct outputs.
Existing transforms changed only 6 distinct outputs: 1,925,451 → 1,742,273 bytes
(9.51% reduction). Across repeated event presentations, 8/446 changed. There were
33 extra identical presentations and 9 known native persistence truncation markers.
Opaque MCP result bodies are outside this output audit. Repeats are investigation
targets, not automatically waste. These are retained bytes, not measured model inputs
or token savings, and the corpus contains research activity.

## Tools worth testing

Upstream repository, release and license metadata were checked on 6 November.
Release dates are observations of cadence, not proof of ongoing support. No new
third-party tool, package, image or model was installed for this work.

| Tool / approach | Fit and current status | Next test |
|---|---|---|
| [ripgrep](https://github.com/BurntSushi/ripgrep), installed 15.2.0 | MIT/Unlicense; latest release July 2026, source activity October. Generic extra discovery lost in this trial. | Batch genuinely independent reads; avoid another blanket discovery instruction. |
| [Headroom](https://github.com/headroomlabs-ai/headroom) | Apache-2.0; upstream 0.43.1 released November 2026. Only the already-reviewed pinned stdlib subset is installed. Its present corpus coverage is narrow. | Fresh varied transfer only after selecting a development winner; preserve reversible/raw retrieval. |
| [RTK](https://github.com/rtk-ai/rtk) 1.1.0 | October release, November source activity. CLI Apache-2.0; embedded engine BUSL-1.1 with additional-use restrictions. **Pinned release blocked by dependency findings.** | Resolve findings before explicit-wrapper tests; do not enable automatic command rewriting. |
| [Aider repository map](https://aider.chat/docs/repomap.html) | Apache-2.0 repository; latest tagged release 0.86.0 is August 2025, latest commit May 2026. Uses a budgeted dependency/symbol map. Runtime graph unreviewed. | Compare a fixed-budget map against normal retrieval on fresh multi-file tasks. |
| [LLMLingua](https://github.com/microsoft/LLMLingua) | MIT code; tagged release 0.2.2 is April 2024 despite November 2026 source activity. Weight licenses/runtime graph unreviewed. | Lower-priority lossy documentation compression, with factual guards and compressor costs included. |
| [Langfuse datasets/experiments](https://langfuse.com/docs/evaluation/experiments/datasets) | Existing local deployment. Native experiment/run/score capabilities may replace additional custom comparison UI. | First verify installed API compatibility and idempotent synthetic records, without evaluator inference. |

OSS license fees are separate from model/compute costs. No managed pricing tier,
paid evaluator or cloud service is provisioned. RTK's engine grant permits specified
production use without charge but restricts paid/hosted derivatives; review the
[pinned license](https://github.com/rtk-ai/rtk/blob/753a3b0e939f2e4490fc24e3a1984010f40a103c/engine/LICENSE)
before embedding it in TTGL.

RTK review pinned commit `753a3b0e939f2e4490fc24e3a1984010f40a103c` and hashed
its manifest/lock/licenses. OSV queried all 251 registry packages in its 255-package
release lock and matched eight package versions. Findings include Rustls and LRU
vulnerabilities plus a maintenance advisory; GHSA/RustSec aliases are not independent
vulnerabilities. These are lockfile findings, not proof that every path is reachable
in a final binary. They still block this candidate under the user's policy. See
[Rustls advisory](https://osv.dev/vulnerability/GHSA-2mjx-qc3c-rqvc) and
[LRU advisory](https://osv.dev/vulnerability/RUSTSEC-2026-0002).
Artifact provenance, scripts and final platform graph review remain incomplete.

## Order and acceptance rules

1. Test independent-read batching with existing tools: at most three fresh pairs,
   all exact checks passing, at least 5% pooled native-token reduction and two pair wins.
2. Check native Langfuse experiment storage without model calls.
3. Review a patched RTK candidate, then test error/warning/unknown-output preservation
   offline before any matched repair tasks. Keep raw results and exit codes.
4. Compare repository maps and affected-test-first verification on separate tasks.
   Verification arms both require a full independent final check.
5. Consider learned compression only if cheaper deterministic approaches leave a
   recurring supported opportunity. Include its model/runtime costs.
6. Freeze a development winner before separately registered fresh coding evaluation.

Each inference experiment needs its own frozen protocol before starting: sample and
order, matched controls, one changed variable, exact quality checks, complete native
accounting, process cap, no automatic process retry and a rollback. Do not select a
favorable subset or tune held-out cases. Record failed trials and analyst/setup expense.

Normal Codex uses the built-in provider. Capture/compression remains **opt-in** after
the preserved startup recovery; this work does not re-enable it globally.

Private metadata receipts, native logs, frozen source, grades and full audit results
are under ignored `work/security/harness-optimization-20261106/`. Public documents
contain aggregate findings, not private histories or credentials.


## 7 November continuation

The pending independent-read batching block is complete: all six checks pass,
308,046 → 265,627 native tokens (13.7703% fewer), two pair wins. Its added
cache-aware audit is 3.20342 → 2.66323 published Standard Codex scenario credits
(16.8629% fewer). Original token gates are preserved; future selection uses total
quality-constrained inference cost. No global prompt/provider change is made.

The active context/memory program is now tracked in the filesystem
[progress register](../../../docs/research/context-memory-experiment-progress.md)
and [scientific manuscript](../../../docs/paper/context-memory/report.md).
Chronological generated diagnostics, preserved setup failures, exact Langfuse
reconciliation, local Mem0 integration, the current LongMemEval development
continuation and held-out reservations are recorded there. Do not start another
batching block, duplicate the active LongMemEval worker or resume the paused
research heartbeat. This queue's remaining proposals are still proposals.
