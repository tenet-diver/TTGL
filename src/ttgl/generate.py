"""Generate real base/LoRA benchmark samples with HF; never execute generated code."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import time
from typing import Any

from .train import (
    SYSTEM_PROMPT, compose_user_prompt, load_rows, load_source_metadata,
    sha256_text, write_json, write_jsonl,
)


def prepare_tasks(
    rows: list[dict[str, Any]], metadata: dict[str, dict[str, str]],
    split: str = "test", max_tasks: int | None = None,
) -> list[dict[str, Any]]:
    """Build inference inputs from public metadata without reading outcome fields."""
    tasks, seen, question_ids = [], set(), set()
    if max_tasks is not None and max_tasks <= 0:
        raise ValueError("max_tasks must be positive")
    for row in rows:
        task_id = str(row.get("task_id", ""))
        if not task_id or task_id in seen:
            raise ValueError("Missing or duplicate task ID")
        seen.add(task_id)
        if row.get("split") != split:
            raise ValueError(f"Unexpected split for {task_id}; expected {split}")
        prompt = row.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"Missing prompt for {task_id}")
        enriched = compose_user_prompt(task_id, prompt, metadata)
        source = metadata[task_id]
        if source["question_id"] in question_ids:
            raise ValueError("Official evaluator question IDs must be unique across selected platforms")
        question_ids.add(source["question_id"])
        tasks.append({
            "task_id": task_id, "platform": source["platform"],
            "question_id": source["question_id"], "split": split,
            "original_prompt_sha256": sha256_text(prompt),
            "user_prompt_sha256": sha256_text(enriched),
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": enriched}],
        })
    if not tasks:
        raise ValueError("No tasks selected")
    # A pilot prefix is frozen by task ID and never selected by outcomes.
    return sorted(tasks, key=lambda x: x["task_id"])[:max_tasks]


def extract_code(output: str) -> str:
    """Match official LCB generic-chat extraction: last pair of code fences.

    Source: LiveCodeBench@28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24,
    lcb_runner/utils/extraction_utils.py. Missing fences are an extraction failure
    retained as empty code; no candidate is removed or retried based on success.
    """
    lines = output.split("\n")
    boundaries = [i for i, line in enumerate(lines) if "```" in line]
    if len(boundaries) < 2:
        return ""
    return "\n".join(lines[boundaries[-2] + 1:boundaries[-1]])


def build_custom_outputs(tasks: list[dict[str, Any]], records: list[dict[str, Any]], samples: int) -> list[dict[str, Any]]:
    """Require exact task/sample coverage, preserving empty-code failures."""
    expected = {x["task_id"] for x in tasks}
    observed: dict[str, dict[int, str]] = {key: {} for key in expected}
    for record in records:
        key, sample = record["task_id"], record["sample_index"]
        if key not in expected or sample in observed[key] or not 0 <= sample < samples:
            raise ValueError("Unexpected task, duplicate sample or out-of-range sample index")
        observed[key][sample] = record["code"]
    if any(set(values) != set(range(samples)) for values in observed.values()):
        raise ValueError("Incomplete task/sample coverage; cannot export a complete evaluation file")
    return [{"question_id": task["question_id"], "code_list": [observed[task["task_id"]][i] for i in range(samples)]}
            for task in sorted(tasks, key=lambda x: x["question_id"])]


def generate(
    tasks: list[dict[str, Any]], args: argparse.Namespace, config: dict[str, Any],
    output_dir: Path, manifest: dict[str, Any],
) -> None:
    import torch
    from huggingface_hub import model_info
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("The frozen inference setup requires a BF16-capable CUDA GPU")
    installed = {}
    for package in ("torch", "transformers", "peft"):
        installed[package] = importlib.metadata.version(package)
        if installed[package].split("+")[0] != config["package_versions"][package]:
            raise RuntimeError(f"Dependency version mismatch for {package}")
    model_id, revision = config["model_id"], args.model_revision or config["model_revision"]
    training_manifest = None
    if args.training_manifest:
        training_manifest = json.loads(args.training_manifest.read_text())
        if training_manifest.get("status") != "training_completed":
            raise ValueError("Training manifest does not document completed training")
        if training_manifest["requested_model_id"] != model_id:
            raise ValueError("Training manifest and generation model IDs differ")
        pinned_revision = training_manifest["resolved_model_revision"]
        if args.model_revision and args.model_revision != pinned_revision:
            raise ValueError("Requested base revision differs from the adapter training revision")
        revision = pinned_revision
    if args.adapter and training_manifest is None:
        raise ValueError("Adapter evaluation requires --training-manifest to align the exact base revision")
    adapter_hashes = None
    if args.adapter:
        adapter_config = json.loads((args.adapter / "adapter_config.json").read_text())
        if adapter_config.get("base_model_name_or_path") != model_id:
            raise ValueError("Adapter config names a different base model")
        adapter_hashes = {
            filename: hashlib.sha256((args.adapter / filename).read_bytes()).hexdigest()
            for filename in ("adapter_config.json", "adapter_model.safetensors")
        }
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        revision = model_info(model_id, revision=revision).sha
    if not revision or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Could not resolve an immutable model revision")
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    if not tokenizer.chat_template:
        raise ValueError("A model chat template is required")
    if training_manifest and sha256_text(tokenizer.chat_template) != training_manifest["chat_template_sha256"]:
        raise ValueError("Training/generation chat templates differ")
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id, revision=revision, trust_remote_code=False, dtype=torch.bfloat16, attn_implementation="sdpa",
    ).to("cuda")
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(args.adapter), is_trainable=False)
    model.eval()
    model.config.use_cache = True
    manifest.update({
        "status": "generation_started", "resolved_model_revision": revision,
        "chat_template_sha256": sha256_text(tokenizer.chat_template),
        "package_versions": installed, "gpu": torch.cuda.get_device_name(0),
        "cuda_version": torch.version.cuda, "generated_at": datetime.now(timezone.utc).isoformat(),
        "adapter_artifact_sha256": adapter_hashes,
        "code_evaluation": "not_run; use the official evaluator with original tests",
    })
    write_json(output_dir / "manifest.json", manifest)
    records = []
    started = time.perf_counter()
    with (output_dir / "samples.jsonl").open("w", encoding="utf-8") as journal:
        for task in tasks:
            encoded = tokenizer.apply_chat_template(
                task["messages"], tokenize=True, add_generation_prompt=True,
                return_tensors="pt", return_dict=True,
            )
            prompt_tokens = encoded["input_ids"].shape[1]
            context_limit = model.config.max_position_embeddings
            if prompt_tokens + args.max_new_tokens > context_limit:
                raise ValueError(f"Task {task['task_id']} exceeds model context; no silent truncation")
            encoded = {key: value.to("cuda") for key, value in encoded.items()}
            for sample_index in range(args.samples):
                if args.max_wall_seconds and time.perf_counter() - started > args.max_wall_seconds:
                    raise TimeoutError("Generation wall-time limit reached; partial samples retained")
                sample_seed = int(sha256_text(f"generation:{args.seed}:{task['task_id']}:{sample_index}"), 16) % (2**32)
                set_seed(sample_seed)
                kwargs = {"do_sample": args.temperature > 0, "max_new_tokens": args.max_new_tokens,
                          "pad_token_id": tokenizer.pad_token_id, "eos_token_id": tokenizer.eos_token_id}
                if args.temperature > 0:
                    kwargs.update(temperature=args.temperature, top_p=args.top_p)
                torch.cuda.synchronize()
                sample_start = time.perf_counter()
                with torch.inference_mode():
                    result = model.generate(**encoded, **kwargs)
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - sample_start
                new_ids = result[0, prompt_tokens:]
                output = tokenizer.decode(new_ids, skip_special_tokens=True)
                code = extract_code(output)
                record = {
                    "task_id": task["task_id"], "question_id": task["question_id"],
                    "platform": task["platform"], "sample_index": sample_index, "seed": sample_seed,
                    "input_tokens": prompt_tokens, "output_tokens": int(new_ids.numel()),
                    "generation_seconds": elapsed, "output": output, "code": code,
                    "empty_code": not bool(code.strip()),
                    "hit_generation_limit": int(new_ids.numel()) == args.max_new_tokens,
                }
                records.append(record)
                journal.write(json.dumps(record, ensure_ascii=False) + "\n")
                journal.flush()
            print(json.dumps({"completed_task": task["task_id"], "samples": args.samples}), flush=True)
    custom = build_custom_outputs(tasks, records, args.samples)
    write_json(output_dir / "custom_outputs.json", custom)
    manifest.update({
        "status": "generation_completed", "generated_samples": len(records),
        "empty_code_samples": sum(x["empty_code"] for x in records),
        "output_tokens": sum(x["output_tokens"] for x in records),
        "generation_seconds": sum(x["generation_seconds"] for x in records),
        "wall_seconds": time.perf_counter() - started,
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "custom_outputs_sha256": hashlib.sha256((output_dir / "custom_outputs.json").read_bytes()).hexdigest(),
    })
    write_json(output_dir / "manifest.json", manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/training-sft.json"))
    parser.add_argument("--source-metadata", type=Path)
    parser.add_argument("--source-sha256")
    parser.add_argument("--split", choices=["test", "calibration"], default="test")
    parser.add_argument("--model-revision")
    parser.add_argument("--training-manifest", type=Path)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument("--max-new-tokens", type=int, default=2000)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--max-wall-seconds", type=float)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if args.samples <= 0 or args.max_new_tokens <= 0 or args.temperature < 0 or not 0 < args.top_p <= 1:
        raise ValueError("Invalid generation settings")
    if args.max_wall_seconds is not None and args.max_wall_seconds <= 0:
        raise ValueError("Wall-time limit must be positive")
    if args.adapter and not args.adapter.is_dir():
        raise ValueError("Adapter directory does not exist")
    config = json.loads(args.config.read_text())
    source_path = args.source_metadata or Path(config["source_metadata"])
    source_hash = args.source_sha256 or config["source_sha256"]
    metadata = load_source_metadata(source_path, source_hash)
    tasks = prepare_tasks(load_rows(args.dataset), metadata, args.split, args.max_tasks)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.output_dir / "tasks.jsonl", tasks)
    manifest = {
        "status": "prepared_not_generated", "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "source_metadata_sha256": source_hash, "source_metadata": str(source_path),
        "task_count": len(tasks), "task_ids": [x["task_id"] for x in tasks],
        "task_ids_sha256": sha256_text("\n".join(x["task_id"] for x in tasks)),
        "split": args.split, "pilot_subset": args.max_tasks is not None,
        "requested_model_id": config["model_id"], "adapter": str(args.adapter) if args.adapter else None,
        "samples_per_task": args.samples, "seed": args.seed,
        "temperature": args.temperature, "top_p": args.top_p, "max_new_tokens": args.max_new_tokens,
        "training_manifest": str(args.training_manifest) if args.training_manifest else None,
        "code_evaluation": "not_run",
    }
    write_json(args.output_dir / "manifest.json", manifest)
    if args.run:
        try:
            generate(tasks, args, config, args.output_dir, manifest)
        except Exception as exc:
            manifest["status"] = "generation_failed_or_incomplete"
            manifest["failure_type"] = type(exc).__name__
            write_json(args.output_dir / "manifest.json", manifest)
            raise
    print(json.dumps({"status": manifest["status"], "task_count": len(tasks), "samples_per_task": args.samples}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
