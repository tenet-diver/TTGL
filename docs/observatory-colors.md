# Observatory semantic colours

Observatory uses its existing shadcn Badge, shared TanStack DataTable and Recharts
components. A small product adapter supplies the missing identity-to-colour mapping;
no new UI package or runtime dependency is installed.

The [EVLV token source](https://github.com/tenet-diver/design-system/blob/develop/tokens/design-tokens.json)
was read on 16 November 2026 (Git blob `ee2f7a1e2e382254cb4b57745d4b0974614368b5`).
The reader/native positive, AI and warning roles and foundation error/secondary
roles supply dark semantic colours: green `#82D6A2`, teal `#83D5DF`, warning
`#FF9F0A`, error `#FF9494` and neutral `#B5B5B5`. Observatory's existing activity
accents extend those roles for categorical data. These activity assignments are
the product adapter, not additional upstream EVLV token definitions. Light text
variants preserve the roles with darker foregrounds; acceptance checks target
desktop dark theme only.

| Activity | Accent | Retained aliases |
| --- | --- | --- |
| Explore | Blue | Investigate |
| Implement | Green | |
| Verify | Yellow | Test |
| Deliver | Orange | Operate |
| Debug | Pink | |
| Coordinate | Teal | |
| Research | Violet | |
| Plan | Lime | |
| Other / unknown | Neutral | Unclassified, Uncategorized, Unreviewed |

Legacy Review uses violet and Document uses teal so the eight activity types
present in the migrated corpus are visually distinct. Start/End boundaries stay
neutral. Retained labels and evidence are preserved; colours do not merge groups.

The same activity mapping colours subtask badges, phase bars and their legends,
process nodes/forward paths, activity charts, step-table accents and native step
timelines. Steps expose an Activity column backed by existing source-linked
interpretations/rules. Colour does not create a new interpretation.

Statuses have a separate vocabulary: green for recorded completion/pass/retention,
blue for active work, yellow for pending work, amber for warnings/blocked/uncertain,
red for explicit failure/errors, and neutral for cancelled/unavailable/unknown.
Exact enumerated values and explicit legacy aliases select the colour. Arbitrary
acceptance prose is neutral; mentioning a failure does not label a task failed.
Status icons and the original labels remain visible. A tool error marks its native
step without changing the activity colour or inferring task failure.

Model and tool identities select stable accents independently of rank, filters or
chart order. Tool treemaps, daily stacks and tables use the same tool mapping;
model stacks, model tables and turn blocks use the same model mapping. Finite
palettes can repeat across many tool identities, so labels and legends always
remain. Token partitions have fixed colours as well. Heatmap colour intensity
continues to encode magnitude rather than category. Dashed process paths remain
amber and dashed to distinguish returns from forward moves.

The registry is `apps/web/src/lib/semantic-colors.ts`, theme values are in
`apps/web/src/styles/semantic-colors.css`, and `SemanticBadge` adapts the existing
Badge. New record lists inherit the mapping from the shared DataTable. Keep
selection/filter values and raw evidence unchanged when adding a colour role.
