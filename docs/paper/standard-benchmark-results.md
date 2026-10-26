# Industry-standard benchmark: a 500-task routing replay

## Data and interpretation

We executed a new routing analysis on **all 500 SWE-bench Verified tasks**, using
the ten complete public submissions dated 17 February 2026 in the official
SWE-bench experiments repository [@ttglsweexperiments2026]. Each submission uses
mini-SWE-agent 2.0.0 and supplies per-instance resolution, estimated inference
cost and API-call counts. This gives 5,000 recorded model–task outcomes, not
5,000 independent tasks. Costs and accuracies reconcile to every submission's
published metadata. The source revision is
`40f164d5b8f1d249bf95a6df8b74b577fd8e519d`; task text comes from the official task
repository at `3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d`.
Canonical task identifiers join the records. We did not independently establish
that this later task-text snapshot is byte-identical to every original model
prompt used in February.

These are **new router fits and outcome replays of previously executed agents**.
We did not rerun those ten models, infer unseen patches, or observe their current
prices. Their historical outcomes are held fixed while we select among them.
This experiment measures the cost–quality opportunities and limits of pre-task
selection in this portfolio. It does not identify the effect of bidirectional
communication, distillation, local inference or Codex subscription consumption.
Same-harness-version comparisons still differ in model-specific settings,
reasoning effort, service behavior and potentially execution conditions.

The protocol and model grid were frozen before fitting. Aggregate source
accuracies and prices had already been inspected during dataset selection, so
this is exploratory secondary analysis, **not prospective preregistration**.
All scripts, source hashes, folds, numerical task records and results are
archived under `experiments/swe-replay-001` and `results/swe-replay-001`.

## Routing method and leakage controls

Five task folds use seed 1729. For each held-out fold, training uses only the
other 400 tasks. Word unigram/bigram TF–IDF, logarithmic issue length and a
repository indicator feed per-model logistic success predictors and ridge
regressors of log-transformed task cost. The vectorizer and transformations are
fit only on that fold's training data. Test patches, reference solutions,
trajectories, actual held-out cost and held-out outcomes are excluded from
decision features. An instance identifier is used only for deterministic ties.

The primary policy allocates GPT-5.2 to half the tasks and GPT-5-mini to the
remainder, ranked by predicted success gain per predicted incremental dollar.
Allocation takes place within each held-out fold. A global ranking over
cross-fitted predictions could otherwise let a task's label influence competing
tasks' scores through their training folds. The within-fold quota avoids that
indirect selection path. This is a batch allocation policy, not a validated
online arrival-by-arrival budget controller.

Fixed single-model policies, random allocation, length and predicted-gain
baselines, a declared allocation grid, and a ten-model expected-utility grid
are also evaluated. Utility is predicted success minus a fixed coefficient
times predicted task cost. A separate subgroup uses models tagged open by the
source metadata; that tag is not our license audit or evidence that the models
run on a desktop. A label-and-cost-informed oracle is deliberately marked
nondeployable. Its apparent performance is an upper bound conditional on these
recorded attempts, never a usable router result.

## Primary result: savings with an unacceptable quality loss

| Policy | Resolved | Success | Estimated inference USD/task | USD/resolved task | Saving vs GPT-5.2 |
|---|---:|---:|---:|---:|---:|
| GPT-5-mini alone | 281/500 | 56.2% | 0.0472 | 0.0840 | 90.0% |
| GPT-5.2 alone | 364/500 | 72.8% | 0.4736 | 0.6505 | Reference |
| Expected random 50% mixture | 322.5 expected | 64.5% | 0.2604 | 0.4037 | 45.0% |
| Primary learned 50% router | 321/500 | 64.2% | 0.2551 | 0.3974 | 46.1% |

The primary router's estimated inference total is **US$127.5667**, compared with
**US$236.7835** for the GPT-5.2 reference on the same 500 tasks. Its 46.1% saving
comes with an **8.6 percentage-point** resolution loss. The paired task-bootstrap
95% interval for the quality difference is approximately **−11.6 to −5.6 points**;
the estimated saving interval is **40.8% to 51.4%**. Repository-cluster sensitivity
also fails the quality gate. The proposed three-point noninferiority margin is
not supported. This is a negative result for the primary joint target, despite
a substantial cost reduction.

The learned router also does not demonstrate a useful accuracy improvement over
the expected random half-mixture: its paired difference is −0.3 points with a
task-bootstrap 95% interval from −2.4 to +1.9 points. The corresponding cost
ratio is 0.980, with interval 0.884 to 1.076. A cheaper policy is not useful evidence for
the central hypothesis when its success falls outside the declared tolerance.
The paired outcomes include 262 issues both models solve, 19 solved only by
GPT-5-mini, 102 only by GPT-5.2, and 117 by neither. The existence of complementary
successes does not imply that pre-task features can reliably identify them.

