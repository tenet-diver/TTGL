# Introduction

## Motivation

An assistant's useful output is completed work: a repository change that passes its acceptance checks, a browser workflow that reaches the requested state, or a frontend that meets a specified interaction requirement. Generating a plausible answer is only part of that process. The model operates through tools, observations, execution environments and stopping rules, so its performance must be measured as part of an agent system. A single language-model score does not fully characterize the service the customer receives.

Model capabilities are heterogeneous. Backend debugging, visual frontend work, unfamiliar programming languages, long repository contexts and browser navigation can require different strengths. Some tasks need visual grounding; others can be completed efficiently from structured text. A smaller specialist may outperform a larger general model on one workload while failing on another. These possibilities motivate empirical comparison, not an assumption that specialization or parameter count guarantees superior performance.

The proposed TTGL assistant therefore selects among a portfolio of eligible models. The portfolio may include several small models, larger general models, browser specialists and compatible customer-adapted variants. A model can run on a desktop, a shared GPU service or a managed endpoint. Model size, weight availability, execution location and customer billing are separate attributes. An open-weight model served remotely still incurs infrastructure cost; local execution consumes memory, energy and time even when the customer pays no per-call fee.

The working title, **We Gotta Combine!**, expresses the hypothesis that complementary models can be more useful together than a fixed choice. Here, combination primarily means selecting an appropriate model for each task. It does not require running every model, voting on every answer, merging their weights or switching after every generated response. Those interventions have different costs and require separate experiments.

## The research problem

The central problem is to predict which eligible model offers the best expected outcome for a task at the customer's price sensitivity. An inexpensive model may be sufficient; a more expensive model may provide enough additional success probability to justify its cost; or neither may have a reasonable chance of success within the budget. The router must learn those conditional differences. Detecting that a task is difficult is insufficient if all candidates fail on it.

A task's full price is not its advertised output-token rate. Repeated context processing, tool calls, failed attempts, verification, model loading, cache behavior, queueing and infrastructure allocation all affect the final bill or economic cost. The study therefore reports both dollars per assigned task and dollars per successful task. The latter includes the cost of failures in its numerator. Price scenarios derived from token rates are useful for planning, but measured task costs require actual traces and an explicit accounting boundary.

Choosing the portfolio itself is part of the problem. Adding a specialist may improve coverage while increasing data acquisition, model residency, adapter training and maintenance costs. Several small remote models may be practical for a shared service but unsuitable for a memory-constrained laptop. Conversely, one well-adapted local model may be preferable when offline operation or privacy dominates small average accuracy gains. The experiment treats the number and sizes of models as choices to evaluate, not fixed consequences of the words “small” and “large.”

Model releases and workloads also change over time. A newly released model cannot be assigned a reliable router score merely because its provider reports a better benchmark. It must pass interface and licensing checks, acquire development measurements and enter a versioned pool. Updating router parameters can then be much cheaper than retraining every generative model, but it still requires evidence. Customer adaptation and portfolio refresh are separate interventions whose effects must be identified independently.

## Scope and terminology

A **model configuration** includes the base checkpoint or service revision, tokenizer and prompt template, precision, inference settings, adapter where applicable, runtime and endpoint. Two deployments of the same checkpoint can have different cost and latency; an adapted checkpoint can have different accuracy. A **portfolio** is the finite, frozen set of configurations eligible within a study epoch. A **router** predicts their conditional value and chooses an eligible action subject to budget, permissions, modality and device constraints.

A **single-model agent** may invoke many tools and make many model calls, but keeps the same configuration throughout its trajectory. A **portfolio-routed agent** can choose a different configuration for different tasks. A **switching agent** can also transfer an ongoing task between configurations. The initial portfolio experiment uses task-level selection so that routing quality can be assessed before adding the confounding effects of state transfer. Two-model local/remote routing is a restricted case, retained as a useful baseline and inexpensive integration pilot.

