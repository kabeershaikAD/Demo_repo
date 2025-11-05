#!/usr/bin/env python3
"""
Enhanced Training Script for Query Booster SLM with 500 Indian Legal Queries
Uses the AI teacher generated dataset for comprehensive training
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Optional imports for training
try:
    from transformers import T5ForConditionalGeneration, T5Tokenizer, T5Config, Trainer, TrainingArguments
    from transformers import DataCollatorForSeq2Seq
    from datasets import Dataset
    import torch
    from torch.utils.data import DataLoader
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedQueryBoosterTrainer:
    """Enhanced trainer for Query Booster SLM with 500 queries"""
    
    def __init__(self, model_name: str = "google/flan-t5-small"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        
        logger.info(f"EnhancedQueryBoosterTrainer initialized with model: {model_name}")
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
        """Prepare dataset for training with proper prompting"""
        training_data = []
        
        for item in dataset:
            # Create input with proper prompting for JSON generation
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
        """Create Hugging Face dataset with proper tokenization"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library not available")
        
        # Initialize tokenizer
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        
        # Tokenize the data
        inputs = []
        targets = []
        
        for item in training_data:
            # Tokenize input
            input_encoding = self.tokenizer(
                item["input"],
                max_length=512,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            
            # Tokenize target
            target_encoding = self.tokenizer(
                item["target"],
                max_length=256,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            
            inputs.append({
                "input_ids": input_encoding["input_ids"].squeeze().tolist(),
                "attention_mask": input_encoding["attention_mask"].squeeze().tolist()
            })
            targets.append({
                "labels": target_encoding["input_ids"].squeeze().tolist()
            })
        
        # Combine inputs and targets
        dataset_dict = {
            "input_ids": [inp["input_ids"] for inp in inputs],
            "attention_mask": [inp["attention_mask"] for inp in inputs],
            "labels": [tgt["labels"] for tgt in targets]
        }
        
        return Dataset.from_dict(dataset_dict)
    
    def train_model(self, dataset_path: str, output_dir: str = "models/query_booster_100"):
        """Train the Query Booster model with 100 queries"""
        if not TRANSFORMERS_AVAILABLE or not torch:
            logger.error("Required libraries not available for training")
            return
        
        # Load dataset
        raw_dataset = self.load_dataset(dataset_path)
        training_data = self.prepare_training_data(raw_dataset)
        
        # Initialize model
        logger.info(f"Loading model: {self.model_name}")
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
        self.model.to(self.device)
        
        # Create dataset
        hf_dataset = self.create_huggingface_dataset(training_data)
        
        # Split dataset
        train_size = int(0.8 * len(hf_dataset))
        train_dataset = hf_dataset.select(range(train_size))
        eval_dataset = hf_dataset.select(range(train_size, len(hf_dataset)))
        
        # Data collator
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            padding=True
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            num_train_epochs=5,
            warmup_steps=200,
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=20,
            eval_strategy="steps",
            eval_steps=100,
            save_steps=200,
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            learning_rate=5e-5,
            lr_scheduler_type="cosine",
            report_to=None,  # Disable wandb
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
        logger.info("Starting training with 100 queries...")
        trainer.train()
        
        # Save model
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info(f"Model saved to {output_dir}")
        
        # Evaluate model
        eval_results = trainer.evaluate()
        logger.info(f"Evaluation results: {eval_results}")
        
        return eval_results
    
    def test_model(self, test_queries: List[str]):
        """Test the trained model"""
        if not self.model or not self.tokenizer:
            logger.error("Model not loaded")
            return
        
        self.model.eval()
        
        for query in test_queries:
            input_text = f"Query: {query}"
            input_encoding = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=512,
                truncation=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    input_encoding["input_ids"],
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id
                )
            
            prediction = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            print(f"\nQuery: {query}")
            print(f"Raw Prediction: {prediction}")
            
            # Try to extract JSON from prediction
            try:
                # Look for JSON in the output
                json_start = prediction.find('{')
                json_end = prediction.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = prediction[json_start:json_end]
                    predicted_json = json.loads(json_str)
                    print(f"✅ Parsed JSON: {predicted_json}")
                else:
                    print("❌ No JSON found in prediction")
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")

def main():
    """Main training function"""
    logger.info("🚀 Enhanced Query Booster SLM Training with 100 Indian Legal Queries")
    logger.info("=" * 70)
    
    # Check if dataset exists
    dataset_path = "data/ai_teacher_dataset_fixed.jsonl"
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found: {dataset_path}")
        logger.info("Please ensure the dataset file exists with 100 queries")
        return
    
    # Initialize trainer
    trainer = EnhancedQueryBoosterTrainer()
    
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
    
    # Check if training libraries are available
    if not TRANSFORMERS_AVAILABLE or not torch:
        print(f"\n⚠️  Training libraries not available:")
        print(f"   Transformers: {TRANSFORMERS_AVAILABLE}")
        print(f"   PyTorch: {torch is not None}")
        print(f"   Install with: pip install transformers torch datasets")
        return
    
    # Ask user if they want to proceed with training
    print(f"\n🤖 Ready to train Query Booster SLM!")
    print(f"   Model: google/flan-t5-small")
    print(f"   Dataset: {len(dataset)} examples")
    print(f"   Output: models/query_booster_100/")
    print(f"   Approach: Enhanced training with 100 Indian legal queries")
    
    response = input("\nProceed with training? (y/n): ").lower().strip()
    
    if response == 'y':
        # Create output directory
        os.makedirs("models", exist_ok=True)
        
        # Train model
        start_time = time.time()
        eval_results = trainer.train_model(dataset_path)
        training_time = time.time() - start_time
        
        print(f"\n🎉 Training completed!")
        print(f"📁 Model saved to: models/query_booster_100/")
        print(f"⏱️  Training time: {training_time:.2f} seconds")
        print(f"📊 Evaluation results: {eval_results}")
        
        # Test the model
        print(f"\n🧪 Testing trained model...")
        test_queries = [
            "What are my rights under Article 21?",
            "What is the punishment for theft?",
            "How to file a divorce case?",
            "What are the labor laws for workers?",
            "Can I get compensation for defective goods?"
        ]
        trainer.test_model(test_queries)
        
    else:
        print(f"\n⏸️  Training cancelled")

if __name__ == "__main__":
    main()
