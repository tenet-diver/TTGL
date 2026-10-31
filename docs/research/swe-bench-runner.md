# Running the metered SWE-bench study on a writable Codex host

The bridge in `scripts/run_swe_bench.py` generates patches through the existing
Codex CLI and imports grades from the **official SWE-bench harness**. It does not
replace SWE-bench tests. The checked-in task manifest selects 12 of the 500
Verified tasks before model outcomes; this is a standard-benchmark pilot, not a
powered 500-task leaderboard result.

The bridge is tested with scripted backends and real temporary Git repositories.
Those software tests are not model-performance results. A real host must pass
the model/metering preflight, provision worker dependencies, and run independent
official grading. The current managed Codex home is read-only; the script does
not relocate it, extract credentials, or bypass filesystem restrictions.

## Prepare the host

Use the supported Codex CLI with its normal writable state directory and
`codex login` using ChatGPT, or an already-authorized API configuration. Do not
copy credentials from another managed runtime. Confirm the desired model IDs
are available to this account: requested identifiers are recorded, but the
adapter cannot establish an immutable provider weight revision.

From the TTGL checkout, run `bash scripts/setup_research.sh` and activate the
printed research environment. Use Docker and the separately pinned official
SWE-bench environment for evaluation. Read the experiment preparation document
for the frozen dataset and harness revisions.

**Worker setup is separate from evaluation setup.** Codex runs on the host,
with a fresh checkout mounted into a pinned official image for public checks.
Prepare a complete [worker configuration](worker-environments.md) covering every
task, with already-present images and passing public dependency probes. Supply
it through `--worker-config`; generation refuses an absent configuration.
This tool container does not establish host read isolation or Codex's permission
to use Docker. Compiled projects may need additional environment preparation.
For a confirmatory study, give each solver a
properly isolated, dependency-provisioned runtime and keep gold patches,
evaluation tests, research outputs and other workers inaccessible.

## Freeze, preflight and generate patches

Choose two real account-supported model IDs. The following identifiers are
examples from the user's proposed design; preflight must confirm availability.
Both output paths must be new, distinct directory trees.

```bash
python scripts/run_swe_bench.py init \
  --tasks experiments/swe-bench-verified-001/tasks.json \
  --output-dir /workspace/study-001 \
  --workspace-root /workspace/workers-001 \
  --worker-config /absolute/path/worker-config.json \
  --small-model gpt-6-luna --large-model gpt-6.1-sol \
  --reasoning-effort medium --timeout-seconds 900

python scripts/run_swe_bench.py preflight --study-dir /workspace/study-001
python scripts/run_swe_bench.py run --study-dir /workspace/study-001
```

`init` is offline. It freezes the public task bytes, exact models, limits,
orchestrator/bridge source hashes, and randomized paired assignment order.
The default six conditions are `small`, `large`, `precall_router`, `oneway`,
`reset_expert`, and `personal`. `--conditions` can freeze a smaller explicit
set, which must include `large`. The pre-call arm is an LLM prompt baseline,
not RouteLLM or Router-R1. `oneway` uses answer-only fresh experts;
`reset_expert` allows clarification/challenge but starts a fresh expert every
consultation; `personal` retains both threads. The one-way comparison changes
both interaction direction and expert state, so it is not a complete factorial
ablation by itself.

`preflight` makes at most two tiny model calls, outside the scored task costs.
It requires successful model access and positive input/output token evidence,
with a reported cached-input counter. It stops after a startup failure and
cannot be silently rerun in the same study. Preserve a failed preflight and
create a new study after fixing the runtime. A preflight is not a check of
solver dependencies, container isolation, expert continuation, or grade quality.

`run` is sequential and consumes subscription/API quota. At the 900-second cap,
72 assignments can take up to 18 hours of model execution, plus setup/grading.
This is a wall-time ceiling, not a quota or dollar cap. Each arm/task gets a
fresh shallow checkout at its exact base commit. The runner never deletes or
resets an existing worker. It includes new non-ignored files in exported patches
and refuses export after the agent changes Git HEAD.

Continue a safely interrupted study with:

```bash
python scripts/run_swe_bench.py run --study-dir /workspace/study-001 --resume
```

