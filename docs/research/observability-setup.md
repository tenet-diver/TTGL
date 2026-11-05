# Single-device observability setup

Current scope, 5 November 2026: consolidate history and continuously collect future records from TWO MacBooks and cloud runs into ONE central analysis stack. Each source needs only appropriate capture/export components with offline queues, not its own full stack. The latest explicit user instruction now authorizes live Codex compression and continued analyst-led experiments; the earlier deferral is superseded. Data quality, provenance and the current Codespace vulnerability rule still apply. The sections below describing one-machine-only scope or merely optional remote imports are superseded by this current scope.

## Live harness update — 5 November 2026

Live tool-result compression is installed for new local Codex CLI sessions, including
plain `codex`, through the existing proxy. It runs before upstream inference and retains
original/forwarded requests plus source hashes. The reviewed Headroom stdlib-only
lossless module is pinned and vendored without installing its complete package.

A four-run matched code-edit-and-test development study used 10.08% fewer pooled native
tokens; all visible/independent checks passed and wall time was unchanged. The analyst
reviewed and kept the bounded candidate; another verified default-route captures and
found no justified additional change. This is not broad coding/cash/first-use savings.
See [results](../../tools/usage-monitor/studies/live-harness-results-001.md) and the
usage-monitor README for install/rollback and measured research costs. Other machines
and the current managed chat are not reconfigured. Existing inference schedules stay paused.

## Latest Codespaces deployment — running

The compact workspace now uses the private EVLV plain-DOM distribution (producer
commit and hashes in `config/design-system.lock.json`). Shared assets remain in
the ignored private state directory because the producer forbids public
redistribution. Consumer layout uses dense tables, local search/sorting/pagination,
accessible shared row menus and add/edit dialogs. See the usage-monitor README
for authenticated sync and browser verification.

A subsequent audit corrected an earlier capture claim: the first six model HTTP
exchanges have retained requests and byte/timing metadata, but no retained raw
response bodies. The old Content-Type-dependent parser discarded octet-stream
SSE; those missing bodies are unrecoverable from the capture files. They are now
shown as partial historical coverage, with session/time correlation explicitly
inferred. Schema-2 capture parses SSE regardless of Content-Type and retains
provider response IDs. A new real canary verified correct body retention and
exact ID correlation. Native transcripts remain distinct from proxy evidence.

Selected task/project/category totals are now displayed alongside all-source and
unassigned totals. The reconciliation endpoint queries the same Langfuse native
generation scope and includes the first retained response across the Metrics API
time boundary. A stable live check reconciled all-source totals exactly; active
generation/ingestion lag can still create temporary differences.

The user clarified that Codex itself should perform the analysis rather than
requiring the user to interpret fallback category charts. An actual read-only
Codex CLI review has now been run against a frozen private snapshot and published
in the workspace's **Codex analysis** view. Agent annotations carry evidence IDs,
rationale and confidence, and distinguish finite operations from background
service lifetime. They are separate versioned interpretations; original native
records and Langfuse observations are preserved. Findings include concrete
recommendations and validation plans, not measured savings. Analyst-native usage
is recorded separately and its turns assigned to a separate task. The reproducible
runner is `observability/agent_review.py`; subsequent runs are incremental unless
`--full` is explicitly selected. No scheduled model calls were enabled.

Reproducible configuration is now checked in under
`tools/usage-monitor/config/`: the active deployment lock, secret-free Compose
template, runtime defaults, Codex provider TOML and analyst MCP template.
`observability/setup_local.py` prepares private files, explicitly downloads the
fixed images when requested, checks installed versions, registers MCP, installs
the owned `ttgl-observability` user profile, starts the supervisor and configures
the dashboard. See the linked usage-monitor README for the complete sequence.
The template was verified to reproduce the existing private Compose document
exactly while retaining its credentials. Runtime data remains outside Git.

The user explicitly authorized installation/execution in this Codespace unless
confirmed vulnerabilities are present. This supersedes the earlier stop on
incomplete reviews for this environment only. The existing Langfuse app candidate
has incomplete review coverage, not a security clearance. Rejected CLIProxyAPI
and mitmproxy candidates remain unused; LiteLLM is not installed.

