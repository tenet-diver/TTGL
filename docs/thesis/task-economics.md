# Task-level prices and portfolio economics

## The unit of purchase is a completed attempt

A token tariff is an input to a cost model, not the price of repairing a repository or completing a browser workflow. One task can consume many prompts, tool results, screenshots, retries and model transitions. Two models offered at the same token rate can therefore have very different task costs. The study reports **US dollars per assigned task** and **US dollars per successfully completed task**, alongside the success rate and latency distribution. Task-specific costs are stratified by domain and difficulty proxies established before outcomes are observed.

For a collection of assigned tasks with total recorded costs $C_i$ and success indicators $Y_i$, the two basic quantities are

$$
\overline C=\frac{\sum_i C_i}{n},\qquad
C_{\mathrm{success}}=\frac{\sum_i C_i}{\sum_iY_i}.
$$

All assigned attempts contribute to the numerator, including failed runs. The second ratio is undefined when no task succeeds. It is an aggregate acquisition cost per observed success, not the cost of repeatedly attempting any particular issue until it succeeds. That interpretation would require assumptions about repeated attempts, dependence and stopping that this calculation does not make. For repeated-seed evaluations, costs and successes use the same registered aggregation.

Three evidence classes are kept separate: historical benchmark-reported costs, illustrative arithmetic using stated token volumes, and future TTGL costs reconciled to usage and billing records. Only the third can establish the deployed system's actual economics. The first two are useful for planning without inventing unobserved task outcomes.

## Attributable historical cost per software-engineering task

The official SWE-bench website exposes an `instance_cost` field and labels it “Average cost per task instance in the benchmark.” Its pinned leaderboard also supplies individual costs and resolution outcomes. For the six historical records below, summing all **500 per-instance costs** reproduces the reported total; dividing by 500 reproduces `instance_cost`. Resolution counts were checked against the same records. The table uses those reported costs and derives cost per resolved issue without changing historical prices.[^econ-site]

All six submissions are dated **17 February 2026**, use **mini-SWE-agent 2.0.0** on **SWE-bench Verified**, and specify one attempt per issue. Monetary columns are rounded to four decimals; the accompanying CSV preserves the source precision and calculation.

| Historical model | Resolution | Reported $ / assigned task | Derived $ / resolved task |
| -------------------------------- | ------------: | -------------------------: | -------------------------: |
| MiniMax M2.5, high effort | 75.8% | $0.0733 | $0.0967 |
| Kimi K2.5, high effort | 70.8% | $0.1466 | $0.2070 |
| GPT-5.2, high effort | 72.8% | $0.4736 | $0.6505 |
| GLM-5, high effort | 72.8% | $0.5344 | $0.7341 |
| Claude Opus 4.6, effort unspecified | 75.6% | $0.5515 | $0.7295 |
| Claude Sonnet 4.5, high effort | 71.4% | $0.6579 | $0.9214 |

These figures are **benchmark-reported cost, not verified invoices or current service quotations**. The inspected records do not establish that repository containers, idle infrastructure, development, tax, storage or human effort are included. They must not be presented as full production cost. The entries also have `checked: null`, and shared harness/version metadata does not prove identical context, sampling, serving or tool budgets. No statistical ranking or current-model superiority claim follows from the table.

The useful observation is methodological: an existing benchmark can attach dollars to complete task attempts rather than only publishing per-token prices. That is the granularity required for this thesis. The manuscript's historical accuracy chapter explains the remaining comparability limits. These figures cannot be relabeled as the task prices of a successor checkpoint or combined with a current model's vendor accuracy score. [The historical cost CSV](task-price-comparisons.csv) links every row to its original submission identifier.

## Illustrative prices for current catalog candidates

Actual task traces for the current candidates do not yet exist. The following table therefore computes **text-token charges for two assumed episodes**, using the dated secondary rates in the model catalog. It is a sensitivity calculation, not a benchmark or a prediction of how many tokens a model will need. Counts are totals over all calls in an episode, not the size of one prompt:

- **Scenario A:** 20,000 uncached input tokens, no cache-read tokens and 4,000 output tokens.
- **Scenario B:** 100,000 uncached input tokens, 400,000 cache-read tokens and 20,000 output tokens.

Each provider's own tokenizer determines its bill. Equal token counts here provide a controlled arithmetic comparison; they do not imply equal text, reasoning, success or latency. Actual cache eligibility and the partition into billing categories must be measured. Scenario B assumes eligible already-cached reads and adds no separately billed cache creation. If that assumption does not match the provider, the scenario must be revised rather than treating cache creation as free. The table excludes images, browser execution, cache-write premiums, provider tools and other charges.

| Candidate / priced service | Scenario A | Scenario B |
| ---------------------------------------------------------- | ------------------: | ------------------: |
| Qwen3.8-27B / Nebius Token Factory | $0.0210 | Unknown |
| DeepSeek-V4.1-Flash alias / Tencent Cloud | $0.0108 | $0.0564 |
| GLM-5.3-Flash / Z.ai | $0.0050 | $0.0370 |
| Kimi K3 / Moonshot | $0.1200 | $0.7200 |
| GPT-6.1 Sol / OpenAI | $0.0800 | $0.4400 |
| GPT-6 Luna / OpenAI | $0.0040 | $0.0240 |
| Claude Sonnet 5.5 / Anthropic | $0.0800 | $0.4400 |
| Claude Opus 5.5 / Anthropic | $0.1600 | $0.8800 |

