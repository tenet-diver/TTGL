# What would make the savings claim thesis-worthy?

The contribution can be a rigorous empirical study even if the architecture
is not new. **Small agents asking larger models for help, learned routing,
multi-round orchestration and memory have substantial prior art.** The most
defensible question is narrower: does expert-initiated clarification, challenge
and revision improve the software-engineering cost–quality frontier compared
with one-way help, a matched router and a single strong model?

The title *We have to combine — A conversation is all you need* states the
hypothesis. It must not imply the result, or that tests, tools and verification
are unnecessary. The existing reviewed paper and this research plan are a
replication and controlled extension, not a claim of first invention.

## Benchmark and evidence levels

Use a pinned **SWE-bench Verified** release and its official evaluator as the
primary public repository-repair benchmark. The 500-issue panel supports a
recognizable comparison, but it is not guaranteed to be sufficiently powered
for a narrow noninferiority claim. Preserve exact issue IDs, base commits,
prompts, harness revisions, container image digests and evaluation logs. Use a
fresh agent environment for every issue/condition/repetition. Keep reference
patches, evaluator-only tests, other conditions' patches and grades outside
that environment.

Development issues and smoke tests belong to a declared development block.
Choose evaluation tasks before observing candidate outcomes, retain all
assigned attempts, and record infrastructure exclusions explicitly. If only a
subset can be afforded, call it a subset and report its selection rule. A few
successful examples from the benchmark do not inherit the precision or ranking
of the complete leaderboard. Public historical issues may be memorized by
current models; an independently collected recent-issue replication is a
useful follow-up, not an excuse to discard the standard panel.

| Evidence | Legitimate claim | Claim it cannot support |
|---|---|---|
| Official published per-instance outcomes/cost replay | Behavior of the replayed allocation policy on those frozen recorded outputs | Live conversations, new tool trajectories, or present account credit savings |
| Live standard-benchmark subset with official grading | Observed success/resource use on that subset | Full-panel leaderboard score or narrow population noninferiority by itself |
| Complete paired live panel with audited metering | A cost–quality comparison for the frozen system and task distribution | Universal savings across accounts, future models or all projects |
| Budget-matched dialogue ablations | Evidence about reciprocal communication beyond the controls | A first-invention claim or benefit from personalization/learning unless tested |

Published-trace replay is worth doing: it gives an inexpensive, reproducible
reference for the potential of allocation before paying for new trajectories.
It remains an offline experiment. If training a routing model on those traces,
use only features available before solving, train each task's prediction on
other folds, and keep gold pass/fail, solution patches, realized token use and
post-task costs out of its inputs. Select policy thresholds on development
data or report all prespecified thresholds without promoting the best test
result to a confirmatory claim. An outcome-aware oracle is only an unattainable
upper reference. Add routing-overhead sensitivity when the replay does not
measure a live router's cost.

## Required comparisons

The Codex implementation now has six arms: small-only, large-only, a task-only
prompted router, one-way assistance, reset-expert dialogue and an acting small
agent with optional continuing expert dialogue. The original live pilot ran
small-only, large-only, task-only routing and personal conversation;
the new arms' implementation and tests are not live performance results.
The task-only prompt router is not RouteLLM or Router-R1.

The thesis's primary system comparison is conversational versus large-only.
The one-way arm permits at most two independent answer-only proposals. The
reset-expert arm permits clarification/challenge but starts a fresh expert
thread for each request. The conversational arm keeps the expert thread.
These hold the expert, allowable disclosure, wall/turn cap and consultation cap
fixed; they do not enforce equal realized token cost. A large-controller control distinguishes
the role of controller size from the mere presence of a second reasoning
stage. Include an existing learned routing baseline when its trained model,
license and supported model pair can actually be reproduced. Otherwise state
that limitation rather than relabelling a new prompt as an established method.

Do not force an expert call on easy evaluation tasks merely to obtain
interesting transcripts. Optional assistance can correctly choose zero calls.
If every controller does so, the treatment did not exercise conversation on
that panel; analyze it as such. Develop consultation behavior on separate tasks
and freeze it before the final evaluation. Required-dialogue trials are useful
mechanism tests, not substitutes for the optional policy's economics.