Langfuse 4.75.0 web/worker, PostgreSQL, Redis, ClickHouse and MinIO now run in six
digest-pinned containers. MinIO is the S3-compatible object store; its digest is
`sha256:cee9a8e35885e93f14b3cb32960e5017aff74e2adfb52ba87c65003b0163886b`.
Ports 3000, 9090 and 9091 bind to loopback; Codespaces forwarding is private.
Databases are network-internal. Health, authenticated login, S3 object creation,
public v2 observation ingestion/query, and all eight native dashboard metric
queries have been observed working. Use the v2 Metrics API: v1 is unavailable in
this deployment's v4 events-only mode.

Native turns, operation inputs/results and per-response measured usage are
continuously exported, with durable immutable receipts and exact IDs. A real
Codex CLI canary also completed through a standard-library HTTP/SSE capture
adapter, returning `TRACE_CANARY_OK`. Its single `/responses` exchange returned
HTTP 200, captured 81,747 request bytes and 96,328 response bytes without capture
truncation, took 2.367 seconds end-to-end and 0.922 seconds to first body byte.
Those are transport observations, not pure inference latency or an efficiency
result. Two `/models` fetches were also captured. Proxy records carry no extra
token usage; native generation records remain the accounting source. Headers,
credentials and opaque reasoning fields are excluded from stored captures;
body redaction remains best effort. Existing chat traffic is not retroactively
proxied. `codex_traced.py` enables HTTP/SSE capture on new explicit CLI launches.

The task/project workspace runs on 8766. A supervisor owns its importer, capture
adapter and Langfuse exporter; its private `runtime.json`, logs, credentials,
capture files, SQLite database and export receipts live under `work/security/`.
The `ttgl-analyst` local stdio MCP server is registered for new Codex CLI sessions.
See `tools/usage-monitor/README.md` for operation, feature boundaries and restart.
No other-machine histories or paused research schedules were activated. Native
subagent identity/parent capture needs a dedicated live validation before claiming
complete cross-subagent coverage.

## Intended flow

### Cloud preflight and native baseline, 5 November 2026

The user clarified that the primary objective is optimizing Codex task time,
performance and cost efficiency; Langfuse remains the intended visualization
backend, while CLIProxyAPI may be replaced. Capture must support decisions about
context growth, repeated work, model latency, cache use, tool runtime, retries and
task outcomes. Raw pairs alone are insufficient, and lower token counts alone do
not establish an improvement.

The cloud checkout is on `work`. Docker responds, but no images are present and
no stack has been started. Fresh metadata-only checks found advisory results for
CLIProxyAPI v8.0.57 and for Tornado 6.5.10 in mitmproxy 12.3.1's resolved 41-package
wheel graph. These are candidate rejection evidence, not complete artifact or
exploitability reviews. Receipts are in `tools/usage-monitor/observability/`.
LiteLLM was also evaluated; its publisher reports an October 21 compromised
1.107.0 release. It has not been installed or cleared. None of these checks
clears the separate Langfuse stack review.

`tools/usage-monitor/observability/baseline.py` provides a standard-library-only,
read-only baseline from one retained rollout, reusing the existing native tool
reader. It deduplicates response IDs, excludes foreign-thread events, flags
conflicting usage, reconciles per-response counters against native thread totals,
and reports native tool-runtime distributions. Legacy token-count events can lag
the newer response records; their residual is reported separately. Cached input
and reasoning output remain subsets. Unknown cash cost and task outcome remain
null. Private snapshot output from this chat is under
`work/security/observability/own-run-baseline.json` (ignored by Git).

This is real transcript-derived evidence from the active cloud session, not raw
wire capture, a completed task result, a deployed visualization or proof of
savings. Model latency/time to first token and wire retry coverage remain missing.
No normal Codex routing, credentials or paused schedules were changed.

Codex -> CLIProxyAPI -> the configured model provider.

Langfuse is the analysis/replay UI. Preserve transcript-derived session/tool records and richer proxy capture records as distinct sources, correlated when possible. This is one local Docker Compose deployment with separate containers for Langfuse web/worker, PostgreSQL, Redis, ClickHouse, object storage and CLIProxyAPI, not one combined privileged container.

Historical transcripts go through a transcript importer. A proxy only captures future traffic that actually traverses it. Do not rerun old prompts to manufacture historical captures.

CLIProxyAPI does not automatically send its request-log files to Langfuse. A reviewed exporter is still required. First check maintained integrations; otherwise build only the missing adapter. Write through Langfuse's public ingestion API/OTLP, never directly into its managed ClickHouse tables. This document does not claim that exporter exists or is deployed.

Keep private raw capture bodies in private object storage or an isolated bounded local capture volume, with searchable metadata and references. Selected request/response generations, measured usage, timestamps and references can appear in Langfuse. Keep transcript and proxy source labels and prevent double-counting the same model call.

