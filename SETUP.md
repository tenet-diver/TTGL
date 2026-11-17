# Set up Observatory

The current web application lives in `apps/web` on branch `work`. It uses Next.js
App Router, React, TypeScript, shadcn/ui, PostgreSQL, ClickHouse and local S3.
The preserved Python implementation has a [legacy runbook](docs/legacy/python-workspace-setup-20261115.md).
Do not change frozen research workers or delete existing data volumes.

## Reviewed runtime and packages

Use Node **24.22.2 or a separately reviewed patched version**. The dated
[dependency receipt](docs/security/next-stack-20261115.json) pins the complete
application graph and reviewed database images. Follow the
[security policy](docs/security/dependency-security-policy.md) before installation.
The runtime and npm bundled with an arbitrary Node distribution are separate
candidates: the reviewed host Node 24.19 and npm distributions had known findings.

A reviewed runtime and an independently reviewed package manager can run the
workspace's normal `npm` scripts. In this environment, the small checked installer
materializes the audited lock without executing npm or lifecycle scripts:

```sh
python3 scripts/install-reviewed-web.py
```

It verifies the lock hash against the receipt and every archive's integrity.
Review a changed lock again; the installer refuses an unreviewed graph. No fonts,
UI libraries or scripts are loaded from CDNs at runtime.

For the remaining examples, set `OBS_NODE` to your reviewed Node executable:

```sh
export OBS_NODE=/absolute/path/to/reviewed/node
cp apps/web/.env.example apps/web/.env.local
chmod 600 apps/web/.env.local
```

Replace every secret placeholder with independent random credentials. Do not
commit `.env.local`, object-store configuration, logs, source transcripts or credentials.

## PostgreSQL and ClickHouse

These services use separate named volumes and loopback ports, preserving the old
Langfuse and workspace installation:

```sh
docker compose --env-file apps/web/.env.local -f compose.observatory.yml up -d
"$OBS_NODE" --env-file=apps/web/.env.local --experimental-strip-types apps/web/scripts/migrate.ts
```

PostgreSQL is on **15432**, ClickHouse HTTP on **18123**. Migrations are numbered,
checksum protected and repeatable. Never edit an applied migration; add the next
numbered migration instead. ClickHouse reads use `FINAL` for version reconciliation.

## Local S3 raw-log storage

Set `S3_ENDPOINT`, `S3_REGION=garage`, `S3_BUCKET`, `S3_ACCESS_KEY_ID` and
`S3_SECRET_ACCESS_KEY` in `.env.local` for an explicitly approved **local S3 deployment**. `S3_ENDPOINT` must be a literal
loopback URL, such as `http://127.0.0.1:13900` or `http://[::1]:13900`; remote
hosts and DNS aliases are rejected. Region redirects are disabled. The S3
client uses path-style requests and the maintained AWS SDK. The bucket must exist;
it is not created implicitly by application requests.

The current Codespace uses **PGSTY SILO RELEASE.2026-11-12T00-00-00Z** under the
user's explicit, narrow exception for **GO-2026-5970**. It is not a clean security
clearance or permission to execute another affected artifact. The
[dated runtime receipt](docs/security/local-s3-silo-20261116.json) records the exact
binary hash, provenance, exception and real-server checks. SILO is existing
AGPL-3.0 S3 software; Observatory continues to use the AWS SDK and its existing
chunk/manifest format rather than building an object server. The console is off,
credentials are independent, and the S3 endpoint binds literal loopback only.
The historical alternative assessment is [preserved separately](docs/security/s3-alternatives-20261116.json).

On this already prepared Codespace, inspect or start the pinned server with:

```sh
python3 work/security/observatory-s3-20261116/start.py
```

This validates the recorded approval and binary hash and mounts only its private
persistent S3 volume if needed. It does not download a replacement. The raw volume
and credentials are persistent workspace files; reviewed runtime binaries and npm
packages currently use temporary-disk caches. If those caches disappear, restore
the exact reviewed artifacts before starting. Server-side compression preserves
the original bytes returned by S3; retained files passed checksum read-back.
The sparse 2 GiB volume shares physical workspace capacity. Check both filesystem
and host free space before more collection; no continuous collector was activated.

PostgreSQL stores archive references, not original log bytes. ClickHouse holds
parsed events. Keep these roles when changing the local S3 provider.

