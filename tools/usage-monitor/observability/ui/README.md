# Observatory components

The workspace follows the repository's `DESIGN.md`: Geist, JetBrains Mono,
neutral surfaces, restrained workflow color, shadow borders, 6/12/18px radii,
responsive layouts, and reduced-motion support.

`../ui.css` translates the pinned MIT-licensed **shadcn/ui New York** component
styles to native CSS. `../ui.js` shares Button, Badge, Empty and Skeleton markup
across the dashboard and task history, and applies Dropdown Menu styles to the
existing keyboard-accessible popover. Input, Native Select, Textarea, Table, Card
and Dialog styles are shared by both views. Semantic tokens and `data-slot`
attributes follow shadcn conventions.

This is a **native-DOM adaptation**, not the official React/Radix runtime. The
current Python-served application uses HTML templates and delegated events;
shadcn's React components cannot mount directly into that structure. Translating
these visual primitives avoids a second renderer, new build/runtime dependencies,
and a rewrite of existing task workflows. Existing private EVLV collection and
popover behavior remains in use; its CSS is no longer loaded. No private source
is redistributed here.

Upstream versions, source hashes, review scope and licenses are recorded in
`sources.lock.json` and the adjacent license files. Fonts and the selected Lucide
SVG paths are served locally. There are no browser CDN requests, paid services,
installation scripts or added runtime packages. These MIT/ISC/OFL assets have no
subscription pricing or free-tier limits. Public source notices were inspected
on 2026-11-12; this scoped static-asset review does not audit the unused upstream
CLI or npm dependency tree.

The concrete radius tokens and shadcn control sizing take precedence over the
template's conflicting prose about pill-shaped cards. Pills are used for badges;
rectangular tables/forms keep usable corners. Light is the default. The top-bar theme toggle works at every viewport size;
its local preference is applied before styles paint and synchronized across tabs.
Tables share per-column filters and three-state sorting, including evaluation
tables in dialogs. Filters combine before pagination, use displayed derived
values, and support numeric comparisons. Table preferences are stored locally;
Reset table clears search, filters and sorting.

With already reviewed Playwright/Chromium available, opt-in workflow checks run
against temporary stores (no real inference):

```sh
TTGL_BROWSER_QA=1 TTGL_CHROMIUM=/path/to/chromium \
  python3 -m unittest discover -s tools/usage-monitor/observability -p '*browser.py'
```

The UI refresh passed the 40 workspace/history unit checks and workspace/history browser
workflows on 2026-11-12, including all 11 views at 1440, 768 and 390px widths.

## Task-centered explorer (12 November 2026)

The current navigation is **Work, Analytics, Knowledge, Settings**. Work starts
with task summaries and opens an inline task → subtask → step hierarchy. Select
a subtask to scope the chronological duration chart. Click a step checkbox to
open the optional manual-group form. Raw evidence is fetched only on inspection.
Collection permission, projects, unassigned prompts and Codex findings are in
Settings; research records and backend APIs are retained. Old overview/activity
bookmarks open Work; old history bookmarks open Knowledge.

The optional Work table retains per-column sorting, filters and visibility.
Theme, display mode, search/type/status, attribution and table preferences persist
locally. Task batches contain at most 100 tasks, with previous/next controls;
column sorting/filtering applies to that batch, while the work search and
analytics cover the full selected project/scope. Inline drill-down stays stable
until Refresh, except while a user-requested mining job is active.

“Mine with Luna” invokes the existing bounded analyzer on demand: one structured
response supplies a task type, summary, complete step partition and optional
knowledge candidates citing retained step IDs. It includes sanitized visible
input/result excerpts from at most the first 40 steps (1,600 characters each,
48,000 total), alongside the bounded metadata snapshot (2,000 steps maximum).
Missing or truncated evidence is explicit. No tools, model retries, automatic
page-load inference or scheduled mining are added. The attempt saves schema,
evidence excerpts, output and reported counters locally. A changed snapshot
invalidates publication. Knowledge remains an unverified interpretation, with
source links, and is not automatically injected into an agent's memory.

Analytics uses native response counters at task scope. Manual groups override
model suggestions for a canonical partition so each tool step counts once.
Subtask tokens and cost are unknown by default. Optional **step-share** allocation
distributes each turn's counters by the count of tool steps in each subtask; this
is an estimate, not measured inference attribution. Model-only turns remain
unattributed. Recorded operation durations can overlap; identified service
lifetimes are excluded and reported separately. Unreviewed operations may still
contain service lifetime. Missing counters/prices remain unknown. Model-rate
scenarios use user-entered exact-model rates and dates, never inferred cash
charges. Naming/mining usage is separate overhead; missing usage is not zero.

