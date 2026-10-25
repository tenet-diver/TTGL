# Introduction

## Motivation: personal capability from an open ecosystem

The motivating objective is to democratize AI: make useful assistance affordable, adaptable and controllable by the person using it. This requires more than a low token tariff. A personal agent should retain relevant preferences and work context, operate within the user's permissions, remain useful on accessible hardware, and preserve value when an external service is unavailable or replaced. These properties are research objectives, not claims that an existing small model already provides them to every user.

The open model ecosystem offers complementary sources of capability. Larger models and domain specialists can solve demanding problems, while compact models can provide responsive local behavior and potentially learn a person's recurring workflows. The proposed system combines them through a small personal controller. It can inspect a task, use local tools, request bounded help from eligible experts, check their outputs and integrate the result into the user's work. The personal model need not reproduce every expert's knowledge in its own parameters to benefit from that knowledge.

This makes **We Gotta Combine!** a hypothesis about cooperation and learning, not only model selection. Routing decides which expert is appropriate. The personal controller also decides what help to request, which context is necessary, how to assess an answer and how to continue after it arrives. A large model can advise on a plan as well as produce a patch, while the controller retains the task contract and personal context. If the controller's competence becomes the bottleneck, the system needs an explicit route to stronger planning or broader delegation.

Verified interactions can then become learning material. Some teach skills that the compact model can later perform independently; others teach it to collaborate more effectively. Both can improve the assistant. Fewer large-model calls is not by itself evidence of learning: the system could simply tolerate more failures or encounter easier tasks. Conversely, a controller that uses the same number of expert calls but solves substantially harder work may have improved. Independent capability, cooperative performance and external dependence must therefore be measured separately.

## The research problem

The first problem is whether a compact personal controller and larger experts can work better together than simpler systems with the same information and resources. Giving only the controller access to user preferences would create an unfair comparison. The large-model baseline must receive the same permitted memory, task contract, tool access and opportunity to retrieve relevant context. Any resulting advantage can then be investigated as an effect of decomposition, delegation, verification or integration rather than an information advantage hidden inside the architecture.

The second problem is how experience changes that relationship. A useful learning loop observes work, identifies trustworthy demonstrations, trains or adapts the student, recalibrates its decisions and evaluates the next version on untouched tasks. Training only on teacher answers ignores the control skills needed to obtain and use those answers. Training only on requests already escalated can also bias the data toward tasks that are too difficult for the small model. The study records the acquisition policy and verification yield, uses a controlled learning curriculum before closed-loop adaptation, and tests whether gains survive changes in task distribution.

A third problem is the cost of making personalization persistent. Current facts, user corrections and project state belong in editable memory, where they can be retrieved, updated and deleted. Repeated behavioral patterns may justify an adapter or full-model adaptation. A separate adapter for every model and user can become expensive to train and maintain, while full fine-tuning may exceed a desktop's memory. The experiment distinguishes memory, routing adaptation and changes to model weights; it does not assume that every personal detail should become a parameter update.

The surrounding expert pool is also a decision variable. Specialists may differ across frontend/backend coding, programming language, browser interaction and visual grounding. Small models can run remotely, and local hardware can support different sizes. Pool membership and execution location are chosen using development evidence and customer constraints. Newly released models enter a versioned evaluation process; the personal agent's identity and memory need not be replaced whenever its expert provider changes.

## Scope and terminology

A **personal controller** is a model-driven agent with access to a permitted user-state store, task state and bounded tools. The controller does not itself define security permissions: the harness enforces them. An **expert** is a model configuration invoked for a declared role such as plan advice, code generation, critique, visual interpretation or a bounded subtask. Its result returns through a recorded interface. A **portfolio router** selects eligible experts; it is one component of the controller rather than the complete cooperative system.

