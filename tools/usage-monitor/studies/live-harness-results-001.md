# Live Codex compression — implemented and measured

As of 5 November 2026, **new local Codex CLI sessions use live tool-result
compression before model inference**. This includes ordinary `codex`, the real
`ttgl-observability` profile and `codex_traced.py`. The running managed chat and other
machines are outside this installation. The local proxy and six-service Langfuse
stack remain running.

This supersedes the earlier analysis-only implementation: no special evidence-view
request or agent-selected command wrapper is needed for eligible ordinary shell results.

## Where the change runs

Normal shell tool → Codex's model-facing result → existing loopback proxy → selected
text transform → upstream model request. Original request, forwarded request, hashes,
policy, transform time and call IDs are retained. Tool arguments, exit status, source
files, system/user prompts and reasoning are unchanged. Native provider response usage
counts the actual forwarded context. HTTP byte reductions are separate measurements.

The progress filter removes only exact transient Docker layer updates. Actual Headroom
functions `search_heading`, `search_dir_heading` and `collapse_runs` provide reversible
search/log folding. Each attempted lossless fold must round-trip exactly; explanations
are included and non-beneficial/unknown shapes pass through. We do not strip ANSI,
truncate source/code, drop JSON rows, invoke summarizing models or run Headroom telemetry.

Changed pre-proxy tool text is addressable by SHA256 through
`read_compression_source`, whose marked raw retrieval bypasses compression. Retention is
redacted/bounded; this cannot recover output already clipped by the CLI before the proxy.
Deterministic transforms recur in request history; six transformation records in the
coding trial represent **two distinct original outputs**, not six separate opportunities.

## Measured normal coding work

Registered [protocol](live-harness-protocol-001.json), two generated development tasks,
one matched pair per task, alternating condition order. Both arms used the same prompt,
model (`gpt-6.1-sol`), CLI (`0.166.0`), initial app/tests and ordinary shell/edit tools.
Agents actually changed `app.py` and ran tests. No replay MCP or `read_evidence` view
was involved. No retries or replacement attempts occurred.

| Actual task | Raw native tokens | Live compact tokens | Raw seconds | Compact seconds | Checks |
|---|---:|---:|---:|---:|---|
| Calculation repair with long search results | 110,130 | 102,847 | 19.977 | 20.452 | Both pass |
| Retry-policy repair with repeated worker logs | 102,057 | 87,962 | 19.388 | 18.945 | Both pass |
| **Total** | **212,187** | **190,809** | **39.365** | **39.396** | **4/4 runs** |

Whole-task native token reduction: **10.075%**. Each task individually used fewer tokens.
Input totals were 211,503 versus 190,123, including cached subsets of 173,952 versus
159,872; output was 684 versus 686. Cached input is counted once. All requests, additional
calls and model outputs are included. Cash expense and subscription quota impact are unknown.

Each run preserved its tests/fixtures and passed visible plus separate post-run checks
(12 quality checks across four runs). This small generated development sample is not a
benchmark or proof of broad coding quality. The task briefs required an initial diagnostic
command, so gains cannot be generalized to workflows that already make narrower reads.
No speedup was observed; transformation time summed to about 17.5 milliseconds. Raw model
latency remains unknown. [Machine-readable measurements](live-harness-results-001.json)
include per-cell usage, quality, request-byte totals and source fingerprints.

## Installation proof and analyst behavior

- A live command canary reduced one actual tool-result field from **27,134 to 381 bytes**
  while preserving its warning, pinned digest and successful status.
- Plain `codex exec`, without provider overrides or an analytics-view tool, exercised
  the installed progress default and returned those facts correctly.
- After the measured gate and analyst keep verdict, the reviewed lossless policy became
  the default. A second plain CLI check ran `rg` against real files, correctly reported
  all 121 matches and the first/last facts, and captured a reversible transform of
  **36,944 → 15,521 bytes**. It is installed in the working-agent path.
- Analyst 001 discovered the project, inspected registered case-level measurements,
  native edit evidence, HTTP compression metadata and retained original sources, then
  recorded **keep**, limited to the demonstrated development result. It distinguished
  repeated history presentations, bytes, native tokens, timing and missing overhead.
- Analyst 002 ran after installation. It verified current configuration and normal-CLI
  captures, inspected remaining large-output signals, and concluded that another
  proposal would duplicate the search/log patterns already treated. It saved no
  unsupported experiment and claimed no speed/cash/net savings.
