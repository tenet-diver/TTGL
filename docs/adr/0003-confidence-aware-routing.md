# ADR 0003: Confidence-aware routing inspired by DeepInfer

Date: 2026-10-25  
Status: Proposed research direction; extends [ADR 0002](0002-local-first-learning-agent.md)

## Finding

The release the user described is **DeepInfer**. Its README identifies it as the inference framework powering DeepSeek production services, with an open-source release for **offline inference**, supporting DeepSeek-V4.1-Flash. It explicitly includes **DSpark and confidence-scheduled verification**.

This corrects the earlier research gap in ADRs 0001/0002: the engine and confidence mechanism are now identified from primary source and implementation. The exact model card/license and commercial API terms remain unchecked; the engine has not been built or benchmarked here.

Source pin inspected: `deepseek-ai/DeepInfer@553741557a57df44a46fb3ab72b6aafeaf945337`. The research checkout is outside TTGL under `/tmp`; it is not a product dependency.

## What the implementation does

1. A learned confidence head predicts each draft token's acceptance probability. `ConfidenceHead` projects hidden/Markov features and supports per-position temperature settings [2]. This is not a natural-language statement such as “I am confident.”
2. The scheduler forms cumulative products of per-position confidence estimates. A deeper draft token only helps when its preceding draft prefix survives [3,4].
3. It estimates expected accepted-token yield against measured execution cost, choosing a verification batch budget using runtime performance curves [4].
4. Given the token budget, it ranks cumulative acceptance estimates across requests and allocates extra verification positions accordingly, in addition to a base token per sequence [3].
5. Runtime statistics track accepted/verified tokens, verification length and confidence error [5]. Estimates can therefore be compared to observed behavior.

The scheduler also deliberately separates historical estimates used to choose the overall budget from those used for per-request lengths. Its comments require that later-position confidence not affect whether an earlier draft token gets verified [4]. This dependency constraint matters to the algorithm; copying only a confidence threshold would miss the design.

The general principle is: **learn a prediction of useful work, allocate computation by expected benefit per cost, and compare predictions to observed results.**

## Decision: apply the principle at task boundaries

Use a calibrated estimate of local task/subtask success to decide whether to continue locally, request verification, or escalate. Begin with rules and outcome collection; compare a small existing classifier/RouteLLM baseline before modifying any model internals. A learned confidence head on the local model is a later experiment, not an MVP dependency.

| DeepInfer mechanism | TTGL analogue | Important difference |
| --- | --- | --- |
| Draft proposal | Local Qwen proposes a patch or tool plan | Work unit is a semantic action or subtask |
| Learned token acceptance estimate | Predictor of local acceptance, test success and repair cost | Must train/calibrate on coding outcomes |
| Target verification | Tests, static checks and selective remote review | Tests/judges are imperfect task verifiers |
| Verification compute budget | Local time, remote spend and latency budgets | Costs span devices, network and providers |
| Acceptance statistics | Held-out task acceptance and routing calibration | User outcomes may be delayed or subjective |
| Cheap drafts improve throughput | Local completion reduces paid inference | Savings require preserved task quality |

Standard speculative decoding can retain a target distribution through its verification/sampling algorithm. Selecting an entire local answer instead of asking a remote model has **no equivalent correctness/distribution guarantee**. The product must establish its own quality constraints and abstention/escalation policy. High token likelihood is not proof of patch correctness.

## Practical policy

For task state `x`, estimate:

- `p_local(x)`: chance a bounded local attempt meets the acceptance criterion.
- `C_local`, `C_verify`: expected local attempt and verification cost, including latency if relevant.
- `C_escalate_after(x)`: expected remote completion cost following local failure, including extra context and repair.
- `C_remote_now(x)`: expected remote completion cost if escalating immediately.

An initial expected-cost comparison is:

`E[local-first] = C_local + C_verify + (1 - p_local) * C_escalate_after`

Compare against `C_remote_now`, subject to quality, privacy, capability and latency constraints. This simplified expression assumes successful detection of local failure; production evaluation must also estimate **undetected local failures** and remote failure probability. Those cannot be treated as free successes. Use empirical accepted-task cost and calibrated risk limits for final decisions.

Actions: continue locally for a bounded attempt, run cheap verification, seek remote review, or escalate outright. Remote review is worth using only when it beats direct remote completion on cost/latency/quality. Never require remote verification on every local task, which would undermine offline operation and free local usage.

Features can include task category, affected modules, context length, tool validity, compiler/test outcomes, repeated failures, progress, and measured device latency. Optional local token probabilities or hidden-state features may help, but do not require them when the selected runtime cannot expose them efficiently. Self-reported confidence alone is insufficient.

Do not multiply arbitrary subtask confidence scores as though independent. DeepInfer's prefix formulation is tied to its draft-token process. Coding subtasks share dependencies and correlated failures. Train conditional outcome predictors or use conservative per-step gates, then validate end-to-end acceptance.

## Learning and validation

Collect paired local/remote outcomes on authorized evaluation tasks, including local successes and failures. Train a predictor using existing software. Calibrate on a separate split; compare reliability plots, Brier score, accepted-local coverage at a fixed error tolerance, escalation rate, task latency and total cost per accepted task. Evaluate separately by device/model revision and repository/task family.

Use fixed-budget randomized comparisons or offline shadow runs to avoid learning only from escalated failures. Keep calibration and final evaluation separate from training. The router must adapt after model updates: the same threshold need not mean the same success rate for a new adapter or quantization.

Distill verified remote repairs into the local model as described in ADR 0002. Retrain/recalibrate the routing predictor against the updated local model. Expand local coverage only when measured quality permits. This closes two linked learning loops: the worker improves its capability; the router improves its estimate of where that capability is sufficient.

## Engine adoption boundary

DeepInfer's README lists NVIDIA SM100 and Huawei Ascend 950 support; prerequisites include Linux, Python 3.12, GCC 13+, CUDA 13 or CANN 9.2. It says the release excludes components required for a complete inference service: a KV-cache system, prefill/decode disaggregation deployment, and replica load balancing [1]. It is therefore a research/reference or later self-hosted serving candidate, not an ordinary-laptop runtime or complete production endpoint.

Use Ollama/llama.cpp locally and an existing remote provider first. Reuse confidence-aware serving support where the selected engine offers a tested compatible implementation. Do not port DeepInfer's kernels or implement a new inference engine for TTGL.

## Sources

All DeepInfer links are pinned to the inspected commit; findings are from source review, not execution or independent performance validation.

1. [DeepInfer README, release scope, DSpark, hardware and service exclusions](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/README.md).
2. [ConfidenceHead implementation](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/deepinfer/model_executor/models/mtp/dflash.py).
3. [Confidence-product allocation and reference implementation](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/deepinfer/model_executor/layers/tilelang_ops/schedule_mtp_varlen.py).
4. [Cost-aware verification scheduling and dependency constraints](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/csrc/engine/mtp_varlen.hpp).
5. [Acceptance and confidence-error statistics](https://github.com/deepseek-ai/DeepInfer/blob/553741557a57df44a46fb3ab72b6aafeaf945337/deepinfer/engine/stats_logger.py).
6. [vLLM speculative-decoding methods and losslessness discussion](https://github.com/vllm-project/vllm/blob/main/docs/features/speculative_decoding/README.md), also inspected 2026-10-25; moving upstream source.