Prices retain the model catalog's **secondary-source, unverified direct-provider rate** status. The Tencent alias is not verified as the exact `1017` checkpoint. Qwen's Scenario B is unknown because the inspected catalog provides no cache-read rate; missing price is not zero. Local Qwen models are omitted from this API table because they require hardware accounting, not because their task cost is assumed zero. The arithmetic is reproduced in [the scenario CSV](task-price-scenarios.csv). No cost-per-success column is supplied because contemporary task success is unmeasured.[^econ-rates]

For browser tasks, image charges may depend on image size, tiling, rescaling or model-specific token conversion. Repeated screenshots and accessibility-tree observations can dominate context volume. The browser study consequently records billed image/text categories and environment time separately. A text-only scenario is not advertised as the price of a visual browsing task.

## Local and hosted infrastructure costs

The economic boundary must match the deployment. A provider-hosted model incurs its charged API categories. A self-hosted model incurs provisioned compute, including model loading, idle capacity and shutdown delay. The same inference must not be charged twice by adding a hypothetical GPU allocation on top of a hosted API tariff that already pays for that inference. Separate browser or repository workers still have their own costs.

For a dedicated device or rental, a planning approximation is

$$
C_{\mathrm{compute/task}}\approx
\frac{r_{\mathrm{hour}}\,t_{\mathrm{active}}}{3600u},
$$

where $t_{\mathrm{active}}$ is seconds of task-attributed busy time and $u$ is the assumed utilization of provisioned capacity. This is appropriate only when allocation and concurrency are defined consistently. It cannot substitute for measuring batched or overlapping workloads. As an **arithmetic example**, a hypothetical $2/hour service with 90 seconds of attributed busy time costs $0.05 per task at full utilization and $0.20 at 25% utilization. Neither the hourly price nor the runtime is a Runpod quote or measured model performance.

Measured reporting reconciles assigned task shares, idle capacity and setup costs with the total resource bill. A portfolio that keeps several large checkpoints resident may lose its apparent advantage through idle memory, replicas or queueing. Shared multi-adapter serving may reduce this overhead but still requires an explicit tenant and task allocation rule. Local-device reporting includes a marginal-cash view and an ownership/energy view; user hardware is not economically free simply because the application does not charge an API fee.

## Adaptation, switching and the price-sensitivity policy

Portfolio inference is only part of lifecycle cost. Customer adaptation adds teacher-data generation, verification, training, adapter storage and validation. If the relevant total is $F$ and a declared customer workload contains $M$ future tasks, its amortized contribution is $F/M$. Both $F$ and $M$ are reported; the manuscript does not select a large hypothetical workload merely to make training appear cheap. With several student bases, each base's adapter and compatibility evaluation contribute to the customer's fixed cost. A shared data pipeline does not make all adapter training free.

A switch can add input reprocessing, weight or adapter loading, summaries and extra validation. Its cost belongs to the receiving task even when the switch fails. Cached-context savings require an actual eligible cache hit. A change in model or adapter may alter both output quality and cache validity, so a policy should compare the expected benefit of switching with the complete transition cost. Keeping a model for an episode or a coherent phase is a candidate policy, not an untested guarantee of lower total cost.

Price sensitivity is expressed through a task budget or a prespecified cost weight in the routing objective. For each eligible action, the router predicts success and **remaining total task cost**, rather than ranking model token tariffs. Its features can include domain, permitted repository/browser state, current model residency, remaining budget and customer policy. Frontend, backend and language labels are useful only if their predicted differences generalize to held-out tasks. A small remote specialist may be preferable to a larger local model; deployment location, capability, parameter size and price are distinct variables.

The evaluation reports paired success differences, mean task cost, cost per success, latency and upper cost quantiles at each registered operating point. Mean cost alone can conceal a minority of tasks that exhaust their budgets. Customer-facing estimates should therefore distinguish a quoted cap from an expected spend and the platform's internal cost from its selling price. An application may offer a free local tier, but that business decision does not change the study's hardware accounting. Actual closed-provider usage still requires its own authorized budget.

## Reproduction and evidence boundary

`python scripts/build_task_price_table.py` regenerates both CSVs from the recorded source register and model catalog. Adding `--verify-upstream` downloads the revision-pinned public leaderboard, checks its SHA-256 and rechecks all 3,000 selected per-instance cost/outcome records. This is a source-consistency check and performs no model inference. [The check record](task-price-checks.json) and [economic source register](task-economics-sources.json) identify the inputs and source code establishing the displayed cost semantics. Future empirical tables must replace assumptions with traces, reconciled charges and the declared failure accounting.

[^econ-site]: SWE-bench website at revision `193160a463a435d05cf44a1fa9dc5eac832113c3`: [leaderboard JSON](https://github.com/SWE-bench/swe-bench.github.io/blob/193160a463a435d05cf44a1fa9dc5eac832113c3/data/leaderboards.json), [table rendering and average-cost label](https://github.com/SWE-bench/swe-bench.github.io/blob/193160a463a435d05cf44a1fa9dc5eac832113c3/js/mainResults.js), and [per-instance cost chart](https://github.com/SWE-bench/swe-bench.github.io/blob/193160a463a435d05cf44a1fa9dc5eac832113c3/js/charts/cumulativeCostChart.js). Retrieved 25 October 2026. The selected submissions and hash are retained in `accuracy-context-sources.json`.

[^econ-rates]: Secondary LiteLLM [price catalog](https://github.com/BerriAI/litellm/blob/dddbaa803d6e9fcc862ea7a5412f771cb1ae040e/model_prices_and_context_window.json), revision `dddbaa803d6e9fcc862ea7a5412f771cb1ae040e`, as recorded in `model-catalog.csv` and `market-sources.json`, reviewed 25 October 2026. The model-landscape chapter explains service identities, aliases, price units and unsuccessful direct-provider price verification.