A **model configuration** identifies the checkpoint or service revision, tokenizer and template, precision, inference settings, runtime, endpoint and compatible adapter. A **learning round** produces a versioned student and policy from a declared cumulative development exposure. A **local-only completion** requires successful work with no external model assistance during the attempt, including remote planning, judging or embedding calls. Ordinary local tools and tests remain available. Past training on permitted teacher outputs does not make every future local attempt externally assisted.

“Open-weight” describes available weights under a published license. Source-code openness, redistribution rights, API output-training terms and inference location are recorded separately. A free local product tier does not eliminate energy, hardware or training cost. The mission of democratization is operationalized through capability, cost, memory requirements, offline operation, user control and portability. A benchmark study cannot demonstrate universal accessibility or broad social impact merely by improving one score.

Agentic software engineering is the main experimental setting. Functional resolution requires the pinned benchmark's execution checks. Study 1's accepted-task success additionally requires the prespecified feasible mandatory user constraints; both components are reported separately, with subjective personalization quality as a secondary outcome. Browser use is a transfer domain with its own environment and success definition. Frontend implementation, browser navigation and desktop operation are distinct workloads. A Python-heavy repository benchmark cannot establish performance across all languages or all forms of frontend work.

## Research questions

The thesis addresses six linked questions:

1. **Cooperative capability:** Does a small personal controller with external experts improve task outcomes or the quality–cost tradeoff compared with a large-model agent given the same personal context, and compared with flat routing?
2. **Learning from use:** Across fixed cumulative exposure rounds, which verified demonstrations improve independent student skills, and which improve delegation, context selection, verification and integration?
3. **Personal independence:** How much useful work can be completed locally at a maintained quality level, how does external-model burden change, and what hardware and lifecycle cost are required?
4. **Specialist complementarity:** When do additional experts, different model sizes and domain-specific choices improve the system enough to justify their acquisition and serving cost?
5. **Personalization mechanisms:** What is supplied by editable memory, router adaptation, per-base customer adapters or full fine-tuning, and how do those effects generalize to unseen tasks and users?
6. **Operational evolution:** How do handoff granularity, cache reuse, model release updates and workload shift affect the reliability and economics of the cooperative system?

The research program has an enabling portfolio study, a fixed-model cooperation study and a separate longitudinal learning study. Their contrasts and evidence requirements are named explicitly. Success in a routing baseline does not establish cooperative superiority; success after one fine-tune does not establish progressive independence over many rounds. Each confirmatory scope must be frozen and resourced before its final outcomes are observed.

## Intended contribution and limits

The contribution is the controlled evaluation of a personal agent that draws on open expertise while retaining and developing useful capability for its owner. Existing software supplies model serving, agent tools, memory interfaces, training and benchmarks. Custom work is confined to missing control, measurement and integration behavior. The experiment compares cooperation patterns and learning interventions without claiming to invent the underlying routing, memory or distillation methods.

The combined capability of all experts is an optimistic opportunity bound. A real controller can choose the wrong expert, omit decisive context, misunderstand a correct answer or fail to recognize an error. A small model may learn common workflows while retaining limits on novel reasoning or long-horizon planning. Increased usage may produce redundant or biased data rather than continual improvement. Negative transfer and plateaus are possible results, and the study must preserve them rather than select the best-looking checkpoint after testing.

The existing TTGL repository contains a historical coding-problem replay, data checks, teacher-example preparation and a training/inference scaffold. It does not yet supply measured evidence for this cooperative or longitudinal system. The approved US$100, single-80-GB Runpod allocation supports bounded feasibility work. A full controlled program, multiple adaptation rounds and device measurements require a costed execution plan and the necessary access; the manuscript does not claim that they have occurred.

## Organization

The foundations and agent-learning evidence chapters review the methods and their limits. System design and the personal-controller chapter specify cooperation, followed by the longitudinal learning protocol. The model catalog, historical accuracy and task-economics chapters supply dated context. Browser evaluation and adaptation/switching provide domain and deployment details. The portfolio study and repository procedures remain reusable controls. The analysis and reproducibility chapters define reporting and completion boundaries. Empirical results and result-dependent conclusions remain unwritten.
