"""Real CPU training on a tiny random fixture; never a Qwen quality result."""
import copy
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("trl")
from datasets import Dataset
from peft import LoraConfig, PeftModel
from tokenizers import Tokenizer, models, pre_tokenizers
from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM, set_seed
from trl import SFTTrainer
from ttgl.train import build_training_arguments


def test_completion_mask_training_updates_and_adapter_roundtrip(tmp_path):
    torch.set_num_threads(2)
    set_seed(1729)
    vocab = {word: i for i, word in enumerate([
        "[UNK]", "[PAD]", "[EOS]", "system", "user", "assistant", ":", "Solve",
        "add", "return", "2", "1", "+", "code", "sum", "3", "4", "5",
    ])}
    backend = Tokenizer(models.WordLevel(vocab=vocab, unk_token="[UNK]"))
    backend.pre_tokenizer = pre_tokenizers.Whitespace()
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend,
                                        unk_token="[UNK]", pad_token="[PAD]", eos_token="[EOS]")
    tokenizer.chat_template = (
        "{% for message in messages %}{{ message['role'] + ': ' + message['content'] + ' ' + eos_token + ' ' }}{% endfor %}"
        "{% if add_generation_prompt %}{{ 'assistant: ' }}{% endif %}"
    )
    model_config = Qwen2Config(vocab_size=len(vocab), hidden_size=32,
                              intermediate_size=64, num_hidden_layers=1,
                              num_attention_heads=4, num_key_value_heads=2,
                              max_position_embeddings=128, eos_token_id=2, pad_token_id=1)
    model = Qwen2ForCausalLM(model_config)
    original_state = copy.deepcopy(model.state_dict())
    config = json.loads(Path("configs/training-sft.json").read_text())
    config.update(max_steps=2, gradient_accumulation_steps=1, max_length=128,
                  learning_rate=0.01, warmup_ratio=0)
    data = Dataset.from_list([
        {"prompt": [{"role": "user", "content": f"Solve add {i} 1"}],
         "completion": [{"role": "assistant", "content": f"return {i+1}"}]}
        for i in (1, 2, 3, 4)
    ])
    arguments = build_training_arguments(config, tmp_path, has_eval=False,
                                        device_cpu=True, eos_token=tokenizer.eos_token)
    trainer = SFTTrainer(model=model, args=arguments, train_dataset=data,
                         processing_class=tokenizer,
                         peft_config=LoraConfig(task_type="CAUSAL_LM", r=4, lora_alpha=8,
                                                target_modules=["q_proj", "v_proj"]))
    batch = next(iter(trainer.get_train_dataloader()))
    assert (batch["labels"] == -100).any(), "Prompt tokens must be excluded from SFT loss"
    assert (batch["labels"] != -100).any(), "Completion must contain trainable target tokens"
    previous = {n: p.detach().clone() for n, p in trainer.model.named_parameters() if p.requires_grad}
    result = trainer.train()
    assert result.global_step == 2 and torch.isfinite(torch.tensor(result.training_loss))
    assert any(not torch.equal(previous[n], p) for n, p in trainer.model.named_parameters() if n in previous)
    adapter = tmp_path / "adapter"
    trainer.save_model(str(adapter))
    assert (adapter / "adapter_model.safetensors").is_file()
    restored_base = Qwen2ForCausalLM(model_config)
    restored_base.load_state_dict(original_state)
    restored = PeftModel.from_pretrained(restored_base, str(adapter))
    trainer.model.eval()
    restored.eval()
    with torch.no_grad():
        actual = trainer.model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
        expected = restored(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits
    torch.testing.assert_close(actual, expected, atol=1e-6, rtol=1e-5)
