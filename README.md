# TTGL research

A reproducible study of confidence-aware routing from a local coding model to a stronger remote model, followed by verified teacher-output distillation.

## Software-engineering thesis

The [pre-results master's thesis](docs/thesis/README.md) specifies the next study: dual-model versus single-model agents under a common harness, router quality and accuracy–cost tradeoffs, current open-weight and closed-model comparisons, and verified distillation. Read the [PDF](docs/thesis/thesis.pdf), [Word document](docs/thesis/thesis.docx), or [HTML](docs/thesis/thesis.html). The dated market review includes source and pricing limitations. Repository-level experiments and their results remain pending.

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
