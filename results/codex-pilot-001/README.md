# Codex conversational-routing feasibility pilot

The [summary](analysis/summary.json) and [trial records](analysis/records.json)
derive from the [frozen adapted BugsInPy study](../../experiments/codex-pilot-001/README.md).
There are 16 live worker assignments on four historical bugs from two repositories.

Functional successes: Luna 3/4, Sol 4/4, task-only routing 4/4, optional
conversation 3/4. Artifact-policy acceptance: 3/4, 4/4, 2/4, 0/4. Several workers
added or modified tests inside original test files, which the frozen grader
rejects separately from functional correctness. These records were not repaired
or replaced after evaluation.

All task routers selected Luna, and all optional controllers reported zero
expert turns. The [separate forced dialogue](dialogue-transcript.md) used two Sol
turns and a resumed expert thread, and its independently graded patch passed
30 selected tests. That mechanism check is excluded from the four-arm analysis.

Cost and token observations are null. Batch observation timestamps are retained
in [the execution log](execution-log.jsonl) but are not per-task latency data.
The host does not supply the same interface as a metered inference API.

The standalone Codex CLI failed before model execution because its app-server
state location is read-only. The live pilot used the platform collaboration
tools. The CLI adapter's tests use an injected backend and subprocess fixtures;
those tests do not establish live CLI authentication or model performance.

Reproduce the analysis from the repository root:

```bash
python scripts/analyze_codex_pilot.py --output-dir results/new-pilot-analysis
```

The result was reproduced exactly in a second output directory. See the
[paper](../../docs/paper/README.md) for prior work, interpretation and the larger
prospective experiment. Do not treat these observations as evidence of dollar
savings, performance noninferiority, learned routing, local-model deployment or
long-term learning.
