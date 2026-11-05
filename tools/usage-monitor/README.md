# TTGL Usage Observatory

## Compact workspace and data coverage

The workspace uses compact, searchable/sortable/paginated tables for tasks,
unassigned turns, activity, categories, rules and opportunities. Add/edit forms
open native modal dialogs. EVLV's shared plain-DOM collection and keyboard/menu
behavior, control/table classes, and light/dark tokens come from the private
`tenet-diver/design-system` distribution pinned in
`config/design-system.lock.json`. App-specific layout stays in this repository.
No React, Radix or npm runtime install is required for the plain-DOM artifacts.

The producer's license prohibits public redistribution. Its three generated
assets are deliberately kept under ignored `work/security/design-system/`, not
copied into this public repository. To reproduce the UI, use an authenticated
local checkout of the private repository containing the pinned commit:

```sh
python3 tools/usage-monitor/observability/sync_design_system.py --source /path/to/design-system
python3 tools/usage-monitor/observability/sync_design_system.py --check
```

The sync reads only the locked `dist/styles.css`, `dist/collection.js` and
`dist/dom.js` via `git show`, validates their hashes, and does not run producer
scripts. Startup and doctor check require those private assets. Tokens/components
are never fetched from the network by the browser.

The token header displays **selected scope**, **all retained sources**, and
**unassigned usage**. A task total excludes other tasks and unassigned turns;
category filters can exclude model generations. “Why totals differ / reconcile”
queries Langfuse v2 Metrics using the same native-generation environment and
shows the all-source difference explicitly. Temporary ingestion lag remains
visible; daily/session rollups and HTTP captures are never added to model usage.

Categories have two independent assignment mechanisms. Codex reviews inspect
event evidence and record purpose/rationale/confidence. Fallback rules use a
case-insensitive **literal substring of the operation label**, not regex, not
full command search and not another LLM call. The first matching enabled rule
wins for unreviewed events. Reviewed labels take precedence. The rule dialog
includes examples and previews both matching labels and eligible unreviewed
events. Table search is a separate shared collection feature.

**Historical capture correction:** the first six model exchanges retained request
bodies and transport byte/timing metadata, but their response bodies were lost
because the old parser treated `application/octet-stream` SSE as unknown binary.
Earlier claims of complete response-body coverage for those exchanges were
incorrect. The app now labels them “not retained by legacy parser”; it does not
reconstruct raw responses from native transcripts. Session/time associations are
explicitly marked inferred. Capture schema 2 detects and parses SSE framing
independently of Content-Type, retains response IDs across chunk boundaries,
omits opaque/private reasoning data and flags dropped/oversize frames. A new
real `CAPTURE_V2_OK` canary verified retained response events, exact provider-ID
correlation and no truncation. HTTP exchange tables use task/project scope and
deliberately ignore tool-category filters, since per-tool model attribution is
not measured.

## Codex is the analyst

The **Codex analysis** view contains agent-authored findings with evidence IDs,
recommended actions, validation plans, confidence and a frozen source cutoff.
The analyst reads actual command intent and failure excerpts rather than relying
on the fallback substring categories. Its event interpretations are versioned
separately from original traces. Agent-reviewed category/role labels take
precedence in workspace views; new unreviewed events remain explicitly unreviewed.

Background service lifetime, reviewed finite operation runtime and unreviewed or
uncertain runtime are shown separately. Finite operations can also overlap, so
their sum is still not elapsed task time or proven agent-blocking time. Historic
Langfuse records stay unchanged; these are analysis interpretations over them.

Run an on-demand review of a task (or omit `--task` for the available source):

```sh
python3 tools/usage-monitor/observability/agent_review.py run --task TASK_ID
```

The runner freezes evidence, strips configured local secrets, invokes the existing
Codex CLI through the capture adapter in read-only mode, validates complete event
coverage and finding references, then publishes the result. Its instructions and
output schema are checked in under `config/analyst-prompt.txt` and
`config/analyst-output.schema.json`. It attempts one bounded run, with no automatic
model-call retries. Failed or uncertain runs are preserved for inspection. The
analyst's own native token usage is saved separately and its source turns are
assigned to a separate analysis task; it is excluded from the frozen baseline.
Actual cash expense and improvement savings remain unknown.

