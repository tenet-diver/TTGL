# Observatory architecture

The current app is a Next.js App Router application in `apps/web`. React and
TypeScript render actual shadcn/ui components, TanStack Table renders every record
list, and Recharts renders data charts. The supplied photos govern the compact
sidebar, summary strips, paired chart cards, shared tables and inline task story.
The [former Python architecture](legacy/python-workspace-architecture-20261115.md)
remains intact for migration compatibility and frozen research.

| Layer | Responsibility |
| --- | --- |
| Next.js server components / route handlers | Scoped page data, bounded reads, validated same-origin mutations and authenticated hook/ingest endpoints |
| Shared React DataTable | Full-cohort phrase search, column filters/natural sorting, pagination, visibility/preferences and stable ID selection; all nested source lists reuse it |
| PostgreSQL | Projects, defined tasks, native turns, assignments, transactional rules/live state, notes, analyses/jobs, evidence, pricing/settings, mutation/hook receipts, provenance and audit |
| ClickHouse | Versioned native analytics events in `ReplacingMergeTree(version)`; scoped queries always use `FINAL` |
| Garage S3 | Original JSONL/request bytes and read-only legacy export snapshots, content-addressed chunks and checked manifests |
| Collector | Changed-file discovery, S3-first retention, native parsing, source reconciliation and transactional outbox delivery |
| Explicit analysis worker | One retained attempt per source snapshot, schema and source-ID validation, separate analyst usage, no automatic model retries |
| Preserved legacy capture / research | Existing source records, transport captures, independent study ownership and active queues; never silently replaced |

## Storage and replay

S3 is the raw evidence store. PostgreSQL stores archive references, exact byte
counts, SHA-256 digests, source identities and retention state. Growing files reuse
complete 4 MiB chunks and get a new ordered manifest; old snapshots remain intact.
Conditional uploads and read-back checks make storage retries safe. No local
object-store fallback, expiration or secret-redaction transformation is applied
to original bytes. Protect the private bucket and application access accordingly.

Parsed native counters remain measurements; costs are configured API list-price
scenarios, not subscription cash. Missing counters, runtimes, tool allocations,
agent identities, screenshot bytes and acceptance evidence stay unknown. Explicit
cache reads are a subset of input; do not add them to native input totals. Native
response IDs deduplicate model usage; cumulative transcript counters are not
additional responses. Main/subagent roles require native identity evidence.

PostgreSQL event identity rows own monotonic versions and immutable workspace,
session/turn and timestamp routing. A transaction commits the identity and pending
outbox together. The dispatcher inserts into ClickHouse and acknowledges only the
matching version. A crash can repeat a delivery; `FINAL` reconciles that repetition.
Conflicting counters or ownership create a reconciliation record, not a silent
replacement. Connection pools are bounded; metadata reads omit large raw payloads.
Task evidence is loaded separately when requested.

## Evidence and interpretation

Defined tasks and source turns are separate units. Assignments use an unambiguous
native session/turn tuple. Model groups cite source event IDs. Process maps use
complete source-linked interpretations; newly published groups retain source
versions so later evidence invalidates their currency. Native tool-command checks
remain distinct from user acceptance and model claims. Raster previews serve
retained bytes only; transcript paths are never opened by a page request.

Impact compares fixed 14-day windows independent of the visible chart range.
New-session changes exclude older sessions only after application. Task metrics
use task cohorts and hourly clusters; supported confidence ranges require sufficient
observations. Unmeasured savings and unsupported cost allocations remain unknown.

## Boundaries

Browsing and collection never invoke a model or restart research schedules. Model
work requires an explicit queued action and separately enabled worker. Hooks use a
shared bearer token and per-event idempotency; UI writes use same-origin requests,
validated payloads, UUID receipts and transactional audit. The local app binds
loopback and expects authenticated access at any remote boundary.

The Garage 2.5.0 candidate has known dependency findings and is not executed.
Deployment needs a reviewed patched build or approved endpoint. S3 protocol-fixture
tests validate application logic, not actual Garage compatibility or multi-node
durability. See [SETUP](../SETUP.md) and the dated dependency receipt for exact
runtime/image choices, migration, operation and validation commands.
