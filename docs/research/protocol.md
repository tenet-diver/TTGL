# Study protocol: confidence-aware delegation for a local coding model

**Protocol date:** 2026-10-25. **Status:** prospectively specified internal analysis protocol, frozen before inspecting aggregate/model-comparison outcomes. This is not an external registry preregistration. Record this file's SHA-256 and the split manifest before the first analysis; record subsequent deviations rather than silently editing the frozen protocol.

## 1. Research objective and scope

Determine whether a small, inexpensive predictor can allocate a fixed remote-model budget more effectively than random allocation when choosing between a local-capable Qwen coding model and a stronger remote-model candidate. The proposed mechanism is calibrated **expected benefit of delegation**, rather than assuming local-model uncertainty alone identifies where a remote model helps.

The primary experiment is a reproducible **offline replay of published paired coding-benchmark generations and correctness outcomes**. It does not run the models, execute an interactive agent, measure laptop inference, or establish that the remote candidate is stronger on every task. “Local” and “remote” below identify intended deployment roles. Published results for Qwen2.5-Coder-Instruct-7B and DeepSeek-V3 are not measurements of quantized laptop Qwen or DeepSeek-V4.1-Flash.

Secondary study designs cover verified sequence distillation and preference learning. They remain **planned and unrun** unless hardware, weights and compatible training/evaluation jobs become available and their real outputs are recorded. A completed routing replay does not establish completion of those training experiments.

## 2. Research questions and hypotheses

- **RQ1 — allocation:** At a fixed 50% remote-call budget, does a prompt-only expected-benefit router improve empirical pass@1 relative to expected random allocation?
- **RQ2 — confidence:** Does estimating both models' success probabilities improve allocation over routing according to predicted local failure alone? This is an exploratory comparison.
- **RQ3 — tradeoff:** What accuracy/remote-exposure frontier is observed at 0%, 25%, 50%, 75% and 100% remote allocation, and under assumed local/remote cost ratios?
- **RQ4 — reliability:** Are predicted success probabilities calibrated on future contest groups, and which platforms/difficulty strata exhibit errors or concentration of escalation?
- **RQ5 — improvement, planned:** Does verified teacher-output fine-tuning improve held-out local success and reduce required remote exposure without unacceptable regressions? Does preference learning add value beyond SFT at comparable training/data budgets?

**Primary directional hypothesis:** the expected-benefit router's held-out mean pass@1 exceeds the expected random policy at the same 50% remote budget. A two-sided 95% paired confidence interval for the difference is reported; a positive lower bound is evidence for improvement on this corpus. A nonpositive interval is reported without selecting a different budget or model as a replacement primary endpoint.

**Exploratory noninferiority question:** Is routed pass@1 within 5 percentage points of remote-only? Report a one-sided 95% lower confidence bound for routed-minus-remote; noninferiority requires it to exceed −0.05. This margin is a planning choice, not a user-validated product threshold. Failing to demonstrate noninferiority is not proof of inferiority.

## 3. Dataset and eligibility fixed before analysis

