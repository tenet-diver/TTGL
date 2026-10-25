# Independent analysis audit: routing-pilot-001

Audit date: 2026-10-25. This is a post-run audit by a separate agent within the same research session, not an external replication or blinded review. The auditor knew the reported headline result before recomputation. No source code, frozen protocol, model, threshold, data split or result artifact was changed during the audit.

## Audit conclusion

**No material implementation or arithmetic error was found that invalidates the reported routing-replay result.** Independent calculations from `predictions.csv` reproduce the primary estimate and its paired contest-bootstrap interval to numerical precision. The result is inconclusive for improvement over expected random routing: the 95% interval spans zero. It does not establish successful local-model distillation, RLAIF, real-device inference or measured financial savings.

This conclusion applies to the supplied artifacts and inspected code. It is not a certificate that upstream grading is correct, model pretraining is uncontaminated, the internal protocol timing is externally authenticated, or a different implementation would reproduce original model generations.

## Independent statistical reconstruction

The audit read the CSV using Python's standard library and recomputed outcomes, selections and intervals using NumPy, without importing `ttgl.routing` or calling its statistic helpers. Per-task outcomes were compared against the processed and raw source grades. The independent bootstrap used seed `1729`, sorted unique contest groups, 2,000 draws of 34 groups with replacement, and all member tasks of each selected group. It preserved each original policy decision and the original random-policy exposure fraction.

| Quantity | Independently recomputed value |
| --- | ---: |
| Held-out tasks / contest groups | 142 / 34 |
| Remote-selected tasks | 71 (50.0000%) |
| Local empirical pass@1 | 17.323944% |
| Remote empirical pass@1 | 39.366197% |
| Expected random at matched budget | 28.345070% |
| Benefit-router empirical pass@1 | 29.929577% |
| Benefit minus expected random | +1.584507 percentage points |
| Paired contest-bootstrap 95% interval | [−1.581743, +4.436699] percentage points |
| Benefit minus remote-only | −9.436620 percentage points |
| Benefit-minus-remote two-sided 95% interval | [−13.877627, −5.816569] percentage points |
| Benefit-minus-remote one-sided 95% lower bound | −13.305244 percentage points |

The primary effect should be reported as **+1.58 percentage points, 95% CI [−1.58, +4.44]**. The positive point estimate is not statistically persuasive evidence of improvement under the planned criterion. The exploratory noninferiority criterion requires a lower bound above −5 percentage points; it is not met. Do not replace the primary comparison with a more favorable exploratory result.

The original 50% budget is exact. In bootstrap samples, frozen original selections have varying exposure because complete contests are resampled; the middle 95% of those exposure fractions is approximately 43.85%–55.56%. This is consistent with the protocol's **conditional fixed-policy contest resampling**, rather than reranking every bootstrap sample to an exact 50% budget. Both are possible estimands, but they are not interchangeable after results are known.

## Data integrity and split checks

- All hashes verified: original protocol, amendment, split manifest, three processed datasets, both pinned raw-source files, executed routing code, and every result artifact listed in the run manifest.
- All 713 processed tasks equal the intersection of the two raw task maps. Every processed prompt, sanitized code array and grade array exactly matches the corresponding source fields for both models.
- Split sizes are 429 training, 142 calibration and 142 test tasks, with 116, 38 and 34 contest groups respectively. The code keeps `(platform, contest_id)` groups intact and joins models by `(platform, question_id)`.
- Date ranges are disjoint in this dataset: training 2023-05-07–2024-03-23; calibration 2024-03-30–2024-07-06; test 2024-07-13–2024-10-05.
- No exact prompt-text duplicate crosses these splits. This does not establish absence of semantic duplicates, reused templates or model-pretraining contamination.
- No shared task was dropped. The 342 remote-only tasks were excluded by the predetermined intersection rule; conclusions therefore concern the overlap, not the remote model's complete submission.
- Every task contributes the mean of ten published boolean grades. This is an empirical per-draw success estimate, not pass@10. The two models' generation indices are not treated as paired random seeds.

## Failed extraction and upstream grading

The dataset retains empty sanitized-code attempts as observed upstream failures. Across the 713 overlapping tasks, Qwen has 22 empty sanitized-code entries and DeepSeek has 291; none carries a true grade. These are nonempty raw-generation records whose extraction/evaluation failed, so removing them after seeing grades would select on outcomes.

All 14,260 sample metadata records in the overlap parse as JSON. Upstream feedback includes wrong outputs, runtime and syntax errors, timeouts and testing errors. Some messages reflect a code/environment interaction: missing-module errors occur in training tasks `leetcode:3000` (2 Qwen samples, 10 DeepSeek samples) and `leetcode:3363` (1 Qwen sample). The DeepSeek messages for task 3000 name `sortedcontainers`. The audit did not rerun these samples or classify them as purely model versus infrastructure failures.

