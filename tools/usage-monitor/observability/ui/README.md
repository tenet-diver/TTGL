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
