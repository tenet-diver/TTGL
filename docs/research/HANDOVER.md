# Handover: run the metered standard-benchmark study

Updated 26 October 2026. Repository: `tenet-diver/TTGL`, working branch `work`.
Continue from the latest pushed commit on that branch. `main` is not the active
research branch; do not merge or replace it implicitly.

Desktop continuation on 26 October: ordinary ChatGPT authentication and native
positive token metering work for both requested models. The isolated worker and
official grader are implemented, with 149 tests and both subtests passing; the
optional PyTorch integration is skipped. All 24 official base/reference controls
pass their expected outcomes on the complete original 12-task panel. See
[`controls-002`](../../results/codex-isolated-20261026/controls-002/validation.json),
[`isolation runbook`](isolated-execution.md), and
[`preparation history`](../../results/codex-isolated-20261026/preparation-history.md).

The scored run is launched in `results/codex-isolated-20261026/study-001`:
12 original tasks, all six conditions, 72 assignments. Both fresh model/token
preflight calls pass. All 12 staged public worker checks are joined in
`worker-validation-final.json`. Final software validation passes 149 tests and
both subtests, with only the optional PyTorch training integration skipped.
The source, configuration and published Codex token-rate scenario are frozen.
Do not edit generation/evaluation source during this run or implicitly repeat
an uncertain assignment. Inspect `artifacts/scored-study-001.log`, finalized
`runs/**/manifest.json` and `grades.json` for current progress. The `grade`
command can reconcile retained patches without new model inference; only
resume after explicit reconciliation of any interruption. Preserve all failed
preparations and the controls' disk stop/resume records.

Host cleanup is complete: 106 rebuildable cache/dependency directories were
removed, including 51 inactive old temporary verification dependency trees.
Their source/package manifests and logs remain. One clean worktree was removed
with its HEAD preserved under a Git recovery ref. Credentials, dirty source,
unique local artifacts, database volumes and active CI were preserved. See
`results/host-cleanup-20261026`. Observed free space is recorded separately from
allocated directory sizes, which can share filesystem blocks.
The read-only startup failure discussed below is historical to the previous
managed host. Consult current records before redoing completed setup.

## The goal and evidence boundary

Paper: **We have to combine — A conversation is all you need**.
Subtitle: **Using small language models as conversational routers for agentic
software engineering**.

Test whether an acting cheaper agent can preserve software-task quality while
reducing total cost by obtaining bounded help from a stronger agent. Both agents
can clarify, challenge, reply and revise; the controller tests and integrates.
Use existing Codex and SWE-bench tooling. Classical distillation and persistent
swarm learning are optional later work. The four personal capabilities and
memory are not mandatory treatments in the primary experiment.

The user wants completed standard-benchmark results, estimated savings, a
practical project-use guide, comparison with prior work, and a committed,
pushable implementation. The user does **not** want another proposal presented
as an executed study. Preserve the distinction between published-trace replay,
live model trials, evaluator controls and hypothetical cost scenarios.

Read, in order:

1. [AGENTS.md](../../AGENTS.md), then [the active paper](../paper/README.md).
2. [Standard-benchmark research design](standard-benchmark-research.md) and
   [project-use instructions](project-usage-guide.md).
3. [Codex metering](codex-metering.md), [harness behavior](personal-harness.md)
   and [current runtime diagnosis](codex-runtime-metering.md).
4. [Task register](task-state.json), the standard-benchmark experiment directory
   and the latest committed results. The generated Jira CSV is a pending import,
   not proof of remote Jira synchronization.

## What is already established

- The previous BugsInPy-based development pilot ran 16 assignments: four tasks
  in four conditions. It is **not** SWE-bench Verified. Functional outcomes were
  small 3/4, large 4/4, prompt-router 4/4 and optional conversation 3/4. Strict
  artifact acceptance was 3/4, 4/4, 2/4 and 0/4 respectively. All optional
  controllers chose zero expert calls. The independent required-dialogue
  mechanism check passed 30 regression tests. Costs and token usage for these
  exact historical runs remain unknown.
