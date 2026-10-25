# System design and formalization

## Design principles

The system follows a reuse-first principle. Existing software supplies the agent loop, repository tools, local inference, provider API adaptation, training and benchmark execution. Custom components are introduced only for the research question: recording the decision state, applying a routing policy, measuring costs and joining outcomes to immutable task identifiers. This separation helps avoid comparing an extensively engineered portfolio system against an artificially weak baseline.

The proposed repository-level harness is mini-SWE-agent, subject to a pinned-version integration check. Its command-oriented interface allows the same repository interaction pattern to be used with multiple model providers. Ollama or llama.cpp is a candidate local deployment runtime; the actual supported model architecture, quantization, chat template and tool behavior must be verified together. AgentLab/BrowserGym is the browser-domain scaffold candidate. Managed endpoints or vLLM can supply remote configurations, including small models and compatible customer adapters. Transformers, PEFT and TRL provide the student-training stack. Choosing these components is a design decision, not a claim that all combinations have passed compatibility tests.

The experiment separates four concerns: the policy determines which model to use; the model proposes an action; the harness determines whether and how that action may execute; and the evaluator assesses the final artifact in an independent environment. A model switch does not grant new tool permissions. Tests used by the agent for development are distinguished from hidden benchmark checks used for final scoring.

![Proposed architecture and evidence flow. Arrows indicate interfaces, not measured performance.](figures/architecture.png){width=95%}

## Model registry, state and eligible actions

The model registry records each candidate's domain and modality support, checkpoint or service revision, license, tokenizer/template, precision, inference settings, endpoint, measured resource requirements and compatible adapter identity. It distinguishes capabilities documented by a provider from capabilities verified in the common harness. A customer preference for a provider, an offline-only mode or a device memory limit changes the eligible set before the router scores it.

Let task $i$ describe an issue or browser objective in a pinned environment. At decision step $t$, the observable state is

$$
s_{it}=(x_i,h_{it},w_{it},b_{it},d_i,m_{t-1},e),
$$

where $x_i$ contains permitted task context, $h_{it}$ is interaction history, $w_{it}$ is the observable workspace or browser state, $b_{it}$ is remaining budget, $d_i$ records deployment and customer constraints, $m_{t-1}$ identifies the current configuration, and $e$ identifies the frozen portfolio epoch. The router receives a declared feature function $\phi(s_{it})$. It cannot access hidden evaluation tests, reference patches, future tool results or eventual success labels.

The eligible model configurations are $\mathcal M_e(s)\subseteq\{m_1,\ldots,m_K\}$. The action set contains those configurations and a stop action. Verification may be an explicit action in a secondary sequential experiment and carries its own resource cost. The initial treatment selects one model configuration for the complete attempt. Parallel voting, multiple simultaneous agents and weight merging are separate interventions, not necessary features of this portfolio.

A policy $\pi(m\mid s,\lambda)$ chooses an eligible action subject to permissions, context capacity and budget. It records whether a candidate was excluded by capability, price, memory, availability or customer policy. No candidate fitting the remaining constraints yields a recorded unresolved or budget-exhausted outcome. An undocumented fallback must not silently change the experimental condition.

## Expected utility and customer price sensitivity

For configuration $m$, let $p_m(s)$ be the probability of successful task completion under a bounded continuation, $c_m(s)$ its expected remaining economic cost, and $\ell_m(s)$ its expected remaining latency. The quality definition belongs to the domain evaluator. A simple proposed decision rule is

$$
m^*(s)=\operatorname*{arg\,max}_{m\in\mathcal M_e(s)}
\left[\widehat p_m(s)-\lambda\widehat c_m(s)
-\eta\widehat\ell_m(s)-\widehat\kappa(m_{t-1},m,s)\right].
$$

Here $\lambda$ expresses the cost penalty, $\eta$ expresses latency preference, and $\kappa$ expresses any additional handoff penalty in the same utility units. Monetary and time components of handoff are included either in $c_m,\ell_m$ or in $\kappa$, never twice. Quality loss from summarization or state transfer should be reflected in continuation success estimates. These are quantities to measure and calibrate; the notation is not evidence that they are known accurately.

The product can expose a price-per-task budget or an accepted quality target rather than an uninterpretable numerical $\lambda$. Development data map that preference to a calibrated policy. Both an expected-spend target and a hard attempt cap are recorded: an expectation alone is not a guarantee about any individual bill. Higher price sensitivity may favor a hosted small model, a local model or an inexpensive specialist, depending on the complete costs. Neither size nor location fixes the choice.

The earlier two-model rule is a special case. With candidates $L$ and $R$ and equal nonfinancial constraints, choosing $R$ requires its expected success improvement over $L$ to justify its incremental cost. A local-failure score $1-\widehat p_L$ is an informative comparator, but it does not identify which of several alternatives can help. For a larger pool, success and cost estimates must be assessed per candidate and on the tasks where the policy selects it.

Task features can include permitted issue/context embeddings, programming languages, frontend/backend indicators, browser modality and resource availability. These labels can overlap, and a task can require several capabilities. A domain label is a useful low-cost baseline rather than a reason to assume one model is universally best for that domain. Features requiring a model call or repository analysis incur acquisition cost.

Calibration is an empirical relationship between predictions and outcomes. Verbal confidence, token likelihood and self-evaluation are candidate features, not correctness guarantees. Outcome-informed selection over all candidates measures diagnostic headroom; it does not demonstrate that the deployed router reaches the union of their capabilities. New models acquire development evidence and a versioned router/calibration update before joining a test epoch. This does not require retraining every generator, and retraining the router alone does not prove that a new candidate is useful.

## Sequential delegation and state continuity

A sequential handoff differs from task-level selection. It first pays for work by one configuration, observes permitted evidence and then decides whether another should continue. If the first attempt changes files, the continuation receives a well-defined state: base commit, current patch, task objective, executed commands, outcomes and remaining budget. A browser handoff additionally preserves the authenticated session, tabs, navigation state and side-effect record through the shared browser environment; session state is distinct from a model cache. Unfinished tools are completed or cancelled before switching. The system does not attempt to transfer incompatible key–value caches or opaque provider reasoning representations.

All work before handoff remains part of the portfolio's cost. A continuation can require extra context and have different success probability from a fresh attempt. The study distinguishes $p_m(x)$ from $p_m(s_{it})$ after another configuration has acted. Substituting an archived standalone outcome for that continuation would erase a central system effect. The default is to retain a model for an entire attempt; phase-level switching and a minimum net-benefit margin are tested before unrestricted per-call switching. The adaptation and switching chapter defines cache and adapter compatibility boundaries.

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

An adapted portfolio member changes the distribution of errors on which the router was trained. The experiment evaluates both a frozen router with the adapted student and a newly calibrated router fitted without final-test labels. This forms a factorial distinction between student capability and routing adaptation. Otherwise, an apparent gain in inexpensive-model coverage could be attributed incorrectly to the generator when it arose from changed allocation. A customer may share verified examples across compatible training pipelines while retaining a separate adapter artifact for each selected base revision.

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
