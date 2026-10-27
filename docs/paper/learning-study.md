# Learning from verified interaction: prospective follow-up

This chapter specifies a follow-up to the fixed-model routing experiment. It
does not report trained checkpoints, GPU measurements, distillation gains or RL
results. First establish proprietary Luna/Sol prompt and routing performance;
then replicate the small-only, large-only and cooperative comparisons with
open-weight models. Learning is an additional intervention on that replication,
not an explanation for the current proprietary results. Hosted Luna weights are
not available to this project for fine-tuning.

## Training data distinct from evaluation

Use executable repository tasks for training, rather than treating the final
SWE-bench evaluation set as a source of demonstrations. Existing candidates are
SWE-Gym, which supplies repository tasks with executable environments and test
verification, and SWE-smith, which supplies generated repair tasks and released
expert trajectories [@pan2025swegym; @yang2025swesmith]. Inspect pinned releases,
licensing and provenance before acquisition. These are candidate sources; no
training corpus from them has yet been assembled for this study. The existing
LiveCodeBench solution-level training scaffold remains a separate, narrower
algorithmic-code experiment, not repository-agent training.

Partition data before collecting adaptive trajectories. The training partition
supports demonstrations, student rollouts, verifier feedback and weight updates.
A separate development partition selects prompts, reward coefficients,
checkpoints and stopping rules. A sealed evaluation panel measures the final
learning curve after those decisions are locked. Tasks used to tune the current
Pro prompts belong to development history and cannot later be called unseen
evaluation. The already reserved validation tasks must likewise be retired from
that role if their outcomes inform another update.

Prevent overlap by task identity, upstream issue/pull request, patch or near-copy
similarity, and common synthetic ancestor. A mutation of a held-out task is not
new training data. Group related issue families together. Where practical,
reserve repositories for a separate cross-repository transfer evaluation;
distinguish that endpoint from generalization to new issues in familiar
repositories. Report language and repository composition, exclusions and
pretraining-contamination limits. Benchmark train/test labels alone do not prove
that two differently named releases are independent.

## Observable traces and credit assignment

Record task and environment revisions, public instructions, visible assistant
actions, tool inputs and observations, edits, public checks, failed approaches,
delegation decisions, selected handoff context, expert messages and subsequent
integration. Bind the final patch and external verification receipt to the
trajectory, and record model identities, inference parameters, tokens, latency
and cost evidence. Preserve unsuccessful episodes for analysis and controlled
negative examples. Do not collect private model reasoning or place evaluator
tests and reference patches in the policy context.

The current Codex journals retain structured controller/expert responses and
tool-status hashes, but deliberately omit full tool inputs/outputs. They support
routing analysis and selected public conversation examples; they are not a
complete replayable action dataset. Future collection therefore needs a
separately versioned observable-trace recorder. Do not retroactively invent
missing actions or alter frozen trials to imply that complete traces existed.

Final success verifies the episode's patch, not every intermediate action.
Successful episodes can contain poor requests or incorrect expert suggestions.
For supervised training, choose explicit targets: investigation/action sequences,
help-request formulation, expert-answer integration, or verification. At a
delegation decision the input ends before the expert's future answer; hidden
final grades cannot become features predicting when to ask. Mask tool and user
tokens from the student loss. Expert messages are context unless the declared
training target is a teacher demonstration of the student's own role. Preserve
state/action boundaries when chunking long trajectories.

## Sequence and on-policy probability distillation

The sequence-distillation baseline trains a compatible student adapter on
selected verified demonstrations using the maintained TRL/PEFT path. Text
supervision does not require teacher/student tokenizer identity. Balance distinct
tasks and disclose rejection rates, target-token exposure and selection bias;
do not count many traces of one easy task as many independent tasks.

The probability-distillation arm generates trajectories with the current student
and obtains teacher probability feedback conditioned on those same visible
histories. This tests correction in states reached by the student, rather than
only imitation of expert-generated histories. Declare whether the objective
uses full vocabulary distributions, truncated top-k distributions or a
sampled-token estimator; these are different estimators, not interchangeable
forms of complete logit access. Verify token-ID alignment, vocabulary, templates,
temperature, masks and treatment of tool boundaries. Same-family model names do
not establish compatibility.