- The Codex adapter supports persistent controller/expert threads, bounded
  consultations, durable journals, recovery checks and per-model usage.
  Cumulative CLI counters are reconciled by thread delta; cached/reasoning
  subsets are not blindly added. Missing observations stay unknown.
- The official Codex CLI/SDK can meter subscription-backed work. Separate API
  billing is not required. `ccusage@20.0.44` was installed and exercised; the old
  platform pilot's rollout logs were absent, so no old usage was reconstructed.
- An optional app-server collector can obtain estimated plan credits/USD by
  owned task thread when the account exposes them. Synthetic protocol tests
  validate its handling; no real credit estimate was retrieved here.
- The standard SWE-bench preparation path pins the official v5 harness and
  official task repository. Task selection is fixed before candidate outcomes,
  and gold patches/tests are exported to a separate evaluator directory.
- The larger paper and its literature review exist, including the limitations.
  The broad architecture overlaps strongly with EdgeWise, Router-R1 and
  Uno-Orchestra. A controlled dialogue ablation and full-cost measurement are
  the defensible research extension.

The completed [500-task SWE-bench Verified replay](../../results/swe-replay-001/README.md)
fits held-out success/cost predictors and uses the published outcomes of ten
models (5,000 upstream attempts). These are **not new TTGL model attempts**.
The fixed primary two-model router resolves 64.2% at a source-estimated
`$0.2551/task`, versus GPT-5.2 high's 72.8% at `$0.4736/task`: **46.1% lower
reported inference cost with an 8.6-point quality loss**, failing the three-point
target. Its quality interval is −11.605 to −5.600 points. The method does not
improve on expected random half allocation in this replay.

The portfolio grid contains a 76.2% / `$0.1154` point at utility weight 0.25,
but MiniMax 2.5 high alone has 75.8% / `$0.0733`. The portfolio costs 1.57 times
that inexpensive single model for a 0.4-point observed gain with an interval
crossing zero. This cheap-single-model comparison was explicitly added after
the initial analysis. It does not establish added routing value. All replay
costs are historical source-estimated API inference, excluding router compute,
environments and subscription allocation. Read the complete declared grid and
paired task/repository uncertainty before selecting a future policy.

The replay is exploratory secondary analysis, not prospective preregistration:
public aggregate outcomes were inspected before the analysis protocol was
frozen. The fitting uses task-held-out folds and pre-task issue/repository
features; its oracles use actual test outcomes and are nondeployable. Keep the
complete records and reproduce with the commands in its README. Never promote
this replay to a claim that TTGL's conversational agent solved those issues.
Never promote an official gold-control pass to a model result.

## Why this managed instance cannot finish live metering

The installed CLI is `codex-cli 0.163.0`. Its ordinary login-status command
recognizes ChatGPT authentication. The inherited runtime home is read-only, and
native CLI/app-server initialization fails before inference with:

```text
failed to initialize in-process app-server client: Read-only file system (os error 30)
```

The inspected startup source requires creating/writing an installation-ID file
there. This is an execution-state problem, not evidence that subscriptions
cannot be metered. The latest initialize-only collector probe is recorded in
`results/codex-runtime-20261026/subscription-preflight.json`. It makes no model
request and obtains no credits. Do not keep retrying unchanged commands.

The actual six-arm bridge was also initialized and its native preflight run in
`results/codex-runtime-20261026/blocked-study`. It failed on the first model
before producing any inference events, so the large-model check and all 72
benchmark assignments were not launched. Preserve this failed study; create a
new study directory on the working host rather than resuming this one.

Use an ordinary writable Codex installation or have the platform supply a
supported runtime correction. Do not copy credentials from this instance,
repurpose `HOME`/`CODEX_HOME`, weaken the sandbox, change the read-only mount or
bypass the inherited proxy. A new machine must sign in using its normal
supported flow. Check actual model entitlement there; a model available through
the platform collaboration tool is not automatically available in every CLI
account.

## Suitable next instance

A Linux x86-64 VM with **at least 8 CPU cores, 16 GB RAM and 120 GB free disk**
matches the official evaluator's documented starting guidance. More disk is
useful for multiple images. Use a functional Docker installation with a suitable
storage driver such as overlay2; this instance's vfs setup used roughly 20 GB
for a single image whose published size was around 2.7 GB. Run sequentially
until disk growth and resource consumption are measured.

