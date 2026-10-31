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

The follow-up now includes both `adaptive-001` and `fallback-001`, each with
four development tasks and three conditions (24 new assignments total). Both
positive-token preflights pass. `selection-protocol.json` fixes highest assisted
resolution count, then lowest absolute scenario cost; independent Luna/Sol
repeats and every candidate remain reported. `scripts/select_delegation_policy.py`
checks registered task identities and hashes before writing an immutable choice.

Current serial queues: `/tmp/ttgl_queue_policy_development.py` runs adaptive after
all original 72 grades; `/tmp/ttgl_queue_fallback_and_controls.py` then runs
fallback, finalizes it, and launches fresh held-out base/gold controls. The old
`ttgl_queue_heldout_controls.py` waiting process was terminated before it started
any controls. `/tmp/ttgl_queue_heldout_validation.py` runs public probes after
those controls; `scripts/validate_policy_workers.py` adds the pinned Pylint pragma
parser smoke without changing the original validator. `/tmp/ttgl_queue_selected_heldout.py`
selects only from the two completed development analyses, waits for staged worker
readiness, creates a validated source configuration and a three-arm held-out
study, binds the selection hash, and runs/preflights/finalizes it. No new inference
is permitted until those checks pass. Inspect logs before restarting any queue.

The held-out reservation is complete: positions 13-24 in the original SHA256
ordering, no overlap with the original panel. Public manifest and private-dataset
hashes are committed; private references remain outside the repository. Any new
image-setup mismatches need explicit audit after the older frozen studies finish,
not silent source-guard weakening or outcome-driven replacement.

`/tmp/ttgl_prefetch_next.py` only warms the next original task's exact frozen
image while the current image is prepared, with a 15-GiB reserve plus incoming
image size and no deletion. Its events are retained in
`results/codex-isolated-20261026/image-prefetch-001.jsonl`. No model assignment,
prompt, evaluator, or solver time limit changes. The native grader's image-list
helper explicitly warns against concurrent use, so grader/worker runs remain
serial. A cold pull or a long official test run is not a stalled model call.

### Compact candidate amendment and current queues

Before any v2 development grades, the documented context-only instruction-file
calibration reduced Sol input from10,481 to6,393tokens and the published-rate
scenario from0.021812 to0.013786USD. Both elementary arithmetic answers were
correct and neither used tools. These two draws establish neither task-quality
retention nor a complete-task saving. Sources and raw counters are committed in
`results/compact-expert-calibration-001`.

A third frozen development candidate, `compact-001`, uses the same adaptive
controller and unchanged acting agents; only context-only specialist/router
instructions are compacted. Its backend/source/system hashes are separately
bound, positive preflights pass, and permission/tool invariance tests pass.
The active registration is `selection-protocol-002.json`; the older two-candidate
registration remains historical. Total planned scored assignments are now
72original+36development+36held-out (before any held-out environment exclusions).

The old WAITING `ttgl_queue_fallback_and_controls.py` and
`ttgl_queue_selected_heldout.py` processes were terminated before starting any
model calls or controls. Their replacements are
`/tmp/ttgl_queue_three_candidate_controls.py` (fallback then compact and their
analyses, then held-out controls) and
`/tmp/ttgl_queue_selected_heldout_002.py` (all three analyses, registered selection,
readiness, selected normal/compact driver and held-out run). The adaptive queue,
original/adaptive finalizer and held-out public-validation queue remain active.
Check current processes and logs rather than restarting old waiting scripts.

All three development caches were seeded with27 archived exact-program official
reports before scored inference. Source snapshots, invariant checks and receipts
are committed. No model attempt, state or usage was reused. Every actual hit
still requires identical patch/image/full grading dataset/timeout and native
report hashes. Independent model attempts remain mandatory. This changes grading
work, not the inference-cost endpoint. The new seed script rejects incompatible
settings and modified reports in behavior tests.

### Integrated held-out readiness

The active tail queue is now `/tmp/ttgl_queue_three_candidate_readiness_004.py`:
it preserves fallback/compact scoring and analysis, then invokes
`scripts/run_swe_readiness.py` for the reserved panel. The prior waiting
`ttgl_queue_three_candidate_controls.py` and separate public-validator queue were
terminated before starting any work. Controls and public probes now run in order
for each case while its immutable image is warm, avoiding a second image download.
The callback runs after both native controls have completed and before image
removal. Native control rows and probe attempts have separate provenance.

The new readiness registration fixes a uniform 1200-second native test limit for
both base and gold controls, matching the scored grader; solver limits remain
unchanged. Existing standalone control commands retain their 600-second default.
Original/development scored-source hashes were checked after this preparation-only
extension and have zero mismatches. Tests cover callback ordering and explicit
resume after a failed public probe without repeating closed native controls.

The selected held-out waiting queue is now
`/tmp/ttgl_queue_selected_heldout_003.py`. It requires all 12 reserved cases to
have valid controls and ready public probes before inference. A recoverable
setup failure therefore requires agent diagnosis and repair, rather than silent
automatic task dropping. Failed preparation containers have their identity and
source diff retained before cleanup; failed records and native reports remain.

## 27 October: completed routing studies, graphs and bounded Pro subset

All 72 original and 36 development assignments are complete. Independent native
patch/report joins and token-delta audits pass for all 108. Original: Luna9/12,
Sol10/12, pretask11/12; continued access9/12 with zero consultations. No assisted
arm meets the joint95/95 target. Adaptive and bounded cheap-first each4/4 on the
same four development tasks, at87.1%/89.1% lower scenario cost than their Sol
controls; Luna controls2/4 and3/4. Compact3/4 with0calls is not evidence that
expert instruction compaction caused a repository-quality change. Final native
records and source hashes are archived. Graphs and interpretation:
results/prompt-comparison-001/README.md (figures-002 is the2x2 layout).

Selected policy remains fallback, frozen before held-out inference. First held
control django7530 passes with sentinel and gold, with identical native report
hashes and all recorded F2P passing on sentinel. Original upstream task metadata
labels a squashmigrations test as F2P while the issue/gold changes makemigrations.
We did not change those labels or tests. Original reservation explicitly permits
invalid independent control exclusions. environment-disposition-002.json records
one exclusion, no replacement, before any model outcome. eligible-tasks-002 has
11. Originalcontrols001/worker-validation001 retained. Private derivative root
../ttgl-heldout-eligible-private-20261027 has exactly those11 unchanged taskrows.

Terminated waiting selected003 PID95492 before held inference; never restart it.
Current /tmp/ttgl_continue_heldout_004.py under caffeinate-s (execsession91285)
runs controls002+worker-validation002, requires all11 valid, then initializes
validated-source002/study002 using SAME selectedfallback, positive preflight,
33scoredassignments, finalanalysis002/target/audit/plot. Log:
artifacts/selected-heldout-continuation-004.log. Source remains frozen after
init. Recoverable public-probe failures STOP for diagnosis; no further automatic
exclusion. Inspect this process before launching overlapping graders.

User prioritizes proprietary prompt/routing comparison FIRST; OSS baseline,
sequence/probability distillation and RL later. No GPU training has run. For the
newer Pro V2 benchmark, user explicitly rejected paying for600task iterations.
experiments/swe-pro-prompt-001 reserves12dev+24disjointvalidation, repository-
roundrobin seeded without outcomes, pins official revision66f92766bba642462d4bbe5479e83f91f9211862.
Only108publicinstruction/config/Dockerfile files downloaded (194803bytes), no
reference solutions/tests. Real validation confirms all filehashes, disjointness
and order-invariant selection. protocol capsdev48assignments (Luna,Sol,adaptive,
fallback with registered shared controls), validation72 (3arms). Firstunit:
environment/adaptervalidation then ONEcomplete taskblock and measureactualcost.
No automatic full642run. No Pro controls/inference yet. Must integrate maintained
upstream Harbor locked evaluator; Verified adapter is NOT yet a Pro adapter.
Official Pro V2 release inspected at pinned revision;642tasks11reposmultiplelangs.

Added docs/paper/live-routing-results.md and buildsource integration, graph.
Generated PDFs/DOCX still previews, finalbuild+fullpageQA outstanding. README
updated to completedlive studies. Pro plots are not fabricated; availablegraph
uses actual Verified pilot/development data. Need finish proprietary heldout
and iterate on boundedPro before claims/learning expansion. Last fullsuite158
remainslastfull; newscriptactualdata validations and4independentaudits pass.

### Learning chapter and Sphinx readiness repair

User explicitly requests paper sections for separate training data, distillation,
RL and learning cost/performance, while continuing proprietary routing first.
Added docs/paper/learning-study.md: executable SWE-Gym/SWE-smith candidates,
train/dev/sealed evaluation and family deduplication, observable action/feedback
traces, current journal's omitted-tool-body limitation, causal loss targets,
sequence versus on-policy probability distillation and API scoring access, RL
reward/integrity controls, matched local/remote checkpoint factorial, standalone
and cooperative learning curves and training-cost amortization. Prospective,
no training results. New abstract includes108actualtrials and95/95targetmiss.
Full build succeeded53PDFpages; newchapterPDFpages42-45 visuallychecked, table
fits, citationsresolve. Final53pagePDF/DOCXQA remainspending; outputs aredrafts.

Readiness004 stopped after6accepted probes at sphinx9320's exact-sourceguard.
Audited gitdiff base..imageHEAD: setup.py dependencycaps only, tox.ini previously
audited pytest-rA. Added exactsetupblobpair206ff4ad4904cd24b81e00dc0b3383fcbb54e6a2
->4bb5faeb12fe7d313b81413f3655954aaa09d9cb, preservingoldpairs; everytrackedfile
stillrestoredtoexactbasebeforemodel. Archive results/delegation-heldout-001/setup-audit-9320-001.
Dockerbehaviorchecks TTGL_CONTAINER_TESTS=1 pytest tests/test_isolated.py:
4passed55.06sec (earlieruninstrumented4skipsnotcountedasverification).

Active replacement /tmp/ttgl_continue_heldout_005.py PID49463 (execsession4578)
under caffeinate-s, logartifacts/selected-heldout-continuation-005.log.
Readiness explicitly--resume reusesclosednativecontrols, newversionedprobe;
Sphinx9320NOWPASSES. NextSphinx10673basefalse/goldtrue; publicprobeinprogress
atlastcheck. Thenremaining4cases, all11mustpassbefore33heldoutassignments.
Old004finishedfailureandmustnotrestart. Selectedfallbackunchanged. No model
callsrepeated. No generationsource editsafterfuturestudy002init/preflight.

