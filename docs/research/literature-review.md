# Literature review: confidence-aware local/remote coding systems

Review date: 2026-10-25. Study context: TTGL, a local Qwen coding assistant that escalates selected work to a larger remote model and may learn from verified remote outputs. This document reviews prior work and motivates experiments; it does not report TTGL experimental outcomes.

## Scope and evidence method

This is a focused, reproducible narrative review, not an exhaustive systematic review. Sources were selected by their direct relevance to five questions: when to defer, how to calibrate confidence, what speculative decoding contributes, how to improve a student, and how to measure code correctness. We followed citations from author-maintained repositories and inspected primary implementation documentation. Inclusion required a named method/evaluation protocol and an identifiable original paper or implementation; product marketing alone was excluded. We did not search a complete scholarly index or claim PRISMA coverage.

The access policy allowed GitHub/raw GitHub but denied attempted arXiv abstract retrieval. Consequently, **most papers below were reviewed through their authors' repository documentation, not their complete PDFs**. The DeepSeek-R1 author PDF was downloaded from its official repository and relevant methodology/discussion sections read. DeepInfer's pinned source and the Hugging Face/Intel dynamic-speculation article were inspected directly. Two foundational works are explicitly marked background references whose original text was unavailable; they are not counted as directly reviewed evidence. This distinction limits the strength of the literature synthesis and should remain visible in any thesis submission.

Bibliographic keys in square brackets resolve to `references.bib`. Upstream benchmark numbers are not TTGL results. We avoid transferring reported percentage savings or model rankings across task distributions.

## Evidence map

| Work | Evidence actually inspected | Relevant finding or role | Limitation for this study |
| --- | --- | --- | --- |
| Guo et al., calibration [guo2017calibration] | Author repository explanation and algorithm | Temperature scaling fits a held-out scalar to logits; confidence must be compared with empirical correctness | Original experiments concern classification; model-token probability is not coding-task correctness |
| Geifman and El-Yaniv, SelectiveNet [geifman2019selectivenet] | Author README and linked implementation scope | Prediction with a reject option makes coverage and accepted-subset risk joint objectives | README is short; no theoretical guarantee is reproduced here |
| Mozannar and Sontag, learning to defer [mozannar2020defer] | Author README, method summary and citation | Cost-sensitive learning can choose between a predictor and an expert | A larger model is an imperfect expert; task-level costs and outputs differ from the source tasks |
| Chen et al., FrugalGPT [chen2024frugalgpt] | Author README and documented cached generations/examples | Budget-aware LLM applications can use cascades and cached paired evaluations | Historical API/cache results do not establish present prices, latency or local-device performance |
| Ong et al., RouteLLM [ong2024routellm] | Author README, threshold calibration and evaluation interfaces | Preference-trained routers expose a cost/quality tradeoff; threshold calibration depends on incoming-query distribution | General-chat preferences differ from executable code correctness; model pairs and feature availability matter |
| Leviathan et al., speculative decoding [leviathan2023speculative] | Primary implementer discussion in Hugging Face/Intel article; bibliographic cross-check in implementation README | Draft generation plus target verification can accelerate autoregressive generation | Original PDF not read; token-verification guarantees cannot be transferred to whole-task routing |
| Mamou et al., dynamic speculation [mamou2024dynamic] | Full Hugging Face/Intel article and its paper citation | Draft confidence can decide when to stop drafting and verify; dynamic lookahead differs from fixed lookahead | Article reports GPU-specific measurements; these are not routing savings |
| DeepInfer [deepinfer2026] | Pinned README, confidence head, scheduling/reference code, statistics | Learned acceptance estimates and runtime cost curves allocate verification computation | Source inspection, not independent benchmark; hardware/service scope differs from laptop inference |
| Hinton et al., distillation [hinton2015distillation] | Bibliographic background only; arXiv denied | Foundational distinction between teacher/student transfer and parameter-efficient adaptation | Original text not retrieved; no numerical or experimental claim relies on it |
| Hu et al., LoRA [hu2021lora] | Author repository method description, examples and results scope | Train low-rank updates while freezing base weights | LoRA changes parameterization, not data quality; claimed latency properties depend on deployment/merging |
| Dettmers et al., QLoRA [dettmers2023qlora] | Author README overview and training configuration | Frozen quantized weights plus trainable adapters reduce fine-tuning memory | Reduced GPU-memory demand does not imply practical CPU/laptop training or universal kernel support |
| Rafailov et al., DPO [rafailov2023dpo] | Author implementation README and data/training interface | Preference learning can follow SFT using chosen/rejected response pairs | Ranking noise, distribution shift and incomplete code verifiers remain issues |
| Bai et al., Constitutional AI [bai2022constitutional] | Bibliographic background only; arXiv denied | Background for learning from AI-generated critiques/preferences | Original text not retrieved; not evidence that AI judges reliably verify code |
| Shao et al., DeepSeekMath [shao2024deepseekmath] | Official repository method/model documentation | Relevant predecessor for GRPO and reasoning post-training | Math outcomes do not establish coding-agent or low-resource training gains |
| DeepSeek-AI, DeepSeek-R1 [deepseek2025r1] | Full official PDF available; §§2.2.2, 2.3.3, 2.4, 4.1–4.2 read closely | Rule-based accuracy rewards, rejection-filtered data, SFT distillation and a distillation/RL comparison | Authors' model/data/compute regime; not a universal SFT-over-RL result |
| Chen et al., HumanEval [chen2021humaneval] | Official evaluation README, sample format and pass@k semantics | Execute generated programs against tests, retain per-sample outcomes | Small function synthesis, public historical benchmark; current repository is marked unmaintained |
| Liu et al., EvalPlus [liu2023evalplus] | Official README, test augmentation and dataset correction history | Expanded tests can reveal fragility missed by original suites | Passing stronger tests is still finite test evidence, not formal correctness |
| Jain et al., LiveCodeBench [jain2024livecodebench] | Official README and date-window evaluation instructions | Continuously collected tasks and time windows help study contamination | Release dates are proxies; known model training cutoffs and task reuse must be checked |
| Zhuo et al., BigCodeBench [zhuo2024bigcodebench] | Official README, task/format description and result-artifact schema | Diverse function calls and per-task generated-code outcomes support realistic function-level evaluation | Library-rich functions do not replace repository-level agent evaluation |
| Jimenez et al., SWE-bench [jimenez2024swebench] | Official README, task/evaluation workflow and resource guidance | Repository issues and executable regression checks broaden external validity | Environment setup, retrieval and harness choices confound model comparisons; substantially heavier execution |

