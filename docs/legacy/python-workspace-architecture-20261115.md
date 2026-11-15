# Observatory architecture

Observatory applies the supplied Claude Mining references to its native task and evidence workspace.
The implementation is Python stdlib, SQLite and native DOM, with a separate
Langfuse deployment. It does not require a Next.js rewrite, a second ClickHouse
schema, Garage, or a new agent framework. Existing Langfuse components supply the
trace backend; Observatory adds source reconciliation, task grouping and evidence review.

## Parts and ownership

| Part | Implementation | Responsibility |
| --- | --- | --- |
| Workspace | `tools/usage-monitor/observability/workspace.py` | Loopback HTTP server, local SQLite store, native ingestion, mutations and audit |
| Native parsing | Existing monitor and Langfuse bridge | Native operation identities, recorded runtimes and deduplicated response usage |
| Work views | `work-explorer.js`, `work_analytics.py` | Task → subtasks → source steps, measured usage, type analytics and knowledge candidates |
| Shared record lists | `data-list.js`, `collection.js` | Single record renderer and controls for pages/dialogs, pagination, filters/search/sorting, persistent preferences, source lists and stable selections |
| Activity dashboards | `dashboard_views.py`, `dashboard-views.js` | Overall summary and native-turn activity, separate defined tasks, coverage, source drilldowns and explicit bounded analysis |
| Usage and task reports | `usage_views.py`, `usage-views.js`, `task-report.js` | Native cost/token reconciliation, tool/action/target drilldowns, optional turn-share estimates and inline task story/evidence |
| Analysis pages | `activity_views.py`, `activity-views.js` | Process paths and rework, explicit agent identities, timezone-aware turns, task outcome signals and evidence drill-down |
| Evidence | `task_evidence.py`, `activity-insights.js` | Retained changes, validations, image references, explicit interventions and task story |
| Interpretation | `task_history.py`, `activity_insights.py`, `agent_review.py` | On-demand model work, versioned outputs, source links, confidence and separate overhead |
| Capture | Existing capture proxy and capture-object archive | Original/forwarded transport evidence and durable private records |
| Backend | Existing Langfuse deployment | Traces, dashboards and maintained storage services; see its runbook |
| Design | `ui.css`, `design-language.css`, `chart-theme.js`, `workspace.css`, `work-explorer.css`, `ui.js` | Shared semantic tokens, native controls, categorical chart palettes with contrasting labels and responsive layouts |

Paths in this table are relative to `tools/usage-monitor/observability/` unless
otherwise stated. Startup and private-state locations are in [SETUP](../SETUP.md).

## Ingestion contract

Collection scans the configured Codex `sessions` and `archived_sessions` roots.
A file's size and nanosecond mtime are checked against the SQLite `files` ledger.
Unchanged successful files are skipped. Changed files are parsed as a whole;
native identities deduplicate replayed observations and responses. An unreadable
or malformed session records an error without stopping other files, and is retried
on the next scan. A failed stat has no successful signature.

Database writes for one parsed file are transactional. Previously recorded model
usage cannot silently change: reconciliation is required. Observatory preserves existing
source evidence rather than adopting the reference's replace-old-rows behavior.
SQLite is authoritative for workspace state; `FINAL` applies only to relevant
ClickHouse tables in the separate backend, not to workspace SQL.

Schema initialization and additive migrations must remain repeatable. Never edit
frozen experiment sources or historical evidence to fit the current schema. New
model work requires an explicit action; collection and styling must not invoke a
model or resume paused schedules.

## Task and data model

| Reference concept | Observatory mapping |
| --- | --- |
| Trace / turn | Native session and turn, retaining source identity and project/repository |
| Generation | Native response counters and model; cached input is a subset of input |
| Tool span | Native tool event with recorded runtime, source line, output hash and outcome |
| Task instance | Explicit or discovered task with assigned turns; one prompt is not assumed to equal one verified task |
| Task annotations | Explicit task state/outcome and versioned assignments; model task boundaries are proposals |
| Subtasks / steps | Versioned interpreted or manually collected groups linked to immutable source steps |
| Categorization | Literal operation rules and separate agent interpretations with rationale/confidence |
| Mining jobs | Source collection status and separately recorded interpretation jobs/attempts |

A prompt follow-up is not automatically a correction or intervention. Completion
of a command is not proof of task success. Keep unclassified activity inspectable.
Task types, grouping, knowledge candidates and confidence are interpretations;
source measurements remain unchanged. Do not copy the reference's `new_tasks`
counting formula onto Observatory's explicit task assignments.