For upcomingProintegration inspectedofficialpinnedlocked_codex.py andpatch_replay.py
(read-only artifacts/pro-harness-source): maintainedHarborcustomBaseAgent API,
execandcapture/appor/testbed, authoritativefreshpatchregrade,50minnativebudget.
ProsubsetadapterISNOTimplementedyet. Harbor0.25.0PyPIwheelmetadata/sourceverified
againstSHA inartifacts/harbor-0.25.0/wheel-provenance.json; notinstalled. Current
CLIupstreamadapterexpectsOpenAIcompatibleAPI; we mustkeepnativeChatGPTcredentials
outsideagentworkerswhenwrappingourhostcontroller. ExistingVerifiedMCPusesfixed
/testbed/Conda; cannotjustpointitatProimagesandclaimintegration.

Latestreadinesscontinuation:005stoppedatSphinx10673sourceguard. Exactonlychange
is tox.ini pytest-rA, baseblob7ca990b56df0c4874f2f99179fcf515d24a37b4c
->a0708b02cfe638662f497b834d8551bd23800266. Archivedsetup-audit-10673-001,
addedexactpairandrestoredtobaseasbefore. No corelogicchangeafter4passingDocker
behaviorchecks; actual10673stagedsmokeNOWPASSES.7/11acceptedprobes.
Activequeue /tmp/ttgl_continue_heldout_006.py PID54437,execsession55277,
caffeinate-s;logartifacts/selected-heldout-continuation-006.log. Both004and005
finishedfailed; doNOTrestart.006reusesclosednativecontrolsandresumescallbacks.
Remainder11casepanelstillrequiresallreadybefore33scoredassignments.

LearningchapterincludesMiniLLM/ThinkingMachinesprimaryreferences, with explicit
limitsonreasoning-to-softwaretransfer. Manuscriptbuild002includescombinedgraph
hashesinmanifest; sourcesandabstractupdated. Currentgeneratedoutputsremain
workingdraftsawaitingfull-documentfinalQA/heldoutresults. Do notclaimProadapter
ortrainingimplementedfromthechapterdesign. Nextconcretework: finishremaining
readinessandheldouttrialqueue, thenimplement/validatemaintainedHarbortransport
foroneProtaskbeforelaunchingthe12taskpromptiteration.

## Current continuation: paper learning chapter, live held-out run and Pro adapter

The paper source now has a dedicated learning-study chapter covering training
sources, train/development/sealed evaluation splits, trace credit assignment,
sequence and on-policy probability distillation, RL, matched small/large and
local/remote controls, learning curves and lifecycle cost amortization. The
abstract reports the 108 completed proprietary assignments. Builds succeeded
at 53 PDF pages; the new chapter's four pages were visually checked. Generated
PDF/DOCX/HTML are working previews, not final fully reviewed deliverables. A
small final source clarification about matching distillation teacher identities
still needs the next build. Whole-document final QA waits for final results.

All eleven held-out native controls and staged public probes now pass.
Readiness source repairs for three Sphinx revisions were exact dependency/runner
metadata pairs, archived in setup-audit-{9320,10673,11510}-001; original source
is restored before model access. Main suite: 172 passed, 2 optional skips,
2 subtests in 64.59s, recorded software-validation-002. The skips are Torch and
the separate Harbor runtime. Native preflight-small and preflight-large passed
with positive tokens; no need to repeat them.

Actual held-out study: results/delegation-heldout-001/study-002, 11 tasks x 3
arms =33 assignments, fallback policy. validated-source-002 is only an UNRUN
six-arm source configuration; do not count its 66 config assignments as trials.
The original 008 queue reached init/preflight then stopped before the first
scored call on the incoming-image reserve. No scored invocation was repeated.

CURRENT NATIVE SUPERVISOR: /tmp/ttgl_continue_heldout_supervised_009.py PID74049,
execsession6913, under caffeinate-s. Log artifacts/heldout-supervisor-009.log;
actual run logs artifacts/selected-heldout-supervised-009-attempt-XX.log.
Registered before the first scored request in study-002/resource-continuation-protocol.json.
It resumes only the exact frozen preparation disk errors, requires no output
for the next missing assignment and a clean known base, audits prior native
patch/usage evidence, rejects uncertain inflight calls, and may remove only a
fully graded predecessor image without force. It keeps the ten-GiB reserve and
never retries started inference. Recovery limit13; space wait up to2h. Immutable
preflight/design/policy selection are reused. On completion it finalizes
analysis-002, target report, independent audit and frontier plot. If it stops,
inspect real state and preserve all logs; do not blindly rerun its fixed log
paths or reinitialize/re-preflight/reselect the study.
At the last observed checkpoint: three scored manifests, two grades on the
first task (Sol true, Luna false); assisted grading pending. Read actual state
for updates. Source and prompt edits are prohibited while this run is active.
Older queues004-008 have finished failures and must NOT be restarted.

SPACE CLEANUP: results/host-cleanup-20261027 records108 clean original/development
base clones removed after full independent audits; all patches/grades/traces
retained. Also33 clean closed-probe source clones, two inactive ignored dependency
trees, unused npm content cache, two old ignored compiler-intermediate directories,
and three closed benchmark image caches removed with checks. Test logs, .xcresult,
coverage, source, Products, SourcePackages, credentials and volumes preserved.
Docker VM block reclamation is not a global prune. Active compiler cache was
preserved while305 handles were open. The separate watcher removed it ONLY after
compiler processes ended and open references reached zero; receipt recorded.
Watcher PID is finished. Free space rose to~18GiB before the first model image,
then~14GiB while first-task grading. Allocated counts and observed free bytes
are not a claim of isolated unique physical reclamation. Active CI continues.

PRO IMPLEMENTATION: src/ttgl/harbor_agent.py + harbor_bridge.py and
 tools/worker-mcp/harbor-server.mjs implement the maintained Harbor custom-agent
callbacks plus host native-Codex MCP transport. They keep credentials on the
host, expert roles tool-free, and authoritative token/prompt/trace records
outside worker-mounted agent logs. Bridge commands preserve Harbor agent-phase
context across HTTP threads (important for network policy). Visible bounded
commands/observations carry request IDs; no private reasoning or grader feedback.
The unchanged official Pro verifier and PatchReplayAgent remain the graders.
Actual Pro actor boundary/network/history, privacy, patch replay and native
metering validation are STILL REQUIRED before model trials.

Optional runtime: artifacts/harbor-runtime-001, Harbor0.25.0. Installed separately;
pip check passes. requirements-harbor-macos-intel.lock is the real full freeze,
including NumPy and pytest. cryptography48.0.1 supplies the verified Intel Mac
wheel; the original latest dependency tried to compile with an incompatible old
Rust toolchain, retained in the failed install log. No main runtime changed.
Six checks pass in this runtime (real Harbor callback API with scripted fixtures,
official MCP client roundtrip, role exclusion, thread phase preservation, and
expert tokens included in totals/per-model counts). Scope proof:
results/swe-pro-prompt-001/adapter-validation-002. 001 is retained predecessor.
These are NO MODEL inference and not benchmark accuracy. No distillation/RL run.

First Pro DEVELOPMENT task prepared with scripts/prepare_pro_harbor_task.py,
all11 official files Git-blob/SHA-verified, at ../ttgl-pro-private-20261027.
Task ID instance_NodeBB__NodeBB-97c8569a798075c50e93e585ac741ab55cb7c28b-vf2cf3cbd463b7ad942381f1c6d077626485a1e9e.
Reference/verifier files remain private; only preparation hashes are in repo.
See docs/research/pro-harbor-runner.md for exact boundaries and command guidance.

CURRENT PRO CONTROLS QUEUE: /tmp/ttgl_queue_pro_controls_002.py PID77749,
execsession97525, caffeinate-s, log artifacts/pro-controls-queue-002.log.
Waits for complete Native analysis-002 independent audit, verifies/removes only
its clean owned base clones, checks12GiB free, then runs ONE Pro task with nop
and oracle in separate native Harbor Docker jobs, one attempt, no retries.
Inspects actual native reward0/1 and exception status, archives receipts.
Results: results/swe-pro-prompt-001/environment-controls-002. Registered in
experiments/swe-pro-prompt-001/control-protocol-002.json. It does NOT automatically
start model trials. 001 was superseded while waiting, zero controls/inference,
with explicit queue-ended receipt. Never restart001. After valid controls,
implement/execute actual boundary/history/records invisibility/native usage/
fresh patch replay checks, then ONE full model task block, measure cost/runtime,
and only then the registered twelve-task prompt development sweep. No full642run.

AUTOMATIC CONTINUATION: heartbeat continue-luna-sol-routing-research is ACTIVE
on this chat, every30minutes. Created at the user's instruction to keep going
until experiments/paper are ready. It reads this handover, inspects real queues,
continues implementation/experiments/paper, and stays quiet on unchanged state.
Notify only meaningful results/failure/required action. Keep proprietary routing
first; no new paid services or training ahead of it. Disable on completion.
Update this existing heartbeat rather than creating another.

## 27 October: verification-feedback steering and separate candidate

The user asked to continue on larger data and investigate benchmarks with useful
self-validation feedback. Native supervisor PID 74049 and Pro controls queue
PID 77749 remain live; no duplicate worker or inference was started. The latest
observed native index has seven official grades. The first two complete blocks
give Sol 2/2, Luna 1/2 and personal 1/2, with zero consultations; Sol also succeeds
on django12125. Read the live state for updates.

The failed personal sklearn25747 patch returned complete with self-reported
passing tests. Its independent grade is false, infra_failure false, expert_calls
zero. Native tool journals retain digests/statuses rather than command/output
transcripts, so the reported 15/103 test counts are NOT independently audited.
Evidence: results/verification-feedback-001/preparation-001/failure-observation.json.
Do not infer that Luna ignored a known failing test or reuse this now-observed
case as fresh held-out evidence.

Separate new files: src/ttgl/verification_policy.py and
prompts/controller-v3-verification-{common,delegation}.txt. They extend fallback
with acceptance-criterion coverage checks, discriminating tests, evidence/gap
summaries and help for material unsupported properties even after narrow tests
pass. Common guidance is shared with standalone controls. This candidate is NOT
wired into the current v2 runner or Pro adapter. Its identity is separate and
refuses mutation during execution. Fifteen focused software tests pass; all
reservation hashes/Git blobs and the active held-out frozen source checks pass.
Receipts: results/verification-feedback-001/preparation-001. No model trials.

Primary-source research confirms that Aider's maintained harness returns test
errors after candidate one and permits a second attempt. LiveCodeBench provides
self-repair, but audit feedback construction before claiming public-only
feedback. Interactive Terminal-Bench checks do not remove hidden-verifier
uncertainty. Assessment/design: docs/research/verification-feedback-study.md.
The paper source adds this topic and corrects stale held-out status; generated
previews were NOT rebuilt.