“Open-weight” means weights are available under a published license; it does not establish all properties of an open-source AI system or grant unrestricted commercial use. Weight licenses, source-code licenses, API terms and training permissions are recorded separately. “Free model” is consequently not used as a synonym for zero total cost. An open-only pool and a pool permitting closed APIs can be compared under clearly declared availability rules.

The primary confirmatory outcome is repository-level issue resolution under a pinned software-engineering evaluator. Browser interaction is a separate domain study using its own common scaffold and task-success definition. Frontend development is not interchangeable with browser navigation: producing an application and operating an existing website require different acceptance checks. Programming language, frontend/backend role and task type are prespecified, potentially overlapping strata. Domain-level scores are not pooled into one accuracy number unless the workload weights and normalization have been declared in advance.

## Research questions

The thesis organizes the empirical work around six questions:

1. **Portfolio value:** Can a frozen multi-model policy retain success within a prespecified tolerance of a strong fixed model selected on development data while reducing total cost per task?
2. **Routing quality:** Does learned allocation outperform random, domain-based, simple-rule and two-model allocation at comparable expected budgets, and are predicted outcomes and costs calibrated?
3. **Complementarity:** How do the attainable frontier and the selected model mix vary with frontend/backend work, programming language, browser interaction, portfolio size and price sensitivity?
4. **Switching granularity:** When do task-level selection, phase-level handoff or per-call switching provide the best tradeoff after accounting for context replay, cache validity, model loading and handoff failures?
5. **Customer adaptation:** Which small models, if any, justify per-customer adapters or full-model adaptation, and how much improvement comes from changed model capability versus router recalibration?
6. **Continual selection:** Can a versioned admission and recalibration process incorporate new model releases without losing calibration, leaking test data or consuming more resources than the resulting savings justify?

The ensemble methodology defines one confirmatory comparison and a restricted statistical claim. Browser transfer, wider portfolio sweeps, switching and customer adaptation are prespecified extensions unless separately funded and registered. This separation keeps the central thesis answerable while retaining the broader product direction.

## Intended contribution and the frontier objective

The thesis does not claim to invent model routing, calibration, parameter-efficient adaptation or agent harnesses. Its intended contribution is a controlled study of their interaction across task domains, with a reproducible per-task economic account and explicit operational costs. Existing libraries supply the agent loops, browser interaction, model transport, inference and training. New code is limited to the research-specific routing, integration and evidence record where maintained tools do not provide them.

The combined capability of a model pool is an attractive upper bound, not a promised deployed frontier. An outcome-informed oracle can choose a successful model after seeing every candidate's outcome; a real router must choose before observing that outcome. Correlated failures, prediction error, insufficient training data and the cost of acquiring routing features can leave a substantial gap. Even the oracle only characterizes the finite evaluated pool and task distribution, not every available open model or every future release.

A useful result could therefore be positive, negative or qualified. Extra models might improve one language but provide no benefit elsewhere. A domain lookup might match an expensive learned router. State handoff might erase the gains from finer-grained selection. A customer adapter might improve its target workload while damaging other tasks or never amortizing its training cost. The protocol is designed to expose these possibilities rather than select only favorable demonstrations.

The repository already contains a historical coding-problem replay, data validation, teacher-example preparation and a training/inference scaffold. These do not establish the performance of the proposed portfolio, browser agent or latest checkpoints. New integration and empirical execution remain necessary. The approved single-80-GB-GPU, US$100 Runpod allocation supports bounded feasibility work; it does not imply that the expanded confirmatory study or additional paid APIs have been funded.

## Organization

The foundations chapter reviews routing, calibration, speculative inference, distillation and agent evaluation. System design defines the model portfolio and decision interface. The dated model landscape and historical accuracy evidence motivate candidate selection, while the task-economics chapter separates published task costs from hypothetical price scenarios. Browser evaluation and customer adaptation receive dedicated chapters. The ensemble protocol controls the expanded experiment, and the software-engineering chapter retains detailed benchmark procedures and the restricted two-model pilot. The analysis plan and reproducibility chapter specify reporting, limitations and completion criteria. Empirical results and result-dependent conclusions are reserved for later completion.
