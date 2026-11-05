# Cross-machine session and request observability

Status: requested architecture, not a deployed system. Preserve existing research protocols and paused schedules. Prefer Langfuse and maintained integrations; build only the missing capture/export adapter after establishing its need.

## Collection and aggregation

Collect recoverable Codex transcripts from every authorized laptop, workstation and cloud job, not only new sessions. Keep originals read-only. Export cloud artifacts before ephemeral workers disappear. A local index entry is not proof that a transcript is retained; report inventory, parsed, imported, incomplete, unavailable and rejected coverage separately. Do not promise recovery of deleted or inaccessible history.

Use a central Langfuse deployment for session replay and aggregate analysis. A shared ClickHouse instance may also hold a separate proxy-capture database, but Langfuse additionally requires its supported PostgreSQL, Redis and object-storage services. Runner hosting is a candidate only: inspect resources and existing service/admission boundaries first, and do not disturb CI or create a second executor.

Do not copy this workstation's credentials to another machine. Each collector uses its own scoped ingestion identity, private storage and authenticated encrypted transport. A cloud worker cannot reach a laptop's localhost; arrange an explicitly reachable authenticated endpoint or retain a private export bundle for later import.

## Separate the evidence layers

| Layer | Data | Destination |
|---|---|---|
| Transcript-derived | User/assistant messages, recorded tools/results, subagent links and observed usage | Langfuse through supported ingestion APIs |
| Proxy request metadata | Client/upstream request IDs, actual attempts/retries, transport, model, status, timestamps, measured usage and capture quality | Separate ClickHouse database/tables, outside Langfuse's managed schema |
| Proxy bodies | Redacted downstream/upstream request and response bodies, SSE/WebSocket capture where supported | Private object storage; content hashes and object references in ClickHouse |
| Derived analysis | Normalized call families, argument patterns, conditional context estimates and findings | Explicitly labeled analytics; selected summaries linked to Langfuse |

CLIProxyAPI's file logging does not automatically populate Langfuse or ClickHouse. Verify a maintained exporter first. Otherwise implement a small reviewed adapter, not another dashboard. Send selected generations, timings, usage and source/capture references to Langfuse through its supported API/OTLP interface. Never insert directly into Langfuse's internal ClickHouse tables.

Separate storage does not require separate dashboards: show correlated records in Langfuse where supported, with access-controlled links to detailed captures. Use a dedicated database, credentials, retention and quotas for raw-capture analytics even if the ClickHouse server is shared. Do not expose ClickHouse directly to collectors on the public internet.

Proxy captures can expose assembled model input that transcript reconstruction misses, but are not necessarily richer for local tool lifecycle or session/subagent identity. Keep both. A proxy cannot recover historic requests that never passed through it. A transcript-derived generation is not a verified copy of an HTTP request.

Record downstream and upstream payloads distinctly: proxies can translate or rewrite requests. Preserve transport and capture stage, truncation, missing frames and transformations. Validate streaming, WebSocket, error, cancellation, compaction and retry coverage with a synthetic canary before routing real traffic. Do not call partial logging complete wire capture.

## Correlation and accounting

Use stable source IDs (not raw hostnames), project/repository IDs, original session/turn/tool-call IDs, provider response/request IDs when exposed, agent/subagent IDs, proxy capture IDs and importer schema versions. Propagate a common correlation ID only where the client/proxy supports it. If exact matching is unavailable, retain an explicitly uncertain link; do not invent a join.

Copies of the same rollout on different machines should map to the same original session identity. Deduplicate immutable event IDs/content hashes within the original stream and preserve ingestion receipts. Identical prompt text alone must not collapse legitimate repeated calls. Partial-file continuation must account for verified offsets and rewritten files. Keep source provenance even after canonicalization.

Treat transcript and proxy observations of one model invocation as two views of the same call, not additional usage. Select one reconciled measured-usage record per actual attempt; flag contradictions and unknowns. Failed or cancelled attempts may still consume tokens. Never infer zero from missing usage.

Keep cached input, fresh input, output and reasoning subset semantics explicit. Separate measured provider counters, estimated source allocations, API-price scenarios and actual charges. Never add overlapping daily/session/source views. Use count, median, p95, p99 and maximum with outcome groups; preserve outliers and label timing scope. Summed overlapping spans are not elapsed task time.

## Privacy, security and operational limits

Raw bodies may contain private code, documents and secrets copied into prompts or tool output. Exclude authorization headers, cookies, OAuth/refresh tokens, API keys and credential-store files. Review all request/error/header logging paths, not just the normal success path. Redaction is a risk reduction, not a guarantee; validate with planted-secret canaries and record redaction/capture version and losses.

Keep source originals private and separate from redacted exports. Do not publish session contents, inventories, archives, credentials or per-user usage in this public repository. Configure private object storage, least-privilege identities, storage encryption, deletion/retention controls and disk quotas before importing real data. Agree retention before automatic deletion; do not silently discard evidence.

Docker is isolation, not a security exception. Before installation or first execution, apply docs/security/dependency-security-policy.md to the exact image digests, base OS and full dependency graphs, publisher/provenance, hooks and auto-download paths. Disable automatic upgrades/panel downloads and avoid host credential/home/Docker-socket mounts. A failed, incomplete or nonzero-finding review blocks startup.

On 5 November 2026 the reviewed CLIProxyAPI v8.0.56 linux/amd64 image failed this gate: OSV Scanner reported 104 advisory IDs across 46 package entries. Advisory IDs can include aliases and do not establish 104 independently exploitable flaws. No CLIProxyAPI container was executed or given credentials in that review. Do not mistake fixing one application advisory for clearing its image. The local detailed scan is private evidence; re-resolve and recheck before any future deployment.

## Acceptance and continuation

1. Inventory retained histories on each host/cloud environment; preserve originals and compare actual availability with index metadata.
2. Resolve and pass security review for all server, collector and exporter artifacts before startup. Save a dated receipt and immutable image/component identities.
3. Bring up private, resource-limited services only on the selected host. Keep monitoring bounded; do not resume the paused research heartbeat.
4. Verify transcript replay and proxy downstream/upstream capture independently with synthetic data, secret redaction canaries, interruption/retry tests and token reconciliation.
5. Import a small historical sample twice to prove idempotency, original timestamps and accurate source labels. Then import broader history with explicit progress/error receipts.
6. Enable future capture on every supported source. Unsupported cloud-native paths must remain labeled unsupported, with explicit artifact-export alternatives.
7. Validate cross-source joins and one-count-per-attempt usage before interpreting dashboards or claiming complete history.

References: [Langfuse Codex integration](https://langfuse.com/integrations/developer-tools/codex), [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI), [CLIProxyAPI configuration](https://github.com/router-for-me/CLIProxyAPI/blob/main/config.example.yaml), [Codex hooks](https://learn.chatgpt.com/docs/hooks).
