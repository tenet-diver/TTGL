# Local Langfuse deployment

As of 4 November 2026, Langfuse is the primary session replay and tracing UI. Use the maintained official Codex converter instead of adding a custom trace parser or UI.

- Sessions: http://localhost:3000/project/ttgl-codex/sessions
- Tracing: http://localhost:3000/project/ttgl-codex/traces
- Historical aggregate usage and reviewed suggestions: http://127.0.0.1:8766

Six services run in Docker Compose project `ttgl-langfuse`: Langfuse web/worker 4.75.0, PostgreSQL 17 Alpine, Redis 7 Alpine, ClickHouse 26.3.62.3 Alpine, and SeaweedFS 4.52 providing S3 storage. All images are pinned by digest in the private deployment file. Secrets and private imports are under `~/Library/Application Support/TTGL Langfuse`; never commit or print its `.env` or `local-access.json`. Backend containers have no Codex directory or Docker socket mounted. Published UI/S3 ports bind only to loopback. Database/queue services have no host ports. Outbound isolation is not guaranteed; a web-container outbound test succeeded. Telemetry is disabled.

Start/stop with Docker Compose using that directory's `docker-compose.yml` and `.env`. Restart policy is unless-stopped; Docker Desktop must run. Preserve volumes when stopping. The service named `minio` uses SeaweedFS, not MinIO.

The official `@langfuse/codex-observability-plugin` 0.4.3 package signature and SLSA provenance were verified against source commit `e1d02be28e6bacbfe350a1bc1ccf861e54edee17`. The installed runtime bundle matches the verified npm package. The host hook uses existing Node 24.22.2; backend software runs in containers. Codex features.hooks is enabled and the local plugin/config is installed. **Live capture needs a Codex restart and user review/trust of the vendor Stop hook through `/hooks`. Never bypass hook trust.**

Two actual sessions, four completed turns, were imported using the vendor converter on copied rollouts. Both appear in the native Sessions UI with tool/generation observations. This is a bounded pilot, not a full historical trace backfill. Original histories remain unchanged. Imported timing is reconstructed from retained logs, not independently measured provider latency. UI cost is an estimate, not subscription billing. The companion ccusage baseline covers broader retained history.

Security review used OSV Scanner 2.3.3. Selected web/worker/Redis/ClickHouse scans returned no advisory groups; PostgreSQL contained 60 unscored groups and one scored 5.5 group, largely in its gosu helper; SeaweedFS contained five unscored groups. The plugin source lock had nine advisory groups, including bundled Zod 4.6.5 memory exhaustion; reviewed use validates small private local configuration, which limits exposure but is not a patch or reachability proof. Container image attestation verification was blocked by registry rate limiting. Digest pinning and npm provenance do not prove absence of a supply-chain attack. Re-scan before updates; do not describe this stack as vulnerability-free.

Official integration: https://langfuse.com/integrations/developer-tools/codex
Official plugin: https://github.com/langfuse/codex-observability-plugin

AI Observer and its feed/projection LaunchAgents are stopped. Their old usage-only projection omitted tool and conversation details. Retained adapter files are historical, not the primary deployment.