scripts/prepare_feedback_subset.py reserves 12 development and 24 validation tasks
across six languages from Aider-AI/polyglot-benchmark revision
7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f. All development exercise families are
excluded from validation across languages; validation has 23 families. The seed
is outcome independent. Complete 225-task inventory and 36 instruction blobs
are verified. No tests, reference solutions or model outputs were acquired for
this diagnostic. Upstream MIT notices/provenance accompany the instructions.
Reservation and prospective protocol: experiments/verification-feedback-001.
This does not authorize an automatic full 225-task launch.

NEXT: finish and audit the native 33 assignments; let the existing Pro queue
complete its first-task controls, then prove real boundary/metering/replay before
Pro scoring. Implement the feedback adapter using maintained test commands,
equal two-stage error feedback, immutable tests, isolated references, first/final
fresh grades and observable tool traces. Validate one task with empty/reference
controls before its first four-arm development block. Inspect measured runtime
and cost, then expand to 12 tasks (48 assignments maximum). Select the policy
and freeze matched standalone common prompts before the 24-task/72-assignment
validation: v2 common prompts if v2 is selected, v3 if v3 is selected. The v2
development arm is a whole-policy ablation, not a clean delegation effect against
v3 standalone controls. Keep Pro and feedback panels separate, and serialize
benchmark workers/image cleanup. Do not tune validation repeatedly until it
passes or claim reliability from tiny samples. Report the frontier if 95/95
fails. Continue the existing heartbeat; no new paid service or training run.

Subsequent adapter inspection found a maintained Harbor aider_polyglot converter:
reuse it after fixing its observed boundaries/verifier, rather than implementing
a parallel conversion. Pinned inspected Harbor source revision:
e77a18bfeed53f907f335b9132d87006e01b3dfd. Downloaded source is under ignored
artifacts/self-verification-research-001/harbor-adapter. The adapter embeds an
encrypted exemplar in the actor workspace with a public default password; keep
all exemplar material outside the actor image/workspace instead. Its C++ wrapper
returns success even when an executed test returns failure. This was reproduced
on Linux in a disposable, networkless cached Python image with a tiny fixture,
not a benchmark worker or model trial. Receipt:
results/verification-feedback-001/preparation-001/upstream-cpp-exit-audit.json.
Initial macOS-find and noexec-tmpfs probes were unsuitable; the final explicit
Linux exec-enabled fixture ran the failing test and proved exit 1 becomes 0.
Correct exit propagation and test-execution counting without weakening assertions,
then require empty/reference controls before any feedback scores. Latest native
checkpoint: nine official grades, three complete blocks: Sol 3/3, Luna 2/3,
personal 2/3 with zero consultations. Neither queue was interrupted.

## Heartbeat 18:47 UTC: strict C++ verifier adaptation

Read AGENTS/HANDOVER and verified both supervisors live. The native run advanced
to ten official grades (personal pylint6903 succeeds); only the first three
blocks are complete. Pro controls are still correctly waiting for the native
final audit. No started inference was repeated or interrupted.

Added separate src/ttgl/feedback_verifier.py, not wired into active generation.
strict_cpp_wrapper requires the exact audited Harbor snippet hash, retains its
test-fixture staging, enables EXERCISM_RUN_ALL_TESTS as Aider's cpp-test.sh does,
builds the explicitly declared exercise target and executes it with strict exit
propagation. Invalid targets and unreviewed upstream snippets are rejected.
Seven behavior checks pass, 22 with related policy/reservation checks (8.02 s).
Five model-free Linux fixture cases independently verify real exit codes:
pass 0, test failure 7, missing executable 1, configure failure 9, build failure
11. Receipt: results/verification-feedback-001/preparation-001/
strict-cpp-exit-validation.json. No model endpoint was called by these checks.

Important scope correction: Exercism's CMake often has an ALL target that runs
tests while building, which can catch errors before the flawed post-build
wrapper. Our mocked-build fixture proves the latter stage loses failure status;
it does NOT prove actual task grades or published scores were inflated. Research
notes now state this limitation. Real compilation, executed-case accounting,
reference isolation and negative/positive task controls are still pending.
Next step remains finishing native grading, then existing Pro controls and real
adapter validation. The feedback adaptation must be integrated into maintained
task conversion before its own first-task controls; no full diagnostic run yet.

## User steering: measure rescue, and run real handoff / larger comparison

The user rejected lack of improvement over Luna alone and explicitly requested
larger data, routing capability and handoff testing. Do not present availability
of Sol or low cost as a positive routing result. Current native supervision and
Pro control queue remain live and unchanged. Latest checkpoint: 14/33 official
grades, four complete blocks, Sol 4/4, Luna 3/4, personal 3/4 with zero expert
requests. Independent partial patch/report/token audit passed for all 14:
results/delegation-heldout-001/checkpoint-routing-rescue-001.json. That is NOT
the completion audit the Pro queue awaits.

NEW PRO MATRIX BEFORE ANY PRO INFERENCE:
experiments/swe-pro-prompt-001/routing-protocol-002.json supersedes the original
unrun matrix, retaining 12 development/24 validation tasks and caps48/72. Arms:
matched v3 Luna, matched v3 Sol, voluntary v3 consultation, required review after
an independent candidate. The last is a diagnostic, not autonomous routing.
Read docs/research/routing-rescue-study.md. Freeze optional policy before sealed
validation; do not tune repeatedly until it passes. Required-review failures to
consult stay in the quality denominator and get explicit noncompliance counts.

IMPLEMENTED: ttgl.harbor_routing_agent:RoutingDiagnosticCodex with policy options
verification/required_review. It uses the maintained Harbor lifecycle and our
existing native transport; condition=personal maps both cooperative arms, while
job identities and policy distinguish them. Parent harbor_agent now exposes a
backend factory; native frozen study sources do not include that file and were
reverified unchanged. The new class captures pre-handoff.patch on the host before
the first expert response using a temporary Git index, preserving real staging
and including new files. Only after generation does it export a replay copy to
agent/pre-handoff.patch. Grade with unchanged official PatchReplayAgent using
patch_name=pre-handoff.patch, alongside separate final-patch fresh regrading.
Never grade the candidate during solving or provide the grade to the model.
Snapshot time is debited from the same call deadline and recorded elapsed time.

Eighteen actual-runtime software checks pass (9.36 s), including all prior six
adapter tests, real Git/index and phase-context snapshot checks, actual callback
fixtures for all four arms and paired rescue/regression/missing-evidence metrics.
Receipt: results/swe-pro-prompt-001/adapter-validation-003. This extends the old
proof, not real Pro environment or accuracy validation. Existing nop/oracle
queue retains its old immutable proof/control registration; do NOT restart it.
Use the new proof/source freeze for subsequent model trials.

LIVE NATIVE HANDOFF TEST DID RUN:
results/handoff-mechanism-001. Three native calls: Luna proposes and asks, Sol
reviews, Luna integrates. One consultation, zero tools, complete positive
per-model usage, event deltas independently reconciled. Public context marker
was actually forwarded. Sol found a NaN edge case in Luna's clamp proposal;
Luna switched to explicit branches. Six POST-HOC sandbox checks: initial5/6,
final6/6. This is a context-only REQUIRED handoff mechanism result, NOT benchmark
accuracy or autonomous routing. Initial empty allowed_paths metadata was rejected
before run-directory creation/inference; the rejected task and zero-call
correction receipt are retained. No started call was repeated. Validation and
native events/manifests are archived; there are no private reasoning traces.

ALL TWELVE PRO DEVELOPMENT TASKS PREPARED using the existing pinned preparer.
Fresh separate evaluator roots under ../ttgl-pro-development-prepared-20261027/
<instance_id>/, each with its own preparation.json and v2/tasks directory.
Do not add them to the original ../ttgl-pro-private-20261027 root: the existing
queue is deliberately one-task controls only. Preparation receipt/index:
results/swe-pro-prompt-001/development-preparation-001/receipt.json and the
private root's development-index.json. Only development reference/verifier files
were acquired; sealed validation private files were not. These are preparation,
not empty/reference checks or model assignments.

NEXT: finish/audit the native33; let existing Pro first-task nop/oracle controls
finish; prove the real offline actor boundary, host-record invisibility, native
usage through the actual transport and pristine replay. Then execute one full
four-arm Pro development block, inspect cost/runtime, and expand within the
registered twelve-task cap. Capture and later regrade pre-handoff candidates
and final patches; use handoff_metrics for paired rescue and loss. Source
hashes must match adapter-validation-003 and then the actual pre-inference freeze.
No Pro model inference has occurred yet. Keep Aider feedback work separate;
prioritize this larger proprietary rescue comparison before training or RL.

## Heartbeat 19:17 UTC: real Pro preflight and first block queued

Native supervisor 74049 recovered a registered preparation disk guard failure
after fifteen completed assignments. Receipts record zero repeated inference;
it subsequently reached nineteen official grades, six complete task blocks.
It and Pro controls queue 77749 remain live. Inspect recovery events/processes
rather than acting on an old traceback. No additional cleanup was performed.

NEW LIVE QUEUE: PID 44928, execsession 51778, under caffeinate-s:
scripts/continue_pro_rescue.py --protocol
experiments/swe-pro-prompt-001/pro-pipeline-protocol-003.json --output
results/swe-pro-prompt-001/first-block-003
Log: artifacts/pro-rescue-pipeline-003.log. queue.json currently says waiting for
existing one-task controls. Never start another copy or reuse that output path.

The queue waits for the existing native33/audit -> Pro nop/oracle chain. It
validates both real control reports and the twelve-GiB reserve before running
ttgl.harbor_preflight:NativeProPreflight. Before model calls, that agent checks
clean source, absence of commits outside HEAD, absence of known private paths
and a host-only sentinel, and direct-IP egress under the no-network actor phase.
The network probe tests one endpoint, not universal security. Missing or
ambiguous observations stop before inference.

The mechanism-only preflight allows 180 seconds, six outer calls and two
consultations. Luna must create/read one random witness file, obtain actual HEAD
and send these observations to Sol, then integrate. Only the witness may change;
the original issue is not supplied. Native metering and actual selected-context
transfer must pass. SETUP inference is reported separately from task quality.
The unchanged official PatchReplayAgent then replays the nonempty witness on a
pristine image: apply_rc must be zero, diffstat must name the witness, and the
unfixed task must retain its known negative reward. No scored trial precedes it.

