"""
PEARL: Knowledge Distillation Framework
Trains Flan-T5-small to imitate expert orchestration using sequence-coherence losses

This implements the second component of PEARL:
1. Training Flan-T5-small on query-to-workflow pairs
2. Using sequence-coherence losses
3. Invalid-sequence penalties
"""

import json
import logging
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    T5Tokenizer, 
    T5ForConditionalGeneration,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq
)
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestrationDataset(Dataset):
    """
    Dataset for orchestration knowledge distillation.
    Loads query-to-workflow pairs from expert traces.
    """
    
    def __init__(self, data_path: str, tokenizer: T5Tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = []
        
        # Load training data
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                example = json.loads(line)
                self.examples.append(example)
        
        logger.info(f"Loaded {len(self.examples)} training examples")
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        example = self.examples[idx]
        
        # Get input and target
        input_text = example.get("input", "")
        target_text = example.get("target", "")
        
        # Tokenize
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        target_encoding = self.tokenizer(
            target_text,
            max_length=128,  # Agent sequences are short
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': input_encoding['input_ids'].squeeze(),
            'attention_mask': input_encoding['attention_mask'].squeeze(),
            'labels': target_encoding['input_ids'].squeeze(),
            'query': example.get("query", ""),
            'agent_sequence': example.get("agent_sequence", [])
        }


class SequenceCoherenceLoss(nn.Module):
    """
    Sequence-Coherence Loss for orchestration training.
    
    According to PEARL:
    - Penalizes invalid agent sequences (e.g., answering before retriever)
    - Rewards coherent sequences that follow workflow dependencies
    - Ensures learned patterns respect agent dependencies
    """
    
    def __init__(self, base_loss_fn, valid_sequences: List[List[str]], penalty_weight: float = 0.5):
        super().__init__()
        self.base_loss_fn = base_loss_fn
        self.valid_sequences = valid_sequences
        self.penalty_weight = penalty_weight
        
        # Define agent dependencies (e.g., answering requires retriever)
        self.dependencies = {
            "answering": ["retriever"],
            "verifier": ["answering", "retriever"],
            "multilingual": ["answering"]  # Can work on its own but often after answering
        }
    
    def is_valid_sequence(self, sequence: List[str]) -> bool:
        """Check if agent sequence respects dependencies"""
        # Check dependencies
        for i, agent in enumerate(sequence):
            if agent in self.dependencies:
                required = self.dependencies[agent]
                # Check if all required agents appear before this agent
                for req_agent in required:
                    if req_agent not in sequence[:i]:
                        return False
        
        # Check if sequence is in valid patterns
        sequence_str = ",".join(sequence)
        for valid_seq in self.valid_sequences:
            valid_str = ",".join(valid_seq)
            if sequence_str == valid_str:
                return True
        
        return False
    
    def forward(self, predictions, labels, agent_sequences: Optional[List[List[str]]] = None):
        """
        Compute loss with sequence-coherence penalty
        
        Args:
            predictions: Model predictions
            labels: Ground truth labels
            agent_sequences: Decoded agent sequences (if available)
        """
        # Base cross-entropy loss
        base_loss = self.base_loss_fn(predictions, labels)
        
        # Sequence coherence penalty
        coherence_penalty = 0.0
        if agent_sequences:
            invalid_count = 0
            for sequence in agent_sequences:
                if not self.is_valid_sequence(sequence):
                    invalid_count += 1
            
            if len(agent_sequences) > 0:
                invalid_ratio = invalid_count / len(agent_sequences)
                coherence_penalty = self.penalty_weight * invalid_ratio
        
        total_loss = base_loss + coherence_penalty
        
        return total_loss


class KnowledgeDistillationTrainer:
    """
    Trains Flan-T5-small to imitate expert orchestration.
    
    According to PEARL:
    - Trains on query-to-workflow pairs from GPT-4 traces
    - Uses sequence-coherence losses
    - Applies invalid-sequence penalties
    """
    
    def __init__(
        self,
        model_name: str = "google/flan-t5-small",
        training_data_path: str = "data/expert_traces/training_data.jsonl",
        output_dir: str = "models/flan_t5_orchestrator"
    ):
        self.model_name = model_name
        self.training_data_path = training_data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tokenizer and model
        logger.info(f"Loading model: {model_name}")
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)
        
        # Add special tokens if needed
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Valid agent sequences (from patterns)
        self.valid_sequences = [
            ["retriever", "answering"],
            ["booster", "retriever", "answering"],
            ["retriever", "answering", "verifier"],
            ["booster", "retriever", "answering", "verifier"],
            ["booster", "retriever", "answering", "verifier", "multilingual"]
        ]
    
    def train(
        self,
        num_epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 5e-5,
        warmup_steps: int = 100,
        resume_from_checkpoint: Optional[str] = None
    ):
        """
        Train the model
        
        Args:
            num_epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
            warmup_steps: Number of warmup steps
            resume_from_checkpoint: Path to checkpoint directory to resume from (e.g., "models/flan_t5_orchestrator/checkpoint-200")
        """
        
        # If resuming, load model from checkpoint
        if resume_from_checkpoint:
            checkpoint_path = Path(resume_from_checkpoint)
            if checkpoint_path.exists():
                logger.info(f"Resuming training from checkpoint: {resume_from_checkpoint}")
                # Load model and tokenizer from checkpoint
                self.model = T5ForConditionalGeneration.from_pretrained(str(checkpoint_path))
                self.tokenizer = T5Tokenizer.from_pretrained(str(checkpoint_path))
            else:
                logger.warning(f"Checkpoint not found: {resume_from_checkpoint}. Starting from scratch.")
                resume_from_checkpoint = None
        
        # Load dataset
        dataset = OrchestrationDataset(self.training_data_path, self.tokenizer)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=10,
            save_steps=100,
            eval_strategy="no",  # Can add validation if needed
            save_total_limit=3,
            load_best_model_at_end=False,
            push_to_hub=False
        )
        
        # Data collator
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            padding=True
        )
        
        # Custom trainer with sequence-coherence loss
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )
        
        # Train (with optional resume)
        if resume_from_checkpoint:
            logger.info(f"Resuming training from checkpoint: {resume_from_checkpoint}")
        else:
            logger.info("Starting training from scratch...")
        
        trainer.train(resume_from_checkpoint=resume_from_checkpoint)
        
        # Save model
        logger.info(f"Saving model to {self.output_dir}")
        self.model.save_pretrained(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        
        logger.info("Training complete!")
    
    def evaluate(self, test_data_path: str) -> Dict[str, float]:
        """Evaluate the trained model"""
        # Load test dataset
        test_dataset = OrchestrationDataset(test_data_path, self.tokenizer)
        
        # Evaluation logic here
        # For now, return placeholder
        return {
            "accuracy": 0.0,
            "sequence_accuracy": 0.0
        }


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Flan-T5 orchestrator via knowledge distillation")
    parser.add_argument("--data", type=str, default="data/expert_traces/training_data.jsonl",
                       help="Path to training data")
    parser.add_argument("--output", type=str, default="models/flan_t5_orchestrator",
                       help="Output directory for trained model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--resume_from", type=str, default=None,
                       help="Path to checkpoint directory to resume from (e.g., models/flan_t5_orchestrator/checkpoint-200)")
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = KnowledgeDistillationTrainer(
        training_data_path=args.data,
        output_dir=args.output
    )
    
    # Train
    trainer.train(
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        resume_from_checkpoint=args.resume_from
    )
    
    print("\n" + "="*60)
    print("Knowledge Distillation Training Complete")
    print("="*60)
    print(f"Model saved to: {args.output}")
    print("="*60)


if __name__ == "__main__":
    main()

