> Supporting design only. See [the current paper](../paper/README.md) for the active protocol and results.

# Optional extension: a personal manager of remote agents

## Research object and scope change

This optional future intervention is a compact personal agent that discovers, converses with and coordinates remote agent services. A remote agent can maintain its own task state, run tools, ask clarification questions and return artifacts over several exchanges. It is therefore identified by its service revision, underlying model configuration, harness, tool permissions, runtime, state policy and communication contract. A checkpoint name alone does not define this treatment.

This design is a separate future ablation and does not replace the active conversational-routing paper or its frozen pilot. Its central question is whether a small personal manager can coordinate the **same remote team** with acceptable quality and lower total cost than a larger manager. Distillation is optional future work; neither manager changes weights during this experiment.

## A bounded, shared remote team

The initial registry contains three distinct services: a coding agent, a browser agent and a review/verification agent. Their roles describe available actions, not proven superiority or different model families. The review agent may inspect evidence and propose checks, but final benchmark grading remains independent. A software-engineering task need not invoke the browser service merely because it is available. The same services, versions, observation contracts and tool permissions are available to all managerial conditions.

Registry records describe supported tasks, input/output modes, authentication requirements, endpoint, service revision, availability timestamp, concurrency limits and the method for obtaining a cost estimate. A description is a claim to validate on development tasks. Availability and a price estimate are observations with a lifetime, not permanent properties of a model. A registry refresh can change eligibility during a task under a frozen rule, but must not silently introduce a more capable worker into only one condition.

The quality experiment starts from a trusted, frozen registry snapshot and a common scripted availability schedule. Dynamic admission of previously unseen services is a separate transfer experiment. Service identifiers are opaque within the model-visible catalog; comparable descriptions and capability-test evidence prevent a familiar provider name from substituting for demonstrated skill. Exact identities remain available in the research manifest. Catalog order is randomized under a paired schedule to expose positional preferences.

## Conditions and common resources

| Arm | Manager and work allocation | Interpretation |
| ---------------- | --------------------------------------------- | ----------------------------------------- |
| M-small | Frozen compact personal manager with the full shared team | Main personal-agent treatment |
| M-large | Frozen larger manager with the identical team | Main managerial reference |
| Workflow | Development-selected fixed workflow using the same team | Value of adaptive coordination |
| Delegate | Select one eligible remote agent for the whole task | Value of continued conversation and coordination |
| Local-only | Compact agent and its permitted local tools | Independent local capability |
| Direct-large | Larger agent operating directly through the task harness | Secondary product baseline with a different service architecture |

M-small and M-large receive identical initial task state, personal-memory snapshot, retrieval results, available memory interfaces, agent catalog, tool access and overall time, spending and action caps. Manager model, precision and runtime are fixed before testing. They may choose different workers and context packets; those choices are the intervention. Neither condition gets a unique customer adapter or extra private history. The fixed workflow and delegation rule are selected on development data, not on the final outcomes.

The overall budget includes manager inference, every remote agent's internal work, communication, environments, retries, verification and storage under the declared accounting boundary. A worker's tool calls or additional model calls do not disappear because its endpoint returns one message. Conversely, a service tariff that already includes inference is not charged again as hypothetical GPU rental. Per-worker limits and a global ledger constrain parallel work. Equal caps do not guarantee equal realized spending, so invoices or reconciled resource records remain necessary.

## Conversation and durable task state

The manager can ask for help, clarify a request, narrow its scope, answer a worker's question, inspect progress, request revision, cancel work or integrate a returned artifact. Natural language carries the task content. A structured envelope carries task and conversation identifiers, recipient, permitted scope, deadline, spending limit, artifact references and version. This allows a conversational answer to be associated with the correct delegated task without making prose such as “done” the sole completion signal.

The manager's durable record tracks the user's objective, each outstanding assignment, dependencies, messages, acknowledged status, returned artifact hashes and remaining budget. Workers can maintain their own state; a resumed task must identify the existing remote task rather than accidentally start a second one. Cancellation is a request whose acknowledgement and remaining resource charges must be observed. A local timeout alone does not prove that remote execution stopped.

