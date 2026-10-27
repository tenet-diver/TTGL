# Fresh metered Luna / Sol routing experiments

The completed live software-engineering panel contains 12 SWE-bench Verified
tasks, six conditions, and 72 officially graded assignments. Three additional
prompt-development studies contain four already observed tasks and three arms
each (36 assignments). All 108 assignments passed an independent audit joining
native reports to exact patch hashes and reconciling event-level model token
deltas with final manifests. Historical published replay records and the earlier
BugsInPy feasibility pilot are separate evidence.

## Original matched panel

| Condition | Resolved | Total model-cost scenario (USD) | Expert requests |
|---|---:|---:|---:|
| Luna alone | 9/12 | 0.070117 | 0 |
| Sol alone | 10/12 | 1.386344 | 0 |
| Pre-task model selection | 11/12 | 0.955308 | 0 |
| One-way expert assistance | 9/12 | 0.110168 | 1 |
| Fresh expert on each request | 8/12 | 0.104738 | 1 |
| Continuing expert conversation available | 9/12 | 0.062689 | 0 |

The pre-task selector achieved the highest observed resolution count, with
31.1% lower model-cost scenario than Sol alone. That is a descriptive result on
this panel, not evidence of population superiority. The continuing-conversation
arm saved 95.5% but retained only 90% of Sol's aggregate accuracy, missing the
joint target. It made no expert requests, so its result does not demonstrate
conversational collaboration. Luna alone saved 94.9% with the same aggregate
resolution count. There is no observed dialogue benefit in the original panel.

## Prompt development with matched independent solving guidance

Each development study gave its standalone controls the same common solving and
verification instructions as the assisted agent. The adaptive and bounded
cheap-first assisted conditions each resolved 4/4 tasks using one expert request
across the panel. Their respective Luna-only controls resolved 2/4 and 3/4; both
Sol-only controls resolved 4/4. Assisted scenario savings relative to their own
Sol control were 87.1% and 89.1%. The compact expert condition saved 95.7% but
resolved 3/4, matching its Luna-only control; it made no expert requests.
Because that condition never invoked an expert, its outcome cannot establish
that expert-context compaction caused either the quality difference or saving.

![Cost versus resolution for each matched panel. Green marks the joint target; separate panels do not pool repeated task outcomes.](../../results/prompt-comparison-001/figures-002/combinations.png){width=100%}

The outcome-first, cost-second development selection rule chose bounded
cheap-first before held-out inference. These four cases were already observed
and cannot establish generalization. Across all studies, no assisted arm meets
both the 95% cost-reduction and 95% relative-accuracy point targets. Costs use
the frozen published Codex Standard token-rate scenario, include all measured
controller/expert/integration inference, and exclude setup and grading. They
are not observed invoices or full deployment costs.

## Held-out status and bounded next study

Held-out model inference has not begun. The first independent control case,
`django__django-7530`, passes the recorded fail-to-pass test without a repair;
base and gold native reports both resolve. The archived evaluator therefore
cannot discriminate repair success for that case. Preserve the failed control
gate and resolve its environment disposition before proceeding; do not override
the score or silently substitute an easier case. An explicit pre-inference
disposition now excludes this invalid control under the original reservation's
eligibility rule, without replacement. Eleven reserved cases are undergoing
readiness checks; the selected policy is unchanged.

A separate SWE-bench Pro V2 subset is reserved: 12 repository-diverse development
tasks for inexpensive prompt iteration and 24 disjoint validation tasks. The
642-task population is not an automatically scheduled run. Only public inputs
have been acquired; controls, adapter validation and model inference remain
unexecuted. Use the official maintained harness and pristine grading protocol.
The open-weight replication and subsequent distillation/RL comparisons follow
this proprietary routing study and are not current learning results.