If every real gate passes, the queue runs ONE four-arm block in the registered
order large, required_review, optional, small. All share v3 common guidance,
2940 seconds, six outer turns, two expert calls and 24k context. Final patches
and available pre-handoff snapshots receive separate pristine regrades AFTER
generation. Native token deltas are audited before costs are calculated.
Unknown tokens/bills stay unknown. Required-review noncompliance remains in the
denominator; attempted expert requests and completed consultations are distinct.

Success writes first-block-003/{records.json,paired-rescue.json,completion.json}.
It stops for actual cost/runtime review before expanding to twelve tasks. No
sealed validation or full population starts automatically. Failure writes
stopped.json and retains unique invocation/native logs. Reconcile those before
any versioned continuation; NEVER repeat started or uncertain model inference.
The locally resolved task-image ID is bound across every job. Sources and the
twelve-GiB reserve are checked before each job; there is no forced image cleanup.

SOURCE FREEZE: protocol003 binds 34 generation/prompt/runtime/task/rate files,
including the pipeline and preflight. Do not edit bound files while PID 44928 is
active. This supplements the native study freeze. Docs/tests may change, but a
generation change requires reconciliation and versioned registration.

Before registration, 34 software checks passed in the actual Harbor runtime
(11.15 seconds), including the earlier 18, boundary decisions and corrupt-token
audit rejection. Receipt: adapter-validation-004. Real actor checks and Pro
scores remain PENDING. Final patches are now sealed in unmounted records before
the in-place verifier; fresh replays use sealed host-only sources rather than
mutable agent logs. Native frozen sources were reverified unchanged. The old
Pro control queue and its immutable original registration were not modified.

## Heartbeat 19:47 UTC: first real held-out paired rescue

All three queues remain live: native supervisor 74049, original Pro controls
77749, new Pro pipeline 44928. At inspection: 21/33 official grades, seven
complete blocks, Sol 7/7, Luna 5/7, assisted Luna 6/7. Assisted Luna has two
completed consultations, both on sphinx10673. This is the first held-out
paired rescue relative to standalone Luna. It loses none of Luna's successes.

Independent partial audit of all 21 passed: checkpoint-routing-rescue-002.json.
Interim records/report/figure: results/delegation-heldout-001/interim-007.
Total scenarios USD: Luna 0.04639970, Sol 1.15456560, assisted 0.08409922.
Assisted saving 92.7159%, retention 85.7143%; joint 95/95 still fails. Added resolution
cost relative to Luna is 0.03769952 and half the observed Sol–Luna resolution gap
is closed. Treat this as descriptive, incomplete independent-attempt evidence.
The run must continue unchanged to 33; no selection/stopping rule changed.

Trace: Luna reports a new regression test still fails and asks for diagnosis.
Sol requests exact code and builder observations. Luna's second message locates
an earlier directive-parser warning path; Sol then advises keeping generated
pages out of source dependencies and fixing the module-index fixture. The final
patch passes official grading. Both expert responses retain the same thread,
first request_context then answer. This is real voluntary bidirectional delegation,
not the earlier forced toy. However Luna itself found the earlier warning path,
the expert did not receive all requested exact code (paths were supplied instead),
and no pre-consultation patch exists in this old runner. Do not attribute the
whole success causally to Sol. Local check counts remain self-reported because
the old journal retains tool hashes rather than full command/output text.

Archived only this closed task's three-arm run records, patches, official reports
and seven effective prompts, plus a hashed rescue-episode.json. No in-flight
case was staged or modified. Interim graph uses the existing plotting tool with
an added optional title, clearly labels 7/11 tasks and 21/33 grades, and was viewed
at full resolution. That plot script is not a frozen generation source. Paper
source and README now include the interim rescue and its limitations. Generated
PDF/DOCX previews remain stale and are not final deliverables.

No new model inference, retries, source changes to frozen code, cleanup or paid
services were launched this heartbeat. Pro pipeline remains correctly waiting
for the original control chain. Its queue.json records the INITIAL waiting
state, not a live stage tracker; inspect invocation files/native jobs and
stopped.json/completion.json plus actual process liveness for subsequent status.


## Heartbeat 20:17 UTC: resource wait, 25 official grades

The supervisor (74049) and both Pro queues (77749, 44928) remain live.
Native held-out generation paused at the registered pre-inference 10 GiB guard;
25 official grades and eight complete matched blocks exist. Those blocks have
Sol 7/8, Luna 5/8 and assisted Luna 6/8. The eighth case failed in all arms;
the previously recorded rescue remains, but the seven-case report is an older
immutable interim checkpoint rather than the latest denominator.

A new read-only checkpoint-resource-025.json audit independently covers all 25
completed assignments; resource-recovery 01 was an earlier 20-assignment audit. Next unstarted: personal/sphinx-doc__sphinx-11510.
The supervisor waits for reserved space and does not repeat completed inference.
Observed free disk is below 10 GiB. Active Calorie Xcode compilation and its
2.2 GiB compiler cache are preserved. Docker has no running containers and no
remaining closed-task images eligible for removal; the current Sphinx image
is needed. No broad cache deletion or worker restart was performed.
Resource snapshot: results/host-cleanup-20261027/resource-wait-2017.json.

All 34 Pro pipeline source bindings were reverified unchanged. Pro controls
and scored trials remain unstarted behind the full native audit gate. Let the
existing supervisor continue after space returns; if it times out, reconcile
its recorded preparation failure and all manifests before versioned continuation.
Do not restart any model invocation blindly.

## Heartbeat 20:47 UTC: disk reserve restored, native continuation resumed

Initially still 25/33 official grades; all three queues live. The Calorie
compiler had ended and its 2.3 GiB rebuildable cache had no open references.
Verified all 25 completed assignment clones against the known base commit and
full porcelain status including ignored files; all clean, all grades/patches/
traces retained outside those clones. Open-file checks on both roots found none.
Removed only those 25 clean clones and the inactive compiler cache. Preserved
active CI, source, products, unique logs, credentials and database volumes.
Receipt: results/host-cleanup-20261027/inactive-resource-recovery-2047.json.
Free bytes increased from 8,061,300,736 to 13,379,182,592 at receipt completion.

The SAME registered supervisor 74049 resumed automatically as attempt-08;
child runner 50101 is live and personal/sphinx-doc__sphinx-11510 now has its
new run state. Do not repeat it. Earlier attempts 02–07 were registered
preparation-only resource retries, not repeated model calls. No generation
source was changed and all 34 frozen Pro bindings still match. Pro queues
remain correctly waiting for the full native audit. Grades remain 25 at this
inspection; no new quality result claimed. Commit and push this cleanup receipt.

## Heartbeat 21:17 UTC: 30/33 audited, final task preparing

Native supervisor 74049 remains live, attempt-10 runner 20880 with Docker child
21528 preparing the final SymPy21847 image. No model run state for that task at
inspection; do not launch another worker. Registered recovery 09 audited all 30
prior assignments and removed only the completed Django13109 image without
container references. The 10 GiB reserve remains unchanged. Pro queues 77749
and 44928 remain waiting for final native audit; no new Pro model results.

New independent read-only audit checkpoint-resource-030.json passes all 30.
Ten complete blocks: Sol 8/10, Luna 6/10, assisted 7/10; no lost Luna successes.
There are now four consultations: Sphinx11510 used two but failed in all arms.
Scenario USD totals 1.56228240 / 0.06298606 / 0.13599578 (Sol/Luna/assisted),
saving 91.2951%, relative retention 87.5%, joint target false. Hashed per-task
snapshot checkpoint-030-cost-quality.json and paper source updated. Treat as
interim, never completed results; pending final block must run unchanged.
No source mutation, model repeats, new paid services or cleanup this heartbeat.


## Heartbeat 21:47 UTC: held-out complete; Pro environment failure isolated

Native study completed all 33 assignments and supervisor exited successfully.
analysis-002/independent-audit.json: complete_study_audit, audited=assigned=33,
missing=[], 362 MCP events. Final quality: Luna 7/11, Sol 9/11, personal 8/11.
Personal four expert requests/responses across two tasks, one paired rescue,
zero lost Luna successes; closes half the Sol–Luna gap. Scenario USD totals:
Luna .06591400, Sol 1.63011920, personal .13945384. Saving 91.4452%, relative
retention 88.8889%, joint target FALSE. Added scenario cost versus Luna .07353984.
Official execution records 32 plus one exact-program grade reuse; not 33 test
executions. Native usage all reconciled. Graph inspected at full resolution.
Paper source and README updated; generated document previews still need rebuild
and full visual QA. No population noninferiority or causal-expert claim.

Pro original no-op control failed during environment construction, before actor
execution/model inference. Oracle did not run. Queue 77749 exited; pipeline
44928 detected its exit and wrote first-block-003/stopped.json. No Pro model
invocation exists and do not restart the same output directories. All attempts
and error logs retained. Root cause: Harbor .25 requires nftables FIB INET for
phase-varying egress; Docker Desktop LinuxKit 5.15.49 has FIB IPv4/IPv6 disabled.
Exact cached pinned Alpine probe independently exits 1. Initial public image
pull also hung in Docker credential helper; isolated empty Docker config pulled
that exact image successfully without modifying credentials. This did not fix
the kernel limitation. Receipts kernel-probe-diagnostic.json and
public-kernel-image-pull.json in environment-controls-002.

Next: preserve the public-setup/no-network-actor/public-verifier requirement.
Evaluate maintained Docker network disconnect/reconnect as a narrowly scoped
Harbor environment integration for this host, or an existing compatible local
runtime; do not claim egress support or bypass the guard. Any continuation must
be newly versioned with source bindings and new control output directories,
retaining zero Pro model calls until actual actor-boundary/replay gates pass.
No extra paid resources or changes to the completed frozen native run.

### Same heartbeat: Docker phase mechanism verified, integration still pending

Maintained Docker bridge disconnect/reconnect works on this host. New reusable
scripts/probe_docker_network_phases.py performed real positive peer HTTP control,
removed all actor network attachments, observed failed peer reachability, then
restored the network and positive HTTP response. Both owned containers and the
owned bridge were removed successfully. Receipt docker-network-mechanism-004.json.
This is NOT Harbor integration, universal egress proof or a Pro quality result.
Earlier fixture failures 001–003 are retained: Alpine lacks httpd (exit127);
the Python server fixture then needed a real readiness gate before HTTP checks.
No model calls were made in any probe. Do not confuse these with model retries.

Next implementation is a narrow Harbor Docker environment subclass using its
custom environment import path and Docker network attachment transitions for
PUBLIC/NO_NETWORK phases only. Reject allowlists and unsupported configurations;
preserve actual agent phase context and existing worker/patch/metering gates.
Prove transition on the real Harbor task before versioned nop/oracle controls,
then register a new pipeline output/protocol before any model inference. Existing
pipeline003 is stopped, not active; retain all frozen sources/protocols as history.