By default subsequent runs review only unreviewed events, preserving earlier
interpretations and avoiding repeated model work. `--full` requests an intentional
complete re-review. Aggregate usage in an incremental snapshot still describes
the selected task/project scope and is labeled accordingly.

Private evidence, final JSON, logs and manifest are stored under
`work/security/analyses/`. For an already completed output, `agent_review.py publish
--directory PATH` validates and publishes it without another model call. No
scheduled analysis or automatic optimization executor is enabled.

## Reproduce this deployment

All non-secret deployment configuration is checked in:

| Source | Purpose |
|---|---|
| [deployment.lock.json](config/deployment.lock.json) | Six active image digests and observed service versions; tested Python, Codex, Docker/Compose and Node versions |
| [compose.template.json](config/compose.template.json) | Networks, volumes, ports, memory/CPU limits, health checks, application settings and secret placeholders |
| [defaults.json](config/defaults.json) | Private state paths, ports, collector intervals, upstream and capture limits |
| [codex-provider.toml](config/codex-provider.toml) | Responses API provider, existing ChatGPT authentication, HTTP/SSE mode and disabled request compression |
| [mcp.template.json](config/mcp.template.json) | Analyst MCP command and portable path placeholders |
| [design-system.lock.json](config/design-system.lock.json) | Private EVLV DOM distribution commit, artifact hashes and source review |
| [Codespaces settings](../../.vscode/settings.json) | Port labels and automatic-forwarding behavior |

The active lock is separate from `observability/candidate-images.json`, which
preserves rejected/historical candidates. No floating image tags or third-party
Python/npm packages are needed by the current app. Container digests pin the
service artifacts; host tools are pre-existing prerequisites whose tested
versions are recorded, not automatically installed or upgraded. Python 3.11+
is required for the checked-in TOML configuration; the tested interpreter is
3.14.2 and Codex CLI is 0.166.0.

From the repository root, on a machine where the dependency policy permits the
locked images, first sync the private design-system assets as described above:

```sh
# Generate private credentials/config; repeated preparation preserves secrets.
python3 tools/usage-monitor/observability/setup_local.py prepare

# Explicit first-time image download. Skip if the locked images are present.
python3 tools/usage-monitor/observability/setup_local.py pull

# Verify prerequisites, the tested Codex version and all six local images.
python3 tools/usage-monitor/observability/setup_local.py doctor

# Register analyst MCP and install the explicitly selected, owned Codex profile.
python3 tools/usage-monitor/observability/setup_local.py configure-codex

# Foreground supervisor: preserves the existing named volumes and delivery ledger.
python3 tools/usage-monitor/observability/setup_local.py start
```

In another terminal, create/update the native dashboard after Langfuse becomes
healthy, or inspect process/container status:

```sh
python3 tools/usage-monitor/observability/setup_local.py dashboard
python3 tools/usage-monitor/observability/setup_local.py status
```

