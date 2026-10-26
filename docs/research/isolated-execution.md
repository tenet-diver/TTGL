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

The study separately freezes adapter, MCP server, dependency lock and driver
hashes, worker image IDs/digests and control eligibility. It records environment
exclusions before model outcomes, with no task substitution. Completed
assignments are not repeated. An uncertain live worker requires explicit
reconciliation rather than an automatic retry.

This fresh desktop study executes tasks in their frozen hash-sampled order and
randomizes the six conditions within each task using seed 1729. This declared
task-blocked ordering lets all conditions reuse the same immutable image while
keeping independent containers; the preceding image is removed before loading
the next task. This avoids retaining the full panel's images on the host.
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
