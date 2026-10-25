# System design and formalization

## Design principles

The system follows a reuse-first principle. Existing software supplies the agent loop, repository tools, local inference, provider API adaptation, training and benchmark execution. Custom components are introduced only for the research question: recording the decision state, applying a routing policy, measuring costs and joining outcomes to immutable task identifiers. This separation helps avoid comparing an extensively engineered dual system against an artificially weak baseline.

The proposed repository-level harness is mini-SWE-agent, subject to a pinned-version integration check. Its command-oriented interface allows the same repository interaction pattern to be used with multiple model providers. Ollama or llama.cpp is a candidate local deployment runtime; the actual supported model architecture, quantization, chat template and tool behavior must be verified together. A hosted endpoint can initially provide the remote model. Transformers, PEFT and TRL provide the student-training stack. Choosing these components is a design decision, not a claim that all combinations have passed compatibility tests.

The experiment separates four concerns: the policy determines which model to use; the model proposes an action; the harness determines whether and how that action may execute; and the evaluator assesses the final artifact in an independent environment. A model switch does not grant new tool permissions. Tests used by the agent for development are distinguished from hidden benchmark checks used for final scoring.

![Proposed architecture and evidence flow. Arrows indicate interfaces, not measured performance.](figures/architecture.png){width=95%}

## State and action spaces

Let task $i$ be an issue description paired with a repository at a fixed base commit. At decision step $t$, the observable state is

$$
s_{it}=(x_i, h_{it}, w_{it}, b_{it}, d_i),
$$

where $x_i$ contains the task and permitted repository context, $h_{it}$ is the interaction history, $w_{it}$ records workspace changes and available verification evidence, $b_{it}$ is the remaining budget, and $d_i$ describes the eligible deployment configuration. The router receives a documented feature function $\phi(s_{it})$. It cannot access hidden evaluation tests, reference patches, future tool results or the eventual resolution label.

The minimal action set is $\mathcal{A}=\{L,R,\mathrm{stop}\}$, where $L$ and $R$ request local or remote continuation. A sequential extension may include an explicit verification action $V$. Its benefit and cost must be assessed as an action; verification is not a free source of confidence. The initial confirmatory policy is kept simple enough to attribute differences to routing. Richer orchestration, parallel branches and multiple simultaneous agents are separate experiments.

A policy $\pi(a\mid s)$ chooses an action subject to hard constraints. These include user/provider permissions, model capability, context capacity and remaining budget. Confidence cannot override a prohibition on sending a repository to a remote provider. When no permitted action fits the remaining budget, the task terminates with a recorded unresolved or budget-exhausted outcome rather than silently changing the experimental conditions.

## Estimating benefit rather than asking for confidence

Let $p_m(x)$ be the conditional probability that a bounded run with model $m$ resolves the task under the common harness. A pre-call router can estimate

$$
\Delta p(x)=p_R(x)-p_L(x).
$$

It may prefer remote execution when the expected benefit exceeds an incremental-cost penalty:

$$
\widehat{\Delta p}(x) > \lambda\,\widehat{\Delta C}(x),
$$

with $\lambda$ chosen using development data according to the prespecified cost or quality constraint. This expression does not assert that resolution and cost are perfectly predictable. It defines a decision objective and exposes the quantities requiring calibration. A small classifier, an embedding-based predictor or an existing routing model can instantiate it; a separate generative router is not required by the architecture.

The local-failure comparator ranks by $1-\widehat p_L(x)$. It is informative because it tests the intuitive hypothesis that local uncertainty is enough. The benefit predictor instead asks whether remote execution is expected to change the outcome. The latter objective can direct remote resources toward tasks with a realistic chance of improvement rather than those that are simply difficult. If the product values particular classes of requests, their utility weights must be declared before evaluation rather than inferred after seeing which tasks the policy serves.

