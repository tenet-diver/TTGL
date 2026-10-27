# Interim held-out checkpoint: seven of eleven tasks

This is an interim snapshot, not a completed study or a stopping decision.
All 21 assignments in seven complete task blocks passed independent official
patch/report joins and native event-delta accounting. The registered study
continues unchanged to 33 assignments.

| Condition | Officially resolved | Total model-cost scenario (USD) | Completed expert consultations |
|---|---:|---:|---:|
| Luna alone | 5/7 | 0.04639970 | 0 |
| Sol alone | 7/7 | 1.15456560 | 0 |
| Fallback Luna/Sol conversation | 6/7 | 0.08409922 | 2 |

The assisted arm resolves one case missed by Luna and loses none of Luna's
successes on this checkpoint. It closes half the observed Sol–Luna resolution
gap, at an extra USD 0.03769952 token-rate scenario cost over Luna. Savings
versus Sol are 92.7159%, with 85.7143% relative accuracy retention. Both miss the
joint 95/95 target. The rates are the study's frozen published Codex Standard
scenario, not an invoice, subscription allocation or full deployment cost.

![Interim cost versus retained accuracy](figures/frontier.png)

## Observed rescue episode

`sphinx-doc__sphinx-10673`: Sol succeeds, Luna fails, assisted Luna succeeds.
The assisted agent returned `ask_expert` while reporting that its new regression
test exposed continuing warnings. Sol requested exact source and builder
observations rather than guessing a repair. Luna's next message identifies the
earlier directive-parser warning path. Sol advised retaining generated entries
outside source-document dependencies and using a valid Python module-index
fixture. Luna's final patch passes the independent official grader.

Both consultations use the same retained expert thread, with the first response
requesting context and the second answering. This demonstrates voluntary
multi-turn escalation in a real benchmark episode. It does not prove Sol caused
the entire improvement: Luna independently located the root warning path before
the second expert answer, and the standalone control is a different attempt.
The old runner did not retain a pre-consultation patch for independent regrading.
The new Pro diagnostic captures that snapshot prospectively.

The handoff is imperfect. The first message summarizes a failing check without
the exact source. The second supplies repository paths rather than the requested
code excerpts, even though the context-only expert cannot inspect those paths.
Sol explicitly retains uncertainty about the exact availability predicate. This
is a limitation to analyze, not a reason to change the active frozen policy.
Local test counts in the final summary remain self-reported; independent grader
success and native invocation/token records are audited.

The separate `scikit-learn-25747` case remains unresolved by assisted Luna, which
made no consultation there. Explicit test failures and unobserved coverage gaps
are different routing challenges. Seven cases do not establish reliable failure
detection, noninferiority or population improvement. Do not tune on the remaining
held-out outcomes or stop the study because this interim result is favorable.

Evidence: `checkpoint-routing-rescue-002.json`, `published-rate-records.json`,
`target-and-added-value.json`, `rescue-episode.json`, and graph provenance.
