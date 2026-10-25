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
- Working thesis title: "We Gotta Combine!" The combined model frontier is a research objective, not an established result.
