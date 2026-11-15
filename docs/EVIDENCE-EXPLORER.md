# Evidence explorer

Open `/investigate` in the running TTGL workspace, or choose **Evidence explorer**
in its sidebar. This is a deterministic investigation tool over retained native
history. It starts no model calls, source scans, benchmark runs or scheduled work.

## Investigating a trace

1. Search retained prompts, task titles/goals/outcomes or operation labels. Choose
   an exact tool/model or an investigation signal. Search is a literal substring;
   it does not search full raw outputs. The default includes all indexed history.
2. Rank **Turns** by measured tokens, recorded runtime, output size or unsuccessful
   tool operations. Native turns can span only part of a task. Open the task link
   for existing task/subtask interpretations and attributed verification records.
3. **Tools** groups recorded operation labels with known/unknown outcomes and
   timing coverage. **Repeated operations** groups exact input fingerprints or
   nonempty output fingerprints within a turn. These are leads to inspect, not
   automatic retry, failure-type or waste judgments.
4. Open **Source steps**, then **Read original evidence**. Original records retain
   redaction, source retention limits and paged access. Unknown source evidence is
   reported as unavailable. The session/source ledger avoids scanning unrelated
   transcripts for each read. A stale source line, changed output hash or changed
   usage record is rejected rather than returned as the indexed event.

Filters and drill-down scope persist in the URL using `trace_` parameters, so a
specific investigation can be shared or reopened. Pages contain 20 results;
server-side counts/ranking cover the entire selected corpus. UI counters describe
the selected whole turns, even when the source-step page filters event type or an
exact fingerprint.

## Analyst MCP and CLI

The new read-only `query_trace_index` tool is shared by the existing stdio MCP,
CLI and `GET /api/trace-index`. Existing MCP clients may need to reconnect to
discover the added tool. The CLI discovers it directly from the current source.
No new provider, dependency, embedding service or database is required.

```sh
# Discover exact model/tool names and corpus coverage.
ttgl query_trace_index --args '{"view":"overview"}'

# Find high-token turns with a recorded unsuccessful tool operation.
ttgl query_trace_index --args '{"view":"turns","signal":"tool_failure","sort":"tokens","limit":10}'

# Find repeated native inputs, without declaring them unnecessary.
ttgl query_trace_index --args '{"view":"patterns","pattern":"input","sort":"count"}'

# Inspect a selected turn, then retrieve original I/O by returned evidence ID.
ttgl query_trace_index --args '{"view":"steps","session":"SESSION_ID","turn":"TURN_ID","kind":"tool"}'
ttgl read_evidence --args '{"id":"EVENT_ID","offset":0,"limit":4000}'

# Existing interpreted task/subtask retrieval stays separate from native facts.
ttgl get_task_history --args '{"task_id":"TASK_ID"}'
ttgl get_task_evidence --args '{"task_id":"TASK_ID"}'
```

`view`: `overview`, `turns`, `tools`, `patterns` or `steps`. Pages accept `offset`
and `limit` (1–100). Sorts: `recent`, `tokens`, `runtime`, `output`, `failures`,
`count`. Tools/patterns use count when `sort=tokens`; this index makes no per-tool
model-token attribution. Default sort is most recent, with stable identity ties.

Scope filters intersect: `project`, `task`, `session`, `turn`, `status`, `query`,
`tool`, `model`, `signal`, `since`, `until`. Exact tool/model/signal filters select
turns **containing** matching events, retaining other events and measured usage in
those turns. `status` is the recorded task status. Signals are `tool_failure`,
`unknown_tool_outcome`, `repeated_input`, `unassigned`. ISO timestamps require a
timezone; `since` is inclusive and `until` exclusive, by **turn start**.

For steps only, `kind` selects `tool` or `generation`; `fingerprint` plus
`pattern=input|output` retrieves a repeated group's source operations. Combine with
the group's session and turn to preserve its boundary. `detail=full` on turns adds
bounded redacted prompts and recorded task outcomes; compact results omit them.

## Measurement boundaries

Each query uses one SQLite read snapshot for scope counts and pages. Native event
IDs remain the ingestion deduplication keys; no daily/session datasets are added
together. Native counters, interpreted subtasks, recorded outcomes and independent
benchmark grades remain different evidence types. No new semantic labels or
independent grades are invented here. Existing `get_task_history` reports label
freshness, and the capable analyst can challenge interpretations against originals.

Runtime is a sum of recorded tool runtime, with timed-call counts. It can overlap
or include background service lifetime, and is not blocking time or task wall time.
Token totals cover retained metered responses. Empty/missing usage stays null;
unknown tool outcomes stay separate from recorded successes/failures. Cash cost,
per-tool inference cost, unused-but-available tools and improvement savings are
unknown from this index. Tool availability requires a separately retained tool
catalogue; an absent operation alone does not establish that it was available.

## Implementation and checks

Reuses TTGL's existing SQLite ledger, native input/output fingerprints,
session/source mapping, redactor and raw evidence reader. Langfuse remains the
maintained tracing integration; these bounded local cohort queries fill the
analyst's discovery gap without another analytics service or package install.
Current Langfuse runtime availability is separate from this workspace feature.

`trace_index.py` contains the shared query contract. `trace-explorer.js` supplies
the interactive browser view. Tests cover deduplication, missing data, whole-turn
filters, timestamps, source identity, repeated-pattern boundaries, pagination,
MCP/HTTP equivalence and raw drill-down. Browser workflow tests are opt-in and
require the already installed, reviewed Playwright/Chromium environment.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/usage-monitor/observability python3 -m unittest test_trace_index
```