Ordinary generation APIs can supply demonstrations. An on-policy scoring service
must additionally score arbitrary supplied student sequences; log probabilities
only for the teacher's own sampled completion do not suffice. Self-hosted
teacher weights or a suitable scoring API can provide that access. Full logits
are not mandatory for every probability-distillation objective. Compare sample
and compute efficiency empirically: richer supervision may reduce required
examples while increasing teacher-scoring cost. Do not promise faster learning
or software-task transfer from reasoning-benchmark evidence alone.

## Reinforcement learning as a separate intervention

RL requires resettable training environments and fresh policy rollouts, not just
a static conversation dataset. Use independently executed training-task
correctness checks as the outcome signal, alongside explicit inference-cost
accounting. Keep policy access separate from the verifier. Add terminal-state
and test-integrity checks so editing checks, claiming tests passed, or declining
all work cannot earn a successful-repair reward. Unavailable dependencies and
infrastructure failures require a declared disposition, rather than an invented
model-quality label.

Optimize cost subject to a quality constraint, or use a registered reward family
and select its operating point on development data. Sweep cost coefficients on
development only and report the resulting frontier; fewer expert calls alone
are not success. Hold time, tool permissions and test access constant. Use a
maintained agent-RL framework after validating its environment and action
interfaces, rather than introducing an unverified custom optimizer.

Separate RL from base, sequence-SFT and probability-distillation conditions.
If RL starts from an SFT checkpoint, the matched comparison is that exact SFT
checkpoint with versus without RL, and the accumulated SFT cost remains in the
RL condition. RL from the untouched base is a separate arm. Likewise, on-policy
probability distillation is teacher-supervised learning; sharing rollout code
with RL does not make the objectives equivalent.

## Factorial controls and learning curves

| Student checkpoint | Small alone | Small with frozen large expert |
|---|---|---|
| Untouched base | Required | Required |
| Sequence-distilled | Required | Required |
| Probability-distilled | Required | Required |
| Registered RL treatment | Required | Required |

A fixed large-only model is the common capacity reference. Serve each eligible
small checkpoint locally and remotely with identical weights/adapters and
matched inference settings where supported. Document precision, quantization,
runtime, context length and device differences; do not interpret a hosting or
precision change as a training gain. Keep the expert revision and common task
context fixed. Compare a frozen routing prompt with separately recalibrated
routing only as explicitly separate controls. User memory and preferences are
the same across arms and remain distinct from learned weights.

Start with a bounded integration pilot and freeze feasible data/compute
milestones from its measured throughput before claiming a longitudinal study.
Count distinct eligible task arrivals, verified demonstrations, target tokens,
student rollouts and optimizer updates separately. Register acquisition order,
seeds and checkpoint selection before evaluation. Compare incremental updates
with restarting from the same base on accumulated data when budget permits;
do not assume that more rounds cause monotonic improvement. Measure forgetting
and transfer on tasks outside the adapted workload.

Plot resolution against total inference cost at each registered checkpoint,
separately for independent and cooperative operation. Plot learning against
distinct tasks, teacher tokens, GPU-hours, elapsed time and measured expenditure.
Include a lifecycle view: acquisition plus scoring plus training cost, amortized
over a stated number of later tasks, together with their inference cost. Report
the break-even workload only when measured training expense and positive
per-task saving support it; otherwise it is unknown or absent. Distinguish
published token-rate scenarios from observed charges and local hardware costs.

All arms face the same frozen evaluation tasks and budgets. Report paired
successes and failures, expert-assisted task fraction, consultation count,
verification failures, latency and uncertainty. Evaluate frozen checkpoints on
the sealed panel only after training and analysis choices are locked; use fresh
development panels for adaptive monitoring. The target remains at least 95%
relative large-only accuracy with at least 95% lower total task inference cost.
Training may shift the frontier without reaching that target; lifecycle savings
require additional evidence. No current result establishes either learning or
amortized-cost improvement.
