# Observatory application validation — 17 November 2026

Branch `work` was fetched and pulled with `--ff-only`; it was already at the
latest remote commit. Existing unfinished React changes were preserved and
validated together. No historical model attempts were repeated. Research
monitoring and the persisted collection pause remain unchanged.

## Delivered

Restored the exact reviewed application packages, ClickHouse binary and explicitly
approved SILO binary after temporary caches disappeared on Codespace restart.
Fixed the external build cache's missing module-resolution link. Built and
started the production Next.js app on loopback port 3333. PostgreSQL, ClickHouse
and the real local S3 bucket pass health checks. Native import populations remain
1,253 explicit tasks, 1,605 turns and 1,480 retained archives, with zero pending
outbox deliveries.

Finished the missing Experiments history view using PostgreSQL's already retained
legacy archive. The existing TanStack DataTable supplies filtering, sorting,
pagination, visibility, preferences and inspection; no new table system or
analytics dependency was introduced. The product-specific addition projects
proposals, evaluations, reviews and accounting snapshots, deduplicates imported
snapshots and intersects task/project/workspace scopes. The large retained baseline field is omitted from list payloads, with its hash
and archive provenance retained. Long change text has a bounded list preview
and remains complete in inspection. Failed measurements, unknown gates, unrecorded decisions and
implementation state remain distinct. Browsing and inspecting run no model.
See [experiment results and unfinished studies](experiment-inventory-20261117.md).
This read-only delivery does not implement an automatic optimization/trial runner.

## Verification

| Check | Result |
| --- | --- |
| Production webpack build | Pass |
| TypeScript check | Pass |
| Unit tests | 47 pass |
| PostgreSQL/ClickHouse/S3-protocol integration tests | 19 pass |
| HTTP benchmark-runner tests | 5 pass |
| Firefox desktop-dark suite | 30 checks pass, including 22 routes |
| Additional read-only production-data checks | 20 pass |
| Whitespace / patch checks | Pass |

The integration suite checks every exposed record column's include/exclude
filter and both sort directions, now including all four experiment collections.
It verifies archive deduplication, linked-record scope isolation, rejected input,
retained failed gates, subtask event isolation, replay-safe ingestion and exact
raw retention. Test databases and the labeled S3 protocol fixture are separate
from real user stores; fixture results are not real S3 compatibility evidence.

The browser suite uses WebDriver and Python's standard library against the
production build and synthetic test stores. It exercises search, empty results,
clear/reset, paging, numeric filters, both sort directions, persisted queries and
columns, exact-value context filters, subtask timeline filters, source/image
retrieval, persisted rule changes/restoration, form saves and measurement
inspection. Only desktop dark theme is in acceptance scope. The final full run
passes all 30 checks. Earlier harness failures remain private: a header assertion
looked at a sibling table, pointer actions omitted scrolling, a uniqueness
assumption ignored repeated valid prompts, and a field selector edited JSON
instead of notes. Those failures were corrected in the test, not hidden by
changing production behavior. One isolated S3 fixture expired and was restarted;
the real S3 service remained healthy.

Additional production checks exercise 14 nonempty record collections, pagination,
sorting, search, workspace scoping, invalid queries, large read-only POST
selections, native source retrieval and an actual SILO archive download matching
its recorded SHA-256 and byte length. HTTP readiness requires the full 1,605-turn
population. These are application checks, not new agent trials or speedup claims.
Browser/HTTP timings are observational and include their resource regime.

## Security and disk cleanup

Fresh advisory metadata for the unchanged 220-package npm graph has zero matches.
The browser uses an isolated current Alpine Firefox closure: 146 pinned packages,
zero OSV matches and zero current vendor fixed-version matches. No maintainer
scripts ran. Signature/provenance revalidation remains incomplete under the
existing Codespace-specific authorization; this is not full security clearance.
Previously blocked Chrome/Playwright/Garage candidates were not executed. The
specific SILO exception remains as recorded in its dated security receipt.

Relocated 80,214,117 bytes of inactive reconstructible dependency download caches
to temporary storage after per-file hash checks, preserving original paths as
symlinks. Losslessly compressed eight closed memory SQLite snapshots from the
completed repository-memory wave A, saving 100,834,079 logical bytes. Total
reclaimed source storage is **181,048,196 bytes (172.7 MiB)**. Concurrent activity
means net filesystem free-space change can differ. About 2.9 GiB remains free
on the root filesystem at the final observed checkpoint.

Each compressed snapshot has original/compressed SHA-256 hashes, timestamps,
mode and a tested no-overwrite restore implementation. Exact snapshot bytes stay
on durable storage. The main SQLite history, active databases, raw S3 volume,
credentials, native logs, frozen research source and unique result evidence were
not removed. No containers or database volumes were pruned.

Private logs, screenshots, immutable failed observations, download/security
receipts, cleanup manifests and restore instructions are under
`work/security/application-validation-20261117/`. None belong in the public repo.
