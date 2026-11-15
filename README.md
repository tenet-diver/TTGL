# TTGL — We have to combine

**An affordable, user-controlled personal agent, built through measured collaboration.**

TTGL researches small-model/expert collaboration, context and memory, and native
coding-agent teams. Its working application is the **Usage Observatory**: a local
workspace for inspecting real tasks, model usage, tool activity, evidence and
experiment decisions. The broader personal-agent frontier remains a research goal.

> Believe in me who believes in you.

| Start here | Contents |
| --- | --- |
| [Setup and startup](SETUP.md) | Run the workspace, restore the observability stack, configure tools and verify the installation |
| [Experiments and results](docs/EXPERIMENTS.md) | Completed comparisons, failed trials, mechanism checks and unfinished reservations |
| [Papers and reading](docs/PAPERS.md) | Manuscripts, reports, bibliographies and reproduction guides |
| [Observatory runbook](tools/usage-monitor/README.md) | Capture, reconciliation, analyst tools and UI behavior |
| [Research handover](docs/research/HANDOVER.md) | Historical ownership, frozen protocols and continuation constraints |

## Run TTGL

The workspace uses Python's standard library; it needs no Python/npm package
installation or model call to start. Python 3.11+ and the pinned private UI
assets are required. From an existing prepared checkout:

```sh
python3 tools/usage-monitor/observability/workspace.py \
  --data work/security/workspace \
  --codex-root "$HOME/.codex" \
  --capture-root work/security/langfuse-stack/captures
```

Open **http://127.0.0.1:8766** or forward port **8766** in Codespaces. This runs the
task/evidence workspace and native-history collection. Langfuse dashboards and
HTTP capture require the [full stack setup](SETUP.md#full-observability-stack).
Private UI assets are deliberately excluded from Git; a fresh public clone needs
an authorized source checkout before it can serve the complete UI.

For an already prepared full installation, use:

```sh
python3 tools/usage-monitor/observability/setup_local.py doctor
python3 tools/usage-monitor/observability/setup_local.py start
```

## What the experiments show

These are separate studies with different tasks, protocols and accounting.
Percentages below retain their original dated model-rate scenarios; they are
**not measured cash or subscription-quota savings**.

| Study | Recorded outcome |
| --- | --- |
| [500-task SWE-bench published-run replay](results/swe-replay-001/README.md) | 46.1% estimated inference saving, but 64.2% success versus 72.8% control: quality target fails |
| [Fresh six-condition coding study](results/codex-isolated-20261026/analysis-001/README.md) | 72 assignments; Luna 9/12, Sol 10/12, pre-task router 11/12; personal condition 9/12 with zero expert calls |
| [Held-out delegation](results/delegation-heldout-001/analysis-002/README.md) | Luna 7/11, Sol 9/11, assisted Luna 8/11; 91.45% scenario saving and 88.89% relative accuracy retention: 95/95 target fails |
| [Adaptive target90 development](results/target90-development-20261031/README.md) | Sol 6/6 versus router 4/6; 96.4048% scenario saving with quality loss; all six router cases use zero experts |
| [Progress-output representation](tools/usage-monitor/studies/progress-replay-results-002.md) | Revised trial uses 45.58% fewer native tokens on three matched log diagnoses; all six checks pass; failed predecessor retained |
| [Live coding harness](tools/usage-monitor/studies/live-harness-results-001.md) | Four runs on two generated tasks; 10.075% fewer pooled tokens, all checks pass, no observed speedup |
| [Long-history retrieval validation](docs/paper/context-memory/report.md) | Original grades: full history 24/24, files 24/24, FTS 23/24; cheaper FTS fails the no-loss gate; anonymous audit also finds quality loss |
| [Native team pilot](docs/paper/codex-team-knowledge/pilot-results.md) | All 24 saved artifacts pass; native capacity eight averages 31.3% less coding time at at least 2.45× model-rate cost on two libraries |
| [Memory-aware teams](docs/paper/codex-team-knowledge/memory-aware-results.md) | Partial 56-cell development comparison; use the linked dated snapshot, not a completed-study claim |

The goal of at least 90% lower total model-inference cost with no observed loss
against matched Sol remains **unestablished**. Development improvements, successful
mechanisms and held-out evidence are kept distinct. Training/distillation and
AI-feedback learning have no demonstrated model-quality result here.

## Repository map

| Path | Purpose |
| --- | --- |
| `tools/usage-monitor/observability/` | Local workspace, native capture, analyst MCP/CLI and evidence-backed reviews |
| `tools/usage-monitor/langfuse/` | Prepared Docker stack, export bridge and dashboards |
| `tools/usage-monitor/experiments/`, `tools/usage-monitor/studies/` | Context/memory/team runners, registrations and sanitized measurements |
| `src/ttgl/`, `scripts/`, `tests/` | Routing research, metered harnesses, analyses and software checks |
| `experiments/`, `results/` | Frozen designs, grading records, audits and published research artifacts |
| `docs/paper/`, `docs/thesis/`, `docs/research/` | Manuscripts, related work, methods and chronological reports |
| `work/security/` | Ignored private logs, captures, credentials, databases and immutable attempt evidence |

The active research branch is **`work`**. Check current processes and immutable
receipts before any continuation; never replay a started or uncertain model call.
Scheduled research monitoring remains paused. See the
[dependency security policy](docs/security/dependency-security-policy.md) before
installing or first executing downloaded software. Existing artifacts and private
histories must be preserved during cleanup.