## Current security gate: BLOCKED

No application container was run, authenticated or connected to Codex during this preflight.

The release check resolved Langfuse v4.75.0 and CLIProxyAPI v8.0.56. On the reviewed linux/amd64 images:

- CLIProxyAPI: OSV Scanner 2.3.3 with all vulnerabilities/packages enabled reported 104 advisory IDs across 46 package entries, including Go dependencies and Debian 12 packages. IDs can include aliases; this is not a claim of 104 independently exploitable defects. The image is blocked.
- Langfuse web: the same scanner reported zero findings, but detected only three Go packages. This is not adequate coverage of its Node dependency graph or UBI/RPM base and therefore is not a security pass.
- Langfuse worker, PostgreSQL, Redis, ClickHouse, object storage, importer and capture exporter still need complete current review.
- Registry digests were resolved, but publisher provenance/signature review and all required artifact evidence are not complete. Digest matching alone does not establish a clean publisher or artifact.

Read docs/security/dependency-security-policy.md. Do not start these images, install a scanner without its own review, bypass findings by disabling scan categories, or infer an exception from this setup request. Resolving a patched image/version creates a new graph and requires a new receipt.

Known application advisory GHSA-4w5v-m7vx-jpmh was patched before v8.0.56, but that does not clear the image's other dependencies.

## Before deployment

1. Produce a complete runtime inventory including the base OS, application dependencies, Go embedded modules and automatically downloaded tools/components. Use metadata/download-only operations; do not execute a candidate image to inspect it.
2. Resolve exact immutable image digests, verify release/publisher identity and available signatures/provenance, review entrypoints and all auto-execution/download paths, and query fresh advisories for every component.
3. Record the exact graph/artifact hashes, coverage, sources, findings and uncertainty. Every required check must pass with no known findings before installation or first execution.
4. Configure host-only UI/API ports, dedicated named data/auth/capture volumes, no Docker socket or home/credential-store mounts, no privileged containers, non-root where supported, dropped capabilities, resource caps and bounded logs. Keep databases private to the Compose network.
5. CLIProxyAPI's container listener must accept Docker-forwarded traffic internally, while the published host binding remains 127.0.0.1. Set API authentication, disable remote management and automatic control-panel/plugin downloads, cap request size appropriately, and explicitly enable request/response logging only after redaction tests.
6. Langfuse needs independently generated local application secrets and a project-scoped ingestion identity. Disable telemetry and unused model/evaluation features. Do not place real credentials in this public repository.
7. Set conservative total Docker CPU/RAM limits appropriate to the machine. Do not claim that putting services in containers reduces their total memory needs.
8. Use image pull policy never for startup after reviewed artifacts are downloaded. No automatic upgrade, package lifecycle install or first-start downloader may introduce unreviewed code.

## Validate before routing real prompts

Use synthetic text and planted-secret canaries, not real credentials. Verify non-streaming, SSE and supported WebSocket request/response captures; errors, cancellations, retries and compaction; downstream versus translated upstream bodies; and model/tool capabilities. Preserve capture-stage, truncation and missing-frame flags.

Verify that authorization headers, cookies, OAuth/refresh tokens and API credentials never reach normal/error capture files or Langfuse. Prompt/tool bodies may themselves contain secrets; redaction is not a guarantee. No raw private reasoning is requested or reconstructed. Any opaque provider reasoning state must be treated as non-display protocol data, not decoded or published.

Compare proxied versus direct behavior, model selection and provider usage on the same harmless canary. Check cache and latency effects rather than assuming routing is transparent. Do not aggregate duplicated proxy/transcript token counters.

Only after these checks should an explicit Codex provider configuration route requests to http://127.0.0.1:8317/v1 using Responses API. Validate that this Codex build supports the configuration, authentication and relevant model/tool features first. Do not change normal user configuration while the image gate is blocked.

Retain native Codex transcripts for full tool/session structure. Proxy captures alone do not prove every local action or provide historical replay. The official Langfuse transcript plugin/importer has its own dependency and hook-review requirements and must not be silently installed on the host when the agreed runtime is containerized.

## Historical import

Inventory current and archived retained rollout files without modifying them. Treat index-only entries, deleted sessions and remote-only history as missing until recovered. Keep private manifests and original IDs, timestamps, hashes, importer version, source labels and delivery receipts.

