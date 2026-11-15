# Bulk activity analysis

Observatory's **Bulk analysis** control opens a persistent queue with progress,
source-event coverage, analysis-token overhead and paginated attempt records.
**Analyze all activity** explicitly starts one finite pass over all indexed tasks
with native events, across projects. There is no scheduled inference.

The analysis uses the existing configured task analyzer (`TTGL_TASK_ANALYZER`,
default `codex`) and small model (`TTGL_TASK_MODEL`, default `gpt-6-luna` for Codex).
It reuses the existing native transport, schema validation, source aliases,
private attempt artifacts and usage accounting. No package installation or new
analytics service is required. This adds the product-specific task/process
interpretation and durable queue behavior to the existing application.

## What it produces

- Tasks retain their explicit recorded status. A separate, versioned interpretation
  labels `done`, `failed`, `dead_end`, `in_progress`, `cancelled` or `unknown`, with
  reasons, confidence and native source citations.
- Subtasks retain activity categories (`investigate`, `plan`, `implement`, `test`,
  `review`, `document`, `operate`, `other`), source-step ownership and interpreted
  outcomes. Raw steps remain accessible beneath each subtask.
- User intervention is `observed`, `possible`, `none_observed` or `unknown`, with a
  reason and references to retained user requests. A new requirement or ordinary
  follow-up is not automatically a correction.
- Tool categories can use the current process interpretation, with explicit
  provenance. Changed native evidence invalidates its label. Explicit existing
  agent annotations retain precedence. Reviewed finite-operation and service-
  lifetime roles remain separate from mixed/unknown cases.

These labels are interpretations of visible evidence, not independent grades or
automatic task acceptance. A successful command or completion marker does not
establish task success. A nonzero tool exit does not establish task failure.

## Scope, persistence and controls

The queue freezes each task's indexed native event metadata and bounded user
request context before invocation. All assigned tasks with events are included;
tasks without events have nothing to analyze. Unassigned active turns require
discovery/assignment before an all-history pass. Known-unavailable sources and
oversized tasks are reported explicitly rather than called successfully analyzed.

The process contract supports up to 10,000 native records per task. Large tasks
use at most 64 chronological source blocks. Visible operation I/O is sampled at
up to 40 evenly spaced records with a 48,000-character total budget. User context
includes up to 40 requests, at most 2,000 characters each. These limits are retained
in the private snapshot and evidence artifacts; indexing coverage does not mean
the model read every character of every raw log. Uncertainty must remain visible.

Two analyses may run concurrently, sharing the existing analyzer's global limit.
There are no automatic retries of failed or uncertain calls. Repeated start
requests return the existing active batch. Unchanged successful process results
are reused; prior failures remain recorded. The worker stops dispatching after
three consecutive failures. **Stop after current analyses** finishes already
running calls and leaves undispatched work visible.

The worker is a separate process with an exclusive database-owner lock, so a web
server restart does not launch another worker. Interrupted dispatch/running state
is never replayed automatically. Inspect uncertain attempts before continuation.
Batch manifests freeze protocol version, model, concurrency and source hashes.
Raw inputs/outputs and receipts remain in ignored private workspace data.

Analysis overhead is reported separately from the original task measurements.
Unknown usage and actual cash cost remain unknown. New activity arriving after
the frozen corpus is outside that batch. Existing research schedules remain paused.

## Pagination and performance

Task lists, dashboard native turns/defined tasks, source-step lists and the bulk
queue use server pages through the shared list component. Full prompts load on
drill-down. Subtasks are bounded by the schema and use the existing local list
pagination. Global counts and measurements still cover the full selected scope.
Existing explicit `limit=all` metadata APIs remain compatible for other clients.

Profiling found repeated shell tokenization dominating overview computation.
Compound scripts are now recognized before full shell parsing, and tool labeling
is reused within an overview request. Dashboard JSON excludes full prompt bodies
and duplicate source-ID arrays from initial charts. HTTP supports gzip and bounded
response lengths; client navigation disconnects no longer emit broken-pipe stacks.

On the retained local corpus, observed overview JSON fell from roughly 9 MB to
454 KB (128 KB compressed), and local request time from about 6.0 to 2.37 seconds.
Task activity delivered 20 rows in about 2.03 seconds and 52 KB compressed. These
are bounded application measurements, not coding-agent speed or cost savings.

## API

- `GET /api/bulk-analysis?offset=0&limit=20`: latest batch and paginated attempts.
- `POST /api/bulk-analysis` with `{"action":"start"}`: explicit all-history pass.
- `POST /api/bulk-analysis` with `{"action":"stop","batch_id":"ID"}`: stop after
  current calls. Normal same-origin mutation checks apply.
- `GET /api/work-explorer?limit=20&offset=0&result=failed`: task hierarchy summaries
  filtered by interpreted result. Recorded `status` remains a separate filter.
- `GET /api/work-steps?task_id=ID&limit=20&offset=0`: source steps, optionally scoped
  by `subtask_id`.

Tests use disposable databases and fixture model outputs. They exercise evidence
validation, native metering, unchanged reuse, failed/uncertain attempts, source
staleness, worker ownership, explicit HTTP launch, paging and transport compression.
