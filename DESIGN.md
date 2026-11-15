# TTGL design system

Adapted from the supplied “Vercel Geist, applied to Claude Mining” reference. These standards apply to the Usage Observatory's native DOM controls and Python-served UI.

## Principles

Use a near-white canvas, near-black ink, 1px hairlines, tightly tracked headings at weight 600, and uppercase mono eyebrows. White cards sit in precise grids with a whisper of shadow. Color is reserved for links, focus, status, charts, and a faint hero mesh behind the overview title.

Use the app half of the system: 6px control corners, 12px cards, and mono section labels. Fully rounded marketing CTAs belong only on marketing surfaces. Do not fill ordinary surfaces with accent colors, stack decorative shadows, or introduce a second decorative system.

## Colors

| Token | Light | Dark |
| --- | --- | --- |
| `ink`, `primary` | `#171717` | `#ededed` |
| `on-primary` | `#ffffff` | `#0a0a0a` |
| `body` | `#4d4d4d` | `#a1a1a1` |
| `mute` | `#737373` | `#a1a1a1` |
| `faint` | `#a1a1a1` | `#737373` |
| `canvas` | `#fafafa` | `#0a0a0a` |
| `canvas-elevated` | `#ffffff` | `#111111` |
| `hairline-soft` | `#f2f2f2` | `#1a1a1a` |
| `hairline` | `#ebebeb` | `#2e2e2e` |
| `link` | `#0070f3` | `#3291ff` |
| `link-deep` | `#0761d1` | choose explicitly with contrast validation |
| `link-soft` | `#d3e5ff` | choose explicitly with contrast validation |
| `error` | `#ee0000` | `#ff6166` |
| `error-deep` | `#c50000` | choose explicitly with contrast validation |
| `warning` | `#f5a623` | choose explicitly with contrast validation |
| `warning-text` | `#a35200` | choose explicitly with contrast validation |
| `success` | maps to `link` | maps to `link` |

Choose dark colors by semantic role, never by automatic inversion. Validate text contrast for each actual foreground/background pair.

The reference's original muted gray `#8f8f8f` has only about 3.3:1 contrast on white. Use `#737373` for small metadata text (about 4.7:1 on white); reserve faint gray for placeholders and decorative marks.

Hero illustration accents: violet `#7928ca`, cyan `#50e3c2`, pink `#ff0080`, and magenta `#eb367f`. Reference gradient pairs: develop `#007cf0` to `#00dfd8`, preview `#7928ca` to `#ff0080`, ship `#ff4d4d` to `#f9cb28`. Keep the overview mesh faint and behind the title. Chart series may use a separate color-vision-deficiency-validated categorical palette; status colors stay distinct from series.

## Typography

Prefer Geist Sans and Geist Mono. If unavailable through the project's approved dependency source, use Hanken Grotesk and JetBrains Mono, or system sans/mono fallbacks. Do not add a public registry dependency solely to obtain a font when the project uses an internal registry.

| Token | Size / line height | Weight | Tracking | Use |
| --- | --- | --- | --- | --- |
| `display-xl` | 48 / 48px | 600 | -2.4px | Hero headline |
| `heading-lg` | 32 / 40px | 600 | -1.28px | Page headings |
| `heading-md` | 20 / 28px | 600 | -0.4px | Card headings; long page titles |
| `label-sm` | 14 / 20px | 500 | -0.28px | Strong labels |
| `mono-eyebrow` | 12 / 16px | 500 | 0 | Uppercase section, breadcrumb, filter, field, and KPI labels |
| `body-lg` | 16 / 24px | 400 | 0 | Lead paragraphs |
| `body-md` | 14 / 20px | 400 | 0 | Body and table cells |
| `body-sm` | 12 / 16px | 400 | 0 | Captions and metadata |
| `button-md` | 14 / 20px | 500 | 0 | Button labels |
| `code` | 14 / 20px | 400 | 0 | Monospaced code |

Use mono for code and eyebrows only. Headings use 600, buttons and labels 500, other text 400.

## Layout and depth

- Spacing uses a 4px base: 4, 8, 12, 16, 24, 32, 40, 64, 96, 128px.
- Radii: controls 6px; cards/code blocks 12px; large panels 16px; badges/avatars fully rounded; marketing pills 100px.
- Level 0: 1px hairline border.
- Level 1: hairline plus `0 1px 1px rgba(0,0,0,.04)`.
- Level 2: hairline plus `0 2px 2px rgba(0,0,0,.04), 0 8px 16px -4px rgba(0,0,0,.04)`; use for menus, drawers, popovers, and tooltips.

## Component mapping

| App element | Treatment |
| --- | --- |
| Page title | `heading-lg`; long titles use `heading-md` |
| Card | White/elevated surface, hairline, 12px radius, 24px padding, level 1 |
| KPI strip | One card divided by hairlines; values 32px at 600 |
| Primary button | Ink fill, on-primary text, 6px radius |
| Secondary button | Elevated surface, ink text, hairline, 6px radius |
| Input/select | Elevated surface, hairline, 6px radius; visible link-blue focus ring |
| Range switch | Soft-fill track with elevated active segment |
| Status badge | Full radius, soft wash; complete/success uses link blue |
| Drawer/popover/tooltip | Elevated surface, hairline, level 2 |
| Sidebar | Canvas, right hairline, body-gray links; active ink on soft fill |
| Link | Semantic link blue |
| Overview header | The app's sole decorative mesh gradient |

Semantic color and font tokens live in `tools/usage-monitor/observability/ui.css`; layout lives in `workspace.css` and `work-explorer.css`. The app uses the existing pinned Geist Sans and JetBrains Mono assets, with system fallbacks. It retains the native DOM adaptation of shadcn/ui and its accessible controls. No Next.js or new component dependency is needed. Preserve keyboard focus, accessible names, and readable contrast throughout.

The overview bloom is confined to the Work explorer header with no task selected. Chart and timeline colors encode data rather than decoration. Task KPI values share one hairline-divided surface. Completed/passed status badges use the semantic link wash; command completion alone does not establish task success.

For small links and status text, `--link-text` uses `#0761d1` in light mode.
The supplied `#0070f3` has about 4.36:1 contrast on `#fafafa` and 3.56:1 on
`#d3e5ff`; the deeper text color provides at least 4.5:1 on both. Link/focus
accents remain `#0070f3`. Warning text uses deep amber rather than the warning fill.

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
