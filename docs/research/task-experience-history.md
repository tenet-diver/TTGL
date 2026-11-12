# Task experience history

The Observatory now provides **task → interpreted subtasks → native source steps**.
Use **Experience history** in the workspace sidebar, or choose **Analyze / inspect
subtasks** on a task. Assign collected turns to the task first. Search includes
unanalyzed task goals/outcomes as well as the latest subtask summaries, tags,
activity categories and operation labels. Filter by completed tasks when looking
for finished experiences. Task completion still requires explicit outcome evidence;
a successful command or model turn does not establish task success.

## Analysis and source fidelity

Analysis is an explicit button/MCP action, never a scheduled inference job. The
small model receives the task definition and bounded native operation metadata,
not full private command/result histories. The context names this limitation;
unavailable intent must remain uncertain. The result supplies meaningful grouped
titles, explanations, activity types, tags and confidence. A structured schema
and server-side validation require each source step exactly once, reject invented
IDs and preserve source ordering. Native raw measurements are not rewritten.
Referenced GitHub PR links are displayed only when present in the task definition
or its recorded outcome, rather than synthesized by the model.

Each analysis has an immutable snapshot hash, model, attempt, timestamp, source
links and version. Duplicate clicks reuse an active job; unchanged evidence and
the same model/engine reuse the existing analysis. Reanalysis creates a new
version and retains prior versions. Changes during inference reject publication;
changes after publication mark the interpretation stale in both search and detail.
Source evidence is read through the existing bounded, sanitized `read_evidence`
path. A deleted/unavailable original remains unavailable, not reconstructed prose.

At most two analyses run concurrently, with at most 2,000 tool steps per task,
60 subtasks per result and a 120-second inference deadline. Larger task scopes
must be split before analysis. Failures and interrupted attempts remain visible;
there are no harness retries. The native CLI can retry transport internally;
unknown retry spend is not assumed free. Reported model counters, including
counters from rejected interpretations, are stored separately from task usage.
Missing usage remains unknown. An expired/interrupted attempt is not silently
rerun. The UI shows progress, errors, interpretation confidence and overhead.

## Model configuration

No dependencies, model weights or services are installed automatically.

By default the existing Codex CLI runs `gpt-6.1-luna` at low effort with structured
output. Set `TTGL_TASK_MODEL` to a supported small model in your existing route.
The analysis subprocess uses a read-only sandbox, ignores user configuration,
disables shell/apps/browser tools and web search, and suppresses automatic project
document injection. Any unexpected completed tool item rejects the result.
Attempt files stay under the private workspace data directory. Supported CLI
authentication is reused; credentials are never copied into task records.

For an already installed local Ollama-compatible server, configure the workspace:

```sh
export TTGL_TASK_ANALYZER=ollama
export TTGL_TASK_MODEL=YOUR_ALREADY_INSTALLED_SMALL_MODEL
export TTGL_TASK_ANALYSIS_URL=http://127.0.0.1:11434/api/chat
```

The adapter requests structured JSON, disables streaming, bounds the output and
records the local server's reported counters. Only loopback HTTP endpoints are
accepted; URL credentials and redirects are refused. Apply the repository's
security policy before separately installing a model/runtime. These variables
must be set on the workspace/MCP process, not inside collected task text.

The current managed workspace rejects `chatgpt.com` through its outbound policy.
Thus live native model completion has not been verified here. Tests exercise a
real local HTTP protocol fixture and a separate explicit CLI fixture; neither
is reported as real-model inference or validation of summary quality.

## Search and progressive MCP access

The existing `ttgl-analyst` stdio MCP now advertises these tools. Restart an
existing MCP client to load the updated definitions; its configured data/source
paths remain the scope of access.

- `search_task_history`: compact task summaries, matching subtask IDs, status,
  project and activity filters, and bounded pagination. Use `status=completed`
  to focus on past completed work; the default includes other states.
