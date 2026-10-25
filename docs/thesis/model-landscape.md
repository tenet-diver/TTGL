# Model and price landscape

This chapter freezes the **model-selection evidence on 25 October 2026**. It contains published vendor claims and a dated price catalog, not results from the TTGL experiment. “Latest” means the latest relevant release found in the inspected official repositories and model cards; this is not a claim of exhaustive market coverage. The accompanying [model catalog](model-catalog.csv) records exact identifiers, model revisions, licenses, service names, units, and evidence status. [The source register](market-sources.json) preserves retrieval timestamps, content hashes, revision-pinned URLs, selected source excerpts, and unsuccessful pricing requests.

## Candidate selection

The current Qwen release catalog lists Qwen3.8-27B, released on 14 August 2026, and Qwen3.8-2.4T-A95B, released on 12 August. Its most recent sub-10B dense releases are **Qwen3.5-0.8B, 2B, 4B, and 9B**, released on 2 March. Consequently, the initial development shortlist includes **Qwen3.5-4B**, **Qwen3.5-9B** for a capacity comparison, and **Qwen3.8-27B** as a potential self-hosted teacher or portfolio member. These roles are hypotheses to test, not evidence that one fixed size pair is optimal. Calling a small local checkpoint “Qwen3.8” would misidentify the verified release. Qwen2.5 remains useful for reproducing the existing implementation, but it is a historical baseline rather than a current-generation claim.[^market-qwen]

The ten candidates below form the initial software-engineering market register. They cover local inference, remotely hosted open weights, inexpensive closed APIs, and premium closed APIs. The browser-domain chapter adds modality-specific evidence and candidate roles. This is neither a fixed two-model architecture nor a final best-model ranking: several small or large configurations may be eligible, and pool membership is selected on development data. Candidate status does not imply that TTGL already supports the model or that an account can access it.

| Candidate | Proposed role | Parameters: total / active | Weight access and license |
|---|---|---|---|
| Qwen3.5-4B | Primary local student | 4B / dense | Open weights, Apache-2.0 |
| Qwen3.5-9B | Local capacity ablation | 9B / dense | Open weights, Apache-2.0 |
| Qwen3.8-27B | Self-hosted teacher or remote baseline | 27B / dense | Open weights, Apache-2.0 |
| DeepSeek-V4.1-Flash-1017 | Remote teacher candidate | Base family: 552B backbone; 8B prefill / 16B decode active | Open weights, MIT |
| GLM-5.3-Flash | Low-price remote baseline | 320B / 18B | Open weights, MIT |
| Kimi K3 | Remote frontier reference | 2.8T / 104B | Open weights, custom Kimi K3 License |
| GPT-6.1 Sol | Premium closed baseline | Undisclosed | Closed weights |
| GPT-6 Luna | Inexpensive closed baseline | Undisclosed | Closed weights |
| Claude Sonnet 5.5 | Premium closed baseline | Undisclosed | Closed weights |
| Claude Opus 5.5 | Higher-price closed reference | Undisclosed | Closed weights |

The official OpenAI and Anthropic SDK model catalogs identify the closed-model API names `gpt-6.1-sol`, `gpt-6-luna`, `claude-sonnet-5-5`, and `claude-opus-5-5`. An SDK entry establishes an identifier, not an immutable weight revision, capability guarantee, or account entitlement. Freeze the returned serving revision and all provider settings at execution; do not silently roll an alias forward midway through a comparison.[^market-sdk]

Open weights and open-source software are different properties. The Qwen licenses above were checked in the individual weight repositories. GLM-5.3-Flash weights use MIT even though its umbrella GLM-5 code repository uses Apache-2.0. Kimi K3 applies its custom license to both code and weights: among other provisions, it requires a separate commercial agreement for a model-as-a-service business above the specified aggregate revenue threshold and branding for certain very large services. The exact license includes exceptions and definitions; it must be read for the intended deployment. A permissive harness or SDK license does not license the model, and a model-weight license does not establish hosted-API output-training rights.[^market-licenses]

The parameter distinction materially changes feasibility. GLM's 18B active parameters do not mean only 18B weights need storage. Even an idealized 4-bit representation of its 320B total parameters requires approximately 160 GB before scales, activations, KV cache, and runtime overhead. Kimi's 2.8T parameters require approximately 1.4 TB at that idealized precision. DeepSeek's base card specifies a 552B backbone and separately describes 196B Engram conditional memory; the inspected wording does not establish an unambiguous combined total, so this chapter does not add them. The backbone alone is already too large for full residency on one 80 GB GPU. Qwen3.8-27B has approximately 54 GB of raw BF16 weights, making a memory-profiled single-GPU inference trial plausible; that arithmetic is not proof of long-context or training feasibility.[^market-large]

