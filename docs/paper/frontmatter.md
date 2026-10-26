---
title: "We have to combine — A conversation is all you need"
subtitle: "Using small language models as conversational routers for agentic software engineering"
date: "26 October 2026 (Europe/Amsterdam)"
lang: en-GB
link-citations: true
toc-depth: 2
---

# Status and scope {.unnumbered}

This is a research paper and master's-thesis core, with a reproducible engineering
pilot, a completed 500-task SWE-bench Verified routing replay, and a prospective
confirmatory conversation protocol. Its central contribution is an
empirical replication and conversational-routing extension, **not a claim to have
invented small agents that consult larger models**. The broader earlier thesis
contains supporting reviews of open-model portfolios, prices, distillation,
browser benchmarks and deployment. Those materials do not change the active
protocol in this paper.

The empirical section distinguishes live model trials from software tests and
unexecuted experiments. An opaque hosted model called Luna is a practical
controller proxy, not evidence of a particular parameter count, open weights or
local-device feasibility. Sol is the pilot expert. User consent covers these
Codex agent experiments. The separately authorized one-80-GB-GPU Runpod budget
of US$100 has not been spent on this work.

Author, university, supervisor and submission declarations remain for the author
to complete. No institutional approval or model-training result is implied by
this manuscript. Historical estimated inference savings are reported separately
from unmeasured conversation benefits, current bills and subscription usage.

# Abstract {.unnumbered}

Can a small acting model reduce the total cost of agentic software engineering
by conversing with larger experts while retaining nearly the same task success?
The proposed mechanism is continuing, bounded dialogue: the controller works
locally, selects context, asks for assistance, answers clarification questions,
challenges proposals and integrates a verified result. This is broader than
initial model selection and more specific than an unconstrained agent swarm.
Learned routing, selective cloud delegation and multi-agent interaction already
have substantial prior art; this work is a replication and controlled extension.

We implement a thin experiment layer over Codex with persistent controller and
expert threads, bounded exchanges, independent grading and explicit missing-cost
handling. A live historical-bug pilot compares a single Luna agent, a single Sol
agent, task-only prompt routing and optional conversational assistance on four
issues from two repositories. Functional regression success is respectively
3/4, 4/4, 4/4 and 3/4. All optional controllers chose zero expert calls, so this
matrix does not estimate the value of an actual conversation. A separate required
two-round clarification-and-integration check passes its 30 regression tests.
Strict artifact-policy outcomes are reported separately because several workers
added assertions inside existing test files.

An additional experiment fits cross-validated pre-task routers on 5,000 published
agent outcomes: ten models on all 500 SWE-bench Verified tasks using mini-SWE-agent
2.0.0. The primary half-budget router achieves 64.2% success at US$0.2551 per task,
versus GPT-5.2's 72.8% at US$0.4736. Estimated inference cost falls 46.1%, but the
8.6-point quality loss fails the three-point tolerance. A ten-model portfolio
operating point reaches 76.2% at US$0.1154; inexpensive MiniMax-M2.5 alone reaches
75.8% at US$0.0733. The latter comparison prevents attributing the benefits of
model choice to routing. These historical outcome replays are not new model
inference or live conversations.

The confirmatory protocol compares conversation with single-model execution,
pre-call routing and one-way assistance under matched information and resource
budgets. The proposed gate combines a three-percentage-point quality tolerance
with lower measured total cost; a 25% saving is the practical target. Personal
memory, learned collaboration skills and multi-agent communication are optional
ablations and extensions. The pilot exposes no complete billing ledger and is
not powered for noninferiority. It therefore establishes execution feasibility,
not conversational cost savings, local-model capability or learning improvement.
The standard-benchmark replay supplies a reproducible negative primary result
and identifies a stronger low-cost standalone control for the next experiment.

**Keywords:** conversational routing; small language models; software-engineering
agents; bidirectional collaboration; cost–quality tradeoffs; replication.

# Motivation and research questions

The immediate research goal is a small acting controller that combines its own
work with outside expertise through conversation. A personal agent that remains
responsible to its user is one motivating application. A user should be able to inspect and
change what the agent remembers, retain control of project goals and decide
which information external services receive. The compact model need not solve
every problem independently. Its useful role can include understanding the
task, doing inexpensive work, asking a precise question, evaluating the answer
and incorporating a tested change.

These responsibilities are more demanding than choosing a model from an initial
prompt. They also create overhead and new failure modes. The controller may
misdiagnose a problem, omit crucial context, accept an incorrect suggestion or
spend more on coordination than direct expert execution. Personal memory may be
stale, irrelevant or less useful than a generic project guide. Learning can
reinforce a mistaken delegation habit. These possibilities motivate controlled
experiments rather than an assumption that a multi-model system is better.

The research questions are:

1. Can an acting small controller with bounded expert dialogue lower total cost
   while retaining accepted software-task success relative to a single expert
   given the same information, tools and resource envelope?
2. Does consultation after observing the repository and test feedback add value
   beyond a task-only router selecting one model before work begins?
3. Does persistent bidirectional dialogue add value beyond one-way assistance
   or reset expert calls under the same total budget? Which effects come from
   selective context sharing, verification or optional personal memory?
4. Can development experience improve the controller's decisions about when to
   ask, what to send and how to recover on later, disjoint tasks?
5. At which measured total-cost operating points is the resulting system useful,
   and which privacy, latency and local-access tradeoffs remain?

The core hypothesis is materially lower total cost with only a prespecified small
loss of task performance. Conversation may also improve performance, but that is
a separate claim. The first live pilot addresses feasibility and a restricted
version of the first two questions. The remaining questions require the registered ablations and
longitudinal data. A null finding is informative: if the same-context expert
remains better or the controller cannot exploit assistance, the proposed
complexity is not justified in that setting.

The project's guiding sentiment is “Believe in me who believes in you.” It is a
motivation for persistent investigation, not a substitute for falsifiable claims.