Use the same issue statement, base repository, initial project memory,
acceptance rules and wall-time allowance. A system with more dialogue may use
more compute even under the same wall deadline. Measure that use and include a
budget-matched control when attributing gains to communication. Report model
identity and effort precisely. Hosted Luna/Sol names do not establish small
parameter counts or local open-model feasibility.

## Outcomes and decision rule

The planned tolerance is **three absolute percentage points** of resolution
loss and the practical target is **25% lower total cost**. These are prospective
engineering choices, not values inferred from the pilot. Freeze them and the
task panel before viewing final outcomes.

For each assigned task, include controller, expert, router, tool, retry and
allocated infrastructure costs. Keep API-equivalent prices, estimated plan
credits and actual payments separate. Include failed tasks in total expense.
Report both `sum(cost)/assigned_tasks` and `sum(cost)/resolved_tasks`. A task
that exhausts its budget remains an assigned failure. A missing usage field is
unknown, not zero; cost comparisons must expose missingness rather than quietly
drop expensive or unsuccessful runs.

Let `d` be paired conversational-minus-large resolution rate, and `r` the ratio
of their mean cost per assigned task. With a registered one-sided 95% procedure:

- Quality noninferiority requires the lower confidence bound for `d` above
  `−0.03`.
- Lower cost requires the upper bound for `r` below `1`.
- A claim of **at least 25% savings** requires that upper bound below `0.75`.
  A point estimate of 25% with a wide interval is not that claim.

Use paired resampling or an appropriate paired binary model with task-level
outcomes, retaining repeated seeds within each task. Report uncertainty across
repositories and a conditional-on-the-observed-repositories sensitivity analysis;
few repository clusters make cluster inference unstable. If multiple budgets
and architectures are tested, register a primary comparison and treat others
as exploratory or correct for multiplicity. Do not switch to a more favorable
noninferiority margin after observing results.

Also record expert-use rate, clarification/revision events, evidence disclosed,
failed integrations, independently caught defects, latency and resource-limit
failures. These explain why a policy helps or fails. They are secondary to
correctness and cost. Correlation between help requests and failures does not
show that help caused failure: harder tasks tend to request help.

## How many tasks?

Size the study using development-only paired disagreement and cost variability.
For planning only, let `q` be the probability that the conversational and
large-only outcomes disagree. Under true equal quality, independent task pairs,
a normal approximation, one-sided alpha 0.05 and 80% power, a three-point
noninferiority margin needs approximately

`N = (z_0.95 + z_0.80)^2 × q / 0.03^2`.

| Assumed disagreement q | Approximate required task pairs |
|---:|---:|
| 0.05 | 344 |
| 0.10 | 687 |
| 0.20 | 1,374 |
| 0.30 | 2,061 |

This is a planning approximation, not a power result for TTGL. Repository
correlation, an actual quality deficit, multiplicity and heavy-tailed costs can
increase the requirement. The full 500-item Verified panel may therefore leave
the three-point claim unresolved. Three seeds on 500 issues are not 1,500
independent issues. Additional seeds characterize model stochasticity; they do
not remove uncertainty about the task population. A thesis can report an
inconclusive interval or a negative result with a useful reproducible method.

Before committing to the full matrix, run a small predeclared metering and
evaluator validation block, estimate resource needs, and choose the affordable
registered scope. The user's US$100 authorization concerns the first Runpod
experiment and is not a promise that thousands of frontier API trajectories or
all evaluation infrastructure fit that amount.

## Comparison with existing research

The detailed primary-source review and retrieval hashes are in
[personal-agent-prior-art.md](../thesis/personal-agent-prior-art.md) and its
[source register](../thesis/personal-agent-prior-art-sources.json).

