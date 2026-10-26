# Personal agents communicating with remote agents

## Decision and research question

The proposed personal system is a small local manager that knows the user's goals, retrieves relevant personal memory, and collaborates with remote agents through natural-language messages. A remote agent is a service with its own tools, execution environment and task lifecycle; it may itself use several models. Selecting that service is therefore different from selecting a completion endpoint. The manager can ask a coding agent to implement a bounded change, ask a browser agent to gather evidence, and ask a reviewer to assess an artifact before integrating the results.

This changes the central question: **can a small personal manager coordinate capable external agents effectively enough to improve the user's quality–cost tradeoff?** Distillation becomes an optional subsequent way to improve the manager's collaboration skills. The initial experiment freezes weights and tests communication, task decomposition, context selection and verification. Neither successful message delivery nor fluent synthesis establishes successful collaboration.

The architecture decision is to reuse MCP for access to tools and resources, A2A for remote-agent task contracts where supported, and existing durable storage for memory and task state. An MCP adapter remains a practical interface for agents without A2A support. Slack is an optional human-visible interface. It is not required for agents to collaborate, and adding it does not establish permission to contact people or publish task information.

## Discover capabilities, then check the contract

Begin with a configured registry of three trusted agent services: coding, browser work and review. These are capabilities, not fixed model sizes. An entry records its operator, endpoint, supported protocol/version, authentication reference, allowed data classes, capabilities, availability checks and measured performance. Credentials remain outside model-visible metadata. The manager retrieves a short description of eligible services rather than being given every tool in the ecosystem.

A2A's Agent Card provides an existing self-description format, including interfaces, skills, media types, capabilities and authentication requirements. A known server can expose a card at `/.well-known/agent-card.json`; discovery can also use direct configuration or a registry. This does not imply a universal directory of agents, universal access, or free execution. A card's description is an advertised capability, not an independently measured success probability [@ttgla2acommunication2026].

The registry therefore separates provider claims from local observations and contractual limits. The inspected A2A 1.0 schema has no standard price or maximum-charge field. Price quotes, quote expiry, spend reservations and billing reconciliation are application contracts, represented in an agreed extension or separate service configuration. They must not be inferred from persuasive descriptions. A model can propose an eligible service; deterministic code checks identity, scopes, price validity and available budget before dispatch. Changing an agent's underlying model or toolset requires a new evaluation snapshot even if its public URL is unchanged.

## Protocol responsibilities and version boundaries

| Interface | Appropriate responsibility | What the application still supplies |
| --- | --- | --- |
| MCP | Discover and invoke tools; obtain resources and prompts; optionally expose agent operations | Personal memory policy, service selection, spending rules and supported asynchronous behavior |
| A2A | Agent Cards, messages, tasks, artifacts, status updates and supported streaming or push delivery | Task acceptance, pricing contract, data-release policy and operational reliability |
| Slack with Bolt | Visible task requests, clarification and progress in a workspace/thread | Authoritative task state, correlation, deduplication and access rules |

MCP's current reviewed specification is **2026-07-28**. Its changelog removes protocol-level HTTP sessions, adds `server/discover`, and makes requests self-contained with per-request version/capability information. Cross-call state uses explicit handles. Long-running tasks are an opt-in extension, `io.modelcontextprotocol/tasks`, with durable handles, polling, mid-flight input and cancellation. Older examples that depend on initialization sessions or earlier experimental task APIs cannot be copied unchanged [@ttglmcpcommunication2026]. The manager's durable conversation therefore belongs in the application, not in an assumed MCP transport session.

The MCP Python repository documents its v2 API and supports client/server integration. Its current examples and requirements must be pinned together with the selected protocol implementation; a dependency name alone does not establish compatibility [@ttglmcppythoncommunication2026]. For an agent exposed through MCP, negotiate the tasks extension if both sides implement it. Otherwise use a documented application tool contract such as submit/status/respond/cancel with explicit handles. Those tool names are a proposed adapter, not standard MCP methods.

The reviewed A2A specification identifies **1.0.0** as its latest release. It distinguishes messages from stateful tasks and resulting artifacts; supports polling, streaming and optional push updates; and defines interrupted states for additional input or authentication. Its Python SDK documents A2A 1.0 support and a compatibility mode for 0.3 across JSON-RPC, HTTP+JSON and gRPC [@ttgla2acommunication2026; @ttgla2apythoncommunication2026]. V1 should choose one binding, pin the SDK, request the registered version and test against each service. Supporting every transport or silently downgrading is unnecessary for the first experiment.

## Natural language inside an enforceable envelope

Natural language lets the manager explain intent, ask a specialist what information it needs, discuss alternatives and synthesize results. Machine-readable fields preserve the boundaries that conversation alone cannot enforce. The application envelope accompanies the protocol's own messages; it does not replace the A2A or MCP schema.

| Envelope content | Purpose |
| --- | --- |
| Local delegation ID, parent task ID, message ID and schema version | Correlation, durable replay and compatibility |
| Selected agent and remote task/context identifiers when assigned | Associate subsequent clarification and status with the correct remote work |
| Goal, relevant preferences and minimal supporting context | Communicate the intended outcome without exporting the whole personal history |
| Allowed actions, artifact destinations, deadline and bounded review rounds | Restrict execution and terminate unproductive loops |
| Accepted quote, remaining reservation and usage contract | Account for execution and further delegation |
| Required deliverables and executable acceptance checks | Distinguish a useful answer from an accepted result |