## Heartbeat 22:17 UTC: real Harbor network integration passes

Read AGENTS and current handover, confirmed all old supervisors/queues exited;
no live Pro/model trial was restarted. Implemented the narrowly scoped
`ttgl.harbor_docker_network:DetachedNetworkDocker` using Harbor's supported custom
environment hook, inherited lifecycle/exec/mounts and Docker attachment commands.
Public/no-network only; rejects unsupported allowlists, Windows, custom Compose,
published ports, elevated network capabilities and Docker socket access. Checks
running actor identity and actual attachments before/after each transition.
Models cannot enter a phase after a failed transition. No nftables guard bypass.

Reproducible real lifecycle check: scripts/probe_harbor_network_phases.py.
Final receipt harbor-network-fixture-004.json matches current source SHA and
passes public HTTP -> zero attachments/failed numeric-IP HTTP -> restored HTTP,
plus unsupported-allowlist rejection and full fixture cleanup. No model calls.
Earlier fixtures retained: 001 found broken global Docker Compose symlink;
002 reached isolated phase but DNS retry exceeded exec timeout. Fixture now
uses a known peer's numeric IP to test routing separately from resolver delay.
003 passed; 004 repeats after accurately disabling advertised Windows support.

Task-local DOCKER_CONFIG artifacts/harbor-docker-public-config-001 contains only
cliPluginsExtraDirs pointing to installed Docker.app plugin, Compose 2.15.1.
Global symlink and credentials unchanged. Config and intended import path are
recorded in experiments/swe-pro-prompt-001/docker-network-runtime-001.json.
Existing upstream .25 lacked required kernel capabilities; this extension adds
only missing host-specific PUBLIC/NO_NETWORK phase switching, not a new harness.

Removed only the fully graded final SymPy image (audit33, zero container refs,
no force), then reclaimed Docker VM unused blocks. Receipt closed-final-image-2217.
Other active CI/compiler cache preserved: compilation has resumed. Free space is
still below the Pro12GiB reserve, before accounting for incoming actual task image.
No Pro controls or model calls launched. All old failure directories preserved.
Next: inspect resource liveness, recover only verified inactive cache if eligible,
prepare actual first Pro image with reserve, then register NEW nop/oracle controls
using custom import and isolated Docker config. After those and actual actor/
metering/replay gates pass, register new pipeline/protocol/output (003 stays stopped).
The whole proprietary study/paper is not complete; heartbeat remains enabled.

## Heartbeat 22:47 UTC: image verified; new model-free control supervisor queued

No old model/Pro workers were live; completed native grades unchanged. Active
Xcode/compiler and its 2.9 GiB cache remain preserved. No cleanup this heartbeat.
Old Docker20.10 `manifest inspect` incorrectly reported no such manifest for the
first official Pro OCI image. Direct anonymous-token GHCR request returns HTTP200;
manifest SHA256 is verified against raw response bytes and registry digest:
0c1bda3771a33dc39070bf3b130b7217a352a144a7e2a9e1360d88113840ed1b.
Official image exists; do NOT call it unavailable. Layers total868,696,622
compressed bytes; uncompressed size remains unknown until pull. Diagnostics
pro-image-manifest-001.json (old CLI failure) and
pro-image-registry-diagnostic-001.json (registry success; no tokens retained).
Official v2 README still specifies these public anonymous GHCR images and
public-setup/no-network-actor/fresh-grading protocol:
https://github.com/scaleapi/SWE-bench_Pro-os/blob/main/v2/README.md

New scripts/continue_pro_controls.py is a staging-only supervisor, registered
control-protocol-003.json. PID82715 (caffeinate82716), exec5615,
artifacts/pro-controls-queue-003.log. Output environment-controls-003.
It verifies completed native audit33 and frozen source bindings; waits up to2h
for18GiB free (12GiB reserve plus conservative6GiB incoming-image allowance,
NOT a claim of known uncompressed size). Current free12GiB. Then pulls the exact
registered digest, records actual image size/ID, tags it with unchanged upstream
reference, checks12GiB before each control, and runs ONLY nop/oracle once each
with fresh native Harbor output and DetachedNetworkDocker through the supported
custom import path. Positive/negative reward and exceptions inspected, no CLI-only
success. Failure preserves stopped.json, no automatic retries. No model agents or
scored assignments are authorized by this supervisor; a successful pair DOES NOT
start inference automatically. Existing pipeline003 remains stopped.

SOURCE FREEZE: control-protocol003 binds new control supervisor, network adapter,
runtime lock, actual passing fixture004, prior audit, task preparation and all11
pinned private files, plus credential-free isolated Docker config. Do not edit
bound files while82715 is active. Runtime compatibility config001 and all prior
failures remain history. This queue should advance when active CI releases its
transient storage; never delete active compiler data to force it. Inspect real
PID, invocations, image binding, native jobs, summary/stopped rather than initial
queue.json alone. Still zero Pro model calls and no new quality results.

## Heartbeat 23:17 UTC: inactive cache recovered; repaired first-block pipeline queued

Control003 PID82715 remains live, waiting before any image pull or control.
No new native grades or Pro quality results. Database container
256cd0e3ccb3 (Supabase Postgres) is active and preserved with all volumes.
Xcode/compiler exited; no compiler processes or open references remained in
3.6GiB compiler cache. Removed only that rebuildable cache, recording
inactive-compiler-cache-2317.json. Free bytes10,025,836,544 ->13,899,378,688
at completion. Recent node_modules directories inspected but preserved.
Free space still about5GiB below the registered18GiB image-preparation gate.
Do not lower it silently or delete live CI/database data. Control003's2h wait
will stop cleanly if the required reserve does not return.

Repaired scripts/continue_pro_rescue.py to use registered custom environment
import path and task-local DOCKER_CONFIG, defaulting to original Docker behavior
for historical protocols. All34 existing Harbor/preflight/handoff/token-audit
checks pass9.84s. Receipt adapter-validation-005. Completed native sources and
frozen control003 sources unchanged. Old first-block003 has no invocation files
or jobs; reconciled before registering the successor, no model inference repeated.

New pro-pipeline-protocol-004.json binds39 source/runtime/task/rate files.
PID7341 (exec9049), log artifacts/pro-rescue-pipeline-004.log; output first-block004.
It waits for control003's actual nop0/oracle1 summary, independently rechecks
native results, and then performs the already registered real actor/private-path/
metering/patch-replay preflight before ONE four-arm first block. Same task,
v3 prompts, model IDs, bounded call limits and arm order; no full12/24 auto-run.
Private native record root ../ttgl-pro-native-records-20261028 avoids old attempts.
No new model calls yet. Stop and preserve any started/uncertain call; no retries.
All39 pipeline sources and control003 bindings are now FROZEN while queues live.
Only docs/reporting/tests outside the bindings may change. Inspect real PID,
image-pull/native invocation files and stopped/completion, not initial queue state.
The first-block cost/runtime review remains required before further development.

## Heartbeat 23:47 UTC: paper reconciled; queues unchanged

Read AGENTS/HANDOVER; actual PIDs82715 and7341 still live, no image-pull/native
invocation files, no new grades. Free disk roughly10GiB with active Xcode/swift
compilation again; preserve those caches. No cleanup or model calls this pass.
Control003 and pipeline004 frozen source bindings verified unchanged.

Used independent time for paper source reconciliation. Frontmatter now counts
141 fresh assignments (72 + three12 +33), includes final held-out8/11 vs7/11 vs9/11,
91.45% scenario saving and88.89% retention, and the explicit target miss.
Live-results chapter now leads with final held-out evidence rather than appended
seven/ten-case snapshots and contradictory in-progress language. Historical
interims stay archived. It retains failed control eligibility disposition,
rescue/handoff limitations, failed consultation, missed escalation, and prospective
Pro distinction. Conclusion/reproduction now distinguish early read-only managed
host failure from actual authenticated desktop trials, include read-only final
audit/target commands, and remove obsolete publication-system workflow prose.

Verified all five closed independent audits (72/12/12/12/33) and exact final
comparison values against real reports; no pooling of repeated-task panel
accuracy. Receipt results/paper-source-reconciliation-001/receipt.json hashes the
three reconciled source chapters and audits. Diff whitespace checks pass for
these edits. Generated PDF/DOCX/HTML remain earlier working previews and need
rebuild plus complete visual QA after bounded experiments; no final document
completion claim. No new Pro quality result or inference. Queue headroom remains
the previously reported blocker, so do not issue repetitive unchanged alerts.

## Heartbeat 00:17 UTC: observed host-capacity blocker

Read AGENTS/current handover, inspected real PIDs82715/7341 (live), queue events,
native invocation absence and actual disk. Free5.1GiB with Xcode and two Swift
compiler processes active. No image pull, official Pro control or model call
has begun. Resource gate18GiB now lacks roughly13GiB, a material deterioration
from earlier10–14GiB observations. Active CI/data preserved; no cache deletion
or new run this pass. All control003/pipeline004 source bindings still match.
Snapshot results/swe-pro-prompt-001/resource-blocker-001.json.

User notified once that additional host capacity is required if active CI does
not release it. Do not keep repeating unchanged blocker updates. Current
staging supervisor has about33min remaining on its registered2h resource wait;
if it expires, reconcile stopped.json and pipeline failure, preserve zero-call
attempts and do not blindly restart. Existing queues are the only continuation
path while live. No paid services or deletion of user files/live CI is authorized
as a workaround. Paper source is reconciled; preview rebuild/visual QA and Pro
quality results are still pending. Heartbeat remains enabled because requested
bounded studies and final paper are incomplete.

## Heartbeat 00:47 UTC: resource wait expired; paper previews rebuilt

Read AGENTS and current handover, inspected live PIDs/queues before any action.
Both control003 and pipeline004 reached their registered resource timeout during
this pass and exited. Control003 stopped before image preparation; pipeline004
then detected exited control process. Inspected both stopped.json files and
verified no image/model invocation files or jobs in either output. No Pro model
inference occurred and no worker was restarted. Resource events and failures
are archived. Capacity is the existing concrete blocker; no new permission or
paid service requested, no user files/active CI/cache removed this pass.
Reconcile these zero-inference outputs before any NEW versioned continuation
once the preparation reserve is actually available. Do not restart004/003 in place.

