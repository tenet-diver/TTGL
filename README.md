# We have to combine — A conversation is all you need

**Using small language models as conversational routers for agentic software engineering.**

The hypothesis is lower **total cost** with minimal performance degradation through continuing small-model ↔ expert conversations: questions, clarification, challenge, revision and tested integration. Personal memory and learning are optional extensions. Closely related architectures already exist; this is a replication and controlled extension, not a first-architecture claim.

Read the **[paper](docs/paper/README.md)**: [PDF](docs/paper/paper.pdf), [Word](docs/paper/paper.docx), [HTML](docs/paper/paper.html). It contains the literature review, explicit prior-art comparison, experiment design, live pilot results and limitations. [ADR 0006](docs/adr/0006-personal-agent-replication.md) records the current scope.

A fresh **12-task, six-condition metered SWE-bench study is complete** on the
`work` branch. All 24 official environment controls and all 12 staged public
worker checks pass. The [frozen study and current official grade index](results/codex-isolated-20261026/study-001/)
and [completed task checkpoints](results/codex-isolated-20261026/study-001/checkpoints/)
record the archived outcomes. The [final analysis](results/codex-isolated-20261026/analysis-001/)
shows Luna 9/12, Sol 10/12 and pre-task routing 11/12. Native model
tokens are measured; published token-rate scenarios, provider estimates and
actual subscription charges are kept separate. [Host cleanup](results/host-cleanup-20261026/README.md)
removed 106 rebuildable cache/dependency directories and one recoverable clean
worktree while preserving source and local results.

A separate [general delegation development study](experiments/delegation-development-001/README.md)
tests stronger independent verification, adaptive consultation, cheap-first
fallback and a compact context-only expert interface. The target is **95% lower
model cost with at least 95% of matched Sol accuracy retained**. Three registered
candidates completed 36 development assignments. Cheap-first reached 4/4 versus
matched Luna's 3/4 and Sol's 4/4, with 89.1% lower model-cost scenario than Sol.
See the [cost–performance graphs and evidence limits](results/prompt-comparison-001/README.md).
One of 12 reserved validation cases has an invalid independent control; its
explicit disposition preserves the evidence without replacement, leaving 11
cases with all independent controls and public readiness checks now passing.
The frozen 33-assignment continuation passed positive metering preflights and
is running. Resource-only
continuation preserves started/uncertain calls rather than repeating them.
A separate [Pro V2 subset](experiments/swe-pro-prompt-001/README.md) reserves only
12 development and 24 validation tasks, with no automatic 642-task run.
Its [Harbor adapter](docs/research/pro-harbor-runner.md) is implemented and passes
six transport/framework checks; first-task Pro controls are queued after the
current study. No Pro accuracy result is claimed from those checks.
The [compact-interface calibration](results/compact-expert-calibration-001/analysis.json)
measured 39.0% fewer input tokens and 36.8% lower token-rate scenario cost on one
fresh arithmetic call per interface. This is a mechanism result, not repository
accuracy or complete-task savings. Scored outcomes and held-out selection remain
separate from preflights and preparation.

The live Codex feasibility pilot completed 16 paired task assignments. Functional regression success was Luna **3/4**, Sol **4/4**, prompt routing **4/4**, and the optional-conversation controller **3/4**. All optional controllers chose zero expert calls. A separately required two-round clarification exchange passed its 30 regression tests. Strict original-test-file rules rejected several otherwise functional patches; both outcomes are [recorded](results/codex-pilot-001/analysis/summary.json). These tiny historical-task results do **not** establish cost savings or noninferiority; token and dollar usage were unavailable.

The new **[SWE-bench Verified replay](results/swe-replay-001/README.md)** analyzes all **500 tasks across ten published model runs**. The primary learned router saved **46.1% estimated inference cost**, but success fell from **72.8% to 64.2%**, failing the three-point quality tolerance. MiniMax-M2.5 alone reached **75.8% at $0.073/task**, versus a ten-model portfolio point at **76.2% and $0.115/task**. Those are historical published-run estimates, not fresh conversational-agent results or measured Codex plan savings.

- **[Run and reproduce the metered study](docs/research/HANDOVER.md)**: complete handover, prerequisites, execution commands and evidence boundaries.
- **[Use it in your own projects](docs/research/project-usage-guide.md)**: installation, bounded collaboration, token/credit accounting and cost scenarios.
- [Metered six-arm SWE-bench runner](docs/research/swe-bench-runner.md), [frozen official task sample and executed evaluator controls](experiments/swe-bench-verified-001/README.md), [independent audit](docs/research/swe-replay-audit.md).
- [Research contribution and sample-size design](docs/research/standard-benchmark-research.md), [ADR 0007](docs/adr/0007-standard-benchmark-and-metered-handover.md).
- [Subscription-backed Codex metering](docs/research/codex-metering.md): official usage counters, provider-estimated credits and ccusage; separate API billing is unnecessary for token metering.
- [Codex conversation harness](docs/research/personal-harness.md): persistent controller and expert threads, clarification/challenge responses, bounded turns, failure records and unknown-cost handling.
- [Frozen pilot and restore instructions](experiments/codex-pilot-001/README.md), [full results](results/codex-pilot-001/analysis/), [live dialogue transcript](results/codex-pilot-001/dialogue-transcript.md).
- [Closest prior work](docs/thesis/personal-agent-prior-art.md), [source register](docs/thesis/personal-agent-prior-art-sources.json), [communication protocols](docs/thesis/agent-communication.md).
- [Earlier broad thesis](docs/thesis/README.md): supporting open-model, distillation, browser and economics reviews. Its older proposed study hierarchy is superseded by the current paper.

Reproduce the recorded analysis without calling a model:

```bash
python scripts/analyze_codex_pilot.py --output-dir results/my-pilot-analysis
python -m pytest -q
```

The research dependencies are pinned below. Latest full research validation:
**172 passed, 2 optional tests skipped, 2 subtests passed**, including
real Docker integration. Native authenticated model/token preflights pass on
this desktop; the read-only failure described in older records belongs to the
previous managed host. All 108 original/development assignments passed independent
native-grade and token-counter audits. No assisted condition meets the joint
95% cost-reduction / 95% accuracy-retention target; population noninferiority is
not established. Runpod remains unprovisioned and its
authorized US$100 budget unspent. No remote Jira/Confluence publication is
claimed; [local task state](docs/research/task-state.json) and an
[import CSV](docs/research/jira-import.csv) preserve progress.

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