## Price comparison and what it measures

**All direct-API rates in the following table are provisional secondary observations, not vendor-verified quotes.** They come from one revision-pinned LiteLLM community catalog snapshot. Direct OpenAI, Anthropic, DeepSeek, Nebius, and Z.ai pricing pages were requested and returned proxy `403` errors, including a later recheck after model-card access succeeded. Successful Hugging Face retrieval therefore does not establish access to those billing sources. The exact failures are recorded rather than replaced with guessed prices.[^market-prices]

Rates are **USD per one million text tokens**, in the order **uncached input / cache-read input / output**, for the catalog's ordinary base tier. They exclude cache creation, long-context multipliers, batch discounts, priority or fast modes, regional adjustments, tool charges, taxes, and subscription conditions. Missing cache prices are unknown, not zero.

| Model / priced service | Input | Cache read | Output | Qualification |
|----------------------------|---------:|------------:|---------:|-------------------------------------|
| Qwen3.5-4B / local | — | — | — | No API token bill; hardware, energy, and training still cost money |
| Qwen3.5-9B / local | — | — | — | Same accounting boundary |
| Qwen3.8-27B / Nebius Token Factory | $0.45 | Unknown | $3.00 | Third-party service; not a Runpod rental quote |
| DeepSeek-V4.1-Flash / Tencent Cloud | $0.30 | $0.006 | $1.20 | Alias-to-1017 mapping unverified; not direct DeepSeek pricing |
| GLM-5.3-Flash / Z.ai | $0.15 | $0.03 | $0.50 | Base catalog rate |
| Kimi K3 / Moonshot | $3.00 | $0.30 | $15.00 | Base catalog rate |
| GPT-6.1 Sol / OpenAI | $2.00 | $0.10 | $10.00 | Standard tier, input at most 272K tokens |
| GPT-6 Luna / OpenAI | $0.10 | $0.01 | $0.50 | Standard tier, input at most 272K tokens |
| Claude Sonnet 5.5 / Anthropic | $2.00 | $0.10 | $10.00 | Standard text tier; separate cache-write charges |
| Claude Opus 5.5 / Anthropic | $4.00 | $0.20 | $20.00 | Standard text tier; separate cache-write charges |

An independently retrieved **primary GitHub Copilot pricing file** lists the same four closed-model base input, cache-read, and output rates. This corroborates those numbers for the Copilot channel only; it does not certify the direct-provider API contract. Its service plan, credit accounting, and model availability are separate. Neither source establishes a free API tier or the price of an available 80 GB Runpod instance.[^market-copilot]

This price table motivates inclusion of an inexpensive closed baseline: a portfolio system must compete with an already cheap API, not only a premium teacher. It does not establish cost effectiveness. A task may use many model calls, cached and uncached context, reasoning tokens, failed tools, and retries. The experiment must compute total inference and tool cost per attempted task, total cost per resolved issue, and wall-clock latency from actual traces. Local cost should be reported both as marginal energy plus incremental infrastructure and under an explicit amortized hardware scenario. Report distillation/training expenditure separately and amortize it over declared future workload sizes; a “free local” product tier is a billing choice, not zero economic cost.

## Published accuracy evidence: contextual, not a leaderboard

Published scores establish that candidate models have been evaluated on relevant tasks. They cannot supply the missing TTGL comparison. Every score below is a **vendor-reported claim** from a primary artifact; none has been reproduced here, and none is a TTGL outcome. A blank latest-model score means insufficient inspected evidence, not zero capability.

| Model | Published claim | Harness and limits disclosed by that source |
|---|---|---|
| Qwen3.5-4B | LiveCodeBench v6: 55.8 | Coding-problem benchmark, not repository-level SWE; exact task count and harness not stated in the inspected card |
| Qwen3.5-9B | LiveCodeBench v6: 65.6 | Same qualification; quantized local deployment must be measured separately |
| Qwen3.8-27B | DeepSWE v1.1: 42.2; SWE-bench Pro: 61.7 | Claude Code; temperature 1.0, top-p 0.95, 256K context; Pro uses vendor-corrected tasks, not an unchanged official task set |
| DeepSeek-V4.1-Flash-1017 | DeepSWE v1.1: 77.0 | Mini-SWE-V2; task count, exact harness commit, and benchmark-specific sampling budget not stated in the inspected update card |
| GLM-5.3-Flash | DeepSWE v1.1: 63.4 | mini-swe-agent, temperature 0.95, top-p 1.0, 400K context, six-hour timeout; task count and exact harness commit unspecified |
| Kimi K3 | DeepSWE v1.1: 67.3 | README footnote attributes this to mini-SWE-agent; main-table 67.5 uses Kimi Code; task count and exact harness commit unspecified |
| Four latest closed candidates above | Not established by inspected SDK/pricing sources | Catalog presence and prices provide no SWE accuracy evidence |

