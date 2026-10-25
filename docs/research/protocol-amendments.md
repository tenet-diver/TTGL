# Protocol amendments and implementation clarifications

## Amendment 1 — before any aggregate outcome analysis

**Date:** 2026-10-25. **Reason:** reconcile the frozen prose with the metadata-only data-preparation contract and fully specify implementation defaults before the first experiment run. This amendment was prepared during code review without inspecting model correctness summaries or router results. Preserve the original protocol unchanged.

Original protocol: `docs/research/protocol.md`, SHA-256 `aa58ce4cb81d0d8a1a1a8ca9b0016877503b88ddf2c3ffce8dbec31481efc8de`, frozen at `2026-10-25T22:04:57Z`.

### A1.1 — prompt definition

Replace the original section 5 statement that title, statement and starter code are concatenated with the implementation contract: **the router prompt is exactly upstream `question_content`**, copied to canonical `prompt`. The question title and starter code remain part of cross-model metadata-equality validation but are not router features. No test outcome motivated this choice. This narrower definition is directly reproducible and avoids inventing a prompt template that was not part of the source-data preparation agreement.

Both TF-IDF and `log1p` character length use this same content-only prompt. IDs, dates, platform, official difficulty, generations, sanitized code, grades, upstream pass fields and evaluation feedback remain excluded from predictors. Platform and difficulty may be used only for descriptive subgroup reporting.

### A1.2 — fixed software defaults

The TF-IDF configuration additionally sets `sublinear_tf=True`; all other unspecified tokenizer/normalization defaults come from the recorded scikit-learn version. The logistic regressions for both outcome prediction and Platt calibration use L2 regularization, `C=1`, `solver="liblinear"`, `max_iter=2000`, and seed `1729`. Probability inputs to calibration are clipped to `[1e-6, 1-1e-6]` before conversion to logits. These settings are fixed before aggregate outcomes and are not tuned on the holdout.

The primary ten-bin ECE uses equal-width probability bins over `[0,1]`, assigning the endpoint 1 to the last bin, with each nonempty bin weighted by its task fraction. A five-quantile-bin reliability plot is an additional visualization; it does not replace the protocol's ten-bin ECE. Both must identify their binning explicitly. The sample-level Brier estimate `mean(p² − 2p*y + y)` averages binary squared error across the ten upstream samples; `y` is each task's sample-mean grade. This includes within-task Bernoulli variation and is distinguishable from `mean((p-y)²)`.

### A1.3 — unchanged choices and review checks

The primary hypothesis, model pair, task eligibility, grouped chronological split, exact 50% batch budget, expected-random comparator, soft-label fitting, 2,000 paired contest-bootstrap replicates, seed, and planned training arms are unchanged. Normalized local-cost ratios remain `{0, 0.01, 0.05, 0.10, 0.25}` as specified in the frozen protocol.

Before fitting, verify each processed split file against its recorded hash inside the frozen split manifest, as well as checking the manifest's own hash. Record this amendment's hash alongside the original protocol and split hashes in the freeze/run metadata. Report any actual later implementation deviation separately with its timing relative to outcome inspection.

Descriptive platform/difficulty results should include task/group counts and local/remote/routed means. These are audit strata, not separately optimized policies or claims about demographic fairness. Record any solver convergence warning; a successful process exit alone does not establish a valid fitted model.