The published **Garage 2.5.0** candidate failed the 15 November advisory review,
including Rustls, SQLite, XML and compression-library matches. It was downloaded
for inspection, **not installed or executed**. `compose.garage.yml` intentionally
requires an explicitly approved **patched image digest** and a private absolute
configuration path. It has no unsafe default image. The separate configuration
example is `apps/web/deployment/garage.toml.example`.

After reviewing a patched release and following its documented bootstrap:

```sh
export GARAGE_IMAGE='your-reviewed-image@sha256:YOUR_APPROVED_DIGEST'
export GARAGE_CONFIG_FILE=/absolute/private/path/garage.toml
docker compose -f compose.garage.yml up -d
```

For a fresh single-node development deployment, use that release's `/garage
status`, `layout assign`, `layout apply`, `bucket create`, `key create` and `bucket
allow --read --write` commands to create the layout, `observatory-raw` bucket and
application key. Keep RPC/admin ports private. The example's replication factor
of one is development-only; it does not provide multi-node durability.

Original bytes are split into content-addressed 4 MiB chunks with a checksummed
ordered manifest. Uploads use conditional creation, verify read-back, and retain
older snapshots as files grow. PostgreSQL records archive status and provenance.
Collection and HTTP ingest require verified retention **before** deriving events.
A failed upload does not advance the successful-source ledger. Raw downloads in
Data list reconstruct and check the original bytes. No expiration is configured.

## Start the UI and collection

Next loads `.env.local` from `apps/web`; do not put `--env-file` in `NODE_OPTIONS`:

```sh
"$OBS_NODE" node_modules/next/dist/bin/next build apps/web
"$OBS_NODE" node_modules/next/dist/bin/next start apps/web --hostname 127.0.0.1 --port 3333
```

Open **http://127.0.0.1:3333**. Forward port 3333 privately in Codespaces. Keep this
loopback application behind authenticated access when using a remote deployment;
it does not introduce a new public login system.

The **Experiments** page (`/experiments?range=all`) exposes retained historical
proposals, evaluations, analyst reviews and overhead snapshots from the read-only
legacy import. Inspect rows for protocols, measurements, hashes and provenance.
Browsing does not run a trial. Decisions, implementation and evaluation remain
separate; overhead snapshots can overlap and must not be summed. See the
[experiment inventory](docs/research/experiment-inventory-20261117.md) for results
and unfinished research boundaries.

The pricing editor accepts input/cached/output rates per million tokens and explicit
`write_5m` / `write_1h` rates, or a flat `write` rate. A response with recorded
cache writes stays unpriced if its required write rate is absent.

The dated [API-equivalent scenario](docs/observatory-pricing.md) seeds the empty
setting for the recorded Sol/Luna models and accounts for cached input and Sol's
long-context premium. Existing user rates are preserved. Missing cache-write
counters remain unknown; unrecorded write surcharges are excluded from the base
estimate. Cost bands distinguish Unmetered turns from Unpriced records.

In **Data list**, add an absolute Codex or Claude Code JSONL source folder. Then
run the collector in another terminal:

```sh
"$OBS_NODE" --env-file=apps/web/.env.local --experimental-strip-types apps/web/scripts/worker.ts
```

The worker scans changed JSONL files, retains their exact bytes in S3, parses native
identities and counters, and flushes the PostgreSQL outbox to ClickHouse. Symlinks
are not followed. Malformed sources are recorded as errors, not silently accepted.
Limits are 10,000 source files, 256 MiB per file and 10,000 events per ingestion
batch. Large valid sources are delivered in batches. Browsing and collection do
not call a model. Native turns automatically receive browsable source-based task pages, without
model calls or inferred acceptance. Use **Task grouping** to define larger tasks
and group native turns; explicit task boundaries remain separate from source
turns. Inline PNG/JPEG/WebP bytes up to 1 MiB can become previews. Transcript
paths and remote image URLs are never opened to create a preview.

`GET /api/health` checks PostgreSQL, ClickHouse and the configured S3 bucket.
An absent S3 endpoint reports unhealthy `raw_storage`; health identifies its kind
as `local_s3`. There is no automatic storage fallback.

## Read-only legacy import

Stop changing the source during your migration window when practical. Preserve the
source database, WAL files, native transcripts and old queue logs. The exporter
uses SQLite read-only/query-only access and a consistent read transaction. It does
not upgrade or write the old database.

```sh
"$OBS_NODE" --env-file=apps/web/.env.local --experimental-strip-types \
  apps/web/scripts/import-legacy.ts /absolute/path/workspace.sqlite
