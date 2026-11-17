# Local view preferences

Observatory reuses the browser's localStorage, Next.js URL navigation and the
existing controlled TanStack tables. No persistence package, server setting or
database migration is needed. Preferences belong to this browser profile and
application origin.

- Date range, project, workspace and display timezone carry across dashboard pages
  and return on a bare URL or reload.
- Model, activity and day list filters, tool family/action and treemap measure are
  remembered per page. Active list filters remain visible and have clear buttons.
- Each table remembers its search, column filters, sort/direction, page size,
  current page, visible columns and whether the filter row is open. Table identities
  include the record kind so different chart drilldowns keep independent settings.
  Existing table preferences are read as a fallback on first use of the new key.
- Expanded/collapsed panels, chart daily/average switches, source-value disclosure,
  process-map connection count and theme are also remembered.

Explicit supported URL values override the corresponding saved preference.
An explicit empty value clears a remembered filter. Changing a tool family does
not inherit an incompatible old action. Task/subtask evidence URLs keep their own
scope; transient source IDs, selections and open evidence dialogs are not saved.
Scope restoration finishes before showing dashboard contents, so a restored range
does not briefly display a different range's data.

Table Reset restores its default query, columns, page size and filter row and saves
that reset. All projects/workspaces and the clear-filter controls also save their
cleared state. Dates/timezones and cached table values are validated. Malformed
JSON falls back to defaults. Removed columns are pruned while compatible search,
filters and sorting are retained; one bounded metadata read handles old remote
table schemas. The hydration guard prevents a newly mounted table from saving
default/previous-table state over its remembered settings.

Blocked or full localStorage does not break the controls. An in-memory fallback
preserves the current tab's changes when writes fail. A browser that prevents
storage cannot preserve those changes across a full reload or browser restart.
No preference is synchronized to another device or sent to a new service.
