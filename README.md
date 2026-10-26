# We have to combine — A conversation is all you need

**Using small language models as conversational routers for agentic software engineering.**

The hypothesis is lower **total cost** with minimal performance degradation through continuing small-model ↔ expert conversations: questions, clarification, challenge, revision and tested integration. Personal memory and learning are optional extensions. Closely related architectures already exist; this is a replication and controlled extension, not a first-architecture claim.

Read the **[paper](docs/paper/README.md)**: [PDF](docs/paper/paper.pdf), [Word](docs/paper/paper.docx), [HTML](docs/paper/paper.html). It contains the literature review, explicit prior-art comparison, experiment design, live pilot results and limitations. [ADR 0006](docs/adr/0006-personal-agent-replication.md) records the current scope.

The live Codex feasibility pilot completed 16 paired task assignments. Functional regression success was Luna **3/4**, Sol **4/4**, prompt routing **4/4**, and the optional-conversation controller **3/4**. All optional controllers chose zero expert calls. A separately required two-round clarification exchange passed its 30 regression tests. Strict original-test-file rules rejected several otherwise functional patches; both outcomes are [recorded](results/codex-pilot-001/analysis/summary.json). These tiny historical-task results do **not** establish cost savings or noninferiority; token and dollar usage were unavailable.

- [Codex conversation harness](docs/research/personal-harness.md): persistent controller and expert threads, clarification/challenge responses, bounded turns, failure records and unknown-cost handling.
- [Frozen pilot and restore instructions](experiments/codex-pilot-001/README.md), [full results](results/codex-pilot-001/analysis/), [live dialogue transcript](results/codex-pilot-001/dialogue-transcript.md).
- [Closest prior work](docs/thesis/personal-agent-prior-art.md), [source register](docs/thesis/personal-agent-prior-art-sources.json), [communication protocols](docs/thesis/agent-communication.md).
- [Earlier broad thesis](docs/thesis/README.md): supporting open-model, distillation, browser and economics reviews. Its older proposed study hierarchy is superseded by the current paper.

Reproduce the recorded analysis without calling a model:

```bash
python scripts/analyze_codex_pilot.py --output-dir results/my-pilot-analysis
python -m pytest -q
```

The research dependencies are pinned below. Core validation: **86 passed, 1 skipped, 2 subtests passed**. The standalone Codex CLI adapter is tested with subprocess fixtures; live trials used the collaboration interface because nested CLI initialization encounters a read-only state directory here. Runpod remains unprovisioned and its authorized US$100 budget unspent. Fastest Jira/Confluence access is still unavailable; [local task state](docs/research/task-state.json) and an [import CSV](docs/research/jira-import.csv) preserve progress.

## Earlier coding-problem replay

The first experiment is complete: published LiveCodeBench outcomes for **713 paired tasks** support a chronological routing replay. At a 50% remote-call budget the learned router achieved **29.93% pass@1**, versus **28.35%** for expected random routing. The difference, **+1.58 percentage points (95% CI −1.58 to +4.44)**, is inconclusive. Remote-only achieved **39.37%**. These are replay results, not fresh model inference or trained-student improvements.

## Study documents

- [Literature review and evidence limits](docs/research/literature-review.md), [20-reference bibliography](docs/research/references.bib).
- [Frozen protocol](docs/research/protocol.md), [pre-outcome amendment](docs/research/protocol-amendments.md), [hash record](docs/research/protocol-freeze.json).
- [Results and interpretation](docs/research/results.md), [independent audit](docs/research/independent-audit.md).
- [Machine-readable results and plots](results/routing-pilot-001/), [fresh-download reproduction check](results/reproduction-verification.json).
- [GPU training and held-out inference](docs/research/gpu-training.md), [Runpod plan](docs/research/runpod.md).
- [Task state](docs/research/task-state.json). Local work item IDs are not Jira issue keys; Atlassian connection is pending.

## Reproduce the routing experiment

Python 3.12 is the tested runtime. From the checkout root:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-research.lock
.venv/bin/pip install --no-deps -e .
.venv/bin/python -m ttgl.fetch
.venv/bin/python -m ttgl.data
MPLCONFIGDIR=/tmp/ttgl-matplotlib XDG_CACHE_HOME=/tmp/ttgl-cache \
  .venv/bin/python -m ttgl.routing --output-dir results/my-reproduction
.venv/bin/python -m pytest -q
```

Downloads are pinned by upstream commit and mandatory SHA-256. Dataset preparation preserves complete contests, checks metadata/sample alignment and records every split. Analysis refuses changed protocol, amendment or split hashes and refuses to overwrite existing result directories. Source artifacts and generated datasets are ignored by Git; the downloader reconstructs them. Preserve the upstream license retrieved with the data.

Expected split sizes: 429 train, 142 calibration, 142 test. The two models have ten published samples per task. Model difficulty labels and grading feedback never enter routing features. Full cost results are explicitly hypothetical normalized scenarios; no dollar savings or inference latency are measured in this replay.

In the managed cloud workspace, `bash scripts/setup_research.sh` installs the tested research environment under `/workspace/.tools/ttgl-research`. Use the existing checkout; each cloud task is already isolated.

## Prepare and run the GPU arm

```bash
.venv/bin/python -m ttgl.train --dataset data/processed/train.jsonl \
  --output-dir artifacts/my-sft-preflight --dry-run
.venv/bin/python -m ttgl.generate --dataset data/processed/test.jsonl \
  --output-dir artifacts/my-generation-preflight --dry-run
```

Preparation selects one nonempty, upstream-verified teacher solution per eligible training task; the current run produces 334 examples. Source titles and starter interfaces are hash-verified and shared between training and generation. Test data are never used for fine-tuning. Dry runs explicitly record `prepared_not_trained` / `prepared_not_generated`.

Follow the [GPU instructions](docs/research/gpu-training.md) for the exact Transformers/TRL/PEFT stack, LoRA training, immutable model revision, baseline/adapter generation and the official LiveCodeBench evaluator. Official test fixtures must be acquired separately. Sample code is never executed by the generation module.

The approved Runpod ceiling is **US$100 total**, one 80 GB GPU. Authentication and runtime access remain required; no pod has been provisioned. Training, fresh held-out coding evaluation, logit distillation and RLAIF have **no model-quality results yet**.

An optional integration test uses a tiny randomly initialized Qwen-architecture fixture to verify completion-only loss, real LoRA updates and adapter reload. It needs the training dependencies and can be run with `python -m pytest tests/test_sft_integration.py -q`; the core research environment skips it. This fixture is software validation, not pretrained-Qwen evaluation.
