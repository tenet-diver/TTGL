# Using conversational routing in your own projects

Use the official Codex CLI with your supported ChatGPT login. TTGL is a small
experimental orchestration layer around it: the cheaper agent edits and tests,
asks a stronger agent for bounded help, then checks and integrates its answer.
It can continue the same expert conversation when clarification is useful. It
does not replace Codex's tools, provide a new subscription, or train a model.

The intended benefit is **more successfully completed work for the same resource
allowance**. A reduced token count does not automatically reduce a flat monthly
subscription charge. A lower API-equivalent price does not establish a lower
Codex credit charge. Both claims need the appropriate measurements.

## A supported installation

Use your workstation or a Linux VM where ordinary Codex state/session storage is
writable. A GPU is unnecessary for subscription-backed hosted models. A VM that
also grades SWE-bench needs Docker and substantially more disk space than this
project-use example; see [the handover](HANDOVER.md).

Install the official CLI using its documented package manager, then use the
normal ChatGPT sign-in flow. The version inspected by this repository is
`0.163.0`; pin the version used for an experiment rather than automatically
updating between conditions.

```bash
npm install -g @openai/codex@0.163.0
codex --version
codex
```

Select **Sign in with ChatGPT** if this is a new installation. An already logged
in installation can use its existing supported authentication. Run
`codex login status` locally to check it; keep account details out of published
research artifacts. Do not copy the managed environment's authentication file
or change its read-only mount to make a nested CLI work. The normal installation
must manage its own authentication and state.

Clone TTGL and install the pinned research dependencies in a Python 3.12
environment. These commands work outside the managed `/workspace` layout:

```bash
git clone --branch work https://github.com/tenet-diver/TTGL.git
cd TTGL
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-research.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m pytest -q
```

Select models that your actual Codex account exposes, and check each with a
small request before a study. `gpt-6-luna` and `gpt-6.1-sol` are the explicitly
requested identifiers in the earlier platform pilot; that interface's success
does not prove a new CLI account has those models. The pinned OpenAI SDK catalog
also lists those identifiers, but catalog membership is not account entitlement
or proof of parameter count. The CLI does not silently replace unavailable
models in this protocol. Record the exact CLI version, requested model and any
returned service/model revision. See [the metering guide](codex-metering.md) for
a fresh-thread plus resumed-thread usage check.

## Current verification and handoff lessons

The first Pro router episode passed independent grading without Sol, while Luna
acknowledged that it had not run endpoint tests. Correctness on that selected task
does not make lint adequate behavioral verification or prove that consulting Sol
would help. Record correctness, observed checks, consultation decisions and any
verified integration separately. The [episode audit](../../results/router-development-010-analysis/README.md)
contains the evidence and accounting limits.

Prefer a bounded executable check that can distinguish a wrong candidate from a
correct one. Give Luna 2–3 meaningfully different checked repair attempts before
help, with a justified exception when no credible useful step is available.
Do not force extra edits just to reach a count. Distinguish infrastructure from
reasoning failure and reserve integration time. If help is useful, send Sol the
goal and constraints, relevant source and candidate patch, prior approaches,
exact checks and outcomes, lessons, ruled-out explanations and a focused question.
Sol cannot inspect the workspace or certify checks it did not run; Luna verifies
any adopted advice. Retain important command exit statuses as well as output.

For experimental continuation, a new output directory is not sufficient to repeat
completed inference. The Pro runner requires validated setup reuse or explicit
fresh-setup registration and uses an exclusive assignment claim. Never remove a
claim to bypass an uncertain call. Transfer research evidence only with authorized
access and content hashes; never copy credentials. Current one-task inference
scenario cost is USD 0.00741304, with no measured invoice, quota saving or
matched-Sol retention estimate. The next verification prompt candidate is unrun.

## Start with one bounded project task

Create a clean project branch or use your normal isolated development checkout.
The harness can modify the task workspace; give it a concrete issue and a known
test command. Keep its output directory outside that workspace. For example,
save this JSON as `/absolute/path/task.json`, replacing every example path and
the prompt with your real project values:

```json
{
  "task_id": "project-issue-001",
  "prompt": "Fix issue 001. Reproduce the bug, make the smallest correct change, and run python -m pytest tests/test_parser.py. Preserve the public parser API. Ask the expert if a failing approach or uncertainty about semantics warrants help; send only relevant code, errors, and questions. Verify the proposed fix before accepting it.",
  "workspace": "/absolute/path/project",
  "allowed_paths": ["src", "tests"],
  "memory": [
    {"id": "project-tests", "text": "Use the project's existing pytest suite. Do not introduce a runtime dependency for this fix."}
  ]
}
```

From TTGL, set the two variables to model IDs verified in your account, then run:

```bash
: "${TTGL_SMALL_MODEL:?Set a verified small/cheaper Codex model ID}"
: "${TTGL_LARGE_MODEL:?Set a verified expert Codex model ID}"
.venv/bin/python -m ttgl.personal \
  --task /absolute/path/task.json \
  --condition personal \
  --output-dir /absolute/path/results/project-issue-001 \
  --small-model "$TTGL_SMALL_MODEL" \
  --large-model "$TTGL_LARGE_MODEL" \
  --reasoning-effort medium \
  --max-expert-calls 2 \
  --max-turns 6 \
  --timeout-seconds 900
```

The two-call limit permits an expert clarification and a subsequent answer.
It also means the controller must recover or finish if the limit is exhausted.
The wall deadline includes consultation and integration. It is not a token,
credit or dollar cap: one Codex invocation may make many model calls.

Keep project memory short and editable: goals, compatibility requirements,
test commands and current preferences. Do not place credentials there. Avoid
copying entire terminal logs or repositories into expert messages. Have the
small agent send the failing test, relevant interface and the specific question.
The harness preserves logical conversations, but this does not guarantee a
physical KV-cache hit or discounted billing.

The output contains a checkpoint, event ledger and final manifest. A final
`completed_ungraded` means only that the protocol finished; review the patch and
run your project's independent checks. An interrupted in-flight request requires
reconciliation before resuming, to avoid duplicating edits or billed work. The
current allowed-path and context-only expert rules are not complete process
isolation. Keep unrelated private files and benchmark answers outside the agent
environment; use separate execution environments for stronger boundaries.

## How to reduce your own plan use

Begin with the cheaper model on tasks for which it has a measured good success
rate. Keep a strong-model-only reference on a small set of representative tasks.
Useful consultation triggers include repeated test failures, uncertainty about
API semantics, incompatible requirements and an unexplained regression. Merely
asking the model whether it feels confident is not a calibrated success signal.
Record whether help actually fixed the problem rather than rewarding fewer
expert calls by themselves.

Use a fresh task thread for unrelated work. Preserve relevant state for a
continuing task, and pass a concise evidence summary when transferring work.
Disable automatic repeated attempts after a hard failure; record and inspect it.
Adjust reasoning effort and consultation limits on development tasks, then
keep them fixed for the comparison. All repeated attempts and abandoned tasks
count toward resource use. An expensive final rescue can erase earlier savings.

For several weeks of your own work, record accepted tasks, task type, rework,
total latency, per-model tokens and—when available—Codex estimated credits.
Compare the same task mix; do not compare yesterday's hard architecture work
with today's easy documentation fixes. A randomized assignment of comparable
tasks to strong-only and conversational modes is more informative than an
uncontrolled before/after dashboard.

| Quantity | How to collect it | What it can establish |
|---|---|---|
| Per-model token use | TTGL manifests plus retained Codex logs | Inference resource use, with cache/reasoning overlap handled |
| Estimated plan credits | Supported app-server `account/usage/read` for the task thread, when returned | Estimated quota consumption; validate parent/child inclusion before adding totals |
| API-equivalent USD | Complete token records × dated rates, or ccusage | A stated price scenario, not your subscription bill |
| Monthly cash expense | Actual subscription and extra-credit invoices | Money paid; unchanged flat fees mean no immediate cash saving |
| Useful throughput | Independently accepted tasks per credit/window | Whether your existing allowance delivers more completed work |

The existing log tool can provide a second view:

```bash
npx --yes ccusage@20.0.44 codex session --json --offline
```

Its `costUSD` is a pricing estimate. An empty report is missing evidence, not
zero cost. Subscription quota may weight models, speed and reasoning differently
from raw tokens or public API prices. A 40% API-equivalent saving is therefore
not evidence of 40% less plan usage. Report credit and token results separately.

The repository also includes an optional official app-server collector for a
completed TTGL run:

```bash
.venv/bin/python scripts/collect_codex_usage.py \
  --state /absolute/path/results/project-issue-001/state.json \
  --output /absolute/path/results/project-issue-001/subscription-usage.json \
  --independent-roots
```

Use `--independent-roots` only after confirming that the recorded controller and
expert threads are independent billing roots and have no nested-agent charges
included in one another. The TTGL harness explicitly starts separate threads;
if a backend or configuration adds nested agents, verify its accounting scope
before aggregating. The collector performs a read-only usage query rather than
new model inference. Account availability is not guaranteed; absent backend
estimates remain null. Do not extrapolate missing credit data from token totals.

## What the completed replay found

First, the actual [500-task historical replay](../../results/swe-replay-001/README.md)
offers a useful warning: its primary router saved **46.1% of source-estimated
inference expense**, but resolution fell from **72.8% to 64.2%**. It failed the
proposed three-point quality tolerance. A ten-model portfolio point achieved
76.2% at `$0.1154/task`, while the inexpensive MiniMax 2.5 high single-model
control achieved 75.8% at `$0.0733/task`. The added routing cost did not establish
an advantage over that cheap single model. This is published-output replay,
not live Codex conversation or measured plan-credit saving; its practical
lesson is to benchmark a good inexpensive standalone model before adding
coordination overhead.

