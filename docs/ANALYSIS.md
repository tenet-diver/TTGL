# Process, agent, timeline and outcome analysis

Start the existing workspace using [SETUP](../SETUP.md). These native pages use
retained source records, explicit assignments and current subtask interpretations.
No new packages, services, model calls or personal hook changes are needed to view them.

| Page | Route | Behavior |
| --- | --- | --- |
| Cost & tokens | `/costs` | Daily/model cost and tokens, cost bands, response and task drilldowns |
| Tool usage | `/tools` | Treemap by calls/time/optional allocation, daily calls, family/action targets and source evidence |
| Task report | `/tasks/<task-id>` | Inline story, evidence, outcomes, phase markers, model/tool timeline and source steps |
| Process map | `/process` or `#process` | Interpretation/source coverage, rework KPIs, interactive flow map, connection slider, transitions, category cost/time, category statistics and path variants |
| Agents | `/agents` or `#agents` | Main/subagent comparison by explicit source identity: models, runs, responses, tools, errors, recorded model time, tokens, API scenario cost, share and cost/run |
| Activity timeline | `/timeline` or `#timeline` | Weekday/hour response heatmap, cost/token/response measures, daily turn tracks and a searchable turn table |
| Outcomes | `/outcomes` or `#outcomes` | Confirmed-fix KPIs, fix rates by actual workspace and interpreted category, task signals and follow-up prompts, friction patterns and commit/PR references |

All pages share project/workspace/range filtering, saved table columns, sorting,
search and pagination. Direct routes and hash navigation are supported. Category,
transition and path selections open their source tasks; agent/heatmap/turn
selections expose retained evidence. The map supports keyboard activation and
limits displayed connections without changing transition totals. Slider and
heatmap preferences persist in the URL.

## Process semantics

The map uses current model-interpreted or explicitly collected subtasks; raw
unclassified turns and stale groups are excluded. Existing activity labels are
preserved. Interpreted task count and complete source-event coverage are separate:
a task with tool-only grouping can have a useful path while its model responses
remain outside those groups. Source files are reported as present, partial,
unavailable or unknown. On-disk presence does not prove complete/readable retention;
a known missing file is not treated as an empty successful transcript.

Groups follow recorded timestamps. A transition counts each move between groups,
including Start/End boundaries. Its task count is distinct, so a repeated transition
in one task does not inflate distinct-task counts. Rework means visiting a category
already seen in that task, including adjacent repeats. Rework does not prove a defect.
Paths retain the whole interpreted category sequence and group identical sequences.

Category spans use first/last recorded event times. They can overlap and are not
summed into task wall time. A single timestamp provides no span. Default category
usage uses only explicitly owned native response counters. The optional step-share
mode estimates each selected group's share of its original turns, using the actual
selected tools per turn even when the date filter clips a multi-turn group. Such
allocations are estimates, not measured per-tool model costs. Missing values stay unknown.

**Review remaining tasks** lists eligible unclassified/stale tasks. Selecting one
or two and pressing **Analyze selected tasks** explicitly starts existing overview
analysis jobs with the configured small model. The existing concurrency/deduplication
rules and separate overhead accounting apply. No automatic/scheduled analysis or
retry is added. A refresh can be pending while an earlier current interpretation
remains available for map and task drill-down. All selected IDs and source snapshots are validated before starting
work; known-unavailable transcript sources are rejected. Restore their files first.

## Agents and timing

Agent identity comes from native session metadata. Unknown identity is a separate
bucket; it is not assumed to be the main agent. Runs count distinct native sessions.
Native response IDs are deduplicated during ingestion, and transport/parent replay
records are not added to model counters. Model time is shown only for explicitly
recorded generation runtimes; a whole session span or tool runtime is not a model
latency measurement. Scenario shares require known costs for the selected scope.

Timeline timezone defaults to the browser's timezone and can be changed explicitly
to UTC. Heatmap counters belong to response timestamps. Empty cells mean no retained
observations; a patterned cell has observations with unknown cost. Multi-day turns
are split at local midnight, without duplicating usage totals. Daylight-saving folds
can place multiple observations in the same local hour; elapsed duration remains
measured in real seconds. Local-hour tracks show wall time, not 24 guaranteed elapsed
hours. Turn spans can include idle gaps. Tracks show up to 120 dates; the turn table
retains all selected turns. Evidence previews are bounded to 100 IDs per drill-down;
measurement totals are computed before preview limits.

## Outcome semantics

Only a confirmed explicit intervention record contributes to the confirmed fix
rate. A native interruption or rejected call is reviewable evidence, not proof the
task failed. Prompt-prefix heuristics (`no`, `wait`, `that's wrong`, `still broken`,
`revert`) inspect consecutive user messages within a session and show the text and
heuristic basis. They can misclassify intentional requests. Subsequent tasks editing
the same recorded file names are warnings, not confirmed defects. File names are
compared lexically; no transcript-suggested file is opened for this check.

