# ADR 0006: Test conversational routing as a replication and extension

Date: 26 October 2026 (Europe/Amsterdam)

Status: Accepted research direction; empirical benefits remain hypotheses.

Supersedes the prioritization, not the historical results, of ADRs 0003–0005.

The latest literature overlaps strongly with the proposed system. Router-R1
already interleaves reasoning, expert calls and synthesis, and learns routing.
EdgeWise already studies a small primary actor, selective cloud delegation and
reinforcement learning on software-engineering tasks. Personal memory and
learning from agent experience also have substantial prior art. Ordinary
distillation, routing and hierarchical delegation are not our novelty claims.

The active contribution is an empirical replication and extension: test whether
continuing bidirectional conversation, selective context sharing and verification
improve a compact acting agent's cost–quality tradeoff, after matching the
information, tools and budgets given to single-model and routing baselines.
Negative or null results answer this question. Architectural novelty is not a
prerequisite for a useful master's-level empirical thesis.

Reuse Codex for model/tool execution. Add only experiment records, controlled
expert handoffs, memory boundaries and independent evaluation. The first live
pilot uses the available Luna and Sol agents. These are opaque hosted model
labels; the experiment cannot establish parameter count, local deployability or
open-weight performance. Astra and open-model replications are separate named
conditions. No ordinary teacher/student training run is required for this pilot.

The four capabilities are optional personal-agent extensions:

1. Editable, versioned user goals, project history and preferences.
2. Local action and bounded consultation with stronger experts when useful.
3. Executable verification and integration by the personal agent.
4. Learning reusable collaboration skills from development experience, separately
   from edits to factual memory. Weight adaptation is optional and must use an
   existing trainer with a separately validated reward and held-out evaluation.

Use a task-only prompt router as an honestly named executable baseline. Do not
call it RouteLLM, Router-R1 or EdgeWise, or transplant another model pair's router
calibration without validation. Native prior-work replications require released
code/checkpoints, compatible licenses, a fixed evaluator and a costed run plan.

Record unknown token usage and dollar costs as null. A count of expert calls is
a mechanism measurement, not a cost estimate. Preserve the previous replay and
training utilities as independent historical work. The authorized US$100 Runpod
allocation remains unspent and is not necessary for the Codex pilot.

Persistent many-to-many collaboration is a later extension. Test the dyadic
personal-agent mechanism first, then compare communication topologies and learned
roles under equal total resource caps. Slack and MCP are integration choices,
not scientific evidence of improved cooperation.

The current paper and executable study are linked from [the paper index](../paper/README.md).
The previous thesis is retained as a broader pre-results design and literature
supplement; it does not override this decision or supply missing model results.

Latest title: **We have to combine — A conversation is all you need.** Subtitle:
**Using small language models as conversational routers for agentic software engineering.**
The principal hypothesis is substantial full-cost savings with a small registered
performance-loss tolerance. Test persistent expert dialogue against one-way
assistance, reset expert sessions, single models and pre-call routing.