Start with a small sample, inspect its session replay and native tool names in Langfuse, reconcile measured tokens, and import it twice to demonstrate idempotency. Then import retained history in bounded resumable batches. A new Langfuse database needs a new import ledger; a ledger from a deleted backend is not proof the new backend received events.

Do not upload source histories or credentials to the public TTGL repository. Preserve source originals and private audit/experiment records independently of Docker volumes.

## Historical imports from other machines and cloud sessions

The single-machine deployment is the destination, not a restriction on where sessions originated. Accept on-demand bundles from other machines and supported cloud session exports alongside this machine's retained history.

Each source should export only the explicitly selected session records and a private manifest containing:
- a stable pseudonymous source ID and source kind (local, other-machine, cloud);
- original session/thread IDs, turn/tool-call/request IDs where available, original timestamps and timezone;
- exporter/client versions, format/schema, per-file SHA-256 hashes, byte counts and record counts;
- scope and completeness flags, redaction version, truncation/errors and missing/unavailable records.

Exclude auth/config credential files, environment dumps, cookies, SSH keys, provider tokens and unrelated home/project files. Never infer that a cloud task's final answer or terminal log is a complete model trajectory. Export only through supported cloud capabilities; if no full trajectory export exists, import the available artifact with its reduced coverage explicitly labeled. Do not claim account-wide retrieval or access to a cloud environment that has not actually been provided.

Historical bundle creation may be on demand; future capture/export should be automatic at supported lifecycle or cloud-job boundaries, with durable local queuing, retry and delivery receipts. Do not install a full observability stack on each source. Fresh dependency review remains mandatory for any exporter installed there. If a cloud job is ephemeral, export available records before its storage expires. No new scheduled monitoring is implied.

Transfer bundles privately to this machine by an approved authenticated/encrypted method. The local localhost endpoint is not reachable from a remote cloud worker; a private bundle transfer avoids exposing the dashboard or ClickHouse publicly. Keep the receiving inbox outside the public repository.

Before extraction/import, verify hashes and size limits; reject path traversal, absolute archive paths, device files and unsafe links. Parse as data only; never execute commands, scripts or instructions found in logs. Keep an immutable private source copy and import ledger.

Deduplicate copied histories by original session/event identities and verified content hashes, retaining all provenance. Do not use machine ID or import time alone as a new session identity, and do not collapse genuinely repeated prompts. Preserve original timestamps and partial-session continuation. Correlate transcript and proxy captures of the same call without adding their token usage twice.

Perform a sample import twice to prove idempotency, then process in bounded resumable batches. Record accepted, skipped duplicates, conflicting, partial, failed and missing records. A receipt should identify the destination backend/project and importer version so migration to a fresh database cannot silently skip data.

This portable export/import path is an agreed requirement, not an implemented or verified exporter. Select a maintained source-format importer first. Develop only missing format adapters after format inspection and security review. No other-machine/cloud data has been accessed or imported merely by writing these instructions.

## Analysis

Use Langfuse for session replay, user/assistant pairs, tool inputs/results, model usage and latency distributions. Keep source coverage and exact measurement definitions visible. Distinguish cached/fresh input, output/reasoning subsets, conditional source allocations, API-equivalent prices and actual charges. Keep all outliers and show sample counts with p50/p95/p99/max.

The capture exporter and exact pairing remain unimplemented/unverified until they pass the canary and accounting tests above. Do not label the stack as running, all prompts captured, or all history imported before observing those outcomes.

## Hosting cost alternative

Docker self-hosted OSS avoids Langfuse Cloud usage fees but still uses local CPU, memory, disk and maintenance. Langfuse Cloud is an optional future alternative, not authorized provisioning here. Pricing checked 5 November 2026: Hobby is free with 50k units/month and 30-day historical access; Core is USD29/month with 100k units and 90-day access; Pro is USD199/month with 100k units and 3-year access. Listed additional paid-plan usage is USD8/100k units before volume discounts. Units are traces + observations + scores, not model tokens. Count a dry-run import before estimating a backfill bill. These are observability charges, separate from model execution, optional evaluations and external storage costs.

References: [Langfuse pricing](https://langfuse.com/pricing), [billable units](https://langfuse.com/docs/administration/billable-units), [official Codex integration](https://langfuse.com/integrations/developer-tools/codex), [CLIProxyAPI source](https://github.com/router-for-me/CLIProxyAPI), [request-log advisory](https://github.com/router-for-me/CLIProxyAPI/security/advisories/GHSA-4w5v-m7vx-jpmh).
