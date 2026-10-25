# Customer adaptation, model placement and switching costs

## The deployed expert is more than a model name

A portfolio expert is a complete deployment configuration: a base checkpoint, optional customer or domain adapter, tokenizer and prompt template, numerical precision, serving engine, placement and inference limits. A 4B model on a desktop, its quantized cloud deployment, and its customer-adapted version need not have identical accuracy or latency. They must have separate configuration identifiers even when they share a model-family name. Parameter count is therefore a candidate attribute, not a sufficient routing rule. A smaller browser specialist may outperform a larger general model on a particular interaction interface; that is a hypothesis to test under the common interface, not a consequence of specialization alone.

Two allocation decisions occur at different times. Deployment planning selects which base models to keep resident, where to serve them, and which adapters to retain near the accelerator. The request policy selects among the configurations that are currently available. A request router cannot obtain an unprovisioned model at the same cost and latency as a warm resident model. Conversely, keeping every candidate loaded can make an apparently inexpensive portfolio expensive through idle capacity. The experimental manifest records both decisions, and the cost model includes the resulting allocation and queueing effects.

## What can be shared across customer adaptations

Ordinary LoRA learns a low-rank update to particular matrices of a particular base model [@hu2021lora]. For a layer with weight $W\in\mathbb R^{d_{\mathrm{out}}\times d_{\mathrm{in}}}$, the adapted weight can be written

$$
W'=W+\frac{\alpha}{r}BA,
\qquad
A\in\mathbb R^{r\times d_{\mathrm{in}}},\quad
B\in\mathbb R^{d_{\mathrm{out}}\times r}.
$$

The dimensions, target-layer names and learned representation determine where this update applies. An adapter for one 4B model cannot generally be attached to an unrelated 9B model. Even matching dimensions do not establish semantic compatibility: the underlying weights, representations and training history can differ. A new revision of the same named base is also not presumed equivalent. Transfer or adapter-conversion methods would be separate treatments with their own evidence, rather than an implicit feature of ordinary LoRA.

The practical shared object is a **customer adaptation package** containing approved training examples, provenance, evaluation cases, preferences and a mapping from eligible base revisions to their separately trained adapters. The package is shared at the product level; the tensor updates remain specific to their validated bases. PEFT's checkpoint format records the base identifier, revision and target modules, while its hotswap mechanism replaces adapter tensors inside an existing base model. Hotswapping is useful for compatible adapters on that base; it does not establish portability across arbitrary architectures.[^adapt-peft]

A minimum adapter manifest contains the customer or public experimental-tenant identifier; base, tokenizer and adapter hashes; training-data revision; target modules; rank and scaling; training precision; supported inference precisions; and held-out validation results. An adapter may be absent for a candidate, in which case the router selects the unadapted model or another eligible expert. The system must not silently substitute another customer's adapter. Public benchmark experiments can use declared repository or organization groupings as simulated tenants, but must not present those groupings as measured customer personalization.

A single base with several domain adapters is a useful alternative to several distinct small bases. It shares the expensive base weights and may simplify deployment, while allowing different task specializations. It does not guarantee the same breadth as a portfolio of independently pretrained models. The comparison should include one general adapter, domain-specific adapters on one base, and separate base-specific adapters, under the same training-data and total adaptation-budget accounting. Combining adapter outputs within one network is a different intervention from choosing between independently served language models; the two should not be pooled under a single “ensemble” label.

## Reuse established multi-adapter serving

The first cloud implementation should use a maintained serving system's existing adapter support. Current vLLM documentation supports per-request LoRA selection for architectures implementing its `SupportsLoRA` interface and exposes limits including `max_loras`, `max_lora_rank` and `max_cpu_loras`. Compatibility is therefore checked for the exact checkpoint and engine revision; support for a model's unadapted inference does not imply support for all its adapter targets. The selected adapter and its resolved hash become part of every model event.[^adapt-vllm]

S-LoRA and Punica explain why this architecture can be economical. S-LoRA manages adapter weights and KV memory through unified paging and schedules heterogeneous adapters; Punica batches computations that share a base while applying separate low-rank updates [@sheng2023slora; @chen2023punica]. Their papers and implementation descriptions support reusing a base across tenants, not the claim that serving arbitrary different bases costs the same as serving one. Their reported throughput gains are historical experiments under their own workloads and baselines. They are not used as predicted gains for the proposed system, and an older README's statement about missing vLLM features is not treated as current: the inspected current vLLM documentation already describes LoRA serving.

