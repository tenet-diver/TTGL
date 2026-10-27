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