```

Every exported row and table schema is archived, including unknown extension
rows. The exact JSONL export is retained in S3. Supported projects, tasks, turns,
assignments, native events, analyses/subtasks, evidence notes, live state, rules,
notes, hook receipts/logs and impact records are mapped into the new stores.
Native event IDs remain unchanged. Repeated imports are idempotent. Conflicting
native usage or ownership is retained for reconciliation and prevents a successful
migration receipt. Unsupported legacy settings and interpretations remain in the
archive rather than being silently assigned new semantics.

Active old jobs are imported as `legacy_running` / `legacy_queued`, never replayed.
The old running worker remains the owner; this importer does not launch, terminate
or resume it. Re-importing a later consistent source snapshot reconciles a retained
legacy attempt to its explicitly recorded terminal status; it does not replay it. Do not start a replacement model worker until those attempts have
been reconciled. Retained images require actual retained raster bytes; filesystem
paths and historical screenshot claims are not fabricated into images.

The **16 November Codespace migration is complete**: 1,253 explicit tasks, 1,605
native turns, 1,258 saved analyses, 1,930 subtasks and 14,664 reconciled native
events (7,575 model records and 7,089 tool records). All 69,963 rows from the 54
source tables are preserved, including legacy records without a dedicated new UI.
The exact legacy export and all 1,479 locally referenced transcripts are retained
in S3; the transcript files total 437,625,382 bytes. Event IDs and native counters
reconcile exactly, with no ingest conflicts or pending deliveries. The original
SQLite database is unchanged. Private source inventories, per-file SHA-256
receipts, audit and observational HTTP benchmark results are in
`work/security/data-migration-20261116/`. Use `?range=all` to inspect the full
historical cohort. No historical model attempt was replayed.

For a database imported before the process-result repair, preview and apply the
retained outcome/state links and empty-setting pricing seed with:

```sh
"$OBS_NODE" --env-file=apps/web/.env.local --experimental-strip-types apps/web/scripts/repair-legacy-process.ts
"$OBS_NODE" --env-file=apps/web/.env.local --experimental-strip-types apps/web/scripts/repair-legacy-process.ts --apply
```

This is idempotent, audit logged and performs no model inference. It preserves
original outcome reasons/citations and genuine uncertainty; it never replaces
missing evidence with success. New imports perform this repair automatically.

During the user-requested disk cleanup, ten inactive pre-deployment backups in
`work/security/maintenance` were compressed to `.sqlite.gz` with verified original
SHA-256 hashes. Their restore command and receipts are in
`work/security/disk-cleanup-20261116/README.md`. Current databases and native logs
remain in place. Inactive experiment dependency/model caches now use checked
temporary-disk copies behind their original paths; frozen study outputs remain
persistent.

The current built UI can be restarted manually with
`python3 work/security/data-migration-20261116/activate-web.py`; this operates only
on the owned Observatory server. When rebuilding the current external dependency
cache, append `--webpack` to the build command above. See the
[improvement study](docs/research/observability-improvement-study.md) for the
read-only HTTP benchmark and the separately gated agent evaluation/analyst loop.

## Explicit analysis and steering

The UI queues versioned, source-bound analysis. Execution is a separate explicit
process using **only `gpt-6-luna` through the source Codex subscription**:

```sh
OBS_ALLOW_ANALYSIS=1 "$OBS_NODE" --env-file=apps/web/.env.local \
  --experimental-strip-types apps/web/scripts/worker.ts --analyze
