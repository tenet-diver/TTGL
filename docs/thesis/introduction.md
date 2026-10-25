# Introduction

## Motivation

The useful output of a software-engineering assistant is a correct and reviewable change to a software system. Generating plausible code is only one step toward that output. A repository task may require identifying an unfamiliar component, reproducing a failure, reading conventions, proposing a change, running tests and responding to intermediate evidence. These activities make the model, its tools and its execution environment a combined decision-making system. An evaluation that measures isolated answer quality does not fully characterize that system.

Current high-capability language models offer a convenient route to strong assistance through hosted APIs. However, their operating cost grows with repeated context processing, long trajectories, retries and concurrent use. A small local model changes the cost structure: the user may avoid an inference-service charge for individual calls, but still bears hardware, memory, energy and latency costs. The local model may also require more attempts or fail on tasks a stronger model could complete. A meaningful comparison must therefore consider the total cost of successful work rather than token prices alone.

TTGL proposes a local-first coding assistant that combines these resources. A local open-weight model performs work when the system expects it to be sufficient. A remote model is available when delegation is likely to improve the outcome enough to justify its cost. Customers may select an eligible remote model; the product selects an appropriate local model for the device. Verified remote outputs can later become training examples for local adaptation. This architecture creates an appealing hypothesis: the system could preserve much of a stronger model's useful capability while reducing paid inference and increasing local coverage over time. The hypothesis requires an experiment. Neither a router's existence nor a small model's high confidence establishes it.

## The research problem

The central question is how to allocate heterogeneous model capability to software-engineering work under cost and quality constraints. A simple “easy local, difficult remote” rule is incomplete. A task may be difficult for both models; remote execution then adds cost with little improvement. Conversely, the remote model may bring a predictable benefit on an apparently routine task where local behavior is unreliable. Some tasks may be solved by the local model and missed by the remote one. The relevant quantity is therefore conditional **benefit of delegation**, not difficulty or local uncertainty alone.

The problem also changes with the point of intervention. A router can choose a model before any generation, after a bounded local attempt, or at successive tool boundaries during an agent trajectory. These settings have different information and costs. A router that observes a failed test has already paid for local reasoning, editing and verification; a pre-call router has not. Treating both as if they selected one equally priced answer hides the economics and confounds experimental attribution.

Training the local model creates a second problem. Improvements in apparent local coverage can arise from a better student, a recalibrated router, a changed workload, altered verification rules or easier task selection. A thesis must distinguish these explanations. It must also separate sequence distillation from token-distribution distillation, and supervised adaptation from learning with AI-generated preference feedback. These methods require different evidence and different resources.

## Scope and terminology

In this manuscript, a **language model** is the generative model queried to produce text or structured actions. An **agent harness** manages the interaction between that model, repository state, tools and termination conditions. A **single-model agent** can invoke many tools and make many calls, but uses one model throughout its trajectory. A **dual-model system** uses a policy that can select between a local and a remote model. It may still use only one model on an individual task.

“Local” identifies an intended deployment on user-controlled hardware. “Remote” identifies an endpoint outside that device. An open-weight model can be served remotely, and a model with an open-source serving engine is not automatically an open-source model in the same licensing sense. The thesis uses **open-weight** when weights are available under a published license and **closed model** when the weights are unavailable to the researcher. Software licenses, weight licenses, API terms and training-data permissions are recorded separately.

The primary outcome concerns repository-level issue resolution, as assessed by a pinned execution-based benchmark. Isolated programming problems serve only as auxiliary diagnostics or development data with their own scope. The experiment does not equate passing benchmark tests with universal correctness, security, maintainability or acceptance by a human reviewer. These are separate dimensions that would need additional study.

## Research questions

The thesis organizes the empirical work around five questions:

1. **System effectiveness:** Can a dual-model agent retain issue-resolution accuracy within a prespecified tolerance of a strong single-model agent while reducing total inference and execution cost?
2. **Routing quality:** Does a learned, calibrated delegation policy outperform random and simple rules at comparable spending, and does predicted benefit outperform local-failure confidence alone?
3. **Operational tradeoff:** How do the attainable accuracy–cost frontier and latency distribution change across models, workload strata, local hardware profiles and deployment modes?
4. **Student improvement:** Does verified teacher-output distillation improve held-out local capability, and how much of any subsequent system improvement is attributable to the student rather than router recalibration?
5. **Market relevance:** How do eligible current open-weight and closed-model alternatives compare under the same experimental conditions, and how do dated published price/performance observations inform—but not replace—that evaluation?

The methodology chapter defines the primary contrasts and multiplicity rules. The questions are deliberately broader than the confirmatory hypotheses: exploratory diagnostic analyses are useful, but they cannot replace a failed or inconclusive primary comparison.

## Intended contribution

This thesis does not claim to invent model routing, confidence calibration or distillation. The intended contribution is a controlled evaluation of their interaction in software engineering. The study specifies a common harness, paired task evaluations, a router whose information is available at the time of decision, explicit uncertainty and calibration checks, and an accounting scheme that charges unsuccessful attempts and verification. A separate adaptation arm provides a way to test whether verified teacher data shifts the local model's frontier.

The accompanying research software already provides data validation, a historical routing-replay implementation, teacher-example preparation and a training/inference scaffold. The prospective repository-level adapter and controlled multi-model evaluation remain to be executed. Reusing established harnesses, inference runtimes and training libraries reduces engineering effort and improves comparability, while project-specific code is confined to routing policy, experiment integration and evidence recording.

The contribution is valuable whether the eventual result is positive, negative or uncertain. A dual-model system may be attractive only for particular task classes, hardware utilization or cost ratios. A simple rule may outperform a learned router under distribution shift. Distillation may improve one class of tasks while damaging another. The experiment is designed to make such outcomes observable instead of selecting only favorable cases.

## Organization

The next chapter reviews the conceptual foundations and related work. The system-design chapter defines state, decisions and learning mechanisms. A dated model-landscape chapter records candidate models, pricing evidence and the limits of published benchmark comparisons. The methodology specifies the controlled software-engineering evaluation, followed by a prespecified analysis and reporting plan. The final substantive chapter discusses reproducibility, ethics, threats to validity and the conditions required to complete the study. Results and result-dependent conclusions are reserved for later completion.