The primary router's break-even additional overhead is about US$0.2184 per task;
only US$0.1000 per task remains if a 25% inference-plus-overhead saving is the
target. Adding a hypothetical US$0.05 overhead per task lowers its saving to
35.6%, without repairing the observed quality loss. These overhead values are
sensitivity assumptions, not measured router or environment bills.

## Portfolio comparison: a strong cheap single model is essential

All rows below use all 500 recorded assignments. The costs include failed
attempts. They are historical upstream estimates, not current provider quotes.

| Published model | Success | Estimated inference USD/task | USD/resolved task |
|---|---:|---:|---:|
| GPT-5-mini | 56.2% | 0.0472 | 0.0840 |
| GPT-5.2, high | 72.8% | 0.4736 | 0.6505 |
| DeepSeek-V3.2, high | 70.0% | 0.4478 | 0.6398 |
| Kimi-K2.5, high | 70.8% | 0.1466 | 0.2070 |
| MiniMax-M2.5, high | 75.8% | 0.0733 | 0.0967 |
| GLM-5, high | 72.8% | 0.5344 | 0.7341 |
| Gemini-3-Flash, high | 75.8% | 0.3560 | 0.4696 |
| Claude-Haiku-4.5, high | 66.6% | 0.3309 | 0.4969 |
| Claude-Sonnet-4.5, high | 71.4% | 0.6579 | 0.9214 |
| Claude-Opus-4.6 | 75.6% | 0.5515 | 0.7295 |

MiniMax-M2.5 alone resolves **379/500** at **US$0.0733 per assigned task**. Its
historical estimated inference cost is 84.5% below the GPT-5.2 reference, with
a three-point higher observed success rate. This is evidence about **model
choice in the archived comparison**, not a routing effect and not a local-small-
model result. Model size cannot be inferred from price or the word "mini".

For illustration within the prespecified exploratory grid, the ten-model
utility policy at coefficient 0.25 resolves **381/500 (76.2%)** at **US$0.1154 per
task**. Compared with GPT-5.2, that appears attractive: 75.6% lower estimated
inference cost and 3.4 points more success. Compared with MiniMax alone, however,
it adds only two resolved issues while costing approximately **57.4% more**.
The quality-difference interval is −0.8 to +1.6 points, while the cost-ratio
interval is 1.398 to 1.762. These additional paired comparisons are explicitly
labelled exploratory and conditional on the fitted policies.
This operating point is not declared a winner after searching the grid. The
whole grid and comparisons with the inexpensive standalone model are retained.
Attributing all of the difference versus an expensive reference to intelligent
routing would be misleading.

The recorded ten-model oracle resolves 87.8%, while the two-model oracle
resolves 76.6%. These bounds suggest potential complementarity, but the oracles
use the answers and realized costs. They do not demonstrate that an available
router, personal agent or conversation policy can achieve those figures.

![Historical SWE-bench Verified cost–quality operating points with standalone controls. Router points replay held-out model selections; the oracle uses unavailable test outcomes. Costs omit unobserved deployment expenses.](../../results/swe-replay-001/figures/standalone-controls.png)

## Statistical and economic limits

Intervals use 2,000 paired resamples and condition on the fitted cross-fold
policies and the recorded outcomes; they do not refit the router inside every
bootstrap sample. A repository-cluster sensitivity analysis uses only twelve
clusters. Training and test folds can share repositories, so repository-unseen
generalization is not established. One recorded attempt per model and task
cannot estimate repeated-inference variance. Grid comparisons are exploratory
and do not support a familywise claim from choosing their best point.

Upstream numerical costs are preserved rather than replaced by current prices.
They are not independently audited invoices. Two unresolved Gemini entries
report zero cost despite one API call each; these values are not proof of free
inference. Neither the primary policy nor the illustrated portfolio selects
those entries. Their effect on other policies is recorded in the supplementary
cost-source checks. Router fitting took roughly two CPU seconds in
this run, but no electricity, machine allocation or test-execution dollar rate
was measured. Total operational cost and Codex subscription-credit savings
remain unknown. No new model-inference purchase was needed for this replay.

The implications for the conversational study are concrete. First, retain a
strong low-cost standalone model in the comparison. Second, ask whether runtime
evidence and conversation improve the weak pre-task selection result. Third,
measure all controller, expert, verification and failed-attempt usage before
claiming savings. The replay supplies a reproducible benchmark finding and
better controls; the causal bidirectional-conversation experiment still needs
fresh metered execution.