A GPU is unnecessary for hosted Codex experiments. The approved Runpod budget
is **US$100 total for one 80 GB GPU**, including storage/startup/cleanup, when a
GPU experiment is needed. No Runpod resource has been provisioned or billed by
this work. That authorization is not a separate approval for unbounded API or
other cloud charges. A Runpod key alone does not fix Codex authentication or
provide Docker privileges. Prefer an already available writable workstation/VM
for this first hosted-model study.

Make generation and evaluation genuinely separate environments. The lightweight
runner's prompt/path checks are not a hardened read boundary. Solver workers
must see the issue and base repository, but not gold patches, hidden evaluator
tests or other conditions' artifacts. Expert/router roles should only see their
intended input. Benchmark project dependencies must be installed in the solver
environment, not only inside the evaluator's Docker image. Record that
environment and validate its public tests before scored generation.

## Installation and preflight on the new host

Use [the project guide](project-usage-guide.md) to install Codex 0.163.0, sign in
normally, clone branch `work`, and create the Python 3.12 research environment.
Keep an experiment's CLI revision fixed. Check the current scripts' `--help`
before running; these commands document the committed interface, not results
already observed on the new machine.

After installing the research environment, activate it for the `python`
commands below: `source .venv/bin/activate` for the portable installation in
the project guide. Use the printed environment path instead when invoking the
managed setup script.

The official SWE-bench installation used here is 5.0.2 from harness commit
`02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`. Its task repository is pinned at
`3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d`. Install that official harness into a
separate environment, then prepare the fixed task panel. Keep the private
evaluator root outside solver-visible mounts:

```bash
python3.12 scripts/prepare_swe_bench.py \
  --evaluator-root /absolute/private/evaluator \
  --install-env /absolute/path/tools/ttgl-swebench
```

With `uv` available, `--install-env` installs the SHA-256-pinned official harness
and its locked dependencies. Alternatively use a prepared SWE-bench environment
and omit that flag. The preparation was executed twice here with an identical
task-manifest hash. It produces
`experiments/swe-bench-verified-001/tasks.json` and a private
`/absolute/private/evaluator/selected.dataset.json`. The private file includes
official gold/test material and must never be passed as an agent prompt or
placed in the task repository. Do not choose substitute issues based on which
models already succeeded.

Run official base/gold controls before scored inference. Four controls actually
ran here. SymPy 17139 is valid: base 0/2 target checks, gold 2/2, and both retain
67/67 preservation checks. Requests 5414 is invalid: its reference patch passes
the target check, but only 123/130 preservation checks pass; the full run also
has 158 missing-fixture errors and proxy-sensitive failures. Retain the failed
control and fix its environment or predeclare an infrastructure exclusion.
Ten of the twelve selected environments remain unvalidated. See the complete
[official control records](../../experiments/swe-bench-verified-001/controls/summary.json).

Initialize the study with exact model IDs available in your Codex account:

```bash
python scripts/run_swe_bench.py init \
  --tasks experiments/swe-bench-verified-001/tasks.json \
  --output-dir /absolute/path/study \
  --workspace-root /absolute/path/isolated-workers \
  --small-model "$TTGL_SMALL_MODEL" \
  --large-model "$TTGL_LARGE_MODEL"

python scripts/run_swe_bench.py preflight \
  --study-dir /absolute/path/study
```

The default matrix has six arms: `small`, `large`, `precall_router`, `oneway`,
`reset_expert` and `personal`. The one-way arm uses independent answer-only
proposals; reset-expert permits clarification/challenge with a fresh expert
thread each time; personal preserves the expert thread. All share the same
wall/turn and consultation caps, not necessarily the same realized token cost.
Use `--conditions` only to make an explicit frozen scope change. Freeze
the full matrix, models, effort, time/consultation limits, prices and acceptance
rules before observing model outcomes.

The preflight makes separately recorded tiny requests to both model backends
and requires positive, usable metering. Do not claim a passed preflight from
unit tests or schema availability. Reconcile a resumed controller/expert usage
example with retained Codex logs before the full study. Missing counters,
authentication failure or unavailable model IDs are blockers to a metered run.

