# Codex metering: current managed-runtime diagnosis

Checked on 26 October 2026. This note concerns the current managed workspace,
not a general limitation of Codex or ChatGPT subscriptions.

## Authentication and local records

The installed binary reports `codex-cli 0.163.0`. A normal
`codex login status` command returned exit code 0 and **ChatGPT authentication**.
Its output was captured and classified; raw output and credential values were
not printed or saved. The credential file was not opened manually. This is
evidence that the CLI recognizes the existing login, not proof that every model
is available or a particular request will be authorized.

The inherited `CODEX_HOME` points to
`/run/codex-environment/codex-home`. Directory-name inspection found only `tmp/`
and `auth.json`. Neither `sessions/` nor `archived_sessions/` exists there.
`/workspace/.codex` is empty, and `/home/agent/.codex` contains no JSONL files.
These checks do not find local rollout usage records for the earlier platform
collaboration trials. They do not establish that the platform has no server-side
usage telemetry, or that a normal desktop Codex installation lacks usage logs.

## Why the nested CLI currently fails

The earlier native probe failed before producing model events:

```text
failed to initialize in-process app-server client: Read-only file system (os error 30)
```

The inspected official source provides a concrete matching failure path:

1. `codex-rs/exec/src/lib.rs` starts the in-process app-server client and adds the
   quoted error context if initialization fails.
2. `codex-rs/app-server/src/in_process.rs`, line 451 at the inspected revision,
   calls `resolve_installation_id(&args.config.codex_home)` during startup.
3. `codex-rs/core/src/installation_id.rs` opens
   `CODEX_HOME/installation_id` with read, **write**, and **create** enabled. It
   then locks and, when needed, writes a UUID to that file.

The current home has no `installation_id` entry and is read-only. This provides
a plausible explanation for the failure even with `--ephemeral`, which concerns
session persistence and does not bypass this startup operation. Exact binary-to-
source identity and a syscall trace were not established, so the source finding
is identified as a diagnosis rather than an observed failing `open` syscall.

The official configuration schema supports `sqlite_home` and `log_dir` overrides.
They relocate SQLite state/log databases and logs, respectively. They do not
relocate the installation-ID operation above. Changing only those paths is
therefore not a supported complete fix for the identified startup requirement.
No override of `HOME` or `CODEX_HOME`, authentication-file copying, sandbox
weakening, proxy bypass, or modification of the read-only mount was attempted.
No model inference was launched by this investigation.

## Consequence for the experiment

The accurate distinction is:

- Subscription-authenticated Codex can expose usage through its supported
  execution interfaces; separate official-source research documents those events.
- This particular managed runtime recognizes ChatGPT login but currently blocks
  nested CLI initialization and does not expose the prior collaboration trials
  as ordinary local session JSONL files.
- The practical next run can use an ordinary writable Codex installation with
  the user's supported ChatGPT login, or a platform-provided fix/export for this
  runtime. The experiment should consume the official token counters and keep
  subscription allocation, API-price-equivalent estimates and actual bills as
  separate economic quantities.

The historical pilot's unknown token and cost fields should remain unknown
unless a trustworthy export tied to those exact session IDs becomes available.
Improved metering on new runs must not be used to invent the missing old values.

## Pinned source evidence

Inspected official revision:
`970111f6cb62cc02fe36a82ea7d71b37a2889c97`.

| Source | SHA-256 of retrieved bytes |
|---|---|
| [Configuration schema](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/codex-rs/core/config.schema.json) | `d98f7bbe84dfe375d05ad5a8249a5368d82989551e38c6a4babe35356b92c14e` |
| [In-process app-server](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/codex-rs/app-server/src/in_process.rs) | `27ef944619c42c3d5e645274e77ab1866c0ffd192b6a51a97e022d319766c733` |
| [Installation ID](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/codex-rs/core/src/installation_id.rs) | `c279cdce8837195f66c362aa87c8a068c75ac022305e72bb129e98581b6930b5` |
| [Exec initialization](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/codex-rs/exec/src/lib.rs) | `4229c67ec7a4d9aa21f26c500f1206660f7ccb3a6c047843a3fa7295938a0848` |
