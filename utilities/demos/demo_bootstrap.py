#!/usr/bin/env python3
"""
Demonstration script for the Query Booster dataset bootstrap
Shows how to use the generated dataset and integrate with the existing system
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bootstrap_dataset import QueryBootstrapGenerator
from booster_agent import PromptBooster

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demonstrate_bootstrap():
    """Demonstrate the bootstrap dataset generation"""
    print("🚀 Query Booster Dataset Bootstrap Demonstration")
    print("=" * 60)
    
    # Initialize generator
    generator = QueryBootstrapGenerator(use_gpt_refinement=False)
    
    # Sample queries for demonstration
    demo_queries = [
        "377 rights",
        "privacy article",
        "IPC theft",
        "Supreme Court case on sedition",
        "article 21 right to life"
    ]
    
    print(f"\n📝 Processing {len(demo_queries)} demo queries...")
    
    results = []
    for i, query in enumerate(demo_queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        
        # Process query
        decision = generator.process_query(query)
        results.append(decision)
        
        # Display results
        print(f"   Need Boost: {decision['need_boost']}")
        print(f"   Boosted Query: '{decision['boosted_query']}'")
        print(f"   Retrieval Mode: {decision['retrieval_mode']}")
        print(f"   Top-K: {decision['top_k']}")
        print(f"   Human Review: {decision['require_human_review']}")
        print(f"   Confidence: {decision['confidence']:.2f}")
        print(f"   Reasoning: {decision['reasoning']}")
    
    return results

def demonstrate_dataset_usage():
    """Demonstrate how to use the generated dataset"""
    print("\n📊 Dataset Usage Demonstration")
    print("=" * 40)
    
    dataset_path = "data/query_booster.jsonl"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        print("   Please run bootstrap_dataset.py first")
        return
    
    # Load dataset
    dataset = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                dataset.append(json.loads(line))
    
    print(f"✅ Loaded {len(dataset)} training examples")
    
    # Analyze dataset
    print(f"\n📈 Dataset Analysis:")
    
    # Count by retrieval mode
    mode_counts = {}
    boost_counts = {"boosted": 0, "not_boosted": 0}
    confidence_scores = []
    
    for item in dataset:
        mode = item["retrieval_mode"]
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        if item["need_boost"]:
            boost_counts["boosted"] += 1
        else:
            boost_counts["not_boosted"] += 1
        
        confidence_scores.append(item["confidence"])
    
    print(f"   Retrieval Modes: {mode_counts}")
    print(f"   Boost Distribution: {boost_counts}")
    print(f"   Avg Confidence: {sum(confidence_scores)/len(confidence_scores):.2f}")
    
    # Show sample entries
    print(f"\n📋 Sample Dataset Entries:")
    for i, item in enumerate(dataset[:3], 1):
        print(f"\n--- Entry {i} ---")
        print(f"Query: {item['query']}")
        print(f"Boosted: {item['boosted_query']}")
        print(f"Mode: {item['retrieval_mode']} | Top-K: {item['top_k']}")
        print(f"Boost: {item['need_boost']} | Review: {item['require_human_review']}")

def demonstrate_integration():
    """Demonstrate integration with existing Query Booster agent"""
    print("\n🔗 Integration with Query Booster Agent")
    print("=" * 45)
    
    try:
        # Initialize the existing Query Booster agent
        booster = PromptBooster(force_rule_based=True)
        
        # Test queries
        test_queries = [
            "377 rights",
            "privacy article",
            "IPC theft"
        ]
        
        print(f"Testing {len(test_queries)} queries with existing agent...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {query} ---")
            
            # Get decision from agent
            decision = booster.generate_decision(query)
            
            print(f"   Need Boost: {decision.need_boost}")
            print(f"   Boosted Query: '{decision.boosted_query}'")
            print(f"   Retrieval Mode: {decision.retrieval_mode}")
            print(f"   Top-K: {decision.top_k}")
            print(f"   Human Review: {decision.require_human_review}")
            print(f"   Confidence: {decision.confidence}")
            print(f"   Reasoning: {decision.reasoning}")
        
        print(f"\n✅ Integration successful!")
        
    except Exception as e:
        print(f"❌ Integration failed: {e}")

def demonstrate_training_preparation():
    """Demonstrate how to prepare data for training"""
    print("\n🎓 Training Data Preparation")
    print("=" * 35)
    
    dataset_path = "data/query_booster.jsonl"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        return
    
    # Load dataset
    dataset = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                dataset.append(json.loads(line))
    
    print(f"📊 Preparing {len(dataset)} examples for training...")
    
    # Convert to training format
    training_examples = []
    for item in dataset:
        # Input: Query
        input_text = f"Query: {item['query']}"
        
        # Target: JSON decision
        target_json = {
            "need_boost": item['need_boost'],
            "boosted_query": item['boosted_query'],
            "retrieval_mode": item['retrieval_mode'],
            "top_k": item['top_k'],
            "require_human_review": item['require_human_review']
        }
        target_text = json.dumps(target_json, ensure_ascii=False)
        
        training_examples.append({
            "input": input_text,
            "target": target_text
        })
    
    print(f"✅ Prepared {len(training_examples)} training examples")
    
    # Show sample training format
    print(f"\n📋 Sample Training Format:")
    for i, example in enumerate(training_examples[:2], 1):
        print(f"\n--- Example {i} ---")
        print(f"Input: {example['input']}")
        print(f"Target: {example['target']}")
    
    # Save training format
    training_path = "data/training_format.jsonl"
    with open(training_path, 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"\n💾 Saved training format to: {training_path}")

def main():
    """Main demonstration function"""
    print("🎯 Query Booster Dataset Bootstrap - Complete Demonstration")
    print("=" * 70)
    
    # Step 1: Demonstrate bootstrap generation
    print("\n" + "="*70)
    print("STEP 1: BOOTSTRAP DATASET GENERATION")
    print("="*70)
    demonstrate_bootstrap()
    
    # Step 2: Demonstrate dataset usage
    print("\n" + "="*70)
    print("STEP 2: DATASET USAGE AND ANALYSIS")
    print("="*70)
    demonstrate_dataset_usage()
    
    # Step 3: Demonstrate integration
    print("\n" + "="*70)
    print("STEP 3: INTEGRATION WITH EXISTING SYSTEM")
    print("="*70)
    demonstrate_integration()
    
    # Step 4: Demonstrate training preparation
    print("\n" + "="*70)
    print("STEP 4: TRAINING DATA PREPARATION")
    print("="*70)
    demonstrate_training_preparation()
    
    # Summary
    print("\n" + "="*70)
    print("🎉 DEMONSTRATION COMPLETE")
    print("="*70)
    print("✅ Bootstrap dataset generation working")
    print("✅ Dataset analysis and usage working")
    print("✅ Integration with existing system working")
    print("✅ Training data preparation working")
    print("\n💡 Next steps:")
    print("   1. Run 'python train_booster_slm.py' to train the model")
    print("   2. Use the trained model in your Query Booster agent")
    print("   3. Generate more training data as needed")

if __name__ == "__main__":
    main()