A coding request might say: “Repair this parser failure, preserve the public API, and return a patch with the failing test and validation output.” The manager supplies the relevant files and conventions. The coding agent can request a missing grammar fixture; the manager either retrieves an already authorized artifact or returns a precise question to the user. It does not automatically expose unrelated memories because the specialist requested them. A reviewer can then receive the patch and contract without receiving the entire original conversation.

Local IDs must not be confused with remote IDs. In A2A, the server creates a new task ID; a client-supplied `taskId` refers to an existing task. The manager persists the mapping to its local delegation ID, remote context and returned artifacts. Terminal tasks cannot simply be reopened by sending another message; revision may require a new task referring to the previous work [@ttgla2acommunication2026]. This distinction matters when replaying a durable workflow after a crash.

## Reliability, clarification and completion

Persist the intended dispatch and its budget reservation before sending it. For an asynchronous task response, record the returned handle before considering dispatch complete. A2A may instead return a direct Message: persist and validate that result without waiting for a nonexistent task ID. Use a durable outbox and a bounded retry policy. A2A explicitly makes message-send idempotency optional: a `messageId` alone does not guarantee exactly-once work. Require server-supported deduplication for retries that could repeat costly or external actions. After an ambiguous timeout, reconcile known state where possible; do not issue an unbounded second job merely because the first response was lost [@ttgla2acommunication2026].

The manager tracks submitted, working, awaiting input, awaiting authentication and terminal outcomes through the selected protocol adapter. Streaming improves progress visibility; polling remains a simple recovery mechanism when a supported stream disconnects. Protocol completion means the provider declared completion. Application acceptance follows only after checking the required artifacts and permitted validation. Keep these two events separate in the trace, including failed checks and rejected deliverables.

Clarification is a normal workflow event. The manager answers from authorized memory when sufficient, obtains a bounded specialist explanation when useful, or asks the user when a necessary decision remains unresolved. Authentication is handled by the application rather than by placing credentials in a conversation. Deadlines, attempt limits and spending reservations prevent endless agent discussion. Cancellation is best-effort operational control: the MCP task extension explicitly describes cooperative cancellation, and A2A can reject cancellation for a noncancelable task. Neither cancels an already completed external effect. Record residual cost and state before releasing a reservation.

## Memory and control stay with the user

Durable memory contains editable preferences, project facts, decisions and unresolved work with provenance, timestamps and correction history. It remains outside the small model's weights. Per-agent context selection creates a recorded projection of those records and relevant artifacts. The manager can personalize an instruction without disclosing the underlying private history; however, summarization is not proof that disclosure is safe or sufficient. Evaluate both unnecessary disclosure and failures caused by withholding necessary context.

The model proposes memory retrieval and communication; application policy enforces access. Tool descriptions, Agent Cards, returned documents and other agents' messages are data, not authority to enlarge permissions, contact another service or spend more money. A downstream agent receives only the scopes and budget explicitly granted for its job. Useful returned facts enter personal memory with their source and verification status. A confident specialist statement is not automatically a durable user preference or a verified project fact.

For coding, isolate parallel workers and integrate their patches against recorded repository revisions. For browser work, preserve permitted session ownership and action history. Sharing a task does not imply sharing mutable credentials or a browser session between independent workers. This also makes failures attributable: the record identifies which service saw which context, produced which artifact and performed which externally visible action.

## Slack as an optional interface

Slack Bolt already provides event subscriptions, scoped OAuth installation handling, message/thread helpers and HTTP signature verification. Its documentation instructs interactive handlers to acknowledge within three seconds and describes deferring longer work; the event listener path has different acknowledgement mechanics. A transport acknowledgement must therefore be separated from agent completion [@ttglslackcommunication2026].

If enabled, map workspace, channel and thread identifiers to the durable local task. Enqueue long work, publish only authorized progress, and ignore self-generated or unauthorized bot events. Agent replies must match a recognized task and permitted sender. HTTP callbacks should retain Bolt's signature/timestamp verification; Socket Mode uses a different authenticated transport. Deduplicate incoming deliveries and correlate responses using application task/message IDs. The current direct Events API documentation was inaccessible during this review, so no exact retry schedule or exactly-once delivery guarantee is claimed. Slack threads provide useful visibility, but cannot replace a durable task ledger or settle billing and acceptance.

## Reuse-first implementation and experiment

V1 uses one local small-model manager, an existing agent harness, existing durable checkpoint/memory storage, the official MCP and A2A SDKs, and three configured services. A SQLite-backed task/outbox ledger is sufficient for a single-user study if the existing runtime does not already supply equivalent persistence. Add only product-specific contracts, policy checks and adapters. Bolt is a later interface integration. No custom communication protocol, universal marketplace or training pipeline is necessary to test the central hypothesis.

Compare this manager with direct task-level selection and a larger manager using the same specialist services, tools, personal-context snapshot and total resource limits. A no-memory condition isolates personalization; a one-shot delegation condition isolates iterative clarification. Record task success and per-success cost alongside context volume, delegation count, clarification utility, rejected artifacts, duplicate execution, recovery failures and unauthorized-context attempts. Charge all manager, specialist, tool, retry and verification work, including unsuccessful tasks. A service's internal model need not be exposed to the manager, but its version and reproducible configuration must be recorded or its opacity reported as a limitation.

Fault-injection tests should cover lost acknowledgements, duplicate delivery, restart after dispatch, stale cards, unavailable agents, requests for excess context and budget exhaustion. These validate orchestration properties, not intelligence. The thesis's substantive result remains unmeasured until controlled agent runs show whether a small personal manager can achieve comparable quality with lower total cost, or better personalized outcomes at a fixed cost. Interoperability makes that experiment feasible; it does not establish the result.
