# Metered isolated SWE-bench results

The study completed 72 assignments on 12 tasks across 6 conditions. Outcomes come from the official pinned SWE-bench evaluator and are joined to exact exported patches.

| Condition | Resolved | Input tokens | Output tokens | Expert requests | Published-rate scenario USD |
|---|---:|---:|---:|---:|---:|
| small | 9/12 | 2491650 | 23561 | 0 | 0.0701 |
| large | 10/12 | 3654412 | 29201 | 0 | 1.3863 |
| precall_router | 11/12 | 3698347 | 30517 | 0 | 0.9553 |
| oneway | 9/12 | 3030415 | 26554 | 1 | 0.1102 |
| reset_expert | 8/12 | 2932924 | 23312 | 1 | 0.1047 |
| personal | 9/12 | 2419963 | 19863 | 0 | 0.0627 |

## Paired quality differences versus the large solo condition

| Condition | Difference in percentage points | Conditional paired bootstrap 95% interval |
|---|---:|---:|
| small | -8.3 | -25.0 to 0.0 |
| precall_router | 8.3 | 0.0 to 25.0 |
| oneway | -8.3 | -25.0 to 0.0 |
| reset_expert | -16.7 | -41.7 to 0.0 |
| personal | -8.3 | -25.0 to 0.0 |

Official evaluator invocations with retained execution records: 67. Exact-program report reuses: 5. Reuse is not an additional test execution.

## Published-rate cost scenario

Rates were verified and frozen before scored inference from the [official Enterprise Codex Standard-mode rate card](https://help.openai.com/en/articles/20001415-chatgpt-rate-card-enterprise-token-based-pricing). They price native uncached input, cached input and output separately. This is a counterfactual token-rate scenario, not this account invoice, API bill or observed quota use. The signed-in Codex long-context exemption follows that rate card. See published-rate-scenario.json for paired cost-ratio uncertainty and published-rate-records.json for every assigned observation.

| Condition | Estimated scenario saving versus large |
|---|---:|
| small | 94.9% |
| precall_router | 31.1% |
| oneway | 92.1% |
| reset_expert | 92.4% |
| personal | 95.5% |

## Interpretation and accounting

This is a small engineering panel of public historical tasks. It cannot establish a three-point noninferiority margin. The task bootstrap is conditional on this panel and may be degenerate; repositories and bug families can be correlated. No architectural novelty or open-weight/local-model result is claimed.

Native input/output token totals are measured. Cached input is included within input, and reasoning is included within output. Input and output tokens have different economic weights; the table does not turn raw token reduction into dollar or quota savings. Router and expert turns are included in their assigned condition. Failed attempts remain in assigned-task accounting.

Backend credit estimates are retained in provider-usage.json, including unavailable values. API-equivalent dollars remain null: API cache-write and request-level context pricing need a separately compatible meter. Provider estimates are not subscription invoices. Setup, independent controls, grading, hardware and subscription allocation require separate accounting. The registered joint cost/quality target is not established by these small-panel model-only measurements.

Environment exclusions determined before scored inference: none.

See analysis/records.json and analysis/summary.json for all assigned records, provenance, paired uncertainty and cost availability. grades-portable.json resolves archived reports relative to this directory so the analysis can be reproduced after relocating the checkout. The frozen design, environment, per-role journals, patches and original official grading logs are in the parent study directory.
