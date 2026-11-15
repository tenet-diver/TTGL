# Set up and start TTGL

Use branch **`work`**. The Usage Observatory and the research environment are
separate: starting the app does not require the full numerical/training stack.
All commands below run from the repository root.

## Prerequisites and private state

- Python **3.11+** for the Observatory; research metadata requires **3.12+**.
- Docker Engine with Compose for Langfuse; no Docker is needed for the workspace alone.
- An existing authenticated Codex CLI for native history and explicit analyst/model work.
- Authorized access to the private design-system distribution for the complete UI.

Recorded tested versions and service digests are in
[deployment.lock.json](tools/usage-monitor/config/deployment.lock.json). They are
historical tested versions, not instructions to install a floating latest release.
The Observatory itself uses no third-party Python or npm runtime packages.

Before any download/install/upgrade/first execution, follow the
[dependency security policy](docs/security/dependency-security-policy.md).
The documented Codespace exception allows incomplete checks here; confirmed
vulnerabilities still block affected artifacts. It is not a security clearance
or a waiver for another machine. None of the setup helpers performs that review
on your behalf. Do not use the older Mac companion's automatic `npx` installation
as a shortcut for this deployment.

| Private location | Contents |
| --- | --- |
| `work/security/workspace/` | Workspace SQLite database and review state |
| `work/security/langfuse-stack/` | Prepared Compose file, credentials, logs, captures and delivery receipts |
| `~/.codex/` | Source native histories and authentication; not copied into Git |
| Docker named volumes | Existing PostgreSQL, ClickHouse, Redis and object-storage data |

Preserve existing credentials, volumes and ingestion ledgers. Daily/session
rollups and transport spans must not be added to native generation usage.

## UI assets

The public repository includes its shared UI adaptation, but startup also uses
three privately licensed DOM assets. From an authorized local source checkout:

```sh
python3 tools/usage-monitor/observability/sync_design_system.py --source /path/to/design-system
python3 tools/usage-monitor/observability/sync_design_system.py --check
```

