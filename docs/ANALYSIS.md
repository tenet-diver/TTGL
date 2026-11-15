# Process, agent, timeline and outcome analysis

Start the existing workspace using [SETUP](../SETUP.md). These native pages use
retained source records, explicit assignments and current subtask interpretations.
No new packages, services, model calls or personal hook changes are needed to view them.

| Page | Route | Behavior |
| --- | --- | --- |
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