## Execute, evaluate and account

```bash
python scripts/run_swe_bench.py run --study-dir /absolute/path/study
```

On a clean restart use `--resume`; it must refuse uncertain in-flight replay.
Reconcile any interrupted call with its session, workspace and provider record.
Do not silently rerun failures until they pass. Keep preflight/development work
separate from scored task work, while reporting both in total research expense.

The runner exports standard predictions per arm:
`/absolute/path/study/predictions/ARM.jsonl`. Evaluate them using official
SWE-bench v5 in the independent evaluator environment:

```bash
swebench eval /absolute/private/evaluator/selected.dataset.json \
  --predictions /absolute/path/study/predictions/ARM.jsonl \
  --run-id UNIQUE-ARM-RUN-ID \
  --workers 1 \
  --timeout 600
```

Use a new run ID for every changed prediction set; the official cache keys
include run ID and instance. Do not pass `--task-repo` merely to identify the
source when using official pulled images: in the inspected v5 harness this
forces rebuilding. Preserve image digests, the actual installed harness version,
stdout, `report.json` and the grader's adjacent `patch.diff`.

Build a grade index with each arm and assigned instance pointing to its official
report. For example:

```json
{
  "small": {
    "repository__name-123": "/absolute/evaluation/logs/run/instance/report.json"
  }
}
```

Use the real frozen instance IDs and include every assigned arm/task, including
failures. The analyzer checks the evaluator's adjacent patch against the exact
exported patch. Supply the index to:

```bash
python scripts/run_swe_bench.py analyze \
  --study-dir /absolute/path/study \
  --grades /absolute/path/grades.json \
  --output-dir /absolute/path/study/analysis-001
```

Add `--prices /absolute/path/prices.json` only with dated sources and a verified
mapping to the served models/tier. The schema is:

```json
{
  "kind": "api_equivalent",
  "currency": "USD",
  "retrieved_at": "REPLACE_WITH_PRICE_RETRIEVAL_DATE",
  "source_url": "REPLACE_WITH_VERIFIED_PRICE_SOURCE",
  "models": {
    "REPLACE_WITH_EXACT_SERVED_MODEL_ID": {
      "input_per_million": 2.0,
      "cached_input_per_million": 0.1,
      "output_per_million": 10.0,
      "accounting": "cached_within_input_reasoning_within_output_cache_write_at_input_rate"
    }
  }
}
```

The numbers above are **schema examples, not a quote**; replace them and the
placeholder strings with verified applicable values. Unknown prices remain
unknown. This accounting convention assumes cache writes are billed at the
ordinary input rate; do not use it for a service with different rules.
Historical reported-cost replay does not need current prices and must retain
the historical accounting boundary. Do not use API-equivalent estimates as
subscription invoices. See [the runner guide](swe-bench-runner.md) for its
complete schema and grade-join checks.

For complete owned task threads, optionally collect backend plan estimates:

```bash
python scripts/collect_codex_usage.py \
  --state /absolute/path/a-finalized-run/state.json \
  --output /absolute/path/a-finalized-run/subscription-usage.json \
  --independent-roots
```

Repeat `--state` to include several finalized harness runs. Only assert
`--independent-roots` after confirming that parent/child charges do not overlap.
The collector performs no new inference and refuses overwrite. Exit 0 means all
requested thread estimates were available; exit 2 means incomplete. Query a
new output file if later settlement is expected. Absent estimates remain null.
Use ccusage as independent aggregation of the same retained logs, not as a
second additive cost source.

Pass the matching complete collector export to the analysis with
`--provider-usage /absolute/path/subscription-usage.json`. The analyzer requires
the recorded source/state hashes and finalized independent-root attestations
before using those estimates. Keep provider-estimated credits separate from
the API-price scenario and actual bills.

## Acceptance before declaring the experiment complete

