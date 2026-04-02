"""
Train any Flan-T5 variant on step-wise orchestration data.

Usage:
    python training/train_iterative_orchestrator.py --model google/flan-t5-small  --output models/iterative_small
    python training/train_iterative_orchestrator.py --model google/flan-t5-base   --output models/iterative_base
    python training/train_iterative_orchestrator.py --model google/flan-t5-large  --output models/iterative_large
"""

import argparse
import json
import random
import time
import torch
from pathlib import Path
from torch.utils.data import Dataset
from transformers import (
    T5Tokenizer,
    T5ForConditionalGeneration,
    Trainer,
    TrainingArguments,
)

VALID_TARGETS = {"booster", "retriever", "answering", "verifier", "multilingual", "done"}


class StepwiseDataset(Dataset):
    def __init__(self, examples, tokenizer, max_input_len=256, max_target_len=8):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len
        self.max_target_len = max_target_len

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        inp = self.tokenizer(
            ex["input"],
            max_length=self.max_input_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        tgt = self.tokenizer(
            ex["target"],
            max_length=self.max_target_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        labels = tgt["input_ids"].squeeze()
        labels[labels == self.tokenizer.pad_token_id] = -100
        return {
            "input_ids": inp["input_ids"].squeeze(),
            "attention_mask": inp["attention_mask"].squeeze(),
            "labels": labels,
        }


def load_data(path):
    examples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            if ex["target"] in VALID_TARGETS:
                examples.append({"input": ex["input"], "target": ex["target"]})
    return examples


def split_data(examples, val_ratio=0.1):
    random.shuffle(examples)
    n = int(len(examples) * val_ratio)
    return examples[n:], examples[:n]


def quick_test(model, tokenizer, device, n=15):
    test_prompts = [
        "orchestrate: What is Article 21? | history: none",
        "orchestrate: What is Article 21? | history: retriever",
        "orchestrate: What is Article 21? | history: retriever,answering",
        "orchestrate: Compare Article 14 and Article 21 | history: none",
        "orchestrate: Compare Article 14 and Article 21 | history: booster",
        "orchestrate: Compare Article 14 and Article 21 | history: booster,retriever",
        "orchestrate: Compare Article 14 and Article 21 | history: booster,retriever,answering",
        "orchestrate: Compare Article 14 and Article 21 | history: booster,retriever,answering,verifier",
        "orchestrate: bail | history: none",
        "orchestrate: bail | history: booster",
        "orchestrate: bail | history: booster,retriever",
        "orchestrate: bail | history: booster,retriever,answering",
        "orchestrate: How does writ jurisdiction work? | history: none",
        "orchestrate: How does writ jurisdiction work? | history: retriever",
        "orchestrate: How does writ jurisdiction work? | history: retriever,answering",
    ]
    model.eval()
    print("\n--- Quick test ---")
    for p in test_prompts[:n]:
        inputs = tokenizer(p, return_tensors="pt", max_length=256, truncation=True).to(device)
        with torch.no_grad():
            out = model.generate(
                inputs.input_ids,
                attention_mask=inputs.get("attention_mask"),
                max_new_tokens=8,
                num_beams=4,
                early_stopping=True,
            )
        pred = tokenizer.decode(out[0], skip_special_tokens=True).strip()
        print(f"  {p}")
        print(f"    -> {pred}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="google/flan-t5-small")
    parser.add_argument("--data", default="data/expert_traces/stepwise_training_data.jsonl")
    parser.add_argument("--output", default="models/iterative_small")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-4)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Model:  {args.model}")
    print(f"Output: {args.output}")

    tokenizer = T5Tokenizer.from_pretrained(args.model)
    model = T5ForConditionalGeneration.from_pretrained(args.model).to(device)
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")

    examples = load_data(args.data)
    print(f"Total examples: {len(examples)}")
    train_ex, val_ex = split_data(examples, val_ratio=0.1)
    print(f"Train: {len(train_ex)}, Validation: {len(val_ex)}")

    train_ds = StepwiseDataset(train_ex, tokenizer)
    val_ds = StepwiseDataset(val_ex, tokenizer)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_steps=100,
        weight_decay=0.01,
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    print(f"\nTraining finished in {elapsed/60:.1f} minutes")

    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"Model saved to {output_dir}")

    quick_test(model, tokenizer, device)


if __name__ == "__main__":
    main()
