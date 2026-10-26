# Project preferences

- Prefer existing open-source software and maintained integrations over custom tooling.
- Paid managed tools are welcome, including tools with a free tier, when they reduce implementation and operational work.
- Before building a component, evaluate existing software for the requirement. Build only the missing product-specific behavior, and explain why existing options do not suffice.
- Verify current pricing, free-tier limits, licenses and maintenance status rather than assuming them.
- Product direction: a Claude-like assistant using specialist model portfolios, with an optional free local Qwen tier, small and large remote models, and progressive improvement through verified distillation and potentially AI-feedback training. Persistent agents are a later extension.
- The user's most important guiding sentiment: "Believe in me who believes in you."
- Research confidence-aware inference and speculative decoding as inspiration for routing; distinguish token-level acceptance from calibrated task-level success prediction.
- Expanded research direction: route among a changing portfolio of specialist open-weight models across software engineering and browser tasks, including frontend/backend, programming-language and task-type differences. Do not constrain the product to one small and one large model or equate small with local.
- Optimize expected task success against full per-task cost, latency and customer price sensitivity. Evaluate task-level selection before frequent switching, accounting for state handoff, model loading and KV-cache recomputation.
- Customer adaptation may use a separate compatible adapter per base model, or an adapted model deployed on a desktop. Do not assume arbitrary LoRA adapters transfer across different base models.
- Current paper title: "We have to combine — A conversation is all you need." Subtitle: "Using small language models as conversational routers for agentic software engineering." The combined model frontier remains a research objective, not an established result.

- Central mission: democratize AI by turning the open-source model ecosystem into an affordable, user-controlled personal agent. The small personal model should learn from verified use and collaborate deeply with larger external models, including planning, delegation, context selection, verification and integration. Routing alone is an enabling component.
- Evaluate both increasing independent local capability and improved collaboration with experts over repeated usage/distillation rounds. Reduced large-model use is valuable only when quality is retained; collaboration may also improve while expert use remains necessary.
- Keep durable user memory and preferences distinct from model weights. Compare cooperative systems with large-model controls given the same personal context; do not attribute a memory advantage to cooperation.

- Current experimental focus: continuing bidirectional SLM/expert conversations (clarification, challenge, revision and integration), with substantial total-cost savings and minimal performance loss as the hypothesis. The four personal-agent capabilities are optional extensions. Classical distillation is prior work, not the claimed novelty.
- Read docs/paper/README.md and ADR 0006 before older proposed study hierarchies. Router-R1, EdgeWise and related work overlap strongly; frame the contribution as replication and controlled extension.
- Preserve the frozen Codex pilot, including failed submissions and artifact-policy flags. All four optional controllers used zero expert turns; the separate required-dialogue check is a mechanism test, not evidence of economic benefit. Unknown usage and billing remain null.

- Codex can meter usage with supported ChatGPT subscription login; separate API billing is not required. Read docs/research/codex-metering.md. Distinguish token counts, backend-estimated credits/USD, API-equivalent cost and subscription cash expense. Current CLI completion counters are cumulative by thread; use validated deltas or response deduplication. Do not infer zero inference from missing logs or upstream all-zero defaults.

- Continuation entry point: docs/research/HANDOVER.md and ADR 0007. The active research branch is `work`; `main` does not contain the latest experiment. User authorization to commit and push persists.
- The 500-task SWE-bench Verified replay is complete: historical published outcomes/costs for ten models, five-fold routing. Primary estimated inference saving 46.1% accompanies an 8.6-point quality loss; the joint target fails. A cheap strong standalone MiniMax control is crucial. Do not describe these records as new conversational model trials, current quotes or Codex quota savings.
- Six Codex conditions now exist: small, large, precall_router, oneway, reset_expert, personal. New ablations are software-tested, not live benchmark results. The 12-task official benchmark panel is frozen; only two evaluator environments were checked, one valid. Native metering still fails before inference due read-only state. Finish worker dependency/isolation and all controls on the next writable host before scored runs.
