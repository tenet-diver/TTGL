# GPU distillation experiment

Status: preparation implemented and CPU data-validation tests executed; no GPU training or fresh held-out code evaluation has run in this environment. A dry run writes `prepared_not_trained`. Only a completed real TRL job writes `training_completed`.

## What requires logits?

The first arm is **sequence-level distillation**: fine-tune a small Qwen model on teacher solutions that passed the published benchmark tests. It needs solution text and provenance, not logits. DeepSeek-generated solutions can train a Qwen student even though their tokenizers differ.

An additional **token-level distillation** arm would compare the same student's probabilities against a frozen teacher distribution. A conventional objective is `L = alpha * CE(y, p_student) + (1-alpha) * T^2 * KL(p_teacher(T) || p_student(T))`, applied to completion tokens. This requires corresponding token events and correctly masked positions. Start with Qwen2.5-Coder-7B-Instruct and Qwen2.5-Coder-1.5B-Instruct only after comparing complete token-to-ID vocabularies, special tokens and chat templates. Being in the same family is not proof of exact compatibility. A DeepSeek-to-Qwen KL over raw vocabulary indices is invalid.

An API's chosen-token or top-k log probabilities do not supply the full teacher distribution. Truncated distributions require a separately specified approximation and omitted-mass treatment. They must not be reported as full-vocabulary KL. In a controlled job, run the frozen Qwen teacher locally in evaluation/no-grad mode and process logits in batches/chunks using established tooling. At vocabulary size 151,936 and sequence length 4,096, a single BF16 full-vocabulary logits tensor alone occupies about 1.24 GB; cached distributions become expensive quickly. These are arithmetic estimates, not measured GPU requirements.

The implemented code deliberately runs the simpler SFT arm. Token-KL and RLAIF are planned comparisons, not results or hidden substitutes for SFT.

## Hardware and deployment

Use one existing A100 80 GB or H100 80 GB instance on Runpod or Nebius, preferably whichever account is already available. The initial 1.5B LoRA job should need substantially less than 80 GB, but that capacity leaves room for a later 7B teacher and avoids selecting a small device before measuring memory. No hourly price, provisioning, or GPU availability has been verified; this document does not authorize an unbounded rental. The job records GPU name, memory, CUDA version and peak allocated memory.

Use an existing CUDA/PyTorch environment and a dedicated virtual environment. The source implementation was inspected against TRL 0.23.1 and PyPI dependency metadata. The actual GPU dependency combination has not yet been installed/executed here; the runtime checks the pinned versions before training.

```bash
python -m venv .venv-gpu
. .venv-gpu/bin/activate
python -m pip install \
  torch==2.8.0 transformers==4.56.2 trl==0.23.1 \
  peft==0.17.1 accelerate==1.10.1 datasets==4.1.1
```

Use the CUDA wheel compatible with the provider driver; preserve package/TLS verification. Do not install optional audio/vision packages for this text-only job. `pip check` and `python -c 'import torch; print(torch.cuda.is_available())'` must succeed before a paid training run. Record a full `pip freeze` with the artifacts. Default Hugging Face caches may require additional disk beyond the adapter output, so allocate sufficient persistent storage and use an appropriate `HF_HOME`.

## Dataset contract and leakage controls

`python -m ttgl.train` consumes JSONL with these fields:

```json
{
  "task_id": "platform:question_id",
  "prompt": "The original problem statement and public examples",
  "teacher_outputs": ["first complete code sample", "second sample"],
  "teacher_grades": [true, false],
  "split": "train",
  "teacher_model": "DeepSeek-V3",
  "source_revision": "6ca212e9c2039373f6e5069d37ffa9db66e23736",
  "source_url": "The pinned upstream file URL"
}
```

Use the frozen chronological training split from the routing study. A mixed train/calibration/test file is rejected, rather than quietly filtered. Duplicate IDs, empty prompts, nonboolean grades and unaligned outputs are errors. From every training task with at least one nonempty passing solution, select one solution using a per-task seeded draw, stable under row reordering. Unsolved tasks are excluded with explicit counts and IDs. Every retained task receives equal representation; tasks with many passing samples are not repeated more often.

The original prompt and completion become a standard conversational prompt-completion dataset. Training loss applies only to the completion via TRL's `completion_only_loss=True`; prompt labels do not provide a cheap loss reduction. Code is wrapped in a Python code fence when the published output is raw code. Benchmark hidden tests, grades and execution feedback do not enter the prompt. The historical grades are trusted as published evidence and are not described as newly executed validation.