URLs are derived from the Codespaces environment; ordinary local machines use
localhost. Overrides are available via `--langfuse-url`, `--media-url`, `--state`,
`--workspace-data` and `--codex-root`. `--codex-root` chooses the transcript source;
profile installation uses the active user's existing Codex configuration home.
Provider keys belong in a user profile or CLI overrides, not a project-local
`.codex/config.toml`, as specified in the
[official OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

Start a new traced Codex session with either:

```sh
codex --profile ttgl-observability
python3 tools/usage-monitor/observability/codex_traced.py
```

The profile includes analyst MCP and the capture provider. The wrapper applies
the checked-in provider settings to its invocation and uses any existing user
MCP configuration. Neither changes the default provider in user configuration.
Existing Codex login is reused; no API/OAuth credentials are stored in Git.

Forward 3000/8766 and keep forwarded ports private. In Codespaces this can be
made explicit without publishing anything:

```sh
gh codespace ports visibility 3000:private 8766:private 9090:private 9091:private
```

Use Ctrl-C on the supervisor to stop its three local processes; Docker services
and persistent data remain. Stop those services without removing data using
`docker compose -f work/security/langfuse-stack/compose.json stop`. Never use
`down --volumes` or remove the export ledger for an ordinary restart. Preserve
private credentials/encryption keys, database/S3 volumes, workspace SQLite and
delivery receipts together when migrating an existing deployment. Fresh setup
recreates software/configuration, not private history or login credentials.

## Current Codespaces workspace — 5 November 2026

The project/task application is `observability/workspace.py`, backed by private
SQLite and Python's standard library. The six-service Langfuse Docker stack is
the detailed evidence UI. Current startup is supervised by:

```sh
python3 tools/usage-monitor/observability/start_local.py \
  --state work/security/langfuse-stack --workspace-data work/security/workspace \
  --langfuse-url https://YOUR-CODESPACE-3000.app.github.dev
```

This requires the existing prepared/pulled stack; it never installs packages or
pulls images. `langfuse/prepare_stack.py --destination work/security/langfuse-stack`
generates six digest-pinned services and private credentials. The running instance
was explicitly authorized by the user despite incomplete security reviews;
confirmed findings still block affected candidates. Do not treat it as a complete
security clearance. See `docs/research/observability-setup.md`.

Forward **8766** for projects/tasks and **3000** for Langfuse; keep both private.
Login details are in `work/security/langfuse-stack/local-access.json` (`email`,
`password`). PostgreSQL, Redis and ClickHouse have no host-published ports. S3
uses MinIO on loopback ports 9090/9091. All database/object data uses named Docker
volumes; do not delete volumes or the export ledger during restart.

The workspace implements project scope, explicit task goals/acceptance/outcomes,
turn assignment and an unassigned inbox, task/project/category filters, measured
response tokens and cache use, native tool-runtime distributions/shares, recurring
category pairs, evidence-linked timelines, versioned literal category rules,
collection pause/resume, and opportunity review with separate decision,
implementation and evaluation states. Rules do not alter source records; reviews
do not apply optimizations. Task completion requires outcome evidence. Agent turn
completion alone is not task success. Actual charges and per-tool token allocation
remain unknown.

`langfuse/live_export.py` automatically polls retained native records every 15
seconds and uses the existing immutable OTLP receipt/outbox ledger. Failed or
uncertain delivery is visible and requires reconciliation, not blind replay.
Workspace ingestion polls every five seconds; the supervisor restarts failed
processes. The source transcripts and captures are durable local queues; there
is no remote delivery if this Codespace is stopped. The supervisor stops when
its process or Codespace stops; this is not OS-login autostart.

For **future explicitly proxied Codex sessions**, launch:

```sh
python3 tools/usage-monitor/observability/codex_traced.py
```

The launcher uses the existing ChatGPT login and command-local provider settings;
normal routing/configuration is unchanged. The local HTTP/SSE adapter on 8317
does not implement OAuth or TLS interception. Streaming is forwarded unchanged;
private stored bodies are redacted with opaque reasoning fields omitted. Headers
and credentials are not journaled. Redaction is best effort, not a guarantee.
Requests are capped at 4 MiB, response capture at 1 MiB, and retained capture
storage at 128 MiB. Oversize/unsupported requests fail explicitly; capture
truncation is flagged. No WebSocket support or compressed request capture is
claimed. Transport durations/first-body-byte timing are not pure inference time.
Proxy observations never contribute additional usage counts. Existing active
chats remain transcript-only; they cannot be retroactively routed.

The `ttgl-analyst` stdio MCP server is registered in the Codespace's Codex CLI.
New Codex sessions can query filtered activity and bounded raw evidence, create
projects/tasks, assign turns, revise rules, record verified outcomes and manage
opportunity review states. Its entry point is `observability/analyst_mcp.py`.
It does not run an autonomous background model or apply changes. Optional SLM
summaries, screenshots, automatic task-boundary inference, optimization execution
and controlled comparative trials are not implemented. Other-machine histories
are not connected by this deployment.

Checks: `python3 -m unittest discover -s tools/usage-monitor/observability -p
'test_*.py'`, the Langfuse adapter tests, and `node --check
tools/usage-monitor/observability/workspace.js`. The compact UI received actual
Chromium browser checks for all views, dialog submissions in an isolated database,
EVLV keyboard/focus behavior, literal rule previews, shared collection search,
task-filtered capture visibility, token reconciliation, light/dark and mobile
layout. QA tool versions are in `config/browser-qa.lock.json`; QA dependencies
are optional and not app runtime dependencies. Screenshots/results and the
isolated QA environment remain private under `work/security/browser-qa/`.

The sections below describe the earlier Mac companion and remain historical;
do not start its automatic `npx` dependency installation for this setup.

A working local Codex companion: retained session usage, daily/model/session views, tool evidence, recurring-opportunity rules, agent-authored reviews and durable review/decline/defer history. This is an initial monitor, not the complete handoff executor.

## Run

Requires Python 3.9+, Node/npm (`npx`) and the installed `zstd` executable. Token accounting reuses MIT-licensed ccusage **20.0.48** rather than duplicating its cumulative/fork/compaction logic. The version's help and live output were checked on 4 November 2026; no paid service is needed. `npx` installs the pinned release from the npm registry on first use; reports use `--offline --no-cost` and do not upload logs. No live pricing or billing estimate is calculated. The custom portion adds the review UI, local evidence rules and decision history that aggregate reports do not provide.

On macOS, `python3 tools/usage-monitor/manage.py install` copies the application into `~/Library/Application Support/TTGL Usage Monitor`, installs a user LaunchAgent with restart and login startup, and installs the `ttgl-usage-monitor` skill. Existing data is preserved. Open http://127.0.0.1:8766. Use `manage.py status` or `manage.py stop` to inspect/stop the service. Re-running install updates the installed app and starts it again.

For a foreground service: `python3 tools/usage-monitor/server.py --data /absolute/local/private/data --port 8766`. Source defaults to `~/.codex`; use `--codex-home` for another root. Source directories are read-only. SQLite stores normalized metadata, sizes, hashes and decisions, not raw commands/results. Runtime data, reports and agent reviews stay outside Git. The service is loopback-only; mutations require the same browser origin. No raw histories are sent to an LLM.

## What is implemented

- ccusage session/daily JSON snapshots every three minutes. Input here is uncached input; cached reads are separate. Reasoning is within output. Reports run sequentially while sources can change; coverage includes the observed daily/session reconciliation residual and capture times.
- Plain and zstd historical import, active/archive duplicate precedence, native completion-ID deduplication, replay-prefix exclusion by session timestamp/thread identity and legacy request/result matching. Native output sizes refer to retained serialized results, which may already be truncated, not exact provider-visible payloads. Native timestamps measure tool completion intervals, not whole-task elapsed time. Legacy timing/outcomes remain null.
- Changed-file polling every 20 seconds. Unchanged files are skipped. Changed files are re-parsed in full, so large active logs add overhead; this is not yet an offset-based low-overhead collector. Malformed/oversize lines and per-file errors are visible in coverage. Format support is based on observed local versions, not a universal stable OpenAI log schema.
- Up to five recurring-opportunity cards: large tool results and repeated identical retained output. The other handoff detectors remain unimplemented. These rules do not prove wasted work. Project and model filters apply to the session browser; tool findings currently cover the imported corpus.
- Explicitly labeled Codex-reviewed cards can be stored in `data/agent-reviews.json`. This chat authored the initial reviews against frozen evidence. Automatic rule findings refresh locally; there is no autonomous background LLM. The installed skill queries `/api/agent-context` for later Codex analysis.
- Review choices persist in SQLite and an append-only event log. They never apply a patch. Execution, bounded trials, adoption/rollback, result comparison UI and savings remain future work. Declines suppress overview resurfacing with stable IDs; all decisions remain inspectable.

## Verify

`python3 tools/usage-monitor/test_monitor.py` checks replay exclusion, duplicate completions, legacy joins, unknown fields and import idempotency. `node --check tools/usage-monitor/app.js` checks UI syntax. Actual UI overview, suggestion navigation and evidence dialogs were inspected with local history. The original handoff fixtures passed separately. Private runtime totals are intentionally not committed here.

Source evaluation: [ccusage Codex source documentation](https://github.com/ccusage/ccusage/blob/main/docs/guide/codex/index.md), [MIT license](https://github.com/ccusage/ccusage/blob/main/LICENSE), and [v20.0.48 release](https://github.com/ccusage/ccusage/releases/tag/v20.0.48). Codex interface review: [official developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli); local rollout field support was established from the selected local corpus.
