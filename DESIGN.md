# Observatory design system

The supplied Vercel Design Language Reference informs controls and surfaces; the Claude Mining screenshots govern page structure, chart colors and analysis density. Shared controls and layouts apply it across analysis, task evidence, optimization and steering pages.

## Principles

Use an achromatic canvas, restrained typography, consistent spacing and shadow boundaries. Blue identifies links and keyboard focus. Use blue, green, amber and the shared categorical palette for data charts, as in the screenshots. Keep ordinary surfaces neutral and status/category markers small. Avoid decorative gradients, hatch patterns, entry animations and moving buttons.

Preserve the application's evidence semantics: unknown values remain unknown, estimates remain distinct from cash expense, and command completion does not establish task success. Styling must not change measurements or launch inference.

## Colors

| Role | Light | Dark |
| --- | --- | --- |
| Canvas | `#fafafa` | `#0a0a0a` |
| Elevated surface | `#ffffff` | `#111111` |
| Primary text | `#171717` | `#ededed` |
| Secondary text | `#4d4d4d` | `#a1a1a1` |
| Small metadata | `#737373` | `#a1a1a1` |
| Interactive accent | `#0072f5` | `#3291ff` |
| Small link text | `#005fcc` | `#3291ff` |
| Input focus | `#005fcc` | `#70b5ff` |

Use the deeper light-mode blue for small links and readable gray for placeholders rather than the reference's faint gray. Validate actual foreground/background pairs rather than automatically inverting colors.

Status dots use information blue `#0062d1`, success green `#398e4a`, warning amber `#ff990a` and error red `#e5484d`. Dots are 8px with neutral adjacent text; labels must carry the meaning independently of color. Charts use shared categorical tones, labels and interactive evidence. Treemap labels select a contrasting foreground for their fill. Unknown heatmap cells have a dashed outline; rework paths use dashed amber strokes.

## Typography

Use the existing bundled Geist Sans. Mono text prefers locally available Geist Mono, then platform monospace fonts; no new font dependency is required. Use mono for code and uppercase eyebrows, sans for labels and numeric tables. Tabular figures align numeric columns.

| Element | Size / line height | Weight | Tracking |
| --- | --- | --- | --- |
| Overview heading | 32 / 40px | 600 | -1.28px |
| Page heading | 32 / 40px | 600 | -1.28px |
| Section/card heading | 16 / 24px | 600 | -0.32px |
| Lead/body | 16 / 24px | 400 | normal |
| Controls | 14 / 20px | 400 | normal |
| Dense table cells | 12 / 18px | 400 | normal |
| Captions | 12 / 16px | 400 | normal |
| Mono eyebrows | 12 / 16px | 500 | normal |
| Code | 13 / 20px | 500 | normal |

Keep weights within 400, 500 and 600. Overview headings reduce to page-heading size on narrow screens.

## Layout and depth

- Use a 4px spacing base, 24px page margins, 16px section gaps and compact table controls. Narrow screens use 16px page/card padding.
- The desktop utility bar is 40px high and the sidebar is 192px wide; mobile navigation retains its horizontal layout. Standard and wide width tokens are 1200px and 1400px; analysis pages use the wide layout.
- Controls have 6px corners, cards 12px, and badges fully rounded corners.
- Surface boundaries use a 1px shadow ring rather than a CSS border. Row boundaries use inset shadows. Separate sections with whitespace.
- Cards use the shared boundary plus a subtle 1px depth shadow. Menus and dialogs use layered elevation tokens.

## Component mapping

| App element | Treatment |
| --- | --- |
| Card | Elevated neutral surface, shadow boundary, 12px radius, 16px padding |
| KPI strip | One shadow-bounded surface with inset dividers; values at weight 600 |
| Ordinary button | Transparent ghost treatment, 40px default height, 6px radius |
| Primary action | Ink fill with inverse text, including hover and active states |
| Compact list control | 28px height; row links use their text height |
| Input/select | Transparent surface, shadow boundary, 6px radius, thin blue focus outline |
| Keyboard focus | Double ring: 2px surface-colored gap and 4px blue outer ring |
| Status badge | Neutral text and transparent background; small colored dot |
| Sidebar | Canvas with a shadow separator; neutral hover/active surfaces |
| Chart | Shared categorical fills with contrasting labels; neutral tracks and gridlines |

Hover transitions change colors over 120ms. Buttons retain their position and size. Reduced-motion behavior and forced-color focus remain supported.

Semantic tokens and native controls live in `tools/usage-monitor/observability/ui.css` and `ui.js`. `design-language.css` is loaded last to align all page modules with the screenshot density; `chart-theme.js` provides shared chart fills, matching label colors and category dots. Page-specific layout remains in the existing stylesheets. This extends the existing native adaptation of shadcn/ui without adding a framework or dependency.

## Record lists

Every record list uses `tools/usage-monitor/observability/data-list.js`, including
page tables, dialog evidence, history/subtasks, suggestions, Impact comparisons,
chart source values and selectable analysis queues. Page modules supply column
schemas, data and actions; they must not implement table markup, filtering,
sorting or pagination. Charts, navigation and explanatory prose remain semantic
visuals/text rather than record lists.

The shared component owns global search, per-column text/numeric filters,
three-state sorting with unknown values last, column visibility, saved preferences,
10/20/50/100-row pages, page navigation, empty states and keyboard-accessible row
actions. Use stable unique list IDs, including separate IDs for a page and an open
dialog. `sourceList` and `selectionColumn` reuse the same renderer; selections are
kept by record ID across search, sort and page changes. List controls are buttons,
not form submissions. Native popovers keep column pickers accessible inside nested
scrolling lists. Extend this component once when a new collection behavior is
needed; keep one implementation for every page.


Task detail uses a single full-width Steps list with short local timestamps,
compact token counts and source links. Its runtime visualization sits beside the
Tools list; a chart is a visualization, not a second paginated Steps table.
Story, Evidence, Prompt and Outcome use collapsible cards. Source collection is
an additional tool that loads only when expanded. Inline evidence lists use the
same record component with collapsed search/column controls; pagination appears
when required. Full lists expose column filters through the Filters button.


Analysis cards share `page-card.js`: native details/summary with visible chevrons,
keyboard collapse and compact header actions. Scope bars use 1d/7d/30d/90d/All
segments; Tools uses the same segmented treatment for area measure. Impact keeps
change details on the left and compact four-column shared comparisons on the
right. Half-width tables fit their card; full Steps and turn tables keep readable
source/prompt widths and scroll internally when required. Retained inline images
use a two-column thumbnail gallery with an original-size modal and source step.
