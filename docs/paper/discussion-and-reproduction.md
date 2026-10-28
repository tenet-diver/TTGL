# Discussion and limits

The literature makes the central hypothesis plausible without making it new or
settled. EdgeWise reports substantial cloud-API savings with small changes in
software-task performance under particular conditions, but its accounting
excludes the local SLM. Router-R1 and related work already make the router an
active participant that reasons across model responses. The present study must
therefore establish its value through reproducible comparisons, complete cost
measurement and a precise intervention, rather than the assertion that models
have never conversed before.

The proposed distinction is continuing expert dialogue: an expert can ask for
missing evidence, challenge an interpretation and revise a proposal while the
small controller continues working. That may prevent context omissions and
uncritical acceptance. It may also waste time, encourage circular conversation
or amplify a shared mistake. Compare it directly with one-way assistance and
reset expert sessions under equal budgets. A bidirectional API alone is not a
scientific contribution; the empirical finding, including a negative result,
is the contribution.

The complete SWE-bench Verified replay sharpens this requirement. The primary
pre-task router saves estimated inference dollars but loses too much quality,
and a strong inexpensive standalone model undercuts the apparent advantage of
several portfolio operating points. A conversational agent must therefore beat
credible cheap standalone alternatives, not merely reduce calls to a costly
reference. The replay is a standard-benchmark result, while its historical
single-attempt data and unmeasured deployment expenses restrict its claims.

The pilot's lack of optional consultations is a useful design lesson. Easy
tasks can show that a controller avoids unnecessary expert work, but cannot
evaluate its capacity to obtain help. The next development sample should span
observed difficulty and failure modes before the final test is frozen. It must
not select final tasks merely because they make conversation look useful. A
registered development-stratified sampling rule, followed by an untouched test
sample, can ensure both easy and difficult assignments without selecting on
final-treatment outcomes.

The artifact-policy problem also matters. In a product, adding a good test to an
existing file is usually desirable. In a controlled repair benchmark, altering
the tests used for evaluation can invalidate success. The next protocol should
make that distinction explicit: immutable evaluator tests are outside the
worker, while permitted public-test additions are reviewed or applied under a
declared patch policy. The current frozen results remain intact. Reinterpreting
them as proof that conversational agents cannot follow constraints would be
unwarranted given the prompt ambiguity and tiny sample.

Personalization and long-term learning remain optional, separable questions.
Editable memory has practical value as a user interface, but it does not
automatically improve task success. Existing developer-skill research motivates
generic and shuffled-user controls. RL can improve decisions without providing
an economical training path at small scale. Training cost, privacy boundaries,
feedback reliability and retained local capability must be measured. The
current code uses no model-weight update, and the live Codex experiment has no
access to the hosted models' weights.

More agents can supply complementary expertise, but also introduce duplicate
work and harder credit assignment. The minimal dyadic design should establish
when conversation helps before a many-to-many experiment claims emergent roles
or self-improvement. Existing graph and multi-agent learning frameworks should
be reused for that extension. The long-term ambition remains affordable,
user-controlled AI; that social objective is not demonstrated by a four-task
hosted-model pilot.

# Reproducibility and next execution

The repository contains the full protocol and adapted benchmark provenance,
separate task workspaces, immutable grader source, regression reports, submitted
patches, nullable-cost records, dialogue transcript and analysis code. It also
contains a tested restore command that verifies downloaded archive hashes and
replays all buggy/fixed controls before creating new worker copies. It refuses
to overwrite existing destinations. The original source and evaluator trees
are checked against their manifest before grading.

From a prepared research environment, the recorded analysis can be reproduced
without any model calls:

```bash
python scripts/analyze_codex_pilot.py --output-dir results/my-pilot-analysis
python -m pytest -q
```

On a fresh compatible workspace, restore the historical benchmark fixtures:

```bash
python scripts/restore_codex_pilot.py --install-env
python scripts/restore_codex_pilot.py --verify-only
```

The analysis command requires the research dependencies in
`requirements-research.lock`. Restore uses its separately pinned CPython 3.8.20
environment and legacy test dependencies, and downloads the exact registered
public archives. The study is deliberately an adapted BugsInPy subset; the
restore process does not claim to recreate every original benchmark environment.
Do not execute new models in the recorded solved worker copies.

For a normal machine with a writable, authenticated Codex installation, the
reusable adapter accepts a task manifest and a new output directory:

```bash
python -m ttgl.personal --task task.json --condition personal \
  --small-model gpt-6-luna --large-model gpt-6.1-sol \
  --max-expert-calls 2 --timeout-seconds 240 \
  --output-dir artifacts/new-conversation
```

The runbook documents the exact supported arguments, structured responses,
resumed threads, failure disposition and grading boundary. Completion means
the controller finished; it does not automatically mean the issue was resolved.
A fake backend verifies control flow; real native trials separately verify
runtime availability and per-model token metering. Earlier managed-host
read-only failures remain archived historical evidence. They are not the state
of the writable desktop continuation, which completed all 141 fresh assignments
across the original, development and held-out panels. The earlier BugsInPy pilot
used the collaboration tool; those records remain distinct from native trials.

The six-condition SWE-bench bridge implements mandatory native model/metering
preflight, isolated source checkouts, official prediction export and grade
import. `scripts/collect_codex_usage.py` uses the supported per-thread estimate
route without new inference. Native completion counters are cumulative, so the
independent audit checks response identity and validated counter deltas before
reconciling total and per-model usage. Missing bills remain unknown.

Reproduce the completed held-out audit and target analysis without new models:

```bash
PYTHONPATH=src python scripts/audit_live_study.py \
  --study-dir results/delegation-heldout-001/study-002 \
  --output artifacts/my-heldout-audit.json
ttgl_analysis=results/delegation-heldout-001/analysis-002
python scripts/report_policy_target.py \
  --records "$ttgl_analysis/published-rate-records.json" \
  --output artifacts/my-heldout-target.json
```

Use fresh output paths; these commands must not replace archived evidence.
The [handover](../research/HANDOVER.md) records source freezes, actual process
state and gates for continuing the bounded Pro comparison. A passing software
check or environment fixture is not a task success. The Pro control, real actor
boundary and pristine patch replay must pass before scored model trials.
No new GPU or provider purchase is authorized as a workaround. Open-weight
training remains a later protocol, and its costs must be measured separately.

# Conclusion

Small-model-led collaboration is established prior art, including learned
delegation for software engineering. The defensible hypothesis is whether
continuing, bounded conversation achieves materially lower **total** cost while
retaining a prespecified level of task success, beyond single-model execution,
initial routing and one-way assistance. Personal memory and learned skills can
be tested as additional interventions.

The present work implements and tests the orchestration and measurement code,
executes a historical-bug pilot and 141 fresh metered assignments, and replays
all 500 SWE-bench Verified tasks across ten published model runs. The primary
historical router saves 46.1% in estimated inference cost but loses 8.6 quality
points. Cheap strong standalone controls explain why model selection alone is
not evidence for a routing advantage.

The completed eleven-task held-out conversational comparison improves the
observed Luna resolution count from seven to eight while Sol resolves nine.
It saves 91.45% of the Sol model-inference scenario cost and retains 88.89% of
Sol accuracy, missing both 95/95 components. One voluntary bidirectional rescue
is accompanied by imperfect context transfer, unsuccessful consultation on
another task, and an unresolved missed escalation. These results show useful
mechanism behavior and a limited descriptive improvement, not reliable failure
detection, a causal expert effect or population noninferiority. The prospective
Pro comparison retains standalone controls and pre-consultation candidate
patches to test those remaining questions before any learning claims.
