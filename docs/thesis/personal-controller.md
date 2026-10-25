# The personal model as a cooperative controller

## A personal agent that can use stronger expertise

The intended system gives the user a persistent personal agent, with a small model operating near their data and tools. That model can maintain the task contract, consult personal context, perform routine actions, ask stronger models for bounded assistance, and integrate the resulting artifacts. Its usefulness need not depend on reproducing every capability of a much larger model. It can improve the overall system by choosing useful questions, supplying relevant context, preserving user constraints and testing proposed work.

This extends whole-task routing into **cooperative control**. A router chooses which configuration should attempt a task; a controller can decide what assistance is needed during the task and how to use it. The scientific question is whether this additional coordination produces better accepted outcomes within a declared resource budget. The small model may instead become a bottleneck through poor decomposition, inadequate context or mistaken rejection of a correct expert answer. Cooperation is therefore an intervention to evaluate, not a guaranteed consequence of adding models.

The democratization objective has two complementary outcomes. The personal model may solve more work independently, and it may become more effective at obtaining and using outside expertise. A user could receive better results from the same expert budget even if the number of large-model calls does not decrease. Both outcomes matter; increased local traffic alone does not establish improved capability or user benefit.

## Foundations and an existing memory layer

ReAct establishes a useful interaction pattern in which an agent alternates model decisions with actions and environmental observations [@yao2023react]. Its evidence concerns the evaluated prompting and decision-making tasks, not small personalized coding controllers. HuggingGPT explicitly organizes a language-model controller around task planning, model selection, execution and response integration [@shen2023hugginggpt]. Its stated limitations include dependence on the controller's planning capability, multiple-call latency and unstable instruction following. These limitations directly motivate a controller-bottleneck control in this study.

MemGPT separates information in the active prompt from external persistent memory and uses function calls to move information between them [@packer2024memgpt]. That separation is valuable here: a user's current project, explicit preferences, previous decisions and unfinished work should remain inspectable state rather than requiring a weight update whenever a fact changes. The paper's conversation and document-analysis experiments do not establish that memory management alone improves repository repair.

Current software must be distinguished from those papers. The inspected Letta migration README states that its older V1 API server is retired on an archive branch and points active development to **Letta Code**. The pinned Apache-2.0 Letta Code repository documents Git-backed memory blocks, local and cloud agent-state backends, provider configuration and model switching [@ttgllettacode2026]. This is a maintained integration candidate to evaluate before creating a new memory subsystem. A local state backend does not prove local model inference, and the documented shared-memory repositories can be cloud-hosted. The selected runtime must demonstrate the required storage location, model interface and retrieval behavior; the old Python API is not assumed to be the current integration path.

The minimum research implementation should retain the common mini-SWE-agent or browser harness and add a bounded expert-call interface. A compatible existing memory layer supplies versioned personal context. Existing model transport, routing and training libraries supply the other components. Adopting an entire alternative agent product for only one condition would obscure which part of the system caused an improvement.

## Responsibilities and the cooperation loop

The proposed division of responsibilities is explicit:

| Component | Responsibility | Observable artifact |
| -------------------------- | ------------------------------------- | ----------------------------------- |
| Personal state store | Goals, explicit preferences, project facts, decisions and pending work | Versioned records with provenance and correction history |
| Small controller | Interpret the task, select context, act, request assistance and integrate work | Task contract, tool actions, expert requests and final artifact |
| Larger expert | Solve a bounded subproblem, propose a plan, generate a patch or review evidence | Typed answer, patch, plan or critique with stated assumptions |
| Harness and verifier | Enforce execution limits, preserve state and run permitted checks | Tool outputs, resource ledger and independent evaluation |
| Learning pipeline | Convert eligible experience into training and calibration data | Base-specific datasets, adapters and evaluation manifests |

