# Observatory SIM memory ablation

We test whether access to past experiments helps a Codex optimizer find better
coding-agent instructions for unseen tasks. The optimizer and task-solving
policy both use native `gpt-6-luna` at low reasoning effort through the
authorized local ChatGPT subscription. The experiment runs without Docker
or newly installed Python dependencies.

## Design

| Condition | Historical records supplied to the optimizer |
| --- | --- |
| C0 | None |
| C1 | Modifications and observed outcomes from successful experiments |
| C2 | Modifications and observed outcomes from successful and unsuccessful experiments |
| C3 | C2 plus the corresponding predictions, diagnoses, rationale and lessons |

All four arms start from the same prompt harness. They receive the same schema
for current-run observations and earlier rounds. Only the optimizer sees the
historical projection. Hidden inputs, expected answers, evaluation code and
other arms' observations stay outside the actor. Historical records contain
no paths or raw trace bodies in model prompts. The C1 projection selects
specific positive fields and only rows classified successful under their
original trial rules. The evaluator never reads the historical treatment.

The bank imports **three observed Observatory trials** with independently
checked outcomes. Two used diagnostic replay with some synthetic inputs, and
one used actual code edits and tests on generated fixtures. Model outputs and
measurements in all three were observed. The records preserve the original
scope and archive references. One trial failed its registered quality gate
after baseline answers missed an incomplete-source warning, even though the
candidate produced fewer tokens. The follow-up surfaced source coverage in both
arms. The third trial measured a reversible tool-output optimization. Historical
hypotheses and lessons are investigator interpretations. No model call generated
them.

The benchmark has three optimization tasks, four held-out tasks and four
historical-split fixtures qualified for future prospective bank construction.
The imported bank uses separate earlier Observatory task IDs. Each task supplies
a public contract, buggy implementation and deliberately incomplete public
examples. Fresh Linux namespaces run the model's tools without network, host
workspace or grader access. The independent grader injects only arguments into
a separate candidate sandbox and compares results to undisclosed expectations
on the host. Its controls require every reference to pass and every empty patch
to fail across all eleven tasks.

## Procedure

The protocol fixes five rounds and up to one candidate per round per arm.
The proposer selects from a finite set of planning, verification, tool-use and
completion instructions. The runner records the proposed setting change,
hypothesis, rationale, prediction, and before/after prompt diff. A change must
retain all incumbent passing tasks and either solve more optimization tasks or
reduce total measured tokens by at least 10% at equal pass count. A no-op uses the
proposer budget and launches no candidate tasks. Incumbent observations are
reused within each arm. The shared initial evaluation is measured once per
repetition. Threshold selection uses optimization tasks exclusively. All four
harnesses are frozen before held-out evaluation. Even an unchanged harness
receives fresh held-out attempts.

Condition order is derived from the registered random seed. Model-side seeds
are unavailable in this transport. Up to three independent task invocations
run concurrently. The per-call wall cap is 100 seconds and there are zero
automatic retries. The registration records source hashes and exact agent
version. A started invocation with no terminal receipt blocks reuse of that
assignment. Completed invocations are reopened only after their exact prompt,
roster, schema, model and execution identity match the existing receipt.

The primary endpoint is binary pass proportion on the four held-out tasks.
The independent unit for comparing memory is the paired optimization
repetition. The analysis reports observed contrasts for the pilot and paired
run-level bootstrap and sign-flip comparisons for repeated runs. The resource
ledger separates proposals, optimization-task rollouts, held-out rollouts and
common starting evaluations. It records total input and the cached subset
without double counting, selection efficiency, and memory prompt bytes.
First native request input includes shared system context. Arm durations
and summed invocation durations are distinct because calls can overlap.
Monetary estimates are the pinned API-equivalent scenario. Subscription
cash and quota effects remain unknown.

## Reproduce

From the repo root, using the existing reviewed local S3 and PostgreSQL setup
and a ChatGPT-authenticated Codex CLI:

```sh
export PYTHONPATH=src
python -m ttgl.sim_ablation historical
python -m ttgl.sim_ablation check

RUN=work/security/sim-memory-ablation/pilot-001
python -m ttgl.sim_ablation --run "$RUN" matrix
python -m ttgl.sim_ablation --run "$RUN" resume
python -m ttgl.sim_ablation --run "$RUN" analyze --output "$RUN/analysis"
python -m ttgl.sim_ablation --run "$RUN" export --output "$RUN/export"
```

To run one arm, use `matrix --condition C0 --phase optimization` and the
same `--run`. Continue through C1–C3, then use `resume --phase heldout`.
The [registered protocol](../../../experiments/sim-memory-ablation/pilot-001.json)
and [frozen bank](../../../experiments/sim-memory-ablation/history-001.json)
are versioned in Git. Raw native traces are retained through Observatory's
approved loopback S3 path. Exact prompts, candidate diffs and execution receipts
remain private. The export lists their checksums alongside public derived
data in JSON, JSONL, CSV and SVG.

The completed summary can be published to Observatory's Experiments view.
The publisher takes an approved SHA-256 of the immutable `summary.json`,
verifies exact S3 read-back and indexes the record through the current
application database. The original SQLite source is untouched.

```sh
SUMMARY="$(realpath "$RUN/analysis/summary.json")"
(cd apps/web && node --env-file=.env.local --experimental-strip-types \
  scripts/publish-sim-analysis.ts "$SUMMARY" SHA256_FROM_REVIEW)
```

See the [research report](report.md) for the relationship to the original paper,
observed results and limits on interpretation.
