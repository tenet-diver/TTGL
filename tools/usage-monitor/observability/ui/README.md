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