Training and generation also read the pinned raw `DeepSeek-V3.json` metadata through `--source-metadata` (configured by default in `training-sft.json`). Its SHA256 is verified against `88548117b84bf567fdadb159cfc65f9c0a6bf7da8b2fe5679829c95334abd661`; only platform, question ID, original statement, title and starter code are retained. Each task's original statement must equal the frozen processed prompt exactly. Public starter code is appended with an instruction to preserve the class/function interface. This matters for functional LeetCode-style tasks and keeps inference/training prompts aligned. No outcomes from non-training tasks enter SFT, and the frozen routing files remain unchanged. Raw-file path/hash may be overridden explicitly with `--source-metadata` and `--source-sha256`; the training CLI rejects a real run without verified interface metadata.

Every example records the task, source revision, selected sample index, teacher identity, prompt hash and output hash. The input file and configuration are also hashed. The public benchmark and teacher may have pretraining contamination; chronological train/test partitioning prevents our fine-tuning leakage but cannot erase pretraining exposure. These are algorithmic code-generation tasks, not full repository-agent trajectories. Keep conclusions within that scope.

## Run preparation

From the repository root, use the generated training JSONL path from the data manifest:

```bash
PYTHONPATH=src python -m ttgl.train \
  --dataset data/processed/train.jsonl \
  --config configs/training-sft.json \
  --output-dir results/gpu/prepared-seed1729 \
  --dry-run
```

Preparation needs no model downloads or GPU packages. It writes the selected examples and manifest but does not tokenize, train, evaluate a model or claim improvement. Use a new output directory for every run; the CLI refuses to overwrite existing evidence. The executed CPU preparation in `artifacts/training-pilot-with-interfaces/` retained 334 of 429 original-training tasks and explicitly recorded 95 tasks without a nonempty passing teacher solution. It supersedes the earlier prompt-only preparation in `artifacts/training-pilot/`, whose evidence was preserved. These are dataset preparation counts, not training or model-quality results.

## Run actual SFT

```bash
PYTHONPATH=src python -m ttgl.train \
  --dataset data/processed/train.jsonl \
  --config configs/training-sft.json \
  --output-dir results/gpu/sft-seed1729 \
  --run
```

The fixed configuration uses Qwen2.5-Coder-1.5B-Instruct, LoRA rank 16/alpha 32/dropout 0.05 on the attention and MLP projections, BF16, SDPA attention, sequence limit 4,096, batch size 1, accumulation 16, two epochs, learning rate 1e-4 and seed 1729. These are preregistered starting settings, not tuned to test results. A moving model alias is resolved once to an immutable Hub commit, used for both weights and tokenizer and recorded in the manifest. Reproduce a completed run by setting `model_revision` to that recorded commit rather than resolving `main` again.

Examples longer than the sequence limit are excluded and listed rather than truncated into partial solutions. The remaining original-training tasks supply a deterministic 90/10 internal split solely for loss monitoring. The routing calibration and test sets are never used by this job. If fewer than ten complete examples fit, it fails instead of running an uninformative job. Training produces a final adapter; it does not choose checkpoints using held-out benchmark accuracy.

Artifacts include `verified_examples.jsonl`, `fit_examples.jsonl`, `internal_validation_examples.jsonl`, `excluded_overlong.json`, `training_config.json`, `trainer_log_history.json`, `adapter/` and `manifest.json`. The manifest records actual train metrics, internal-validation loss, runtime and memory only after successful training. Any failure records `training_failed`. `heldout_code_evaluation` remains `not_run_by_this_job`: training loss is not a task-success result.

## Required evaluation after training

Run fresh baseline and adapter inference for **the same 1.5B model** on the frozen held-out tasks, with the same tokenizer revision, prompt template, decoding settings, sample count and independent seeds. Execute generated code through the existing LiveCodeBench evaluation harness in an isolated worker with limits. Record actual per-task samples, pass/fail grades, generation times, tokens and evaluator revision. The prior replay uses 7B Qwen outputs; it cannot serve as the untrained 1.5B baseline.

The implemented generation CLI reuses Transformers and PEFT. It reads only task IDs, split, original problem statement and public source metadata; historical outcomes cannot affect prompts or task selection. The base and adapted runs below load the same immutable model/tokenizer revision from the completed training manifest. Per-task/sample RNG seeds are reproducible and shared between arms; inference uses ten samples at temperature 0.2/top-p 0.95 with a 2,000-new-token cap. The measured timing is sequential single-request generation on the selected GPU, not a serving-throughput benchmark.

```bash
PYTHONPATH=src python -m ttgl.generate \
  --dataset data/processed/test.jsonl \
  --config configs/training-sft.json \
  --training-manifest results/gpu/sft-seed1729/manifest.json \
  --output-dir results/gpu/base-generation --samples 10 --run

PYTHONPATH=src python -m ttgl.generate \
  --dataset data/processed/test.jsonl \
  --config configs/training-sft.json \
  --training-manifest results/gpu/sft-seed1729/manifest.json \
  --adapter results/gpu/sft-seed1729/adapter \
  --output-dir results/gpu/sft-generation --samples 10 --run
```