The Knowledge catalog offers local explorer bookmarks for existing Mem0,
Cognee, Graphiti and Letta deployments. It does **not** install services, configure
API adapters or export activity. Sources inspected 2026-11-12:

- [Mem0 SDK and Apache-2.0 license](https://github.com/mem0ai/mem0)
- [Archived older OpenMemory UI](https://github.com/mem0ai/openmemory/blob/main/openmemory-archive/README.md)
- [Cognee project](https://github.com/topoteretes/cognee)
- [Graphiti, including database/UI options](https://github.com/getzep/graphiti)
- [Letta ADE (currently legacy V1 docs)](https://docs.letta.com/v1-sdk/ade)

These are discovery links, not deployment or managed-plan recommendations; no
paid plan or free tier is assumed. Installation needs its own dependency review.
There is no single representation declared optimal by this UI. The existing
SQLite records/FTS and analyzer are reused; the product-specific hierarchy and
small bar/timeline charts use native DOM/CSS to avoid introducing a second app
renderer or chart dependency stack. This preserves the shared shadcn-derived
controls. No new dependencies were installed for this revision.

Validation adds six hierarchy-accounting/knowledge-contract checks to the
existing 46 unit checks, plus four browser workflows covering the current four
views at desktop/tablet/mobile widths. Model-backed workflows use an explicit
fake native CLI; they establish wiring and accounting, not live Luna quality.
Private screenshots and runtime receipts remain in `work/security/ui-review-20261112`.

## Tables and log backfill (12 November, later update)

Entity lists now use the shared table: tasks, subtasks/recorded turns, source steps
and model responses, knowledge candidates, and explorer integrations. The card
list/toggle is removed; old saved display preferences cannot restore it. Sorting,
column filters and column visibility remain local preferences. Common usage
columns show tool steps, model responses, recorded tool runtime, native tokens,
and the API-equivalent estimate. Supporting columns remain available in Columns.
Sorting/filtering can replace the table DOM without losing row drill-down or
explorer editing. Timelines and statistical charts remain visual.

The missing-data audit found that activity since November 9 had not been
assigned to tasks. `task_discovery.py` adds opt-in, idempotent discovery by native
session identity, with the first retained prompt as the task name and recorded
turns as provisional subtasks. It uses only unassigned turns, preserves existing
human/research assignments, follows collection pause, and performs no inference.
Work's “Discover tasks from logs” enables it; the existing collection watcher
then attaches future activity. The actual local backfill created 754 tasks and
assigned 818 turns without changing any source event. Session boundaries are
provisional organizational boundaries, not a claim of semantic task identity or
verified completion. Nothing changes the frozen experiment artifacts or research
monitoring schedule.

Unmined work now shows recorded turn groups, including response-only turns.
Their tokens and token-rate estimates are measured/derived from those exact turn
responses rather than guessed step shares. Semantic groups retain unknown token
attribution unless step-share estimates are selected. The source-step table
includes both tool events and model responses; only response rows have native
model counters. This keeps model-only work visible. Manual/model groups take
precedence over remaining logged turns, preventing duplicate accounting.

When no custom scenario is saved, a dated Standard API-equivalent token scenario
covers the two observed models. Current sources were opened and checked on
2026-11-12: [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
and [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
Per million: Sol input/cached/output = $2/$0.10/$10; Luna = $0.10/$0.01/$0.50.
Above 272K input tokens, the scenario applies 2× input/cache and 1.5× output.
This is a current-price counterfactual applied to retained usage, not historical
quotes or subscription cash expense. Unrecorded cache-write fees, paid tools,
region and service premiums remain outside this token scenario. Custom scenarios
still take precedence. Partial known totals are labeled as partial; missing
prices/counters do not become zero. The editor loads from a dedicated bounded
rates endpoint and stays disabled until loaded to prevent overwriting edits.

Live validation preserved a pre-inference source-import failure and a metered
Luna result rejected for duplicate step ownership. The next contract maps every
short source alias to exactly one subtask index; canonical IDs are restored
locally with the mapping and raw/decoded output retained. Two **different** real
logged tasks completed with this contract (23,317 and 21,083 reported tokens).
The rejected model call's 25,790 tokens remain mining overhead too. No started
model assignment was silently repeated, and no rejected output was published.
No broad model-quality or cost-saving claim follows from these plumbing checks.

Current validation: 59 unit checks plus four browser workflows, including a clean
server-process regression for source loading, idempotent discovery, preserved
assignments, model-only accounting, long-context rate arithmetic, exact source
coverage, and row actions after sorting/filtering. Private receipts, raw attempts,
and live table screenshots stay in `work/security/ui-review-20261112` and the
workspace's private task-history attempt directory.

Live overview mining accepts strictly appended steps while retaining its original
analyzed snapshot and marking the interpretation as needing refresh. Changes to
existing steps, goals, names or other task facts still reject publication; added
steps remain visible as unmined log groups. Recorded prompts from at most 20
assigned turns (2,000 sanitized characters each) provide request context. This
lets a human inspect an ongoing conversation without freezing collection.

The larger backfill also exposed repeated unindexed joins and one SQLite
connection per task. The overview now uses indexed assignment/annotation lookups
and one consistent read transaction. A local 1,252-task snapshot returned in about
one second after these changes; this is a diagnostic timing, not a general
performance benchmark.

The longer current UI conversation produced a fully covered 315-step assignment
plus one empty proposal. Its failed validation and 89,920 reported tokens remain
unchanged. A separately recorded derivation omits only that empty proposal,
retains every supported step assignment, and publishes the four supported groups
without further inference. The UI labels this derivation; the original failed job
and raw response remain visible. Future decoding omits unsupported empty groups
before publication and records that derivation too. The local recovery helper
requires the exact retained output, source-alias map and known failure condition;
it cannot turn an arbitrary failed model attempt into a successful one.

## Latest-ten review and always-available measurements

The user-requested latest-ten review freezes task IDs in activity order before
starting inference. `task_review.py` runs at most two existing Luna miners at a
time, with one attempt per task and no automatic retries. Its manifest lives in
the private workspace task-reviews directory and is mirrored in settings for the
UI. Unchanged analyses can be reused without another model call or counting old
usage as new batch overhead. This is a finite explicit review, not scheduled
monitoring. The actual registered review completed all ten entries, with no
failed assignments; its metered mining overhead is separate from source tasks.

Overview mining now includes both tool events and model-response records. A
response-only task has one recorded step and zero tool calls, rather than zero
steps. Large inputs use at most 64 contiguous record blocks; the saved alias
ledger expands every block back to the exact native IDs. Blocks are indivisible
for that interpretation. Single-response work need not be split into invented
internal stages. Up to 40 evenly spaced sanitized record excerpts and 20 user
requests supply bounded context. No raw model reasoning is included.

For these analyses, subtasks own explicit response records, so tokens and the
API token estimate follow those records. The association of a response with a
subtask remains an LLM interpretation; the native counters themselves are not
estimated. Tool-only groups have no independently recorded model usage. Legacy
step-share estimation is not applied again to already assigned response records.
The ten-task audit checks unique complete ownership of every captured record and
conservation of current steps, tokens, and scenario cost across groups.

Every task, including one never sent to a model for classification, exposes:

- Total recorded steps, with tool calls and model responses distinguished.
- Recorded tool runtime and a separate elapsed lifecycle span (including gaps).
- Native tokens and the dated API-equivalent token estimate where rates exist.
- Per-operation call/runtime counts and per-model response/token/cost tables.
- Recorded-turn groups and the paginated raw step/response table.

The last-ten cohort is reachable through **Show reviewed tasks** and the `review`
URL parameter. **Show all tasks** restores the entire collection. This explicit
scope navigation clears row-search filters while preserving theme, sort and
column choices. A summary line in each task row makes interpreted work visible
without adding cards. Unclassified tasks open their raw-record section directly;
classification is never required to inspect measurements.

The observed latest ten comprise two longer conversations and eight single-
response maintenance operations. Each of the latter correctly reports zero tool
calls, while still showing its response, elapsed span, tokens and estimate. No
successful benchmark or task outcome is inferred from a classification. Raw
outputs, aliases, manifests and audit receipts remain private.

The completed review has private per-task source-ownership and accounting audits.
Validation for this revision passes 63 unit checks and five browser workflows.
A live browser check confirms all ten reviewed rows, return to the full task
collection, and unprocessed-task measurements/source drill-down at desktop and
390px widths. Long raw requests are collapsed beneath the summary so measured
data appears first, and arbitrary unbroken log text wraps without page overflow.
Response-only tasks show a model-record table instead of a misleading empty tool
timeline. Classification remains an interpretation of sampled historical logs,
not an independently verified current research outcome.

Core step, tool-call, elapsed-span, token and cost columns precede administrative
columns, so they remain visible on desktop without scrolling past classification
metadata. Saved column visibility and sorting are retained.