- The first analyst unnecessarily fetched an unscoped experiment payload around 94 KB.
  Compact discovery now returns about **1.7 KB** rather than **97 KB** on the same
  current database; scoped `detail=full` preserves all measured evidence. This later
  interface change is not included in the coding trial's 10.075% result.

Observed analyst calls, final answers, native rollouts, fixtures, repaired apps,
operator checks, captures, source blobs and screenshots stay under ignored
`work/security/live-harness/`. The public aggregate contains no raw private transcript.

## Source and dependency review

The full Headroom distribution is not installed. We use its Apache-2.0
[lossless module at pinned commit 2d3ee518](https://github.com/headroomlabs-ai/headroom/blob/2d3ee51846435ef5b320eea4806af14e602b0d8c/headroom/transforms/lossless_compaction.py),
with the relative logging import changed to a small local content-safe adapter.
The module and adapter use Python's standard library. Package initialization, the
SmartCrusher native extension, LiteLLM, tokenizer/ML dependencies, proxy server,
network telemetry, automatic scripts and model downloads are excluded.

[Pin and reviewed file hashes](../config/headroom-subset.lock.json), license and notice
are committed. The installer/doctor verify them. OSV commit lookup reported no findings;
one public advisory, [GHSA-h46j-26q3-rggf](https://github.com/headroomlabs-ai/headroom/security/advisories/GHSA-h46j-26q3-rggf),
affects excluded WebSocket proxy handling. This is not a security clearance of the full
upstream package. No third-party package/image installation was performed for this work.

The existing Codex provider configuration is the supported integration point; see the
[official OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
No hook-trust bypass is installed. New global settings preserve unrelated Codex TOML,
keep a first private backup and reuse the existing login. Transport request encoding
compression stays disabled; this is **context compression**, not HTTP gzip.

## Cost of the research

Accrued snapshot **2026-11-05T21:44:47.136796+00:00**, while implementation is active:

| Component | Native tokens |
|---|---:|
| implementation and supervision | 11,322,598 |
| installation verification | 121,750 |
| matched coding trials | 402,996 |
| analyst evaluation | 406,473 |
| **Current live-harness research** | **12,253,817** |
| Earlier frozen replay/usability ledger | 7,085,151 |
| Combined accrued count | 19,338,968 |

Mean observed saving is **10,689 native tokens per development coding task**. Dividing
this cycle's accrued tokens by that mean gives **1146.4 similar tasks**;
including the earlier ledger gives **1809.2**. These are illustrative
unweighted token-count amortizations, not cash break-even, forecasts or quota estimates.
Research has **no net first-use saving**. Cached tokens, human time, operating costs,
future model variability and the tiny sample prevent a monetary ROI claim. The ledger
is available in the Experiments dialog and via `section=experiment_accounting`.

## Operate and inspect

```sh
# Reproduce the installed provider/MCP settings; local stack must be running.
python3 tools/usage-monitor/observability/setup_local.py configure-codex
codex

# Disable transforms while retaining request/response capture.
python3 tools/usage-monitor/observability/install_live_codex.py --policy off

# Restore the reviewed policy.
python3 tools/usage-monitor/observability/install_live_codex.py --policy headroom-lossless

# Inspect measured experiments and raw sources.
ttgl query_activity --args '{"section":"experiments"}'
ttgl query_activity --args '{"section":"experiments","project":"9b5b22837e414a11bbbf081a712f4eaa","detail":"full"}'
ttgl read_compression_source --args '{"sha256":"SOURCE_SHA256","limit":"4000"}'
```

The UI Activity table links original/forwarded live compression observations.
Langfuse receives additive `codex-compression` spans with no extra usage; existing
transport receipts remain unchanged. API v2 observations and a real logged-in browser
confirmed the compression record. Legacy trace API reads are unavailable in this v4
`events_only` deployment; the UI trace link works. Collector errors were empty.

Verification: **40 observability tests + 24 exporter tests**, JavaScript syntax, ready
setup doctor, real default CLI checks and Chromium views of live results/capture links.
Further claims should use preregistered fresh diverse tasks with independent quality
checks and repetitions. Both earlier failed evidence and successful development results
remain preserved; no inference schedule was enabled.
