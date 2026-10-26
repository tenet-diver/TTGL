# Isolated desktop execution

The desktop continuation uses the existing six-condition Codex orchestrator
and official SWE-bench evaluator. The new code supplies the missing worker
boundary; it does not implement replacement grading or a new agent framework.

`tools/worker-mcp` uses the official TypeScript MCP SDK, pinned by its npm lock
(SDK 1.32.2, MIT), with one repository shell tool. Codex remains on the host
with its ordinary ChatGPT login. User configuration, project instructions,
plugins, native shell and other host tools are disabled for these trial clients.
Experts and pre-call routers receive no worker tool. Their selected context
continues to come from the existing orchestrator.

Each solving assignment receives a new offline Docker container with no host
mounts, no Docker socket, all capabilities dropped, no privilege escalation,
two CPU cores, 4 GiB memory and 256 processes. Its source and Git history are
replaced with a shallow checkout at the frozen base commit. Before staging,
the runtime checks that the image's tracked source matches that base; ignored
compiled dependencies remain so editable scientific packages keep working.
No evaluator dataset, gold patch or hidden test is mounted into the worker.
The trusted MCP process can execute only in the one assigned container.

The worker tool is explicitly approved for the duration of this client under
the user's experiment authorization. This applies only to the disposable
container shell, not arbitrary host execution. The supported per-tool setting
is documented in the [official Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
The client also sets a minimal, read-restricted native permission profile; see
[official permission profiles](https://learn.chatgpt.com/docs/permissions).
These profiles are beta. The independently verified Docker boundary is the
primary solver filesystem/network boundary.

The official pinned harness runs in a different tooling container with the
private dataset and Docker socket. That container needs the Docker CLI as well
as the Python SDK: upstream cleanup invokes the CLI. The initial missing-CLI
attempt and its actual reports are preserved in `controls-001`; the corrected
tooling image is used for `controls-002`. This setup repair changes no tests,
predictions, or harness grading logic.

## Execution order

1. Reconstruct and hash-check the original frozen 12-task panel using
   `scripts/prepare_swe_bench.py`. Keep its private dataset outside the TTGL
   checkout and all solver environments.
2. Build `scripts/Dockerfile.swe-evaluator` using the verified harness archive
   and pinned evaluator requirements as its context. Preserve the image ID.
3. Install worker tooling with `npm ci --prefix tools/worker-mcp`.
4. Run `scripts/run_swe_controls.py --private-root PRIVATE --output NEW_CONTROLS`.
   Retain every base/reference result, including failures. No model inference
   is performed by this command.
5. Validate public tests in the staged worker environments before scored runs.
   Use `scripts/validate_swe_workers.py --controls CONTROLS --output NEW_VALIDATION
   --workspace-root NEW_PROBE_WORKERS`. This uses fixed public smoke modules,
   records failures, and makes no model calls.
6. Freeze a new study with `scripts/run_isolated_swe.py init --controls CONTROLS
   --worker-validation NEW_VALIDATION/summary.json --study-dir NEW_STUDY
   --private-root PRIVATE --workspace-root NEW_WORKERS`, then use its `preflight`
   and `run` commands. Defaults retain Luna, Sol, medium reasoning, all six
   conditions and the original 900-second assignment budget.
7. Grade each exported condition with the same official harness, preserving
   original reports and exact patch joins. Analyze using
   `scripts/run_swe_bench.py analyze` and collect finalized thread estimates
   using `scripts/collect_codex_usage.py`.

The isolated `run` command grades each completed assignment immediately after
closing its worker, while the pinned task image is still cached. This avoids
another panel of image downloads. The evaluator receives a private dataset copy
that changes only the image reference to the exact validated image ID; its test
and reference fields are unchanged. Original and copied dataset hashes are
recorded. Native evaluator reports are copied into the study and joined through
the existing strict patch-hash importer. Explicit infrastructure failures stop
the run and remain ungraded. The `grade` command can grade retained predictions
without new model inference; use it to reconcile a grading interruption before
resuming generation.

Byte-identical submissions for the same task may share an original official
report. The cache key includes the task, exact patch SHA-256, evaluator image,
private dataset hash and grading timeout. Reuse verifies the original report
and patch hash and writes a separate receipt; it does not fabricate or copy a
new official report. Changed patches always receive a fresh run ID. Report the
number of actual evaluator executions separately from model assignments.

The study separately freezes adapter, MCP server, dependency lock and driver
hashes, worker image IDs/digests and control eligibility. It records environment
exclusions before model outcomes, with no task substitution. Completed
assignments are not repeated. An uncertain live worker requires explicit
reconciliation rather than an automatic retry.

This fresh desktop study executes tasks in their frozen hash-sampled order and
randomizes the six conditions within each task using seed 1729. This declared
task-blocked ordering lets all conditions reuse the same immutable image while
keeping independent containers; the incoming immutable image is pulled before the preceding image is removed,
so shared layers can be reused while the disk reserve is enforced. This avoids retaining the full panel's images on the host.
It is an execution amendment to the unrun globally shuffled host-checkout
design, not a retrospective reordering of scored attempts.

`TTGL_CONTAINER_TESTS=1 python -m pytest tests/test_isolated.py` exercises real
container edits through the MCP SDK, checks mount/network boundaries, verifies
that the host source stays unchanged, checks that the exported patch applies,
and rejects a changed worker HEAD. It requires the small local
`ttgl-worker-fixture:20261026` Git/Python image. Live mechanism checks are recorded
separately from scored benchmark outcomes.

Build that fixture with `docker build -t ttgl-worker-fixture:20261026
tests/fixtures -f tests/fixtures/Dockerfile.worker`.

Token counters are measured, and unknown subscription credits/dollars stay
null. Clone/container preparation time is recorded separately from the model
execution manifest. Evaluator/setup overhead and hardware allocation are not
silently counted as zero. This 12-task engineering panel cannot establish a
three-point quality margin or reliable full deployment savings.

## Repairs and amendments before scored inference

The first live conversation check exposed an overly strict protocol check:
a complete expert question with empty additional context was rejected. Empty
selected context is legitimate for a self-contained question. The repaired
orchestrator still requires a nonempty question and enforces the total context
limit. A fresh three-turn Luna/Sol/Luna check passed, and its ledger exactly
matched the owned native rollout token totals. The failed check is retained.
Frozen historical trials are not rewritten or resumed under the new source.

The Requests image lacks the `mocker` fixture needed by its public utility
tests. Its base repository explicitly pins `pytest-mock==2.0.0` in
`requirements-dev.txt`. The runtime installs that SHA-256-verified wheel,
offline and without dependency resolution, in each Requests solver container.
All six conditions receive it. The official evaluator image is unchanged.
The original 192-pass/8-error public check and the repaired 200-pass check
(11 skips each) are retained. `tools/worker-dependencies.json` freezes the
download and enters the study source checks.

The SymPy no-fix control completed near the original 600-second evaluation
limit on this host while retaining all 67 preservation checks. Before any
scored model outcome, the fresh study's grader limit is set to 1200 seconds
for every condition to reduce host-speed artifacts. The solver's original
900-second budget is unchanged. Control records keep their actual 600-second
limit; passing within that limit also validates the longer grading allowance.

Official image preparation also changes regular-file execute bits. The worker
compares complete Git blob identities, including binary files, before staging.
It permits only those mode changes and audited build/runner metadata changes identified by both exact Git blob
hashes. Astropy pins setuptools in `pyproject.toml`; Sphinx constrains build
dependencies in `setup.py` and adds only pytest verbosity in `tox.ini`. Staging restores the original base blob, records
the setup exception, and requires the final exact-base checkout to be clean.
Other content changes, added/deleted paths and symlinks are rejected. Ignored
compiled dependencies survive this normalization. Public worker tests check
that those dependencies still import after source restoration.

The control runner supports an explicit `--resume` after a host free-space
stop between tasks. It verifies the original protocol, dataset, prediction
bytes and every completed native report before skipping completed pairs.
A resume receipt records the revised driver hash without rewriting the
original protocol. Partial control attempts require reconciliation and are
never automatically replayed. Source control records retain the actual process
return codes, including the Django-17084 successful gold report followed by
an image-enumeration cleanup race. That native report has
`infra_failure=false`; its nonzero wrapper exit is not hidden.

Controls and worker image cleanup are now run sequentially: concurrent image
removal can race the upstream Docker SDK's image inventory. The 10-GiB worker
reserve stays enforced. An already cached image no longer needs its own size
added to the pre-download reserve; uncached images still do. Disk stops and
failed preparations make no model calls and remain in their original folders.

Before scored inference, image handoff was amended to pull the next immutable
image before removing the completed task image. At most the predecessor and
incoming image overlap during the pull, with the same free-space reserve.
This retains shared Docker layers without retaining the full panel. The
solver source, dependency image identity, prompts and grading are unchanged.

Before scored inference, `experiments/codex-isolated-20261026/pricing-scenario.json`
freezes the official Enterprise Codex Standard token-rate card for the exact
requested model IDs. It enters the execution source freeze and is copied into
the study. Final analysis reports its counterfactual token-rate cost separately
from API-equivalent dollars, observed subscription credits and actual cash.
The published signed-in Codex context policy applies to that scenario; API
cache-write/context billing is not silently substituted. Router and expert
usage are included. Missing counters or unpriced models produce unavailable
cost, and per-model counters must reconcile to the task total. Seven pricing
behavior tests passed before inference. No scenario proves full deployment
savings or small-panel quality noninferiority.

The final Sphinx dependency/runner audit is recorded with exact hashes and
diffs in `results/codex-isolated-20261026/image-setup-audits`. Restoring those
files to the original base revision passes its public utility smoke module.
The original rejected preparation is retained in worker-validation-006 and
the successful final check in worker-validation-007. No benchmark model
outcome preceded this setup normalization.