For a desktop deployment, llama.cpp documents loading and scaling LoRA adapters and controlling adapters through its server interface. MLX-LM documents LoRA, QLoRA and full fine-tuning on supported models, as well as producing a fused model. These are implementation candidates, not evidence that the thesis's current checkpoint, export format and tool interface work together. The preflight must verify conversion, generation and held-out behavior after adapter fusion or quantization. Repeatedly merging and unmerging quantized weights is not treated as lossless; PEFT explicitly warns about accumulated rounding error.[^adapt-local]

## KV-cache continuity and the meaning of a switch

A key–value cache stores internal tensors computed from a token prefix under a particular model computation. It is not a portable transcript. Changing the base weights, architecture, tokenizer, position handling or relevant adapter generally invalidates reuse, even when the human-readable conversation is unchanged. A successful checkpoint load or a matching tensor shape does not establish cache validity. The safe default for a cross-base handoff is to re-tokenize the permitted state and recompute the recipient's prefix.

The distinction between three warm states is essential. A **warm base** has its weights resident; a **warm adapter** has its additional tensors available; a **warm conversation prefix** has reusable KV state for the exact computation. The first two can make loading cheap without making prefill free. Returning to a previous model may recover a retained compatible cache, but only if that state is still resident and its prefix identity matches. Changes to a browser screenshot or conversation ordering can invalidate the expected match.

Current vLLM prefix-cache documentation explicitly includes LoRA identifiers, multimodal-input hashes and tenant-isolation salts in its block identity. It also states that automatic prefix caching reuses matching prefixes to avoid repeated prompt computation; this does not eliminate the generation of new tokens. The design should preserve those correctness boundaries, not remove adapter identifiers merely to increase cache-hit counts. Customer authorization remains separate from cache optimization.[^adapt-cache]

A provider's cache-read billing category is another measurement. It may reward an eligible repeated prefix, but it is not proof that a particular tensor cache is available to the application or transferable to another service. API pricing, server-side cache observations and local cache residence are logged separately. Likewise, the browser's cookies, tabs and application state live in the controlled browser session, rather than in the language model's KV cache. A model handoff may preserve that external state while still losing computational reuse and some unrecorded reasoning context.

## A useful exception: activated LoRA on one base

Activated LoRA (aLoRA) modifies when adaptation begins. Its weights activate from a declared invocation sequence; preceding tokens are processed with the base model's weights. The paper and current PEFT implementation explain how this preserves compatible base-model KV values before the activation boundary [@greenewald2025alora]. This is directly relevant to using several specialized checks or continuations over an already processed context.

The guarantee is restricted. It applies to the shared base computation before activation, not to arbitrary different LLMs. KV values generated after an adapter has activated are not automatically reusable by the base or a different adapter; the reusable prefix must be identified, and contaminated suffix state discarded or separately retained. PEFT's documentation restricts aLoRA to causal-language-model tasks, requires an invocation sequence, and does not support merging these selectively applied weights into the base. Consequently, aLoRA is a promising secondary experiment for **one base plus several specialists**, not a reason to assume costless transitions throughout a heterogeneous portfolio.[^adapt-alora]

## Select once, then switch at justified boundaries

The primary portfolio policy selects a model configuration for a whole task attempt. This minimizes handoff ambiguity and makes comparison with fixed-model baselines interpretable. A secondary policy permits changes at declared phase boundaries: for example, after repository investigation and before implementation, or after locating a browser form and before a specialized extraction step. Per-call switching is an ablation whose benefit must overcome its extra overhead; it is not the default merely because a routing decision can be computed cheaply.

Let $Q_j(s)$ predict terminal success from the current permitted state $s$ when model configuration $j$ continues. Let $C_j(s)$ and $T_j(s)$ predict remaining cost and time, excluding the transition. If $k$ is the current configuration, switch to $j$ only when

$$
\begin{aligned}
\widehat Q_j(s)-\widehat Q_k(s)
&> \lambda\bigl[\widehat C_j(s)-\widehat C_k(s)+\widehat C_{k\to j}(s)\bigr] \\
&\quad+\mu\bigl[\widehat T_j(s)-\widehat T_k(s)+\widehat T_{k\to j}(s)\bigr]+h.
\end{aligned}
$$

Here $\lambda$ and $\mu$ convert monetary cost and latency into the declared utility scale, and $h\geq0$ is a calibrated hysteresis margin against repeated reversals. Transition terms include loading, re-prefill, serialization, summarization, network transfer and queue delay as applicable. The quality predictor must be trained on the actual handoff state, including any summary loss; a fresh-start benchmark score is not a continuation-success probability. Already incurred expenditure remains in total task cost but is a sunk cost for this forward-looking decision. A remaining-budget constraint independently excludes unaffordable actions.