They remain in the frozen corpus. The appropriate limitation is that outcomes measure the **published generation, extraction and test environment together**. They are not a clean measure of reasoning alone. No missing-module error was found in the held-out sample metadata during this audit, but other upstream testing assumptions remain unverified.

## Model fitting, calibration and leakage review

Only training prompt text and log character length enter the feature map. TF-IDF vocabulary and standardization are fit on training tasks; only transformed features are used for calibration/test. Platform, official difficulty, IDs, dates, generated code, grades and evaluation feedback do not enter the fitted predictor features. Test metadata labels are used only for ordering ties, grouping and descriptive reporting. The batch allocator uses unlabeled test scores, as explicitly declared by the protocol; it is not a streaming threshold policy.

The soft-label logistic implementation is correct for the specified objective. A task with empirical success `y` is duplicated with labels 0/1 and weights `1−y`/`y`. Its total weight is one and its weighted loss is the Bernoulli cross-entropy for `y`; it does not multiply the effective task count by ten. L2-regularized `liblinear`, `C=1`, clipping and iteration limits match the frozen amendment. The four saved estimators converged in 4, 7, 4 and 4 iterations, respectively.

The calibration stage uses calibration outcomes only, with a one-feature logistic model of the raw logit. This is a regularized Platt-style transform, not a proof of calibration under distribution shift. The sample-level Brier calculation `p²−2py+y` correctly averages binary squared error over equal-sized sample sets. It differs from squared error against each task's empirical mean by within-task label variance; the code and amendment label that distinction.

Oracle allocation reads test outcomes only for the explicitly nondeployable ceiling. Its attractive score must not be attributed to a learned system. Hyperparameters and policies are fixed in the inspected code; the audit found no test-outcome-based tuning branch. Code inspection cannot independently establish that no human inspected or selected results before the recorded freeze.

## Reliability and interpretation risks

There is substantial chronological outcome shift:

| Split | Local mean pass@1 | Remote mean pass@1 |
| --- | ---: | ---: |
| Training | 42.214452% | 69.114219% |
| Calibration | 26.408451% | 62.957746% |
| Test | 17.323944% | 39.366197% |

On test tasks, the mean calibrated remote prediction is **59.819870%**, versus **39.366197%** observed success. The mean local prediction is **23.404094%**, versus **17.323944%** observed. Calibration improved the recorded Brier scores relative to raw predictors, but the remote predictor still substantially overpredicts success. Calling it a “calibrated model” should denote the fitting procedure, not assert good out-of-time calibration. The changing prevalence may reflect difficulty composition, model-data familiarity or other temporal differences; this audit cannot identify its cause.

At the primary budget, the policy delegates 80.56% of easy, 45.83% of medium and 34.48% of hard tasks. This is consistent with an expected-benefit objective allocating scarce remote calls where solvable improvement is predicted, rather than always sending the hardest problems remotely. It must not be marketed as evidence that this predictor recognizes all difficult tasks. These subgroup outcomes are descriptive and were not used to retune the policy.

The test platform strata contain 15 AtCoder and 19 LeetCode contests. Easy/medium/hard strata cover 25/32/28 distinct contests, with contests potentially present in multiple difficulty strata. The current `subgroups.csv` contains task counts but omits group counts requested by the amendment; these audit counts close that reporting gap without changing the result artifact.

Other limitations to preserve in the report:

1. Intervals condition on fitted models, one split and the recorded ten-sample means. They omit model-refitting variability, original generation-sampling uncertainty and unobserved provider configuration differences.
2. The future contest sample has only 34 clusters; precision is limited. A null result does not establish no useful routing method exists.
3. Task-level exact-match and group separation do not certify model-training or semantic-task decontamination.
4. Equal remote-call counts do not imply equal token charges, latency or energy. Normalized cost scenarios are assumptions, not observed dollar savings.
5. Qwen-7B/DeepSeek-V3 archived outputs are not evidence about a quantized laptop deployment, DeepSeek-V4.1-Flash, interactive repair trajectories or trained adapters.

## Provenance observations and audit boundary

**Low-severity timestamp wording discrepancy:** the frozen amendment describes the original protocol as frozen at `22:04:57Z`; the machine-written freeze manifest records `22:06:39.752952Z`. The lead investigator reports the former as protocol-completion time and the latter as persisted freeze time. The amendment's persisted time is `22:08:39.452525Z`. Preserve these originals and this explanation; do not rewrite a frozen file to make timestamps appear identical. Both reported times precede the amendment and run, but this is internal session provenance, not a trusted third-party preregistration timestamp.

The run manifest identifies the executed routing module by SHA-256 and the input/artifact hashes, but does not itself hash every ancillary module or establish a signed Git revision. Raw-to-processed source equality was independently checked here. A future replication package should pin the full source tree and dependency lock alongside these existing artifact hashes.

This document adds post-run checks and limitations only. It changes neither the primary estimand nor the pre-analysis protocol and reports no new tuned experimental arm.
