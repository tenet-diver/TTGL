# Local Langfuse deployment

As of 4 November 2026, Langfuse is the primary session replay and tracing UI. Use the maintained official Codex converter instead of adding a custom trace parser or UI.

- Sessions: http://localhost:3000/project/ttgl-codex/sessions
- Tracing: http://localhost:3000/project/ttgl-codex/traces
- Historical aggregate usage and reviewed suggestions: http://127.0.0.1:8766

Six services run in Docker Compose project `ttgl-langfuse`: Langfuse web/worker 4.75.0, PostgreSQL 17 Alpine, Redis 7 Alpine, ClickHouse 26.3.62.3 Alpine, and SeaweedFS 4.52 providing S3 storage. All images are pinned by digest in the private deployment file. Secrets and private imports are under `~/Library/Application Support/TTGL Langfuse`; never commit or print its `.env` or `local-access.json`. Backend containers have no Codex directory or Docker socket mounted. Published UI/S3 ports bind only to loopback. Database/queue services have no host ports. Outbound isolation is not guaranteed; a web-container outbound test succeeded. Telemetry is disabled.

Start/stop with Docker Compose using that directory's `docker-compose.yml` and `.env`. Restart policy is unless-stopped; Docker Desktop must run. Preserve volumes when stopping. The service named `minio` uses SeaweedFS, not MinIO.

The official `@langfuse/codex-observability-plugin` 0.4.3 package signature and SLSA provenance were verified against source commit `e1d02be28e6bacbfe350a1bc1ccf861e54edee17`. The installed runtime bundle matches the verified npm package. The host hook uses existing Node 24.22.2; backend software runs in containers. Codex features.hooks is enabled and the local plugin/config is installed. **Live capture needs a Codex restart and user review/trust of the vendor Stop hook through `/hooks`. Never bypass hook trust.**

In the initial full-transcript pilot, two actual sessions, four completed turns, were imported using the vendor converter on copied rollouts. Both appear in the native Sessions UI with tool/generation observations. This is a bounded pilot, not a full historical trace backfill. Original histories remain unchanged. Imported timing is reconstructed from retained logs, not independently measured provider latency. UI cost is an estimate, not subscription billing. The companion ccusage baseline covers broader retained history.

Security review used OSV Scanner 2.3.3. Selected web/worker/Redis/ClickHouse scans returned no advisory groups; PostgreSQL contained 60 unscored groups and one scored 5.5 group, largely in its gosu helper; SeaweedFS contained five unscored groups. The plugin source lock had nine advisory groups, including bundled Zod 4.6.5 memory exhaustion; reviewed use validates small private local configuration, which limits exposure but is not a patch or reachability proof. Container image attestation verification was blocked by registry rate limiting. Digest pinning and npm provenance do not prove absence of a supply-chain attack. Re-scan before updates; do not describe this stack as vulnerability-free.

Official integration: https://langfuse.com/integrations/developer-tools/codex
Official plugin: https://github.com/langfuse/codex-observability-plugin

AI Observer and its feed/projection LaunchAgents are stopped. Their old usage-only projection omitted tool and conversation details. Retained adapter files are historical, not the primary deployment.

The user prioritizes token/cost breakdown and time breakdown. Native dashboard: http://localhost:3000/project/ttgl-codex/dashboards/cmw2k9kd90003p61tatyoxvn6 (Codex Token and Time Breakdown). It ranks sessions by generation tokens, model input/output and estimated API cost, tools by summed latency and p95, and generation duration separately. Respect the selected time period and imported coverage. Input includes cache reads; high token volume is not equal to high cost. Summed tool/model durations may overlap and do not equal elapsed session time. Wrapper names such as exec obscure underlying tools. Exact per-tool model-token attribution and a non-overlapping wall-time decomposition remain unavailable. Prioritize fixing those data gaps before adding more UI.

## Broad metadata analytics (4 November update)