## 1. Routing is selective prediction with an imperfect alternative

A useful formalization observes task features `x`, model outputs `a_s` and `a_l`, task acceptance labels `y_s,y_l ∈ {0,1}`, and model/verification costs. A router chooses the small or large model, or a cascade that first observes the small model's work. The object of interest is the **system's accepted work per unit resource**, not the small model's confidence in isolation.

Selective prediction separates coverage—the fraction handled without deferral—from risk conditional on acceptance [geifman2019selectivenet]. Learning-to-defer explicitly models a downstream expert [mozannar2020defer]. Together, they motivate reporting both local coverage and correctness on that coverage. A policy can appear cheaper simply by refusing escalation; that is not an improvement unless quality remains acceptable.

The larger model should not be assumed to dominate on every task. If both models' fixed outputs are available, the four outcome cells `(0,0), (0,1), (1,0), (1,1)` reveal complementarity. A router trained only to detect small-model failure ignores cases where remote escalation cannot help or makes the answer worse. A more aligned target estimates the conditional gain `E[y_l-y_s | x]`, adjusted for resource cost. Small-model success prediction remains a useful, simpler baseline.

FrugalGPT and RouteLLM show why cascades and routing are distinct [chen2024frugalgpt; ong2024routellm]. A prompt-only router decides before paying for generation. A cascade can inspect local output and test feedback, but must count the local attempt, verification, and any duplicated remote work. These feature/cost budgets must not be mixed in one table without labels. An oracle that reads held-out correctness labels is an upper bound, never a deployable router.

**Experiment consequence:** compare small-only, large-only, random routing at matched remote-use budgets, a prompt-feature classifier, and an output-aware cascade when such features are available. Add an oracle ceiling to quantify remaining opportunity. Use paired outcomes on the same task IDs and generation configuration. Do not attribute differences between unrelated model evaluations to routing alone.

## 2. Confidence requires calibration and an explicit target

Temperature scaling illustrates the difference between a score that ranks examples and a probability that estimates correctness [guo2017calibration]. A classifier can rank tasks well while being overconfident; conversely, a near-constant base-rate prediction can be reasonably calibrated but useless for routing. Therefore discrimination, calibration, and operational performance need separate measures.

