# TTGL: Local-first coding app — product proposal and architecture decisions

**Status:** Proposed. **Primary sources reviewed:** 2026-10-25. **Intended location:** [FASTEST, Confluence](https://fastestswarm.atlassian.net/wiki/spaces/FASTEST).

> Believe in me who believes in you.

## Product decision

Build a Claude-like coding app that runs a small Qwen model locally for free, routes difficult work to the customer's selected paid remote model, and improves local capability using verified, authorized teacher outputs. Success means **more accepted work completed locally at a fixed quality threshold**, rather than simply fewer remote calls.

Use maintained open-source software and existing managed services wherever possible. Paid tools, including products with free tiers, are welcome when they reduce implementation and operational work. Build only missing product-specific behavior; verify pricing, licenses, free-tier limits and maintenance status before adoption.

This consolidates the proposed local-first product decision and confidence-aware routing research. It supersedes the earlier hosted-first direction. Remotely hosted and persistent agents remain a later extension.

## Customer workflow

1. Install an existing coding client and a hardware-appropriate Qwen checkpoint.
2. Work on a local repository using local inference, files, shell and tests.
3. Escalate difficult or stalled work to the selected remote model within a visible budget and data-sharing policy.
4. Apply the same local tool permissions to all model outputs; inspect diffs and execute relevant repository checks.
5. Save verified examples locally. Explicitly enrolled customers may contribute permitted sanitized examples or train isolated adapters.
6. Receive tested, signed model updates with rollback. Expand local routing only after held-out evaluation demonstrates improvement.

“Free local” means no software or inference-service charge; hardware, energy, storage and downloads remain user resources. Offline/local-only mode must work with downloaded weights and local tools, without remote inference or telemetry transmission. Remote inference can transmit code and context even when execution stays local.

## Reuse-first architecture

| Responsibility | Initial candidate | Product-specific integration |
| --- | --- | --- |
| Coding client, agent loop and tools | OpenCode; compare Qwen Code | Configuration, model policy and minimal routing hooks |
| Local inference | Ollama; compare llama.cpp for packaging/control | Hardware profiles, pinned models and tested tool templates |
| Routing | Rules first; RouteLLM or a small classifier later | Coding outcome prediction, calibration and escalation |
| Remote provider access | Existing provider adapter; LiteLLM when justified | Customer model selection, budgets and usage reconciliation |
| Evaluation and traces | Local artifacts; Langfuse for opted-in managed evaluation | Representative repository tasks, verifiers and holdouts |
| Training | Unsloth or Axolotl for SFT/LoRA; TRL for preference/RL experiments | Data selection, promotion criteria and artifact export |
| Distribution | Existing signed update tooling | Compatibility manifests, canary releases and rollback |

The data path is: **existing coding client → agent harness → router → local Qwen or remote premium model → local tools/tests**. Verified outcomes feed an optional training pipeline; evaluated model or adapter releases return to the local runtime. Choose one inference runtime and one training stack initially. A custom desktop shell, orchestration platform and GPU cluster are unnecessary for the first experiment.

## Local model selection

Select a verified current small dense Qwen checkpoint, initially evaluating approximately 1.5–7B total parameters and an 8B-class option if supported checkpoints justify it. Check current model cards, license, tool use, quantization and runtime compatibility before pinning a model name.

Qwen3-Coder-30B-A3B activates roughly 3B parameters per token but has roughly 30B total parameters; Coder-Next is based on an 80B-total/3B-active architecture. Active parameters do not establish laptop memory requirements. At four bits, raw 3B/7B weights are approximately 1.5/3.5 GB before metadata, KV cache and runtime overhead. These are arithmetic estimates, not measured device requirements.

Benchmark constrained and higher-memory devices for prompt ingestion, tool-call correctness, sustained generation, context memory, thermals and accepted-task latency. Use repository search and summaries to control context growth. CPU-only operation needs measured expectations.

## Confidence-aware routing: DeepInfer findings

DeepSeek's **DeepInfer** is the release identified in the research. Its README describes an offline inference release supporting DeepSeek-V4.1-Flash with **DSpark and confidence-scheduled verification**. Source inspection was pinned to commit `553741557a57df44a46fb3ab72b6aafeaf945337`.

The implementation uses a learned confidence head to predict draft-token acceptance, cumulative products to estimate surviving draft prefixes, and runtime cost curves to choose a verification budget. It ranks cumulative acceptance estimates to allocate verification positions across requests and records acceptance, verification length and confidence error. It also preserves dependencies between historical confidence estimates and scheduling decisions; a generic confidence threshold does not capture the full algorithm.

Apply the principle to tasks: **predict useful local work, allocate computation by expected benefit per cost, and compare predictions with observed outcomes**. Start with rules and outcome collection, then compare existing routing/classification tools. A custom model confidence head is a later experiment.

| Inference mechanism | Product analogue |
| --- | --- |
| Draft tokens | Local patch or tool-plan proposal |
| Predicted token acceptance | Calibrated local task/subtask success probability |
| Target-model verification | Tests, static checks and selective remote review |
| Verification compute budget | Local time, remote spending and latency budgets |
| Acceptance/error statistics | Held-out acceptance, routing calibration and repair cost |

Task routing does not inherit speculative decoding's distribution-preservation guarantees. Token likelihood is not patch correctness; tests and AI judges are imperfect verifiers. Do not multiply arbitrary subtask confidence scores as though their errors were independent.

## Initial routing policy

Enforce provider/data permissions, model capability, context fit and budget first. Use task category, affected modules, invalid tools, failed patches/tests, progress and device latency to decide whether to continue locally, verify, request remote review or escalate. Switch at completed tool/subtask boundaries with canonical context, current diff and recent evidence. Bound retries and preserve spending limits.

A starting comparison is `E[local-first] = C_local + C_verify + (1 - p_local) × C_escalate_after`, compared with immediate remote completion. Include extra context, repair and latency costs. This simplified expression assumes detection of local failure; production evaluation must measure undetected local failures and remote failures too. Use empirical cost per accepted task and quality constraints for final decisions.

Collect paired local/remote outcomes on authorized evaluation tasks, including local successes and failures. Use separate training, calibration and final evaluation splits by repository/task family/time. Compare reliability, Brier score, local coverage at a fixed error tolerance, latency and accepted-task cost. Recalibrate after every model, adapter or quantization update. Escalation logs alone create selection bias.

## Improvement loop: verified distillation first

Capture observable task context, relevant repository state, tool calls, patches, test evidence, user corrections and accepted outcomes. Filter secrets and preserve customer boundaries. Teacher outputs are candidates for verification, not automatic ground truth. An app distribution channel does not itself grant customer-data or teacher-output training rights; validate these for each actual provider/model and record provenance.

Verify examples through meaningful compilation/tests, type checks and review. Reject invalid tools, incomplete patches and examples that succeed only by weakening tests. Split datasets before creating near-duplicates and maintain untouched holdouts.

Train a stable base using existing SFT and LoRA/QLoRA tooling. Include multi-step observable behavior and representative prior capabilities to limit forgetting. Keep failed attempts paired with verified repairs for preference training. Start with one shared base plus repository instructions/retrieval; introduce customer-specific adapters when their measured gain justifies isolated data and deployment costs.

Prove the complete delivery chain: base revision → adapter training → supported loading or merge → quantization/export → local tool-use tests. Training-framework adapter support does not guarantee Ollama/GGUF compatibility. Use existing exporters and distribute merged quantized artifacts if required. Sign, canary, evaluate and support rollback.

Training should initially run as controlled offline/managed jobs. Optional on-device personalization comes later on supported hardware. Local inference and local training have different resource requirements.

## RLAIF research path

RLAIF uses AI-generated preference/reward feedback. First compare verified SFT with teacher-ranked candidate pairs and DPO using TRL. Consider online RL/GRPO only after simpler approaches establish a baseline. For executable coding tasks, prioritize verifiable rewards, with carefully weighted AI review for less measurable qualities.

Keep independent tests and held-out human review; prevent the trainee from changing the reward definition. Compare base → SFT → SFT+DPO → RL on the same held-out tasks. Include teacher judgments, candidate generation, training and validation in the cost model. AI agreement alone does not establish correctness.

## Delivery and release gates

1. **Runnable experiment:** OpenCode or Qwen Code, one local runtime, a verified small Qwen checkpoint and one remote provider; manual switching and representative tasks.
2. **Automatic routing:** thin endpoint or harness hook, deterministic escalation, budgets and route evidence; reuse provider/gateway capabilities.
3. **Dataset pipeline:** local trajectories, opted-in export, verifiers, provenance and untouched holdouts.
4. **First model update:** existing SFT/LoRA tooling, exact-runtime export, quantized-model regression tests, signed rollout and rollback.
5. **Learning experiments:** calibrated router, DPO/RLAIF and verifiable-reward RL; customer adapters and remote persistent execution follow demonstrated demand and gains.

Track accepted-task rate, strictly local accepted-task rate, escalation, tool validity, latency/memory by device, regressions and total cost per accepted task. Report evaluation-only teacher calls separately. Release only when quality remains within an agreed tolerance, local coverage improves, supported devices meet resource targets, rollback works and spending/data policies hold. Retain a premium-only baseline.

Economics must include remote inference, hosted product services, training/evaluation and model-update distribution allocated across tasks. The customer can select a premium model with a disclosed surcharge; verify prices and commercial terms before launch. Lower server inference spend alone does not establish positive unit economics.

## Research limits and open decisions

These are researched proposals. No harness/model benchmark, DeepInfer build or training run has been performed. Some current model cards and provider documentation were inaccessible under the research environment's network policy. DeepInfer's engine and confidence mechanism are verified from source; exact DeepSeek-V4.1-Flash weight/API availability, model license, commercial terms and integration remain unverified.

DeepInfer lists NVIDIA SM100 and Huawei Ascend 950 support and excludes service components such as a KV-cache system, deployment of prefill/decode disaggregation and replica load balancing. It is a later serving/reference candidate, not the proposed laptop runtime. Immediate decisions are the first device profiles, current small Qwen checkpoint, remote provider, task dataset and quality/cost baseline.

## Primary sources

- [OpenCode](https://github.com/anomalyco/opencode/blob/dev/README.md), [Qwen Code](https://github.com/QwenLM/qwen-code/blob/main/README.md), [Qwen3-Coder architecture and parser notes](https://github.com/QwenLM/Qwen3-Coder/blob/main/README.md).
- [Ollama](https://github.com/ollama/ollama/blob/main/README.md), [llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/README.md), [RouteLLM](https://github.com/lm-sys/RouteLLM/blob/main/README.md), [LiteLLM](https://github.com/BerriAI/litellm/blob/main/README.md).
- [DeepInfer release scope](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/README.md), [confidence head](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/deepinfer/model_executor/models/mtp/dflash.py), [confidence allocation](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/deepinfer/model_executor/layers/tilelang_ops/schedule_mtp_varlen.py), [cost-aware scheduler](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/csrc/engine/mtp_varlen.hpp), [acceptance statistics](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/deepinfer/engine/stats_logger.py).
- [Langfuse](https://github.com/langfuse/langfuse/blob/main/README.md), [Axolotl](https://github.com/axolotl-ai-cloud/axolotl/blob/main/README.md), [Unsloth](https://github.com/unslothai/unsloth/blob/main/README.md), [TRL](https://github.com/huggingface/trl/blob/main/README.md), [SWE-bench](https://github.com/SWE-bench/SWE-bench/blob/main/README.md).

DeepInfer links are pinned to the inspected commit. Other links follow upstream branches and should be pinned during implementation.