Independent progress: rebuilt PDF/DOCX/HTML/assembled Markdown with current141
assignment evidence. Build004: 16,273 words, PDF55 pages, DOCX43 rendered pages.
Used bundled LibreOffice via packaged render_docx.py (not desktop LO). Inspected
changed abstract, results/graphs and conclusion pages in both formats. Found a
right-margin overrun in the reproduction command on PDF51/Word40. Replaced long
record-path argument with local ttgl_analysis variable; rebuilt and re-rendered,
then verified corrected PDF51 and Word40/41. The corrected command reproduces
archived target95/95 JSON exactly without model calls. All build source/artifact
hashes verified. Markers had already been run earlier; not repeated.

Working previews are now committed with explicit non-final README language.
Receipt results/paper-preview-qa-004/receipt.json records precise partial visual
coverage. Current Word pages1,4,5,29,30,40,41 reviewed; first five inherited from
build003 by exact PNG hashes (41/43 pages unchanged;40/41 rechecked). Current PDF51
reviewed after fix; earlier build003 PDF5,6,35–38,51,52 inspected. No all-page
100% QA claim; full review and Pro results remain pending before final delivery.
QA intermediates under artifacts/paper-qa-003 and004, not final artifacts.
Do not disable heartbeat or mark research complete. Keep unchanged capacity
checks quiet; continue independent paper QA while waiting for sufficient space.

## Heartbeat 01:17 UTC: complete Word preview visual review

Read AGENTS/latest handover and checked real processes and closed queues. No
research worker remains live; free disk9.9GiB is below registered18GiB Pro
preparation gate. No cleanup, image pull, model call or restart. Existing
capacity blocker persists; preserve zero-call stopped attempts and use fresh
versioned continuation only after capacity returns.

Inspected remaining36 current build004 DOCX page images. Combined with seven
previously reviewed current pages, all43 Word pages now have visual review.
No additional clipping, overlap, missing glyph or figure/table defect observed.
Receipt results/paper-preview-qa-005/receipt.json binds exact current DOCX and
all43 rendered PNG hashes and records coverage. This is working-preview QA,
not final paper completion. Main XeLaTeX PDF still has only current page51
certified; complete its55-page visual review separately. No scientific results
changed. Pro bounded trials and final research remain incomplete; heartbeat
stays enabled.

## Heartbeat 01:47 UTC: PDF review continued

Read AGENTS/latest handover; actual control003/pipeline004 stopped receipts
still show resource expiry/process exit, no live research workers. Free9.8GiB,
below18GiB gate. No new queue, cleanup, image pull or inference.

Applied existing PDF skill read-only workflow; rendered and visually reviewed
current main PDF pages1–8. Body/title fit; contents page3 has cramped separation
between two-digit chapter numbers10–12 and titles. Repair TOC number-column
width before final delivery, then re-render affected pages. No source changed
this pass. Exact PDF/PNG hashes and remaining46-page review coverage recorded
in results/paper-preview-qa-006/receipt.json. Current main PDF reviewed pages
are1–8 and51; Word43-page review remains complete for unchanged DOCX. No new
scientific result or final-document completion claim.

## Heartbeat 02:17 UTC: repaired PDF contents spacing

Read AGENTS/latest handover, checked real process liveness, stopped receipts
and native33-assignment complete audit. No research workers; disk9.8GiB below
18GiB gate. No model or image invocation/restart/cleanup.

Fixed root cause of contents spacing in shared layout.tex: report-class chapter
numbers have a distinct tocloft width from section numbers. Guarded chapter
width3em preserves compatibility with article-class documents. Rebuilt working
previews (build005,16,273words), visually verified both current contents pages.
Current PDF1,4–8 PNGs exactly match previously reviewed images;2/3 newly reviewed.
DOCX ZIP members changed: ['docProps/core.xml']; unchanged member content preserves
prior43-page Word review despite ZIP metadata differences. Receipt
results/paper-preview-qa-007/receipt.json binds actual artifacts. Current PDF
review1–8 complete;9–55 still require review/equivalence (old51 inspected).
No final-paper or new scientific-result claim. Heartbeat remains enabled.

## Heartbeat 02:48 UTC: PDF review through page20

Read AGENTS/latest handover, checked real process liveness, stopped control003
receipt and completed33-assignment native audit. No research workers live;
free9.8GiB still below18GiB preparation gate. No model/image invocation,
restart or cleanup. Existing capacity blocker unchanged; no repeated alert.

Rendered and visually inspected current build005 main PDF9–20, including
prior-art table, equations and architecture figure. No additional clipping,
overlap or missing glyph found. Receipt results/paper-preview-qa-008/receipt.json
binds current PDF and12 inspected page PNG hashes. Current PDF1–20 reviewed;
21–55 remain. Word content unchanged apart from core metadata per prior receipt.
No new scientific result or final-delivery claim; heartbeat stays enabled.

## Heartbeat 03:18 UTC: PDF review through page32

Read AGENTS/latest handover; checked actual process liveness, stopped control
receipt and33-assignment native complete audit. No research workers live;
free9.8GiB below18GiB resource gate. No image/model call, restart or cleanup.

Rendered and visually inspected current main PDF21–32: methods, tables,
economic equations and historical pilot results. No additional clipping,
overlap or missing glyph observed. Current PDF1–32 reviewed;33–55 remain.
Receipt results/paper-preview-qa-009/receipt.json binds actual PDF and12page
PNGs. No scientific results changed; no final completion claim. Existing
resource blocker unchanged, no repeated user alert. Heartbeat remains enabled.

## Heartbeat 03:48 UTC: PDF results and frontier review

Read AGENTS/latest handover; inspected actual liveness, stopped control receipt
and33-assignment complete audit. No research worker live, free9.8GiB below18GiB
gate. No new image/model invocation, restart or cleanup.

Rendered and visually reviewed current main PDF33–44, including results tables
and three cost-quality figures. No additional clipping, overlap or missing
glyph observed. Target regions and misses are legible. Current PDF1–44 reviewed;
45–55 remain. Receipt results/paper-preview-qa-010/receipt.json binds actual PDF
and12page PNGs. No scientific result changed; existing resource blocker unchanged.
No final completion claim or repeated alert. Heartbeat stays enabled.

## Heartbeat 04:18 UTC: current preview visual QA complete

Read AGENTS/latest handover; inspected actual processes, stopped control003
receipt and complete33-assignment audit. No research workers live. Disk11GiB
still below18GiB gate; no image/model call, restart or cleanup.

Rendered and visually inspected remaining main PDF45–55, including learning
protocol, discussion, reproduction, conclusion and bibliography. All55 current
PDF page images now reviewed across QA007–011; no further clipping, overlap or
missing glyph observed. References wrap within text block; reproduction command
fits. All43 Word pages remain reviewed (only core metadata changed on rebuild).
Receipt results/paper-preview-qa-011/receipt.json binds current PDF/DOCX and all55
PDF PNGs; README now distinguishes completed preview QA from pending research.
No final research delivery or Pro quality result. Next work is capacity recovery
and fresh versioned staging continuation, preserving stopped zero-call attempts.
Do not disable heartbeat: bounded Pro trials and final manuscript remain pending.

## Heartbeat 29 October22:00 UTC: capacity recovered; model-free controls resumed

Read AGENTS/latest handover and inspected real processes, closed control003/
pipeline004 receipts and complete33-assignment audit. Host free38GiB now exceeds
18GiB preparation gate; active Xcode/Swift CI preserved. Reconciled both old
output directories: no invocation files or jobs; original stopped receipts
retained. Verified every registered control003 source SHA256 still matches.

Registered control-protocol-004.json before launch, preserving same pinned
image, task, model-free nop/oracle arms, resource gates and zero retries. New
output environment-controls-004; caffeinate-started supervisor PID6859 is live,
image-pull invocation recorded. Log artifacts/pro-controls-queue-004.log.
No model inference authorized by this supervisor; do not duplicate it. Inspect
actual pull/control results next. Pipeline005 has NOT been registered/launched;
first require official nop0/oracle1 summary, then real boundary/meter/replay
gates before any scored block. Old003/004 outputs must remain immutable.

## Heartbeat 29 October22:30 UTC: control004 image pull failed before controls

Read AGENTS/latest handover and inspected real supervisor PID6859: exited.
Host free34GiB. Actual image-pull stdout reports Docker Desktop internal
registry/access IPC backend.sock timeout. stopped.json preserves pull exit1;
no official nop/oracle invocation or job, no model inference.

Read root-cause skill and checked actual Docker service. Initial read-only
version query hung; terminated only our diagnostic client PIDs35330/35331.
Fresh bounded10s query returned server20.10.23 successfully, receipt
environment-controls-004/daemon-diagnostic.json. Docker daemon was NOT restarted;
user containers/volumes/auth preserved. This establishes recovered daemon
query availability, not registry pull success. Preserve004 failure; any new
staging continuation needs fresh protocol005/output005, verify original source
hashes and absence of model/control execution, then pinned pull again. No
pipeline005 or scored model trial launched.

## Heartbeat 29 October23:00 UTC: fresh model-free staging continuation

Read AGENTS/latest handover, inspected real processes (no prior supervisor),
complete33-assignment audit and closed004 output. No nop/oracle invocation or
job exists in004; pull failure retained. Docker version returned20.10.23 within
bounded10s query; free36GiB exceeds18GiB preparation gate.

Verified all original control source hashes. Registered control-protocol-005
before launch; new output environment-controls-005, supervisor PID71910,
log artifacts/pro-controls-queue-005.log. Same pinned image/task and nop/oracle
only, zero model calls authorized, zero automatic retries. Do not duplicate
this active supervisor. Inspect pull and native control outputs next; pipeline
and scored inference remain unlaunched until required gates pass.

## Heartbeat 29 October23:30 UTC: repeat Docker registry IPC blocker

Read AGENTS/latest handover and inspected actual PID71910 (exited), pull stdout
and stopped receipt. Control005 failed at same Docker Desktop internal
http://ipc/registry/access backend.sock timeout as004. Free35GiB; capacity no
longer blocks, Docker registry IPC does. No nop/oracle jobs or model calls.
Preserve005 evidence. Do not repeatedly launch new identical staging attempts
based solely on docker version responding: it does not test registry IPC.

Docker Desktop service recovery is required before another pinned pull. Do not
restart shared daemon while user CI/database containers may be active. User
notified of concrete blocker and need to recover Docker Desktop when safe.
No paid service, daemon restart, volume deletion or scored inference performed.
Heartbeat remains enabled for external recovery; keep unchanged checks quiet.


## 31 October: subset-first prompt iteration and failure diagnosis

User requests larger dataset with multiple prompts, debugging routing on subsets
before full evaluation, with 95% of matched Sol accuracy as the progression gate.
Continuation registration: experiments/swe-pro-prompt-001/continuation-20261031.json.
Retain 12 development / 24 untouched Pro validation tasks, four matched arms,
and first-block controls/boundary/metering/replay gates. Do not repeatedly tune
on validation; use fresh reservation after any validation-informed update.