The sync reads the exact locked Git revision, checks artifact hashes and runs no
producer build scripts. It writes only ignored private assets. A public clone
without access to that source cannot reproduce the complete UI. See
[the UI runbook](tools/usage-monitor/README.md#compact-workspace-and-data-coverage).

## Workspace without Docker

This serves tasks, retained native activity, local evidence and saved analyses:

```sh
python3 tools/usage-monitor/observability/workspace.py \
  --data work/security/workspace \
  --codex-root "$HOME/.codex" \
  --capture-root work/security/langfuse-stack/captures
```

Open **http://127.0.0.1:8766**. The command runs in the foreground; Ctrl-C stops
that process. Use your terminal/process supervisor for a persistent local launch.
It binds to loopback. In Codespaces, forward port **8766** using the Ports panel.
Local history collection does not invoke a model. Explicit analysis actions can
invoke a configured model and are accounted for separately.

Check from another terminal:

```sh
curl --fail http://127.0.0.1:8766/ --output /dev/null
```

Langfuse links/reconciliation and new HTTP capture are unavailable until their
separate services are running. The workspace can still inspect retained native
evidence and previously saved private captures.

## Full observability stack

After reviewing the exact pinned graph and syncing UI assets:

```sh
# Prepare local config and credentials; preserves existing secrets.
python3 tools/usage-monitor/observability/setup_local.py prepare

# Download only reviewed locked images, if absent. This is an explicit install step.
python3 tools/usage-monitor/observability/setup_local.py pull

# Inspect versions, pinned artifacts and image availability; installs nothing.
python3 tools/usage-monitor/observability/setup_local.py doctor

# Start Langfuse plus the supervised workspace, capture adapter and exporter.
python3 tools/usage-monitor/observability/setup_local.py start
```

Do not run the standalone workspace and full supervisor on the same port at the
same time. Stop the process you own before switching modes. `doctor` checks exact
tested Codex-version equality: a newer installed CLI is reported as a mismatch;
that does not mean the standalone workspace is incompatible. Do not silently
downgrade it or revise a lock without validation.

In a second terminal:

```sh
python3 tools/usage-monitor/observability/setup_local.py dashboard
python3 tools/usage-monitor/observability/setup_local.py status
curl --fail http://127.0.0.1:3000/api/public/health
```

| Port | Service | Access |
| --- | --- | --- |
| 8766 | TTGL workspace | Browser / forwarded Codespaces port |
| 3000 | Langfuse | Browser; private login instructions in `work/security/langfuse-stack/LOGIN.md` |
| 8317 | Local capture adapter | Loopback only; keep unforwarded |
| 9090 / 9091 | Object-storage API / console | Local stack infrastructure |

The supervisor uses `pull_policy: never`; starting does not upgrade or download
images. Ctrl-C stops its local child processes and preserves Docker services/data.
Never use `docker compose down -v` as a repair step.

### Restored Codespaces with missing Docker layers

At the 15 November inspection, saved container records and named volumes existed,
but the local image inventory was empty. Starting a container returned
`RWLayer ... is unexpectedly nil`. The workspace alone starts successfully;
the full stack does not. Only about 550 MB was free before cleanup.

This is a Docker restore problem, not evidence of an application or study failure.
Inspect `docker image ls`, `docker ps -a`, `docker volume ls` and `df -h` before
recovery. Keep database volumes, raw evidence and container metadata; do not prune
them to recover space. Restoring the exact images requires enough disk capacity,
the applicable dependency review and a data-preserving recovery plan.

## Optional analyst tools and capture routing

```sh
python3 tools/usage-monitor/observability/setup_local.py configure-cli
ttgl tools
ttgl query_activity --args '{"section":"experiments"}'
```

`configure-cli` writes an owned launcher under `~/.local/bin`; ensure that
directory is on PATH. It installs no package. Register the analyst MCP for local
Codex sessions only when wanted:

```sh
python3 tools/usage-monitor/observability/setup_local.py configure-codex
```

The current installer keeps the built-in OpenAI provider as the normal route.
Capture/compression is an explicit experimental profile or `codex_traced.py`
operation. Earlier default-compression installation claims describe a historical
configuration. Inspect actual local configuration and the
[runbook](tools/usage-monitor/README.md) before routing new traffic. Starting the
workspace does not alter provider configuration or resume research schedules.

## Verification and research reproduction

Software checks use existing tools and make no scored study invocation:

```sh
python3 -m unittest discover -s tools/usage-monitor/observability -p 'test_*.py'
python3 -m unittest discover -s tools/usage-monitor/langfuse -p 'test_*.py'
node --check tools/usage-monitor/observability/workspace.js
```

Browser checks are optional and need their already reviewed QA runtime. Do not
auto-install a browser or package runner when it is absent.

For research, first select a specific [experiment](docs/EXPERIMENTS.md) and read
its frozen protocol. The numerical environment uses
[requirements-research.lock](requirements-research.lock) and
[pyproject.toml](pyproject.toml); review the entire resolved graph before creating
or populating a virtual environment. Do not automatically install it just to run
the stdlib Observatory. With an already prepared research environment:

```sh
python -m pytest -q
python scripts/analyze_codex_pilot.py --output-dir results/my-pilot-analysis
```

Use a fresh output directory. The pilot analysis does not call a model. Dataset
fetching and routing replay instructions are in
[the original results](docs/research/results.md) and
[reproduction guide](docs/paper/discussion-and-reproduction.md). GPU training
instructions remain [prospective](docs/research/gpu-training.md); no completed
training-quality result should be inferred from a dry run.

For the native-team work, use the dedicated
[reproduction/porting guide](docs/paper/codex-team-knowledge/REPRODUCING.md).
Do not start a queued study, repeat an uncertain call, access reserved validation
or enable a schedule as part of ordinary app setup.
