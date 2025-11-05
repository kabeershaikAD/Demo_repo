#!/usr/bin/env python3
"""
Training Script for Query Booster SLM using the generated dataset
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Optional imports for training
try:
    from transformers import (
        T5ForConditionalGeneration, T5Tokenizer, 
        TrainingArguments, Trainer, DataCollatorForSeq2Seq
    )
    from datasets import Dataset
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryBoosterTrainer:
    """Trainer for Query Booster SLM using generated dataset"""
    
    def __init__(self, model_name: str = "google/flan-t5-small"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        
        logger.info(f"QueryBoosterTrainer initialized with model: {model_name}")
        logger.info(f"Device: {self.device}")
    
    def load_dataset(self, jsonl_path: str) -> List[Dict[str, Any]]:
        """Load training dataset from JSONL file"""
        dataset = []
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    dataset.append(json.loads(line))
        
        logger.info(f"Loaded {len(dataset)} training examples from {jsonl_path}")
        return dataset
    
    def prepare_training_data(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Prepare dataset for training"""
        training_data = []
        
        for item in dataset:
            # Create input prompt
            input_text = f"Query: {item['query']}"
            
            # Create target JSON output
            target_json = {
                "need_boost": item['need_boost'],
                "boosted_query": item['boosted_query'],
                "retrieval_mode": item['retrieval_mode'],
                "top_k": item['top_k'],
                "require_human_review": item['require_human_review']
            }
            
            target_text = json.dumps(target_json, ensure_ascii=False)
            
            training_data.append({
                "input": input_text,
                "target": target_text
            })
        
        logger.info(f"Prepared {len(training_data)} training examples")
        return training_data
    
    def create_huggingface_dataset(self, training_data: List[Dict[str, str]]) -> Dataset:
        """Create Hugging Face dataset"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library not available")
        
        # Convert to Hugging Face dataset format
        dataset_dict = {
            "input_text": [],
            "target_text": []
        }
        
        for item in training_data:
            dataset_dict["input_text"].append(item["input"])
            dataset_dict["target_text"].append(item["target"])
        
        return Dataset.from_dict(dataset_dict)
    
    def train_model(self, dataset_path: str, output_dir: str = "models/query_booster"):
        """Train the Query Booster model"""
        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
            logger.error("Required libraries not available for training")
            return
        
        # Load dataset
        raw_dataset = self.load_dataset(dataset_path)
        training_data = self.prepare_training_data(raw_dataset)
        
        # Initialize model and tokenizer
        logger.info(f"Loading model: {self.model_name}")
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
        
        # Create Hugging Face dataset
        hf_dataset = self.create_huggingface_dataset(training_data)
        
        # Split dataset
        train_size = int(0.8 * len(hf_dataset))
        train_dataset = hf_dataset.select(range(train_size))
        eval_dataset = hf_dataset.select(range(train_size, len(hf_dataset)))
        
        # Custom data collator for text-to-text
        def data_collator(batch):
            # Tokenize inputs
            inputs = self.tokenizer(
                [item["input_text"] for item in batch],
                max_length=512,
                padding=True,
                truncation=True,
                return_tensors="pt"
            )
            
            # Tokenize targets
            targets = self.tokenizer(
                [item["target_text"] for item in batch],
                max_length=256,
                padding=True,
                truncation=True,
                return_tensors="pt"
            )
            
            return {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
                "labels": targets["input_ids"]
            }
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            num_train_epochs=3,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=10,
            eval_strategy="steps",  # Changed from evaluation_strategy
            eval_steps=50,
            save_steps=100,
            save_total_limit=2,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # Train model
        logger.info("Starting training...")
        trainer.train()
        
        # Save model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info(f"Model saved to {output_dir}")
    
    def evaluate_model(self, test_dataset: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate the trained model"""
        if not self.model or not self.tokenizer:
            logger.error("Model not loaded")
            return {}
        
        self.model.eval()
        
        correct_predictions = 0
        total_predictions = 0
        
        for item in test_dataset:
            # Create input
            input_text = f"Query: {item['query']}"
            input_encoding = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=512,
                truncation=True
            )
            
            # Generate prediction
            with torch.no_grad():
                outputs = self.model.generate(
                    input_encoding["input_ids"],
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                    temperature=0.3
                )
            
            # Decode prediction
            prediction = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse prediction
            try:
                predicted_json = json.loads(prediction)
                
                # Check if prediction matches target
                if (predicted_json.get("need_boost") == item["need_boost"] and
                    predicted_json.get("retrieval_mode") == item["retrieval_mode"]):
                    correct_predictions += 1
                
                total_predictions += 1
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse prediction: {prediction}")
                total_predictions += 1
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "correct_predictions": correct_predictions,
            "total_predictions": total_predictions
        }

def main():
    """Main training function"""
    logger.info("Starting Query Booster SLM training")
    
    # Check if dataset exists
    dataset_path = "data/query_booster.jsonl"
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found: {dataset_path}")
        logger.info("Please run bootstrap_dataset.py first to generate the dataset")
        return
    
    # Initialize trainer
    trainer = QueryBoosterTrainer()
    
    # Load and inspect dataset
    dataset = trainer.load_dataset(dataset_path)
    
    print(f"\n📊 Dataset Statistics:")
    print(f"   Total examples: {len(dataset)}")
    
    # Count by retrieval mode
    mode_counts = {}
    boost_counts = {"boosted": 0, "not_boosted": 0}
    
    for item in dataset:
        mode = item["retrieval_mode"]
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        if item["need_boost"]:
            boost_counts["boosted"] += 1
        else:
            boost_counts["not_boosted"] += 1
    
    print(f"   Retrieval modes: {mode_counts}")
    print(f"   Boost distribution: {boost_counts}")
    
    # Show sample entries
    print(f"\n📋 Sample Training Examples:")
    for i, item in enumerate(dataset[:3], 1):
        print(f"\n--- Example {i} ---")
        print(f"Query: {item['query']}")
        print(f"Boosted: {item['boosted_query']}")
        print(f"Mode: {item['retrieval_mode']}")
        print(f"Top-K: {item['top_k']}")
        print(f"Need Boost: {item['need_boost']}")
    
    # Check if training libraries are available
    if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
        print(f"\n⚠️  Training libraries not available:")
        print(f"   Transformers: {TRANSFORMERS_AVAILABLE}")
        print(f"   PyTorch: {TORCH_AVAILABLE}")
        print(f"   Install with: pip install transformers torch")
        return
    
    # Ask user if they want to proceed with training
    print(f"\n🤖 Ready to train Query Booster SLM!")
    print(f"   Model: google/flan-t5-small")
    print(f"   Dataset: {len(dataset)} examples")
    print(f"   Output: models/query_booster/")
    
    response = input("\nProceed with training? (y/n): ").lower().strip()
    
    if response == 'y':
        # Create output directory
        os.makedirs("models", exist_ok=True)
        
        # Train model
        trainer.train_model(dataset_path)
        
        print(f"\n🎉 Training completed!")
        print(f"📁 Model saved to: models/query_booster/")
        print(f"💡 You can now use the trained model in your Query Booster agent")
    else:
        print(f"\n⏸️  Training cancelled")

if __name__ == "__main__":
    main()
