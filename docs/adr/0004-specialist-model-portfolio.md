# ADR 0004: Cost-aware specialist model portfolios

Date: 2026-10-25  
Status: Accepted research direction; empirical validation pending  
Scope: Extends ADRs 0002 and 0003 beyond a fixed small/local and large/remote pair.

## Context

The product should choose among complementary models for software engineering and browser interaction. Model strengths can depend on frontend/backend work, programming language, modality and task type. Small models may run locally or remotely. Customers differ in price sensitivity, privacy constraints, hardware and adaptation needs. Token prices alone do not measure the cost of completed work.

## Decision

Use a versioned portfolio of eligible model configurations. A configuration identifies the base revision, compatible customer adapter where used, runtime, precision, inference settings and endpoint. Select by predicted task success, full task cost and latency under customer constraints. Treat pool membership, model sizes and the number of adapted small models as development-selected experimental variables.

Start with one model choice per complete agent attempt. Compare phase-level and per-call switching only through actual continuation experiments that charge loading, prefill, summaries, state transfer and failed work. Preserve the agent workspace or browser session independently of any model's KV cache. Do not assume caches or ordinary LoRA weights are transferable between different bases.

Keep customer training data and adapter metadata in a common pipeline, with a separate compatible artifact per chosen base revision. Evaluate one small adapted model before maintaining several; add another only when held-out complementarity and lifecycle economics justify it. Full-model adaptation may be trained on suitable infrastructure and deployed to a desktop. Training on the device is a separate hardware feasibility question.

Reuse mini-SWE-agent for the software-engineering case and evaluate AgentLab/BrowserGym for browser tasks. Prefer existing model APIs, local runtimes, PEFT/TRL and multi-adapter serving support over custom serving infrastructure. Implement only the missing portfolio policy, cost recording and experiment integration.

Report dollars per assigned task, dollars per successful task, success rate and latency together. Historical benchmark costs and hypothetical token scenarios remain separate from new TTGL measurements. Open weights, zero API bill and zero economic cost are different concepts.

## Evaluation and update policy

The controlling thesis protocol compares one frozen K-model portfolio with a strong fixed reference chosen on development data, using a common within-domain harness. Domain lookup, random allocation, restricted two-model routing and an outcome-informed oracle provide context. Software engineering is the primary domain; browser interaction is a separate transfer study. Frontend and language claims require datasets that actually cover those strata.

New releases pass licensing, interface, resource and development-performance checks before admission to a new portfolio epoch. Router retraining/recalibration, generator adaptation and pool changes are evaluated separately. Neither public leaderboard ranking nor final-test performance is used to silently update an ongoing condition.

The combined capability of all evaluated models is diagnostic headroom, not a guaranteed achievable frontier. The US$100 Runpod allocation remains a bounded feasibility budget for one 80 GB GPU. It does not expand automatically with this research scope.

## Consequences

The product can adapt to new specialists without being tied to one model pair. The experiment must account for greater label-acquisition cost, customer adapter proliferation, memory residency and distribution shift. Keeping a bounded eligible pool and beginning with task-level selection makes those costs measurable before fine-grained coordination is attempted.

See the [thesis sources](../thesis/README.md), [ensemble protocol](../thesis/ensemble-methodology.md), [task economics](../thesis/task-economics.md), [browser study](../thesis/browser-domain.md), and [adaptation and switching](../thesis/adaptation-and-switching.md).
