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


## Vuls020 launched with frozen v6; Go available in image

Controls019 pass0/1, no exceptions. Model-free readonly/no-network public runtime
probe finds go/gofmt at/usr/local/go/bin; unlike Teleport, image has the expected
tools. No model/environment mutation from probe. Runtime evidence under
results/router-vuls-20261031/public-runtime-probe.json. Registered router020,
validated setup008 cross-task transport-only reuse (zero new setup calls),
supervisorPID31913. Claim unique, max one assignment/no retries. Current chat
owns; monitoring PAUSED; sources frozen through grading. FAST-98 In Progress.


## Vuls020 COMPLETE; early delegation and shell PATH defect separated

Initial/fresh1 after1 completed Sol consultation; pre-handoff0 but snapshot is
ONLY go.mod version bump. Expert packet explicitly says no main edits/checks.
No concrete early-help exception: premature delegation relative to user's
2–3 useful checked attempts. Do not call this rescue of a substantive repair.
Final implementation passes, no behavioral tests added; explicit verification
incomplete. Export under results/router-vuls-20261031/vuls-analysis-020.
Input1070045 (cached996864), output8300; scenarioUSD0.04838064, not invoice/quota
or matched-Sol saving. Request+tools115.87s, actor125.26s, start-to-fresh322.98s;
host busy/uncontrolled, no speedup or transfer claim.24 validation untouched.

After ALL grading, real-image regression reproduced bridge bash -lc replacing
image toolchain PATH. Changed extra shell to bash -c, matching Harbor semantics.
Go now executes; same model-free comparison confirms Teleport image also has Go.
This corrects verification opportunity, not prompt policy or model competence.
10 focused runtime/transport/isolation/router tests and27 reuse/pipeline tests
pass. Original bridge and supervisor archived with hashes matching frozen020.
No completed model/setup call repeated. General v6 unchanged.

CRITICAL for next unit: old native setup does not validate changed transport.
Merge experiments/router-vuls-20261031/transport-amendment.json with existing
reuse metadata, preserving original script/router amendments. Gate now requires
bridge archive, before/after source hashes, bound validation receipt, actual
test source and raw regression outputs. Unbound/failed/stale proof refuses
reuse. Actual amended setup_stage audit on real records passed with0 new calls;
its stored protocol cap0 is model-free AUDIT ONLY, not an inference registration.
Each future target still needs own controls/image/boundary and source freeze.
Disclose corrected transport as changed condition; do not attribute any future
outcome difference to unchanged v6. Never rerun setup as fallback.

Current unit complete; no active supervisor/next assignment. FAST-98 tracks
completion. Scheduled monitoring remains PAUSED by user, no replacement. Future
active-chat continuation requires next original development reservation/new cap.
Preserve all raw untracked logs, sealed records and archived transport evidence.


## New target90/no-quality-drop active research objective

User says keep going until90% cost reduction with no quality drop. Active chat
objective created; monitor remains PAUSED. Default interpretation communicated:
>=90% all-role published-rate inference scenario reduction, observed held-out
resolution count >= matched Sol; not invoice/quota or population equivalence.
Async optional question pending about statistical noninferiority; development
continues without touching held-out tasks. Prior95/95 failure evidence immutable.

Registered target90-development-20261031/plan.json covers remaining original
index6..11 tasks, in order, two arms large/optional,12 assignments cap, zero
validation inference, no replacements/retries/favorable stopping. First candidate
v7 consolidates common verification for both arms and voluntary routing separately,
without stacking older prompt versions. No task-specific triggers; activation
record has mechanism/risks. Matched Sol is required by new target and supersedes
prior standalone deferral only for new paired units. Corrected transport shared.

Flipt controls021 supervisorPID62576 active; no scored v7 model call registered
yet. Current chat owns this development plan. New pair runner validates two
distinct immutable claims, source freeze and all-role cumulative deltas. Next
register022 only after own controls pass, test v7/pair wiring and validate amended
setup008 reuse. No new setup calls. Existing raw histories preserved.


## Target90 first matched pair022 ACTIVE, source freeze

Flipt controls021 pass0/1. Paired022 registered, Sol-only first then optional Luna,
shared consolidated v7 common policy and corrected transport, independent threads/
containers/actor boundary. SupervisorPID37864. Both native inference and pre/final
replay owned by this chat, distinct immutable per-arm claims. Setup008 amended
reuse audited0 new model calls. Source freeze includes v7 module/prompts/tests,
runner, target/control/activation metadata. DO NOT edit those files while active.
No duplicate workers or reruns; no held-out task access. Monitoring PAUSED.
Software48 focused tests pass before v7 inference. Target90 plan committed619925f.
After pair completion independently audit both arms/costs/quality, then next
original development reservation index7; no favorable subset stopping.


## Target90 Flipt022 audited; Navidrome controls023 ACTIVE

Both native/fresh grades1; Luna0 expert requests/consultations. Validated
cumulative-thread usage and sealed replay joins; Sol scenarioUSD0.1233776 vs
router0.00947576,92.3197% saving. One development pair only, no target proof.
Both experienced visible exit137 checks; both achieved focused package passes,
Luna serial Go test pass and diff check. Luna accurately disclosed the137 and
limited scope; no observed false completion/missed escalation on this case.
No delegation-success claim from a zero-consult episode. Keep v7 unchanged.
Analysis results/target90-development-20261031/flipt-analysis-022, progress.json
tracks all six fixed tasks and no favorable subset gate. Pair supervisor done.
Navidrome model-free controls023 PID55144 active; own image digest bound.
Next register pair024 ONLY after controls pass; router first by preregistered
counterbalance. Setup008 amended reuse only, zero new setup calls. Monitoring
PAUSED; active chat owns plan;24 validation untouched. Preserve raw host records.


## Target90 Navidrome024 ACTIVE

Own controls023 pass nop0/oracle1,0 model calls. Pair024 PID63897 launched
with optional Luna first then matched Sol by preregistered counterbalance.
Setup008 amended reuse independently audited0 new setup calls. Freeze bound
generation/policy/transport/source metadata until BOTH arms and replays finish.
Keep v7 unchanged; no task-specific tuning after Flipt pass.1/6 pairs audited.
Confluence19103791 published/read back, FAST-99 In Progress. Monitoring PAUSED.
Next after full024 audit: original index8 Protonmail controls025/pair026, not yet
registered. Disk last17GiB free, next pull guard18GiB; inspect unused OWNED completed
Pro image caches only if necessary, preserve all raw/sealed evidence and user
CI/database volumes. No global prune. Validation24 untouched.


## Navidrome024 DISK STOP; evidence-validated continuation ACTIVE

Original supervisor63897 stopped before first-block-optional-fresh (no invocation
marker/job). Luna native generation/grading completed, sealed patch and positive
cumulative-thread metering independently audited. Large claim/invocation absent.
DO NOT rerun continue_pro_rescue.py. Original stopped.json and evidence preserved.
New scripts/continue_target90_partial.py has exclusive recovery marker, same task
flock, source/image/inventory checks, rejects ambiguous/started jobs and never
repeats inference.11 focused recovery/pair/summary tests pass. New registration
navidrome-recovery-024.json binds original protocol/queue/stop/native/seal/usage,
permits only unstarted Luna-fresh and Sol generation/fresh. PID73633 ACTIVE, log
artifacts/target90-navidrome-024-recovery.log. No setup calls or Luna repeats.
Original generation sources unchanged/frozen until both arms/replays complete.
Reclaimed unused completed OWNED Flipt and Vuls image caches after checking no
container references, preserved raw/sealed/transport proof and pinned digests.
Receipts under target90 results; no global prune/volume/user-CI deletion.
Actual pair disk_guard is12GiB; preparation pull uses extra6GiB margin, separate.
Next after full audit unchanged Protonmail original index8;24 validation untouched.
Monitoring PAUSED; active chat owns continued target90 development.


## Target90 Navidrome024 complete/audited; Protonmail025 controls ACTIVE

Partial continuation73633 completed only unstarted replay and Sol, no repeated
Luna/setup inference. Original disk stop preserved, recovery bound to protocol
and raw artifacts. Initial/fresh grades1 both arms. Luna0 expert requests; scenario
USD0.0086526 vs Sol0.172766,94.9917% saving. Complete independent audit joins
seals/grades/native metering/cumulative deltas/boundary and fixed v7 commonpolicy.
Across2/6 pairs Sol2/2/router2/2 and aggregate ratio-of-costs saving93.8785%; not
held-out target proof, no escalation-benefit evidence from zero-consult cases.
Protonmail original index8 model-free controls025 PID79408 active, pinned public
image compressed5.78GB so watch disk during pull. Pair026 only after own controls
pass; same v7 and Sol first. No task-specific policy amendment. Validation24
untouched. Monitoring PAUSED, active chat owns series, next held-out separately
registered only after candidate selection/freeze. Do not rerun completed units.


## Protonmail025 prejob control failure; model-free recovery ACTIVE

Image pull complete pinned,11.66GB unpacked. Original025 nop invocation failed
at Harbor official Docker readiness (generic message conflates called-process
error and10second timeout), before jobs directory/native task/container creation.
Zero model calls, no completed/uncertain task execution. Current default and
task-config Docker info pass, official DetachedNetworkDocker.preflight passes
in1.48s. No daemon restart required or claimed. Preserve stopped/output markers.
Evidence-bound protocol protonmail-control-025-recovery.json registered; supervisor
PID87526 runs ONLY never-started nop/oracle in separate controls025-recovery
output, explicitly resolves cached image digest using unchanged controls script.
Proof results/target90-development-20261031/protonmail-preflight-recovery-proof.json.
Pair026 unregistered; require recovered own controls pass, then register_pair
helper with controls_override absolute recovered summary path. Helper now accepts
this explicit path and uses its sibling image-binding. Do not fabricate a summary
in the stopped original directory. Corrected Sol Navidrome cost USD0.172766.
Unused completed Navidrome cache removed after artifact-manifest validation.
24 validation tasks untouched, monitoringPAUSED, active-chat owner continues.


## Protonmail026 matched pair ACTIVE

Recovered own controls025 pass nop0/oracle1,0 model calls. Pair026 PID96569
registered against recovered summary and native results, source-bound; Sol first
then voluntary Luna by counterbalance. Same general v7, corrected transport,
fresh actor boundary both arms. Setup008 transport/metering reuse audit0 newcalls.
Protocol experiments/target90-development-20261031/protonmail-pair-026.json;
log artifacts/target90-protonmail-026.log. Source freeze until BOTH arms and
pre/final replays finish. Do not modify bound generation, prompts or metadata.
Current2/6 audited pairs unchanged; next original index9 Openlibrary027/028
only after full026 audit. Preserve stopped original025 prejob failure separately,
no native control or model repeat.24 validation untouched, monitoringPAUSED.


## Protonmail026 audited FAILURE; Openlibrary027 controls ACTIVE, v8 registered

026 complete both initial/fresh: Sol1, Luna0,0 expert requests. Sol scenario
USD0.4970548; routerUSD0.01136196 (per-resolved router null). Across first3 v7
pairs Sol3/3 router2/3,96.2821% aggregate saving BUT QUALITY LOSS; target NOT met.
Full native/delta/seal/replay audit in protonmail-analysis-026. Failure-audit-026
classifies acknowledged-unverified completion without escalation, not false claim
that checks passed, failed consultation or failed integration. Sol-only success
does not prove advice would rescue. No scored experiment rerun. Raw Jest1fail/
2pass; output parser folds names, do not infer2 functional failures from names.
Offline specific defect is a duplicate loading marker across wrapper/child. Keep
hidden assertions private, never feed this fix/example into routing prompts.

V8 completion_review_router.py/new common/routing prompts registered separately;
62 focused checks pass (raw artifacts/target90-v8-software-checks.txt). No v8
model calls yet. General mechanism: an honest admission of uncertainty does not
resolve material acceptance gaps; useful bounded attempts then focused review
when source/check design can help, explicit early exception for blocked feedback
after a candidate, complete handoff and verified integration. No mandatory call
for adequate evidence, no task-specific rules. V7 sources/outputs immutable.
Amendment permits v8 on remaining original indices3..5, same task order/cap12,
no replacements/repeats/validation. Analyzer now accepts registered v7/v8 and
summary separates adaptive blocks; mixed aggregate cannot pass fixed-policy gate
or establish causal prompt improvement. Held-out evaluation separately frozen.

Openlibrary own model-free controls027 PID57098 active. Pair028 NOT registered;
only after controls pass and v8 source/software/activation commit, register_pair
('openlibrary',3,28,version='v8'). Helper updated explicit version whitelist/agent/
prompts/claims and binds8 activation/amendment/software; defaults7 for history.
Setup008 amended transport/metering reuse only0 newcalls. MonitoringPAUSED.
Next Qutebrowser029/030 then NodeBB031/032, same original reservations.


## First v8 Openlibrary028 ACTIVE, source freeze

Own controls027 pass0/1, first v8 pair028 PID62079 launched Luna thenSol.
Registered v8 source/prompts/test/activation/amendment/software hashes,62-test
receipt/raw log rechecked before launch, amended setup008 reuse0 newcalls.
Protocol experiments/target90-development-20261031/openlibrary-pair-028.json,
log artifacts/target90-openlibrary-028.log. DO NOT edit bound sources/metadata
while both arms, pre/final replays remain active. Own new v8 claims distinct.
Paper/docs/state files are not in pair source freeze, safe for evidence updates.
FAST-99 and Confluence19103791 now prominently record v7 QUALITY LOSS:3/3vs2/3,
96.2821% scenario saving does NOT meet no-quality-drop target. Mixed v7/v8
development must remain separate, not causal improvement/final-policy evidence.
Next only after full028 audit: Qutebrowser controls029/pair030(version8).
24 validation untouched, monitoringPAUSED. Preserve failed Protonmail records.


## V8 Openlibrary028 audited; Qutebrowser029 controls ACTIVE

Both initial/fresh grades1,0 expert requests. Luna focused vendor suite33pass
and separate runtime edge/cleanup checks pass; initial ad hoc fixture AttributeError
is corrected using missing product fields and rechecked. Final accurately records
the correction. Sol scenarioUSD0.1462204 vs routerUSD0.00731174,94.9995% saving
on one v8 selected task only; no consultation/rescue evidence or causal prompt
improvement. V7 quality loss remains Sol3/3 vs router2/3. Four of six adaptive
pairs completed; mixed cost saving96.0825% is not fixed-policy target proof.
Analysis openlibrary-analysis-028 independently audits8 mode/common identity,
usage/deltas/boundary/sealed replays. No duplicate or new setup calls.

Qutebrowser original index4 controls029 PID68491 active. Pair030 unregistered;
only after own controls pass, register_pair('qutebrowser',4,30,version='v8'),
Sol first. Keep v8 unchanged. Then original NodeBB031/032. No held-out access.
Completed unused Protonmail image reclaimed after full artifact-manifest check;
all raw/failed/sealed grading evidence preserved, receipts target90 results.
MonitoringPAUSED; active chat owns continuation toward target, not reached.


## Qutebrowser030 v8 matched pair ACTIVE

Own controls029 pass0/1. Pair030 PID72263, Sol then optionalLuna, v8 unchanged
from Openlibrary028. Source freeze covers new8 module/prompts/activation/software
and existing transport/setup/generation dependencies; do not edit while both
arms/pre/final replays active. Setup008 audited reuse0newcalls. Protocol/log
under target90 qutebrowser-pair-030 / artifacts/target90-qutebrowser-030.log.
After full audit, final original development NodeBB controls031/pair032(v8).
Keep all failed7 evidence, adaptive versions separate, validation24 untouched.
Official OpenAI docs check used skill source order; exact Luna/Sol IDs preserved,
no migration/pricing/auth changes. Current family guidance discusses Astra for
delegation; do not present that as measured Luna behavior. Bounded verification
and representative eval guidance consistent with existing study, not proof of
v8 efficacy. MonitoringPAUSED; current active chat owns continuation.


## Qutebrowser030 confirmed v8 FAILURE; v9 registered, NodeBB controls031 pass

030 both grades Sol1/router0,0 expert requests. Sol scenarioUSD0.3188324 vs
router0.00523228, failed-router cost/resolved null. V8 now Sol2/2/router1/2.
Across5 adaptive pairs Sol5/5/router3/5,96.6593% scenario saving but quality
loss; target NOT met. Native/delta/identity/seal/replay audit qutebrowser-analysis-030.
Visible decision: absent test path collects0, general completion-model6pass,
compilation/diff pass; explicitly says dedicated new-behavior tests not present
or run, then completes with no Sol. No failed consultation/integration occurred.
Do not rerun case or feed specific expected fixes/evaluator assertions to prompts.

V9 evidence_decision_router.py adds native controller output fields for
verification status, property/evidence scope, attempts, material gaps and
escalation reason. Applies same schema/common to Sol; only Luna gets routing.
Backend records full public decision, projects SAME action/question/context/
summary to unchanged personal harness, preserves all native usage/timing. It
never turns a gap/grade/exit into an automatic Sol call. Expert schema/read-only
permissions unchanged; extra fields not automatically forwarded, Luna must
include decisive evidence in handoff. Known usage retained even malformed
decision/audit-write errors. No additional inference calls from formatter,
extra output tokens counted. All7/8 sources/results immutable.
74 focused checks pass,2 v9-only-inapplicable skips; raw tracked under
results/target90-development-20261031/v9-software-validation/pytest.txt.
V9 activation/amendment/software frozen before any9 models. Analyzer supports
version9 and verifies full native evidence text/hash, unchanged projected
action, schema/request/policy identity and exports structured decisions.

NodeBB own controls031 passed0/1; pair032 not registered yet. Commit9 artifacts,
recheck receipt, register_pair('nodebb',5,32,version='v9'), Luna first. Cap12/
original tasks unchanged. One9 task cannot establish calibration/improvement;
additional fresh development may be needed before candidate selection, keep
validation24 untouched. MonitoringPAUSED; active chat owns goal, not achieved.


## Final original v9 NodeBB032 ACTIVE

Pair032 PID96563 registered source/software9 receipt rechecked, own controls031
pass0/1, Luna then Sol, setup008 reused0newcalls. Freeze all bound9/source/prompt/
software/activation/generation dependencies until both arms/pre/final replays
complete. Protocol nodebb-pair-032.json, log artifacts/target90-nodebb-032.log.
Early visible tool evidence: focused mocked controller behavior checks pass.
No task-quality/cost conclusion yet. Model must still choose its own action;
formatter records full evidence, projects unchanged action, no automaticSol.
Continue after full audit; don't treat one9 case as proven calibration or
causal improvement over7/8 different blocks.24 validation untouched.
Current Sol5/5 vs adaptive router3/5 remains targetNOTmet. MonitoringPAUSED.


## Original target90 six-pair development COMPLETE; target NOT MET

032 complete initial/fresh both1,0 experts; v9 enriched schema works live, all
action/projection/evidence hashes/policy IDs and cumulative metering reconcile.
Sol scenarioUSD0.1329696 vs router0.00798336,93.9961% saving on ONE9 case only.
Luna focused mocked checks pass; Redis integration0tests blocked; declares
incomplete/material gaps and EMPTY escalation reason yet completes, not a
proven calibrated escalation policy. No backend override or extra model calls.
Final original phase:12/12 assignments, Sol6/6 vs adaptive router4/6; total
model-rate scenariosUSD1.3912208 vs0.0500177,96.4048% saving BUT QUALITY LOSS.
Perassigned Sol0.23187013/router0.00833628; perresolved Sol0.23187013/router
0.012504425. All failed tasks retained. Different versions/task blocks cannot
prove prompt improvement:7=2/3vs3/3,8=1/2vs2/2,9=1/1vs1/1. No final target proof.
All supervisors complete; no active model/control assignment. MonitoringPAUSED.

Next active-chat work: hold9 fixed on a separately preregistered small fresh
development block before burning24 reserved validation cases. Use pinned642
metadata IDs only, exclude ALL original development+validation families and any
prior started Pro family, outcome-independent seeded repository-diverse choice.
Do not read validation task content/solutions/grades or rerun original failures.
Reuse existing official preparer/Harbor/controls/replay; separate newcap and
source freeze, same models/effort/budgets/rates. No full642 automatic run.
Currentgoal active, cost-only success insufficient. Preserve all failed7/8
results and9 evidence; update paper/guide/Jira/Confluence with complete phase.


## 4 November: measurement-first usage optimizer direction