For coding, token softmax probability is about the next token under a language model; it is not directly the chance that the final program passes unseen tests. Natural-language self-confidence has the same mismatch plus prompt sensitivity. Confidence should be trained or calibrated against the actual outcome: accepted local solution, expected remote improvement, or probability that verification misses an error. Inputs may include task text, requirements, syntax validity, tool failures and observed test results, provided those observations would exist before the real decision.

Report Brier score and reliability diagrams for probabilistic correctness predictions, plus AUROC/precision-recall only when the class balance and target make them meaningful. Expected calibration error is sensitive to binning and sample size; it should not be the only calibration measure. Risk/coverage and quality/remote-use curves directly describe the product tradeoff.

**Experiment consequence:** keep training, calibration/threshold selection, and final evaluation disjoint. A threshold chosen to meet a validation budget or quality tolerance is not a test-set guarantee. Recalibrate after student training, quantization changes or hardware/context policy changes. Assess uncertainty at the task level; repeating bootstrap resamples does not create new independent tasks.

## 3. What transfers from speculative decoding—and what does not

Speculative decoding generates cheap draft tokens and asks the target model to verify them [leviathan2023speculative]. The Hugging Face/Intel dynamic-speculation implementation stops drafting when draft confidence falls below a threshold, while its related DISCO work uses a classifier to decide lookahead [mamou2024dynamic]. The article explicitly reports some model/task combinations where heuristics slow execution, which argues for measuring the complete cost instead of assuming a universal speedup.

DeepInfer provides a stronger implementation analogue. At commit `553741557a57df44a46fb3ab72b6aafeaf945337`, a learned confidence head predicts token acceptance; cumulative estimates describe draft-prefix survival; the scheduler combines these with runtime curves and allocates a verification budget [deepinfer2026]. Acceptance and confidence-error statistics close the measurement loop. Its historical scheduling dependencies matter to the method, so a generic “if confidence is high, trust the answer” rule is not an implementation of DeepInfer.

The transferable idea is **expected useful work per unit compute, calibrated with feedback**. The non-transferable guarantee is token-distribution preservation: an entire local patch is not a draft token sampled and corrected by a target verifier. Arbitrary code checks can miss bugs, and remote reviewers can agree on a wrong answer. Likewise, multiplying marginal success scores across coding subtasks assumes dependencies that the evidence does not justify.

**Experiment consequence:** identify the proposed method as confidence-aware task routing inspired by speculative scheduling. Do not label it “lossless speculative decoding.” Separate the study of router quality from a future experiment on token-level inference acceleration. Measure whether adding output/test features improves routing enough to pay their acquisition cost.

## 4. Distillation, LoRA and RLAIF answer different questions

Distillation transfers behavior from a teacher to a student; LoRA and QLoRA determine how parameters are adapted [hinton2015distillation; hu2021lora; dettmers2023qlora]. An adapter trained on teacher outputs is not evidence of useful transfer until performance improves on disjoint tasks. Reducing training memory also does not establish free training or practical on-device updates.

DeepSeek-R1 gives directly inspected evidence for a staged approach. The paper's §2.2.2 uses rule-based accuracy rewards for reasoning/code and reports avoiding neural reward models in R1-Zero because of reward-hacking and training-complexity concerns. §2.3.3 filters multiple generated responses and combines reasoning/non-reasoning examples. §2.4 states that the released distilled models receive SFT without an RL stage. Its §4.1 comparison favors distillation over a specific direct-RL setting, supporting a strong SFT baseline but not a universal theorem about every student or dataset [deepseek2025r1].

DPO operates on preferred/rejected response pairs and the reference implementation recommends an SFT stage first [rafailov2023dpo]. Preference labels can be human, AI-generated or test-derived. RLAIF describes the source of feedback; it is not synonymous with DPO, GRPO or all reinforcement learning. For code, a unit-test reward is a verifiable reward, while a model's judgment of maintainability is AI feedback. These should be recorded separately even if combined in a later objective [bai2022constitutional; shao2024deepseekmath; deepseek2025r1].

Teacher failures and selection bias complicate the feedback loop. Training only on escalated failures concentrates difficult examples and misses the routine local distribution. Training only on easy verified teacher successes can produce the opposite bias. Student training should mix verified new examples with retained capabilities, log sampling probabilities where applicable, and evaluate both new-task transfer and forgetting. Model outputs, task IDs, or tests from the final evaluation split must not enter training or threshold selection.