The Qwen figures come from its exact model cards, the GLM figure from a pinned official chart plus its model-card evaluation footnote, and the Kimi and DeepSeek figures from their official release artifacts.[^market-accuracy] These are different benchmark families and operating points. LiveCodeBench is not SWE-bench Verified; SWE-bench Pro is not DeepSWE; corrected tasks are not the original evaluation set. Even the DeepSWE rows differ in context, timeout, harness, and version details. The table is deliberately **not sorted by score**, and no price–accuracy Pareto frontier is inferred from it.

The parent DeepSeek-V4.1-Flash card illustrates why harness control matters: it reports DeepSWE v1.1 scores ranging from 65.5 with OpenCode to 74.2 with mini-SWE for the same model, under a described eight samples per task, one-million-token context, and 500-step setting. The newer 1017 card reports 77.0 with Mini-SWE-V2; this cannot be treated as a clean model-only improvement over the older number. It also compares older closed releases, including GPT-5.6 Sol and Opus 5; those scores must not be reassigned to GPT-6.1 Sol or Opus 5.5.[^market-deepseek-base]

For the thesis, “software-engineering accuracy” should mean issue resolution by the benchmark's official executable evaluator. Compare always-local, always-remote, and routed systems on the **same held-out issues, harness revision, tools, prompts, retry policy, step limit, context policy, and task timeout**. A direct single completion without tools is a separate model-only task condition; it must not be presented as equivalent to an agent using shell access and tests. The closed and open models require this same evaluation before any capability or price–accuracy ranking is defensible.

## Runtime readiness and the first bounded study

The verified releases are **research candidates, not deployment-ready TTGL configurations**. The existing Qwen2.5 training stack's Transformers 4.56.2 / TRL 0.23.1 pins do not establish support for Qwen3.5's hybrid architecture or Qwen3.8. The Qwen3.5-4B card recommends current frameworks, illustrates Transformers installed from `main` with serving support, SGLang from its Git repository, and vLLM with a nightly-wheel index. It specifies `qwen3` reasoning parsing and `qwen3_coder` tool parsing, and offers a language-model-only serving mode. It does **not** give a stable numeric minimum version that this chapter can certify. The Qwen3.8-27B card likewise recommends current SGLang, vLLM, or TokenSpeed recipes without specifying a numeric minimum in the inspected text.[^market-runtime]

Resolve compatible released versions or immutable commits in a new lockfile; verify loading, tool calls, loss masking, one optimizer step, adapter save/reload, and evaluation on an excluded smoke-test task before a paid run. Serving support is not proof of fine-tuning or TRL compatibility. Keep model revision, tokenizer/template revision, quantizer, engine build, precision, reasoning-effort setting, and maximum context in the run manifest. For local Qwen, evaluate the same quantized deployment that the product intends to ship.

DeepInfer is valuable related work, but its current README targets **NVIDIA SM100 or Ascend 950**, requires Linux, GCC at least 13, Python 3.12, and CUDA 13 or CANN 9.2, and states that a complete service still needs KV-cache management, disaggregation, and load balancing. Its example benchmarks use four SM100 GPUs for prefill and 64 for decode. This is not the first experiment's single A100/H100-class 80 GB deployment. Its default checkpoint is exactly DeepSeek-V4.1-Flash-1017. Use the model through a suitable remote service for the bounded pilot if exact revision and API behavior can be established; use a manageable Qwen teacher for direct access to full logits.[^market-deepinfer]

With a US$100 total GPU budget, the ten-model catalog is a selection space rather than a commitment to an exhaustive training matrix. For the smallest integration pilot, prioritize one small candidate, one reference model and the restricted two-model combination. That pilot verifies infrastructure; the expanded portfolio claim requires at least three eligible configurations under the ensemble protocol and a separately costed experiment. Add the 9B capacity ablation only after a costed smoke run establishes feasibility. An inexpensive closed API is a useful later comparator, subject to a separate authorized API budget; the Runpod approval does not cover that spending. Keep broad frontier comparisons descriptive until funded comparable evaluations exist. Teacher API text or top-k log probabilities must not be described as full logits; exact-token distillation additionally requires tokenizer compatibility or an explicitly validated alignment method. All TTGL held-out software-engineering and browser accuracy, portfolio calibration, savings, and adaptation gains remain unmeasured. The task-economics chapter provides attributable historical dollars per task and separate current-rate arithmetic scenarios; neither fills that empirical gap.