Require official base/gold validity, complete assigned-task accounting, an
audited patch/report join, and an honest missing-usage assessment. Report point
estimates and paired uncertainty; do not claim noninferiority simply because a
difference is not statistically significant. The registered target is at most
three absolute points quality loss and 25% practical savings, with uncertainty.
The [research design](standard-benchmark-research.md) explains why even 500 tasks
may not prove such a narrow margin.

Write the outcome into the active paper sources, then rebuild PDF, Word and
HTML using `bash scripts/build_paper.sh`. Run the relevant tests and preserve
the complete manifests/results. Commit and push all authorized changes to
`work`, then verify the remote commit. The user already authorized commit/push;
do not stop to ask again for that routine step. Do not commit credentials,
private user memory or benchmark answers into solver-visible inputs.

## Tracking and continuity

The intended external destination is the Fastest Confluence space:
<https://fastestswarm.atlassian.net/wiki/spaces/FASTEST>. Jira should use the
Fastest board/project once a working connector is present. No remote issue IDs
or successful Confluence publication have been established. Update
`docs/research/task-state.json` and its Jira-import CSV while disconnected;
do not describe those local files as synchronized remote tickets.

The old `results/codex-pilot-001` and `experiments/codex-pilot-001` are frozen
historical evidence. Their worker directories have already been used. Never
reuse them as fresh trials or alter frozen graders/protocol hashes. A new
experiment has a new output location and retained source provenance.

Suggested first message for the next session:

> Continue TTGL branch `work` from docs/research/HANDOVER.md. This host has a
> writable ordinary Codex installation with supported ChatGPT login and Docker.
> Verify both model entitlements and live token/credit metering, inspect the
> existing standard-benchmark control/replay results, then complete the frozen
> paired SWE-bench study with independent official grading. Preserve failed
> attempts, report quality and cost uncertainty, update the paper and task state,
> and commit/push. Do not treat offline replay as conversational-agent results.

The user's guiding sentiment remains: **“Believe in me who believes in you.”**

## Policy development continuation

The user sharpened the objective: pursue 95% lower total model inference cost
while retaining at least 95% of matched Sol-only task accuracy. This is a target,
not a guaranteed outcome. Strengthen Luna's independent solving before crediting
expert access, and use a general evidence-driven delegation policy, applicable
beyond coding. See `delegation-policy-development.md` and `prompts/controller-v2-*`.

The first four original task blocks now form disclosed development evidence for
future prompts; do not reuse them as an untouched final test. A separate
12-assignment study is frozen at `results/delegation-development-001/adaptive-001`
(four tasks, Luna, Sol, and assisted Luna), using `scripts/run_policy_study.py`.
Its two positive-token preflights pass. The backend adds shared solving guidance
to standalone and assisted controllers, and additional handoff/escalation guidance
only to assisted controllers. Effective injected prompts are archived separately;
original source and prompt hashes are guarded. Do not edit those files while its
queued run is pending or active.

Local process `/tmp/ttgl_queue_policy_development.py` waits for original PID 87486
to exit and verifies all 72 archived outcomes before starting the new scored run.
Log: `artifacts/policy-development-001.log`. Avoid concurrent image-removing
workers/graders. `/tmp/ttgl_finalize_when_ready.py` waits for complete official
grades, then finalizes each study and computes the declared joint target with
`scripts/report_policy_target.py`. Inspect actual processes and logs before
restarting anything; no implicit retries.

A separate private directory, `../ttgl-heldout-private-20261026`, is preparing the
first 24 tasks in the original deterministic order. Reserve tasks 13 through 24
for fresh held-out evaluation; retain tasks 1 through 12 as the original panel.
Do not inspect held-out model outcomes or choose the final policy after scoring
them. This preparation alone supplies no new environment controls or inference.

Paper source methods now include the isolated live study and general delegation
policy. A development build is exercising the Docker-based Pandoc pipeline, but
final results, frontmatter, discussion and build provenance still require updates,
and every final PDF/DOCX page must be rendered and visually inspected. Artifact
operation markers were already run exactly once per format earlier; do not rerun.

Policy extension software validation: 158 passed, one optional Torch skip, both
subtests passed, real Docker checks enabled. See
`results/delegation-development-001/software-validation-001/validation.json`.
This validates software behavior, not model task accuracy.