## Task story and evidence

The task detail includes collapsible Story, Evidence, Prompt and Outcome cards.
Story summarizes the request, changed files, latest unambiguous validation and
remaining gaps. Current interpreted subtasks provide colored phase markers;
retained evidence markers and phases filter the shared Steps list. Unknown or tied
check/edit ordering cannot establish that a check covers an edit.

Evidence preserves original-step inspection and explicit-record provenance.
Conservative lexical links connect last-message validation claims to the last
matching command, with passed, failed or unbacked labels. They do not independently
verify the claim or establish task acceptance. Visual claims remain reference-only.

Only inline PNG/JPEG/WebP bytes actually retained in native ImageView records have
previews. The task-scoped `/api/task-image` endpoint rescans registered sources on
a cache miss; it never opens paths or fetches URLs suggested by transcript text.
Each image is bounded to 1 MiB, four per record; the private in-memory LRU is bounded
to 64 images / 8 MiB. Responses are same-origin, no-store and nosniff. Path-only and
manual URL references remain references, without a fabricated thumbnail. Viewing
an image does not establish visual correctness.

## Cost and timing

Editable rates are API-equivalent scenarios computed from measured model tokens.
They are not subscription bills or cash savings. Preserve unknown rates/usage as
unknown. Separate analysis/mining overhead from source task counters. Never add
alternative daily/session aggregations, transport spans or allocations to native
response totals.

Per-tool call-cost shares and future context-cache costs from the reference are
estimates, not currently measured Observatory per-tool costs. Keep them unattributed until
a documented attribution method is implemented. Rate changes recalculate scenarios;
they do not require reparsing native token counters. Recorded operation runtime,
background-process lifetime, overlapping tool time and task elapsed span remain
distinct. A nonzero operation is not by itself a failed task.

## Suggestions and agent boundaries

Reuse the on-demand review pipeline. Suggestions cite source steps and carry an
action, risk and validation plan. Accepting a suggestion records a trial decision;
it neither applies a code change nor claims savings. Preserve failed trials and
immutable attempts. Keep decision, implementation and evaluation separate.

Observatory's analyst tools expose bounded evidence queries and read-only review behavior.
The reference's Claude runner, single SQL shell command, four-table ClickHouse
principal and fixed 200-row/20-second settings are not Observatory interfaces. Do not
advertise them as existing controls. Review actual tool capabilities and runtime
isolation before expanding an agent's access.

## Archive and live-steering boundaries

Observatory reads retained native archived sessions and has private HTTP/capture archives.
These do not establish a full transcript-retention service. The reference's
archive-before-ingest, preserved pre-truncation versions, archive-only session
reprocessing and archive-size dashboard remain additional product work. Do not
claim a same-disk archive protects against disk loss. Preserve private originals,
source hashes, delivery receipts, credentials and backend volumes.

## Optimization and steering implementation

`optimization.py` owns deterministic findings, source-linked outcome patterns,
UTC daily/weighted seven-day trends, applied-change records and fixed-window hourly
cluster comparisons. `optimization.js` renders their native tables and SVG charts.
`steering.py` owns separate live-session/rule/event/note tables, authenticated
machine decisions, idempotency and firing history. `steering_hook.py` provides an
opt-in Claude Code adapter and generic client. These reuse SQLite transactions,
the existing rate scenarios, native evidence reader and maintained browser
popover/dialog/SVG primitives; Langfuse remains the trace backend. No additional
framework, chart package or agent runtime is required for these local records.

Log only / Warn / Ask / Block modes, budgets, pause/notes and a bounded fail-open
adapter are implemented. They remain distinct from collection pause and category
rules. The adapter is not automatically installed in personal settings; clients
must support the returned decisions. Codex telemetry does not establish equivalent
pre-tool enforcement. No research schedule is resumed. See [the operations guide](OPERATIONS.md)
for supported source fields, approval semantics, statistical limits and installation.

Native collection and keyboard-accessible popover behavior now ship in
`collection.js`; private DOM assets are no longer required to start the workspace.

`activity_sources`, `activity_signals` and `activity_files` are additive local
projections. Their one-time rescan preserves measured events. Tool-identity v2
also includes the native tool/server/name and file-change inputs so unrelated
failed calls are not grouped into one loop; old identities are marked unknown
until rebuilt from available sources. See [analysis semantics](ANALYSIS.md) for
coverage, confirmed versus heuristic fixes, local time/DST, and bounded source previews.