## A transparent cost scenario, not an experimental result

The repository's 25 October price snapshot gives provisional standard text
rates per million uncached-input/cache-read/output tokens of
`$0.10/$0.01/$0.50` for Luna and `$2.00/$0.10/$10.00` for Sol. Those are secondary
LiteLLM observations, corroborated by the primary GitHub Copilot pricing file
**for Copilot's own channel**. Direct OpenAI prices remain unverified here: the
vendor pages returned proxy 403 on 26 October. Priority/fast mode, context tiers,
cache writes, tools and taxes can change the applicable rate. None of these
sources establishes the user's Codex credit conversion.

Under those provisional rates, an illustrative strong-only task using 100,000
uncached input and 10,000 output tokens costs `$0.30` in API-equivalent inference.
Suppose all small-model work uses 120,000 input and 12,000 output tokens (`$0.018`),
and another `$0.002` is assigned to incremental tools/infrastructure. The table
varies the fraction of tasks consulting the expert and the *total* expert work
per consulted task, including all conversation turns:

| Assumed consultation fraction | Assumed expert cost per consulted task | Combined mean cost/assigned task | Saving against $0.30 |
|---|---:|---:|---:|
| 40% | $0.15, short bounded assistance | $0.080 | 73.3% |
| 40% | $0.45, longer dialogue/repeated context | $0.200 | 33.3% |
| 80% | $0.45, frequent long dialogue | $0.380 | **−26.7%** |

These are arithmetic sensitivity examples with invented workloads, **not
measured TTGL savings, a forecast or a subscription discount**. They assume no
cached input and that all output, including billable reasoning, is already in
the stated output total. The long-dialogue scenario breaks even at roughly
62.2% consultation, because `(0.30 − 0.018 − 0.002) / 0.45 = 0.622`.
Actual failures, retries and shared infrastructure allocations change this.

Generally, `saving = 1 − mean(total conversational cost) / mean(total strong-only
cost)`. Also report `total cost / independently resolved tasks`; unsuccessful
attempts remain in the numerator. If local hardware or training is introduced,
include its allocated cost and state the workload over which it is amortized.
The current Codex implementation is a hosted-model experiment; it does not yet
offer a local-Qwen provider or learned adapter. A later local deployment needs
its own performance and energy/hardware measurements.

## Research status and sources

The existing live pilot establishes that the conversation mechanism runs. Its
optional controllers never consulted the expert, and it has no attributable
usage export. The completed standard-benchmark replay tests an offline router,
not this conversational product. Neither validates a Codex-plan savings
recommendation. Consult the current
[handover](HANDOVER.md) and [standard-benchmark research plan](standard-benchmark-research.md)
for the larger evaluation and unresolved evidence.

- [Official Codex README at the inspected revision](https://github.com/openai/codex/blob/970111f6cb62cc02fe36a82ea7d71b37a2889c97/README.md): installation and supported ChatGPT login.
- [Metering source review](codex-metering-evidence.md) and [runtime diagnosis](codex-runtime-metering.md).
- [Model and price landscape](../thesis/model-landscape.md), [exact model catalog](../thesis/model-catalog.csv) and [retrieval register](project-usage-sources.json).
- [Personal-agent CLI details and limitations](personal-harness.md).


## Current router-development practice

The active v5 completion guidance asks Luna for a bounded executable behavioral
check before declaring completion. Lint and diff checks alone do not establish
behavior. Preserve exact failing output and shell exit status: a later successful
command can mask an earlier failure. After useful independent repairs, a material
unverified requirement can justify a focused Sol consultation. Default to two or
three distinct checked approaches before help, with a concrete early-help reason
when no useful independent attempt is available; preserve time for integration.
Transfer source, candidate changes, attempts, exact results, lessons, ruled-out
hypotheses and remaining questions. Verify Sol's advice after integrating it.

Ansible's first v5 trial passes fresh grading and supplies behavioral checks, but
uses no expert. This supports that episode's completion claim, not a proven
improvement in failure detection or delegation. The next Element Web and Tutanota
units are sequential, with their own controls and no automatic retries. Observe
visible commands, results, decisions and handoffs; never feed hidden grades back
to a live actor. See experiments/router-iterations-20261031/plan.json.


The October31 three-case series is complete: Ansible and Element(v5) pass without
Sol; Tutanota(v6) passes after one voluntary consultation. The pre-handoff candidate
also passes, so no rescue is established. Tutanota's handoff is detailed but lacks
some relevant branch source, and behavioral tests remain unexecuted due to build/
dependency failures. Keep verification status separate from official outcome.
Retain the general policy for varied fresh tasks rather than add a prompt exception
for every case. Generality and transfer requirements are in router-generality.md;
full evidence is in results/router-iterations-20261031/README.md.
