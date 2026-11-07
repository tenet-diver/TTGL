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


### Startup recovery, 5 November 2026

After a reported provider-related failure in another Codex session, the local
installation was changed to use the built-in `openai` provider by default and in
`ttgl-observability`. The analyst MCP remains installed. The earlier experiment
measurements and raw captures are preserved, but their successful CLI trials do
not establish compatibility with every Codex client or session-resume path.
Capture/compression is now opt-in through `codex -p ttgl-capture-experimental`
or `codex_traced.py`; `configure-codex` preserves this boundary. The `--policy off`
option controls transformation on the experimental route, not native-provider
restoration. Existing sessions may retain their earlier provider selection;
restart with the built-in provider explicitly if necessary.

The follow-up startup investigation found that CLI 0.166.0 rejects an owned named
profile file when the same name also exists under the legacy `[profiles.*]` table.
The named analyst profile additionally retained the capture provider, overriding
the recovered global default. Setup now generates an OpenAI analyst profile and
migrates the two owned legacy tables to named files. The experimental capture
profile remains explicit. Six setup checks pass. Two pre-inference configuration
failures were retained privately; the second came from unsupported command-local
retry overrides for the reserved built-in provider. Removing those overrides lets
the analyst start on native transport, whose own retry defaults still apply.

### Native analyst usability follow-up

A new native-provider analyst completed 14 TTGL product calls and four source
inspections. MCP queries and evidence reads worked. CLI schema discovery worked;
data queries failed under the read-only shell because Store initialization writes
local bookkeeping. This is separate from gateway availability. The analyst
observed repeated identical 65,542-byte evidence wrappers and a turns query that
ignored its limit and included full prompts. It switched to scoped event pages,
bounded previews, direct source IDs and local field projection during the run.
Its native completion reports 221,735 input tokens (194,560 cached subset) and
2,313 output tokens: 224,048 total, recorded as analyst overhead, not savings.

The observed turns issue is fixed: offset/limit now apply, summary omits prompts,
and detail=full preserves access. Twenty-two workspace tests and six setup tests
pass. The standard agent_review runner also uses the native analyst profile
instead of forcing the experimental gateway. Historical trials are unchanged;
this usability check is not a matched token-saving experiment.

A separate native analyst verification then successfully queried data through both
CLI and MCP: limit=1 returned the same single turn, omitted prompts, and exposed
next_offset=1. CLI output was 652 bytes including its newline. It used two product
calls and independently checked the prior analyst native completion counters.
CLI local bookkeeping required workspace-write access. The current analyst was
not established as MCP-indexed; current-session coverage remains a limitation.
Verification native usage: 106932 input (including 96256 cached) plus 1047 output tokens, additional analyst overhead.

### Continued analyst context loop

Two further observed analyst sessions proposed and verified exact session scoping
and compact task discovery. Session queries now intersect task/project scopes;
refresh=true incrementally ingests authorized native logs and respects collection
pause. Explicit coverage distinguishes missing indexed records from zero inference.
Task pages omit goal/acceptance/outcome by default; detail=full preserves them.
The standard analyst prompt now describes these retrieval choices. No gateway or
schedule change was needed.

The first registered matched retrieval pair failed both task-list calls because
the model sent integer pagination values to the string-only interface. Both failed
attempts and their 129,042 native tokens remain preserved. Pagination schemas and
validation now accept integers or strings, rejecting booleans, floats and invalid
ranges. This was a usability failure, not a successful optimization comparison.

A separately registered corrected pair, analyst-interface-002, reversed condition
order and used the same frozen 29-task records and prior analyst session. Both
gpt-6.1-sol runs made exactly two successful MCP calls and returned all five
expected facts correctly. Native indexed counters reconcile exactly with CLI
completion usage; task records and implementation hashes remained unchanged.

| Corrected condition | Input | Cached subset | Output | Total | Quality |
|---|---:|---:|---:|---:|---|
| Full task records | 87,201 | 67,328 | 203 | 87,404 | 5/5 fields |
| Compact task records | 81,163 | 64,384 | 232 | 81,395 | 5/5 fields |

Observed whole-run reduction: 6,009 native tokens, or 6.875%, on ONE existing-data
analyst retrieval task. Full versus compact discovery payloads were 24,319 versus
11,180 bytes with identical task IDs. This is reused development evidence with
explicit query forms, not a coding benchmark, general quality guarantee, latency
result or cash/net saving. Full/raw evidence remains accessible.

The two proposal/verification sessions consumed another 246,656 and 79,767 native
tokens. Including the failed and corrected pairs, this continuation's observed
spawned-agent overhead is 624,264 tokens. Parent implementation/supervision usage
is additional and not included: there is no demonstrated net research saving.
Private protocols, source snapshots, final responses, native events, evaluations
and reconciliation receipts are under work/security/analyst-self-review/.
Forty-five observability tests pass. Research schedules remain paused.
