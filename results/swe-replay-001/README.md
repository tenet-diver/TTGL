# SWE-bench Verified: 500-task public replay

This experiment **was executed**: success and cost predictors for ten models were fitted in five held-out task folds and routed the published outcomes of 500 SWE-bench Verified tasks (5,000 upstream model attempts). It did **not** execute 5,000 new model attempts. The separate live Codex experiment remains a different artifact.

The fixed primary cost/benefit router saved **46.1% of source-estimated inference cost**, but resolved **64.2%**, versus **72.8%** for GPT-5.2 (high): an **8.6 percentage-point loss**. It fails the proposed 3-point noninferiority criterion. This is evidence of a cost-quality tradeoff, not evidence that the proposed conversational system preserves quality.

| Policy | Resolved | Estimated inference/task | Saving vs GPT-5.2 |
|---|---:|---:|---:|
| `always_gpt_5_mini` | 56.2% | $0.0472 | 90.0% |
| `always_gpt_5_2_high` | 72.8% | $0.4736 | 0.0% |
| `random_expected_large_0.5` | 64.5% | $0.2604 | 45.0% |
| `cost_benefit_router_large_0.5` | 64.2% | $0.2551 | 46.1% |
| `always_minimax_2_5_high` | 75.8% | $0.0733 | 84.5% |
| `portfolio_lambda_0.25` | 76.2% | $0.1154 | 75.6% |
| `NONDEPLOYABLE_pair_outcome_cost_oracle` | 76.6% | $0.1538 | 67.5% |
| `NONDEPLOYABLE_portfolio_outcome_cost_oracle` | 87.8% | $0.0936 | 80.2% |

All dollars are **historical source-reported estimated API inference costs**. They exclude router compute, repository environments, grading, energy and subscription allocation; they are not invoices or current quotes. New paid model-inference spend for this analysis was $0. Full operational cost and Codex subscription savings remain unknown. Added-cost sensitivities are recorded for $0, $0.001, $0.01 and $0.05 per task, without pretending these hypothetical overheads were measured.

## What the comparisons actually show

The primary router does not improve on expected random half allocation: its resolution difference is -0.3 points (task-bootstrap 95% CI -2.40 to 1.90), with 2.0% lower estimated cost.

The ten-model portfolio has attractive outcomes relative to GPT-5.2, but **MiniMax 2.5 alone is the essential control**: 75.8% at $0.0733/task. The portfolio at utility weight 0.25 resolves 76.2% at $0.1154/task, 0.4 points more, but costs 1.57 times MiniMax alone. Its paired quality CI against MiniMax is -0.80 to 1.60 points. Thus this replay does not establish that routing adds value over the strongest cheap single model. That comparator was selected for discussion after inspecting the planned single-model table; the extra comparison is explicitly labelled post-analysis.

The full declared utility grid is retained. No chosen grid point is presented as a confirmatory win. Open-weight portfolio variants use the upstream `os_model` metadata classification, which is not an independent license audit or a claim that these models run on a consumer laptop. GPT-5-mini is a smaller **product tier**, with no parameter-count claim.

Small/large complementarity exists: 262 tasks solved by both, 19 only by GPT-5-mini, 102 only by GPT-5.2, and 117 by neither. The pair oracle reaches 76.6%, and the ten-model oracle 87.8%. These oracles inspect the **actual test outcomes and actual task costs**, select the cheapest successful model, and are impossible deployment baselines. They bound the value of perfect selection, not the expected benefit of conversation.

## Method and uncertainty

The protocol was fixed before model fitting, after public aggregate accuracies/costs had been inspected. It is an exploratory secondary analysis, not prospective preregistration. The primary pair and 50% large-model quota were fixed before fitting. Feature extraction uses only issue text, its length and repository name. Logistic regression predicts success; ridge regression predicts log-transformed cost. Each prediction uses four folds and each quota is ranked **within its own held-out fold**, so held-out labels/costs do not influence that fold's choices through global ranking. No gold patch, test patch, trajectory or API-call count enters routing.

The same mini-SWE-agent 2.0.0 harness version and 2026-02-17 submission family were used. Model effort and API parameters may differ; source metadata for GPT-5.2 says high, while GPT-5-mini does not declare high effort. The study compares the published configurations, not matched weights or all current October-2026 frontier products. Source cost/accuracy aggregates reconcile exactly (within numerical tolerance) with the 500 per-instance records for every model. No missing grade or cost is replaced by zero.

We report 2,000 paired task-bootstrap draws and paired repository-cluster sensitivity over 12 repositories, conditional on the fixed fitted policies and published single attempts. The primary resolution difference CI is −11.605 to −5.600 points, and the cost-ratio CI is 0.4860–0.5917; the cluster sensitivity leads to the same failed quality conclusion. These are not intervals for fresh-run stochasticity or router retraining. Folds share repositories, the benchmark is public/historical, and contamination remains possible. Neither unseen-repository transfer nor conversation is measured. Router issue text comes from the pinned official task distribution joined by instance ID; byte identity with each upstream model's original prompt was not independently established.

## Reproduce and inspect

```bash
bash scripts/setup_research.sh
/workspace/.tools/ttgl-research/bin/python scripts/swe_public_replay.py fetch
/workspace/.tools/ttgl-research/bin/python scripts/swe_public_replay.py analyze --output /tmp/ttgl-swe-replay-reproduction
/workspace/.tools/ttgl-research/bin/python scripts/swe_replay_report.py --results /tmp/ttgl-swe-replay-reproduction
```

Use the Python environment path created by setup if your checkout is not under `/workspace`. `analyze` refuses an existing output directory. It validates every source SHA-256 and the frozen protocol before fitting. Raw problem statements/submissions are an ignored local cache because the two distribution repositories did not expose a top-level license at the inspected commit. Numerical results, source URLs/hashes, and retrieval code are retained; review upstream terms before redistributing raw text.

- `summary.json`: every policy, confidence interval, sensitivity and interpretive limit.
- `task-records.jsonl`: all 500 task-level public outcomes/costs, held-out predictions and choices.
- `additional-comparisons.json`: primary versus random; all portfolio grid points versus MiniMax, transparently added after initial analysis.
- `folds.json`: exact training/test allocations.
- `policy-table.csv`: compact table for all declared policies.
- `sources.json`: 522 pinned sources with hashes, including all 500 official problem statements.
- `cost-quality.png` / `.svg`: standard exported cost-quality plot.
- `run-manifest.json`: frozen protocol, code and result hashes for the original analysis.
- `software-versions.json`: statistical package versions.

Primary source: [SWE-bench/experiments at 40f164d](https://github.com/SWE-bench/experiments/tree/40f164d5b8f1d249bf95a6df8b74b577fd8e519d/evaluation/verified). Issue text: [official swe-bench-tasks at 3d07b46](https://github.com/SWE-bench/swe-bench-tasks/tree/3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d).

## Explicit upstream zero-cost records

Gemini 3 Flash has two literal source cost values of $0: `django__django-15731` and `django__django-15814`. Both report one API call and an unresolved task. These are retained published values, not imputed missingness, but their billing completeness is unverified. They must not be interpreted as free inference. They affect the standalone Gemini row and some low-penalty portfolio points; the primary pair, portfolio weight 0.25, and both reported oracles select different models for these rows. `additional-comparisons.json` lists every affected policy. No zero-cost claim is used to infer a subscriber's plan usage.

Pinned repository-root license inspection is recorded in `license-checks.json`; it found no explicit top-level license in either distribution repository. Model open-weight labels come from submission metadata and are not a license audit.