Tasks count once in each category they contain and once in each actual native
workspace where their selected events occurred. Project roots are not substituted
for worktree paths. A missing signal does not mean success. Friction/commit views
retain their original source drill-downs. Commit/PR references do not establish
remote merge state, delivery, or task acceptance. Costs remain API-equivalent scenarios.

## Storage and checks

Additive `activity_sources`, `activity_signals` and `activity_files` projections are
populated by native ingestion. On first use, existing files are marked for a metadata
rescan; repeated scans deduplicate projections and preserve original response counters,
assignments, analyses and historical attempts. Existing measured events are not rewritten.

From the repository root, using the already installed browser tooling:

```sh
PYTHONPATH=tools/usage-monitor/observability python3 -m unittest test_activity_views test_workspace_server
PYTHONPATH=tools/usage-monitor/observability TTGL_BROWSER_QA=1 TTGL_CHROMIUM=/path/to/chromium python3 -m unittest test_activity_views_browser
```

The browser tests cover process nodes/paths, source task navigation, native counters,
heatmap measures/timezones, signal drill-downs, explicit mocked job submission, and
layouts at 1440, 768 and 390 pixels. Backend tests cover rework/counting, unknowns,
source backfill/missing files, scoped cost allocation, midnight/DST and heuristic
versus confirmed outcomes. Tests use temporary state and explicit model fixtures.

## Cost, tokens and tool usage

`/costs` adds native response KPIs, daily cost stacked by model, model spend,
assigned-task cost bands (including unknown and 20+), daily tokens by type/model,
and the model comparison table. Chart segments, models and cost bands open their
source responses or assigned tasks. Unassigned responses remain in daily/model
totals and are reported separately from task bands. A partially priced scope has
an unknown total alongside its known priced portion. Cost bands are in the
configured scenario unit and use half-open boundaries. Latency is shown only when
native generation runtime exists.

`/tools` adds an accessible, clickable treemap, daily calls by the top seven tool
labels plus Other, and a searchable comparison table. Drilling into a tool family
and action exposes retained command targets and source evidence. The selected
measure (calls, recorded time, allocated API estimate or context cost), family and
action persist in the URL. Shell actions use conservative lexical program labels;
compound commands remain one call. No command is run to classify it. Existing
agent category annotations and fallback name rules supply category colors.

Tool costs are unknown in recorded-only mode. The explicit **Estimate by turn tool
share** option allocates a full original turn's scenario cost equally among its
tool calls, even if the date filter clips that turn. It is not measured inference
per tool. Recorded output characters are shown as characters, never guessed token
counts. Background service lifetimes are excluded from operation time. Unknown
runtimes and outcomes remain unknown; failure rates use known outcomes only.
Context-carry costs remain unknown because native records do not identify how
later context tokens belong to individual tool results.

Native input already includes cache-read tokens: token-type stacks partition it
into cached and uncached input, then add output. Explicit cache-write tokens have
a separate KPI because their overlap with input is source dependent. Missing
cache-write counters are not zero. The existing Settings rate editor supplies the
scenario; no new live quote or subscription expense is implied. Charts show the
latest 365 observed dates, while totals and tables cover the full selected scope.

## Inline task report

`/tasks/<task-id>` and ordinary Work task navigation show Story, Evidence, Outcome,
a model/tool step timeline, and an eleven-column step table above the existing
subtask collection and full source explorer. Phase buttons and retained evidence
markers filter the report's step table. Every source link uses the existing
retained-record endpoint. The chart previews 100 events and the report table loads
up to 1,000; the existing paginated explorer retains access beyond those limits.
Agent-type summaries, timeline bounds and measurement totals use the full task, not preview limits. Bar starts are derived from completion timestamps and recorded runtime; unknown runtimes stay as points.

The story reuses the existing bounded evidence packet and highlights failed checks,
changes after validation, missing acceptance and incomplete scans. The last retained
assistant statement is displayed as a claim, without assigning verification based
on its wording. Image references display their retained paths and original source
records; paths mentioned by a transcript are never opened and external images are
not fetched automatically. An image reference does not establish before/after
coverage or visual correctness. Task outcomes retain the confirmed-intervention
versus heuristic-signal distinction used by the Outcomes page.

Usage checks:

```sh
PYTHONPATH=tools/usage-monitor/observability python3 -m unittest test_usage_views
PYTHONPATH=tools/usage-monitor/observability TTGL_BROWSER_QA=1 TTGL_CHROMIUM=/path/to/chromium python3 -m unittest test_usage_views_browser
```

Tests reconcile duplicate counters and token partitions, unknown prices/timing,
unassigned work, exact band boundaries, native workspace/timezone filters, lexical
actions, optional allocation conservation under clipped scopes, failed validation,
phase filtering, source retrieval, URL persistence and light/dark responsive layouts.
They use temporary native fixtures and make no real model calls.
