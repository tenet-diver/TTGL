# Optimization, outcomes and live steering

Start the workspace as described in [SETUP](../SETUP.md). These pages use the
existing local SQLite database, retained native evidence, editable rate scenarios
and on-demand interpretation jobs. No new runtime packages or model calls are
needed to display them. Shared table search, numeric filters, sorting, saved
columns, pagination, light/dark themes and responsive layouts remain available.

## Pages

| Page | URL | Working behavior |
| --- | --- | --- |
| Suggestions | `/suggestions` or `#suggestions` | Deterministic findings, affected source records and evidence drill-down, alongside the existing explicit small-model review/grouping workflow |
| Impact | `/impact` or `#impact` | Record/delete applied changes, select metrics and workspace, choose immediate/new-session effect, compare fixed windows and inspect daily/7-day trends with numbered intervention markers |
| Outcomes | `/outcomes` or `#outcomes` | Confirmed-fix KPIs, workspace/category fix rates, task warning signals, repeated failures, context jumps and retained commit/PR references |
| Live sessions | `/live` or `#live` | Connected sessions in the last 24 hours, working/waiting/idle status, queued notes, pause/resume, KPI strip and persistent rule log |
| Steering rules | `/live/rules` or `#steering` | Eleven built-ins, editable mode/message/threshold, enable switch, custom command rules, firing counts, last firing, edit/delete |

These pages filter by project, workspace and 1/7/30/90 days or all retained
history. Live pages filter by workspace. Filters persist in the URL. Impact graphs show
UTC days; daily observations and weighted seven-calendar-day averages can be
hidden independently. Each chart has a source-value table and accessible labels.
Unsupported metrics show Unknown rather than synthetic observations.

## Measurement semantics

The chart catalog covers cost per task, average context, large-context calls,
shell exploration, known failed tools, large shell outputs, repeated failures,
consecutive shell explorations, break/context warnings, confirmed interventions,
configured top-tier/small models, explicit main/subagent roles, explicit explore
roles, and explicit cache-write/TTL evidence. Model-tier fragments and the short
answer threshold can be edited on Impact. They are analytical assumptions, not
quality predictions. Existing Settings controls edit the API-equivalent rate scenario.

Task denominators count explicitly assigned tasks first observed in the measured
period. Warning-rate denominators use tasks with matched hook receipt coverage (a five-second clock tolerance); historical tasks from before hook capture are not treated as warning-free. A user follow-up is not automatically a correction. Unknown tool outcomes,
agent roles, answer sizes, cache writes and cache TTLs stay unknown. Cached input
alone never establishes a cache write. Findings link to actual source identities;
output characters are neither bytes nor attributed tokens. Commits/PRs are retained
references, not verified remote delivery. Original logs and measured counters stay
unchanged; an additive metadata projection is backfilled during the next scan.

Affected spend is the priced amount associated with a finding, not its saving.
Findings can overlap. Estimated savings stay Unknown without a quality-preserving
comparison; no saving amounts are invented or summed. Model work remains on demand
and its overhead stays separate. These are token-price scenarios, not cash charges.

Each applied change compares the 14 days before its time with up to 14 days after,
independently of the chart range. New-session effects exclude sessions whose native
start timestamp precedes the change or is unknown. Comparisons aggregate hourly
clusters and use 400 deterministic bootstrap resamples for a 95% interval, requiring
at least eight observed hours on each side and sufficiently many valid resamples.
Unknown rates, empty denominators and insufficient samples suppress the interval.
Only intervals entirely below/above zero receive lower/higher labels. These are
observational comparisons; check quality, seasonality and concurrent changes before
attributing an effect. Charts retain at most the latest 365 days; comparisons still
use the full selected-project data within their fixed windows.

## Connect a hook

The workspace creates `steering-token` in its private data directory with mode
0600. It is never exposed by an HTTP endpoint. The machine endpoint is
`POST /api/steering-hook`; it requires `Authorization: Bearer <token>`, rejects
browser Origin headers and validates the normal allowed Host boundary. UI mutations
continue to require same-origin requests. Do not publish the token or bind the
workspace to a public interface.

A generic authenticated client can send these fields:

```json
{
  "session_id": "client-session-id",
  "event_id": "unique-stable-event-id",
  "event": "pre_tool",
  "workspace": "/path/to/project",
  "tool": "Bash",
  "command": "pytest tests",
  "input_hash": "optional-canonical-input-hash",
  "task_id": "optional-explicit-task-boundary",
  "cost_usd": 5.25,
  "context_tokens": 120000,
  "main_folder": false
}
```

Events are `start`, `prompt`, `pre_tool`, `post_tool`, and `stop`. A post-tool event
may include boolean `failed` and operation `edit`, `check`, or `other`. Costs are
cumulative per session; explicit task boundaries reset task-budget deltas. Without
an explicit task boundary the task budget is session-scoped. When available,
fully priced native session counters provide an API-scenario fallback. Missing
cost/context data cannot fire those rules. Daily budgets cover reported sessions,
not an entire provider account. The UI labels their reported/scenario basis.