**Experiment consequence:** use a factorial sequence: frozen student; SFT on a fixed verified teacher dataset; optionally SFT plus DPO from fixed preference pairs. Hold base model, split, training budget and evaluation protocol constant. An online-RL extension requires its own compute budget, reward specification and ablations. Record training, teacher generation, verification and distribution cost. A router replay experiment cannot substitute for training a language model, and updating a tabular router is not Qwen distillation.

## 5. Code benchmarks define the scope of the conclusion

HumanEval makes functional correctness operational through executable tasks and per-sample outcomes [chen2021humaneval]. EvalPlus strengthens the test suites and documents fixes that can change scores [liu2023evalplus]. This makes benchmark version, test version and timeout policy part of the experimental treatment. A sample that fails because a required library is missing is not automatically a model reasoning failure.

BigCodeBench expands function-level tasks toward diverse libraries and complex instructions, while SWE-bench evaluates repository-level issue resolution [zhuo2024bigcodebench; jimenez2024swebench]. A successful routing result on short Python functions is evidence about that task distribution. It does not establish reliability for multi-file agent trajectories, dependency installation, long-running workspaces or customer acceptance. Conversely, repository experiments introduce harness and environment confounds that should be fixed across model conditions.

LiveCodeBench's temporal windows are useful for contamination-aware evaluation [jain2024livecodebench]. However, a benchmark described as “contamination free” is not automatically unseen by every future model. Compare release dates with the selected checkpoint's documented training window and acknowledge uncertainty. Deduplicate across train/calibration/test by task family and repository when those groups exist, not just exact text. Public historical output replay has additional limits: generation randomness, prompts and model revisions may already be fixed, and latency/energy cannot be recovered from outcome labels.

**Experiment consequence:** preserve original artifacts and hashes, record missingness, fix one benchmark version, and exclude or categorize infrastructure failures before comparing policies. Use task-level paired bootstrap confidence intervals and a paired test such as McNemar for binary completion changes when its assumptions fit. Report multiple exploratory comparisons as exploratory or apply a stated multiplicity correction. A failure to detect a difference is not evidence of equivalence or non-inferiority.

## Synthesis and thesis contribution

Prior work already establishes routing frameworks, selective prediction, parameter-efficient tuning and AI-feedback training. The defensible research contribution is therefore not “inventing routing” or assuming a confidence score solves it. It is a controlled evaluation of **how well calibrated, low-overhead routing transfers to executable coding outcomes, and whether verified student adaptation increases local coverage without unacceptable quality loss**.

The core gaps are: (1) chat-preference router transfer to execution-based correctness; (2) confidence calibration under model and task-distribution changes; (3) full accounting for local generation, verification and escalation; (4) separating genuine student improvement from router retuning and benchmark leakage; and (5) external validity from isolated functions to repository tasks and real local hardware.

A resource-constrained study may rigorously answer the first three using archived paired outputs and newly trained routing models. It must describe that result as a **retrospective routing experiment**. Live Qwen inference, teacher collection, LoRA/SFT, RLAIF and device latency are separate empirical claims requiring actual runs. Unavailable compute/access does not justify synthetic results being presented as measured model performance.

## Retrieval register and primary links

All successful retrievals below occurred on 2026-10-25 through the allowed HTTPS route. Repository branches move; DeepInfer is commit-pinned. Source hashes below record retrieved document contents and can distinguish later revisions. Local temporary copies are research aids, not promised permanent archives.

| Source key | Retrieved source |
| --- | --- |
| guo2017calibration | https://github.com/gpleiss/temperature_scaling/blob/master/README.md |
| geifman2019selectivenet | https://github.com/geifmany/selectivenet/blob/master/README.md |
| mozannar2020defer | https://github.com/clinicalml/learn-to-defer/blob/master/README.md |
| chen2024frugalgpt | https://github.com/stanford-futuredata/FrugalGPT/blob/main/README.md |
| ong2024routellm | https://github.com/lm-sys/RouteLLM/blob/main/README.md |
| leviathan2023speculative / mamou2024dynamic | https://github.com/huggingface/blog/blob/main/dynamic_speculation_lookahead.md |
| deepinfer2026 | https://github.com/deepseek-ai/DeepInfer/tree/553741557a57df44a46fb3ab72b6aafeaf945337 |
| hu2021lora | https://github.com/microsoft/LoRA/blob/main/README.md |
| dettmers2023qlora | https://github.com/artidoro/qlora/blob/main/README.md |
| rafailov2023dpo | https://github.com/eric-mitchell/direct-preference-optimization/blob/main/README.md |
| shao2024deepseekmath | https://github.com/deepseek-ai/DeepSeek-Math/blob/main/README.md |
| deepseek2025r1 | https://github.com/deepseek-ai/DeepSeek-R1/blob/main/DeepSeek_R1.pdf |
| chen2021humaneval | https://github.com/openai/human-eval/blob/master/README.md |
| liu2023evalplus | https://github.com/evalplus/evalplus/blob/master/README.md |
| jain2024livecodebench | https://github.com/LiveCodeBench/LiveCodeBench/blob/main/README.md |
| zhuo2024bigcodebench | https://github.com/bigcode-project/bigcodebench/blob/main/README.md |
| jimenez2024swebench | https://github.com/SWE-bench/SWE-bench/blob/main/README.md |

