"""Prepare verified teacher demonstrations and run an optional TRL LoRA SFT job.

Preparation uses only Python's standard library. GPU dependencies are imported
only with --run; a successful dry run is never recorded as model training.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import re
import sys
from typing import Any


DEFAULT_TEACHER = "DeepSeek-V3"
SYSTEM_PROMPT = (
    "You are a coding assistant. Solve the programming problem in Python. "
    "Return a complete solution in a Python code block."
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at line {line_number}") from exc
                if not isinstance(row, dict):
                    raise ValueError(f"Expected object at line {line_number}")
                rows.append(row)
    if not rows:
        raise ValueError("Dataset is empty")
    return rows


def load_source_metadata(path: Path, expected_sha256: str) -> dict[str, dict[str, str]]:
    """Read only public task metadata from a hash-pinned benchmark source.

    Labels, generated solutions and evaluator metadata are deliberately omitted
    from the returned structure so held-out metadata cannot become supervision.
    """
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Source metadata file does not match its pinned SHA256")
    records = json.loads(raw)
    if not isinstance(records, list):
        raise ValueError("Expected a list of upstream task records")
    result = {}
    for record in records:
        platform, question_id = str(record.get("platform", "")), str(record.get("question_id", ""))
        if not platform or not question_id:
            raise ValueError("Source metadata lacks platform/question ID")
        task_id = f"{platform}:{question_id}"
        if task_id in result:
            raise ValueError(f"Duplicate source metadata task: {task_id}")
        selected = {
            "platform": platform,
            "question_id": question_id,
            "prompt": record.get("question_content"),
            "title": record.get("question_title", ""),
            "starter_code": record.get("starter_code", ""),
        }
        if any(not isinstance(value, str) for value in selected.values()):
            raise ValueError(f"Malformed public source metadata for {task_id}")
        result[task_id] = selected
    return result


def compose_user_prompt(task_id: str, prompt: str, metadata: dict[str, dict[str, str]]) -> str:
    """Keep problem wording intact and restore the required public interface."""
    if task_id not in metadata:
        raise ValueError(f"No source metadata found for {task_id}")
    source = metadata[task_id]
    if source["prompt"] != prompt:
        raise ValueError(f"Original prompt does not match pinned source for {task_id}")
    content = f"Problem: {source['title']}\n\n{prompt}" if source["title"] else prompt
    if source["starter_code"].strip():
        content += (
            "\n\nComplete the starter code below, preserving its class and function signatures "
            "and required interface. Include any necessary imports.\n\n```python\n"
            + source["starter_code"].rstrip()
            + "\n```"
        )
    return content


def prepare_examples(
    rows: list[dict[str, Any]], seed: int = 1729, teacher_model: str = DEFAULT_TEACHER,
    source_metadata: dict[str, dict[str, str]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select one nonempty, verified teacher solution per training task.

    A mixed-split file is rejected, not silently filtered. Selection is stable
    under row reordering, and every retained task contributes exactly once.
    """
    seen: set[str] = set()
    examples = []
    skipped = []
    for row in rows:
        task_id = str(row.get("task_id", "")).strip()
        if not task_id:
            raise ValueError("Every row needs a nonempty task_id")
        if task_id in seen:
            raise ValueError(f"Duplicate task_id: {task_id}")
        seen.add(task_id)
        if row.get("split") != "train":
            raise ValueError(f"Refusing non-training task {task_id}")
        prompt = row.get("prompt")
        outputs, grades = row.get("teacher_outputs"), row.get("teacher_grades")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"Missing prompt for {task_id}")
        user_prompt = compose_user_prompt(task_id, prompt, source_metadata) if source_metadata is not None else prompt
        if not isinstance(outputs, list) or not isinstance(grades, list) or len(outputs) != len(grades):
            raise ValueError(f"Unaligned teacher outputs/grades for {task_id}")
        if not outputs or any(not isinstance(x, str) for x in outputs):
            raise ValueError(f"Teacher outputs must be a nonempty string list for {task_id}")
        if any(type(x) is not bool for x in grades):
            raise ValueError(f"Teacher grades must be booleans for {task_id}")
        candidates = [i for i, (text, grade) in enumerate(zip(outputs, grades)) if grade and text.strip()]
        if not candidates:
            skipped.append(task_id)
            continue
        task_seed = int(sha256_text(f"{seed}:{task_id}"), 16)
        selected = random.Random(task_seed).choice(candidates)
        solution = outputs[selected].strip()
        completion = solution if solution.startswith("```") else f"```python\n{solution}\n```"
        examples.append(
            {
                "task_id": task_id,
                "prompt": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "completion": [{"role": "assistant", "content": completion}],
                "provenance": {
                    "split": "train",
                    "teacher_model": row.get("teacher_model", teacher_model),
                    "source_revision": row.get("source_revision"),
                    "source_url": row.get("source_url"),
                    "selected_sample_index": selected,
                    "upstream_test_passed": True,
                    "prompt_sha256": sha256_text(prompt),
                    "training_user_prompt_sha256": sha256_text(user_prompt),
                    "interface_metadata": "hash_verified_source" if source_metadata is not None else "not_supplied",
                    "teacher_output_sha256": sha256_text(outputs[selected]),
                    "verification": "published benchmark grade; not re-executed by this preparation job",
                },
            }
        )
    if not examples:
        raise ValueError("No nonempty verified teacher solution exists in the training split")
    examples.sort(key=lambda x: x["task_id"])
    return examples, {
        "input_task_count": len(rows),
        "retained_task_count": len(examples),
        "skipped_without_verified_solution_count": len(skipped),
        "skipped_task_ids": sorted(skipped),
        "samples_per_retained_task": 1,
    }