Re-delivering an identical event ID returns its original response without duplicate
firings or note delivery. Reusing the ID with changed content is rejected. Responses
contain `allow`, `warn`, `ask`, or `block`, messages and matched rules. Receiving a
response does not prove a client enforced it. Post-tool rules warn or log; they
cannot retroactively stop a completed operation.

## Claude Code adapter

The stdlib adapter implements Claude's hook input/output protocol. Start the
workspace, then explicitly opt in:

```sh
python3 tools/usage-monitor/observability/steering_hook.py install --data work/security/workspace
python3 tools/usage-monitor/observability/steering_hook.py status --data work/security/workspace
python3 tools/usage-monitor/observability/steering_hook.py uninstall --data work/security/workspace
```

Use `--settings /path/to/settings.json` for another settings file and `--url` for
another loopback port. Installation backs up the selected settings file, preserves
other hooks and adds only TTGL's marked commands. Uninstall removes only TTGL
commands. The request timeout is 1.8 seconds; the hook command has a 3-second client
timeout. Transport/configuration errors fail open and report only the exception
type to stderr, without echoing the hook input or credentials. Set
`TTGL_HOOK_OFF=1` to bypass this adapter for a session.

Supported hooks: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse,
PostToolUseFailure, Stop. PreToolUse maps Ask to Claude's approval prompt and Block
to deny. Prompt-time approval/block requests stop submission for user review.
Stop has no native ask primitive: a block or delivered note requests continuation;
`stop_hook_active` prevents an endless stop loop. A successful check means only
that the reported check operation passed, not that the whole task is accepted.
Main-folder detection distinguishes a discovered `.git` directory from a worktree
`.git` file; callers can supply an explicit flag. Input identities use the complete
structured input hash even when the displayed command is bounded.

Claude's standard hook payload does not always include cost/context counters.
Those rules need explicit counters or matching ingested native usage. TTGL's
current native-history reader is Codex-oriented; this adapter does not claim a new
full Claude transcript importer. Codex clients may use the generic event protocol
for telemetry, but current Codex hooks do not provide equivalent synchronous
pre-tool approval. The adapter is implemented and tested; it is not automatically
installed into the user's personal agent settings.

## Rule behavior

Built-ins cover idle prompts, task/daily budgets, main-folder checkout/switch,
explicit public npm registries, Claude commit attribution, external-record writes,
shell file exploration, context threshold, repeated identical failures, and edits
after the last successful check. All default to Warn except task budget, which
starts in Ask. Built-in kinds are fixed; mode, message and relevant threshold can
change. Custom rules match tool/workspace globs and command literal text or glob
patterns, with an optional main-folder restriction. Arbitrary regex is deliberately
not executed in the hook path. Rules are evaluated in a transaction; notes are
marked delivered once and all firings persist in the log. Pause requests approval
for each subsequent pre-tool call. It does not terminate a running process.

## Validation

From `tools/usage-monitor/observability/`:

```sh
python3 -m unittest test_steering test_workspace_server test_optimization test_workspace test_task_evidence test_work_analytics test_activity_insights test_task_history test_task_curation
TTGL_BROWSER_QA=1 TTGL_CHROMIUM=/path/to/chromium python3 -m unittest test_workspace_browser test_activity_insights_browser test_task_story_browser test_optimization_browser
```

Tests use temporary SQLite stores and retained-source fixtures. No live model,
new package installation, personal settings mutation, or paid trial is required.

To validate the entire Observatory from the repository root, including every
browser workflow, use an existing Playwright/system Chromium installation:

```sh
PYTHONPATH=tools/usage-monitor/observability TTGL_BROWSER_QA=1 TTGL_CHROMIUM=/path/to/chromium python3 -m unittest discover -s tools/usage-monitor/observability -p 'test_*.py'
```

The server-entry-point tests launch the actual workspace process against disposable
state, verify every new page and native asset, restart it to check persisted rules,
notes and tokens, and invoke the hook CLI over HTTP. Additional regression cases
cover concurrent duplicate receipts, stable Claude tool-event identities, UTC daily
budget rollover, and workspace-filtered logs beyond the global display limit.
Browser checks cover retained outcome sources, persisted URL filters, chart
visibility and source values, model assumptions, and custom-rule disable/delete.
They use explicit model fixtures; they do not validate a live provider installation
or change personal hook settings.
A delayed-response browser regression also verifies that an earlier search cannot
replace a focused draft, move its caret, or prevent the next query from reaching
the empty-results state. The content region exposes its pending state through
`aria-busy` so both assistive technology and tests can observe completion.

Validation on 15 November 2026: the full command above passed **154 tests with no
skips**, including ten browser tests and actual server/adapter subprocess checks.
The tests use temporary state and explicit CLI/model fixtures; live provider
behavior, production traffic and personal hook installation are outside that result.
JavaScript syntax checks and `git diff --check` also passed.

[Additional analysis pages](ANALYSIS.md) cover the interactive Process map,
Agents and timezone-aware Activity timeline, together with expanded Outcomes.
The Activity timeline uses a selected local timezone or explicit UTC; the Impact
charts above retain UTC daily buckets.