`bridge.py` fills the missing Codex native-event support in the official converter. It reuses the existing read-only rollout reader, streams compressed archives, and sends OTLP/HTTP JSON to **localhost only** using Python's standard library. No packages or additional UI were installed. Original transcripts remain unchanged. The vendor plugin still serves detailed replay in `local`; it is excluded from the aggregate analytics.

The existing [Token and Time Breakdown dashboard](http://localhost:3000/project/ttgl-codex/dashboards/cmw2k9kd90003p61tatyoxvn6) is configured by `configure_dashboard.py`. It has native tool frequency/total time/p95, argument pattern frequency, measured model/daily tokens, cached/fresh/output buckets, API-equivalent price scenarios, and lifetime session ranking.

Datasets are intentionally disjoint:

| Environment | Records | Intended use |
|---|---|---|
| `usage-tools` | Native completed tools plus derived argument-shape events | Actual underlying tool names, frequency, known timing, argument patterns |
| `usage-daily-v3` | Positive day/model counter increments from ccusage | Model/token/cost breakdown and calendar-day trends; Europe/Amsterdam |
| `usage-sessions-v2` | Positive session/model counter increments from ccusage | Whole-session ranking, selected by last activity; not per-day allocation |
| `local` | Official plugin detailed replay | Conversation investigation; not added to analytics counters |

**Never sum daily and session datasets.** They are alternative aggregations of the same usage. Each widget has the appropriate environment filter; leave the dashboard-wide environment selection inclusive. Bucket charts show `total` as a reference bar, not an extra bucket. Cached input and output reasoning are subsets, not additional provider calls. Aggregate source reasoning can occasionally exceed its model-row output total; that invalid subset is explicitly flagged, not subtracted into a negative output. v2 usage exports inclusive output plus separate metadata about the reasoning subset.

Tool completion IDs deduplicate repeated native events. In files with native tool evidence, wrappers are omitted to avoid counting a batch and its children as separate calls. Older files without native completions retain their original opaque tool names and unknown duration. Parent replay and events belonging to other thread IDs are excluded. Unknown duration is a zero-width record marked `timing_known=false`, excluded from duration widgets; it does not mean instantaneous execution. Native tool time can overlap across calls and is not session wall time. Tool roots are structural first-to-last intervals, excluded from timing totals. No model latency is invented for usage-summary observations.

Argument summaries retain key names, size buckets, command families and allowlisted program names. Only explicitly safe enum/numeric options (such as compact/full and result limits) retain values. Query text, arbitrary values, source code, credentials and paths are not exported by this bridge. One derived zero-duration EVENT per actual tool makes shape frequency chartable without misrepresenting it as another TOOL. Full tool I/O is still available only where the official replay plugin imported it. No per-tool token estimate is produced: all token records identify measured model counters; byte sizes are not tokens.

Langfuse v4 observations are immutable: re-sending the same ID can inflate aggregate metrics. The adapter records successful sends, skips completed tool IDs even if attributes later change, and exports only positive counter increments with new IDs. It journals each outgoing batch before network I/O; an uncertain response must be verified against the backend before proceeding. Missing/duplicate backend receipts block automatic replay. Counter decreases also block export pending reconciliation. Initial `usage-daily` / `usage-daily-v2` / `usage-sessions` canary snapshots are retained for diagnosis and excluded from production widgets; do not include them in totals.

The local `analytics/export.sqlite` ledger and `analytics/status.json` live under the private Langfuse directory. Keep the ledger with its backend volumes: deleting receipts then re-importing can duplicate immutable observations. The `local.ttgl.langfuse-analytics` LaunchAgent refreshes metadata every three minutes, alongside the existing ccusage report refresh. It requires Docker Desktop/backend availability, does no inference and does not alter the paused research heartbeat. Stop with `launchctl bootout gui/$(id -u)/local.ttgl.langfuse-analytics`; preserve receipts and backend volumes.

Run a manual pass (stop the owned LaunchAgent first; the exporter takes an exclusive lock):

```sh
python3 bridge.py --monitor-data "$HOME/Library/Application Support/TTGL Usage Monitor/data" \
  --credentials "$HOME/Library/Application Support/TTGL Langfuse/local-access.json" \
  --state "$HOME/Library/Application Support/TTGL Langfuse/analytics"
```

Tests cover parent/wrapper exclusion, native identity, privacy summaries, unknown timing, disjoint usage buckets, immutable receipts, ambiguous delivery and incremental counter accounting. Validate remote Metrics API totals against the cursor ledger and inspect backend uniqueness before publishing a backfill claim. API costs use Langfuse's model-price catalogue at ingestion, not verified historical invoices, cash subscription expense or remaining quota; absent model pricing means unknown cost.

References: [OTLP/JSON and attribute mapping](https://langfuse.com/integrations/native/opentelemetry), [v4 immutability](https://langfuse.com/faq/all/tracing-data-updates), [native custom dashboards](https://langfuse.com/docs/metrics/features/custom-dashboards).

Daily counter records use a UTC calendar-date label to keep the chart axis aligned with the Europe/Amsterdam source day. Their timestamp is a day label, not a provider-call timestamp. Whole-day rollups cannot answer hourly usage questions.

## Runtime correction and actionable groups

The initial `usage-tools` span timestamps used `started_at_ms` to `completed_at_ms`. A forensic audit found that this lifecycle window can include delayed completion or process bookkeeping and substantially exceed the native `item.duration`. **Do not use those lifecycle spans as measured execution latency.** Frequency, argument shapes and token counters are unaffected.

`runtime_enrichment.py` imports corrected timing into `usage-runtime-v2`, using only the explicit Rust Duration (`secs`, `nanos`) from native completed items. It preserves the old event window as diagnostic metadata and reconstructs a display start from the known completion time minus reported runtime. Unknown duration is excluded instead of inferred. These records describe process/tool runtime, not time blocking the agent or full-task elapsed time; parallel and background processes can overlap.

The two timing widgets now use only `usage-runtime-v2`. Shell calls are grouped by conservative top-level command classification (test framework, build, git operation, search, file inspection, scripts, servers and network). Embedded here-document code is not scanned as if it were shell commands. A mixed command batch retains one duration; its time is not allocated to every constituent command. Script bodies and arbitrary paths/values are not exported. Chat operations are labeled list/read/wait/create, and outcomes are separate. The completed-operation table shows count, median and p95; timeout/failure rows stay in the overall runtime ranking. Small samples and outliers require inspecting evidence before proposing changes.

Concrete audit examples: a failed xcodebuild record had a lifecycle window of 175,353.470 seconds but an explicit runtime of 357.968724629 seconds. A recorded `codex_app.list_threads` failure had an event window of 4,848.832 seconds and native runtime of 3,600.024119641 seconds, with a timeout error. This is evidence to investigate that timeout, not to infer that ordinary chat listing generally takes an hour. Existing lifecycle data is retained for diagnosis; corrected immutable records have their own IDs/environment and are never added to it for timing totals. The local `runtime_files_v2` receipt index ensures one correction pass per source snapshot, then incremental refreshes.

Operation labels are conservative static summaries, not profiling inside Python/Node scripts. Shell parsing skips here-document bodies and preserves later commands; multi-operation batches show their constituent categories with one shared duration. Unrecognized or ambiguous shell syntax remains unclassified. A nonzero exit / `failed` tool status is not proof that the user's task failed (for example, a deliberate server stop or expected negative check). Review the source evidence before classifying time as waste. The initial `usage-runtime-v1` grouping canaries are retained and excluded; production timing widgets use `usage-runtime-v2`.


## Runtime distributions

The user chose distribution metrics instead of excluding outliers. Primary timing widgets now show median runtime by operation/outcome and a table with count, median (p50), p95, p99 and maximum. All recorded outcomes remain included; failures are separate named groups, not removed. No minimum-count cohort or per-call clipping applies. Rare groups remain visible and percentiles must be read alongside sample counts. The briefly created recurring-cohort profile is disabled; its hourly refresh is removed. Existing full-data dashboard records remain available. Token/cost charts are unchanged.
