# Observatory router: native Codex comparison contracts

18 November 2026. Proposed implementation contracts, not completed adapters or
scored results. The user selected our own router; RSI is related work only.
See [the study](knowledge-accumulation-codex-study.md) and
[protocol 004](../../experiments/model-led-delegation-001/protocol-004.json).

## Required comparison

| ID | System | Selection mechanism |
| --- | --- | --- |
| `luna` | Native Luna-only | Luna performs the whole coding episode |
| `sol` | Native Sol-only | Sol performs the whole coding episode |
| `frugalgpt_native` | FrugalGPT adapted to coding episodes | Learned candidate-quality scorers and a development-selected cost-aware cascade |
| `routellm_native` | RouteLLM adapted to native execution | Frozen released router variant selects the executor from the public task input |
| `observatory` | Our model-led experience router | Subtask delegation informed by applicable verified workflows, cheaper-model outcomes, similarity and recency |

Random mixtures, public-check fallback and static subtask mappings are additional
simple controls. Released SkillOrchestra is optional. Neither optional methods
nor simple controls replace the two required named router baselines.

## FrugalGPT

Source: [stanford-futuredata/FrugalGPT](https://github.com/stanford-futuredata/FrugalGPT).
Repository metadata reports Apache-2.0, not archived, last push 10 February 2025.
The README provides notebooks and published model generations; those are not
Luna/Sol coding-agent observations. Inspection is not an execution clearance.

Preserve learned quality scoring and cost-aware cascade selection. The adapter
defines a bounded coding candidate as the answer, derives scorer inputs only
from the public request and retained candidate/public trace, and obtains training
labels from the disjoint construction/development episodes. Exact source
components, scorer features/model, objective and threshold selection must be
documented and frozen before test. Do not invent a confidence threshold from
held-out outcomes or replace the scorer with hidden test access.

At deployment, scorer inputs exclude official grades and hidden test/patch data.
Any Sol continuation/restart policy, candidate checkpoint, budget allocation and
code passed between stages must be explicit. All stages share total episode caps.
Charge unsuccessful candidates, scorer calls/training and Sol execution. A single
Sol fallback on public test failure alone is the separate `public_check_cascade`
control, not an implementation of FrugalGPT's learned cascade.

## RouteLLM

Source: [lm-sys/RouteLLM](https://github.com/lm-sys/RouteLLM).
Repository metadata reports Apache-2.0, not archived, last push 10 August 2024.
Freeze an actual released variant and identify any changes. The default matrix
factorization route uses embeddings and pretrained model identities; changing its
executor names alone does not establish Luna/Sol calibration.

Use disjoint Luna/Sol development observations for pair-specific fitting and
threshold selection. Predeclare low-cost, balanced and quality-oriented points
from development. Runtime chooses a native executor and lets that agent complete
the task using the common harness and permitted knowledge. Subtask-level reuse
would be an additional adaptation, separately named.

The README's default MF and similarity-ranking paths require an OpenAI API key
for embeddings. Do not use that path under the source-subscription-only rule.
A reviewed compatible local encoder or another released variant needs explicit
qualification; changing the encoder is a documented adaptation. No API-key
workaround, external generative scorer or unrelated model fallback is allowed.
Keep upstream selection code reusable while replacing provider invocation with
the existing native Codex transport; no need to deploy the upstream API server.

## Fairness and evidence

All executors use the same qualified Luna/Sol identities, source subscription,
public checks, benchmark versions, pristine controls and total resource caps.
Every family receives the same eligible knowledge access. Generic retrieval for
standalone/baseline agents must not secretly use our routing decision. Keep
baseline-specific learned parameters distinct from runtime workflow packets.
Describe the primary results as native-Codex adaptations; do not compare against
published numbers from other model pairs as if they were matched controls.

Native account/actor/integration qualification, dependency review, exact source
pins, pair-specific training sufficiency and the expanded campaign budget remain
unresolved. Twelve construction and twelve development tasks are only a proposed
pilot and may be insufficient to train reliable learned comparators. Diagnose
that on development; revise/freeze the allocation before any held-out launch.
Do not report superiority to undertrained, incompatible or unrun baselines.

Measure official success, cost at matched quality, quality at matched cost,
latency, cache behavior and amortized construction/training. Include the endpoint
mixture envelope and paired uncertainty. A positive result extends only the
observed frontier for the registered systems/tasks. Code availability or an
independent implementation alone does not establish algorithmic novelty.

No baseline dependency was installed or executed for this source review. Resolve
and review exact upstream commits and their dependency graphs before execution;
the README installation commands are not an approved setup script.
