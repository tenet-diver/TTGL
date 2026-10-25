# TTGL thesis experiment: routing, distillation and measured results

Status: CPU routing study completed; GPU training and fresh inference pending secure connection. Target space: [FASTEST](https://fastestswarm.atlassian.net/wiki/spaces/FASTEST). This is a prepared publication draft; no Confluence page has been created.

## Research question

Can a calibrated, inexpensive router delegate local-Qwen coding tasks to a stronger model more effectively than random allocation at the same remote-call budget? Does subsequent verified-teacher distillation improve the student's local coverage? The second question requires actual student training and remains unmeasured.

## Completed experiment

We acquired 713 shared tasks from the official LiveCodeBench submissions for Qwen2.5-Coder-Instruct-7B and DeepSeek-V3, ten published generations per model/task. Sources are pinned to commit `6ca212e9c2039373f6e5069d37ffa9db66e23736` and verified by SHA-256. Complete contests were split chronologically into 429 training, 142 calibration and 142 test tasks. The test set contains 34 contests.

A protocol and implementation amendment were frozen before aggregate outcome inspection. The router uses statement TF-IDF and length, fits separate local/remote success models, calibrates on a disjoint split and ranks predicted remote-minus-local benefit. Official difficulty and execution feedback are excluded from features. The primary budget sends exactly half the test tasks to the remote model.

| Policy | Remote calls | Empirical pass@1 |
| --- | ---: | ---: |
| Qwen only | 0% | 17.32% |
| Expected random | 50% | 28.35% |
| Prompt-length rule | 50% | 26.62% |
| Local-failure router | 50% | 26.13% |
| Expected-benefit router | 50% | 29.93% |
| DeepSeek only | 100% | 39.37% |

The primary difference is **+1.58 percentage points, 95% paired contest-bootstrap CI −1.58 to +4.44**. This run does not establish a gain over random. The router also fails the exploratory five-point noninferiority criterion against remote-only. No post-hoc model or budget replaced the primary comparison.

These are retrospective published-output results. They are not new Qwen generations, quantized laptop performance, measured inference costs or evidence of successful distillation. Strong remote overconfidence under temporal shift is a key finding: average predicted remote correctness was 59.82%, observed 39.37%.

## Implemented training and evaluation pipeline

The TRL/PEFT LoRA pipeline selects one verified teacher solution per original training task, preserves interfaces through hash-checked public metadata, and excludes held-out tasks. Preparation produced 334 demonstrations from 429 tasks. It resolves immutable model/tokenizer revisions and records explicit prepared/failed/completed status.

The inference runner uses the same prompt construction for base and adapter, aligns exact base revisions, records tokens/latency and exports the official LiveCodeBench evaluator format with strict task/sample alignment. Official benchmark test fixtures are required separately.

The main software suite passed 38 tests. A separate real CPU integration test on a tiny random model verified completion-only loss, two LoRA optimization steps and adapter save/reload. That fixture is not a pretrained-model research result. Fresh download and rerun reproduced the metrics exactly; an independent audit reproduced the primary interval and found no material implementation error.

## Remaining work and state

- Runpod: user selected one 80 GB GPU and a **US$100 total ceiling**. SDK installed, payload staged and data preflight passed. No pod provisioned and no spend incurred. Secure `RUNPOD_API_KEY` and runtime access remain missing.
- GPU study: train Qwen 1.5B on verified teacher demonstrations and compare base versus adapter on untouched tasks with the official tests. No training or fresh-inference results yet.
- Logit distillation/RLAIF: designed as later controlled comparisons; full-vocabulary KL needs compatible tokenization. DeepSeek-to-Qwen solution distillation does not require logits.
- Jira/Confluence: Atlassian MCP tools are not exposed to this session. Work-item states and a Jira CSV are retained locally for reconciliation; no remote issue keys or publication are claimed.

The repository contains a 20-reference narrative literature review, explicit evidence-access limitations, frozen protocol, source manifests, code, tests, plots, result tables, independent audit and reproducibility instructions. No full-paper systematic-review coverage is claimed.

## Primary source links

- [LiveCodeBench submissions](https://github.com/LiveCodeBench/submissions/tree/6ca212e9c2039373f6e5069d37ffa9db66e23736).
- [RouteLLM](https://github.com/lm-sys/RouteLLM).
- [DeepInfer confidence-scheduled verification](https://github.com/deepseek-ai/DeepInfer/tree/553741557a57df44a46fb3ab72b6aafeaf945337).
- [TRL](https://github.com/huggingface/trl), [PEFT](https://github.com/huggingface/peft), [Runpod SDK](https://github.com/runpod/runpod-python).

Project principles: reuse maintained existing software, distinguish measured findings from proposals, and preserve the user's guiding words: **“Believe in me who believes in you.”**
