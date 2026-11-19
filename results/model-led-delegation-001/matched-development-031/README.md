# Matched development and baseline calibration

The original 12 development tasks each received a standalone Luna and Sol
attempt with the same final knowledge snapshot. All 24 attempts completed,
with 4,176,013 native tokens reconciled against the archived event streams.
Two prescribed evaluator replays on one task reached their deadline. Recovery
036 retained both grades as unknown and independently finished the other
grades without additional model calls.

| Outcome | Luna | Sol |
| --- | ---: | ---: |
| Assigned | 12 | 12 |
| Known official resolutions | 6 | 6 |
| Unknown official grades | 1 | 1 |
| Resolutions with the original public check and valid scope | 3 | 3 |
| Resolutions with the portable public check and valid scope | 5 | 6 |

All 24 exact candidates passed the portable public smoke check. The official
grade and edit-scope gate still apply. On the 11 fully graded pairs, Luna
incurred 95.4% lower inference cost in the frozen historical-rate scenario
and had one fewer admissible resolution. Subscription cash remains unknown.

Both released-method adaptations passed the registered numerical sufficiency
gate using the 11 paired labels. On the portable view the FrugalGPT quality
scorers' out-of-fold Brier scores were 0.2978 for Luna and 0.2999 for Sol,
compared with 0.3000 for each constant prior. Each method selected the same
operating point across its three budgets. These are development calibration
results. The native released-baseline and held-out comparisons are pending.

[Accounting and calibration summary](summary.json) · [Model registration](../../../experiments/model-led-delegation-001/matched-development-031.json) · [Portable smoke check](../../../experiments/model-led-delegation-001/public-check-amendment-034.json) · [Grade recovery](../../../experiments/model-led-delegation-001/development-grade-recovery-036.json)