The loop begins with a task contract: the requested outcome, relevant user constraints, permitted tools, completion checks and spending limit. The controller retrieves only the context relevant to that contract, then chooses a local action or an expert request. For example, it may inspect a failing test locally, ask an expert for a candidate cause or patch, execute the proposed change, and compare its behavior with the contract. The result returned to the user is the checked artifact and a concise explanation appropriate to that user.

An expert request contains a concrete objective, relevant files or observations, interfaces, visible failures, required output format, constraints and remaining budget. A request can ask for competing explanations or a testable plan without asking the provider to reveal hidden internal reasoning. The controller learns from observable actions, outputs and consequences. Expert answers remain proposals until the harness applies them and the relevant checks run.

The expert can assist planning as well as implementation. If the small controller cannot construct a useful decomposition, it can request a bounded plan and execute its steps locally. A declared failure trigger can transfer the complete remaining attempt to a stronger model. Tool completion, workspace snapshots, browser state and remaining limits must be preserved at that boundary. The small model's role as personal interface does not require it to approve every technical conclusion unaided.

A local controller is also not an automatic privacy boundary. An expert request transmits whatever context it includes. Data-release rules are enforced by the application, independently of a model's claim that a summary is safe. Private memory is not sent by default, and removal of decisive context can reduce expert performance. The study measures that tradeoff separately from the equal-context scientific comparison.

## Which forms of cooperation to test

The first design is a **small controller with a strong expert tool**. The controller retains goals and task state while issuing bounded expert requests. This is the closest implementation of a personal model that learns how to use a larger model. Initially, one frozen expert is sufficient to test the mechanism; multiple specialist experts extend the portfolio after the interface and cost accounting work.

The reverse arrangement is a necessary alternative: a **large planner with a small executor**. The larger model develops a plan, while the small model performs constrained tool steps, checks progress and returns exceptions. This can help when planning is the small model's limiting capability. It may incur more expensive planning or repair calls, and the plan can become stale as the environment changes. Its performance cannot be inferred from either model's standalone score.

A third arrangement uses **bounded review and revision**. The small controller produces or integrates a candidate, obtains a targeted expert critique when a registered trigger fires, and revises against executable evidence. Critique is fallible; agreement between models is not an independent correctness proof. The protocol limits review rounds, logs disagreement and provides an explicit fallback rather than allowing endless debate. Routine tasks need not pay for review merely because the system has two models.

Direct fusion of hidden states, cross-model attention or arbitrary KV-cache transfer is outside the first implementation. Such methods couple architectures and serving stacks and require their own training and compatibility study. Structured task state and artifacts are sufficient for the initial cooperative architecture. Within-base adapter techniques can later provide more efficient specialization, subject to the cache boundaries already specified in the adaptation chapter.

## Personal state and learned behavior

Personalization has several timescales. Immediate facts, explicit corrections and active project state belong in editable memory or retrieval. Stable conventions and recurring skills may justify a compatible customer adapter after enough authorized examples accumulate. Core permissions and spending caps belong in deterministic application configuration. Treating all three as model weights would make correction, inspection and deletion harder and would blur what an experiment changed.

The controller's training targets can include deciding when to ask for help, describing the subproblem, selecting useful context, following a plan, using tools, detecting a failed check, incorporating an expert patch and producing a user-appropriate final artifact. These are collaboration skills, distinct from copying a teacher's final answer. Examples should preserve the actual request, permitted observation, action, expert response and verification outcome. Tool observations serve as context rather than targets that the student is rewarded for inventing.

A successful final task does not prove that every delegation or intermediate action was necessary. Credit assignment therefore requires ablations or additional supervision: compare alternative requests on development tasks, label unsupported assumptions, preserve unsuccessful attempts, and record the cost of obtaining better demonstrations. Teacher-produced plans should not become “correct” labels solely because a larger model wrote them. Preferences expressed in outputs must also agree with the explicit user contract.