Inspected exact sklearn25747 assisted patch, effective prompt, journal and grade.
The v2 fallback prompt WAS injected; two expert calls were allowed. Luna completed
after one turn with zero calls and reported passing tests. Its patch preserves
DataFrame index only for unequal row counts; official keep-index regression fails
without infrastructure failure. This is an incomplete semantic fix and false
completion; full tool outputs are missing, so ignored visible failure is unproven.
Preserve visible outputs and pre-handoff grades in the new development diagnostic.

User explicitly approved Docker Desktop restart. Normal quit left old backend;
termination/relaunch produced fresh frontend/backend/VM processes, preserving disk
and volumes. Daemon still reports missing docker.raw.sock; VM startup not ready.
No new model/control jobs or identical pinned pulls launched. All 18 prior control
source hashes match. Resolve VM startup before fresh versioned controls; prior
failed outputs remain immutable. No new quality or cost result this continuation.


## 31 October: autonomous three-arm subset queued

Latest user explicitly prioritizes voluntary router failure detection and switching
against Luna-only and Sol-only controls. Docker recovered after authorized restart:
docker ps succeeds, no active containers at preflight, version20.10.23. Fresh model-free
control006 supervisor PID60801 is downloading pinned Pro image successfully; no
registry IPC failure so far. Do not duplicate it. Protocol control-protocol-006.json.

Registered pro-pipeline-protocol-005.json before any new model invocation. Supervisor
PID64600, output results/swe-pro-prompt-001/router-subset-005, log artifacts/pro-router-subset-005.log.
Waits for control006 nop0/oracle1, then real actor/native handoff and pristine witness
replay, then exactly three scored arms: large, optional, small. Required-review omitted
from scored comparison; setup handoff is disclosed separately. Existing v3 prompt
is baseline candidate; no forced consultation, no policy changes during block.
Host visible tool traces and sealed pre-handoff/final patches support failure
recognition, switching and integration audit. No scored result yet.

Generalized paired metrics to explicitly registered three- or four-arm blocks;
missing/duplicate assignments rejected. 14 policy/metrics checks and25 checks in
real Harbor runtime pass. Diff check passes. No automatic retries or full dataset
expansion. After this block review actual grades/tokens/runtime/visible observations
before next development subset/prompt. Preserve24 validation tasks untouched.
Generation/pipeline source hashes in protocol005 now frozen while supervisor live.


## 31 October: router-only failure detection, checked independent attempts

Latest steering replaces matched comparisons with Luna voluntary router development
on varied tasks, inspecting failures and improving prompt between units. No new
standalone Luna/Sol calls. Three-arm queue005 stopped before calls when control006
failed Harbor daemon preflight (image DID pull successfully). Docker info now passes
in default and task-local config. Model-free control007 PID72819 is executing nop
then oracle; preserve it, no duplicate jobs.

Router-only queue006 was deliberately terminated while only queue.json existed;
stopped receipt records zero invocations. User then added default2–3 meaningful
independent repair attempts, checked after each, before consulting Sol. Promptv4
records concise observable evidence/action decisions, discriminating verification,
early-help exceptions with concrete reason, and preserves integration time.
New backend ttgl.router_development:RouterDevelopmentCodex preserves unchangedv3
treatments.17 policy/routing/metrics checks pass in real Harbor runtime.

Active router-only protocol pro-pipeline-protocol-007.json, PID77215, output
results/swe-pro-prompt-001/router-development-007, log artifacts/pro-router-development-007.log.
It waits for control007, performs separate setup boundary/native/replay preflight,
then ONE optional/router assignment on first Pro development task. No matched
comparison/accuracy-retention claim from this unit. All registered source frozen
while active. Inspect results/visible host traces, classify failure, then register
next task/prompt; do not repeat uncertain inference or use validation for tuning.

Actual archived failure audit: results/router-failure-audit-20261031/failures.json.
Of three heldout router failures, sklearn25747 and django10999 had zero expert
requests and complete responses claiming passing tests; sphinx11510 had two
completed consultations and still failed. Missing old tool outputs stay unknown.
Future failure categories: no-call false completion; no-call acknowledged blockage;
request without completed consultation; failure after completed consultation.
Do not substitute self-reported checks or private reasoning for visible evidence.


## 31 October: handoff continuity amendment before inference

User adds context/attempts/lessons transfer to Sol to avoid repeated work. While
queue007 had only queue.json, terminated supervisor77215 and preserved zero-call
stopped receipt. Added compact explicit handoff checklist to routerv4: goal,
criteria, source/candidate, distinct attempts and hypotheses, checks/results,
lessons, ruled-out explanations, unknowns and focused question; request no repeats
without new evidence. Context-only Sol remains bounded; Luna verifies integration.
Active replacement protocol008, PID80720, output router-development-008,
log artifacts/pro-router-development-008.log. Source frozen while active.
Control007 nop passed, oracle executing; do not duplicate. No scored calls yet.

## 31 October18:03 UTC: replay gate root cause repaired without inference

Control007 completed official nop0/oracle1. Supervisor008 exited after completed
native setup (two expert consultations) and fresh witness replay; no scored
router assignment started. Both setup/native and pristine grades0, apply_rc0,
exact witness path successfully applied. Gate incorrectly searched diffstat,
which excludes new untracked files. Changed gate to require exact successful
`git apply --verbose` path line plus apply_rc0 and both negative grades. Eight
pipeline tests pass in Harbor runtime; archived actual replay passes offline.
Receipt replay-gate-audit-001.json. Old008 evidence remains unchanged.

Next continuation MUST reuse completed setup/replay after auditing original
source bindings, sealed patch hashes and metering; register a fresh output and
explicit reuse path before the ONE unstarted router assignment. Do not restart
008 or rerun its setup model calls. No scored result or retained-accuracy claim.


## 31 October: managed-host continuation audit

Fetched active work at a43c9e7; preserved older host changes separately on
`handover-host-20261031`. No model calls launched. Original private task root,
private records root, controls007 summary and raw setup008 are absent here;
0/42 original absolute source bindings exist on this Linux host. Codex state
remains non-writable. Receipt: `results/host-continuation-20261031/readiness.json`.
Connect the original desktop or transfer sealed research evidence to a writable
Codex host before validated setup reuse. Do not rerun completed setup calls.

## Active continuation preparation: setup008 reuse on original Mac

The current user requested exactly one unstarted router assignment. This chat owns
continuation009 preparation; no other supervisor should launch it. Raw setup008,
controls007 and all42 registered source paths are present on this original Mac.
No transfer/credential copying is needed. No research workers were live at audit.
The old heartbeat chat is idle; its scheduled runs must inspect this entry and
avoid duplicate work. New pipeline uses a per-task OS lock and an exclusive
assignment claim before a scored invocation. Setup reuse audit/tests are being
completed before registration/launch. Do not edit generation sources or launch
another setup or scored attempt while this continuation is active.


## Continuation010 launched: reuse008, one unstarted router assignment

Protocol010 is frozen; supervisor PID18187, log artifacts/pro-router-development-010.log,
output results/swe-pro-prompt-001/router-development-010. Exactly one optional router
assignment authorized; no new setup inference. Explicit setup reuse audits60 pinned
artifacts, native controls, sealed final/pre-handoff patches, actual witness replay,
original source bindings with archived amended files and cumulative-thread deltas.
39 reuse/pipeline/boundary/router checks pass; real raw reuse audit passes.
Actor runs a fresh model-free boundary check before inference. Per-task flock
and exclusive assignment claim prevent concurrent or repeated starts. Do not
change frozen generation sources or launch another supervisor. Latest user asks
to continue through this assignment, independent grading, analysis and documentation.
Original Mac private evidence exists; no migration/credential transfer needed.
Codex ChatGPT login and supported model/list confirm both requested model IDs;
Docker healthy,56GiB free. Fastest Atlassian connector now authenticated; sync
publication is authorized by latest user, superseding older no-publication note.


## Continuation010 complete: one Pro success without consultation

Exactly ONE unstarted voluntary router assignment ran; initial official grade1
and independent pristine replay grade1. Supervisor18187 exited normally; no
additional assignment is authorized by protocol010. Never restart010 or remove
its assignment claim. Setup008 was audited/reused, with zero repeated setup
model calls. All24 reserved validation tasks remain untouched; no standalone
comparisons, second task, training or full evaluation launched.

Evidence and deterministic no-inference analyzer:
results/router-development-010-analysis/README.md and summary.json;
scripts/analyze_router_episode.py. Exact native/sealed patch/replay provenance
and cumulative-thread deltas reconcile.39 pre-run reuse/pipeline/boundary/router
checks and2 analysis cost/latency checks pass. Raw setup/private evidence exists
on this original Mac; no migration transfer or credential copying was needed.

New episode:333186 input including301184 cached,2402 output including reasoning;
one outer controller invocation, zero Sol requests/completed consultations.
Frozen published-rate scenario USD0.00741304 per assigned/resolved task.
Request elapsed39.73s, actor phase54.15s, generation through fresh grade203.51s.
Historic setup usage112615 input/1631 output and scenarioUSD0.03098282 remain
separate; no new setup inference. Invoices, quota saving, matched-Sol saving
and accuracy retention unknown. One selected public dev task does not prove
95/95 or generalization; original141 Verified assignments remain unchanged.

12 visible shell requests show lint correction and successful final lint/diff
checks, no endpoint tests. Luna explicitly acknowledged incomplete runtime
verification and chose complete. Since independent grade passes, do NOT label
this a false-success claim or missed failure/escalation. No functional failure
opportunities or handoffs were observed; failure-detection recall and expert
integration quality cannot be estimated. Default2–3 checked repairs applies
before help, not forced extra edits after every candidate.

Prepared UNRUN v5 completion-evidence addition and candidate registration;
no demonstrated improvement, no backend wired or next-task invocation. Next
research unit requires a separate development-task/protocol/source freeze;
keep validation sealed and preserve all existing attempts. While this chat
finishes publication, heartbeat/other chats must not launch extra inference.

Paper Markdown/HTML, current result chapter and practical project guide updated.
PDF/Word deliberately remain older, unchanged working previews; their old QA
receipts apply only to those binaries. text-update-010.json records current
text hashes and unchanged binary hashes. No new full visual-QA claim.
Fastest connector is authenticated: FAST-95 completed and Confluence page19103748
published/read back. Current-user publication authorization supersedes the old
heartbeat prohibition. No architecture novelty or proven economic gain claimed.