Use the official [LiveCodeBench submissions repository](https://github.com/LiveCodeBench/submissions), pinned at commit `6ca212e9c2039373f6e5069d37ffa9db66e23736`, for `Qwen2.5-Coder-Ins-7B` and `DeepSeek-V3`. Preserve exact source URLs, SHA-256 hashes, retrieval timestamps, upstream documentation/license and generation settings in provenance files. The observed source filenames identify temperature 0.2 and ten samples; do not claim to control original inference conditions.

The metadata inspection identified 713 shared tasks dated 2023-05-07 through 2024-10-05, grouped into 188 `(platform, contest_id)` contests. Eligibility is the intersection of unique `(platform, question_id)` records with matching task prompt/title/date/contest/difficulty/starter-code metadata, exactly ten nonempty raw generation strings, and ten aligned boolean correctness labels for each model. Fail closed on duplicate IDs, metadata disagreement, nonboolean labels or unaligned arrays. Record exclusions and reasons before any metric computation.

An empty sanitized `code_list` entry is an **observed generation/extraction failure**, not a missing attempt: retain its upstream grade. Dropping unsuccessful code extraction would bias the sample. Training-data export may later require both nonempty code and verification, but that filter must not change the routing test corpus.

The study reuses upstream test outcomes. It does not rerun or certify the underlying tests. Upstream `metadata` includes evaluation feedback; exclude it from every router feature. Execution times in that metadata measure submitted-code execution, not model generation latency, and cannot be used to price inference.

## 4. Units, outcomes and split

The sampling/analysis unit is the **task**, with contest as a dependence cluster. For task `i`, compute `y_local_i` and `y_remote_i` as the mean of the ten boolean grades from the respective model. These are empirical single-draw success estimates (pass@1), not pass@10. Every task has equal weight regardless of prompt length or contest size. Do not treat the 7,130 generations as independent tasks, and do not assume generation index `j` has paired random seeds across models.

For each `(platform, contest_id)` group, compute the latest task timestamp. Sort groups by that timestamp and then by the group key. Choose cumulative group boundaries whose task counts are nearest 60% and 80% of all tasks, resolving equal distances toward the earlier boundary; require three nonempty disjoint splits. Assign the first segment to training, the second to calibration and the last to test. Keep complete groups together. One inspected contest has two timestamps; the group-maximum rule resolves this deterministically. Complete-group constraints mean task proportions may differ slightly from 60/20/20; report resulting task/group counts and date ranges.

Write a manifest listing every task/group, split, ordering key and source hashes before outcome summaries. Check pairwise-disjoint task IDs and contest groups. No test outcomes, grades, reference code, generated code, official difficulty, evaluation metadata, pass fields or result summaries enter model fitting, feature selection, calibration or hyperparameter selection. Platform/difficulty are reserved for reporting. Model training contamination from public programming problems remains a threat even with a temporal router split.

## 5. Features and fixed models

Use prompt text available **before generation**: question title, problem statement and starter code in a fixed documented concatenation. Fit a scikit-learn TF-IDF vectorizer on training prompts only: word unigrams/bigrams, `max_features=5000`, `min_df=2`. Add standardized `log1p(prompt character count)`, with its scaling fit only on training data. Task/contest IDs and dates are used for grouping and deterministic ties, not as predictors. Do not change feature extraction after inspecting test performance.

Fit separate L2-regularized logistic regressions for local and remote success, with `C=1`, deterministic seed `1729`, and a documented solver/iteration cap. Use soft Bernoulli targets `y_model_i`: represent each task by two identical feature rows, labels 0 and 1, with weights `1-y_model_i` and `y_model_i`. Each task therefore contributes total weight one. This minimizes the Bernoulli cross-entropy for empirical per-draw success without pretending that a fractional target is a binary class. Record convergence warnings; do not silently treat a failed fit as valid.

Fit one Platt-style calibration model per predictor using **only calibration tasks**, taking the raw predictor logit as its input and the same soft Bernoulli target weighting. Clip probabilities for numerical stability; record exact settings. Calibration is fit once. Handle degenerate class support with an explicitly reported constant-probability fallback or fail the learned-model arm; never inspect test labels to choose a remedy. Use calibration curves, Brier score and a ten-bin expected calibration error descriptively on test data.

Define learned routing score `s_benefit(x) = calibrated_p_remote(x) - calibrated_p_local(x)`. This can be negative: a remote model need not help every task. The comparator local-uncertainty score is `s_uncertainty(x) = 1 - calibrated_p_local(x)`.

## 6. Policies and budgets

Evaluate these predeclared policies on identical held-out tasks:

| Policy | Selection rule |
| --- | --- |
| Local-only | Select the published Qwen outcome for every task |
| Remote-only | Select the published DeepSeek outcome for every task |
| Expected random | At remote fraction `b`, task-level expected outcome is `(1-b)y_local + b y_remote` |
| Prompt-length rule | Delegate the longest prompts first; no outcome-trained rule |
| Local-uncertainty router | Delegate highest predicted local failure first |
| Expected-benefit router | Delegate highest predicted remote-minus-local success first |
| Oracle bound, diagnostic only | Rank by observed `y_remote-y_local`; clearly mark nondeployable and never use for tuning |

For a budget fraction `q`, select exactly `floor(q * N_test)` tasks by descending score, resolving ties with the stable task key. The primary budget is `q=0.50`; `q=0.25` and `q=0.75` are exploratory, with 0/1 endpoints. Set random baseline fraction `b=floor(q*N_test)/N_test` so exposure is exactly matched in expectation. The random expectation is analytical, avoiding a lucky or unlucky single random draw; optional seeded random permutations are diagnostic only.

This is **batch/queued allocation**: unlabeled test-batch scores determine which requests use a fixed budget. It is not a streaming router and must not be presented as one. An optional secondary streaming simulation may freeze a score threshold from calibration and report the realized test exposure, but it cannot replace the primary result. Comparing a test-optimized threshold to an untouched baseline is prohibited.

A selected action yields `z_i = (1-a_i)y_local_i + a_i y_remote_i`. Compute mean quality, remote exposure, local accepted-work contribution and quality gaps on the task scale. This replay selects one already-generated candidate distribution; it does **not** measure a failed-local-then-remote repair cascade, confidence-guided token decoding, tool use, or the extra context generated by an interactive agent.

## 7. Statistics and interpretation

Report task/group counts; both model means; all predeclared policy results; the primary expected-benefit-minus-random contrast; and exploratory uncertainty-rule, prompt-rule and remote-only contrasts. Report absolute percentage-point differences and uncertainty, not just relative percentages.

Use **2,000 paired contest-cluster bootstrap replicates**, seed `1729`: sample test contest groups with replacement, include every task in sampled groups, and compute paired differences using the same resampled groups for both policies. Keep trained models, calibration and original test routing decisions frozen in this primary bootstrap. Compute the quality mean over sampled tasks, not a mean of contest means, so large contests retain their original task weight. Report percentile 95% intervals and the number of clusters. These intervals are conditional on the fitted model and recorded generation outcomes; they do not include all training-set or original model-sampling uncertainty.

For expected-random paired comparisons, keep the original design fraction `b` in the task-level expectation when resampling. Bootstrap replicates can have different realized selected exposure because complete groups are resampled; report this as a limitation of conditional cluster resampling. Do not relabel the resulting uncertainty as a randomized controlled online trial.

Only RQ1 at 50% is confirmatory within this internally frozen protocol. Budget curves, calibration, subgroup comparisons and noninferiority are exploratory; report them all and avoid choosing the best as the main finding. If formal p-values are added, specify their test and multiplicity adjustment before use; confidence intervals are sufficient for the planned primary analysis.

Power is limited by the held-out contest count. The effective sample size is smaller than the task count when outcomes within contests correlate. A 5-point noninferiority margin may be unresolved even when point estimates look similar. Provide a sensitivity or minimum-detectable-effect discussion using empirical paired variability, clearly marked post hoc; it cannot retroactively turn an inconclusive result into evidence of equivalence.

## 8. Cost and resource accounting

No original model inference latency, GPU utilization, energy or validated API prices are available in the replay. Report remote-call reduction and **normalized assumed cost sensitivity**, not measured dollar savings or local speedups. Normalize one remote call to cost 1 and evaluate assumed local-call ratios `r` in `{0, 0.01, 0.05, 0.10, 0.25}`. For primary **pre-call selection**, normalized expected cost is `(1-b)r+b`; exactly matched-budget policies have the same cost under this simplified model, so their comparison tests allocation quality. A **post-local escalation** scenario would cost `r+b`, because every task first pays for local generation; this can be shown as a sensitivity illustration only, since no post-local features or repair cascades are evaluated. Compare quality per cost where defined. At `r=0,b=0`, quality/cost is undefined and must not be reported as finite or infinite profit.

These fixed-call ratios ignore input/output length, model-specific tokens, batching, idle GPU costs, download/training costs and latency. Output characters, if reported, are descriptive length proxies only; they are neither token counts nor token prices. Router fit and replay wall time may be measured on this machine and explicitly separated from LLM inference timing.

## 9. Leakage, selection bias and robustness

- Use complete paired submissions rather than only escalated failures; this avoids the deployed-router selection bias of observing the teacher only on hard tasks.
- Freeze the overlap and missingness rules before outcomes. Retain failed extraction attempts.
- Train vocabulary, scaling and outcome models on training only; calibrate on calibration only. Test is used once for the frozen analysis.
- Report temporal drift and platform/difficulty strata, but do not tune separate policies on the test strata. Treat small strata as descriptive and avoid demographic-fairness claims from programming-platform categories.
- Record upstream prompt/generation/evaluation differences. Paired task identity does not establish identical inference stacks, model release dates, token budgets or contamination exposure.
- Benchmark tests are imperfect correctness criteria. Published outcomes do not establish security, maintainability, task acceptance by users or reliable multi-step agent behavior.
- Negative results, failed fits and unsupported arms remain in the report. No synthetic labels or simulated model generations may be presented as empirical Qwen/DeepSeek outputs.

## 10. Planned training experiments and GPU gate

If suitable GPU access and model/artifact permissions become available, use existing Transformers/PEFT/TRL or equivalent tooling. Before any training, freeze a training extension with exact checkpoint revisions, hardware, precision, token budgets, optimizer, stopping rule and three seeds. Keep router test tasks and all their near-duplicates out of every training stage. Do not train on the held-out submissions used to report model improvement.

**Sequence-distillation arm:** train a Qwen 1.5B-class student on nonempty, verified DeepSeek outputs from training tasks only, using SFT/LoRA. This requires observable teacher sequences, not teacher logits. Compare to the unchanged student and a token-matched control trained on verified same-family Qwen outputs, separating data quality/model source from extra training. Verification-filtered data is appropriate here but must be reported with acceptance/exclusion counts. Reevaluate the entire student—including export/quantization—on untouched tasks.

**Token-level distillation arm:** if a compatible same-family Qwen 7B teacher and 1.5B student expose aligned token vocabularies, evaluate a temperature-scaled teacher/student KL objective plus supervised loss. Verify actual tokenizer/vocabulary/chat-template alignment first. DeepSeek/Qwen tokenizers cannot be assumed aligned, so naive tokenwise KL between them is not a valid substitute for sequence distillation. Teacher logits are not mandatory for the sequence-distillation arm.

**Preference/RLAIF arm:** construct teacher-ranked or verifier-ranked pairs using training tasks, then compare SFT with SFT+DPO under matched example/token budgets. AI preference labels and executable verification labels are distinct sources; record each. Keep reward definitions and independent test suites out of trainee control. Online RL/GRPO is a later arm only when adequate generation/verification compute exists. It cannot be claimed completed merely because TRL imports or a configuration file exists.

For each completed arm, record training/evaluation wall time, GPU memory, token counts, teacher-generation cost if known, checkpoint hashes, three-seed variability, held-out pass@1, regression strata and fixed-router versus recalibrated-router results. Recalibration uses a new calibration split, never the final test. Compare improvement per training cost and estimated break-even use, with assumptions stated. If hardware/access is unavailable, report the blocker and mark all training outcomes unrun.

## 11. Reproducibility and completion criteria

Persist source/protocol/split hashes, dependency lock or exact package versions, code revision, command lines, seed, machine resources, data validation output, per-task predictions/decisions, machine-readable aggregate metrics, plots, execution logs and an interpretation that includes limitations. Keep raw upstream data unchanged; derived files must identify their input hashes. Tests should catch mislabeled pass@10, leaked feedback features, overlapping groups, wrong joins, nondeterministic ties and bootstrap pairing errors.

The routing study is complete when the frozen data/analysis pipeline runs from a documented command, its required checks pass, every policy is reported, and the measured results plus limitations are written. Planned GPU experiments and inaccessible Jira/Confluence publication remain separately tracked; no fabricated ticket IDs, publication URLs, model runs or empirical results are permitted.
