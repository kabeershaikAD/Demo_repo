#!/usr/bin/env python3
"""
Fixed Training Script for Query Booster SLM
Uses proper prompting and fine-tuning approach
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
    from transformers import T5ForConditionalGeneration, T5Tokenizer, T5Config
    import torch
    from torch.utils.data import Dataset, DataLoader
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryBoosterDataset(Dataset):
    """Dataset for Query Booster training with proper prompting"""
    
    def __init__(self, data: List[Dict[str, str]], tokenizer, max_length=512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Create proper prompts for T5
        self.prompt_template = """You are a Legal Query Decision Agent.
Rewrite vague or short user queries into precise retrieval queries, and output structured JSON.
Always fill ALL fields. Do not add facts not implied.

Examples:
User query: "377 rights"
Output:
{{
"need_boost": true,
"boosted_query": "Section 377 of the Indian Penal Code, Supreme Court judgments after 2018",
"retrieval_mode": "both",
"top_k": 10,
"require_human_review": false
}}

User query: "privacy article"
Output:
{{
"need_boost": true,
"boosted_query": "Article 21 of the Constitution of India, right to privacy, Supreme Court cases after 2017",
"retrieval_mode": "judgments",
"top_k": 8,
"require_human_review": false
}}

Now process this query:
User query: "{query}"
Output:"""
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Create input with proper prompting
        input_text = self.prompt_template.format(query=item["query"])
        
        # Create target JSON
        target_text = item["target"]
        
        # Tokenize input
        input_encoding = self.tokenizer(
            input_text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        # Tokenize target
        target_encoding = self.tokenizer(
            target_text,
            max_length=256,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            "input_ids": input_encoding["input_ids"].squeeze(),
            "attention_mask": input_encoding["attention_mask"].squeeze(),
            "labels": target_encoding["input_ids"].squeeze()
        }

class FixedQueryBoosterTrainer:
    """Fixed trainer for Query Booster SLM"""
    
    def __init__(self, model_name: str = "google/flan-t5-small"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        
        logger.info(f"FixedQueryBoosterTrainer initialized with model: {model_name}")
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
                "query": item['query'],
                "target": target_text
            })
        
        logger.info(f"Prepared {len(training_data)} training examples")
        return training_data
    
    def train_model(self, dataset_path: str, output_dir: str = "models/query_booster_fixed"):
        """Train the Query Booster model with proper prompting"""
        if not TRANSFORMERS_AVAILABLE or not torch:
            logger.error("Required libraries not available for training")
            return
        
        # Load dataset
        raw_dataset = self.load_dataset(dataset_path)
        training_data = self.prepare_training_data(raw_dataset)
        
        # Initialize model and tokenizer
        logger.info(f"Loading model: {self.model_name}")
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
        self.model.to(self.device)
        
        # Create dataset with proper prompting
        dataset = QueryBoosterDataset(training_data, self.tokenizer)
        
        # Create data loader
        dataloader = DataLoader(dataset, batch_size=1, shuffle=True)  # Small batch size for stability
        
        # Set up training
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-4)  # Lower learning rate
        self.model.train()
        
        # Training loop
        logger.info("Starting training with proper prompting...")
        num_epochs = 5
        
        for epoch in range(num_epochs):
            total_loss = 0
            num_batches = 0
            
            for batch in dataloader:
                # Move to device
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                total_loss += loss.item()
                num_batches += 1
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                if num_batches % 5 == 0:
                    logger.info(f"Epoch {epoch+1}/{num_epochs}, Batch {num_batches}, Loss: {loss.item():.4f}")
            
            avg_loss = total_loss / num_batches if num_batches > 0 else 0
            logger.info(f"Epoch {epoch+1}/{num_epochs} completed. Average Loss: {avg_loss:.4f}")
        
        # Save model
        os.makedirs(output_dir, exist_ok=True)
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info(f"Model saved to {output_dir}")
    
    def test_model(self, test_queries: List[str]):
        """Test the trained model"""
        if not self.model or not self.tokenizer:
            logger.error("Model not loaded")
            return
        
        self.model.eval()
        
        prompt_template = """You are a Legal Query Decision Agent.
Rewrite vague or short user queries into precise retrieval queries, and output structured JSON.
Always fill ALL fields. Do not add facts not implied.

Examples:
User query: "377 rights"
Output:
{{
"need_boost": true,
"boosted_query": "Section 377 of the Indian Penal Code, Supreme Court judgments after 2018",
"retrieval_mode": "both",
"top_k": 10,
"require_human_review": false
}}

User query: "privacy article"
Output:
{{
"need_boost": true,
"boosted_query": "Article 21 of the Constitution of India, right to privacy, Supreme Court cases after 2017",
"retrieval_mode": "judgments",
"top_k": 8,
"require_human_review": false
}}

Now process this query:
User query: "{query}"
Output:"""
        
        for query in test_queries:
            input_text = prompt_template.format(query=query)
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
                    do_sample=False,  # Use greedy decoding for more consistent JSON
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
    logger.info("Starting Fixed Query Booster SLM training")
    
    # Check if dataset exists
    dataset_path = "data/query_booster.jsonl"
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found: {dataset_path}")
        logger.info("Please run bootstrap_dataset.py first to generate the dataset")
        return
    
    # Initialize trainer
    trainer = FixedQueryBoosterTrainer()
    
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
        print(f"   Install with: pip install transformers torch")
        return
    
    # Ask user if they want to proceed with training
    print(f"\n🤖 Ready to train Query Booster SLM!")
    print(f"   Model: google/flan-t5-small")
    print(f"   Dataset: {len(dataset)} examples")
    print(f"   Output: models/query_booster_fixed/")
    print(f"   Approach: Proper prompting + fine-tuning")
    
    response = input("\nProceed with training? (y/n): ").lower().strip()
    
    if response == 'y':
        # Create output directory
        os.makedirs("models", exist_ok=True)
        
        # Train model
        trainer.train_model(dataset_path)
        
        print(f"\n🎉 Training completed!")
        print(f"📁 Model saved to: models/query_booster_fixed/")
        
        # Test the model
        print(f"\n🧪 Testing trained model...")
        test_queries = [
            "377 rights",
            "privacy article",
            "IPC theft"
        ]
        trainer.test_model(test_queries)
        
    else:
        print(f"\n⏸️  Training cancelled")

if __name__ == "__main__":
    main()