[^market-qwen]: Qwen official [release catalog](https://github.com/QwenLM/Qwen3.8/blob/2ea10dc725823bf7c3e21ce8557cbe15245132ae/README.md). Individual weight-card revisions and licenses are recorded in `model-catalog.csv` and `market-sources.json`.

[^market-sdk]: OpenAI [SDK model identifiers](https://github.com/openai/openai-python/blob/5d72315876ffd8b72b958623ef4db26da3fb1e61/src/openai/types/shared/chat_model.py); Anthropic [SDK model identifiers](https://github.com/anthropics/anthropic-sdk-python/blob/202db72c87d7c6eaa72129c67ce67fd343a3a20c/src/anthropic/types/model.py). Retrieved 25 October 2026.

[^market-licenses]: Qwen [4B weight license](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/LICENSE), [9B weight license](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/LICENSE), and [27B weight license](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/LICENSE); [GLM-5.3-Flash weight license](https://huggingface.co/zai-org/GLM-5.3-Flash/blob/46a050bec13002ad29ee795c16e61cf4fa3c4a9c/LICENSE); [Kimi K3 license](https://github.com/MoonshotAI/Kimi-K3/blob/3cb39dfd32e51c3328e2e4b4af21341247d06c43/LICENSE); [DeepSeek-1017 license statement](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/1bae0e1088993b9b82de08f59de5be5a34e42170/README.md#license).

[^market-large]: [GLM official model table](https://github.com/zai-org/GLM-5/blob/83c03d317378f86f0a012f7c4cd48b6243c7e69b/README.md); [Kimi K3 architecture](https://github.com/MoonshotAI/Kimi-K3/blob/3cb39dfd32e51c3328e2e4b4af21341247d06c43/README.md); [DeepSeek base family architecture](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/314113f8a7dadb388215396ba5fbee2c610a04d6/README.md).

[^market-prices]: Secondary source: [LiteLLM price catalog, commit dddbaa8](https://github.com/BerriAI/litellm/blob/dddbaa803d6e9fcc862ea7a5412f771cb1ae040e/model_prices_and_context_window.json), retrieved 25 October 2026. Exact catalog keys, raw selected entries, and the catalog's cited upstream URLs are preserved in `market-sources.json`. Upstream direct API rates remain unverified.

[^market-copilot]: Primary source for its own service channel: [GitHub Copilot model prices](https://github.com/github/docs/blob/02c25d16369fe27f9bdb28d1201f6b452f0d21dd/data/tables/copilot/models-and-pricing.yml), retrieved 25 October 2026. This is not a direct-provider API quote.

[^market-accuracy]: Qwen model cards: [4B](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md), [9B](https://huggingface.co/Qwen/Qwen3.5-9B/blob/c202236235762e1c871ad0ccb60c8ee5ba337b9a/README.md), [27B](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md); [GLM official benchmark chart](https://github.com/zai-org/GLM-5/blob/83c03d317378f86f0a012f7c4cd48b6243c7e69b/resources/bench_53.png) and [evaluation settings](https://huggingface.co/zai-org/GLM-5.3-Flash/blob/46a050bec13002ad29ee795c16e61cf4fa3c4a9c/README.md); [Kimi README footnotes](https://github.com/MoonshotAI/Kimi-K3/blob/3cb39dfd32e51c3328e2e4b4af21341247d06c43/README.md); [DeepSeek-1017 model card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/1bae0e1088993b9b82de08f59de5be5a34e42170/README.md).

[^market-deepseek-base]: [DeepSeek-V4.1-Flash base release card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/314113f8a7dadb388215396ba5fbee2c610a04d6/README.md), especially “Performance across agent scaffolds”; this is separate from the 1017 update card.

[^market-runtime]: [Qwen3.5-4B serving instructions](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md) and [Qwen3.8-27B serving instructions](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md). Framework recommendations are vendor documentation, not a completed TTGL compatibility test.

[^market-deepinfer]: [DeepInfer README](https://github.com/deepseek-ai/DeepInfer), retrieved 25 October 2026; content hash and retrieved source URL in `market-sources.json`. Hardware and complete-service limitations are explicitly documented by the project.
