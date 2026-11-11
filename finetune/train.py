"""QLoRA fine-tune of Qwen3-4B-Instruct-2507 for REACH name->ID resolution.

Locked config: LoRA r=16, alpha=32, 4-bit base (QLoRA), on the 3090.

Usage:
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 \
        python train.py --data data/train.jsonl --epochs 3
"""

from __future__ import annotations

import argparse
import json

import torch
import unsloth  # must be imported first
from unsloth import FastLanguageModel
from trl import SFTConfig, SFTTrainer
from datasets import Dataset

MODEL = "models/Qwen3-4B-Instruct-2507"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/train.jsonl")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--seq-len", type=int, default=512)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--save", default="checkpoints/reach-4b-lora")
    args = ap.parse_args()

    print("loading model (4-bit)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL,
        max_seq_length=args.seq_len,
        dtype=None,  # auto: bfloat16 where supported
        load_in_4bit=True,  # QLoRA
    )

    print("adding LoRA adapters (r=16, alpha=32)...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=32,
        lora_dropout=0,
        bias="none",
        use_rslora=False,
        random_state=42,
    )

    ds = Dataset.from_list([json.loads(l) for l in open(args.data) if l.strip()])

    print(f"training: {len(ds)} examples, {args.epochs} epochs...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=ds,
        dataset_text_field="messages",
        max_seq_length=args.seq_len,
        dataset_num_proc=2,
        args=SFTConfig(
            per_device_train_batch_size=args.batch,
            gradient_accumulation_steps=4,
            warmup_steps=50,
            num_train_epochs=args.epochs,
            learning_rate=args.lr,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            weight_decay=0.01,
            logging_steps=10,
            save_steps=200,
            save_total_limit=2,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
            report_to="none",
            output_dir=args.save,
        ),
    )
    trainer.train()

    print(f"saving adapters -> {args.save}")
    model.save_pretrained(args.save)
    tokenizer.save_pretrained(args.save)
    print("done. Next: export.py to merge + GGUF Q8_0")


if __name__ == "__main__":
    main()
