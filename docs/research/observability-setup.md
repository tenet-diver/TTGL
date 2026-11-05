# Single-device observability setup

Current scope, 5 November 2026: ONE analysis stack on a development machine, with optional historical imports from other machines and exported cloud sessions. Other sources do not need their own Langfuse/ClickHouse deployment or a continuously running collector. Do not provision a shared runner or additional cloud infrastructure for this scope.

## Intended flow

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

## Optional imports from other machines and cloud sessions

The single-machine deployment is the destination, not a restriction on where sessions originated. Accept on-demand bundles from other machines and supported cloud session exports alongside this machine's retained history.

Each source should export only the explicitly selected session records and a private manifest containing:
- a stable pseudonymous source ID and source kind (local, other-machine, cloud);
- original session/thread IDs, turn/tool-call/request IDs where available, original timestamps and timezone;
- exporter/client versions, format/schema, per-file SHA-256 hashes, byte counts and record counts;
- scope and completeness flags, redaction version, truncation/errors and missing/unavailable records.

Exclude auth/config credential files, environment dumps, cookies, SSH keys, provider tokens and unrelated home/project files. Never infer that a cloud task's final answer or terminal log is a complete model trajectory. Export only through supported cloud capabilities; if no full trajectory export exists, import the available artifact with its reduced coverage explicitly labeled. Do not claim account-wide retrieval or access to a cloud environment that has not actually been provided.

Bundle creation should be on demand on the source machine or at an explicitly configured cloud-job completion boundary. Do not install a full observability stack on each source. Fresh dependency review remains mandatory for any exporter installed there. If a cloud job is ephemeral, export available records before its storage expires. No new scheduled monitoring is implied.

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
