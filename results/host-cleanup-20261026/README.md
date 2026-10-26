# Host cleanup, 26 October 2026

Completed cleanup removed 106 rebuildable cache/dependency directories and one
clean worktree with a saved Git recovery ref. The removed caches accounted for
56.70 GiB allocated before deletion; shared filesystem blocks mean this is not
a unique-byte reclaim total. Docker separately reported 15.051 GB reclaimed in
the initial prune. Dirty source, unique local artifacts, active CI, credentials
and database volumes were preserved. The completion check records observed
free space with ongoing experiment images loaded.

Removed 47 generated cache/dependency directories, occupying about 22.55 GiB
before removal. Docker image pruning reported 7.495 GB and build-cache pruning
7.556 GB reclaimed. These rounded figures are different accounting sources;
they are not a precise filesystem free-space delta. Free space increased from
about 13 GiB to about 50 GiB before benchmark image downloads.

Inspected the calorie-budget worktrees. Removed one clean secondary checkout
with no ignored artifacts and preserved its HEAD at the recovery ref recorded
in `report.json`. All dirty worktrees remain. Other checkouts contain local
ignored artifacts and were retained. Source files, database volumes, native
test logs/results, SwiftPM recovery directories, Android SDK, authentication,
Codex runtime and previous experiment evidence were preserved.

`report.json` records every cache path, allocated size before removal, recovery
ref, preservation checks and the observed free bytes during setup. Some caches
were subsequently recreated by ordinary use; the report lists those observed
at verification. Cleanup does not disable or stop the existing CI runner.

A later pass removed the inactive Cypress 12.9.0 downloadable binary cache
(0.50 GiB allocated). The ongoing experiment also deletes its own completed
images and reclaims unused Docker VM blocks. The active native CI workload is
preserved; its changing resource use means the initial free-space gain is not
a promise of continuously available capacity.

The second cache pass also removed 1.31 GiB of Chrome HTTP/code/image caches
and npm content-addressed downloads. Chrome profiles, cookies and persistent
Storage directories were not touched. Additional cache removals total 1.82 GiB
allocated before deletion and are itemized in report.json.

A further 51 ignored node_modules directories were removed from temporary
calorie-budget pre-push verification checkouts older than one day. Each unit
was checked for live command/open-file references and tracked files before
deletion. Their source checkouts, package manifests and logs remain. All 51
dependency paths were verified absent afterward; all 51 package manifests
remain. These dependencies accounted for 32.33 GiB allocated before removal.
Allocated counts may share filesystem blocks and are not a claim of unique
physical bytes reclaimed. The report records observed free space separately.