def internal_validation_split(
    examples: list[dict[str, Any]], seed: int, fraction: float = 0.1
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Use only retained original-training tasks for a loss-monitoring split."""
    if not 0 <= fraction < 1:
        raise ValueError("Internal validation fraction must be in [0, 1)")
    if len(examples) < 10 or fraction == 0:
        return examples, []
    ranked = sorted(examples, key=lambda x: sha256_text(f"validation:{seed}:{x['task_id']}"))
    count = max(1, min(len(examples) - 1, round(len(examples) * fraction)))
    return ranked[count:], ranked[:count]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_training_arguments(
    config: dict[str, Any], output_dir: Path, has_eval: bool,
    device_cpu: bool = False, eos_token: str | None = None,
):
    """Shared real TRL arguments; CPU mode is for an explicit integration test."""
    from trl import SFTConfig

    return SFTConfig(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=config["num_train_epochs"],
        max_steps=config.get("max_steps", -1),
        per_device_train_batch_size=config["per_device_train_batch_size"],
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        lr_scheduler_type="cosine", weight_decay=0.0,
        bf16=not device_cpu, fp16=False, use_cpu=device_cpu,
        gradient_checkpointing=not device_cpu,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_length=config["max_length"], packing=False,
        completion_only_loss=True, assistant_only_loss=False,
        eos_token=eos_token, seed=config["seed"], data_seed=config["seed"],
        report_to="none", save_strategy="epoch", save_total_limit=2,
        eval_strategy="epoch" if has_eval else "no", logging_steps=5,
        optim="adamw_torch", dataloader_num_workers=0,
    )


def run_training(
    examples: list[dict[str, Any]], config: dict[str, Any], output_dir: Path, manifest: dict[str, Any]
) -> None:
    """Run the standard TRL SFTTrainer with PEFT LoRA, on real CUDA hardware."""
    try:
        import torch
        from datasets import Dataset
        from huggingface_hub import model_info
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
        from trl import SFTTrainer
    except ImportError as exc:
        raise RuntimeError("GPU dependencies are missing; follow docs/research/gpu-training.md") from exc

    if not torch.cuda.is_available():
        raise RuntimeError("--run requires a CUDA GPU; preparation does not count as training")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("This frozen training configuration requires BF16-capable CUDA hardware")
    installed = {}
    for package, expected in config["package_versions"].items():
        installed[package] = importlib.metadata.version(package)
        if installed[package].split("+")[0] != expected:
            raise RuntimeError(f"Expected {package}=={expected}, found {installed[package]}")

    seed = config["seed"]
    set_seed(seed)
    model_id = config["model_id"]
    requested_revision = config["model_revision"]
    # Resolve first, then use the same immutable revision for model and tokenizer.
    revision = model_info(model_id, revision=requested_revision).sha
    if not revision or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Could not resolve the model to an immutable Hub revision")
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, trust_remote_code=False)
    if not tokenizer.chat_template:
        raise RuntimeError("The chosen model must provide a chat template")
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Drop overlong examples rather than silently training on truncated solutions.
    retained, excluded = [], []
    max_length = config["max_length"]
    for example in examples:
        ids = tokenizer.apply_chat_template(example["prompt"] + example["completion"], tokenize=True)
        if len(ids) <= max_length:
            retained.append(example)
        else:
            excluded.append({"task_id": example["task_id"], "tokens": len(ids)})
    if len(retained) < 10:
        raise RuntimeError("Fewer than ten complete examples fit the frozen sequence-length limit")
    train_rows, validation_rows = internal_validation_split(retained, seed, config["internal_validation_fraction"])
    write_jsonl(output_dir / "fit_examples.jsonl", train_rows)
    write_jsonl(output_dir / "internal_validation_examples.jsonl", validation_rows)
    write_json(output_dir / "excluded_overlong.json", excluded)
    training_rows = [{"prompt": x["prompt"], "completion": x["completion"]} for x in train_rows]
    eval_rows = [{"prompt": x["prompt"], "completion": x["completion"]} for x in validation_rows]

    manifest.update(
        {
            "status": "training_started",
            "resolved_model_revision": revision,
            "resolved_tokenizer_revision": revision,
            "chat_template_sha256": sha256_text(tokenizer.chat_template),
            "package_versions": installed,
            "gpu": torch.cuda.get_device_name(0),
            "gpu_memory_bytes": torch.cuda.get_device_properties(0).total_memory,
            "cuda_version": torch.version.cuda,
            "fit_tasks": len(train_rows),
            "internal_validation_tasks": len(validation_rows),
            "excluded_overlong_tasks": len(excluded),
            "training_started_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    write_json(output_dir / "manifest.json", manifest)

    model = AutoModelForCausalLM.from_pretrained(
        model_id, revision=revision, trust_remote_code=False,
        dtype=torch.bfloat16, attn_implementation="sdpa",
    )
    model.config.use_cache = False
    lora = LoraConfig(task_type="CAUSAL_LM", **config["lora"])
    args = build_training_arguments(config, output_dir, bool(validation_rows), eos_token=tokenizer.eos_token)
    trainer = SFTTrainer(
        model=model, args=args,
        train_dataset=Dataset.from_list(training_rows),
        eval_dataset=Dataset.from_list(eval_rows) if eval_rows else None,
        processing_class=tokenizer, peft_config=lora,
    )
    result = trainer.train()
    eval_metrics = trainer.evaluate() if validation_rows else {}
    adapter_dir = output_dir / "adapter"
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    write_json(output_dir / "trainer_log_history.json", trainer.state.log_history)
    manifest.update(
        {
            "status": "training_completed",
            "training_completed_at": datetime.now(timezone.utc).isoformat(),
            "train_metrics": result.metrics,
            "internal_validation_metrics": eval_metrics,
            "adapter_directory": str(adapter_dir),
            "heldout_code_evaluation": "not_run_by_this_job",
            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        }
    )
    write_json(output_dir / "manifest.json", manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/training-sft.json"))
    parser.add_argument("--teacher-model", default=DEFAULT_TEACHER)
    parser.add_argument("--source-metadata", type=Path, help="Pinned upstream JSON for public title/starter-code fields")
    parser.add_argument("--source-sha256", help="Required expected SHA256 for the upstream metadata file")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source_path = args.source_metadata or (Path(config["source_metadata"]) if config.get("source_metadata") else None)
    source_hash = args.source_sha256 or config.get("source_sha256")
    if source_path is not None and not source_hash:
        raise ValueError("Source metadata requires a pinned --source-sha256 or config value")
    if args.run and source_path is None:
        raise ValueError("Real training requires hash-verified source metadata to preserve starter-code interfaces")
    metadata = load_source_metadata(source_path, source_hash) if source_path is not None else None
    examples, summary = prepare_examples(load_rows(args.dataset), config["seed"], args.teacher_model, metadata)
    # Use a new output directory so previous evidence cannot be overwritten.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.output_dir / "verified_examples.jsonl", examples)
    write_json(args.output_dir / "training_config.json", config)
    manifest = {
        "status": "prepared_not_trained",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(args.dataset),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "seed": config["seed"],
        "requested_model_id": config["model_id"],
        "requested_model_revision": config["model_revision"],
        "source_metadata": str(source_path) if source_path is not None else None,
        "source_metadata_sha256": source_hash,
        "verification_scope": "published teacher code grades; no new code execution",
        "data_summary": summary,
    }
    write_json(args.output_dir / "manifest.json", manifest)
    if args.run:
        try:
            run_training(examples, config, args.output_dir, manifest)
        except Exception as exc:
            manifest["status"] = "training_failed"
            manifest["failure_type"] = type(exc).__name__
            write_json(args.output_dir / "manifest.json", manifest)
            raise
    print(json.dumps({"status": manifest["status"], **summary}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
