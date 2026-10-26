# Host cleanup, 26 October 2026

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