Completed assignments are not rerun. In-flight uncertain turns require manual
reconciliation and are never automatically replayed. Source, design or task
changes require a new study. A task with incomplete meters is preserved and
stops further execution; do not relabel its missing cost as zero. Failed
attempts remain part of assigned-task accounting.

## Grade with the official evaluator

Standard prediction files appear at
`/workspace/study-001/predictions/<condition>.jsonl`, with only
`instance_id`, `model_name_or_path`, and `model_patch`. Run each file through the
pinned official evaluator against the exact frozen tasks in a separate
evaluation environment. The preparation script/runbook owns the evaluator
command and dependency setup. Archive the original official `report.json`,
`patch.diff`, test output and runtime logs for every task.

Create a grade index mapping conditions and instance IDs to those existing
per-instance reports:

```json
{
  "small": {
    "psf__requests-5414": "/evaluator/logs/run_eval/run-small/ttgl-small/psf__requests-5414/report.json"
  }
}
```

Populate every graded assignment. Relative paths are resolved beside the grade
index. Missing grades remain ungraded; they do not become fabricated failures.
The importer requires the official report's boolean `resolved` field and an
adjacent `patch.diff` whose SHA-256 matches the exported patch. It does not
accept a grade for another solution. For an empty patch that the official
evaluator skips, map that task to the original **aggregate** report instead.
The importer records unresolved only when the exported patch is exactly empty
and the task appears in both official `empty_patch_ids` and `submitted_ids`,
and not in `resolved_ids`. The record labels this evidence separately from a
per-instance test result. Missing reports or infrastructure errors do not
become empty-patch failures. Never create a synthetic official report.

## Collect usage and estimate savings

The personal harness records model-specific validated token deltas and all
thread IDs. Collect backend subscription estimates from each selected finalized
state with `scripts/collect_codex_usage.py`; repeat `--state` for every assigned
task. Include controller, router, and every fresh expert root. The collector
discovers those IDs from the state ledger.

```bash
python scripts/collect_codex_usage.py \
  --state /workspace/study-001/runs/personal/psf__requests-5414/state.json \
  --independent-roots --output /workspace/study-001/provider-usage.json
```

The example selects one task; it cannot yield complete study savings. Supply
all finalized states for complete accounting. Only attest independent roots
when no selected parent includes another selected thread's billing. Collect
again to a **new** output path if backend estimates have not settled. Missing
estimates remain null. These estimates are not an invoice.

For a separate API-equivalent comparison, supply a versioned `prices.json`:

```json
{
  "kind": "api_equivalent",
  "currency": "USD",
  "retrieved_at": "<date of verified pricing snapshot>",
  "source_url": "<official pricing source>",
  "models": {
    "<exact model identifier>": {
      "input_per_million": "<replace with verified numeric rate>",
      "cached_input_per_million": "<replace with verified numeric rate>",
      "output_per_million": "<replace with verified numeric rate>",
      "accounting": "cached_within_input_reasoning_within_output_cache_write_at_input_rate"
    }
  }
}
```

This template deliberately contains invalid numeric placeholders; it is not a
price claim. Provide every observed model's verified numeric rates or omit
`--prices` and retain unknown API-equivalent costs. The supported convention
counts cached input within total input, reasoning within output, and cache
writes at the ordinary input rate. A provider with different billing semantics
needs a separately validated estimator. No alias substitution or invented
closed-model price is performed.

```bash
python scripts/run_swe_bench.py analyze \
  --study-dir /workspace/study-001 \
  --grades /evaluator/grade-index.json \
  --provider-usage /workspace/study-001/provider-usage.json \
  --prices /workspace/verified-prices.json \
  --output-dir /workspace/study-001/analysis-001
```

Analysis includes all assigned manifests, quality per assigned task, estimated
model cost per assigned/resolved task, paired cost ratios, bootstrap intervals,
and provider-estimated credit savings when complete. Provider data must be
bound to the exact finalized state hash. Unknown model prices, usage or credits
prevent a complete savings estimate. Fixed subscription fees, local hardware,
training, tools, and evaluator infrastructure are not secretly treated as zero:
full deployment cost remains outside this model-cost endpoint.

A 12-task study can test whether the experiment works and expose large effects;
it cannot establish a 3-percentage-point noninferiority margin. Replication on
a sufficiently powered held-out set and measured quota accounting are needed
before claiming reliable personal plan savings or thesis-level confirmation.