Unsuccessful primary retrievals: `https://arxiv.org/abs/1503.02531` and `https://arxiv.org/abs/2212.08073` returned a proxy tunnel 403. Their background references should be revisited when scholarly full-text access is available. Other papers' linked PDFs were not assumed read merely because a README linked to them. The Mamou source uses both “Dynamic Speculation Lookahead Accelerates Speculative Decoding of Large Language Models” in its references and “Accelerating Speculative Decoding using Dynamic Speculation Length” in its BibTeX; the bibliography preserves the supplied BibTeX title for arXiv:2405.04304.

### Retrieved source SHA-256 hashes

| Source file | SHA-256 |
| --- | --- |
| calibration.txt | `a369deae4a82e3ed2a68cb4c7fac38bc04117ff88567017f4d8200f077593faf` |
| selectivenet.txt | `19d3150c45835c74675541968e6a524abc302a1e706a78581610e964145128b9` |
| defer.txt | `8edf9a9d4fc7d22e691289daed64b19968db0ecb158458862f50f0aeaf637da0` |
| frugalgpt.txt | `0d9619cb90b594c7113d88e035f6588836242ff714632a3f111bbdf6de6ff851` |
| routellm.txt | `380ebee5361b8a191d92091639bc2be08e258dd2b4404f804a680f343fa16f0c` |
| dynamic.txt | `9ff4a10dfae2dcc5ba2a3c44fbe3f5388d52c3f76e153edf784cc30a165fd8ad` |
| lora.txt | `ce0b726fedd1198ebd841093b53ff5490672ffb2264479d8be044b5826a791c6` |
| qlora.txt | `f9205f6b2572f81b8919f523176315207806357482049c96fd6471c1c6b17472` |
| dpo.txt | `d639655c1843ca1c73e09c057e06dac58f04ddf1cbe26546fb03df3a0d1237d0` |
| deepseekmath.txt | `6266dba5f54db9d34cbaf13c8116a933ba0a3f8bb81d3598b3fa220519fe1f26` |
| r1paper.pdf | `f03fc7290a99b48cb02f374b16f18a9b984a28170933111f0dde58822fdd5269` |
| humaneval.txt | `a6a3741a64527ae20026b7880e37af5de88e8ae4dcfed81eb19620c674b6e272` |
| evalplus.txt | `667f3f937cf8dfa67dd6624c24c22cb0e938c9b31179cf2e40457d2708ff2260` |
| livecodebench.txt | `ee0029cddc1d9051f35818f3348a4327819a3e35a9e597732519245605195cf6` |
| bigcodebench.txt | `4aa8cbfa3111e92db886583d554a3c9e8f14561d47261d6441c069835e3bdc28` |
| swebench.txt | `06841624d7b5130dfe3cc6714642e9a8fd2a608c95c66ae0180e409f12b73aaa` |
| deepinfer-README.md | `b55624158ada4dc21b882d24ded06bf82f65350b44d170877b68395712cd670d` |
| deepinfer-dflash.py | `12ebfb9c793062844d40e0fab17164d5365d965c318f8b9f0f4adf51b3afb684` |
| deepinfer-mtp_varlen.hpp | `164f45db4cccd6d6909dd2846e7dfffb57754b108af679443bf4bd71ec33785a` |
| deepinfer-schedule_mtp_varlen.py | `0c6e5eb4faa087b96e0558ea4791e1b4ead1939a6cc8b086de86ca2f68bd4e88` |
| deepinfer-stats_logger.py | `9ef93c3930d6dd8d889d4ba69558a85459c2210ae0714d5073c3b4328c8e7cb9` |