Reuse maintained protocol SDKs and an existing checkpointed orchestration framework. LangGraph's pinned official README documents stateful orchestration, durable execution and memory as integration candidates; these are documentation claims, not a tested TTGL deployment.[^manager-langgraph] The application still needs correct task identity and idempotency around external side effects. A durable manager checkpoint cannot by itself guarantee exactly-once behavior in a remote agent. No new general message bus is required for the initial study.

## Primary claim and statistical boundary

The endpoint is accepted task success: the benchmark's functional completion criterion together with the prespecified feasible mandatory user constraints. Functional success and constraint adherence are also reported separately. The same constraints apply to both managerial arms. Subjective style and user satisfaction use separate blinded assessments and do not modify the binary endpoint after results are observed.

Let $A_s,A_b$ denote accepted-success probabilities for M-small and M-large, and $C_s,C_b$ their mean total cost per assigned task. The proposed confirmatory sequence first requires a lower one-sided 95% paired confidence bound for $A_s-A_b$ above $-0.05$. Conditional on that quality gate, an upper one-sided 95% bound for $C_s/C_b$ below one supports lower total cost. The five-percentage-point tolerance is a proposed engineering margin to accept before freezing; a smaller tolerance requires renewed power planning. All estimates remain visible if a gate fails.

The adequately funded study uses three attempts per task/condition, averages within task, and applies the repository-aware paired uncertainty scheme in the analysis plan. Browser replication uses its own task/site grouping. Success under the same cap without the cost gate does not establish savings. Lower manager-token expense without lower complete-system expense does not establish the primary economic claim. Other arms, budgets, memory variants and service pools are explanatory unless separately registered with a multiplicity plan.

## Diagnosing management quality

Beyond final success and dollars per assigned or successful task, measure delegated-task completion, clarification exchanges, time awaiting workers, duplicate assignments, stale-result acceptance, cancelled work that continued, artifact integration failures and factual support for the final synthesis. A polished summary unsupported by the returned artifacts is not successful coordination. Record manager reasoning-call expense separately from the workers' execution expense while retaining their sum in the main metric.

Context handling needs two observations: whether the manager supplied enough relevant information for the worker to act, and whether it disclosed fields outside the declared sharing policy. Controlled fixtures can include explicitly marked private fields and task-relevant facts, without using real secrets. Disclosure violations can be counted against that policy; the experiment does not claim to infer a universal minimum sufficient context from token volume alone. Missing-context failures and avoidable disclosure may trade off.

Ablations remove personal memory, prohibit clarification, replace synthesis with a fixed artifact presentation, or restrict the manager to one worker. Each changes one declared mechanism while holding the eligible team and resource account constant. Human-visible explanations and artifact links can be assessed separately from functional completion. A personal manager's advantage should be attributed to observed coordination mechanisms, not to extra tools or stronger workers available only to it.

## Transport reliability and execution boundary

Protocol reliability is tested separately using deterministic scripted workers. Inject duplicate deliveries, reordered updates, delayed replies, stale catalog entries, expired artifacts, lost acknowledgements and cancellation races. Verify task identity, budget accounting and whether side effects repeat. These tests establish application behavior under faults; they are not language-model accuracy results. The model-quality study uses a fixed transport profile, with a separate robustness condition if desired.

A Slack interface and a protocol-native interface can be compared only when the task meanings, worker capabilities and permission boundaries remain equivalent. Differences in notifications, delivery delay or human intervention are measured rather than attributed to a better manager. The initial implementation may simulate both with controlled endpoints before connecting live services. Discussing Slack as an interface does not authorize sending messages to any real workspace.

The minimum executable research system is one local-capable manager, a small trusted registry, the three fixed service wrappers, durable task state, structured conversation envelopes, a complete cost ledger and independent evaluation. All empirical outcomes remain unmeasured. The existing Runpod approval supports bounded feasibility work; it does not automatically fund the whole agent-service matrix or unrelated communication services.

[^manager-langgraph]: Official [LangGraph README](https://github.com/langchain-ai/langgraph/blob/a25bfafe4858d2a85bede09ba83f9a591d1f1133/README.md), revision `a25bfafe4858d2a85bede09ba83f9a591d1f1133`, inspected 25 October 2026. The source register `manager-experiment-sources.json` records the hash and narrower README-only review scope; no runtime integration was executed.
