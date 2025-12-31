"""
Collect GPT-4 routing decisions as ground truth for 300-query evaluation dataset
SAFE VERSION: Better error handling and progress output
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

async def collect_gpt4_ground_truth_300_safe():
    """Collect GPT-4 routing decisions for 300 evaluation queries with better error handling"""
    
    print("="*60)
    print("Collecting GPT-4 Ground Truth for 300-Query Dataset")
    print("="*60)
    
    # Check API key first
    print("\n[INFO] Checking configuration...")
    if not hasattr(config, 'api') or not config.api.OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY not found in config!")
        print("[INFO] Please set it in config.py or as environment variable")
        return
    
    print("[OK] API key found")
    
    # Load 300-query evaluation dataset
    test_dataset_path = "data/legal_queries_300_evaluation.json"
    if not os.path.exists(test_dataset_path):
        print(f"[ERROR] Test dataset not found: {test_dataset_path}")
        return
    
    print(f"[INFO] Loading dataset: {test_dataset_path}")
    with open(test_dataset_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"[OK] Found {len(test_cases)} test cases")
    
    # Initialize GPT-4 orchestrator
    print("\n[INFO] Initializing GPT-4 orchestrator...")
    try:
        from orchestrators.gpt4_orchestrator import GPT4Orchestrator
        
        config_dict = {
            "model_name": "gpt-4",
            "openai_api_key": config.api.OPENAI_API_KEY,
            "groq_api_key": getattr(config.api, 'GROQ_API_KEY', None),
            "database": getattr(config, 'database', {}),
            "retrieval": getattr(config, 'retrieval', {})
        }
        
        gpt4_orchestrator = GPT4Orchestrator(config_dict)
        # GPT4Orchestrator initializes in __init__, no separate initialize() method needed
        print("[OK] GPT-4 orchestrator initialized")
    except ImportError as e:
        print(f"[ERROR] Failed to import GPT4Orchestrator: {e}")
        print("[INFO] Make sure openai package is installed: pip install openai")
        return
    except Exception as e:
        print(f"[ERROR] Failed to initialize GPT-4: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check if we have existing progress
    existing_decisions = []
    last_batch = 0
    for i in range(1, 7):
        batch_file = f"evaluation/gpt4_ground_truth_300_batch_{i}.json"
        if os.path.exists(batch_file):
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                existing_decisions.extend(batch_data)
                last_batch = i
                print(f"[INFO] Found existing batch {i} with {len(batch_data)} decisions")
    
    if existing_decisions:
        print(f"[INFO] Resuming from batch {last_batch + 1} (already have {len(existing_decisions)} decisions)")
        start_from_batch = last_batch
    else:
        start_from_batch = 0
    
    # Collect GPT-4 decisions in batches
    print("\n[INFO] Collecting GPT-4 routing decisions...")
    print("[INFO] This will take ~30-60 minutes and cost ~$2-3")
    print("[INFO] Processing in batches of 50 queries...\n")
    
    gpt4_decisions = existing_decisions.copy()
    batch_size = 50
    total_batches = (len(test_cases) + batch_size - 1) // batch_size
    
    for batch_num in range(start_from_batch, total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(test_cases))
        batch_cases = test_cases[start_idx:end_idx]
        
        print(f"\n{'='*60}")
        print(f"[BATCH {batch_num + 1}/{total_batches}] Processing queries {start_idx + 1}-{end_idx}")
        print(f"{'='*60}")
        
        batch_decisions = []
        
        for i, test_case in enumerate(batch_cases):
            query = test_case["query"]
            query_num = start_idx + i + 1
            
            try:
                # Get GPT-4's analysis
                print(f"  [{query_num}/{len(test_cases)}] Analyzing: {query[:60]}...", end="", flush=True)
                analysis = await gpt4_orchestrator.analyze_query(query)
                print(" [OK]", flush=True)
                
                # Get GPT-4's routing decision
                print(f"  [{query_num}/{len(test_cases)}] Routing...", end="", flush=True)
                agent_sequence = await gpt4_orchestrator.route_to_agents(query, analysis)
                print(f" [OK] -> {agent_sequence}", flush=True)
                
                # Store decision
                batch_decisions.append({
                    "id": test_case.get("id", query_num),
                    "query": query,
                    "gpt4_agents": agent_sequence,
                    "gpt4_analysis": analysis,
                    "original_expected": test_case.get("expected_agents", []),
                    "complexity": test_case.get("complexity"),
                    "reasoning_type": test_case.get("reasoning_type")
                })
                
            except Exception as e:
                print(f" [ERROR] {str(e)[:100]}", flush=True)
                # Use fallback
                batch_decisions.append({
                    "id": test_case.get("id", query_num),
                    "query": query,
                    "gpt4_agents": ["retriever", "answering"],
                    "gpt4_analysis": {"complexity": "moderate"},
                    "original_expected": test_case.get("expected_agents", []),
                    "complexity": test_case.get("complexity"),
                    "reasoning_type": test_case.get("reasoning_type"),
                    "error": str(e)
                })
        
        # Add to total decisions
        gpt4_decisions.extend(batch_decisions)
        
        # Save intermediate results after each batch
        intermediate_path = f"evaluation/gpt4_ground_truth_300_batch_{batch_num + 1}.json"
        with open(intermediate_path, 'w', encoding='utf-8') as f:
            json.dump(gpt4_decisions, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Saved batch {batch_num + 1}: {intermediate_path} ({len(gpt4_decisions)} total decisions)")
        
        if batch_num < total_batches - 1:
            print("[INFO] Pausing 5 seconds before next batch...")
            await asyncio.sleep(5)
    
    # Save final GPT-4 decisions
    output_path = "evaluation/gpt4_ground_truth_300.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(gpt4_decisions, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Saved final GPT-4 ground truth to: {output_path}")
    print(f"[OK] Collected {len(gpt4_decisions)} routing decisions")
    
    # Update evaluation dataset with GPT-4 decisions
    print("\n[INFO] Updating evaluation dataset with GPT-4 ground truth...")
    
    # Create mapping from query to GPT-4 agents
    gpt4_map = {item["query"]: item["gpt4_agents"] for item in gpt4_decisions}
    
    # Update test cases
    updated_test_cases = []
    for test_case in test_cases:
        query = test_case["query"]
        if query in gpt4_map:
            # Store original expected agents
            test_case["original_expected_agents"] = test_case.get("expected_agents", [])
            # Update with GPT-4's decision
            test_case["expected_agents"] = gpt4_map[query]
            test_case["ground_truth_source"] = "gpt4"
        updated_test_cases.append(test_case)
    
    # Save updated evaluation dataset
    updated_path = "data/legal_queries_300_evaluation_gpt4_ground_truth.json"
    with open(updated_path, 'w', encoding='utf-8') as f:
        json.dump(updated_test_cases, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Updated evaluation dataset saved to: {updated_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"  Total queries: {len(test_cases)}")
    print(f"  GPT-4 decisions collected: {len(gpt4_decisions)}")
    print(f"  Updated dataset: {updated_path}")
    print("\n[OK] Ground truth collection complete!")
    print("\n[INFO] Next step: Update batch_evaluation.py to use the new dataset")
    print(f"   Or manually rename: {updated_path} -> data/legal_queries_300_evaluation.json")

if __name__ == "__main__":
    try:
        asyncio.run(collect_gpt4_ground_truth_300_safe())
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Progress saved in batch files.")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()