The user supplied Codex Usage Optimizer v1.1 and prioritizes measuring existing usage before automating improvements. Read [usage-optimizer.md](usage-optimizer.md); track [FAST-102](https://fastestswarm.atlassian.net/browse/FAST-102). The original pack is retained at docs/handoffs/codex-usage-optimizer/ with checksums intact. First work is source discovery, versioned read-only import, accounting reconciliation and a real ordinary-usage baseline; then incremental analysis, review and bounded verified trials with durable history. Adoption is not a deployed collector or measured saving. Existing research results, frozen artifacts and validation reservations remain intact; no new benchmark or inference launch follows from the handoff. Monitoring remains paused.


## 4 November: local usage monitor started on explicit user request

Implemented tools/usage-monitor: ccusage20.0.48 session/daily accounting, SQLite tool metadata, custom local UI, stable review decisions, deterministic opportunities and agent-authored reviews. Actual private history import and UI navigation/evidence views were verified on this Mac; no private totals or histories are committed. User LaunchAgent local.ttgl.usage-monitor serves127.0.0.1:8766; data/app under ~/Library/Application Support/TTGL Usage Monitor. Installed personal ttgl-usage-monitor skill reads /api/agent-context. Five focused adapter/HTTP tests pass; source/coverage/reconciliation limitations remain visible. The user authorized this new local monitor; the older benchmark heartbeat remains paused. No optimization executor, paid background analysis or proven savings. See tool README for install/status/stop and exact supported scope.


## 4 November: start the OSS observability dashboard

On explicit user request, started Docker Desktop and the pinned official AI Observer0.6.0 amd64 image as ttgl-ai-observer, loopback8080, watch codex --backfill. Existing ccusage/TTGL report stays on8766. AI Observer lacks direct compressed-file support in this release: separate local expanded copies cover468 compressed histories, originals remain read-only. All expansion completed without errors. The source setup and helper are under tools/usage-monitor/observer; no private histories are tracked. AI Observer pricing/reconstruction is independent of ccusage and not actual billed charges. A sidebar link opens the OSS dashboard.


## 4 November: native OSS session observability

Langfuse now runs locally in six containers, replacing the stopped AI Observer usage-only pilot as the primary trace/session UI. The official verified Codex plugin imported two real sessions/four completed turns; the full historical aggregate report and reviewed suggestions remain in the TTGL companion. Live capture awaits restart and normal vendor-hook trust in Codex. Prefer existing OSS replay/tracing capabilities; do not build a custom trace viewer. See [deployment and security limits](../../tools/usage-monitor/langfuse/README.md). Dependency scans have residual and unscored findings; provenance does not establish absence of malicious code. No optimization executor, benchmark rerun, or heartbeat change was introduced.


## Broad Langfuse analytics continuation — 4 November

The user explicitly prioritizes where model tokens/cost and tool time go, then underlying tool names, broader history and summarized argument patterns. A standard-library, metadata-only OTLP bridge now reuses the existing native rollout reader and ccusage reports. Native Langfuse dashboards serve all views; no additional custom UI or dependency was added. The local analytics LaunchAgent refreshes every three minutes independently of Codex hooks and without inference. Daily and lifetime-session counter datasets are alternative views; never sum them. Native tool records omit parent wrappers when native children exist and preserve unknown timing. Argument-shape events are derived summaries, excluded from tool/time/token counts. No per-tool token estimate is produced.

Langfuse v4 immutable observations require positive counter increments and persistent delivery receipts; blindly updating the same IDs inflates metrics. Initial canary environments are retained but excluded from the production dashboard. Counter decreases and ambiguous delivery block replay until reconciliation. See tools/usage-monitor/langfuse/README.md and local private status files for current coverage and validation. Existing benchmark sources/evidence and paused research heartbeat remain unchanged.


## Native runtime audit — 4 November

Timing audit correction: `usage-tools` start/completion timestamps are lifecycle windows, not trustworthy execution latency. Timing widgets now use `usage-runtime-v2` from explicit native item.duration (secs/nanos), with shell command/action groups and separate outcomes. Unknown native durations are excluded. Completed operation stats show count/median/p95; investigate failure outliers separately. Mixed batches remain one shared runtime, and process runtime still is not agent-blocking or end-to-end task latency. Do not rank bottlenecks using the old monitor duration/lifecycle totals. Token and tool-frequency accounting is unchanged. See runtime_enrichment.py and the README audit examples.


## Runtime distribution preference — 4 November

Latest user choice: preserve outliers and use runtime distributions instead of filtering. Primary timing widgets show median by operation/outcome plus count, p50, p95, p99 and maximum. All outcomes stay included, grouped separately. No minimum-count cohort or individual clipping is applied; its temporary refresh is removed. Read quantiles alongside sample counts, especially for rare operations. Token/cost accounting is unchanged.

## 6 November: harness tools queue and rejected retrieval guidance

User authorized existing-tool research and bounded experiments. See
tools/usage-monitor/studies/harness-optimization-backlog.md and its JSON registry.
Normal Codex remains on the built-in provider after the preserved startup recovery;
capture/compression is opt-in. Do not infer global live compression from older text.
Schedules remain paused. Existing pre-turn source edits were preserved.

retrieval-guidance-001 is COMPLETE: three fresh public-source investigation pairs,
six native Sol sessions, all exact facts/source checks pass; native/CLI counts
reconcile. Neutral269570 vs scoped301326 tokens (+11.7802%), only1/3 pair wins:
registered gate FAIL, reject recorded. Output bytes28577->24125 but calls9->11;
extra31360 cached input/286 fresh/110 output. No cash/general coding-quality claim.
Never repeat/replace these runs. Evaluation7866ead9b08644889f34396949d68fa1,
proposal1f5732e17b4e452fa1d2a5024fa47c27 in TTGL Experiments.

Offline pre-registration audit:683 indexed tools matched,446 retained command
outputs/413 distinct; existing transforms change6 distinct,1925451->1742273 bytes.
Not measured model-token savings; opaque MCP bodies excluded, research mixed in.
RTK1.1.0 pinned753a3b0 release lock255 packages/251 registry queries has OSV
matches in8 package versions, including vulnerability and maintenance findings;
BLOCKED, no install/execution. CLI Apache2, engine BUSL additional-use restrictions.
Aider/LLMLingua remain uninstalled/unreviewed candidates. Metadata/security receipts
and all private trials under work/security/harness-optimization-20261106/.

Four next-step proposals saved (independent-read batching, security-blockedRTK,
Aider map, LLMLingua), none launched. No development winner yet. Next prefer
bounded batching tests with existing tools; freeze a separate fresh protocol first.
17:25UTC accounting lower bound: parent2358148+trials570896=2929044 native tokens;
parent active, no net first-use saving. No extra analyst model session spawned.
Six-cell identity/hash/type/accounting audit and4 existing compression checks pass.


## 7 November: active context/memory program; cost-aware selection

User explicitly authorizes all planned context/memory experiments using local
Codex with no spend/runtime ceiling, report publication in TTGL repo, and a
Markdown progress doc. Main entry:
`docs/research/context-memory-experiment-progress.md`; living scientific report:
`docs/paper/context-memory/report.md`. Commits8e3ac69/e477c0d are pushed to work.
Preserve the nine pre-existing modified observability files; they were not
included in these commits. Native provider remains the default; proxy/compression
opt-in. Research schedules remain PAUSED; active chat/goal owns continuation.

Completed new blocks: batching001 six exact fact checks,308046->265627native
 tokens; chronological002 twenty-four generated coding cells,all24checks pass.
Every completed session's unique IDs and native/CLI/cache buckets reconcile
exactly with Langfuse v2. Old v1 trace/session read404s are an API mismatch;
explicit v2 usage fields work. TTGL Experiments contains results plus separate
post-hoc cost evaluations. One actual existing Codex analyst review is published,
178274native tokens,74tools annotated; its expense is separate.

User steering explicitly requires cost, including cache loss. Versioned rates:
`tools/usage-monitor/studies/context-memory-pricing-20261107.json`, verified
Codex Standard50/2.5/250 credits per1M fresh/cached/output. Actual cash/quota and
backend credit estimates remain unknown: existing subscription collector returned
no thread estimates for all six batching sessions. Cost scenarios, not token
counts, govern future nomination. Raw history saves17.47%tokens but only3.24%
scenario cost; FTS/notes cost slightly MORE despite fewer tokens. FTS was never
queried. Original token gates remain frozen; no memory optimum selected.

Mem0/FastEmbed isolated runtime under ignored
`work/security/context-memory-20261107`:50exact packages,50OSVqueries no matches,
wheel hashes reviewed, no .pth/install scripts; explicit Codespace incomplete
security-evidence allowance, NOT clearance. Local pinned MIT ONNX model works.
Stock engine uses explicitly adapted Codex transport/local model paths; optional
NLP/BM25 unavailable, semantic fallback disclosed. Small preflight one extraction
32935tokens, two persisted/retrieved facts, other-tenant empty. Search API error
preserved; corrected reads used zero new LLM calls.

LongMemEval-S MIT JSON data pinned to98d7416c and SHA d6f21ea9..., eight
stratified development plus24held-out reservations before inference. No routing
validation reused. LME001 stopped after three reader completions on first case
and an uncertain300s extraction timeout; usage is null, NOT zero. Never repeat
that case/call. LME002 is RUNNING on ONLY the seven originally unstarted cases,
no replacement,63process cap,1800s memory timeout, same prompts/model. First
extraction completed423s,238facts,actual20hits despite requested10; keep observed
context/cost unchanged and disclose deviation. All readers precede blinded
judges; no accuracy/official score/economic result yet. Read processes and
`longmemeval-002/{started.json,complete.json,stopped.json}` before any continuation.
Do not duplicate/retry or alter frozen code while running: longmemeval_codex_trial,
mem0_codex_adapter,memory_retrieval,longitudinal_memory_trial,cost_context_study,
and pricing JSON. All24held-out cases untouched. Preserve001 partial artifacts.

Maintained MCP graph server2.1.0 also installed ONLY in private experiment review
folder, four locked packages no OSV matches, scripts disabled, attestation and
source licensing transition documented (Apache/MIT, do not call uniformly MIT).
Probe003 passes7protocol/persistence checks with0model calls; failed test-client
probes001/002 preserved. Full RPCs now journaled on each response. No Codex global
MCP integration or efficacy result.17software tests pass. Longer coding/terminal,
Headroom transfer, masking/hierarchy and other planned comparisons remain pending;
see progress doc. Never claim all experiments completed or optimality yet.

### 7 November: cache-aware long-memory development002 completed

All63 LME002 processes completed; measure results and read-only Langfuse audit001
reconcile every session/unique generation/counter.28/28 local rubric successes.
Full-history43.47417, plain search9.02639, FTS7.47870, adapted Mem0 dense81.80931
published Codex scenario credits, including extraction. FTS nominated by the
pre-grade conservative >=5 paired wins rule (actual7/7 wins), not held-out proof.
24 reserved cases untouched. Failed001 extraction usage remains unknown; no
repeat. Worker84072 ended normally. No schedules resumed. Public progress/report
and aggregate JSON updated. Actual cash/quota/local CPU costs remain unknown.

Existing native-provider recovery and session-scoped evidence-query modifications
are preserved separately in commit9f24cf7 (25 workspace and6 setup checks passed),
superseding the earlier note that those nine files remained uncommitted. New
experimental archive/age policy and exact persistence have8 offline checks;
MCP read_compression_source recovery works, normal provider remains unchanged,
and actual model-facing/cache/coding trials remain pending.

### 7 November17:42UTC: reserved long-history validation active

Frozen separate validation runner/protocol002, commitd33630e.24 prior reserved
questions x3arms (full_history/file_search/exactFTS),72 readers then72 blinded
judges,144 maximum processes, no automatic retries. Same prompts/models/methods;
primary added-value comparator plain search, require every control success
retained, >=10% pooled scenario saving and >=13/24 paired cost wins versus each
control. No policy changes based on validation. Original source002 remains
frozen; new runner and its manifest-listed dependencies now also frozen.
Worker exec session28040, PID233572, private longmemeval-validation-002. Inspect
actual started/complete/artifacts/processes before any continuation; never
repeat. First preparation longmemeval-validation-001 ended before preflight,
zero model calls; independent full-JSON decode exited143 with cause unknown.
Preserved and replaced with tested bounded stdlib reader, not a model retry.

Development002 published to TTGL project4ad15b1e75834af6a4656f2f7e4e6225,
experimentf3b623afd5f54aa796537ee8310d800f, eval95a19e6556aa4e5a8254b0e786940b43.
Role-aware publication does not mark extractors/judges as failed reader grades.
Accounting discovery now includes partial/failed long-history calls, keeps
unknowns null and deduplicates native response IDs. Snapshot17:43UTC known
50,808,716 tokens /434 responses /383.578 scenario credits; parent active,
unknown001 extraction and local costs make this lower-bound accounting only.

### 7 November: continuation003 and neutral audit002, native archive005 gate

Validation002 stopped after61 completed readers, zero grades. Cause reproduced:
str.splitlines splits literal U+2028 inside valid JSON strings; physical-LF parser
(native_jsonl.py,2 focused checks) recovers unchanged completion. All61 existing
sessions now reconcile native/CLI AND Langfuse: validation-recovery-audit-001.
Original002 stdout/answers/source unchanged, failure preserved. New frozen
continue_longmemeval_validation.py/protocol003 seals61 existing answer/stdout
hashes and runs only11 unstarted readers plus72 unstarted rubric judges,83 new
processes /144 across lineage. No model retry/replacement. Worker session55728;
inspect work/security/context-memory-20261107/longmemeval-validation-003 started,
complete/stopped and processes. Original84072 and28040 are finished; don't retry.
After complete, run continuation script measure, Langfuse audit, then publish.
Frozen sources include native_jsonl.py, original LME sources, FTS, pricing and
continuation runner: do not edit while active.

Original judge cwd contains condition despite rubric prompt hiding it. Report
prompt-only blinding. Separately registered BEFORE ANY validation grade:
longmemeval-neutral-judge-audit-002,72 anonymous assessments, all exact original
random IDs/order retained, same model/rubrics. Original labels preserved; require
no observed baseline-success loss under BOTH labels plus frozen cost gates.
neutral_memory_judge.py prepared and FROZEN; run only AFTER continuation003 has
complete + measured results, then measure and audit all72 additional judge
sessions. No tools allowed. Same-model/answer-style limitations remain.
Audit001 prepared0calls retained. First audit002 prep copied protocol001 path;
preserved as ...002-preparation-protocol-path-error, zero model calls; corrected
002 prepare has identity guard. Do not launch duplicate judges or reprepare.

Native archive canaries001–003 UNAPPLIED: guard cannot establish recovery from
HTTP schemas, though native app-server catalog probes prove MCP loading. Preserve
all failures/usage.004 separate shell/TTGL-CLI method actually transforms3requests,
exact source and raw recovery work; first relative-path read fails, agent fixes
absolute path, so clean gate FAILS.005 absolute-scope fix passes:2 transformations,
1exact source,1successful CLI recovery, raw bypass,69,890native tokens /1.54366
published-rate scenario credits.00493,010 /1.07998; fewer tokens005 costs more
because cache differs—unmatched configurations, NOT saving evidence.8 policy/
persistence +3 HTTP/CLI checks pass. analyst_cli.py raw-source read avoids Store
DB writes. Experimental routes require explicit opt-in; normal8317 unaffected.

Current owned experimental proxy sessions:37135 port8319(canary002),94934 port8320
(003),92961 port8321(004),28256 port8322(005), all canary models finished. Stop only
these owned proxies after receipts audited.001 proxy8318 already stopped.
Supervisor4332 and normal8317/8766/Langfuse3000 must stay running. Optional profile
~/.codex/ttgl-archive-canary-003.config.toml is explicit-only, never default; archive
and remove only if exact owned contents unchanged. Current005 reader worker16891
finished; no retry. Detailed private mechanism audits004/005 reconcile CLI/native;
public aggregate JSONs exist. Need canonical TTGL role-aware canary publication,
Langfuse audit and updated full expense accounting. New helper/parser/canary/
protocol/report changes are currently uncommitted: commit/push after inspection.
No schedule restarted. Unknown original LME001 extraction usage remains NULL.

### 7 November19:00UTC checkpoint: validation original gate FAILS; neutral audit active

Continuation003 completed all83 new processes;144 total across lineage.
Measured original local rubric: full_history24/24, file_search24/24, FTS23/24.
Deployment scenario credits146.19174 /20.23384 /15.11030. FTS wins24/24 paired
costs vs full and22/24 vs files but loses1baseline success, so reject frozen
nominee regardless of later favorable labels. Plain-file control saves86.159%
with24/24 original labels; descriptive control, not newly selected held-out arm.
All144 native/CLI/Langfuse IDs/counters reconcile. Public original aggregate is
longmemeval-codex-validation-results-003.json. Original rubric judge cost26.16577
scenario credits is research expense. Native rubric scores are not official
benchmark scores or independent programmatic truth.

Neutral audit002 is NOW RUNNING, exec session57938. Registered72 assessments,
random anonymous cwd/order sealed before any original grade, identical rubric/
model and immutable original answers. No retries/selective regrade. Run its
measure action only after complete, then Langfuse audit and joint original/neutral
summary. Audit raw-source/lookup code is FROZEN; do not edit. Primary worker55728
ended normally, no need to wait/restart. Main original-validation publication:
experiment366c50179968421091bdec23ac71a9bb/eval7ed6cb08a3244e6e8fdd1505a32b5ffb.
An additional immutable cost/quality rejection review was recorded, preserving
original generic-import fallback wording and clarifying actual frozen primary
rule / model rubric / no independent programmatic answer-grade claim.

All5 archive canaries now have canonical results.json, native reconciliation and
TTGL publication.json.005 measurement helper measure_archive_canary.py derives
public filename from registered ID; earlier public004 filename collision was
corrected from separate private004/005 audited receipts before publication/commit.
All5 public IDs/path identities now checked. Source snapshots preserved privately
for001–005; failed001–003 and004repair retained. Owned experimental proxies
8319–8322 stopped; exact owned explicit profile003 archived/removed. Normal
services/supervisor4332 remain. Need grouped Langfuse audit for5canary sessions.

native_resume_metering.py preflight001 completed2 actual calls with same exact
thread,2 unique native responses. Current CLI remains cumulative:24411 then48852
input; actual second turn24441. Total48866native /0.38498 scenario credits,
research overhead only. Public protocol/results exist. Account source maps this
SID once and unique native rows, never adds cumulative snapshots. Next reuse
study is DESIGN ONLY in docs/research/cache-and-memory-reuse.md; actual continued
full-context cache control is required before claiming extraction amortization.
No hook installed; official PostToolUse feedback interface merely screened as
another future maintained integration, not a working output-update API.

### 7 November: neutral audit complete; warm-reuse registration prepared

Neutral audit002 completed72, measured and Langfuse audited72/72 exact. Labels:
full24/24, file_search24/24, FTS22/24;1 disagreement vs original FTS23/24. Extra
25.87580 scenario credits research expense. Gate rejects FTS under BOTH sets.
No model worker remains from validation/neutral/canary/resume phases. Need final
joint public aggregate/evaluation, updated expense snapshot and cohesive paper
update. Original and neutral labels must both remain, no cherry-pick/adjudication.

New cache_memory_reuse.py / cache_reuse_measure.py and protocol001 prepared,
private cache-memory-reuse-001, zero models so far.3 generated corpus sizes
(24/96/240 entities, two dated records),4 actual different questions each,6 arms:
continued_full / fresh_full_head / fresh_full_tail / file_search / FTS / Mem0dense.
72 reader CLI calls +3 true per-corpus Mem0 extracts=75maximum. Raw files equal;
fresh arms see own priorQA, continued retains real conversation. Extraction never
gets future questions. Latest-field gold independently parsed from dated source;
12 reference+12 empty-rejection+12 stale-rejection controls and2 source/schema
checks pass. Per-turn allocator was tested READ-ONLY on existing resume preflight:
2native calls,48866total/0.38498credits, no new model call. Native cumulative CLI
snapshots are compared with native prefixes, not added together. Data/code hashes
sealed. Prepared zero-model earlier source and process-timer amendment retained.
Need commit/push prepared protocol/source BEFORE launching this scored block;
then run cache_memory_reuse.py run (no retries). After complete, run
cache_reuse_measure.py, aggregate continued per-turn cells by SID for Langfuse
read-only audit (generic auditor expects complete SID), and publish. Do not edit
its manifest-listed sources while running. No scored reuse result exists yet.

A broad metadata-search command also hit monolithic JSON in old delegation-heldout
files and produced excessive output. Subsequent file-only audit confirms matches
were those old files plus verification-feedback reservation/tree metadata. Do not
repeat broad text scans over experiments JSON. Parse explicit metadata fields;
all36 reserved Aider family names are excluded across languages for any new code
transfer selection (notably Forth/react are reserved). No new routing/Aider model
trial or policy tuning performed; their sources/schedules remain untouched.
Potential fresh public-source code candidates: connect, dominoes, sgf-parsing;
only source/provenance screening considered, zero code benchmark inference.

### 7 November: cache-aware continuation and reuse block running

The user explicitly requires cost, including cache loss, rather than token-only
optimization. The living paper abstract now incorporates completed24-case
validation and72-call neutral audit: full/files24/24; FTS23/24 original and22/24
neutral, so the frozen nominee remains rejected. Both labels are preserved.
`update_context_progress.py` now reads actual reuse-worker progress; no partial
quality/cost result is inferred. The existing worker PID461630 owns
cache-memory-reuse001; inspect completion/stopped/progress before any action.
Its generation and allocator sources remain frozen. Do not duplicate/retry.

Accounting now discovers repeated-query readers and Mem0 extractions, deduplicates
continued sessions, and refuses unregistered model rates. The21:04UTC snapshot
has91,769,661 known native tokens /833.41517 published-rate scenario credits,
including implementation/supervision. It is a cumulative lower bound, not cash,
quota or net saving. One historical timed-out extraction remains unknown.
Five native archive canaries and the actual two-call resumed-thread preflight
also reconcile against Langfuse:6sessions, all exact, readonly audit receipt in
private mechanism-langfuse-audit001. No new generation observations inserted.
A three-contract session aggregation helper supports resumed-thread LF audits.

Older-shell-mask is an explicit experimental variant, preserving the latest four
completed outputs and supplying scoped exact-source CLI recovery. Four proxy/CLI
contracts pass. Archive-age-canary001 is PREPARED ONLY, zero model calls; source
manifest includes its read-only measurer under a preserved pre-inference amendment.
Run only after reuse001 ends, through separate experimental proxy8323, to avoid
cache interference. The registered gate requires actual native effective input
drop and exact recovery, not just request byte changes. No default route change.

Pinned unreserved Exercism Python Connect/Dominoes/SGF source controls pass all
six expected empty/reference outcomes,48 official reference tests total; no coding
model trials yet. Dated source/advisory/provenance reviews and private artifacts
are retained. No new dependency install. Schedules remain PAUSED.

### 7 November21:10UTC: actual reuse complete and older-history gate passes

Cache-memory-reuse001 completed all75 calls with72/72 exact independent reader
checks. Source/allocator remains frozen.115 unique responses reconcile CLI/native
and Langfuse across66sessions (continued threads aggregated once); TTGL experiment
9de806031e7740138a3d7a7296ccab18/evaluation3bf991182b844045bbd2064c361c5a03.
Published results include every actual1–4 question curve. Pooled scenario credits:
continued5.46879, files5.50505, stable-prefix fresh13.72351, changing-prefix
fresh14.21133, FTS6.59329, Mem0incl3extractions20.33354. Allsamequality on this
synthetic recall diagnostic. Changing-prefix fresh uses1.07% fewer tokens but
costs159.86% more than continued; Mem0 is271.81% more after actual reuse.
No cash/general-coding/optimality claim. Failed LME FTS validation stays rejected.

Archive-age-canary001 then completed both model calls, clean registered native
input gatePASS: firsttransform input drops4494 versus raw grows88, latest4
preserved, exactsource andoneCLI recovery0/rawbypass. Complete treated cost1.63609
versusraw1.39721credits,17.09% higher; no saving.15unique native responses exactCLI.
First LF audit caught delivery lag: raw7responses reconciled, treated hasonly6of8;
preserve receipt001 and recheck readonly withfreshreceipt afterdelivery. No rerun,
retry or duplicate generation. Separate experimental proxy8323 exec11561 remains
running; stop only this owned proxy when checks finish. No normal route changes.
Measurer source remains frozen; public result has separate complete-cost fields.
Accounting discovers both agecalls. Schedules remainPAUSED.

Age LF receipt002 now reconciles both sessions/all15responses after ordinary
delivery delay. Receipt001 retained. Owned8323 proxy stopped with ownership check.
Coding-context-transfer001 prepared12 fresh workspaces, protocol/source manifest
sealed before inference; complete transform dependencies and read-only measurement
added in preserved pre-inference amendment. Source controls remain6/6,48tests.
Next run uses8324 experimental proxy, all4arms common transport. Do not infer
compression efficacy from0transforms or public coding quality from controls.

### 7 November: coding transfer complete; memory/backend continuation

Coding-context-transfer001 completes12 calls,12/12 host original-test and
artifact-policy passes.60 responses reconcileCLI/native/LF across12sessions.
Raw315134tokens/3.68218scenario credits;Headroom341896/3.83520;age369345/4.15041;
reversible443592/5.08760. Only reversible actually transforms3/3cells; each6
changes/2exact sources/2successful recoveries. OthersUNAPPLIED. Appliedreversible
costs38.17%more; no default adoption, no official benchmark/population claim.
TTGLexperiment4d3cf1dd3f9442328da6d46b798168b6; owned8324proxy stopped.
All generation/measurement sources remain frozen; no active model worker now.

New infer=False Mem0 mechanism uses existing reviewed runtime, rawdatedrecords
with no extraction, LLMmethodguardraisesbeforeinvocation.3exactrecords,latest
retrieved,cross-tenant0. Firstexit0hasQdrantdestructorImportErroratshutdown;
preserved. Follow-upreopenonlyreads3records,explicitvector/historyclose,0LLM
and0embeddings; only ONNX PCI-discovery warning remains, no shutdown exception. Publicmechanismreceiptpreserveswarning; no efficacy.
A fresh registeredraw-memorycostcomparison/long-horizoncodepanel remainsneeded.

Graphiti[ku zu]28wheelgraph/OSV0butKuzudeprecated/upstreamarchived,notinstalled.
FalkorDBLitecandidate35PythonOSV0butbundledRedis8.10.2affected byupstream8.10.3
securityfix; pinnedpackagingsourcedownloadsunpatchedtag. Blockedbeforeinstall,
neverexecute. UbuntuOpenSSL3.0.13-0ubuntu3.16backportsarenotupstream3.0.13
unpatched; don'tmisflagversionstring. Fullprivatewheel/SBOM/source receipts.

LHTB2pin7ca0cacea9bf6a0694eaad7306bed794eaaaabce,Apache2,77taskconfigs;
onlymetadata/README/license/harnesspyprojectread,notgolds/hidden-tests/tasks.
ForkHarbor0.7runtime102packagesresolves,butfilelock3.32.7selectedbyLiteLLM<4
constraintmatches13OSVadvisories(fixed4.0.9/4.2.1).Blockedbeforeinstall,nooverride.
No benchmarkimage/code/modelrun. Newdocs/research/long-horizon-context-memory.md
recordsfeedback/stopping/fairness/readinessrequirements. Findmaintainedpatched
runtimeorfullyreviewedexistingnativeadapterbeforetrials; don'tdeclareallbenchmarks
permanentlyblocked. ExistingMem0filelock4.2.9isadifferentcleangraph.

NormalTTGL/LFsupervisor4332remains; researchschedulesPAUSED. Remaininggoalactive.

### Next registered storage ablation, zero inference at preparation

memory-storage-ablation001 uses freshseed20261108 with old factual generator,
3sizes×4actualqueries×6arms=72readers+3Mem0extractions. Continued/files/FTS/
Mem0extracted/Mem0inferFalse/MCPgraphraw. Notheldout,notcoding. Sourceforks
memory_storage_ablation.py andmeasure_memory_storage.py leave all old frozen
sources intact. raw_memory_backends.py only missing transport/ranking glue:
stockMem0inferFalse withLLMguard, maintainedMCPcreate/search_nodes andchronology
edges; genericinverse-hit-frequency lexicalunion10nodes/12000chars, notgraph
reasoning. Localtimeincludesloading; localmonetarypricesunknown.

Rawbackendpreflight001 Mem0build/querypass; MCPstores3buthelpermiscountswrapper
keys as1. ExplicitacceptanceFAILpreserved. Correctedpreflight002freshMCPstore3
andlatestvaluepass,0models. No modelretries. Preparedstudyhasprotocol/corpora/
source/graphhashbindings and12reference/empty/staleoraclecheckseach. Mustcommit/
push beforeinference, useoneworker,75max,zeroautoretry. Oldcacheallocatorallocates
continuednativeperturn; newmeasurerboundtofreshstudy. UseaggregatedSIDLangfuse
readonlyaudit androle-awareTTGLpublisher aftercompletion. Keepallfailures.

### Native benchmark preparation while storage ablation runs

Storageworker exec65214 owns memory-storage-ablation001. At last snapshot31/72
readers/33completedprocesses; inspectactualprogress/stopped/complete. Do notedit
itsfrozen sourcesorstartanothermodelworker. Sources/accounting/snapshothelpers
nowdiscovernewstoragecells,continuedSIDdedupunchanged. Latestaccounting21:33
108610717knownnativetokens/928.40349scenario credits,lowerbound;timedoutextraction
unknown,then-activeunmeteredreaderunknown. Neveraddcumulativesnapshots.

TTGLexistingContainerBackendcanbridgehostauthenticatedCodex tooneDockerworker
withhosttoolsdisabled. FullHarborstillblockedfilelockconstraint. NativeSDK1
95-packageexactlock reviewed:OSV0,95tarballhashes/3.4MB,nonativefiles,nounsafe
members,ninesourcepreparehooks(notexecuted).Notinstalled. UnscoredopenOAuth
reportSDK1.32.2/server-legacy2.4.0issue3142 retained; GitHubRESTrate403,webprimary
pagefetched. Don'tcallitaconfirmedmodernserver2.4.0vulnerability.

Newnative_worker_v2.mjs adapts onlyimports/stdio,containercwdandPATHpreservation
ofexistingworkerMCPserver; usesexistingprivate4-packageMCPmemoryreviewruntime,
not95newpackages. Privatecopyinmcp-memory-review matchespublicsource. Probe001
passesoneboundedtoolcatalog/absent-containererrorandinvalid-namecontrols,
0models/0containers/0imageexecution. Notrealactorboundary. Existinglegacyfrozen
sourceunchanged. CurrentMCPmemorystudy'score/lock/entryfilesuntouched.

lhtb2-context-memory-readiness001 publicJSON reserves3devunknown-config/
sqlite-WAL/grammar-fuzz and6validationtasks fromtree-onlymetadata,beforeanytask
instructions/golds. Onlydevtask.toml/environmentDockerfilesfetchednow,exact
Gitblobhashes. AllFROMpython3.11-slim; currentamd64base digestb701198cb708b68d9413
ca67d6311bd97c9389a2c5fe4da0511fc652642366cd pinnedregistrymetadata. Noimagepulled,
builtorstarted. Taskdepspytest8.4.1/coverage/pandasplusdebianpackagesneedreview.
No tasksolution/verifier/instructionread yet. AvoidfullHarborinstallorSDK1install;
reviewnativeadapter/owncontrols/imagessafely. Docsreadinessupdated.SchedulesPAUSED.

### Storage/scoping complete and next reader-boundary canary prepared

Storage001all75complete,72/72independentexactchecks.134responsesreconcileCLI/
native/LF66sessions; TTGLexperiment78fcf67b43ff482c87ca0bd29a941493. Scenario
creditscontinued5.56269/files5.45635/FTS6.48917/MCPraw6.35546/Mem0dense20.02849/
Mem0raw8.10584. RawMem059.53%lessLLMcostthanextracted,but45.72%morethancontinued;
MCP14.25%moredespitefewertokens. No memorydefaultpromoted. Publicresultswritten.

Scope001all6complete,3/3hosttest/artifactsuccesseseach. Markerremovedall3scoped.
319118→238757tokens(-25.18%),3.80190→3.39557credits(-10.69%).25native responses
reconcileCLI;LFaudit40915andpublisher97906pendingpoll. Proxy8325exec8377still
running,stopownedafteraudit. Actorworkdirsanonymous;onlyexperimentinstruction
scopechanged;globalAGENTSunchanged. Reused3developmenttasks,notheldout/global
userinstructionremoval. Allold generation/measurement sourcesfrozen.

Native-reader-boundary001 prepared0models;1CLImax,noautoretry. Source
native_reader_boundary.py +protocol pinned. Customnamedprofile:rootdeny/minimal
read/assignedworkread,networkdisabled,ignore-rules/noAGENTSforactor,unrelated
featuresdisabled. No-sandboxshorthandthatcouldoverrideprofile. Randomownedallowed
anddeniednonsecretsentinels;mustactuallyreadallowedandfailoutsideattemptwith
nosecretintooloutput. Needcommit/pushBEFORErun, ownproxy8326offtransform,then
positiveCLI/native/LFmeter. Notgeneralactorcertification.Don'tretryifstarted.

Standardpython3.11base static81componentOSVqueries22source/Pythonversionmatches,
includingactualpip24/setuptools79;imageblocked,neverexecuted. Taskdep13graphalso
flagsPytest8.4.1(GHSA6w46/PYSEC2026-1845);patchcompatibilityrequired,noofficial
unchangedenvironmentclaim. ChainguardPythonlatest-devmanifestpublicaccessworks
butlatestis3.15,notoriginal3.11. DHIanonymous401preserved;existingDockerHubauth
wasavailable. TemporaryprivateDHIconfigreusesexistingaccountperofficialDocker
docs,no normalconfigchanges(secretchecksumverified),nonewaccount/subscription.
DHIpython3.11-debian13-devamd64digest440a9e19228819eb1645de6b0707eeb4c31016513d
3007ab7c83a7556de73d92,5layers40.3MBcompressed. Metadataonly,noimagepull/runyet.
PrefermaintainedDHIforfuturecontainercontrolsafteractualcomponentreview. Do not
print/commitprivateDockerconfigorcredentials. Freecommunitycoreverifiedofficial
DockerDocsApache2.0; notSLApaidvariant. Currentfreeworkspace3.197GiBvsLHTB4–6GiB
configuredstorage;fullresource-matchedreproductionneedscapacityreview. Continue
localreadiness/eligibleexperimentswithoutinterruptingservices. SchedulesPAUSED.


### 7 November: reader002 reconciled and cost-first decisions
Reader-boundary002 passes the assigned read and blocked outside read through actual native tooling;2 responses reconcile native/CLI/Langfuse,22,027 native tokens/0.19323 scenario credits. Failed001 is retained. TTGL experiment eef0160b292046b7868910379328a89f. Cache-cost steering is explicit: decisions use verified quality and all-in model inference rate scenarios, not token counts; unknown cash/quota/local compute remain null. Reuse001 observed1.07% fewer tokens but159.86% greater scenario cost for changing prefix versus continued context. No scheduled research resumed.


### 8 November: verification-selection001 complete; runtime reviews continue
Six scoped fresh seeded Exercism repair calls complete (alphametics/word-search/tournament), all6 sealed original-test/artifact checks pass. Full_initial429772 tokens/4.15052 scenario credits, focused_initial282537/2.96321:34.26% fewer tokens,28.61% lower modeled cost and3/3 pair wins.46 unique responses reconcile CLI/native/transport/Langfuse. Read-only adherence audit: initial full10/24/12 versus focused1/3/2, all initial failures precede reported file edits, all final full counts pass. Public development evidence only, no held-out/long-horizon/general-quality claim or global default. TTGL experiment e80d44550db84c669499cc95ae4c06e7; worker20102 terminal pending handle poll, owned proxy8333 still running (exec13089). New measurement/results/accounting edits need commit.
Compaction001 pre-inference provider rejection preserved;002 completes actual local-compaction branch with3 responses/67055 native/.85683 scenario, all transport/native/cumulative/LF exact. Original checker incorrectly counted userMessage as tools; measurement revision2 corrects without replacing first measurement. Remote endpoint not exercised.003 initialize times out before thread creation or wire requests; preserve, never retry. Owned8330/31/32 proxies stopped with exact ownership check.
Graphiti Neo4j client27 packages reviewed/re-OSV0 installed isolated graphiti-runtime. Import probe001 fails missing httpx: metadata supplies httpx2 but source imports httpx. Reviewed existing Mem0 httpx0.28.1/httpcore1.0.9 added under fresh29-package receipt (OSV0); no source alias. Probe002 pending. Telemetry false, network guard, no Neo4j endpoint configured or model/graph calls. Kuzu/Falkor rejected candidates stay excluded.
DHI Debian3.11 runtime variant pulled/created/exported metadata only, never started;40 queries/58 source matches need applicability review. Alpine3.24-dev3.11 pinned aa73ad1901249b232a4301462add08fb9f5590130d8838e39080e671f9af24f4 also data-only reviewed:92 OSV queries, one setuptools84.0.0 finding GHSA-xmj3-9gf7-h52w (fix84.1.0). Actual wheel.py copied from unstarted owned container, SHA4ea62eda3c94c91e05e8e16f6b77e65557de10f972b72fd6aba9e030360b12fe, no validation guard in namespace path construction. Windows-focused advisory does not justify simply ignoring its unsafe source on Linux. Image remains unexecuted. Existing Buildx0.38.1/Docker29.9.2 may support a data-only scratch/COPY--exclude derivative with reviewed patched setuptools; do not RUN the affected base to patch it. No derivative built or patched wheel downloaded yet. Available disk~2.2GiB, candidate images consume space; never prune normal services/volumes or unique evidence. LHTB source/harness controls still incomplete; no LHTB models. Schedules PAUSED.


### 8 November active validation and clean runtime gate
Verification-validation00124 assignments are now RUNNING: worker exec35990, owned proxy8334 exec6508. Registered source verification_selection_validation.py and verification_actor_controls.py are frozen; do not edit/retry/duplicate. Own24 actor software controls +24 empty/reference +12 seeded bug controls pass,236 reference tests/arm. Prompt AST identical to development. Modulo ordering gives6 first positions each arm. Source/actor controls hashed. Actual host grades only after all24 generation; do not inspect/tune held-out outcomes. Latest pushed8b035d8.
DHI derived runtime first execution PASSES after74 fresh package queries0matches and actual absence audit. Immutable image sha256:f2c053a1a31a5d57e875062ccbd33fe79aeedf44043defc11051ee8cbfa62544, private recipe in lhtb2-source-review-001/minimal-alpine-runtime-001. Built FROM scratch by copying allowed files from pinned Alpine donor without executing donor; removes4 pip/setuptools APK packages and8 owned root paths, updatesworld/inventory. No patched setuptools wheel installed (downloaded patch candidate unused). Original donor remains blocked/unexecuted. AllnewimagesreadonlyfirstcanaryCPU1/mem128M/networknone/capsdropALL; Python3.11.18 SQLite3.53.4 and BusyBox sh/timeout pass. This is Codespace exception, not blanket security clearance.
Resource discovery: /tmp on /dev/sda1 has35GiB free, separate from1.3GiB workspace/Docker loop4. Use owned/tmp workspaces with persistent sealed receipts/artifacts; do not relocate volumes or prune global images/cache.2 CPUs match allthree selected tasks’ configured2; eachneeds4096MBmem and4–6GiBstorage. /tmp can hosttaskbinds; actualresource/source/feedbackcontrolsremain. No LHTB models.52selecteddev sourcefiles totaling642KB are downloading under development-source (exec pending); validationcontentsuntouched. Graphiti client probe002 actualimport/telemetry/networkguard passes29packageisolatedruntime,0models/DBcalls. OptionalNeo4jconnectionquestionpending; keepotherworkmoving. SchedulesPAUSED.

### 8 November: held-out verification rejected; fresh large-input gate registered
Verification-validation001 is COMPLETE:24 calls,139 unique responses,24 sessions reconcile native/CLI/transport/Langfuse. Both arms12/12 sealed original-test/artifact successes. Full829472tokens/10.11332 scenario credits versus focused990245/12.26397 (+21.2655% cost),4/12cost wins: registered gate FAIL, reject. No held-out tuning/repeats. TTGL experiment e5ea538280a64aefa7b3707ea1bf4eda/eval5769c9f8d55447aab4c9e034d7a4a066/reject reviewd4a0c3818fd140d1b7b5e938ce562f07. Worker terminal; owned8334 proxy still live pending shutdown. Earlier active handles stale. Graphiti29-package import probe002PASS0DB/models; no backend.

Native-long-capture001 completes3 normal responses77403tokens/1.47291 credits, correct marker and exact wire hashes; native CLI retains315070characters but code-mode serializes40757model-visible characters. No automatic compaction/full-string transport exercised. Preserve negative gate, not proxy loss or savings. Owned8336 still live pending final audit/shutdown.

Fresh native-long-capture002 REGISTERED/prepared before inference:315k stdin payload bypasses tool-output cap, seedREADY then same-thread recall, max2CLI processes/no process retries. Built-in openai provider canonical openai_base_url http://127.0.0.1:8337/backend-api/codex; source capability check requires providernameOpenAI and canonical suffix. Previous custom-named/bare-base cohorts exercised local compaction, not native remote behavior. New capture_proxy_native_routes.py normalizes only fixed relative canonical prefix, preserves body/authentication/fixed upstream, records downstream_path.11 software capture controls pass. Never infer zero auxiliary inference from missing native counters. Old001–003/normal configuration unchanged. Run only after registration commit; all response/compact usage must reconcile before long-horizon cost readiness. Schedules remainPAUSED.

### Native long-input002 complete: compaction must be added to CLI scope
Fresh002twoCLI processes complete;3native/transport/LF responses reconcile. Full327917-character stdin retained exactly;READY/recall correct;actual automatic compaction uses in-band/responses with compaction_trigger and nativecompacted eventID. NO separate/responses/compact. Native total528522tokens/16.63802 credits; compaction189257/.52017. CLI final cumulativeordinary339265 excludescompaction: native IDs accountall, neveraddsnapshots. Publicresults002+measurement source. TTGL exp06a62f2b18c84c66bf71982e2eb7cd03 evala070abb292a240d2b9514b7be76d7893; metadatareviewinconclusiveoptimization(positive mechanismonly).001 expcc87951c3c144648b61a797e9840ad82/evalf688279f50394d2983a4e0ee18c5ffb3, LFexact but gateunexercised;preserve. Proxies8334/8336/8337 maystilllive;stoponlyexactownednowcompleted.
Bash7APK recursivegraph static/signatures/10currentAlpineOSVqueries0;all6deps exactlyalreadyinbase. Datedpreinstallreceipt;Bashnewonly--no-network--no-scripts buildin bash-runtime-001, handle94871. Donoraffectedimage NEVERexecuted;reviewedcleanbaseused. No LHTB modelcalls;selectedtaskPython10wheels stilluninstalledpendingnative/publisherreview, ownframeworkcontrolsrequired. SchedulesPAUSED.

### Unknown-config control002 empty passes; reference ready
Review userreply choosesLOCALNeo4jdeployment, noAuraaccount/credentialwait. Neo4jofficiallatest2026.10.2(6Nov) fixesbundledGuava; reviewexactcurrentcommunitygraphbeforeexecution. No graphbackendstarted.
PatchedtaskPython10wheelisolatedinstallcomplete /tmp/ttgl-lhtb-python-gf35lks6. Firstimport001failsmode700traversal; correctedrevieweddepsaccessbits(onlynonsecretdependencies) and002imports+numericchecksPASSPython3.11.18/pytest9.2/coverage7.17.2/Pandas3.1.1/NumPy2.4.6/SQLite3.53.4. ActualNumPy/Pandaslibstdc++ aligned-new usesposix_memalign,notknownCVEsize-roundingbranch;allnativecoverageincompletenessdisclosed. No normaldependencychanges.
Bashruntime001buildPASSsha256:9ed8bd351e618aa9075306abee2a94a14954f35c23dbdc22902080e0dfbb930e. Unknowncontrols001failsat sealinghostreadroot-ownedruns/.keybeforegrading;0models. Preserveoriginalsource/state. Newlhtb_unknown_controls_002.py usesUID1000bothcontainers,separateverifierafteractorshutdown,hashseal. Empty002reward0(expected),~21sec,0modelcallsPASS. Reference002notstartedatthisentry:registeredreal105rounds50secminimum~88min;singleprocessnoautomaticretry. Sourcefrozenafterempty;do notchangeitduringreference. Controlsprivateunknown-controls-002; fullHarborandunsafeimagesnotexecuted. NeedactualmodernMCP/nativeactorboundarybeforeanyLHTBmodels. No schedulesresumed.

### User priority: record original-style Smallville plan FIRST; no paid memory
Userexplicit8Nov: NEVERpaid/hostedmemory,onlyself-hostedopensource. CloudCodexinferenceauthorizedunchanged; no paid memoryservicehasbeenused. Original-styleSmallvilleimplementationandtestingrequested,includingactualupstreamprompts/ranking/storage. ThenuserasksFIRSTrecordwhat/how/progress. DONEnewdocs/research/smallville-memory-implementation-plan.md,componentS01–S15statusandgates. NoSmallvillecoreimplementation/modeltrialsstarted. Sourcereadonlypinfe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4(2023Aug11),Apache2. FullGitHubrecursive44150treeTRUNCATEDbeforebackend;useexactreveriesubtreeforfiles,doNOTassumeabsence. Actualwebsourcecurrentnew_retrieveweights0.5/3/2diffpaperall1; auditrecencyordering/defaults,keepvariantsdistinct,doNOTsilentlyfix. Templatesmustpreserveoriginalcallerformatting;nativeauth/localembedadapterexplicit. Langchainexperimentalupstreamsunset,don'tinstalloldstack. Planlinkedmainregister. Existingread-onlyinspect_memory_artifacts.pyuncommitted:360extractedgeneratedMem0memoriesallpasslexicalsame-service old/newvalues;notsemanticquality. Useraskedinspectactualmemories;showcodingnotesandfactexamplesafterdocumentedinspection.
Unknownreference002RUNNINGexec67702,105paced50secrounds;actorloginitialA0/21atstart. Neverduplicate/editlhtb_unknown_controls_002duringrun. Empty002expected0PASS. Source001hostrootkeypermissionfailurepreserved. Currentreferencehasnograderfiles;separateverifierafteractorstops.0LHTBmodelcalls. Ownedcapture8337maybealivecompletedcanary002;stoponlyexactownedafteraudits(done). SchedulesPAUSED.

### Active Smallville continuation, 8 November 2026, 10:56 UTC

Current chat restored TTGL UI8766 (process21156) and retained running six-service
Langfuse health3000. No schedule resumed. Exporter restarted with SAME immutable
native-export ledger and Smallville canonical capture root003; keep receipts.
Owned canonical proxy25846port8338stores all003/004/005/benchmark HTTP captures.
No full dependency installation, paid memory, or global routing change.

Strict original mechanism003:6importance+1focal completed, stopped list-string
parser on actual JSON list.004reuses focal,2new completed calls, stops comma
object parser.005reuses all9,32newcalls, completes6obs/15thoughts/21nodes/exactfix
recall. Inspection finds malformed full subject tuple fields; preserve snapshot.
006newparser accepts suffix/full tuple, reconstructs with41exact-prompt/role output
reuses,0newLLMcalls; all thought tuple shapes valid and same correct recall.
Actual41responses reconcile native/CLI/proxy/Langfuse;421840tokens,5.1868frozen
Nov7credit-scenario. Actualcash/quota unknown. Reflection FORCED; original remaining
135.005natural_remaining0is copied forced state, correction in measurement, raw
completion unchanged. TTGL mechanism experiment69a92858c9ae4d8da711c2a10a906cb3,
eval8ce619d13a1c4e459c67b438f4145a0f,inconclusive efficacy,not savings.
Results tools/usage-monitor/studies/smallville-mechanism-results-001.json.
17software checks pass. Original sources and failed evidence unchanged.

RUNNING registered smallville-benchmark-001 (PID48510; exec11079):3previously used
eligible LongMemEval dev IDs60036106,c7cf7dfd,35a27287,first3after excluded uncertain
case.9new readers(full-history/raw-files/evidence-first)then9blinded judges;
max18CLIprocesses,0processretries. First3readers complete at checkpoint; second
case indexing. Source/protocol frozen. Modern evidence-first memory distinct from
originalSmallville:exact1200char chunks,SQLiteFTS4+BGE4,full rawfilefallback,0LLM
importance/reflection. Need ALLreaders/judges,measure_smallville.py benchmark,
audit_langfuse_study.py withresults,thenpublish_smallville.py benchmark. Do not
repeat any started/uncertain call or touchreservedvalidation. Native boundary each
reader ownscope passes. Local model/index runtime separately recorded (~250sec
first corpus),not model tokens or pureinference latency. Do not infer benefit
before completed paired evidence. Benchmark memoryQA not long-horizoncoding.

LHTB unknownreference002was hostinterrupted after20rounds;containerexit255 and
missing/tmpreviewedPythondeps retained. FreshOSV10queries0findings+samehashes,
restorationreceipt dated8Nov,exactpreviouslyreviewed wheels restored original
/tmp/ttgl-lhtb-python-gf35lks6,no downloads/lifecycle scripts. Freshzero-model
empty003passes expected0(~18sec). reference003PID31207exec96261RUNNING105paced
50secrounds;initial10/105observed. Keep pacing, neverduplicate. Preserved frozen
002source and live003wrapper; noactortrialsuntilgate. Current benchmark/native
sources frozen; readactualcomplete/stopped/progress before continuation.

Prior untracked inspect_memory_artifacts.py preserved, not overwritten/staged.

### Smallville active update, 8 November, 11:11 UTC

Developmentbenchmark001COMPLETE:3/3all3arms, creditsfull17.01395/files3.91324/
evidence1.00715; tokens365139/188660/44987.18sessions native/CLI/proxy/LFreconcile.
Candidate94.0804%modeledremote inference savingvsfull,74.2630%vsfiles; coldlocal
index697.462sec,1351actual BGEcalls693.718sec,sofirst-uselatencyworse. Do NOT call
"memory inference0" local0: means0remotememory-creationLLMcalls. Signedraw preserved,
clarificationregister. TTGL expd992c5f9fc8048748f4df75c4bb01890 eval6bfaa31f95db413f8a04a33671e92436,
inconclusive pendingfresh; no globaladoption.

NEW registered/frozen RUNNING original-style direct arm:
smallville_original_benchmark.py,protocolsmallville-original-benchmark-protocol-001,
outputsmallville-original-benchmark-001,exec16298. max384processes,128percase,
3sameolddevelopmentIDs,originalsocialprompts/releasedranking/threshold150,
compatibleV3outputparsers,chronologicalfull-sessionobservations. Literalparentheses
encodedstandardJSONUnicodeescapessoobserve()doesn'tdiscardrecordtext;rawfiles
unchanged. LocalBGEtruncationoflongsessionsembeddingsdisclosed. Naturalreflection
only,neverforce. Firstcase41/44observationsremaining50,0thoughtsat11:09. Allscoring/
reflection/readerscount;grade3originalreadersafterallgeneration. Frozen source
imports smallville_benchmark.py too;don'teditit. Completedcontractfailureisrecorded
casefailure,nextindependentcaseallowed;started/uncertainprocessfailurestopsblock.
Needmeasure_smallville.py original AFTERbothblockscomplete;LFreadonlyauditand
combinedpublication/reportnotyetimplementedfororiginal. Preserveallcurrentcalls.

NEW frozen freshvalidation:
smallville_validation.py,smallville-validation-protocol-001.json,
outputsmallville-validation-001,exec17351.RUNNING6newIDsoneper6types,hashseed
andmetadata-onlyreservationprivate smallville-fresh-validation-reservation-001.json,
excludingpriorreservations/IDfamilies/supportingsessions.36modelprocessesmax,
18readersTHEN18blindedjudges,0retries. Sameunchangedevidence-memorymethods,
readercommonandownnativeboundaries. Firstindexbuilding,nooutcomesyet. All6complete;
no tuning/replacement/favorable stopping. Measure_smallville.py validation
implemented(dynamicmajority>n/2);audit_langfuse_study.py;publish_smallville.py
validationimplemented. Latestmeasurement/publicationchangesnotyetcommitted.
Do notmodifyfrozenbenchmark/validation/originalsourcesduringruns. Existingowned
8338canonicalcapture(root003),8766TTGLandLangfuseexporterSAMEledgercontinue.
Unknownreference003stillRUNNING,30/105pacedroundsseen,stageB;noactortrialyet.
ResearchschedulesPAUSED. Workonlyactivechat; no duplicateworkers.

### 11:22 UTC live checkpoint

Alloriginalsource/adaptationevidence retained. Direct original arm:44+51+47
observations completed,0naturalreflections,thirdcorpusremaining40;2readerscomplete,
nojudgesyet. Freshvalidation6/18readerscomplete (first2cases),thirdindexbuilding;
nojudgesyet. Do notinspectgrades/tunepolicy. Bothnoerrors. Existingpacedreference
40/105rounds,stageB. No duplicates/retries. Normal existing capture8317also restored
via capture_proxy.py (exec59927), in addition to study8338; no globalconfigchange.
After all study capture exports reconcile, return SAME native-export ledger
watcher to normal global captures rather than leave only studyroot configured.
All seventeen software tests passed before these calls. Latest measurement and
publication scripts now support original/validation; don't rerun finished blocks.

### 11:29 UTC original benchmark COMPLETE

Directoriginal3case arm all3success,0contractfailures.146socialimportance+3reader
calls(149taskprocesses),2122977tokens,39.93569scenario credits.3judgeoverheadcalls
0.35720credits. All152sessionsnative/CLI/proxy/LFreconcile, LFreceipt001true.
No naturalreflection:146observations/0thoughts,remaining41/23/32. Cost2.3472xfull,
10.2053xfiles;0/3pairedwins,failsnomination. Resultsprivate+public
smallville-original-results-001.json. Published original exp930733e43e3944f680b76fa4a5239d50,
eval55766928d6b24926b57bce3479f4a099,reviewreject; mainworker
exec16298done. No reruns or policychanges.
FreshvalidationstillRUNNING:9/18readers(3/6cases),1774localembedsat11:28:50;
nojuryyet,nofailures. Candidate/methodsfrozen. Awaitall18readers+18judges,
measure_smallville.py validation, readonlyLF audit thenpublish. Current allsource
andfailedraw evidencepreserved. Unknownreference003~50/105rounds,stageC,
minimum50sec pacing unchanged. SchedulesPAUSED;activechatonly.

### 12:04 UTC validation primary COMPLETE, audit active

Fresh6casesall3arms6/6primaryrubricpasses. Creditsfull35.23015/files3.97731/
evidence3.34583; tokens737187/299051/143071. Candidate90.5029%savingvsfull,
15.8771%vsfiles;pairedwins6/6vsfullbut3/6vsfiles,soFROZENnominationgateFAILS
(required4/6). No defaultadoption. Coldlocalbuild1544.036sec,2692local BGEcalls
1535.444sec;memoryfirstuseoperationtime1645.602secvsfiles148.797sec.
36sessionsnative/CLI/proxy/LFreconcile;primaryresultsprivate/publicgenerated.

Neutral-directory audit001strictprepareREFUSEDbecause1primarygradealreadyexisted;
0auditmodels,sourcepreserved. Separately registered002explicitpost-generation
sensitivityauditbeforeoperatorlabelinspection (manifest2primarygradefiles),
ALL18answers,unchangedrubricandcondition-neutralitempaths. Primarypromptsomit
methodnamesbutcwdrevealslabels; auditremovesthatcue withoutreplacingprimarylabels.
CurrentRUNNING smallville_neutral_audit_002.py run(exec14161),13/18assessmentscomplete
at12:03;NOresultsinspected/noerrors/no retries. Protocol002/sourcefrozen. Need
measure_smallville.py neutral -> audit_langfuse_study.py sameusualdatesoutput001.
Don'trerun startedaudit. Freshpublish waitsneutralLFaudit; measurementkeepbothlabel
sets,globalpromotionvetoifqualitylossundereither. Candidatealreadyfailscostgate.

Unknownreference003stillRUNNING90/105pacedrounds,stageE. Awaitcomplete.json;
noagentmodeltrials started. Report_smallville.py prepared:requiresall5blocksresults
+LFaudits andreferencecompletion; aggregatesdedupnative/proxyallIDs,pending/final
receipts,localops,researchlowerbound; writespublicfinalaccounting001and
 docs/research/smallville-results.md. It doesNOTre-runmodels. Actualreferencefailure
mustbereportedifitoccurs,notrepeated. Afterallstudiesexported,stoponlyowned8338
proxy25846andreturnSAME native-exportwatcherledger tonormalglobalcapturepath.
KeepTTGL8766,Langfuse6servicesandnormal8317capture running. ResearchschedulesPAUSED.
Originaluntrackedinspect_memory_artifacts.pystillpreserved. Pendingsourcechanges
aremeasurement/publication/reportandthesehandoverupdates;commit/pushfinish.

### FINAL Smallville checkpoint, 8 November 2026, 12:15 UTC

All registered memory-QA model assignments/audits and paced control COMPLETE.
DO NOTre-run/retry/replace any. Final docs/research/smallville-results.md and
smallville-final-accounting-001.json.17software tests pass, frozen sources
unchanged,all30native reader scope controls pass. No global memory adoption.

Original3dev arm3/3,39.93569credits (146importance ratings34.72764 +3readers5.20805),
2122977tokens;0naturalreflections/146observations. Nominationreject.
Evidence-first3dev3/3,1.00715credits vsfull17.01395/files3.91324.
Fresh6primaryall6/6;creditsfull35.23015/files3.97731/memory3.34583;memory90.5029%
vsfull/15.8771%vsfiles,3/6pairedfilescostwinsfails>=4gate. ColdBGEindex1544sec.
Neutral002all18assessmentscomplete:full6/files6/memory5;singlepreferenceitem
fca70973disagrees(primarytrue,neutralfalse). Bothlabelsretained,no"corrected"grade,
noheldouttuning/repeat. Same-modelrater sensitivity,notprovenhumantruth. Audit
post-generation registrationbeforelabelinspectionexplicit;001strictpre-grade
prepare refusal0modelcalls preserved. Freshpromotionrejectdespitepooledsavings.

All5blocksresults+LFreadonlyaudits reconcile:265processes/298unique responses,
4815960tokens/115.36792frozenNov7ratecreditslowerbound;parent/setupinferenceextra
unknown,cash/quotaunknown.4248recordedlocalembeddingops2421.995sec. No unresolved
captureoperations. Signed finalaccounting retained, report can regenerateonlyif
identicalaccounting receipt. Pub/report helperchanges areanalysis,notfrozenworkers.
TTGLfreshexpd1754620509248cb97922ecb0b769a5e,
eval9e218093b62d4a11b77262d0eadbb40d,reviewreject10146a0250f34bf1a30d1221b5bce4a5.

Unknownreference003COMPLETEreward1(expected1),105rounds,min50sec,
wall5259.551975685,0modelcalls. Empty003expected0pass. All priorinterrupted/
permissionfailurespreserved. No actual LHTBmodelactor orcoding-memoryefficacytrial;
reserved6LHTBvalidationcontentsuntouched. Do notmistakereadinessforagent score.

Ownedstudy8338proxy25846STOPPEDonlyafterallmodelblockscomplete and0pending
operations. NativeLFexporter50015stoppedonlyatnaturalidleafterflush, sameledger
retained;normalcapture-rootwatcher restartedexec56398. Normal8317proxy127075,
TTGL8766process21156,and6Langfusecontainers retainedrunning. No globalCodex
provider/memoryconfigchanged. ResearchschedulesremainPAUSED. All raw private
histories/prompts/memory nodes/captures/receiptsremainignored work/security.
Prioruntrackedinspect_memory_artifacts.pypreserveduntouched. Finishcommit/push
ofreport/summary/publicresultsifnotyetdone; no moreinference isneededforthisblock.

### Online-memory continuation, 8 November 2026, 14:08 UTC

User explicitly requested continued full testing after the QA result. DO NOT stop
at the integration checkpoint or rerun any completed model assignment. New plan:
docs/research/smallville-online-plan.md; checkpoint report:
docs/research/smallville-online-results.md. Prior QA studies/failed evidence stay
frozen, original scorer still rejected, reserved LHTB validation six untouched,
no global memory adoption, schedules PAUSED. No subagents. This active chat owns
the new work. Original untracked inspect_memory_artifacts.py remains untouched.

Native integration diagnostics all COMPLETE, no retries:
001: two CLI processes/6responses, MCPapproval blocked,0actualtools.
002: two/17responses, firstedit/check/note succeeds; restart calls search with
limits10/20 outside8 and assumes taskreadonly without attempting write, finalfail.
003: two/13responses, scoped4toolpermissions, bounded search and general task
workspace guidance; bothfreshsessions actualedit/check/remember/search/read,
independent saved-codecheck PASS,0toolerrors. Continuation001: two/13responses in
one resumednativeSID, lexical-onlyfilesmode, independentcheck PASS,0toolerrors.
All8processes/49unique responses native/CLI/proxy/Langfuse reconcile:
633879tokens/7.70659frozenNov7scenario credits. Research cost, not efficacy/saving.
Parent/setupinference additionalunknown;cash/quota unknown. Seven local BGEops
3.3647712409965606sec, coldstartup additional. Four actual results/reviews and
accounting published in TTGL Experiments (failedonesreject, successesinconclusive).

IMPORTANT linkage defect retained/audited: 003/continuation worker constants copied
002protocol into output directories. Intended003/continuation protocols AND actual
generation sources committedbeforeinference (877a56d/79488fd); private
protocol-linkage-audit-001.json proves exactbytes/timestamps. Do not edit frozen
workers/manifests/protocol.json or rerun. Append-only corrected TTGL evaluations
published by annotate_online_protocol.py; original evaluations preserved. No
measurement/accounting replaced or duplicated. New matrix has explicit ID,
allocation and copiedprotocolhash guards.

Incremental memory online_task_memory.py: immutable SHA sources, SQLiteFTS, optional
reviewed offline BGE only instructions/agentnotes; agent_assertion neververified
byclaim/sourcepointer. task_terminal_mcp_v2.py fixes boundsearchusability, explicit
writabletask vs readonlyhost guidance; UID1000fixedcontainer, noarbitraryhostpath,
rawpaging, durableRPCintent/idempotency, no uncertain replay. Runtimev3 actual
nativeCLI and scopedinvocationlocalapproval4tools only, no globalpolicy/hookchange.
24storage/bridge checks pass; 5scheduler controls pass (fullhorizon, resume/fresh,
uncertaincallstop, startedmatrixreplayrefusal). New analysis helpers:
measure_online_memory.py, audit_online_memory.py, publish_online_memory.py,
annotate_online_protocol.py, measure_online_longhorizon.py.

Actor controls:
- Unknown FINAL runtime_v5 plus controls010: empty expected0PASS. FULL reference
  STILL RUNNING PID338427, exec51364, rootlhtb2-source-review-001/actor-controls-010/
  reference. At14:07 latest70/105pacedrounds, nofailure. Began13:06, minimum50sec,
  expectedfinish~14:34UTC. Check actualcomplete/stopped/process, NEVERduplicate.
  Do not edit imports runtime.py/runtime_v2/runtime_v5/controls010 whileactive.
- SQLite FINAL lhtb_sqlite_actor_v2.py + controls002: emptybinaryfail/dense.1667,
  referencebinarypass/reward1.0; ownboundary/privatechildchecks pass. Originaljudge
  compare/dense unchanged, candidate subprocess dropsUID1000.001mountprep failure
  preserved,0models. Immutableobservations separate from writableworkspace.
- Fuzz FINAL lhtb_fuzz_actor_v2.py + controls002, fuzz_worker.py and
  fuzz_verifier_bridge.py: empty.2119FAILexpected, reference.9154PASS. Separate
  UID1000JSONIPCworker cannot introspect rootcoverage/parsers; original scorebody
  andthreshold unchanged butthroughput differs => adaptedLHTB-derivedNOTofficial.
  Two actual verifier workers in fuzz-adversarial-control-001 confirm UID1000,
  CapEff0, privatecoverage/reward/testwritesdenied,no parentobjects. Trustedgrader
  alone hasKILL toterminate droppedUIDchild.001prepprivatecoveragepath/kill failure
  preserved0models. Alltaskimages/Harbor remainblocked; onlyexistingreviewedimage
  and taskwheels reused, noinstall/pull/download execution this continuation.

NEXT required full matrix: online_longhorizon_trial.py and
tools/usage-monitor/studies/online-longhorizon-protocol-001.json. Not prepared/
started yet: ONLY missinggate=unknown_reference. Actual gate command confirms.
Nine assignments, three originalreserveddevelopmenttasks unknown14400s,
SQLite5400s,fuzz10800s xcontinued_records/restarted_records/restarted_memory.
LexicalFTS/rawrecords/falliblenotes/publicinfo in ALLarms; memory addslocalBGE.
102maxnativeprocesses,900seccheckpoints,60tools/phase,toolsclose600s,timeout840s,
25.5actorhours sequential. Continued arm originalinstruction once, shortlater
continuation; fresh arms fullinstruction eachtime. Noearlysuccessstop, no private
livefeedback, no uncertainstartedcallreplay. Offlineartifactreview for everyarm
separatefrom binary/dense/score. Source/evaluation/protocol/source-task hashes
freeze at prepare before first benchmarkcall. Finishall9 before selection;
retainallbaseline successes, >=10%costsaving and >=2/3pairedwins vs BOTHcontrols.
Ifnonequalifiesrejectpromotion; onlyqualifierfrozen beforefresh6validation.
Do NOT claimpreparedmatrix as scoredmodeltrials or stopatthis checkpoint.

After referencecontrol finishes andallgatespass: commit finalsource/protocol,
run online_longhorizon_trial.py prepare then run ONE worker. Pointer
work/security/context-memory-20261107/online-longhorizon-development-001.json
will identify private /tmp output root. Do not edit listed frozen sources while
matrixactive, duplicateworkers or resume schedules. Need monitor/audit allactual
assignments, offlineartifactreview, measure_online_longhorizon.py afterfullmatrix,
groupedLangfuseaudit, publishandfinalreport/summary. Registered modeloutputcost
counts allresponses+compaction, validated cumulativeCLIdeltas, rejectsorphans.

Services: TTGL8766 PID21156 and6Langfusecontainers retained. Normal8317capture
PID127075 unchanged. Owned8370proxy old358049 stoppedONLYafterallrequestscomplete;
new PID398985/exec48902 destination /tmp/ttgl-online-memory-captures-wryycodk
(private online-capture-storage-002.json). Old001/captures remainretained; early
002507reserve rejections notsubmitted then SAMEinvocation began when spacegrew,
allcompletedresponses counted. Fullcanonicalcaptureworks, preserveCAS+pending
receipts. Thisproxyserves onlydiagnostics/matrix; no normalroutingchanges.
Exporter238891 stoppedONLYatfreshflushedidle; SAME native-exportledger exported
29old+33newtransportobservations,0newmodelusage, noerrors. Normalcapture-root
watcher restored PID430384/exec9293. Newprivate
online-transport-export-handoff-001.json records handoff; noledgerduplication.
Workspace nearlyfull; private corpus longmemeval_s_cleaned.json relocated
byteidentical to /tmp/ttgl-preserved-memory-corpus-*/ with verifiedSHA and original
pathsymlink; relocationreceipt retained. No frozenstudydeleted. Newcaptures and
matrix use roomy /tmp. Preserve all raw histories, credentials and DBvolumes.

14:21UTC addendum: reference010now90/105,laststageE,PID338427stillactive, no
completion/stopped yet. Final benchmark runner also imports
plan_online_longhorizon.py: after `prepare`, run that helper with the new private
root BEFORE `online_longhorizon_trial.py run`. It creates TTGLproject/nine tasks
and immutable protocol linkage, then phases attach actual native turns. Existing
experiment framework correctly requires real baseline evidence; experiment row
is deferred until first full control completes (activate helper), not fabricated
from0events/oldQA. Preserve any metadata-failure receipts; they never trigger
another model call. First full control creates actual baseline; final comparison
still uses ALLmatched cases. Five scheduler tests pass after this hook. This
source/protocol remains pre-inference; matrix still NOTprepared/started.

14:41UTC: FULL reference010COMPLETE reward1.0, all105rounds/50sec,5264.5928sec;
PID338427exited. Finalcleanupreview fixed root-supervisor child timeout cleanup
beforeanybenchmarkinference. FinalUnknownruntime_v6 uses newbase_v6/private_v6
copies; ONLY rootKILLcap + importversion changes. lhtb_supervisor_timeout_control.py
actually timesout/reaps UID1000engine andSQLitechild; actorsCapEff0. Strictsource
equivalence receipt permits explicit reuse of fullreference010; originaldaemon/
runner/grader bodiesunchanged, notsilent repeat. Newempty/private011passes.
SQLitefinalv3,controls003ownempty/referencepass. Fuzzfinalv3worker_v2 restores
reviewedPythondependencyimports+upstreammodulename; controls003empty.2380expected
FAIL/reference.9154PASS; actualadversarial002confirmsimports+UID1000CapEff0private
writesdenied. Earlier002/001controls preserved. Runtimev4 adds stricterMCPserver/
tool validation after SAME v3generationcommand; deterministicreplayall8priorCLI
outputsPASS,0newmodelcalls. Two securityscopeunittestsplus5schedulerpass.
ALL13gate checks NOWPASS, matrixstillNOTprepared/started atthisaddendum. Commit
allpendingfinalsource/protocol FIRST, then prepare, plan helper(root), ONErun.
RuntimeSOURCES includesnewbase6/private6/v6,SQLitev3,Fuzzv3/worker_v2,nativev4,
meterandTTGLplanhelper. Onceprepared/activeDONOTeditfrozenfiles. Remainingwork
isactualfull9assignmentmatrix+offlineartifactreview/meter/LFaudit/selection, NOT
anotherprep-onlysummary. Scope/protocolattachmentfixedbeforegeneration; all
researchschedulesstillPAUSED. Userexpectsfinishedexperimentsandresultsummary.

### ACTIVE full online matrix, 8 November 2026, 14:58 UTC

Allfinalsource/protocol committedandpushed256fdd3 BEFORE benchmarkgeneration.
`prepare` COMPLETE: pointer
work/security/context-memory-20261107/online-longhorizon-development-001.json
root=/tmp/ttgl-online-longhorizon-development-c58pqefb. Frozenmanifest28sourcefiles,
13green gate receipts, copiedprotocolSHA and ALL3tasksourcehashes. TTGLplan helper
completedbeforemodelcall, projectbfaaccd058ca411d89ce6ab551ea469a, nine task IDs in
root/ttgl-plan.json, first task79b99c3dc7d84a75a37faf5379803c65. ExperimentIDnull
untilfirstfullcontrol(actualbaseline)completes; thisisintentionalguard.

ONE worker RUNNING PID508386, exec13061: online_longhorizon_trial.py run.
Started14:42:52; firstactorready/phase0about14:43:06. Originalfirstcondition
unknown/continued_records assignmentb359d2728417ad1b, horizon4h,16phases.
DO NOT startanotherworker, editANYmanifest sourcefiles, retuneprompts, repeatcalls,
inspectreservedvalidation, stoponfavorable subset or resume schedules.
All9assignments25.5actorhours sequential; expectedfinish~Nov9 16:15UTC if no
ambiguity. Needcontinueactivechatuntilfullmatrix/analysisdone, notprep-onlyfinal.

FirstCLIphasecall-00COMPLETE, SID01a1bb9d-389d-7e01-b3fd-ccbf743251df,15MCPcalls
(includesphaseclosureanswers, not15assumedexecutedcommands),0MCPerrors,0remember
calls. Taskstillunfinished; do notinferagent/taskfailureorsuccessfromthis.
Actualnative/CLI/proxyreadonlyaudit35unique responses767014tokens(input764501,
cached722560,output2513),4.5317scenario credits. Immutable
call-00/interim-accounting-001.json retained. ThisisPHASEONLY, includedlaterinfull
assignmenttotal, NEVERadditagaintoresults. TTGLturnassignmentreceiptpasses;
nativeeventtasksummarymeasuresmatchingusage. No privategraderlivefeedback.
Phase1nextstarts~14:58:06; sourceprogressJSON/rootstopmarkers inspectbeforeactions.

Langfuse exporter430384 stoppedONLYafterflushedidle14:47:47; sameledger nowwatcher
PID519613/exec47562 with --capture-root /tmp/ttgl-online-memory-captures-wryycodk,
allnative/.codex imports continue. Status14:56noerrors; studypairs nowLIVE.
Normal8317rawcapturesstillspoolunchanged, restore/exportnormalroot atmatrixfinish
throughSAMEledger(notnewone). Proxy8370PID398985retained; TTGL8766PID21156,
normal8317PID127075,and6Langfusecontainersretained. No normalmodelroutingchange.
Earlier handoff receipt records previous restoration; this addendum supersedes
its normal-rootwatcherstate duringnewmatrix. SchedulesremainPAUSED.

Finalsoftware31checksPASS (24storage/bridge+5schedule+2scope), actualfullreference
010PASS, empty011+supervisorcleanup/reference-reuseauditPASS, SQLite003controls
PASS,Fuzz003/reference.9154+adversarial002PASS. No furtherpreparation needed.
Laterwork: letALL9finish; offlineartifact-review.json forEVERYarm with sealed
sourcehashes+rationale/status, runFROZENmeasure_online_longhorizon.py, grouped
Langfuseaudit, publishactualwholematrixandreport; applyfrozenbothcontroljointgate.
Onlyqualifieradvancestoseparatelyfrozenfresh6validation. AllfailedQA/canaries/
linkageannotations staypreserved. Parentinference/cash/quotaunknown.

18:22UTC addendum: firstcontrol15/16nativecheckpoints COMPLETE, next/finalphase
starts~18:28; whole4hgrade stillwaitsuntil~18:43. QueuePID508386/exec13061healthy,
no fatal/stopped markers, frozen28sourcehashesremainunchanged. Useraskedprogress
at17:44; answered12/16, nofinalgrade, matchedmemorynext, full9blockexpectedNov9
afternoon(~16:15). Keepgoinguntilfulltesting/summary; statusquestiondidnotcancel.

Read-only55secmonitor process exec85298 continues (checksphasecounts/PID/source
hashes/fatal markers). Last V8wrapper352was terminated ONLYto do offlineanalysis;
theactualmodelworker wasNOTstopped. No V8wrapperactiveatthisaddendum. Canread
85298orstartnewreaderwrapper, nottwo simultaneousreaders. Monitorhas0modelcalls,
notascheduledheartbeat. Sourcecode/generationprotocol STILLFROZEN.

Offlinehelper extract_online_artifacts.py +4privacy tests committed/pushed73b71de.
UseONLYaftereachassignmentcomplete: exports submittedengine.py only forunknown
(neverprivateoracle/key/verifier), submittedsource forSQLite/Fuzz; validatesarchive
againstactualsealedgradingfiles. Outputartifact-view-001/ plus
artifact-view-001-provenance.json. Refuseslive/traversal/changedsources. No automatic
artifactPASSorgradechange; mainmustreviewcode+visiblecommands andwrite explicit
artifact-review.json statuspass/fail/unknown+rationale+source_hashes. Thishelperis
analysisonly, notafrozen generator/scorerchange. Olduntrackedinspect_memory_artifacts
remainsuntouched.

TTGLmetadataonly literalcategoryrules added viaexistingMCPtools; IDs/private
receiptcontext-memory.../online-observability-labels-001.json. Names:
ttgl_task.terminal=>taskterminalcalls; .search_records=>memorysearchcalls;
.remember=>memorynotecalls; .read_record=>memorysourcereads. Actualterminal/search
viewsverifylabels. Rawmeasurements/inference unchanged; callsarenotassumed
successfulcommands orverifiednotes. Currenttokenandtimingcountersremainnative.

Diskpressurehandled WITHOUTtouchingactiveruntimes/credentials/.codexhistories/
DBvolumes/Copilotcache. Rootfell~487MiB; now~1.7GiBfree, /tmp~30GiBfree. Cold
browserQA vendorbulk +reviewed-wheels +graphiti-reviewed-wheels movedbitidentical
to /tmp/ttgl-preserved-cold-artifacts-yvmfz6ks, originalslogicalpathsymlinked.
Allfilehashes/links, copiedtree+fulltararchives verified; noactiveFDs, ownedfiles,
noclones/specialfiles. Browseruniquescreenshots/preview/securityreceipts additionally
copiedpersistentlyunderwork/security/cold-storage-relocation-001/
browser-qa-unique-and-receipts. Vendorbulktars liveon/tmp; alloriginalbytesretained.

Six COMPLETED priorstudyoutputtrees likewisepreservedandlinked: smallville-original-
benchmark001, smallville-validation001, smallville-benchmark001,
verification-selection-validation001, cache-memory-reuse001,memory-storage-ablation001.
TheirFULLverifiedcompressedarchivesarePERSISTENT under
work/security/cold-storage-relocation-001/completed-study-archives; perfilehash
receipts thereparent. No oldmodelrerun/metricrewrite/uniquedata loss.
Coldverifierattempt001stoppedbeforerenamebecauseinefficientgziprandomseeks;
streaming002verifiedandfinished. Legacyrelocationattempt stoppedatmissing
complete markerforlongmemeval-validation002 BEFOREchangingthatthirdsource;
itscopy/tmpretained, originalleftintact. Alloperationalfailures0modelcalls.

Corpusrawlivefile/tmp+originallogicalsymlinkretained; compressedbyteverified
workspacebackup longmemeval-s-preserved-001.json.gz(77800679bytes) and
corpus-durable-backup-001.json allowrestorationif/tmpgone. Currentstudyregistration
also copiedbyteidenticalonto workspace at online-longhorizon-registration-preserved-001
(protocol/manifest/TTGLplan/started/intent+hashreceipt); noactivefilesmodified.
NeedarchiveEACHcompletedcurrentassignmentandfinalcanonicalcapturesonto workspace
afterstable/fullresult, preservingprivateevidenceandallfailedcalls. Restore/export
normal8317capture inputafterfullmatrix via SAME native-exportledger. Study8370
andallnativecapturecontinue; lastLangfusestatus18:11noerrors.

### 8 November: user redirects to small tasks; memory inspected

Supersedes the earlier instruction to finish all nine long assignments. User asked
for smaller tasks and inspection of relevant memory. Long worker PID508386 stopped
gracefully after call-04 completed (no interrupted model calls); stopped.json and
operator-discontinued-001.json retained under the existing /tmp study root. Do not
resume/retry this matrix. Completed control reward .9913793103448276, verifier1;
partial memory arm has no final matched comparison. Five notes/68 tool results/one
instruction now retained; all note source links exist and hashes verify. Notes
retain useful public findings, corrections and uncertainties; all five remain
active with supersedes empty. Search reuse observed, source reopening absent.
See smallville-online-results.md and private memory-relevance-inspection-001.json.
Smaller completion-driven matched trials remain outstanding; no new trial has
been registered or run. Existing Langfuse/TTGL retained; schedules remain paused.

### 9 November: Luna Smallville / TokenEconomizer comparison complete

User requested Luna-maintained Smallville versus Microsoft TokenEconomizer.
Read docs/research/luna-memory-tokeneconomizer.md and the final aggregate in
tools/usage-monitor/studies/luna-memory-tokeneconomizer-final-results-001.json.
All 72 coding assignments passed selected tests: two 32-assignment blocks on
8 reused public HumanEval functions, plus 8 later-period Sol-maintenance controls.
Same Sol solver throughout; Luna maintained memory, not independent task solving.
Native remote-rate totals: source search 4.409320 credits; Smallville/Luna
5.2218505 (+18.43%); TE defaults 4.676670 (+6.06%); TE micro-skills/Luna
3.8781115 (-12.05%); later Smallville/Sol 9.725940 (+120.58%). Luna maintenance
was 0.3834605 versus Sol 5.7164 credits (93.29% lower); whole remote-call scenario
46.31% lower versus Sol-maintained memory, but still above plain Sol/search.
TE numerical development gate passes for memory-on, but neither TE arm injected
skills, applied pruning or issued redirects: do not attribute the difference to
learned memory or claim broad savings. No coding arm naturally reflected. Forced
Luna diagnostic stored15 thoughts/exact recall only after v4 JSON-triple wrapper;
original refusal and all failures preserved. No global memory/provider adoption.

Full native launch stopped after6 progress rows plus a completed7th solver/Luna
reply whose wrapper exit receipt was missing. Recovery001 verified native/CLI/
capture, replayed ONLY that exact reply through unchanged TE fold with0 new LLM
calls, then continuation002 ran only25 never-started cells using upstream async
folds. Original sources/stopped/progress preserved. One late-seal flag and unknown
child-process lifetime remain. No started or uncertain call repeated. Control
was later-period, not simultaneous randomized; all are development, not held-out
or official SWE-bench/TokenEconomizer paper scores. Target90 not met.

All494 unique responses across270 model-bearing native sessions reconcile;
5,292,938 native tokens and49.1993445 scenario credits include trials/diagnostics.
Parent implementation/supervision additional/unknown; local embeddings unpriced;
cash/quota/full deployment cost unknown. No net first-use research saving.
20 focused unittests pass; original source ResourceWarnings retained, upstream
pytest unavailable. Source pin264e7a7 reviewed stdlib only; no new install/image
pull. Capture port8381 closed and2 OWNED non-model idle-pruning workers stopped.
All capture bytes copied+hash-verified to workspace work/security/context-memory-20261107/luna-te-captures-preserved-{001,002}; /tmp originals retained. Final
accounting/preservation/delivery handoff receipts beside them. Langfuse delivery
not verified; don't claim4-way reconciliation. Existing collection config and
research schedules unchanged/paused. No more trials/queues running; do not repeat
these completed attempts, resume the discontinued old long matrix, or launch
larger/held-out work without a new instruction. Prior user local edits preserved.

### 9 November: knowledge accumulation paper and same-repository design

New user instruction requests Mem0/Zep comparison and a Markdown research paper,
including native memory on/off and a cheap-model editable challenge graph whose
knowledge can transfer across tasks in one codebase. Read
docs/research/knowledge-accumulation-study.md and
docs/paper/knowledge-accumulation/paper.md. The separate routing paper is unchanged.
Draft includes focused literature, completed historical diagnostics, new metadata
feasibility audit, methods and conclusions; no new repository model-quality
results or innovation benefit is claimed. Full head-to-head is still pending.

VibeMemBench metadata audit:111 targets/90 repositories;9 Python repositories
have multiple targets. Deterministic metadata-only reservation selects cfn-lint5
development and moto4 validation; validation content not inspected for tuning.
Own/future history excluded by strict upstream issue-ordinal rule; real PR-time
chronology not established. Latest8 earlier histories cap is bounded development,
not the full upstream protocol.13 software checks pass. Private viewer response
includes grading data, kept ignored and never forwarded; pinned Parquet/viewer
equivalence remains a pre-inference gate. Installation metadata's targeted test
commands must stay outside the actor/memory boundary.

repository-memory-protocol-001.json is a prospective design/metadata reservation,
NOT frozen runnable assignments. First two development targets are the initial
unit after environment/backend/native-memory/metering/budget gates.0 new model
trials. First original image blocked: digest-verified base-layer email/generator.py
matches CPython3.10.19, not the documented3.10.20 security fix for CVE-2024-6923.
No image installed/executed; complete final-overlay/OS scan not claimed. Prefer a
patched compatible environment with empty/reference evaluator controls; preserve
existing services/volumes and scarce root disk. Graphiti real server and native
eligible extraction/injection controls remain pending, not substituted by generic
graph storage or a resumed thread. All background inference must be captured.

Fresh exact-package OSV recheck returns no matches for existing50 Mem0/29
Graphiti/4 MCP graph packages; no whole-stack security clearance. Public source,
metadata and image receipts accompany protocol. Private inspection evidence lives
under work/security/knowledge-generalization-20261109/. No new packages, model
calls, image execution, global memory/provider changes or schedules; monitoring
remains paused. Original15-line HANDOVER and25-line Smallville user edits retained.

### 10 November: repository-memory first results and216-assignment accumulation study

Read docs/research/knowledge-accumulation-study.md latest checkpoint and private
work/security/repository-memory-20261110/active-continuation.json before acting.
WaveA eight assignments complete: strict exact-set0/2 each; post-hoc prescribed
tests1/2 each. Added passing regression tests explain3342 strict failures;2387
regressions are real. Mem0/Luna+5.63%,Graphiti/Luna+46.35% scenario inference
cost versus fresh, including maintenance; no quality benefit.84 processes and
200responses reconcile; separate native-background cancellation remains unknown.

Actual longitudinal001 PID559763/session88796 is running.216 sealed assignments
(36tasks x6arms), all36 empty/reference controls pass. Reservation003 preserves
exact36 membership, reorders by verified ancestry, separates cfn12,Click10+2,
attrs12 lineages.198 all-pair GitHub metadata comparisons; no cross-lineage/arm
experience. Fresh/raw/Mem0/Graphiti/persistent graph/reset graph; only own public
work accumulates; all generation precedes hidden grades. DO NOT edit files in
manifest.json, duplicate workers, retry started/uncertain calls or tune held-out
data. No longitudinal grade/learning outcome yet. External memory, no weights.

MCP editable graph implements evidence-linked versioned claims. Two real-server
tests and18 prior checks pass. Cheap preparation001/002 failed (enum omission,
literal end-token); retained without partial admission.003 supported native
output-schema passes. Native child-home seed ages naturally; thread-start-only
probe timedout with zero new model requests. New registered initialization003
produces actual phase1/settled phase2; fresh-thread004 exact-summary injection
is confirmed in an unmodified request, with supported cfn-lint/tox recall and no
file tools. Background accounting and coding efficacy remain pending.
Never manipulate native jobs/timestamps or normal personal memory.

Paper0.2 and repository-memory-wave-a-results.md record results and limits.
Smallville/TokenEconomizer/native supplemental repository comparisons remain
pending, not silently omitted. All maintenance/preparation/background inference
needs accounting; cash/quota unknown, local/parent overhead separate. Research
schedules stay paused. Unique /tmp captures/Git/source artifacts require verified
backup before cleanup; preserve services/volumes. Original user HANDOVER15lines,
Smallville25lines and inspect_memory_artifacts.py remain untouched/unstaged.


## Codex team knowledge scaling, 11 November 2026

The user authorizes sustained active-chat research on native Codex teams and
shared knowledge. Paper draft preceded inference in
`docs/paper/codex-team-knowledge/paper.md`; dated controls and local-provider
failures are in `preparation-results.md`. No schedules resumed. The supplied
knowledge-innovation-agents GitHub URL is inaccessible through Git and connector;
new work is in the existing TTGL `work` checkout.

Private root: `work/security/codex-team-knowledge-20261110/`. TinyDB standalone
feasibility passes independent source-only replay:200pass/1skip,244.42s,726995
reconciled native tokens; excluded from comparison. Sealed SimPy reference140pass
and base57fail; TinyDB reference200pass/1skip and baseimportfail. Runtime is a
declared Python3.11variant. Pinned dataset parquet equals all54viewerrows exactly.

The24-cell development scaling pilot is active:SimPy/TinyDB × native/notebook/
officialMCPmemory × total capacities1/2/4/8. One attempt/cell, randomized order;
30min,80sharedterminalcalls,4Mobservedordinarytoken threshold (in-flight/compaction
can exceed). Twelve evaluation libraries remain reserved and untouched. Sources
in `experiments/codex-team-knowledge-001/scaling-pilot-protocol-003.json` are frozen.
Do not edit those generation/replay/queue sources, restart a queue, or duplicate
started units. Current driver `continue_codex_team_scaling.py`, execsession80167,
logs `scaling-pilot-001/continuation-001.log`. Inspect actual checkpoint/completion/
continuation-stopped receipts before continuation. All original failures remain.

First cell SimPy/notebook/cap2 passes140tests in157.89s,969516tokens. Second
TinyDB/notebook/cap4 passes200/1skip in186.36s,1498884known tokens, but seven
communication-interrupted streams lack usage. The original queue stopped; all
per-thread account/usage/read estimates returnnull and read-only retrieval404
with a positive authenticated catalog control. Amendment003 continues only the
remaining22cells, preserving incomplete costs as lower bounds and total costs
null. No inference is repeated. Do not claim complete cost/rank incomplete cells.

Per-unit archives are lossless and byte-hash verified before owned raw files
are removed; authentication remains untouched. Original capture frames and exact
CAS objects are retained within units and archives. Use the new read-only
`analyze_codex_team_scaling.py` for archived evidence; raw rpc/actor paths may have
been archived. First analysis snapshot only covers the first complete cell.
The capture-only proxy on8452(session9626) writes under/tmp/native-capture-001
with full prefix `/tmp/ttgl-team-knowledge-20261110/`. Do not stop it during runs.
No Headroom transformations or global routing changes apply to study homes.

Local auxiliary services are stopped before comparison. Qwen0.6B schema
extraction passed3formats but strict1/3identifiers; Graphiti ingestion attempts
failed, including533.34s/9682localtokens in attempt002 with stock retries counted.
Cognee's original lock has confirmed advisory matches; updated resolution not
cleared/installed. Llama.cpp remains unexecuted/blocked. MCPmemory2.1.0 passes
eight-process storage and native four-agent visibility; no auxiliary LLM calls.
Existing services, credentials, historical studies and unrelated dirty files
remain preserved. Raw/private/security artifacts stay ignored.

Storage continuation: the pilot reached17completed assignments, then stopped
before the next inference at the128MiBworkspace reserve. Exact archived SQLite
WAL/SHM copies accounted for leftover space. Amendment004 verifies original
archive hashes and each database file hash, removes only those backed-up copies,
and continues the seven unstarted cells. Authentication remains untouched.
Current driver is `resume_codex_team_scaling.py`, execsession28367, log
`scaling-pilot-001/storage-continuation.log`; inspect its stopped/completion
receipts before acting. Protocol004adds only this storage continuation source;
generation/prompts/order/budgets/replay/accounting remain unchanged. All17database
compactions verified; free space recovered to250MiBbefore the next cell. No
model assignment was repeated. The installed native backend reportsv2 in child
metadata and offers the registered slot count in server guidance, despite the
CLIfeatureflagintent; report actual observed behavior rather than flag names.
Read-only analysis now distinguishes exact peer observation exposure from mere
memory writes; the first three MCPcoding cells have no observed peer reads.


### 11 November — coding-team development pilot complete

All 24 registered SimPy/TinyDB × native/notebook/official MCP memory × total
capacity1/2/4/8 assignments are complete, once each. Independent source-only
replay and artifact policy pass24/24; one parent turn fails despite a passing
sealed artifact. Protocol005 records a native-only final usage response missing
from the RPC delivery; auditv2 verifies the exact capture and cumulative prefix,
without changing the frozen grader. No pilot worker remains active. Completion:
`work/security/codex-team-knowledge-20261110/scaling-pilot-001/completion.json`.
Authoritative analysis is `scaling-analysis-final-002/analysis.json`. Public paper,
report, CSV, sanitized JSON and standalone figures live under
`docs/paper/codex-team-knowledge/`. No reserved-library model trials have run.

Native capacity8 uses four/five actual threads and averages31.323% less coding
run time than native1 on these two development libraries. Known inference cost
is already at least2.4458× the fully measured native1 controls. Quality is at a
ceiling. Only7cells have complete usage;17remain lower bounds,98interrupted
requests unknown. Known counters33,076,632tokens, >=260.226880Standard credits,
>=$10.4090752API-equivalent; actual total/subscription cash unknown. MCP publishes
91observations, but all4queries returnempty: no peer-observation retrieval is
observed. Do not turn publication or timing differences into learning evidence.

All24gzip archives were losslessly recompressed toXZ after exact uncompressed
Tar-byte comparison. Original archive receipts remain; recompression receipts
link old and new hashes. Reader supportsXZ; per-unit captures still present.
Storage is about93MiB free on workspace; /tmp has20GiB but is not a durable
replacement. A user storage-retention question is pending before larger runs.
Original failures, raw archives, credentials and unrelated dirty files retained.
Research schedules remain paused. Capture proxy8452 session9626 remains active.
Auxiliary LLM/embedding/Neo4j are stopped except new provider006 dtype diagnostic:
FP32 Qwen0.6B, unchanged second ingestion002 request and90s bound, session21373.
No dependency install or memory-core changes; previous failed attempts preserved.


### 11 November, 04:30 — reserved coding-team extension launched

Pilot24 remains complete with published report/figures. Local-provider work is
complete for the bounded candidates: Graphiti ingestion005 with Qwen0.6B
FP32-sharded/dynamicINT8 + localBGE + Neo4j finishes in88.2908s/twoLLMrequests,
3312input+212output=3524tokens but fails fact fidelity, returning an unrelated
Alice/Bob promotion fact. UnquantizedFP32 diagnostic006 retains the command;
startup failures007/008 have zero acceptedrequests and remain preserved. Cause
of SIGTERM is unresolved; do not claim OOM. All auxiliary services now stopped.
Cognee remains blocked, no coding score. See preparation-results.md updates.

Five original reserved libraries pass untouched reference admission on declared
AlpinePython3.11.18/25reviewedwheels (no lxml/Setuptools): WCWidth38pass1skip,
Cachetools215pass, Voluptuous149pass, IMAPClient267pass, Babel6700pass6skip.
Babel uses published2.14.0 CLDR data only,1014sealedfiles, no implementation.
All blank controls fail. OriginalPython314 and failednewercontrols retained.
MiniTorchreference fails211NotImplementedError; Chardet has a Hypothesis
counterexample; Portalocker multiprocessing/coveragefails. Deprecated/Marshmallow/
PyJWT security/dependencyblocked; Parsel XMLnativefindings unresolved. The
XML-bearing Python314testvenv must not execute further pending patchreview.
Raw review receipts/public-wheelassets live/tmp; compact admission receipts
are private under reserved-readiness-001/002. No candidate outcomes used to
select tasks. No replacements beyond original12reserved.

Registered80cells: addedMCPmemoryoff/on × generalexplicitknowledgeuseoff/on ×
capacity1/2/4/8 × fiveadmittedrepos, oneattempt each. Protocol/order/frozenhashes:
experiments/codex-team-knowledge-001/reserved-factorial-protocol-001.json.
Paperdesign: docs/paper/codex-team-knowledge/reserved-extension.md. Newprepare/
boundary code codex_team_coding_v2.py reuses original native run. Newreplay
codex_team_grade_v3.py restores in-package tests and immutabledata, requires
referencecollectioncount/skipceiling; newtests/generatedoutputs are excluded,
existingtest/config/data modifications separatelyflagged. Source-only quality
and normalparentcompletion distinct.13softwarechecks and threeactualzero-
inferencegrade witnesses pass (poisonedVoluptuoustests/Babeldata restored;
blankVoluptuousfails). Allfive native/containerboundaries pass beforeinference.
Do not edit frozen sources while queue active; originalpilot files unchanged.

Current queue: tools/usage-monitor/experiments/codex_team_reserved_queue.py,
execsession83749, root work/security/codex-team-knowledge-20261110/scaling-heldout-001.
First randomcell Cachetools/MCP/standard/cap1. Inspect started/stopped/checkpoints
before continuation, never restart a startedqueue or repeatuncertainmodelcalls.
Cost gaps prospectively retained as lowerbounds, no retries. Driver seals and
gradesended budget/stream artifacts; auditambiguity stops. Archives gzipverified,
SQLiteWALcompacted, exacttarXZrecompressedpercell. Source bases/control assets
in/tmp/ttgl-team-knowledge-20261110/reserved-sources-001 and manifest001.

Captureproxy oldsession9626 had stopped143 afterpilot; restartedreviewed
capture_proxy_native_routes.py on8452, execsession59028, NEWdestination
/tmp/ttgl-team-knowledge-20261110/native-capture-002. Keepthisproxyalive during
queue. Perunit captures durably retained by nativeaudit. No globalrouting/
Headroomchanges. Workspacefree recovered from93MiB to615MiB independently;
initialstoragequestion no longerblocks boundedrun. Hard128MiB gate before
newunit. Do not delete privateevidence or use/tmpforuniqueonlyretention without
userchoice if spacefailsagain. Researchschedules staypaused. No commits/pushyet;
userunrelateddirtyfilespreserved, HANDOVER itself has prioruserdirtycontent.


### 11 November — memory-aware multi-system team extension

User requests Mem0, Smallville, Graphiti/Luna and shared searchable agent logs,
with explicit memory awareness for every worker and a paper appendix. Read
`docs/research/team-memory-extension.md`. Separate 56-cell development protocol
is finalized before scored inference; original pilot/reserved sources untouched.
All four new backends and native parent/child reciprocal checks pass after
versioned Mem0 scoping, Graphiti episodic retrieval and Smallville empty-store
fixes; failed attempts preserved. 23 software checks and 14 gate receipts pass.
Queue `codex_team_memory_queue.py`, exec session73673, sole root
`work/security/codex-team-memory-extension-20261111/scored-001`, is active.
Inspect checkpoints/stopped/completion/processes; never restart/repeat a started
cell or edit frozen generation/evaluation/adapter files. Configuration and 65
source hashes: private `scoring-config-003.json`. First cell SimPy/notebook/cap1.
Own capture8452 exec45454 and Neo4j17687 exec67772 must stay alive during run.
Some mechanism transports have unknown usage; all completed native counters
reconcile, totals remain lower bounds where needed. Paper appendix has actual
hash-verified benchmark memory/failure/query excerpts and synthetic mechanism
examples. No new comparative coding result yet. Sources/runtime restored from
exact public pins in/tmp; durable private evidence stays workspace. 128MiB
pre-inference reserve. Preserve unrelated user changes; schedules stay paused.

Memory-extension scored checkpoint006: all six source-only artifacts pass;
five parents complete normally, Mem0/SimPy/cap4 stops at shared token threshold
with passing source. Sources/conditions unchanged. Actual log-arm cell003 has
12 nonempty searches, 11 with identifiable peer exposure, no full-record reads.
Mem0 cell005 has four full peer-record reads; Smallville006 has three and 11
Luna importance calls, zero natural reflection. This is interim development
mechanism evidence, not causal benefit or a matched-system conclusion. Unknown
transport usage retained. Public current/final report: memory-aware-results.md;
one zero-model completion publisher exec68722 waits on this exact queue PID.
No schedule or extra inference worker. See dedicated continuation doc.

Memory-extension continuation after security review: original queue102697/session73673
ended143 after sealed12. Additional native SBOM findings OSV-2026-1068 and
OSV-2025-219 match Pillow bundled codecs in original memory runtime. All12
source artifacts pass;11 normal parents. Original checkpoint12 creation was
signaled before write; zero-byte original preserved and record reconstructed
from sealed generation/grade/audit, then losslessly archived. Old attached
publisher68722 failed on partialcheckpoint; it is no longer active.

Read memory-aware-security-amendment-004.json and continuation-finalized-007.json.
Isolated FastEmbed0.9.1 text-only derivative under
/tmp/ttgl-team-memory-20261111/text-only-global-002 excludes all Pillow/image
artifacts. Fourteen text files exact, tokenizer AST unchanged, eight stored BGE
vectors exactly reproduced; four actual service startup/close checks pass with
zero remote calls. Original global runtime and frozen agent/engine sources
remain untouched.78 existing Python version queries zero matches; no whole-stack
clearance. New plotting/Pillow build candidates remain unexecuted.

Continuation005 had Docker startup timeout before any model intent.006 adopted
the owned sleep container and passed original boundaries, then hit an existing
log collision, still pre-model. Complete original preparation now preserved in
scored-001/preparation-history-013-005-006; both stop receipts and all absence
proofs remain. No started model call was repeated. Latest sole continuation:
continue_team_memory_text_runtime_v4.py, config scoring-config-007.json,
exec62793; exact registered prefix12, only untouched remaining44 fromcell013.
It writes continuation-003-started.json and cumulative checkpoints, with zero
automatic retries. Inspect actual started/stopped/completion and processes first.
146-or-fewer frozen source/import checks percell,11046 full runtime files checked
at launch and required again at final audit. Do not edit frozen sources while
active. Public docs/read-only nonfrozen finalization can change. Capture8452
exec45454 and own Neo4j17687 exec67772 stay alive. Scheduled research stayspaused.

Read-only analysis now verifies protocol prefix, sealed grades/audits, positive
deduplicated responses and null unknown totals; six new analysis and six
continuation checks pass,33 total team-memory checks. Public CSV includes
runtime strata. Finish all56, independently audit archives/runtime, update main
paper/appendix/results (not only progresslinks), then respond. Migration agent
prompt is docs/paper/codex-team-knowledge/PORTING_PROMPT.md. Preserve unrelated
user dirty files, especially earlier HANDOVER content and repository-memory work.

Memory-extension latest transport continuation008:19 confirmed model assignments
all pass prescribed source-only replay. Old controller268125/session62793 was
held and ended143 after two pre-thread timeouts in20/21. Their RPC traces show
only initialize and thread/start, with no turn/task input or owned model session;
22 was prepared but no native model process started. All three preparations and
old zero-counter checkpoint20/21 rows are preserved under
scored-001/pre-model-transport-history-008. Independent preparation-audit-008
proves the pre-model boundary from trace/source control flow, not zero counters.
Original actual model order remains20,21,22,...56. No started model call repeated.

Latest sole queue: continue_team_memory_text_runtime_v5.py, config
work/security/codex-team-memory-extension-20261111/scoring-config-008.json,
exec47320, PID384111, owner continuation-004-started.json. It retains prefix19
and attempts only37 originally uninvoked cells. Native StartupClient allows
120secs on ONE initialize/thread/start request; turn/start keeps original20s.
No prompt/model/algorithm/budget extension or request retry. A future failure
before recorded turn intent stops for audit instead of consuming later cells.
One live empty-thread startup probe and three transport checks pass with zero
task turns. Model invocation20 is now accepted; inspect live state for outcome.
145 source hashes percell,11046 runtime files atlaunch,20 gate receipts. Frozen
core sources and new analysis/client/queue source must not change while active.

One zero-model publication phase now waits on this exact queue PID: exec20053,
finish_team_memory_study.py, publication-phase-started-003.json. It cannot launch
models/restart queue. On actual56 completion it runs independent full archive/
runtime audit, five Pygal SVG figures and a factual main-paper/README/appendix
update in fresh processes. Then do editorial review, JSON/link checks, final
scope/commit review before responding. Prior publication phase002 canceled
without output on oldqueue change; earlier68722 failure remains preserved.

New read-only finalization code: finalize_team_memory_results.py (all archive
file/link hashes, broker operation seconds, finite setup markers, roles and
peer exposure), inspect_team_official_memory.py, update_team_memory_paper.py.
Pygal3.1.3/importlib-metadata8.7.1/zipp3.23.0 reviewed as pure Python, installed
only in/tmp/ttgl-team-memory-20261111/pygal-runtime-002 with no scripts/plugins/
native/image extras. Five private SYNTHETIC render fixtures pass; no scored plot
before all56. Reviewed lock memory-aware-svg-runtime-002.lock. Matplotlib/Pillow
and new Pillow build alternatives still unexecuted/blocked. Raw original
Pillow runtime left untouched; generation uses text-only FastEmbed002.

Paper appendix now includes scored Graphiti baseline failure and retained MyPy
verification caveat with original archived member hash, plus conditional Cognee
RCE/advisory interpretation. Port prompt and REPRODUCING.md added. Main paper
has methods4.5; substantive final abstract/results/discussion/conclusion are
gated on completion/audit. Preserve original24pilot and interrupted80 separately.
Capture8452 exec45454 and own Neo4j17687 exec67772 remain needed during models.
No schedules resumed. Preserve unrelated dirty user files and prior HANDOVER
content. Continue active-chat work until56 end and final publication/review.

Latest memory extension009:20 CONFIRMED model assignments complete/pass. New21
preparation failed on the old dead Unix socket from its preserved earlier
startup, before native process/turn/maintenance intent. Whole failed preparation
and rootstop are in pre-model-service-history-009. Socket guard removes only
exact assignment-derived owned socket pathname with no kernel endpoint,
ECONNREFUSED, unchanged inode; preserves active/bound endpoints and regularfiles.
Four guard checks pass. Frozen original broker/algorithms/model policy untouched.

Sole latest queue: continue_team_memory_text_runtime_v6.py, config
scoring-config-009.json, exec31102, PID416899, owner continuation-005-started.json.
Resumes prefix20 with36 originally uninvoked models. Actual task21 nowaccepted;
no model turn ever repeated. Entry uses StartupClient120secs only on initialize/
thread.start and new service bootstrapv2 dead-socket guard.150 frozen sources,
11046 runtime files atlaunch,21 gates. Inspect current stopped/completion/
checkpoints/processes; do not duplicate or edit frozen source. Earlier queue
384111/47320 stopped pre-model21 and publisher20053 stopped003 accurately; no
pending old worker. New attached zero-model publisher is publicationphase004,
finish_team_memory_study.py, binds owner005/config009; see actual execsession
from activechat. It must finish before final editorial edits to avoid overwrites.

Public reports represent20 confirmed modelcells; historical pre-model rows20/21
are separatelypreserved with source/RPC proof, not discarded coding failures.
Quality is conditional on actual task-model start, not first-launch reliability.
All pre-model overhead remains separate/unpriced; do not infer cashzero.
A pending optional asynchronous scope question asks whether user also wants
the separate older80-run reservation; current authorized continuation remains56
unless usersteers. Scheduled work stillpaused; activechatcontinues.

## 12 November 2026 — requested memory-study pickup record

Read [team-memory-handoff-20261112.md](team-memory-handoff-20261112.md) first.
The user explicitly selected only the active56-run comparison and paper; the
older interrupted80-run reservation stays untouched. Snapshot00:03UTC:
38 verified,37 passing source artifacts,36 normal parents; actual039 submitted.
Existing queue598104 (`continue_team_memory_text_runtime_v8.py`, config011,
owner007) and zero-model publication598863 (phase006) are left running.
Do not duplicate them or repeat any started/uncertain call. Inspect actual
processes/checkpoints/stop/completion receipts before acting.

The handoff records all operational amendments, the retained Mem0/capacity8
failure, two provider-only completions/native transcript gaps, restored own
services after daemon restart, interim matched performance, frozen sources,
private evidence boundaries and exact final publication/editorial/port-manifest
steps. All81 focused software checks pass at handoff. Research schedules remain
paused; no recurring work was created. Unrelated dirty files and prior HANDOVER
content remain preserved. No commit/push yet; many required study files are
untracked. The study and final paper update are not yet finished.

## 15 November 2026 — repository documentation, startup and space recovery

The user requested latest `work`, TTGL startup, setup/README, a complete research
index, and commit/push of existing changes; later also authorized safe space
cleanup. Pulled origin/work fast-forward to d777f62 without stashing or replacing
local work. Added root SETUP.md, docs/EXPERIMENTS.md, docs/EXPERIMENT-ARTIFACTS.md
and docs/PAPERS.md; replaced stale root README with app/research entry points.
The artifact inventory links all 133 public usage-monitor study files, including
41 result/analysis JSON files, plus routing collections and team-paper evidence.
No new model trial, queue or scheduled monitoring was started.

Memory study inspection found no generation/publication worker and no completion
receipt. Actual latest checkpoint039 has 39 assignments, 38 passing sources and
37 normal parents. The read-only analyzer validates those recorded cells and
refreshes public JSON/CSV/Markdown as **incomplete, 39/56**. Earlier 38-cell public
files are preserved privately under maintenance/memory-report-before-refresh-
20261115. Failed Mem0 grade, lower cost bounds, historical amendments, the
interrupted 80-cell reservation and untouched suffix remain preserved. Do not
infer permission to repeat uncertain calls or resume the study from this startup.

The standalone stdlib workspace is running on loopback8766 with the existing
workspace database/native histories and saved capture root. Its HTTP root
returns200. Private startup log: langfuse-stack/workspace-start-20261115.log.
It does not start the capture proxy, model inference or Langfuse ingestion.
Full stack could not start: restored Docker container records/named volumes
remain, but image inventory is empty and existing container start returns
`RWLayer ... is unexpectedly nil`. Doctor also reports CLI0.169.0 versus tested
0.166.0. No images downloaded, containers removed, volumes pruned or normal
provider configuration changed. Preserve all database volumes during recovery.

Safe cleanup removed only five superseded, unreferenced Copilot binary cache
versions1.0.105–109, retaining1.0.112 and the active VSCode runtime. `/proc`
command/maps/exe/cwd checks found no references. Free space rose by1,307,615,232
bytes (about1.22GiB), to about1.8GiB. Dated path/size/before/after receipt is
private at work/security/maintenance/space-cleanup-20261115.json. Experiment
evidence, native histories, credentials and database volumes were not deleted.

Validation: 249 unique stdlib software tests pass, six optional tests skip
(123 Observatory,74 team,24 Langfuse,11 original team,23 repository tests;
123 includes the six skips). Two changed/relevant JS files pass node syntax
checks. Changed Python ASTs and29 JSON documents parse, all local Markdown link
targets resolve, git whitespace check passes, and exact local credential values
are absent from public changes. Native-model inference was not used for checks.
The team source-port inventory is refreshed after the last paper edits; raw
private state stays ignored. Research schedules remain paused.

## 15 November 2026 — user objective: effective 100-agent swarms

The user now explicitly wants to understand running 100 agents in parallel and
which knowledge-sharing, monitoring and communication mechanisms improve scale.
This authorizes the literature/research direction; it is not an instruction to
launch 100 workers, install a harness or resume any old queue/schedule.

Read [agent-swarms-literature-review.md](agent-swarms-literature-review.md) and
[agent-swarms-sources.json](agent-swarms-sources.json). The focused review covers
20 primary papers/first-party reports through15November, including Agensh's
large shared-repository organization, November's parallel-small-team search
result, CAID, native concurrency, ParallACT, DeLM, SEPM and monitoring/triage.
Different workloads support different organizations; no universal topology or
economical100-agent result is asserted. Current source licenses/activity are
checked read-only; unavailable code and unresolved reuse permission are explicit.

Recommended next research separates shared-artifact integration from competing
solutions selected by an executable scorer. Compare decentralized workers,
modular teams and independent attempts under matched information/resources;
measure actual concurrent model/tool work, verified outcomes, total inference,
integration queues and evidence publication/retrieval/use. The proposed stepped
study is not yet registered or launched. Existing frozen sources, failed runs,
39/56 memory extension and reserved validation stay unchanged. No dependencies
installed, new model trials started or schedules enabled by this review.

## 15 November 2026 — benchmark-driven observability improvement loop

The user proposes running an out-of-the-box agent on benchmark tasks, collecting
logs, using a small model to tag/categorize/analyze its process, making and applying
suggestions, and measuring improvement across repeated rounds: quality, cost,
wall time, failure detection, tool utility and ability to run more work in parallel.
This is now the central proposed experiment; swarm organization is a later
intervention/scaling axis rather than the required starting point.

Read [observability-improvement-study.md](observability-improvement-study.md).
The design separates stock-agent baseline, passive monitoring, audited trace
interpretations, concrete candidates, controlled trial measurements and decisions.
It includes development/selection/final-evaluation boundaries, total optimizer
expense, labeler audit, component controls and a staged concurrency comparison.
GEPA/ACE/ADAS/AFlow are close precedents; no broad novelty claim or new optimizer
implementation is assumed. Prior TTGL trial successes and failures remain prior
development evidence, not newly run benchmark results.

No task suite/split, inference/search budget or final acceptance rule is frozen by
this design. No model trials, installations, global routing changes or scheduled
work were started. Select fresh tasks only after auditing old reservations and
queues; preserve frozen sources and uncertain attempts. Existing app lifecycle
and failed/incomplete study artifacts remain unchanged.

## 15 November 2026 — processor and analyst are separate roles

User clarification: the analyst can be a large model. Simple log processing,
task/subtask organization, candidate failure tagging and data mining should make
the logs easy for that analyst to query and understand. Do not require one small
model to do both preprocessing and deep diagnosis/intervention design.

The proposed study now separates deterministic measured facts, cheaper semantic
organization, queryable evidence and capable analyst investigation. Tool exit,
agent completion assertion, visible check result and independent task grade are
different fields. Cheap labels are source-linked interpretations; missing data
stay unknown and original evidence remains accessible. The analyst can challenge
labels and inspect counterexamples before proposing changes.

Evaluate the same analyst with basic indexes versus enriched representation,
keeping raw access, and meter processing and analyst overhead separately. A
small-versus-large analyst comparison is optional; large analysis is permitted
in the main design. No new model trials or executable pipeline were started by
this clarification; frozen studies and paused schedules remain unchanged.

## 15 November 2026 — useful evidence tools before analyst experiments

Latest steering is to build a useful tool, pull latest and deploy, before asking
what the analyst can improve. The evidence explorer at `/investigate` and shared
read-only `query_trace_index` MCP/CLI/HTTP query contract are implemented. See
[the operating guide](../EVIDENCE-EXPLORER.md). They reuse the existing SQLite
ledger and input/output fingerprints; no new dependencies, model calls or
analytics service were added.

Queries cover whole-turn cohorts, literal search, exact model/tool/status filters,
time boundaries, unsuccessful/unknown tool signals, stable ranked pagination,
repeated inputs/outputs and raw source-step drill-down. Existing interpreted
task/subtask history remains separate, with its existing freshness contract.
Native completion markers and task status are not independent grades. Repetition
is an investigation lead, not inferred waste, retry count or task failure. Runtime
stays recorded process/tool time, not blocking time or full-task latency.

Raw retrieval now uses the ingester's session/source map and rejects mismatched
native identity, changed output hashes and changed usage records. HTTP raw reads
support bounded character pagination. The retained corpus read-only smoke covered
about 1,600 turns/13,800 events; individual query views took 0.15–0.37 seconds in
that local check. This is query behavior, not an agent-performance improvement.

Validation: 219 observability checks, 195 passed and 24 optional checks skipped;
JavaScript syntax/module-graph/four-renderer smoke passed. The new browser workflow
is implemented but was not executed because reviewed Playwright/Chromium is absent
here; no layout/browser-success claim. No benchmark/model trials or automatic
optimization were launched. Frozen artifacts and paused research schedules remain
unchanged. Existing MCP processes must reconnect to discover tool version 1.4.0.
Final deployment review adds an exact operation filter for fingerprint drill-down,
so different tools producing identical outputs cannot expand the selected group.

## 15 November 2026 — app latency, process outcomes and bulk history analysis

User reports app slowness and explicitly requests pagination, task → subtask → step
hierarchy, categories/results (including failed/done/dead ends), user-intervention
detection, tool-usage analytics and a button to analyze all retained activity.
Read [BULK-ANALYSIS.md](../BULK-ANALYSIS.md). Upstream's Observatory branding and
browser-cleanup fixes were rebased into this work; legacy identifiers stay compatible.

Profiling identified repeated full shell parsing, duplicate tool classification
and a roughly 9 MB initial overview response. Compound scripts now bypass full
shell tokenization; an overview reuses tool labels. Dashboard/task/source-step/bulk
lists use server pages, prompts load on drill-down, and HTTP supports gzip. Observed
local overview: roughly 6.0 → 2.30–2.37 seconds, 454 KB JSON / 128 KB compressed.
Task activity: about 2.03 seconds / 52 KB compressed / 20 turn rows. These are app
measurements, not coding-task cost, accuracy or speed improvements.

Process protocol `task-process-v1` reuses the existing small-model analyzer, native
transport, source aliases, validation and metering. Versioned task/subtask outcomes,
intervention evidence and runtime roles are interpretations, separate from native
facts, independent grades and explicit recorded task acceptance. Current source-
matching process labels feed tool categories; explicit prior agent annotations
retain precedence. Unknown evidence stays unknown. Long-task excerpt/block limits
are recorded; event coverage does not mean every raw character was read.

The user-authorized finite batch is RUNNING:
`73e6f3d334f6429daef5de6f3fc97065`, worker PID 159045, app PID 158547.
It freezes 1,246 indexed tasks / 14,020 native events, with two concurrent Luna
analyses and zero automatic retries. At an early checkpoint, 21 completed, 2 ran,
1,223 remained pending, and no failed attempts were recorded. All observed completed
calls report positive native token usage; accrued analysis overhead was 435,025
known tokens, with the two active calls' usage still unknown. These counts are
interim; inspect `/api/bulk-analysis` or private DB state for current progress.
Do not duplicate or silently replay this queue. Frozen source hashes are in its
private protocol manifest (`bulk_analysis.py`, `task_history.py`, `process_analysis.py`).

The worker is separate from the web process and holds an exclusive owner lock.
Its status and attempt pages are in the top-bar **Bulk analysis** dialog. Stop
finishes active calls before leaving pending work. Failures/uncertain calls remain
retained, and three consecutive failures stop further dispatch. New source activity
after the frozen snapshot remains separate. Reused successful analyses add no new
batch overhead; historical attempts and measurements remain intact. No research
generation, benchmark reruns, installations or recurring inference were started.
Research schedules remain paused.

Validation: the merged observability suite passed 232 checks (208 passed, 24 optional
skips), plus focused accounting checks and an actual JavaScript module/event smoke
for server-page navigation and page-size changes. Real deployed queries, raw assets,
worker progress, process publication and positive model metering were checked.
Browser QA remains unexecuted here because reviewed Playwright/Chromium is absent.

## 15 November 2026 — browser validation and merged pagination controls

The user explicitly requires functional validation before declaring completion.
The earlier browser-validation gap is now closed for the local Observatory flows:
217 non-browser unit/API checks and 12 actual Firefox workflow cases pass on the
merged sources. The 25 legacy optional Playwright/Chromium cases were not executed;
Firefox covers the changed workflows, rather than treating those skips as passes.
Coverage includes all 17 main navigation views at 1440/768/390 CSS pixels, global
pagination/search/numeric filters/sorting, saved columns/theme/rates/knowledge links,
task → subtask → source steps, raw evidence, chart drill-downs, process maps, live
notes/pause/resume, project/rule/change mutations, and bulk start/stop/progress.
An additional populated 28-task fixture exercises 13 reference routes on desktop
and mobile and loads retained image bytes in the gallery and full-image dialog.
Browser mutations use disposable stores; model invocation is blocked in fixtures.

The first pass found removed table controls and progress polling that could stop
permanently after table focus. Controls now apply to the full server collection
before slicing, and polling resumes after focus leaves the table. Unknown numeric
values stay last when sorting and never become zero in numeric filters. Global
measurements remain independent of table filters. A foreign-input guard and focus
restoration preserve shared-list interactions.

Upstream `b2b06e4` arrived during validation. Its layout, retained-image and shared
`record_collection.py` query changes are integrated; the temporary competing query
implementation was removed. The running analyzer's three generation source files
match the original batch manifest hashes. The new read-only
`bulk_analysis_views.py` contains the upstream queue-table projection so adopting
that UI does not change the frozen `bulk_analysis.py` generation module. Preserve
this boundary while batch `73e6f3d334f6429daef5de6f3fc97065` is active.

Firefox 160.0 and geckodriver 0.37.1 run in a separate unprivileged Alpine native
runtime. All 142 pinned package signatures/control hashes/data hashes were checked
before extraction; OSV and vendor security metadata showed no candidate findings.
Maintainer scripts were retained and not executed. The pre-execution receipt and
remaining provenance limitations are private under
`work/security/maintenance/browser-validation-20261115/`. Confirmed findings blocked
the considered Playwright bundles and host-library browser alternatives. No app
runtime dependency or model configuration was installed/changed for browser QA.
Absence of findings is not a guarantee of vulnerability-free software.

The web process was restarted as PID 285140 after an SQLite online backup; original
bulk worker PID 159045 continued. At the deployment checkpoint, 642 analyses had
completed, one had failed, two were running and 601 were pending. The failed attempt
used an unexpected tool: its result was rejected, its 31,355 reported tokens were
retained and it was not retried. Inspect current queue state for later counts.
The external Langfuse UI remains outside this validation: its previously restored
Docker stack is unavailable, with database volumes preserved. Research schedules
remain paused, and no extra model trials or duplicate workers were launched.

Post-restart read-only Firefox validation passed against the retained live history:
all 17 main routes loaded without JavaScript errors or failed app/API resources,
and deployed next-page/page-size/sort controls, the active bulk-progress dialog,
and selected 768/390-pixel layouts passed. The start button remained disabled for
the existing active batch. Screenshots, timings and route records are in the same
private validation receipt directory. Commit `81a0755` integrates the validated
merged application; the original worker was not restarted.

## 15 November 2026 — table value context filters

Right-clicking a shared table's data value now offers **Show matching** and
**Filter out**. This reuses the existing native menu, shared renderer and full-
cohort server query implementation; no dependency was added. Exact typed filters
keep null/unknown separate from numeric zero, boolean false and the literal text
“Unknown”. Column filters expose the active expression for editing/clearing;
other search/sort/filter state remains in place, with pagination reset to page one.
Server-side filters apply before slicing and do not alter cohort measurements.

The menu also works inside modal dialogs, uses the shared keyboard controls,
restores focus on Escape, and can open through Shift+F10 from a focused cell.
Editable controls retain their native context menu. A manual native popover avoids
the original right-button release immediately dismissing the new menu; outside
pointer interaction and Escape dismiss it explicitly.

Validation: 258 checks discovered, 233 passed, 25 legacy optional Chromium checks
skipped. All 15 Firefox workflows passed, including three new cases using actual
right-button pointer actions, exact inclusion/exclusion, unknown/zero handling,
keyboard dismissal/opening, local and full-cohort remote tables, persisted filters,
and filtering inside a modal. Existing chart, tool, hierarchy, bulk, responsive,
settings and mutation flows also passed. A test-driver timing race was corrected
by waiting for select-triggered navigation before clicking the next control.
Raw logs and screenshots remain private under the value-filter maintenance receipt.
The active finite bulk queue and its frozen generation sources remain untouched.

## 15 November 2026 — compact top scope controls

Project/workspace/range selectors now occupy one compact, horizontally scrollable
row above the page title. The shared filter form is moved intact so its existing
submit handlers stay attached. On mobile, the range segments become a keyboard-
accessible native dropdown. Work-search filters and legacy scope selectors use the
same top placement. Filter rows measure at most 48 CSS pixels at tested widths.

The mount hook runs only for the current load epoch, clears obsolete scope forms
on navigation, and preserves focused inputs/carets. A delayed-response fixture
verifies that a draft search survives a prior request completing after the move.
Range, project and workspace changes, URL persistence, and mobile filtering pass.
Validation: 259 checks discovered; 234 pass, including all 16 Firefox workflows;
25 legacy optional Chromium checks remain skipped. The existing 17-view navigation
check also asserts compact row height and placement at 1440/768/390 CSS pixels.

These are static HTML/JS/CSS updates served directly by the existing app. No new
dependency, backend migration, web restart, model call or queue worker was needed.
Research schedules and the active analyzer's generation source files stay unchanged.

A final layout check removed an inherited 120-pixel range-label minimum and input
flex growth that wasted mobile width. The three primary selectors and Apply now
fit together at 390 pixels. Both layout/navigation and filter/draft workflows were
rechecked after this CSS adjustment, including an explicit visible-Apply assertion.

## 17 November 2026 — experience routing implementation checkpoint

The new additive experience/delegation implementation is **unfinished**. Resume at
[experience-routing-implementation-status.md](experience-routing-implementation-status.md)
and the preserved [full user plan](experience-routing-plan.md). That checkpoint
records completed modules, validation receipts, outstanding gaps, applied immutable
migrations, processes, storage policy and exact next commands. New experiment
registration: `experiments/experience-routing-001`; model execution remains disabled.
No new scored model trials or benchmark reservations; scheduled monitoring stays paused.
The user requested committing/pushing all work before pausing. Preserve this checkpoint
and continue from it rather than restarting the feature or repeating any retained call.

## 18 November 2026 — experience routing continuation

Pulled `cdd00e2` and continued the implementation without model execution or new
installs. Runtime failure retention, partial usage accounting, separate actual and
shared-planner budgets, bounded replanning, first-party verification ownership,
source-bound subscription reconciliation and exact-node replay were strengthened.
All four replay adapter conditions run through synthetic transport. Validation:
48 Python tests, 82 web/database tests, 5 targeted subscription regressions,
TypeScript and production build pass. Native calls and new benchmark grades remain
zero. Migration 008 is additive; prior migrations/studies remain unchanged.

Resume at [the updated implementation status](experience-routing-implementation-status.md)
and `results/experience-routing-001/software-validation-20261118.json`. Model
execution stays disabled until native actor/MCP, corpus/audit, immutable source/model/
rate pins, budgets and pristine control gates qualify. Keep source histories and
uncertain attempts intact; scheduled monitoring remains paused.

## 18 November 2026 — experiment summary and pnpm assessment

Added a plain-language experiment summary to the current
[implementation checkpoint](experience-routing-implementation-status.md).
No native/model trials were started. Reviewed pnpm 10.34.9, 11.28.12, 12.21.0,
11.28.13 and 12.22.0 without executing their code. All inspected candidates contain
confirmed advisory matches; notably `picomatch` 4.0.7 in the current 11/12 packages
is affected by high-severity GHSA-fc5q-39xc-vjpf. Registry archive integrity and
registry signatures were verified, but this does not remove those findings.
The [dated assessment](../security/pnpm-assessment-20261118.json) records coverage
limits and the blocked migration. A fresh npm advisory API check of the existing
220-entry application graph returned zero findings. Active package manifests,
locks, installed dependencies, frozen workers and environment routing are unchanged.
Review a patched pnpm graph before importing the lock and adopting pnpm; do not
silently use the preinstalled manager or waive confirmed findings.

## 18 November 2026 — RSI-Router Luna/Sol implementation handover

The user requested a detailed coding-agent specification for reproducing
RSI-Router with Luna/Sol, including benchmarks and a Pareto comparison. Start at
[rsi-router-luna-sol-spec.md](rsi-router-luna-sol-spec.md). It defines a separate
proposed `rsi-luna-sol-001` registration; no executable registration, new task
reservation, dependency installation or model invocation was created in this step.

The first gate is a host-owned one-action loop with pre-action Luna identification,
qualified subscription-bound switching and common context across all conditions.
The old large-plan/node delegation runner is not the same treatment. Reuse its
transport, retention, accounting and evaluator boundaries without editing frozen
generation sources. The proposed sequence is native microqualification, an 8/8
development pilot, 32/32 main development and an eligibility/budget/precision-gated
100-task held-out SWE-bench Verified study. Terminal-Bench 2.0 and corrected 2.1
are separate profiles with cross-version exclusions. All volumes are planned,
not automatic launch authorization or claims that enough eligible tasks remain.

The spec includes eight conditions, validation-only representative selection,
paired skill masking, optimizer and amortized accounting, unknown/failed-attempt
retention, strict source/subscription identity, test-feedback isolation, proposed
modules/CLI, required tests and milestone gates. Additional Observatory experience
retrieval remains a later controlled extension. Implement model-free preparation
first; resolve actual runtime/security/source/budget gates before enabling finite
native stages. This handover does not change paused research schedules.

## 18 November 2026 — prioritize model-led delegation

The user prefers relying more on the model. The preferred implementation path is
now [model-led Codex delegation](model-led-delegation-spec.md): a native primary
chooses subtasks, context, delegation and integration; bounded workers execute
their own tool loops. Experience and earlier outcomes inform model judgment.
The host enforces scope, identity, budgets, isolation and retained evidence.
Default Luna workers return needs-parent on failure; no hidden Sol fallback.

Keep the per-action RSI specification as a separate comparison, rather than
calling this a faithful RSI reproduction. The supplement defines the proposed
MCP surface, autonomous worker lifecycle, cache considerations, native-harness
controls and first fixture/native gates. It creates no executable registration,
new dependency, model call or task reservation. Existing frozen sources,
subscription binding, local S3 policy and paused schedules remain intact.

## 18 November 2026 — implement tool routing with action similarity and recency

Latest user steering authorizes implementation and a run, and specifies tool-owned
routing based on cheaper-model availability, similar past actions and experience
recency. The primary still chooses bounded work and integrates results. Start at
[the registration](../../experiments/model-led-delegation-001/README.md) and
[dated result/readiness checkpoint](../../results/model-led-delegation-001/README.md).

New `src/ttgl/model_delegation/` adds strict source-scoped availability, lexical/
category/action similarity, weighted positive/negative outcomes with independent
parent deduplication, exponential verified-execution age decay, immutable decision
receipts and fixed worker packets across age ablations. New MCP tools expose
route, async delegate, poll and cancellation requests. One active worker/four-job
queue; no implicit Sol fallback, uncertain retry or budget reset after restart.
Active cancellation may complete the bounded native call; do not claim immediate
termination. Native adapter reuses existing retained Codex/Docker/checkpoint/
verification/accounting code through an exact enabled freeze; no old frozen
generation module or dependency lock was changed. CLI route-only is the default.

All **22 new tests and 48 shared experience tests pass**. The worker adapter was
exercised with synthetic transport editing real temporary source and running
public checks, not actual Luna/Sol. A registered retrospective leave-one-task-out
replay ran over eleven retained paired outcomes, verifying both native manifest
and official grade hashes: parent 9/11; always-cheap 7/11; both evidence policies
retain all work with parent and therefore yield 9/11. No recency advantage or
live delegation saving is established. Age uses completion-time proxies in this
diagnostic and original grade-publication chronology is not inferred.

Native preflight remains blocked: managed Codex auth has no account ID, so the
required canonical collector subscription cannot be verified; no qualified
coding actor/native stage/corpus/capability/budget/control freeze is installed.
No new model call, task reservation, dependency install or UI change occurred.
The user wants a real experiment; this is **not complete** until native gates
qualify and finite parent-plus-worker attempts run with independent grading.
Continue on the registered authenticated collector host; preserve historical
studies and keep unknown/started attempts unreplayed. Private evidence is in
`work/security/model-led-delegation-20261118/`; public receipt records exact
software source hashes and the remaining gaps. Research schedules remain paused.

## 18 November 2026 — typed subtasks, grounding and model-specific successes

The user adds subtask similarity, guiding/grounding experience and whether the
cheaper model itself succeeded before. Current native registration is
[protocol-002.json](../../experiments/model-led-delegation-001/protocol-002.json).
V2 requires typed subtask/goal/constraint/action matching. Whole-task replay
proxies are explicitly restricted to the retrospective simulation profile.

Routing distinguishes independent cheaper-model completion, completion with
versioned retrieved guidance, teacher examples and expert/human/unknown help.
Only verified public integrated outcomes attributed to the actual cheaper
executor support its competence estimate. Guided success requires a retained
context reference and the matching currently applicable guidance fitting in the
worker packet. Procedures contain preconditions, acceptance criteria and linked
source checks. Teacher guidance can inform a bounded trial but never counts as
student success; known guided failures are retained even if old guidance is absent.
Raw exposure is not a causal claim that the worker used or benefited from advice.

The autonomous adapter now delivers the grounded procedure and provenance; parent
MCP previews stay compact. Thirty delegation tests pass, including a real source
edit/check with synthetic transport verifying teacher guidance reaches the worker.
New source hashes/receipt are separately versioned; earlier receipts and replay
results are preserved. No dependency, frozen legacy source, native model call or
fresh benchmark assignment changed. Original native account/actor/integration
qualification gaps remain; do not declare the live experiment complete.

## 18 November 2026 — connect the experiment to knowledge accumulation/generalization

The user's topic is knowledge accumulation and generalization accelerating
effective innovation outcomes. They favor an RSI-inspired study using templates,
workflows and experience to improve cheaper-model capability, with the existing
Codex harness and a subset of the paper's benchmarks. Start at
[knowledge-accumulation-codex-study.md](knowledge-accumulation-codex-study.md) and
[protocol-003.json](../../experiments/model-led-delegation-001/protocol-003.json).

The main factor is nested construction knowledge (0/4/8/12 task prefixes), tested
on unseen issue/fix lineages with Luna, Sol and the model-led routed system given
matched library access. Proposed pilot: 12 construction, 12 development, 32 fresh
SWE-bench Verified evaluation tasks; all IDs/budgets/precision remain unresolved.
Thirty-two tasks at twelve system/snapshot cells imply 384 single-repeat episodes,
plus construction and qualification, not an automatic launch. Recency is a small
secondary comparison, not a replacement for measuring knowledge transfer.

Keep frozen-prefix learning curves distinct from later online accumulation. All
test cells freeze before test feedback; no evaluated result publishes into the
construction library. Coding effectiveness/time/resource measures operationalize
technical problem-solving, not verified originality or commercial innovation.
Reuse native Codex/tool/official benchmark infrastructure; an official RSI code
release remains unlocated. The separately inspected Apache-licensed SkillOrchestra
source is an optional reuse candidate, not a change to QA benchmarks or a new
executed dependency. No new model run/install/reservation occurred in this update;
the existing native source-account, actor and parent integration gaps remain.

Follow-up: user explicitly requires Luna/Sol and other-router comparisons and
asks about novelty. The same proposed (unfrozen) protocol003 now includes random/
mixture, public-check cascade, static subtask mapping, a real released task-router
candidate and close skill-aware prior-method adaptations. Select tradeoff points
on development only; compare the union of baseline points including the endpoint
mixture envelope. Missing/incompatible baselines limit claims. The 384 core
episodes exclude this added comparison suite; expanded assignments/budgets remain
unresolved before any test call. RSI and SkillOrchestra already cover experience/
skill routing, so Luna/Sol/Codex substitution is replication, not automatic method
novelty. Candidate contribution is controlled accumulation/transfer, recency and
full amortized-cost evidence; no positive frontier result is promised.

## 18 November 2026 — our router against released baselines; RSI related work only

Latest explicit user decision supersedes the RSI reproduction direction: implement
our own Observatory router and compare it with Luna, Sol, FrugalGPT and RouteLLM.
The current proposal is
[protocol004](../../experiments/model-led-delegation-001/protocol-004.json);
protocol003 is preserved. The former RSI handover has an explicit inactive notice,
and the current study/index/implementation handover follow the new direction.

[Baseline contracts](router-baselines-codex.md) distinguish FrugalGPT's learned
quality cascade from a simple public-check fallback and require a real released
RouteLLM variant with Luna/Sol development calibration. Read-only source/README
inspection confirms public Apache-2.0 repositories for both; upstream last pushes
reported February2025 and August2024 respectively. No package/model/encoder was
installed or executed. API-key/default embedding paths are not authorized by the
baseline choice; qualify a compatible reviewed local feature path and document
all coding-episode/native transport adaptations. Small proposed training sets may
be insufficient; assess on development before freezing the complete campaign.

Luna/Sol-only, both required named routers and our method need equal eligible
knowledge, tools, total caps and grading. Simple random/mixture, fixed subtask
mapping and public-check cascade remain controls; SkillOrchestra is optional.
RSI is not a runnable comparator. No change to historical results, native gates,
task reservations, paused schedules or zero new model-call status. Documentation
and protocol validation do not establish adapter compatibility or model quality.

## 18 November 2026 — native implementation and benchmark gates in progress

Active-chat continuation pulled `work` to `d26b6dc`. New native accumulation,
common-context campaign, source-bound isolated actor, released-baseline adapters,
immutable invocation admission, exact loopback S3 retention/restoration and
base-plus-delta candidate replay are implemented in `src/ttgl/model_delegation`.
The existing source subscription is available. No schedules were resumed.

Private evidence root:
`work/security/model-led-delegation-20261118/continuation-001/`.
Read actual completion/stopped records before continuation; never repeat started
or uncertain assignments. Seven completed metered native CLI invocations precede
the benchmark pair: transport006, coding007, failed handoff008 and successful
required handoff009. Their measured token subtotal is355756, excluding unknown
startup005 and this managed chat/implementation overhead. Required handoff009 is
an empty-memory always-cheap mechanism diagnostic, not autonomous routing,
benchmark quality or economic benefit. Original failures are preserved.

Full original evaluator dependency graph remains blocked by confirmed findings.
A reduced original grader/parser/TestSpec namespace subset with unidiff1.0.1,
reviewed patched Alpine actor and pure mpmath1.4.1 is qualified instead. This is a
patched runtime/host-test-setup adaptation, **not the full upstream Docker image
or CLI**. Original scripts' test-command body and official parser are retained.
See `docs/security/router-evaluator-20261118.json` and
`docs/security/router-reduced-runtime-20261118.json`. Local classifier wheels'
known bundled GCC runtime findings were replaced with reviewed fixed vendor
payloads before import. Synthetic released RouteLLM/FrugalGPT core and persistent
process fixtures pass; these are not trained benchmark baseline results.

Benchmark preparation011–013 failed before model invocation (dependency/mode/
noexec boundary). Preparation014 passes own empty/reference controls for the
qualification-only case. Actor testbed explicitly permits tracked script
execution, while remaining offline, unprivileged, read-only outside ephemeral
source/tmp and without host/evaluator mounts. No frozen historical source changed.

**Currently registered:** `benchmark-qualification-015.json`, at most two fresh
native invocations, Luna then Sol, equal empty knowledge/public tools/caps,
private `benchmark-pair-015`. Source hashes and exact frozen archive are retained
before inference. Check `pair-completion.json` and per-model completion/stopped
records. First Luna result has passing public check/scope and256607 native tokens;
Sol and independent post-pair grading were still pending when this entry was
written. Do not mistake this interim public check for an official score.
Exclude this qualification task from subsequent transfer/calibration.

`reservation-016.json` reserves12construction/12development/32heldout plus15
metadata spares, all with identity/base/patch-lineage exclusions. It enables NO
inference. Exact source/version advisory scans and each task's own controls remain
gates. Any environment-only eligibility/split amendment must freeze before first
construction inference; never replace model failures or tune heldout results.
Protocol004's full640-point comparison remains unrun. Need real construction
public-evidence extraction, native development labels, learned-baseline sufficiency
and operating-point selection, then a complete finite heldout registration.
Do not call the main study complete from software or generated-task fixtures.

Verification at this preparation checkpoint:74 focused Python tests pass,48
shared experience-routing tests and4 web execution-policy tests passed earlier;
TypeScript check passes. Exact candidate base+delta replay also passes through
real local S3 and raw restore, including byte/mode/link preservation. Raw logs and
credentials stay private; current code/results are not yet committed.

Qualification015 is now COMPLETE: Luna0/1, Sol0/1 on independent official grading;
both public smoke checks pass, Sol has2protected-test edit flags. Native tokens
are256607/151818, total408425. See
`results/model-led-delegation-001/benchmark-qualification-015/` and private
`benchmark-pair-015/pair-completion.json`. Preserve exact frozen source archive;
no retry. Generic prompt subsequently clarifies existing-test protection and
requires focused evidence of public requested behavior beyond smoke checks.
No issue-specific or hidden test information was added.

Preparation017 is RUNNING sequentially on71metadata candidates, zero model
calls: `/tmp/observatory-router-benchmark-20261118/eligibility-017`, log
`continuation-001/preparation-017.log`. It is an active-chat eligibility pass, not a
scheduled worker. Exact83source commit/version advisory queries found0matches;
reviewed runtime graph is separate and incomplete coverage is explicitly retained.
Check its actual process/started/completion files before any continuation; no
relaunch of started controls. Current protocol forbids retries. Main construction,
calibration and heldout inference still have not started. Persistent numerical
baseline fixture002 passes with actual upstream route/cascade methods and local
scorer process, measuring training/prediction CPU/wall overhead; synthetic only.

Further active-chat implementation: public-only `knowledge.py` uses native Luna
interpretation with host differential assertions, preserving teacher provenance;
`stages.py` collects finite construction/development endpoints and annotations
before reading any sealed grades. `baseline_process.py` runs actual selected
released methods in the separately reviewed numerical environment, with JSON-only
transport and explicit setup/prediction CPU/wall accounting. `accounting.py`
reconciles native receipts without adding parent aggregate counters to children
or summing overlapping wall envelopes.81focused software checks now pass.

Annotation qualification018 made ONE new native Luna CLI invocation,20331tokens,
and returned two proposals. An invalid ledger purpose caused post-processing to
stop after native completion. The exact response was reconciled without another
call (`annotation/postprocessing-recovery.json`); both public assertions already
passed on the original base, so ZERO support records were admitted. No hidden
grades/patches were supplied. Corrected future ledger role/purpose are
`extraction`/`seed_construction`. Original failed source archive is preserved.
Results: `results/model-led-delegation-001/annotation-qualification-018/`.
Positive-gate canary019 is only host replay of the retained generated009 fixture:
base assertion17, integrated candidate0, zero new model calls or benchmark results.
It creates no study knowledge. Keep this distinct from actual native extraction.

Cumulative receipt audit003:11native ledger receipts,10positive-metered CLI
invocations,784512measured-token lower bound. The startup005receipt remains
unknown, so the complete total is null; managed analyst overhead is outside this
subtotal. No actual cash/quota/net saving result. Native-only request IDs may
repeat across separate local ledgers; reconcile using thread/raw-response identity,
not request labels. No credentials remain in completed private client homes.

Preparation017 remains the ONLY active queue, sequential environment controls,
with no model invocation. At31of71candidates, inspect the latest log/completion
records for current eligibility; do not relaunch. Existing generation/evaluation
sources listed in017stay frozen. Full scientific splits/budgets and baseline
training/sufficiency still need their final freeze before main inference.

Preparation017 is now COMPLETE:71candidates checked,46eligible and25excluded
before main model use. Original metadata order and stage-rules020 allocate
12construction/12development/22heldout, with no unused eligible reserve. Exact
split: `qualified-split-022.json`; projected full point matrix440assignments.
No main generation has started at this entry. Calibration amendment021 was
registered before main data: genuinely single-class executor labels use a
Beta(1,1) empirical prior, explicitly marked as nondiscriminative; no opposite
labels are invented. Mixed classes still need at least2examples per class and
all OOF Brier/heldout-exclusion rules remain. The synthetic numerical fixture
executes this path but fails its small-sample OOF gate; that failure is preserved,
not a real development baseline result.88focused software checks pass.

Construction source archive/readiness and finite native registration are being
prepared. Require its actual archive acknowledgement before inference. If it is
running, freeze ALL sources listed in that registration until generation and
independent grading finish; do not start another worker or repeat assignments.
Public construction records can support bounded implementation outcomes only;
posthoc annotator/host verification must not be credited as unaided verification
by the original executor. Other capabilities require their own evidence.

## 19 November 2026 — context-identity protocol correction before clean transfer

Construction023 was deliberately terminated after6pairs/24native calls, before
another admission and with no model call in flight. A recorded environment
message revealed benchmark identity through the CLI cwd path. The explicit user
prompt had no ID. The stop decision preceded model-grade inspection. All12coding
candidates were then graded once with frozen original sources: Luna2/6, Sol5/6.
All9public support records and all failed/successful attempts remain preserved,
but NONE enter the clean knowledge library. See `protocol-termination-024.json`
and `results/model-led-delegation-001/terminated-construction-024/`. One following
case had preparation only and no model invocation. Never repeat affected calls.

Fix: `anonymity.py` gives each CLI a random physical cwd/home under private /tmp,
with private host-side symlink/index paths. Source account/auth remains original;
no API key/fallback or normal-routing change. Canary026 made2fresh generated-task
coding calls; both repairs and recorded environment audits pass with zero tested
identity exposures. Captured complete credential-free client state also passes
real S3 retention. Model-facing route evidence now replaces parent task IDs with
opaque hashes; raw host provenance remains intact. Public proof copies now use
owned /tmp scratch instead of filling the persistent volume. Completed old proof
exports were relocated with exact manifest checks and original paths preserved;
raw logs and original source archives remain unchanged.95focused tests pass.

Replacement selection025 was frozen from full-SWE SymPy metadata outside Verified,
version>=1.10 for existing actor compatibility, with prior ID/base/exact+normalized
fix exclusions. All12fresh candidates pass advisory queries and own independent
empty/reference controls in preparation027, zero model calls. `clean-split-028.json`
keeps original development12/heldout22 intact: clean construction is6uninvoked
original Verified cases plus first6qualified fresh full-SWE cases; remaining6are
unused development reserve. This population change must be explicit in reports.
No affected model attempt is repeated and no model outcome selects replacements.

The original construction023 is STOPPED and independently graded; its admission
lock guard has been released. Current clean construction registration/source
archive is being prepared next. Inspect actual subsequent manifests/processes
before any continuation. Keep schedules PAUSED and do not restart old workers.

### Active clean collection029 — inspect before continuation

`clean-construction-029.json` is RUNNING through
`python3 -m ttgl.model_delegation.stages`, private output
`work/security/model-led-delegation-20261118/continuation-001/clean-construction-029`,
log `clean-construction-029.log`, original exec session52705. Exact source archive
and `source-archive-ready.json` are acknowledged. ALL source files listed in029
must remain unchanged until its generation/annotation and independent grading
finish. Do not duplicate or restart this phase. No scheduled work was resumed.

This is the clean12-task construction cohort from split028, max48native calls,
12M observed native tokens and6hours. It uses anonymous physical client cwd/home,
private symlink indexes, /tmp public-proof copies, full credential-free client
state backups to loopback S3, and opaque parent references in model-facing route
results. No-action completed responses are retained/metered for independent
scoring rather than discarded as infrastructure failure.96focused tests pass.
First clean coding attempt completed public checks/scope with131578tokens; its
recorded model-visible environment has1message and ZERO task/study ID exposures.
No clean official grade, transfer curve, voluntary-routing benefit or baseline
comparison is yet available. Grades stay sealed until collection finishes.

User explicitly asked for knowledge/routing research progress: report the actual
required Sol→Luna→Sol mechanism trial, rejected unsupported extraction proposals,
flagged/retired6-pair cohort (Luna2/6, Sol5/6), and distinguish these from the
still-unrun clean accumulation/FrugalGPT/RouteLLM comparisons. Software checks and
working mechanisms do not establish economic or capability improvement.

After029 finishes, build immutable0/4/8/12 prefixes from ONLY clean public records
and split028; retain all construction parents/failures. Then register matched
12-task development with common final-prefix knowledge, collect disjoint labels,
apply sufficiency rules020+021, use at most the6unused fresh development reserves
if required. Preserve heldout22 unchanged. Freeze the full440-assignment manifest
and native budgets before any heldout model call. Numerical baseline fixtures are
not native calibration. Existing `heldout.py`, `scratch.py`, `reports.py` provide
further orchestration/reporting glue but still require review/qualification before
main use; avoid uncontrolled scratch expansion. Restore retained exact candidate
artifacts for independent grading, never use hidden outcomes in live decisions.

## Saved for tomorrow — 19 November 2026, 01:03 UTC

User requested: write current state, commit and push; pick up tomorrow. The
already registered bounded clean construction029 is left running to finish.
No development/heldout stage is queued and no scheduled monitoring is enabled.

Observed snapshot: 20 of 24 coding attempts and 20 annotations complete; 13
supported local implementation records; 3,356,734 native tokens across completed
calls in this clean phase. These are public-check outcomes, not official task
success or demonstrated knowledge/routing benefit. No phase stopped/completion
record existed at observation. Official grading follows the entire collection.
Snapshot: `results/model-led-delegation-001/checkpoint-20261119/summary.json`.

Active owner PID579001, parent579000, started with:
`PYTHONPATH=src python3 -m ttgl.model_delegation.stages experiments/model-led-delegation-001/clean-construction-029.json`.
Private output/log remain under
`work/security/model-led-delegation-20261118/continuation-001/`.
Read `clean-construction-029/completion.json`, `stopped.json`,
`generation-complete.json`, `native-claims.jsonl`, per-invocation response and
completion records, and actual processes BEFORE doing anything. Do not rerun the
command: its owner guard intentionally rejects re-entry. Never repeat a started
or uncertain call. If still running, leave every source pin in029 unchanged.
If complete, audit grades/usage and then proceed with the development gates above.
If stopped, distinguish completed calls from verified pre-invocation failures;
audit recovery explicitly without discarding evidence or repeating inference.

Source generation/evaluation and contexts are frozen in the acknowledged exact
source archive for029; current Git commit alone does not replace that receipt.
Raw private evidence, credentials, native client state and exact candidate
archives remain local/loopback-S3 and ignored by Git. /tmp contains active owned
workspaces, reviewed numerical libraries, grader subset and benchmark inputs;
inspect and restore retained artifacts if scratch is lost, never infer that a
missing scratch directory means an assignment was unrun. Preserve database/S3
volumes, other active processes and every historical/frozen study.

Current research boundary: one required Sol→Luna→Sol mechanism diagnostic works;
unsupported extraction checks were rejected; the protocol-exposed six-pair cohort
is preserved at Luna2/6 versus Sol5/6 and excluded uniformly. Clean knowledge-size
curves, voluntary routing gains and native FrugalGPT/RouteLLM comparisons remain
unrun. Main development12/heldout22 are unchanged; six fresh unused candidates
are reserved for development expansion.96focused tests passed; do not report
software fixtures as model-quality, cash/quota or net-saving evidence.

## 19 November continuation — construction recovered, matched development active

The Codespace stopped midway through the last construction parent. Recovery030
accounts for 44 completed invocations, one started-only Sol call and three
unrun slots. Preserve the started call with unknown usage and grade. The
remaining Luna endpoint and both annotations for that parent stay unrun.

Recovery restored all 22 completed candidates from local SILO and matched
their recorded source hashes. All 22 coding rollouts passed the recorded
environment identity check. Ephemeral annotations preserved their prompts and
CLI events, with no rollout environment-message coverage. Their captured
prompts passed the identity scan. All 44 event streams independently reconcile
to 3,636,846 native tokens, a construction lower bound. On the pinned grader
Luna resolves 8/11 and Sol 9/11, with 6/11 and 7/11 respectively under public
check and edit-scope rules. The four planned prefixes hold 0, 6, 9 and 14 public
records. The final prefix has 11 completed pairs out of 12 registered parents.
See [recovery 030](../../results/model-led-delegation-001/construction-recovery-030/README.md).

[Matched development 031](../../experiments/model-led-delegation-001/matched-development-031.json)
has entered generation with the original 12 development tasks, exact restored
base states and historical control records, and the same frozen final packet
scope in both arms. The source/archive acknowledgement precedes inference.
Owner PID 35099 at launch, original exec session 36158. The private output is
`work/security/model-led-delegation-20261118/continuation-001/matched-development-031`
with a sibling log. Inspect actual manifests, claims and processes before
continuing. Preserve the pins and never repeat a started or uncertain model
call. The 22 held-out tasks have zero new inference. Schedules remain paused.

The exact reduced grader, original Codex CLI 0.169.0, previously approved local
SILO and patched numerical runtime were recovered. The paired numerical model
fixture passed after restore, and all 96 focused Python checks passed. The
private `run-development-calibration-032.sh` audits all paired endpoints and
then fits the released-method adaptations on disjoint development labels.
Require actual stage completion before invoking it. If sufficiency fails,
inspect the frozen rule before using up to six prespecified development
reserves. Held-out launch additionally needs the Observatory policy selection,
bounded scratch replay, exact full assignment and budget freeze, and the
original controls. No further native stage is queued.

### Matched development reconciled and Observatory development registered

All 24 matched031 native calls completed and audited to 4,176,013 tokens.
The independent evaluator reached its deadline on both candidates for one
task. Recovery036 left their grades unknown and finished the remaining
unstarted grades without native inference. The two null grades remain in
the assigned denominator. The 11 complete pairs resolve 6/11 for each model
on the official outcomes.

Public check amendment034 removes the unsupported quiet option on older
SymPy versions. An exact pristine witness and all four affected construction
candidates passed the same suite with the option omitted. Reporting preserves
the original 031 outcomes and adds 24 model-free portable replays. The
portable outcome with valid edit scope is Luna 5/11, Sol 6/11. Luna's matched
historical-rate scenario is 95.4% lower, with one fewer resolution. Both
released-method adaptations pass the frozen local numerical calibration
floor. They each select duplicate points across the three budgets. No
new native released-baseline trials or held-out calls have occurred.
See [the matched development results](../../results/model-led-delegation-001/matched-development-031/README.md).

The command is portable in new registrations. The endpoint collector now
preserves independent evaluator infrastructure errors as unknown and
continues later first-time grades. All 97 focused tests pass.

[Observatory development 037](../../experiments/model-led-delegation-001/observatory-development-037.json)
has an acknowledged exact frozen archive and has entered its finite native
stage. It covers 36 assignments across the three prespecified thresholds and
12 development tasks, with a cap of 72 native invocations. Use the fixed 11
fully graded comparison tasks for policy quality selection and all 12 for
cost. Track assigned unknowns and meter every parent and worker. Active PID
203838 at launch, exec session 49009, with private
`work/security/model-led-delegation-20261118/continuation-001/observatory-development-037`
and the sibling log. Preserve its source pins until generation and sealed
grading finish. No parallel stage or retries are authorized by registration.
Research schedules remain paused.

### Observatory development continued after a bounded timeout

037 stopped on its third assignment. The first two completions reconcile
to 309,278 measured native tokens. The third started call reached its parent
deadline with no worker admission and unknown usage. Its partial candidate,
ledger receipt and native event stream remain retained. The original three
assignments will be used only as immutable evidence, with the timeout grade
remaining unknown.

[Continuation 038](../../experiments/model-led-delegation-001/observatory-development-continuation-038.json)
registers exactly the 33 previously unstarted identities. All original
per-assignment model, policy, actor, source, cap and public check settings
are pinned. A verified parent deadline with zero worker admission remains
an unknown assignment and allows the next independent identity to start.
Other ambiguities stop admission. The private output is
`work/security/model-led-delegation-20261118/continuation-001/observatory-continuation-038`
with a sibling log, PID 230591 at launch and exec session 5200. Inspect actual
receipts before acting. Grade exact completed artifacts after combined native
generation closes, and select only from the frozen sufficient development
evidence. Schedules remain paused.

Model-free held-out preparation reconstituted the 22 original pristine base
states and recorded control receipts from the frozen split. One real managed
candidate replay established bounded scratch release for a new redundant
local copy. Held-out model inference and grades remain untouched.

Held-out runtime preparation is isolated on local branch
`observatory-heldout-runtime-prep` at `6dbfbe1`. The live 038 source pins
remain on `work`. The isolated change verifies point policy identities,
links identical policies within a task/system/snapshot, releases only
verified redundant candidate copies, and retains exact sealed grade
archives. It can preserve verified parent deadlines as unknown under the
frozen holdout qualification. All 100 focused tests pass there. A model-free
440-slot fixture from actual released-baseline calibration verifies 88
duplicate references before any Observatory operating-point disposition.
Apply the prepared code only after 038 closes. The private registration
helper for 039 requires the actual combined generation seal, grades and
development selection before it can freeze an execution manifest.

038 then finished four more assignments. Its fifth model response was
complete and metered at 171,556 tokens, with a retained candidate. The
assigned 420-second full envelope was breached. The start-to-stop receipt
window is 432.1 seconds, and the exact outer monotonic value was lost when
the guard stopped. Preserve this as a wall-budget failure, with its actual
usage and full candidate independent of its eventual official grade.

[Continuation 040](../../experiments/model-led-delegation-001/observatory-development-continuation-040.json)
admits only the remaining 28 untouched assignments under the original
model, policy, actor and per-assignment caps. It preserves the six already
admitted completions, the original timeout with unknown native usage and
the fully metered wall-cap failure. A fully metered elapsed cap breach
retains its usage and candidate, with a false protocol-admissible outcome
and separate official grade. Other ambiguities still stop. The exact
archive was acknowledged before native admission. Active owner at launch
was PID 278011, exec session 54462. The private output is
`work/security/model-led-delegation-20261118/continuation-001/observatory-finite-continuation-040`.
The active-chat scoring supervisor waits for the combined generation
and grading receipts. Inspect actual claims and processes before any
continuation. Research schedules stay paused.

The isolated held-out preparation branch now points to `559527a` and
passes all 101 focused tests. It preserves fully metered wall-cap failures
behind the future qualification and retains one immutable pristine base
per task before model execution. The private 039 reporting helper verifies
the full seal and reports paired comparisons, the baseline mixture
envelope and explicit local CPU rate sensitivity separately from measured
native tokens. Preserve the 040 source pins until its combined independent
grading finishes. SILO free extents were trimmed in place, and exact
continuation archive read-back still passed.

Persistent workspace free space briefly reached 33 MiB during 040. The
installed optional Next SWC musl binary had no open users on this glibc
host. Its original bytes are now referenced through a temporary copy,
with a verified compressed archive on the persistent workspace and a
second verified local buffer. This released 61,007,494 bytes net without
installing a package. Exact SILO read-back passed again. The private
`capacity-maintenance-20261119/completion.json` records both hashes and
`capacity-maintenance-20261119/restore-cache.py` rehydrates the optional
cache after a temporary filesystem reset. Check durable physical capacity
before the 039 base preparation and held-out admissions.

## Routing development complete and held-out matrix archived

The 037, 038 and 040 stages closed every one of the 36 assigned routing slots
without repeats. Twenty-eight completed within cap, seven had recorded
usage and wall-cap failure, and one native deadline left its usage unknown.
Independent replay produced 35 official grades. The selection rule chose
threshold 0.65 at the quality point. The cost and balanced points were
infeasible. On the fixed 11 common tasks the selected point matched Sol at
6/11 admissible resolutions, with 13.4% lower historical-rate scenario cost.
All 36 primary calls used Sol and the retained traces show zero route
requests, delegation requests or Luna worker admissions. The target
remains unmet. See [routing development](../../results/model-led-delegation-001/observatory-development-037/README.md).

The held-out runtime is integrated on `work` and all 102 focused software
checks pass. Registration039 is frozen and disabled with the 440 assigned
slots, including 242 independent native slots, 88 identical-policy
references and 110 infeasible Observatory slots. Its exact source,
numerical parameters, selection records and manifest passed S3 read-back.
The disabled runner rejects the registration before storage preparation.
Zero held-out calls or grades exist. See [readiness](../../results/model-led-delegation-001/heldout-comparison-039/README.md).

The current blocker is durable local capacity. The model-free sizing probe
found 160,841,590 missing compressed pristine payload bytes and 95,289,344
available workspace bytes, before future raw traces and grades. Retain 039
as immutable evidence. When adequate persistent local capacity is available,
recheck readiness and register an enabled continuation against the same
sealed matrix, sources, policies and task memberships. Research schedules
remain paused. The optional musl backup now resolves to its verified copy
on the separate local shared filesystem, recorded in
`capacity-maintenance-20261119/overflow-location.json`. Exact cache and
archive reads passed after that transfer.

## 20 November clarification of the small-model experiment

The hypothesis is that Luna can use verified experience from Sol to complete
new, bounded subtasks and reduce the amount of work Sol has to do while
preserving quality. The frozen library contains public-check-supported records
from both models. Sol-derived procedures can guide Luna. Observed Luna
competence comes from Luna's own attempts. The library is runtime context and
both models' weights stay fixed.

In the registered design, Sol is the controller. It can choose a subtask,
delegate it to Luna with relevant guidance, then verify and integrate the
result. Across all 36 routing-development slots, Sol made zero routing or
delegation requests. Luna received zero worker assignments, leaving the
handoff step untested. Luna's ability to use Sol-derived
guidance on a delegated subtask remains unmeasured in this development
cohort. The earlier required handoff was a separate mechanism diagnostic.

The selected Sol-controller point matched standalone Sol at 6/11 admissible
resolutions and had a 13.4% lower historical-rate inference cost. The observed
cost difference is between Sol-only attempts.
In separate standalone runs with the same final library, Luna achieved
5/11 admissible resolutions and Sol achieved 6/11. Those scores measure
whole-task performance with shared context. The contribution of Sol-derived
guidance and the effect of growing the library remain open.
[Routing results](../../results/model-led-delegation-001/observatory-development-037/README.md) ·
[Standalone results](../../results/model-led-delegation-001/matched-development-031/README.md)

The archived held-out matrix 039 still has zero model calls and requires
additional persistent local storage before activation. The 22 pristine
bases alone need about 153 MiB. Research schedules remain paused.
[Held-out readiness](../../results/model-led-delegation-001/heldout-comparison-039/README.md)

## 20 November proposal for a direct Sol-to-Luna transfer experiment

The question is whether Luna solves more unseen tasks when it receives
experience from Sol. Use the existing native Codex runner and independent
grader. Defer Observatory routing until the direct transfer effect has been
measured.

1. **Build the teaching set.** Compare independent Sol and Luna attempts on
   the same development tasks. Reuse audited paired results where the
   configuration and evidence match. Keep cases where Sol passed and Luna
   failed. Extract reusable procedures from the successful Sol attempts and
   retain the corresponding worked examples. Use independent grades for
   offline selection and public traces for the teaching material.
2. **Test on fresh tasks.** Freeze the library and retrieval rules before
   inference. Exclude shared issue, base and fix lineages between teaching
   and evaluation. Run two independent Luna attempts per held-out task:
   the usual prompt and the same prompt with relevant Sol-derived
   procedures. Hold the model, tools, resource caps and grader fixed.
   If comparing extraction with direct examples, add a third Luna arm
   using worked examples from the same Sol attempts.
3. **Measure paired outcomes and costs.** Report failures rescued, successes
   lost, verified completion, and the inference and latency difference
   from adding guidance. Report Sol and Luna teaching-set runs and any
   extraction inference as one-time construction costs. Preserve assigned
   denominators and unknown outcomes.

This proposal starts with Luna alone versus Luna with Sol-derived procedures.
It has zero registered assignments and zero model calls. Matrix 039 remains
archived and disabled. Preserve prior evidence and leave research schedules
paused.

## 20 November Observatory SIM ablation and routing holdout recovery

The user requested completion of the archived routing holdout and an actual
Observatory self-improvement memory ablation, followed by a question about
closely reproducing the SIM paper. The design and appendix review are documented
in [the SIM report](../experiments/sim-memory-ablation/report.md). The active
pilot is an adaptation. It uses a common initial prompt harness, four fixed
historical projections, new private stdlib coding tasks, and native Luna for
both proposal and execution. It does not stand in for the original paper's
ten independently evolved source harnesses and cross-benchmark continuations.

Pilot 001 is running under this chat at
`work/security/sim-memory-ablation/pilot-001`. Inspect `matrix.log`,
`registration.json`, `invocations/*/started.json` and terminal receipts before
attempting to resume. The out-of-suite live smoke passed independent checks,
metered 65,013 tokens and verified loopback retention. Eleven model-free empty
and reference pairs passed. The frozen bank contains three already observed
Observatory experiments (two accepted, one rejected). All study source hashes
were sealed before pilot inference. Do not expose held-out evidence to the
proposer, repeat an admitted call or tune the active pilot. Five repetitions
are conditional on the measured pilot budget.

The routing capacity blocker is resolved. Restored bases, fresh controls,
patched actor security evidence, historical-rate sizing, and continuation 043
commands are in [the routing restoration record](../../results/model-led-delegation-001/heldout-comparison-039/RESTORATION-20261120.md).
The original 039 registration stays disabled. The active chat owns restoration
and activation of 043. Avoid overlapping the authorized source account with
the SIM pilot and inspect actual claims and stop/completion markers first.
Research schedules remain paused.

### SIM pilot completed and routing continuation activated

SIM pilot 001 completed all four arms and 100 native calls. All 80 independent
coding grade replays agreed. C0/C1/C2/C3 passed 3/4, 2/4, 4/4 and 2/4, with the
first three arms retaining identical final prompt settings. Total 5,859,729
tokens, $0.19191098 in the API-equivalent scenario and 23m50s wall. The observed
differences are descriptive. No independent repetitions were started. The
user shifted research priority to a small sequence of dependent repository
tasks, comparing code-only with access to past decisions via MCP. Keep model
size and cost comparisons as follow-up. Read the
[SIM results](../../results/sim-memory-ablation/pilot-001/README.md) and the
[coding-agent MCP direction](observability-improvement-study.md). The SIM
aggregate passed exact local S3 read-back and appears in the Observatory
Experiments API.

The new bounded harness-trial MCP interface is `python -m ttgl.experiment_mcp`.
The real stdio exchange verified planning, readback and execution disabled
under the default host configuration. No native model trial was invoked
through this MCP prototype. The separate dependent repository task benchmark
has no registered assignments or scores yet.

After the SIM pilot fully finished, the ready 043 activation was sealed and
started from this chat. The exact old 039 file is still disabled. Check native
claims, terminal slot receipts, log and stop/completion markers in
`work/security/model-led-delegation-20261118/continuation-001/heldout-comparison-continuation-043`.
This is parent-serial and projected to take over eight hours plus grading.
Do not duplicate the owner, edit the frozen sources or repeat a claimed call.
Research schedules are still paused.
