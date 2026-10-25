# Analysis and reporting plan

## Estimands and success criteria

The principal system estimand is the difference in issue-resolution probability between the dual-model condition and the declared remote-only baseline on the target task population. Its primary economic estimand is the ratio of mean total cost per assigned issue, dual divided by remote-only, under a specified deployment/accounting scenario. The paired mean cost difference is a supporting estimand. A claim of useful savings requires both acceptable quality and lower cost. A system that is cheaper because it abandons difficult issues must not be described as equivalently capable.

The primary analysis follows the gatekeeping procedure specified in the methodology: first assess the declared noninferiority condition for resolution, then assess cost superiority if that gate is passed. The router-specific comparison with a baseline matched on estimated cost using calibration data addresses a different question—whether allocation is useful—and is a prespecified exploratory contrast. Actual realized cost is reported because calibration does not guarantee an exact spending match on test tasks. An exploratory configuration that happens to look best is not substituted for the primary system after inspecting the final test.

Let $Y_{ir}^a\in\{0,1\}$ indicate resolution for task $i$, replicate $r$, under condition $a$, and let $C_{ir}^a$ be its total recorded cost. For the three-repeat confirmatory design, define task means $\overline Y_i^a=\frac{1}{3}\sum_{r=1}^3Y_{ir}^a$ and $\overline C_i^a=\frac{1}{3}\sum_{r=1}^3C_{ir}^a$. The paired task differences are $D_i^Y=\overline Y_i^{\mathrm{dual}}-\overline Y_i^{\mathrm{remote}}$ and $D_i^C=\overline C_i^{\mathrm{dual}}-\overline C_i^{\mathrm{remote}}$. The primary cost ratio divides the across-task mean of $\overline C_i^{\mathrm{dual}}$ by the corresponding remote-only mean; it does not average per-task ratios. Assignment to all eligible tasks is the analysis denominator. Infrastructure failures, timeouts and budget exhaustion are handled by the declared failure policy, with a sensitivity analysis that preserves the initial analysis rather than selectively deleting inconvenient cases.

Repeated seeds estimate stochastic variability within a task/condition. They are not independent repositories or independent task draws. The report states whether a metric estimates a single attempt, the expected success of one sampled trajectory, or the success of a budgeted multi-attempt system. Reporting pass@k as if it were single-attempt resolution would obscure both sampling effort and cost.

## Accuracy and cost frontiers

For every prespecified policy configuration, the report plots mean issue resolution against mean total cost. Markers identify model pair, routing policy, intervention point and deployment scenario. Uncertainty is attached to both coordinates or to pairwise contrasts as appropriate. Policies are considered dominated when another evaluated configuration is no less accurate and no more expensive under the same accounting assumptions, with uncertainty acknowledged. An empirical Pareto frontier is descriptive and does not establish optimality among untested policies.

Two views are required. A **fixed-quality view** asks how much cost can be reduced while remaining within the quality constraint. A **fixed-cost view** asks how much resolution improves at the same available spending. Remote-call fraction is also reported, but is not the horizontal axis for all economic conclusions: different requests can have different input/output lengths, cache behavior and reasoning budgets. A policy that sends fewer calls remotely can still cost more.

API and self-hosting scenarios are analyzed separately. The same open-weight model can be evaluated as a provider-hosted endpoint and as a self-hosted service, but the change in serving stack can alter latency, quantization and outputs. Prices from a dated catalog are not substituted for invoices when an actual call is made. Catalog-based extrapolations are labelled estimates, and intervals from task resampling do not imply certainty about future provider prices.

## Router quality as a prediction problem

A routing model should be assessed independently of the end-to-end system it controls. The study therefore reports predictive discrimination, calibration and decision quality.

Discrimination measures whether higher predicted success corresponds to higher observed success. AUROC and, where class imbalance makes it useful, precision–recall summaries can describe local and remote outcome predictors. A high score does not guarantee good allocation because the router needs to identify differences between models, not merely easy tasks. Benefit ranking is assessed through matched-budget resolution, opportunity regret and gains over a random policy.

The Brier score for a binary outcome is

$$
\mathrm{BS}=\frac{1}{n}\sum_i(\widehat p_i-Y_i)^2.
$$

When multiple samples estimate a task's success probability, the report specifies whether it scores individual Bernoulli outcomes or task means; these are different quantities. Reliability plots show bin counts and uncertainty. Expected calibration error is reported with the binning rule fixed in advance, since changes in bins can materially alter it. Proper scoring rules are primary calibration summaries; an attractive reliability plot alone is insufficient.

