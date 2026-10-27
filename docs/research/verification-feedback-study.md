# Failure recognition and test-feedback study

## Question and current observation

The goal remains at least 95% lower total model-inference cost while retaining
at least 95% of matched Sol accuracy. It is a research target, not a stopping
condition that licenses unlimited prompt search or selective reporting.

On the first completed held-out task, `scikit-learn__scikit-learn-25747`, the
fallback-assisted Luna returned complete with zero consultations. Its final
summary claimed a passing reproducer, 15 focused tests and 103 broader tests.
The official independent report says unresolved, with no infrastructure failure.
The archived patch changes index handling only when row counts differ. This is
evidence of a false completion judgment under available feedback, not proof that
Luna consciously ignored an observed failing acceptance test. The native pilot
journal retains tool hashes/statuses, not complete command outputs; the claimed
test counts cannot be independently reconstructed from that journal. Do not
relabel those self-reported counts as audited checks.

This case is now observed evaluation evidence. It cannot become a fresh held-out
case for the new policy. Its grader output and reference patch never go into a
live controller prompt. The running 33-assignment study and its frozen v2
sources are unchanged.

## Benchmark assessment (27 October 2026)

| Benchmark | Agent-visible verification | What it can establish here |
|---|---|---|
| SWE-bench Verified / reserved Pro V2 subset | Repository tests and agent-created reproducers; independent evaluator tests withheld | Transfer to realistic repairs; passing a local test does not certify evaluator success |
| Aider Polyglot | Official harness returns test errors after an unsuccessful implementation, with two attempts by default | Whether useful execution feedback changes repair and consultation behavior on a multi-language coding set |
| LiveCodeBench self-repair | Maintained self-repair scenario consumes previous code-generation/evaluation records | A useful follow-up with dated contest tasks; audit feedback construction before claiming public-only feedback or reusing private evaluation outputs |
| Terminal-Bench / Harbor | Interactive terminal checks; independent task verifier remains separate | Broader operational transfer; switching benchmarks does not itself make self-verification complete |

Primary sources: [SWE-bench Verified evaluation explanation](https://openai.com/index/introducing-swe-bench-verified/),
[Aider benchmark harness](https://github.com/Aider-AI/aider/blob/main/benchmark/benchmark.py),
[Aider Polyglot source](https://github.com/Aider-AI/polyglot-benchmark),
[LiveCodeBench self-repair documentation](https://github.com/LiveCodeBench/LiveCodeBench#self-repair),
and [Terminal-Bench / Harbor release](https://www.tbench.ai/news/announcement-2-0).
No current leaderboard number is used as a matched control. Public Exercism
exercises carry contamination and scope limitations relative to repository repair.

## New candidate and bounded data reservation

`verification_policy.py` adds an explicit evidence challenge to the frozen
fallback policy. It asks for acceptance criteria, discriminating checks, important
coverage gaps and a supported/contradicted/incomplete completion summary. The
assisted extension allows consultation for an important unsupported property
even when a narrow test passes. Standalone Luna and Sol receive the same new
common verification instructions. Expert roles and thread continuations retain
their existing semantics. This is a candidate, not an observed improvement.

The Aider source is pinned to `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`.
`experiments/verification-feedback-001/reservation.json` records 12 development
and 24 disjoint validation assignments, balanced across six languages from 225
tasks. All development exercise families are excluded from validation across
languages, avoiding translated-exercise leakage. Validation has 23 families, so
uncertainty estimates must cluster by family. Inventory order does not affect
selection. Only instructions and inventory metadata have been acquired; no
reference solutions, tests, or model outputs have been downloaded for this study.

## Prospective execution and analysis

Finish the frozen current study first. Keep its held-out outcomes separate from
new development. Complete the queued Pro environment controls and real adapter
boundary/metering/replay checks. For the feedback diagnostic, reuse maintained
language test commands and dependency setup; do not replace their assertions with
custom easier checks. Preserve track-specific Exercism licenses. Prove empty
failure, reference success, offline source isolation, immutable tests and fresh
regrading on one task before scored inference. The existing Pro queue does not
launch this diagnostic automatically.

Development compares four matched arms: v2 fallback Luna/Sol cooperation; v3
Luna alone; v3 Sol alone; and v3 Luna/Sol cooperation. The v2 arm is an ablation,
not the standalone control for v3. All arms receive the same bounded test-error
feedback opportunity. Start with one complete task block and inspect measured
tokens/runtime before expanding to 12. Freeze source, task order and exact
feedback budgets before that first block. No more than 48 development assignments
are authorized by this design; no full 225-task launch follows automatically.

After a first candidate, the maintained test harness produces a bounded failure
observation or a pass. Preserve both the first and final outcomes. A second
attempt may repair independently or consult Sol; all stages, expert requests and
integration count toward the same per-task time and model-cost total. The test
budget, error truncation, worker visibility and solver-turn limits must be
identical across arms and recorded in the final executable registration.
Controller-selected checks are distinct from mandatory harness feedback. An
automatic test gate is an orchestrator decision, not evidence that Luna detected
the error unaided. Run the unchanged final tests in a fresh environment, reject
test/harness modifications, and label these as Aider-derived conversational
results rather than official Aider leaderboard scores.

Select a cooperative policy using development resolution count, then total model
cost, then a fixed lexical tie break. Freeze it before the 24-task validation
panel (72 assignments including matched standalone controls). Match the
validation standalone common prompts to the selected policy:
v2 common guidance if v2 is selected, v3 common guidance if v3 is selected.
The development v2 arm is a whole-policy comparison; it cannot isolate the
effect of delegation using v3 standalone controls. Do not tune on the validation
panel or repeatedly sample it until a preferred result appears. Keep any later
policy generation and validation reservation separately versioned.

Report final quality and total cost together with: first-attempt success;
remaining observed failures; consultation rate after genuine failure feedback;
independent-repair and expert-assisted recovery; unresolved-failure completion;
unnecessary consultations on independently correct candidates; and regressions
after integration. Distinguish syntax/test failure from unavailable dependencies
or access. Abstention is not a solved task. Visible-suite success is test fit;
generalization is assessed separately by unseen tasks and the withheld repair
grader. Do not assert detection recall for hidden failures without an independent
per-candidate correctness label. Missing trace evidence stays unknown.

Twelve development and 24 validation tasks are iteration panels, not proof of
95% reliable detection. Even with independent failure opportunities and zero
misses, 59 observed failures are required for a one-sided 95% exact binomial
lower bound to exceed 95% detection recall. Correlated exercise families weaken
that calculation further. Report numerators, denominators and uncertainty; a
larger confirmatory reservation would follow a useful small-panel result, with
its size and spending scope registered before inference.

If savings require accepting false completion, report the frontier failure. If
reliable delegation requires more Sol calls than the 5% cost budget permits,
report that tradeoff instead of forcing the 95/95 claim. No training or RL result
is implied by these prompt and feedback experiments.