## Router iteration series authorized by latest user

The user now explicitly requests continued Luna-router trials and prompt
improvement based on observed failures and delegation behavior. This supersedes
the previous one-assignment cap for future separately registered units, not for
retries of completed work. This chat owns a new three-task development series:
next reserved Ansible, Element Web and Tutanota tasks, in original reservation
order, one attempt each and no replacements. Plan:
experiments/router-iterations-20261031/plan.json. No validation or standalone
comparison authorized. Other heartbeat/chats must not duplicate these units.

V5 completion-evidence backend is implemented separately from v4. Per-target
empty/reference controls must pass; only original setup008 transport/metering
is reusable across tasks. Original task grade/image is never reused as target
readiness. A fresh actor boundary check precedes inference on each task. New
cross-task reuse and v5 checks pass (31 focused tests). No new scored call yet.

Current preparation note: Docker CLI manifest inspect reported no manifest for
Ansible before any image pull/control/model call. Auditing registry HTTP metadata
and content digests directly to distinguish CLI behavior from actual image
availability. Preserve any preparation failure; do not substitute favorable tasks.
No active research supervisor or new scored assignment yet.


## Router series checkpoint: Ansible complete, Element controls active

Ansible controls011 passed0/1. Router012 (PID55711, now complete) used v5 and
passed initial/fresh official grading without Sol. Scenario costUSD0.00551832.
Actual trace confirms3 selected public tests passed and a corrected traversal/
root-extraction reproducer passed; no inference of failure-detection recall or
causal prompt improvement. Decision audit and exact evidence under
results/router-iterations-20261031/ansible-analysis-012. No model retries.

Element controls013 supervisorPID60278 is pulling/preparing its pinned image;
no Element model started yet. Tutanota not launched. Current chat retains
exclusive series ownership; do not duplicate workers. Existing heartbeat was
updated through the app to router-only focus and monitor-only while owner active.
FAST-96 tracks this series. Each model unit is separately registered only after
its own controls pass; source freezes and immutable assignment claims remain.


## Element router014 launched after valid controls

Element controls013 completed with nop0/oracle1 and no exceptions. Registered
router014 and audited cross-task reuse; supervisorPID47357 owns exactly one
new assignment, zero setup calls. Do not duplicate or edit frozen model sources.
V5 retained after Ansible success; no causal improvement claim. Tutanota remains
unlaunched until this unit is audited. Current chat retains ownership.


## Element complete; v6 registered; Tutanota controls active

Element014 initial/fresh1, no Sol; full native/thread/patch audit complete. Scenario
USD0.01017514. Old-contract Jest suite fails, broad tsc exits137, Luna explicitly
acknowledges incomplete behavioral verification. Not false success on passing
candidate; no failure-detection recall or handoff evidence. Analysis at
results/router-iterations-20261031/element-analysis-014.

V6 registered separately in v6-activation.json: obsolete old assertions need a
new-contract executable check; continue useful bounded work before honest but
unsupported completion, or ask focused Sol test-design help after useful attempts.
Two optional-backend tests pass. No forced review or demonstrated causal gain.
Tutanota model-free controls015 supervisorPID15384 active. Router016 not launched.
Use RouterContractCodex only after its own controls pass; source hashes must include
new module/prompt/test/activation. Current chat retains ownership; no duplicate work.


## Explicit user constraint: general-purpose router

User warns against benchmark-overfit prompts. Added router-generality.md and
AGENTS constraint. V6 has no repository/case-specific rules; added task-appropriate
verification and old/current requirements principle before any v6 invocation,
updated activation hashes. Benchmark development diagnoses mechanisms; no transfer
or causal gain claim without separately registered diverse fresh evaluation.
Controls015 source unaffected; no model repeat or reserved validation access.


## Tutanota router016 active

Controls015 passed nop0/oracle1, no exceptions. Fresh router016 registered
with RouterContractCodex v6 and all new module/prompt/test/activation hashes.
SupervisorPID50975, single claim, zero new setup calls. Frozen sources must not
change; no duplicate inference. Generality constraint committed at8317da1,
mechanism/falsification review atcda3afb. Confluence checkpoint19202180 published
and read back; FAST-96 remains In Progress. Current chat owns until final audit.


## FINAL October31 router series audit; owner release after commit/push

All3 registered assignments complete, no retries/new setup inference. Ansible012
v5 initial/fresh1, no Sol; Element014 v5 initial/fresh1, no Sol; Tutanota016 v6
initial/fresh1 after1 completed voluntary Sol call, and pre-handoff1. No observed
rescue, regression, causal benefit or failed integration. Series model scenario
USD0.14409084 (mean0.04803028), not invoice/quota or matched-Sol saving.
Tutanota input7309359 incl cached7160448, output30311;2 Luna outer controller
requests+1 Sol expert. Validated cumulative-thread deltas and sealed patches.
Model+tool1552.76s, actor1568.77s, generation start to fresh grade2444.80s; later
pre-handoff replay separate. Exact raw grades/token/patch evidence in analysis
exports with artifact manifests and series summary. All24 validation untouched.

Luna repaired local compiler errors, voluntarily consulted about correctness and
test design, integrated changes and added tests. Behavioral tests remain unrun:
compile137, native dependency DNS failure. Final completion explicitly incomplete.
Detailed handoff omitted full relevant branch source; Sol explicitly limits its
side-effect conclusion. Do not infer Sol failure, false completion or missed
escalation from this passing episode. No failure-detection recall estimate.

User explicitly requires general-purpose routing, not benchmark-overfit prompts.
Read router-generality.md. V6 frozen before Tutanota, no repository/case triggers;
retain it for varied fresh diagnostics instead of adding a case-specific patch.
No transfer/causal improvement claim from changed development cases. Future
transfer evaluation needs separately registered diverse tasks with frozen policy.

Paper Markdown/HTML and practical guide updated; PDF/Word unchanged older previews.
FAST-96 Done, Confluence19202180 updated/read back. Existing heartbeat
continue-luna-sol-routing-research updated, ACTIVE30min, no duplicate automation.
This chat releases ownership of the completed three-task series after final
commit/push. No active router/control supervisor remains. Next heartbeat may
continue only a separately registered ONE-task unit from remaining development
reservations in original order after checking current liveness/claims/ownership.
Keep v6, own target controls/boundary, audited setup reuse, zero retries; no
standalone/full evaluation or validation expansion. Preserve all raw untracked
results and host sealed records. Do not overwrite completed outputs or claims.

## Heartbeat21:04 UTC: next one-task Teleport development unit registered

Read AGENTS/generality/latest owner release, inspected actual processes and
immutable claims. Prior series committed/pushed d80f49b; no research workers live.
Next original reserved development index4 is Teleport, no replacement. Registered
experiments/router-teleport-20261031/plan.json, cap ONE v6 router assignment,
zero validation/standalone/retries. Heartbeat owns this unit through audit.

Anonymous registry manifest/config digest validated amd64/Linux; pinned digest
faed731d68feab39528cf63606de71210eb2eadd9369c4ad738e28f880724940,
compressed layers2640191103 bytes (not unpacked size). Model-free controls017
supervisorPID95296, results/router-teleport-20261031/teleport-controls-017,
log artifacts/router-series-teleport-controls-017.log. No model registered or
started. Preserve this worker. After own nop0/oracle1, separately register018
with frozen v6, explicit cross-task transport-only setup008 reuse, all source
bindings and fresh actor boundary. Do not reuse another task's readiness.


## User disables scheduled monitoring; this chat continues Teleport

Latest user explicitly says continue but disable monitoring. Existing heartbeat
continue-luna-sol-routing-research is PAUSED through the app (confirmed). Do not
resume it or create a replacement schedule without new user instruction. Prior
heartbeat turn ended after launching controls017; this chat now owns the already
registered Teleport unit. Preserve supervisorPID95296, no duplicate controls.
Continue exactly one018 router assignment only after own controls pass, using
frozen general-purpose v6 and validated setup008 transport-only reuse.


## Teleport018 launched in active chat, monitoring disabled

Controls017 pass0/1. Native cross-task transport-only setup008 reuse audit passed,
zero new setup calls. Protocol teleport-router-018.json freezes general v6 and
all target/private/control/source hashes. SupervisorPID3271, claim unique; exactly
one router assignment. FAST-97 In Progress. Current chat owns through final audit.
Heartbeat PAUSED by user, do not resume. No retries or other units concurrently.


## Teleport018 COMPLETE; scheduled monitoring remains disabled

Initial/fresh official grades1, zero Sol,4 visible shell requests. Own controls017
pass0/1, fresh boundary passed, setup008 reuse audited, zero new setup/model
retries. Cost scenarioUSD0.00427448; input110481 (cached90368), output2719.
Request+tools34.27s, actor50.16s, start-to-fresh233.84s. Actual cash/quota and
matched-Sol savings unknown. Evidence export with artifact hashes at
results/router-teleport-20261031/teleport-analysis-018.

Actor made one new queue candidate, attempted gofmt/go test (not found on PATH),
then acknowledged incomplete compile/behavioral verification. git diff --check
does not inspect the untracked new file, but authoritative sealed patch includes
it and replay passes. No observed false completion, missed escalation, failed
consultation or integration. No failure-detection recall/transfer claim. Keep
public verification runtime readiness distinct from evaluator readiness. Do not
add a task-specific prompt patch or infer lack of tool alone warrants Sol.

This one-task unit is complete; no live supervisor or new pending model assignment.
Current chat ownership ends after final evidence commit/push. User explicitly
disabled scheduled monitoring: continue-luna-sol-routing-research is PAUSED,
confirmed by app and on-disk status; no other TTGL monitor found. Do not resume
or replace it without new user instruction. Future authorized active-chat work
requires a new registered unit, remaining development order, frozen v6, own
controls/boundary, evidence-validated reuse, no retries/validation/standalone run.
FAST-97 records completion; Confluence19202180 gets a separate follow-up section.
Preserve all raw untracked result directories and host records.


## Next active-chat Vuls unit registered

Latest user says continue. No live prior supervisor and monitor remains PAUSED.
Next original development index5 future-architect/vuls registered, cap one v6
router assignment, no replacement/validation/standalone/retries. Plan and
measurement intent under experiments/router-vuls-20261031. Preparation inventory
and receipt hashes verified; pinned image digest1aee15022a4e086e0d7929ed1046bddb922b4382f9f0a39645fd01d821ae2287.
Model-free controls019 supervisorPID24340 active, router020 not yet registered.
Current chat owns this unit; do not duplicate or enable monitoring. Own controls,
readiness evidence, validated cross-task setup008 reuse and fresh boundary required.