For an action $a_i$, a simple observed utility is $U_i(a_i)=Y_i(a_i)-\lambda C_i(a_i)$. An outcome-informed oracle can define an upper bound by choosing the best observed action for each task. Regret to that oracle exposes headroom, but the bound is optimistic when it selects among noisy outcomes. It is diagnostic only, never an achievable deployed baseline or a way to choose test thresholds.

Selective-risk curves report error among tasks retained locally as a function of local coverage. Coverage must count actual local-only completion; a task using a remote planner or judge cannot be silently classified as local-only. The report also shows unresolved tasks, abstentions and remote escalations rather than counting only accepted local outputs.

## Statistical uncertainty and dependence

Paired analysis uses the same tasks across conditions, reducing variation attributable to the task mix. Bootstrap or model-based uncertainty must respect the dependence structure specified by the dataset: trajectories within tasks, tasks within repositories, and potentially related issues or patches. The primary uncertainty scheme is fixed before observing test outcomes and is accompanied by the number of independent repositories/clusters.

If the available benchmark contains few repositories, a large number of tasks does not create equally many independent repository samples. Results can characterize the benchmark more precisely than they characterize arbitrary unseen repositories. Repository-level resampling, leave-one-repository-out sensitivity and the prespecified unseen-repository subset help reveal this distinction, but none makes a small set representative of all software development.

For ratios such as cost per resolved issue, uncertainty is computed from the paired numerator and denominator within each resample, not by independently combining marginal intervals. A denominator of zero produces an undefined value, which remains visible. Cost distributions are often skewed; the report includes median, upper quantiles and extreme-run attribution in addition to means.

Subgroups, multiple budgets and model pairs create multiplicity. The methodology identifies the confirmatory contrasts and correction/gatekeeping rule. Other comparisons are explicitly exploratory. The thesis will report negative and inconclusive outcomes and will avoid treating a failure to reject a null as proof of equivalence.

## Power and the role of the feasibility pilot

A limited pilot serves to validate tooling, task duration, hardware memory, logging and price estimates. It is not described as a well-powered test of a small accuracy difference. The number of pilot tasks and stopping rule are frozen before outcomes are seen; a pilot task used for tuning is ineligible for a later untouched test.

A simple planning approximation illustrates the scale required for paired binary comparisons. If $q$ is the probability that two conditions disagree and the desired detectable difference is $\delta$, an independence approximation gives

$$
n\approx\frac{(z_{1-\alpha/2}+z_{1-\beta})^2q}{\delta^2}
$$

for a two-sided difference test near the null. For example, **assuming** $q=0.25$, two-sided $\alpha=0.05$, power $0.80$ and a five-percentage-point difference yields approximately 785 task pairs before accounting for clustering. This is a planning scenario, not an observed discordance rate or a claim that this sample size is sufficient for noninferiority, all policies or all repositories. The final calculation must use the declared test and a conservative dependence assumption.

The approved US$100 GPU allocation is treated as a feasibility resource. A full benchmark across several current models, multiple seeds and closed-provider APIs requires a separately costed acquisition plan. If the funded scope remains a pilot, the final thesis must describe its conclusions as preliminary and narrow its claims accordingly rather than asserting the confirmatory design was executed.

## Prespecified outputs

The completed study will produce five groups of tables and figures:

1. **Cohort and execution accounting:** task/repository counts, exclusions, environment failures, seeds, model/harness revisions and actual resource use.
2. **System outcomes:** resolution, regressions, costs and latency by condition; primary paired contrasts with uncertainty.
3. **Routing diagnostics:** coverage, remote exposure, calibration, regret and prespecified subgroups.
4. **Economic scenarios:** API invoice accounting, self-hosted utilization sensitivity, local marginal versus total cost, and adaptation amortization assumptions.
5. **Student intervention:** base versus adapted model, fixed versus recalibrated router, training cost, export/quantization checks and forgetting diagnostics.

Empty result-table templates are provided in the appendix. No cells are populated from hypothetical values. Published external scores belong in the background model catalog and retain their original attribution; they do not populate the study's result tables.

## Result-dependent discussion to be written later

The final discussion will answer the research questions in the order established here. If quality is retained with lower cost, it will examine the range of workloads and accounting assumptions supporting that result. If cost decreases alongside unacceptable quality loss, it will explain the tradeoff without presenting it as a successful substitute for the remote model. If differences are unresolved, it will discuss precision and sample size rather than asserting equivalence.

Possible explanations—miscalibration, inadequate features, task shift, weak local tool use, state-transfer overhead, teacher-data bias or serving incompatibility—will require diagnostic evidence. The discussion will distinguish observed mechanisms from plausible hypotheses. It will also assess whether any improvement transfers to unseen repositories, current model revisions and real local hardware. None of those conclusions is written in advance.