```

The model cannot be changed to another model. API-key billing is disabled: jobs
require `auth_mode=chatgpt` in the source Codex home's local `auth.json`. The
collector stores only the canonical home path and account hash, never tokens.
For an ordinary Codex `sessions` folder its home is inferred; for copied history,
Claude transcripts or another folder, set **Local Codex subscription home** when
adding the source folder. A missing login permits retention but blocks analysis.
Mixed or changed account bindings are rejected. The worker uses the bound home,
forces the OpenAI/ChatGPT provider, ignores user provider configuration and removes
inherited API keys and endpoint overrides. It neither falls back to API billing
nor silently switches accounts. Historical file ownership cannot be proven from
a copied transcript; choose its original local subscription explicitly.

Only one invocation is claimed at a time. Existing legacy/uncertain/running attempts
block replacements. No automatic model retry occurs. Failures after invocation
remain uncertain; inspect the retained snapshot, events and stderr before any
manual reconciliation. Analysis usage is stored separately from observed work. Snapshots, schema, original
CLI event/stderr bytes and the answer are retained in S3. Output also streams to
a private local spool so a storage outage cannot silently discard an invocation;
uncertain attempts remain blocked from automatic replay.
No paid invocation is needed for the test suite.

Native agents can post canonical hook events to `/api/hooks`, authenticating with
`Authorization: Bearer $OBS_INGEST_TOKEN`. Events use stable `session_id` and
`event_id` identities and the schema in `src/lib/steering.ts`. Modes are log, warn,
ask and block. Notes deliver once, pause blocks the next pre-tool hook, and replay
returns the saved response. The caller must enforce ask/block decisions; collecting
JSONL alone cannot control an agent. No user's CLI hook configuration is rewritten.

## Tests and validation

```sh
"$OBS_NODE" node_modules/typescript/bin/tsc --noEmit -p apps/web
"$OBS_NODE" --experimental-strip-types --test apps/web/src/lib/*.test.ts
"$OBS_NODE" --experimental-strip-types apps/web/scripts/prepare-test-db.ts
"$OBS_NODE" --env-file=apps/web/.env.test.local --experimental-strip-types apps/web/scripts/migrate.ts
```

The integration suite requires isolated `observatory_test` PostgreSQL and ClickHouse
databases and an explicitly labeled **S3 protocol fixture**, never real user data:

```sh
"$OBS_NODE" --env-file=apps/web/.env.test.local --experimental-strip-types apps/web/tests/s3-fixture.ts
# another terminal
"$OBS_NODE" --env-file=apps/web/.env.test.local --experimental-strip-types \
  --test --test-concurrency=1 apps/web/tests/*.test.ts
"$OBS_NODE" --experimental-strip-types apps/web/scripts/serve-test.ts
python3 apps/web/tests/browser_validation.py
```

The original browser suite uses Playwright and Chromium; review them before a new
installation. The currently reviewed isolated Firefox/WebDriver runtime can instead
run `python3 apps/web/tests/browser_webdriver.py` using only Python’s standard
library. It expects an existing driver on loopback port 14444 and the isolated
fixture app on 3433; `OBS_WEBDRIVER_URL`, `OBS_TEST_URL` and `OBS_BROWSER_OUTPUT`
configure these. It verifies synthetic fixtures before exercising mutations.
It downloads or installs nothing. Keep the test S3 fixture running for its health
and retention checks. The 17 November private runtime/advisory receipts are under
`work/security/application-validation-20261117/`. It checks production routes, shared tables, persisted mutations,
source/image dialogs and phase filters in the requested desktop dark theme. The validation
report distinguishes protocol-fixture checks from actual S3-server validation.

An optional larger **synthetic read-model fixture** checks list responsiveness with
1,000 turns and 12,000 events. Run it only against the isolated test stores above:

```sh
"$OBS_NODE" --env-file=apps/web/.env.test.local --experimental-strip-types apps/web/scripts/seed-load-test.ts
python3 apps/web/tests/load_browser.py
```

This measures generated dashboard data, not collector throughput, actual usage,
model quality, billing, or a before/after performance improvement.

## Tasks, subtasks and prompt meaning

Open a task to see its subtask list. Open a subtask to inspect only its retained
steps, tool totals, native checks, timeline and screenshots. The server intersects
all step filters with the subtask membership; changing an ID filter cannot include
a sibling's steps. Stale source interpretations must be refreshed first.

Luna supplies each subtask's activity type, lifecycle state, outcome, reason,
failure explanation, confidence and evidence references. It also classifies each
analyzed prompt as a separate task, continuation, course correction, interruption
or unknown, using nearby retained prompts in the same session. Missing evidence
stays unknown. Prompt links are interpretations for review; current grouping
assignments and explicit user acceptance are preserved. No keyword rule or tool
exit status is treated as a model's task-level success decision.
