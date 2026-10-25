# Analysis and reporting plan

## Study hierarchy, estimands and success criteria

The program separates three experiments. **Study 0** evaluates flat portfolio selection as an enabling baseline. **Study 1** tests the fixed-model personal controller with expert assistance against the same strong model acting directly with the same personal information. **Study 2** evaluates repeated learning from use. Each answers a different causal question. Portfolio allocation, cooperative control and student adaptation cannot be substituted for one another when interpreting success.

Study 1 supplies the current primary cooperative claim. Its endpoint is accepted task success: benchmark resolution plus the prespecified feasible mandatory user constraints. All conditions receive the same initial personal-memory snapshot, retrieval results, tools, task environment and resource caps. The frozen cooperative condition C is compared with the strong-agent condition B, using the one-sided superiority test specified in the personal-controller chapter. A lower one-sided 95% confidence bound for $A_C-A_B$ above zero supports greater accepted-task success under those caps. Subjective style remains a separate outcome. An unsuccessful superiority test is not replaced after the fact with a cheaper-system or noninferiority claim.

Realized costs need not match merely because caps match. Report the ratio and difference of mean total cost per assigned task, cost per accepted success, and latency alongside the primary quality contrast. Higher success with higher spending can be a useful tradeoff but does not establish economic dominance. The full task-cost boundary includes the local controller, expert calls, tools, verification and all failed work.

Let $Y_{ik}^a\in\{0,1\}$ indicate accepted success for task $i$, replicate $k$, under condition $a$, and let $C_{ik}^a$ be total cost. The adequately funded design uses three repeats, with task means $\overline Y_i^a=\frac{1}{3}\sum_{k=1}^3Y_{ik}^a$ and $\overline C_i^a=\frac{1}{3}\sum_{k=1}^3C_{ik}^a$. The primary paired difference is $D_i^Y=\overline Y_i^C-\overline Y_i^B$; the economic contrast uses the corresponding cost means. Cost ratios divide across-task means rather than averaging per-task ratios. Assigned tasks remain in the denominator under the registered failure policy.

Study 0 retains its proposed quality-noninferiority then cost-superiority sequence within the enabling protocol. Study 2 specifies a separate final-round chain for standalone improvement, retained assisted quality and increased verified local coverage. These are prospective designs, not extra ways for Study 1 to pass. In the present hierarchy their additional comparisons are explanatory unless independently registered and funded as confirmatory studies. A joint confirmatory submission must freeze a multiplicity allocation before acquisition; it cannot promote whichever study succeeds. Every protocol's displayed 95% bounds describe its standalone scope, not simultaneous coverage across the whole program.

If a preceding study's final outcomes influence a later study's design, the later study requires a fresh held-out cohort. Alternatively, every condition, checkpoint rule and analysis can be frozen before a single sealed evaluation campaign, with no test feedback during learning. Repeated attempts characterize stochastic variability within tasks; they are not additional independent repositories. Pass@k, independent single-attempt success and best-of-many selection are different estimands with different costs.

## Accuracy and cost frontiers

For every prespecified condition, the report plots mean success against mean total cost. Official benchmark resolution and the cooperative study's accepted-task endpoint are labelled separately. Markers identify portfolio epoch and membership, routing policy, intervention point and deployment scenario. Uncertainty is attached to both coordinates or to pairwise contrasts as appropriate. Policies are considered dominated when another evaluated configuration is no less accurate and no more expensive under the same accounting assumptions, with uncertainty acknowledged. An empirical Pareto frontier is descriptive and does not establish optimality among untested policies.

Two views are required. A **fixed-quality view** asks how much cost can be reduced while remaining within the quality constraint. A **fixed-cost view** asks how much resolution improves at the same available spending. Remote-call fraction is also reported, but is not the horizontal axis for all economic conclusions: different requests can have different input/output lengths, cache behavior and reasoning budgets. A policy that sends fewer calls remotely can still cost more.

API and self-hosting scenarios are analyzed separately. The same open-weight model can be evaluated as a provider-hosted endpoint and as a self-hosted service, but the change in serving stack can alter latency, quantization and outputs. Prices from a dated catalog are not substituted for invoices when an actual call is made. Catalog-based extrapolations are labelled estimates, and intervals from task resampling do not imply certainty about future provider prices.