- `get_task_history`: task and latest subtask summaries. Supply a returned
  `subtask_id` to fetch a page of exact source step IDs/metadata. It rejects
  subtasks from another task or an older version.
- `read_evidence`: existing bounded source retrieval by a returned step ID.
- `analyze_task_history`: explicitly invokes the configured small model and
  returns an attempt ID/status. Poll `get_task_history` for progress.

Example with the existing CLI (no extra MCP SDK):

```sh
python3 tools/usage-monitor/observability/analyst_cli.py search_task_history \
  --args '{"query":"pagination regression","status":"completed","limit":10}'
python3 tools/usage-monitor/observability/analyst_cli.py get_task_history \
  --args '{"task_id":"RETURNED_TASK_ID"}'
```

Pass the existing `--data`, `--codex-root`, and `--capture-root` flags when using
nondefault source locations. Search is restricted to that store; it does not
silently crawl other computers or publish private histories.

Keyword search uses SQLite's built-in FTS5 for interpreted evidence, with bound
parameters and safely quoted lexical terms. It invokes no model. Semantic search
is opt-in and uses an existing local Ollama-compatible embedding endpoint:

```sh
export TTGL_HISTORY_EMBEDDING_URL=http://127.0.0.1:11434/api/embed
export TTGL_HISTORY_EMBEDDING_MODEL=YOUR_ALREADY_INSTALLED_EMBEDDING_MODEL
```

Vectors are cached by analysis ID, exact embedding model, dimension and document hash. Documents include task metadata and subtask summaries/tags, bounded to 24,000 characters. Metadata changes invalidate the document cache. Semantic mode ranks whole task documents; keyword mode also returns matching subtask IDs.
Dimensions, finite values and nonzero vectors are validated; incompatible vectors
are not compared. Cosine similarity is a retrieval score, not confidence that an
experience applies. Search is bounded to 50 candidate tasks for semantic mode;
narrow project/status scope first for larger stores. The first query can generate
missing embeddings; subsequent queries reuse them. Endpoint absence is an explicit
error, not a silently substituted “semantic” keyword result. HTTP semantic search
uses the same-origin POST endpoint because it can invoke embedding computation.
MCP semantic callers explicitly select `mode=semantic`.

## Storage and UI choices

The authoritative task/turn/assignment data already resides in the private local
`workspace.sqlite`. The new versioned hierarchy, FTS index, job state and optional
vectors extend that store with additive migrations and foreign keys. This keeps
history available offline without installing another database client or coupling
task definitions to Langfuse's private application schema. PostgreSQL/pgvector
would be a reasonable shared-service migration when cross-machine serving and
access control require it; ClickHouse remains appropriate for high-volume measured
telemetry. Neither database is modified by this feature.

The app already uses pinned EVLV DOM/collection assets. The new search page,
expandable subtask cards, source drill-down and responsive modal reuse those tokens,
buttons and styles. React/shadcn is not installed just to wrap this existing DOM
app. All model/source text is escaped before rendering. No new runtime dependency,
new trace UI, global configuration overwrite or scheduled inference is introduced.

## Verification

```sh
python3 -m unittest discover -s tools/usage-monitor/observability -p test_task_history.py
python3 -m unittest discover -s tools/usage-monitor/observability -p test_workspace.py
TTGL_BROWSER_QA=1 python3 -m unittest discover -s tools/usage-monitor/observability -p test_task_history_browser.py
```

The optional browser test uses existing Playwright and system Chromium, never
auto-installs them, and explicitly labels its CLI model response as a fixture.
It exercises task discovery, the analysis/background-process flow, subtask/source
drill-down, retained raw evidence, tag search, empty results and a 390px mobile
modal. A local HTTP fixture verifies the Ollama structured protocol and ensures
failed validation retains its consumed counters. Other tests cover exact step
coverage, stale snapshots, cross-task rejection, search scope/pagination, migration,
no automatic retry, semantic dimensions, local-only endpoints and HTTP origin checks.
