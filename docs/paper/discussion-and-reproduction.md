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
A unit-tested fake backend verifies the control flow without pretending to be
an LLM. The installed standalone CLI's read-only-state failure in the present
managed session remains a known runtime limitation. The actual live trials used
the collaboration tool instead and do not establish CLI service readiness.

The next performance experiment requires a larger frozen task sample, strong
worker/evaluator isolation, unambiguous artifact rules, a native one-way
assistance comparator and observable billing. It can use existing hosted Codex
agents if their usage can be recorded, or compatible open models through an
existing serving stack. A faithful reproduction of prior large-scale training
requires additional resources; it is not silently charged to the existing
US$100 Runpod allocation. No new credential is needed to reproduce the recorded
analysis. Credentials and connectivity are still required for future paid GPU
or provider runs.

Fastest Jira and Confluence synchronization remain unavailable in the current
tool set. Local task records and an import CSV preserve progress; they are not
remote issue keys or evidence of publication. The intended Confluence destination
remains the FASTEST space at fastestswarm.atlassian.net.

# Conclusion

Small-model-led collaboration is established prior art, including learned
delegation for software engineering. The defensible hypothesis is whether
continuing, bounded conversation achieves materially lower **total** cost while
retaining a prespecified level of task success, beyond single-model execution,
initial routing and one-way assistance. Personal memory and learned skills can
be tested as additional interventions.

The present work implements and validates the orchestration and measurement
path, executes a four-condition historical-bug pilot, and demonstrates one live
two-round clarification-and-integration exchange. It does not establish cost
savings or performance noninferiority. The complete records expose where the
pilot is informative and where its task scale, absent billing and grading
policy prevent a stronger conclusion. The registered next comparisons turn the
product intuition into a falsifiable software-engineering experiment.