The primary inference concerns software engineering. Browser-task success, visual grounding and frontend acceptance are reported under their own evaluators and denominators. A global score requires workload weights fixed before outcomes; equal weighting is a chosen deployment scenario, not a discovery about the task population. Dollar-per-success ratios are computed within each domain before any declared workload aggregation.

## Router quality as a prediction problem

A routing model should be assessed independently of the end-to-end system it controls. The study therefore reports predictive discrimination, calibration and decision quality.

Discrimination measures whether higher predicted success corresponds to higher observed success. AUROC and, where class imbalance makes it useful, precision–recall summaries can describe candidate-specific outcome predictors. A high score does not guarantee good allocation because the router needs to identify differences between models, not merely easy tasks. Benefit ranking is assessed through matched-budget resolution, opportunity regret and gains over a random policy.

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

Subgroups, multiple budgets and model portfolios create multiplicity. The named study protocols and the hierarchy above identify the confirmatory contrasts and multiplicity boundary. Other comparisons are explicitly exploratory. The thesis will report negative and inconclusive outcomes and will avoid treating a failure to reject a null as proof of equivalence.

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
3. **Routing diagnostics:** per-model allocation, local/remote exposure, calibration, regret, portfolio-size effects, switching frequency and prespecified subgroups.
4. **Economic scenarios:** API invoice accounting, self-hosted utilization sensitivity, local marginal versus total cost, and adaptation amortization assumptions.
5. **Student and portfolio interventions:** base versus customer-adapted configurations, fixed versus recalibrated router, release-epoch refresh, training/admission cost, export/quantization checks and forgetting diagnostics.

Empty result-table templates are provided in the appendix. No cells are populated from hypothetical values. Published external scores belong in the background model catalog and retain their original attribution; they do not populate the study's result tables.

## Result-dependent discussion to be written later

The final discussion will answer the research questions in the order established here. If cooperation improves accepted-task success, it will examine the realized cost and latency required for that gain. If a separately specified economic comparison retains quality with lower cost, it will examine the workload and accounting assumptions supporting that result. If cost decreases alongside unacceptable quality loss, it will explain the tradeoff without presenting it as a successful substitute for the remote model. If differences are unresolved, it will discuss precision and sample size rather than asserting equivalence.

Possible explanations—miscalibration, inadequate features, task shift, weak local tool use, state-transfer overhead, teacher-data bias or serving incompatibility—will require diagnostic evidence. The discussion will distinguish observed mechanisms from plausible hypotheses. It will also assess whether any improvement transfers to unseen repositories, current model revisions and real local hardware. None of those conclusions is written in advance.

## Portfolio and switching diagnostics

The report separates the static single-model frontier, a development-selected domain lookup, the restricted two-model policy, the larger frozen portfolio and the outcome-informed oracle. Pool membership and its data-acquisition cost accompany every curve. A best observed test model is not retrospectively substituted for the development-selected primary comparator. Missing candidate outcomes cannot be filled with invented counterfactual successes.

Switching analysis compares fresh task-level selection with actual phase-level and per-call continuations. It reports cold and warm latency, replayed context tokens, adapter/model load time, switch count, invalidated cache volume where observable, and task failures caused by handoff. API discounts and hardware KV reuse are distinct measurements. A policy saving model tokens while increasing infrastructure time is evaluated under the same declared total-cost accounting.

Customer and release-epoch analyses separate generator adaptation, router recalibration and changes in pool membership. Customer data volume and task volume determine whether training costs can amortize; a cost-only break-even calculation cannot establish that quality is preserved. Later release epochs use new held-out tasks or are labelled exploratory re-evaluations, not fresh confirmations on a repeatedly tuned test set.

## Learning curves and personal capability

Learning rounds are indexed separately from stochastic replicates. Plot checkpoint performance against cumulative task arrivals, verified target tokens, teacher-acquisition expenditure and training compute; calendar time alone is not an exposure measure. The sealed final panel is scored only after all round checkpoints and analysis choices are frozen. Display every registered round, including regressions, with the final-round contrast chosen in advance. A fitted trend or apparent plateau is descriptive unless separately specified for inference.

Report standalone student success, cooperative accepted success, verified local completion coverage, external-model reliance, device feasibility and lifecycle cost as separate quantities. A changed router or easier task mix can increase local assignment without improving the student. Better collaboration can increase success while retaining expert use. Neither outcome is relabeled as the other. Analyze the memory, allocation and generator interventions using their matched controls, and keep failed collection, rejected demonstrations and training costs in the ledger.