For a declared smoke pilot, add `--max-tasks 5 --samples 1`; that output is explicitly marked as a subset and cannot establish held-out study results. `--max-wall-seconds` stops a long job while retaining its partial journal; its manifest records incomplete generation and does not export a falsely complete evaluation file. A source-only preflight with `--dry-run` has executed for all 142 held-out tasks in `artifacts/generation-preflight/`; this is prompt/interface validation, not model inference.

The generator writes full raw outputs, code extracted with the official LiveCodeBench last-fenced-block rule, measured input/output tokens, CUDA-synchronized per-sample times and exact task IDs. It keeps missing/empty-code outputs as failures and never retries based on quality. Only complete task/sample coverage produces `custom_outputs.json`. Adapter files, input data, prompt template and model revision are hashed. Generated code is never executed by the inference process. Original benchmark tests and the official evaluator remain a separate required step.

The official evaluator was inspected at commit `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24`. It needs the original `livecodebench/code_generation_lite` Hugging Face dataset containing public/private test cases; published submissions provide outcomes but do not contain those tests. Its loader executes a dataset script via `trust_remote_code=True`; review and pin that dataset script/revision in the isolated evaluation environment. Keep this environment separate from training: the inspected loader needs the datasets 3.x script-support interface, whereas the training stack pins datasets 4.1.1. Do not silently upgrade the evaluation dataset or reuse existing result files.

The existing custom-evaluation interface accepts JSON of the form `[{"question_id":"abc400_a", "code_list":["complete Python sample 1", "sample 2"]}]`. From a pinned official evaluation checkout, its supported invocation is:

```bash
python -m lcb_runner.runner.custom_evaluator \
  --scenario codegeneration \
  --release_version release_v4 \
  --start_date "$TTGL_TEST_START_DATE" \
  --end_date "$TTGL_TEST_END_DATE" \
  --custom_output_file "$TTGL_OUTPUTS_JSON" \
  --num_process_evaluate 4 --timeout 6
```

Set the dates from `data/processed/split-manifest.json`; verify that the selected release/window contains exactly the frozen platform/question IDs before executing this command. Release v4 is a candidate matching the historical period, not a dataset alignment verified in this session. Date filters alone may include additional tasks or omit boundary tasks; if the sets differ, select the frozen IDs through the existing `codegen_metrics` Python API rather than treating them as interchangeable. The upstream custom evaluator sorts by question ID and checks counts but does not prove ID correspondence, so an explicit exact-ID check is mandatory. These commands are source-verified instructions; they have not yet executed against downloaded tests. Record per-task outcomes from the new `_eval_all.json`, not merely the process exit status.

Compare base versus verified SFT using paired task/contest-level analysis and confidence intervals. Repeat training for separately declared seeds before making claims about variance; teacher example selection, data shuffling and LoRA initialization must be tracked separately. Evaluate and recalibrate the router against the new student's outcomes without retraining on test tasks. A second teacher-output selection policy or a higher data volume is a new experimental arm, not a silent change to this run.

Only after that baseline should the study add token-KL or AI-ranked DPO. To isolate the effect of logits, token-KL and sequence SFT must use matched teacher/student identities, prompts, examples and compute budgets; changing from a DeepSeek text teacher to Qwen7B simultaneously confounds teacher quality with the loss. For RLAIF, freeze the judge rubric and use independent code execution; report judge calls and training cost, not just API savings.

## Sources inspected

- [Official archived Qwen2.5-Coder model catalog](https://github.com/QwenLM/Qwen2.5-Coder/blob/d5ead97fea36bca3744e1a4c49e882f6fa2f406a/README.md) lists the exact 1.5B/7B Instruct model IDs. Their full current model cards/licenses were inaccessible in this environment and require verification before deployment.
- [TRL 0.23.1 SFT configuration](https://github.com/huggingface/trl/blob/v0.23.1/trl/trainer/sft_config.py) and [trainer](https://github.com/huggingface/trl/blob/v0.23.1/trl/trainer/sft_trainer.py) establish the completion-loss, max-length and PEFT interface used here.
- [PEFT](https://github.com/huggingface/peft) provides the existing LoRA implementation. Package requirements were checked against PyPI metadata on 2026-10-25.
- [Pinned LiveCodeBench custom evaluator](https://github.com/LiveCodeBench/LiveCodeBench/blob/28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24/lcb_runner/runner/custom_evaluator.py), [argument parser](https://github.com/LiveCodeBench/LiveCodeBench/blob/28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24/lcb_runner/runner/parser.py) and [original test-dataset loader](https://github.com/LiveCodeBench/LiveCodeBench/blob/28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24/lcb_runner/benchmarks/code_generation.py).