The handoff record contains the goal, completed work, current repository patch or browser state reference, observed test or tool outcomes, unresolved questions, permissions and remaining limits. Tools must finish or be cancelled at a documented boundary. The model receives externally recorded work and observations, not an assumed transfer of opaque reasoning state. This makes semantic state loss observable and keeps model switching separate from changing tool privileges.

## Desktop fine-tuning versus cloud adapters

Training location and inference location are independent design choices. A customer can run a model locally after its permitted adaptation was trained on a cloud GPU, or train on their own supported desktop. Local training is useful when data cannot leave the device, but full fine-tuning should be conditional on measured memory, runtime, power and thermal limits. A model fitting in quantized inference memory does not establish that full training fits.

For scale, a conventional mixed-precision AdamW configuration can require approximately 16 bytes per trainable parameter for weights, gradients, master weights and optimizer moments before activations and temporary buffers. A 4B-parameter model would therefore require approximately 64 GB for those quantities alone in that illustrative configuration. Optimizers, sharding, precision and offloading change this accounting; it is not a universal lower bound. LoRA and QLoRA reduce trainable-state requirements but still consume base-model, activation and runtime memory [@dettmers2023qlora]. MLX-LM's documented full-fine-tuning option establishes software functionality, not suitability for every desktop.

The initial product configuration should compare one locally resident compact model with a small remote specialist pool. Additional local bases are admitted only when their measured marginal benefit justifies memory, disk, loading and maintenance costs. In a shared cloud deployment, additional adapters on a common base may be cheaper than additional independently resident bases, but traffic mix and contention can reverse that advantage. Pool size and placement are therefore experimental variables rather than fixed beliefs about what “small” should mean.

## Measurements and adaptation lifecycle

The switching study records cold and warm base loading, adapter loading, time to first token, prefix tokens recomputed, cache-hit observations, peak memory, queue time, end-to-end latency and final success. It compares task-level selection, phase-level selection and per-call selection under the same resource ceilings. Within-base ordinary LoRA and aLoRA are separate configurations. Cold-start and steady-state results are both reported; the experiment must not warm every expert for one policy while charging startup to its comparator.

Adaptation evaluation separates model improvement from allocation changes: first test the adapted experts under a frozen router, then recalibrate routing on development data and test that distinct policy. Training, teacher generation and repeated compatibility checks enter an explicit amortization ledger. A new model release triggers an admission evaluation and, if selected, revised base-specific adapters or retraining; it does not inherit the old adapter's quality label. The serving system can keep the same customer-facing identity while changing its validated internal mapping. These mechanisms make a changing portfolio feasible without assuming that every new model improves the frontier or that every customer benefits from training an adapter for every candidate.

[^adapt-peft]: Revision-pinned PEFT [checkpoint format](https://github.com/huggingface/peft/blob/7d6315ae910bf62b6044a7ca917bccf5881f5e43/docs/source/developer_guides/checkpoint.md) and [hotswapping documentation](https://github.com/huggingface/peft/blob/7d6315ae910bf62b6044a7ca917bccf5881f5e43/docs/source/package_reference/hotswap.md), retrieved 25 October 2026. Source hashes and review scope are recorded in `adaptation-sources.json`.

[^adapt-vllm]: vLLM [LoRA serving documentation](https://github.com/vllm-project/vllm/blob/237d2ffd08044b52625453af59f1e47b9802d4ff/docs/features/lora.md). Per-request adapter support is explicitly conditional on the model interface and configured capacity limits.

[^adapt-local]: Pinned [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/48c9f08b7b25766324282b7605177e2f2be755bb/tools/server/README.md), [MLX-LM fine-tuning documentation](https://github.com/ml-explore/mlx-lm/blob/4cfc6478473b0668ede3eb0cc93f2a9181a15052/mlx_lm/LORA.md), and [PEFT LoRA documentation](https://github.com/huggingface/peft/blob/7d6315ae910bf62b6044a7ca917bccf5881f5e43/docs/source/package_reference/lora.md).

[^adapt-cache]: vLLM [prefix-cache design](https://github.com/vllm-project/vllm/blob/237d2ffd08044b52625453af59f1e47b9802d4ff/docs/design/prefix_caching.md) and [automatic prefix-caching feature description](https://github.com/vllm-project/vllm/blob/237d2ffd08044b52625453af59f1e47b9802d4ff/docs/features/automatic_prefix_caching.md).

[^adapt-alora]: PEFT [activated-LoRA documentation](https://github.com/huggingface/peft/blob/7d6315ae910bf62b6044a7ca917bccf5881f5e43/docs/source/package_reference/lora.md#activated-lora-alora) and [training example](https://github.com/huggingface/peft/blob/7d6315ae910bf62b6044a7ca917bccf5881f5e43/examples/alora_finetuning/README.md); the source register distinguishes inspected documentation from the paper's targeted full-text review.
