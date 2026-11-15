# Set up Observatory

The current web application lives in `apps/web` on branch `work`. It uses Next.js
App Router, React, TypeScript, shadcn/ui, PostgreSQL, ClickHouse and Garage S3.
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
commit `.env.local`, Garage configuration, logs, source transcripts or credentials.

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

## Garage raw-log storage

Set `S3_ENDPOINT`, `S3_REGION=garage`, `S3_BUCKET`, `S3_ACCESS_KEY_ID` and
`S3_SECRET_ACCESS_KEY` in `.env.local` for an approved Garage deployment. The S3
client uses path-style requests and the maintained AWS SDK. The bucket must exist;
it is not created implicitly by application requests.

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
not call a model. Use **Task grouping** to define projects/tasks and assign native
turns; explicit task boundaries remain separate from source turns.

`GET /api/health` checks PostgreSQL, ClickHouse and the configured S3 bucket.
An absent Garage endpoint reports unhealthy raw storage; it is not silently
replaced by local files or another object store.

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
or resume it. Do not start a replacement model worker until those attempts have
been reconciled. Retained images require actual retained raster bytes; filesystem
paths and historical screenshot claims are not fabricated into images.

## Explicit analysis and steering

The UI queues versioned, source-bound analysis. Execution is a separate explicit
process using an already authenticated Codex CLI:

```sh
OBS_ALLOW_ANALYSIS=1 "$OBS_NODE" --env-file=apps/web/.env.local \
  --experimental-strip-types apps/web/scripts/worker.ts --analyze
```

Only one invocation is claimed at a time. Existing legacy/uncertain/running attempts
block replacements. No automatic model retry occurs. Failures after invocation
remain uncertain; inspect the retained snapshot, events and stderr before any
manual reconciliation. Analysis usage is stored separately from observed work.
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

The browser suite uses existing Playwright and Chromium; review them before a new
installation. It checks production routes, shared tables, persisted mutations,
source/image dialogs, phase filters, themes and phone layouts. The validation
report distinguishes protocol-fixture checks from actual Garage validation.