| Prior work | Already establishes | Remaining distinction for this study |
|---|---|---|
| [Router-R1](https://arxiv.org/abs/2506.09033), inspected v3 | A trained small controller interleaves thinking, routing and answer integration; cost ablations | Its principal experiments are QA, not repository repair with independent executable acceptance; main runs use zero cost coefficient |
| [EdgeWise](https://arxiv.org/abs/2610.17560), inspected v2 | Local small solver, selective cloud help, SFT/RL delegation, context-transfer ablations on software/terminal tasks | Replicate with full accounting and an explicit quality margin; isolate expert clarification/challenge versus one-way help |
| [Uno-Orchestra](https://arxiv.org/abs/2605.05007) | Learned heterogeneous orchestration across 13 benchmarks including SWE-bench Verified | Does not make “a small coordinator selects experts” a new contribution; author-linked implementation was unavailable during review |
| [DecisionBench](https://arxiv.org/abs/2605.19099) | Controlled peer pools and information channels; routing process gains need not yield quality gains | Apply similarly controlled contrasts to executable repository repair and total cost |
| [Do Personalized Skills Help Coding Agents?](https://arxiv.org/abs/2608.10319) | Personalized/generic/shuffled-skill comparisons; generic skills can outperform personalization | Memory advantage must be independently tested, not attributed to dialogue |

EdgeWise is particularly close. On its reported SWE-ReBench-03 setup, the
GPT-5.5 comparison changes pass@1 from **56.36% to 58.18%** with **51.22% lower
reported cloud API cost**; the Opus comparison changes **60.00% to 57.27%** with
**62.68% lower API cost**. Its main accounting excludes local SLM computation,
and its inspected text does not establish this study's noninferiority gate.
Those are within-paper findings, not projected TTGL savings. Its training uses
40 A100 80 GB GPUs, so the current single-GPU US$100 scope cannot claim a faithful
reproduction of that training configuration. Check release availability before
promising an integrated checkpoint.

The paper's historical [SWE-bench cost table](../thesis/task-price-comparisons.csv)
uses 500 tasks per mini-SWE-agent 2.0.0 submission. Examples include MiniMax M2.5
high at 75.8% and reported `$0.0733` per assigned task, and Claude Opus 4.6 at
75.6% and `$0.5515`. These establish useful *historical* operating points under
that scaffold; neither figure is a current-model quote or a matched comparison
with TTGL's new trajectories. Do not combine unrelated leaderboard accuracy
and current token pricing into a claimed measured frontier.

## Novelty judgment

**The broad architecture is not sufficiently novel by itself.** A master's
thesis can be strong as a careful replication with an independently useful
extension: a standard-benchmark, budget-matched measurement of what reciprocal
conversation contributes, full cost and quota accounting, transparent failure
analysis and a reproducible open harness. Research publication novelty depends
on the completed results and the closest contemporaneous comparisons; it cannot
be guaranteed by a title or a lit-review search.

A positive result must show that dialogue beats a serious alternative rather
than simply spending more inference. A negative result can establish that a
simple router or one strong agent already reaches the relevant frontier. Open
weights, local operation, personalization and learning become additional claims
only after their own controlled replications. Keep those claims out of the
headline until the corresponding evidence exists.

## Executed standard-benchmark evidence in this repository

The [SWE-bench Verified public replay](../../results/swe-replay-001/README.md)
has now executed cross-fitted allocation over all 500 tasks and ten published
model runs per task. Its primary cost/benefit router resolves 64.2%, versus
GPT-5.2 high's 72.8%, while reducing **historical source-estimated inference
cost** from `$0.4736` to `$0.2551` per task: 46.1% lower expense with an 8.6-point
quality loss. The paired task-bootstrap quality interval is −11.605 to −5.600
points. The primary target fails; a similar expected random half allocation
has 64.5% resolution. This is useful negative evidence about the tested router,
not evidence against every possible learned router or conversation policy.

The exploratory portfolio at utility weight 0.25 reaches 76.2% at
`$0.1154/task`. Against GPT-5.2 this looks attractive, but the inexpensive
MiniMax 2.5 high control reaches 75.8% at `$0.0733/task`; the portfolio's cost
ratio is 1.57 and its 0.4-point quality difference has a task-bootstrap interval
of −0.8 to +1.6 points. That additional comparator was explicitly selected for
discussion after inspecting the single-model table. The full declared policy
grid is retained. There is no established routing benefit over the cheap
single model, and no measured dialogue benefit or Codex quota result.

The analysis uses historical source estimates, not new provider invoices.
Its intervals condition on the fitted routing policies and published single
attempts, not new-run stochasticity. Router compute and environment costs are
excluded with separately labelled overhead sensitivity. Its exploratory freeze
followed inspection of public aggregate results. Those limitations belong in
the thesis alongside the numerical findings; a reproducible negative result is
more informative than presenting an outcome-aware oracle as achievable savings.