The separate longitudinal study tests whether the student gains standalone capability, collaboration skill or both. It freezes the acquisition process for its causal comparison and distinguishes generator training from router recalibration and memory changes. A system can benefit from improved context selection without compressing the expert's full knowledge into the student. Conversely, an improved student can be underused by a stale controller or can become overconfident about its new abilities.

## A controlled collaboration experiment

The first cooperation study uses the same study-unadapted small checkpoint $S_0$ wherever a small model appears. No customer-specific or study-trajectory adapter is unique to the cooperative arm. It freezes all model weights, personal-memory snapshots, expert configurations and policy rules; trained personal controllers belong to Study 2 or a separately named adaptation arm. It collects no training updates during test execution. Its core arms are:

| Arm | Controller and assistance | Purpose |
| ---------------- | ----------------------------------------------- | ----------------------------------------- |
| S | Small model with tools and personal context | Personal local-agent capability |
| B | Strong model with the same tools and personal context | Main strong-agent comparator |
| F | Frozen whole-task selector between S and B | Benefit of selection without cooperation |
| C | Small controller with the same strong model as an expert tool | Main cooperation intervention |
| R | Strong planner with small executor | Secondary test of controller-role choice |

Every arm receives the same initial task state, shared personal-memory snapshot, initial retrieval results, available memory/tool interfaces and registered spending, wall-time and action caps. The small controller may adaptively select which parts of that context to send to its expert; that is part of the intervention and its acquisition and transmission costs are counted. B is not deprived of the user's preferences to manufacture an apparent advantage for C. For this equal-context comparison, profiles must be public, synthetic or explicitly shareable with both model configurations. A privacy-constrained deployment is a separate condition with its changed information boundary disclosed.

The primary endpoint is **accepted task success**: benchmark resolution together with all prespecified, objectively testable mandatory user constraints. Constraint fixtures are set before model outcomes and checked for feasibility under the task's acceptance procedure; tasks without added constraints reduce to the standard resolution endpoint. Functional resolution and constraint adherence are also reported separately. Subjective style or helpfulness is a secondary blinded human-rating outcome and cannot silently change the binary primary label.

The single confirmatory comparison is C versus B. Let $A_C$ and $A_B$ be their accepted-task success probabilities under the frozen resource caps. The superiority claim requires a paired one-sided 95% lower confidence bound for $A_C-A_B$ above zero. The task/repository dependence scheme and repeated-attempt aggregation follow the software-engineering analysis plan. A power assessment based on development data precedes the final run. Failure to establish superiority is not retrospectively converted into a different noninferiority-plus-cost success criterion.

Identical caps do not imply identical realized expenditure. Actual dollars per assigned task, dollars per success, latency and resource use are reported alongside the primary contrast. If C succeeds more often while spending more within the cap, the supported result is greater success under that allowed budget, not economic dominance or an automatic reduction in user cost. Matched-spend curves, other caps, role reversals and additional experts are prespecified exploratory comparisons unless separately registered. The multi-expert extension also retains F and per-domain fixed choices, so model diversity is not mistaken for evidence about cooperative control.

## Failure analysis and implementation scope

Diagnostics identify failures in task interpretation, memory retrieval, decomposition, expert selection, request context, expert output, verification and integration. This makes a small-controller bottleneck visible. Useful measures include expert requests per attempt, requests that lead to a successful correction, rejected correct proposals, accepted incorrect proposals, repeated work, state-handoff failures, constraint violations and time spent waiting for experts. No single model-agreement or verbal-confidence score substitutes for these outcomes.

The minimum useful implementation is one local-capable controller, one expert endpoint, versioned personal context, the existing coding harness, typed expert requests, complete cost traces and independent grading. Browser interaction and several experts reuse the same contract only after domain compatibility is demonstrated. Learning is then added as a separate intervention. This sequence tests whether cooperation helps before attributing improvements to adaptation, and whether adaptation improves the partnership before claiming that the small model can eventually replace most external work. All of these outcomes remain unmeasured.
