"""
PEARL: Knowledge Distillation via Classification

Trains Flan-T5-base to classify legal queries into routing patterns.
Uses balanced training data with single-word targets (simple / standard / boosted) instead of generating agent sequences as text.

This is dramatically easier for a 250M-param model:
- Single-word output vs comma-separated agent lists
- Balanced classes (250 each) vs 84% majority class
- Classification accuracy typically 2-3x higher than sequence generation
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Optional

import torch
from torch.utils.data import Dataset
from transformers import (
    T5Tokenizer,
    T5ForConditionalGeneration,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_CLASSES = {"simple", "standard", "boosted"}


class ClassificationDataset(Dataset):
    """Dataset for routing classification.

    Each example:
      input:  "classify: <query>"
      target: "simple" | "standard" | "boosted"
    """

    def __init__(self, data_path: str, tokenizer: T5Tokenizer, max_input_len: int = 128):
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len
        self.examples = []

        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ex = json.loads(line)
                    if ex.get("target") in VALID_CLASSES:
                        self.examples.append(ex)

        logger.info(f"Loaded {len(self.examples)} classification examples from {data_path}")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]

        input_enc = self.tokenizer(
            ex["input"],
            max_length=self.max_input_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        target_enc = self.tokenizer(
            ex["target"],
            max_length=8,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        return {
            "input_ids": input_enc["input_ids"].squeeze(),
            "attention_mask": input_enc["attention_mask"].squeeze(),
            "labels": target_enc["input_ids"].squeeze(),
        }


class KnowledgeDistillationTrainer:
    """Trains Flan-T5-base on balanced classification data."""

    def __init__(
        self,
        model_name: str = "google/flan-t5-base",
        training_data_path: str = "data/expert_traces/classification_clean.jsonl",
        output_dir: str = "models/flan_t5_base_orchestrator",
    ):
        self.model_name = model_name
        self.training_data_path = training_data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Loading model: {model_name}")
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def train(
        self,
        num_epochs: int = 5,
        batch_size: int = 16,
        learning_rate: float = 3e-4,
        warmup_steps: int = 50,
        weight_decay: float = 0.01,
        resume_from_checkpoint: Optional[str] = None,
    ):
        if resume_from_checkpoint:
            cp = Path(resume_from_checkpoint)
            if cp.exists():
                logger.info(f"Resuming from: {resume_from_checkpoint}")
                self.model = T5ForConditionalGeneration.from_pretrained(str(cp))
                self.tokenizer = T5Tokenizer.from_pretrained(str(cp))
            else:
                logger.warning(f"Checkpoint not found: {resume_from_checkpoint}, starting fresh")
                resume_from_checkpoint = None

        dataset = ClassificationDataset(self.training_data_path, self.tokenizer)

        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            weight_decay=weight_decay,
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=10,
            save_steps=100,
            save_total_limit=3,
            eval_strategy="no",
            load_best_model_at_end=False,
            push_to_hub=False,
            fp16=torch.cuda.is_available(),
        )

        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            padding=True,
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )

        logger.info("Starting classification training...")
        trainer.train(resume_from_checkpoint=resume_from_checkpoint)

        logger.info(f"Saving model to {self.output_dir}")
        self.model.save_pretrained(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        logger.info("Training complete!")

    def quick_test(self, queries=None):
        """Run a few test queries to check model output."""
        if queries is None:
            queries = [
                "What is Section 302 IPC?",
                "Compare Article 14 and Article 21",
                "explain privacy",
                "What were the charges against the accused?",
                "How to file an FIR?",
            ]

        self.model.eval()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(device)

        print("\n" + "=" * 60)
        print("Quick Test Results")
        print("=" * 60)
        for q in queries:
            prompt = f"classify: {q}"
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=128, truncation=True).to(device)
            with torch.no_grad():
                out = self.model.generate(inputs.input_ids, max_new_tokens=8, num_beams=4)
            result = self.tokenizer.decode(out[0], skip_special_tokens=True).strip()
            print(f"  Q: {q}")
            print(f"  -> {result}")
            print()


def main():
    parser = argparse.ArgumentParser(description="PEARL: Train Flan-T5 routing classifier")
    parser.add_argument("--data", type=str,
                        default="data/expert_traces/classification_clean.jsonl")
    parser.add_argument("--output", type=str, default="models/flan_t5_base_orchestrator")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--resume_from", type=str, default=None)
    parser.add_argument("--test_only", action="store_true", help="Skip training, just test existing model")

    args = parser.parse_args()

    trainer = KnowledgeDistillationTrainer(
        training_data_path=args.data,
        output_dir=args.output,
    )

    if not args.test_only:
        trainer.train(
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
            resume_from_checkpoint=args.resume_from,
        )

    trainer.quick_test()

    print("\n" + "=" * 60)
    print("Knowledge Distillation Complete")
    print(f"Model saved to: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