Calibration is an empirical relationship between predictions and outcomes. A statement such as “I am 90% confident” is not accepted as a calibrated probability. Token log probabilities, hidden-state features and self-evaluation outputs are candidate features, not correctness guarantees. Their acquisition overhead is recorded, and a feature is excluded if it requires information unavailable at the policy's decision point.

## Sequential delegation and state continuity

A local-first cascade differs from pre-call selection. It first pays for a local attempt, observes its permitted evidence and then decides whether to escalate. If the local attempt changes files, the remote continuation must receive a well-defined state: base commit, current patch, task objective, executed commands, outcomes and remaining budget. Unfinished tools are completed or cancelled before switching. The system does not attempt to transfer incompatible key–value caches or opaque provider reasoning representations.

The cost of an unsuccessful local attempt remains part of the dual system's cost. Remote repair can also require extra context, and its probability of success may differ from starting remotely. The thesis therefore distinguishes $p_R(x)$ from $p_R(s_{it})$ after local work. Assuming that the same remote-only outcome can simply be substituted after any local failure would erase a central system effect.

For paired comparisons, every experimental condition starts from the same immutable repository snapshot. Workspaces, generated files and cached agent conclusions are isolated by task, seed and condition. Dependency caches may be shared only when they do not expose solutions or mutable task state. Replaying a tool event is not equivalent to re-executing it: external side effects, generated dependencies and process state require explicit treatment.

## Confidence-scheduled verification as an analogy

DeepInfer provides a concrete implementation example of using learned confidence estimates to allocate inference computation. Its DSpark mechanism predicts draft-token acceptance and schedules verification using acceptance estimates and runtime cost information. This motivates a general design principle: spend computation where it is predicted to produce useful progress, and compare predicted benefit with observed behavior.

The analogy has limits. Token-level speculative decoding involves a particular relationship between a draft distribution and target verification. A task router that accepts a local patch does not inherit that algorithm's distribution-preservation properties. Repository tests are incomplete, remote reviews can be wrong, and task failure events are correlated. Multiplying arbitrary subtask confidence scores as if they were independent is unjustified. The proposed system uses direct task/continuation outcome labels and reports uncertainty rather than importing a token-level guarantee.

## Student learning mechanisms

The adaptation study begins with sequence distillation. For training task $i$, a teacher generates an observable solution or trajectory, which is retained only if it passes the declared verification procedure. The student is trained on the resulting target sequence $y_i^T$:

$$
\mathcal{L}_{\mathrm{SFT}}(\theta)
=-\sum_i\sum_{t\in\mathcal{T}_i}
\log p_\theta(y^T_{it}\mid x_i,y^T_{i,<t}),
$$

where $\mathcal{T}_i$ contains completion tokens included in the loss. Prompt tokens are masked. LoRA changes which parameters are optimized; it does not determine whether the targets are correct or representative. Complete examples that exceed the declared context limit are explicitly handled instead of silently truncating a solution and treating the remainder as valid supervision.

Verification filtering creates selection effects. Tasks with no verified teacher solution disappear from the training set, while the evaluation corpus must retain its prespecified eligibility rules. A student may consequently receive a distribution biased toward tasks the teacher already solves. Counts, task classes and exclusion reasons are recorded. A token- and compute-matched adaptation control is needed to distinguish teacher-data quality from the mere effect of extra training.

A token-distribution arm has a different objective. With aligned teacher/student tokenization, an example formulation is

$$
\mathcal{L}_{\mathrm{KD}}
=\alpha\mathcal{L}_{\mathrm{SFT}}
 +(1-\alpha)\tau^2\sum_t
 D_{\mathrm{KL}}\!\left(p_T^\tau(\cdot\mid c_t)\,\Vert\,
 p_\theta^\tau(\cdot\mid c_t)\right).
$$

Temperature $\tau$, mixture coefficient $\alpha$, context $c_t$, vocabulary mapping and teacher precision must be specified. Different Qwen and DeepSeek tokenizers cannot be assumed to share token events. A same-family teacher/student pair is a practical controlled case, but still requires exact vocabulary, special-token and template checks. A provider's limited top-$k$ log probabilities are not the full teacher distribution; treating the omitted probability mass as zero changes the objective and requires its own method and ablation.

RLAIF describes the use of AI-generated feedback. It is distinct from using executable tests as a verifiable reward. DPO on teacher-ranked pairs is one possible preference-learning arm; DPO on pass/fail pairs is verifier-based preference learning. Online reinforcement learning adds generation and reward-computation costs and is a separate extension. The experiment does not relabel ordinary supervised fine-tuning as RLAIF.

## Adaptation and routing as separate interventions

An adapted student changes the distribution of errors on which the router was trained. The experiment evaluates both a frozen router with the adapted student and a newly calibrated router fitted without final-test labels. This forms a factorial distinction between student capability and routing adaptation. Otherwise, an apparent gain in local coverage could be attributed incorrectly to the language model when it arose from threshold changes.

Model/adapter releases are immutable artifacts with hashes, base revision, tokenizer revision and training provenance. The exact deployed artifact—including quantization or adapter merging—is reevaluated. Training-time loss alone is not a software-engineering outcome, and improvements before export do not guarantee the same behavior in a local runtime.

## Cost model

For model call $j$, API expense is recorded using the provider's billed categories:

$$
C^{\mathrm{API}}_j
=\frac{r_u n_u+r_c n_c+r_o n_o+r_w n_w}{10^6}+f_j,
$$

where $n_u,n_c,n_o,n_w$ represent uncached input, cached input, output and any separately billed cache-write units, with their respective rates. A category is omitted or reformulated when a provider bills differently. Reasoning/thinking tokens are included according to the actual invoice definition; they must not be counted twice as both visible output and an independent category. Tool, search, batch, regional and context-tier charges are stored explicitly when applicable.

The complete task cost includes all model calls, routing, verification, execution and relevant allocations:

$$
C_i=\sum_{j\in i}C_j^{\mathrm{model}}
 +C_i^{\mathrm{router}}+C_i^{\mathrm{sandbox}}
 +C_i^{\mathrm{verification}}+C_i^{\mathrm{storage/network}}
 +C_i^{\mathrm{allocated}}.
$$

For self-hosted models, GPU rental is charged for provisioned time, including loading, idle periods and shutdown delay. Local operation is reported under two accounting views: marginal cash expenditure and total economic cost including energy and hardware allocation. A zero API rate is therefore not represented as zero total cost. Cost per resolved issue has the total cost of all assigned attempts, including failures, in its numerator and the number of resolved issues in its denominator. Under repeated sampling, the numerator and denominator use the same registered aggregation. Zero resolved issues makes this ratio undefined; unsuccessful runs cannot be removed from the invoice.

Distillation adds an amortization question. If training and data generation cost $C_{\mathrm{adapt}}$ and the adapted system saves an expected $s$ per task at an acceptable quality level, an illustrative break-even task count is $N=C_{\mathrm{adapt}}/s$ for $s>0$. No break-even claim is valid when quality is not maintained or the estimated saving is nonpositive. Estimates must be accompanied by workload assumptions and uncertainty rather than presented as a guaranteed product margin.

## Evidence record

Every run records task and repository identifiers, base commit, dataset/harness revisions, container image digest, condition, model/adapter revision, decoding settings, seed where supported, resource limits, prompts/tool traces under the retention policy, output patch, evaluator logs and billed usage. Cached and uncached scenarios are identified separately. A run manifest links these records through hashes and identifies whether a stage was prepared, started, completed, failed or unrun.

This evidence structure serves both scientific reproducibility and task continuity. Jira tickets can index work and Confluence can host the manuscript, but neither substitutes for run manifests and versioned artifacts. If external tools are unavailable, local state records remain explicitly pending synchronization and must not invent issue keys, page IDs or completed runs.
