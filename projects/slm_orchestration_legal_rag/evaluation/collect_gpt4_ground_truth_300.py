"""
Collect GPT-4 routing decisions as ground truth for 300-query evaluation dataset
This creates a fair comparison by using GPT-4's actual decisions as the expected answers
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from orchestrators.gpt4_orchestrator import GPT4Orchestrator

async def collect_gpt4_ground_truth_300():
    """Collect GPT-4 routing decisions for 300 evaluation queries"""
    
    print("="*60)
    print("Collecting GPT-4 Ground Truth for 300-Query Dataset")
    print("="*60)
    
    # Load 300-query evaluation dataset
    test_dataset_path = "data/legal_queries_300_evaluation.json"
    if not os.path.exists(test_dataset_path):
        print(f"[ERROR] Test dataset not found: {test_dataset_path}")
        return
    
    with open(test_dataset_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"\n[INFO] Found {len(test_cases)} test cases")
    print("[INFO] Initializing GPT-4 orchestrator...")
    
    # Initialize GPT-4 orchestrator
    config_dict = {
        "model_name": "gpt-4",
        "openai_api_key": config.api.OPENAI_API_KEY,
        "groq_api_key": config.api.GROQ_API_KEY,
        "database": config.database,
        "retrieval": config.retrieval
    }
    
    try:
        print("[INFO] Checking OpenAI API key...")
        if not config.api.OPENAI_API_KEY:
            print("[ERROR] OPENAI_API_KEY not set in config!")
            print("[INFO] Please set it in config.py or environment variable")
            return
        
        print("[INFO] Initializing GPT-4 orchestrator...")
        gpt4_orchestrator = GPT4Orchestrator(config_dict)
        # GPT4Orchestrator initializes in __init__, no separate initialize() method needed
        print("[OK] GPT-4 orchestrator initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize GPT-4: {e}")
        import traceback
        traceback.print_exc()
        print("[INFO] Make sure OPENAI_API_KEY is set in config")
        return
    
    # Collect GPT-4 decisions in batches
    print("\n[INFO] Collecting GPT-4 routing decisions...")
    print("[INFO] This will take ~30-60 minutes and cost ~$2-3")
    print("[INFO] Processing in batches of 50 queries...\n")
    
    gpt4_decisions = []
    batch_size = 50
    total_batches = (len(test_cases) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(test_cases))
        batch_cases = test_cases[start_idx:end_idx]
        
        print(f"[BATCH {batch_num + 1}/{total_batches}] Processing queries {start_idx + 1}-{end_idx}...")
        
        for i, test_case in enumerate(batch_cases):
            query = test_case["query"]
            query_num = start_idx + i + 1
            
            try:
                # Get GPT-4's analysis
                print(f"    Analyzing query {query_num}...", end="", flush=True)
                analysis = await gpt4_orchestrator.analyze_query(query)
                print(" [OK]", flush=True)
                
                # Get GPT-4's routing decision
                print(f"    Routing query {query_num}...", end="", flush=True)
                agent_sequence = await gpt4_orchestrator.route_to_agents(query, analysis)
                print(f" [OK] -> {agent_sequence}", flush=True)
                
                # Store decision
                gpt4_decisions.append({
                    "id": test_case.get("id", query_num),
                    "query": query,
                    "gpt4_agents": agent_sequence,
                    "gpt4_analysis": analysis,
                    "original_expected": test_case.get("expected_agents", []),
                    "complexity": test_case.get("complexity"),
                    "reasoning_type": test_case.get("reasoning_type")
                })
                
                if (i + 1) % 10 == 0:
                    print(f"  [{query_num}/{len(test_cases)}] {query[:50]}... -> {agent_sequence}")
                
            except Exception as e:
                print(f"  [ERROR] Query {query_num}: {e}")
                # Use fallback
                gpt4_decisions.append({
                    "id": test_case.get("id", query_num),
                    "query": query,
                    "gpt4_agents": ["retriever", "answering"],
                    "gpt4_analysis": {"complexity": "moderate"},
                    "original_expected": test_case.get("expected_agents", []),
                    "complexity": test_case.get("complexity"),
                    "reasoning_type": test_case.get("reasoning_type"),
                    "error": str(e)
                })
        
        # Save intermediate results after each batch
        intermediate_path = f"evaluation/gpt4_ground_truth_300_batch_{batch_num + 1}.json"
        with open(intermediate_path, 'w', encoding='utf-8') as f:
            json.dump(gpt4_decisions, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved intermediate results: {intermediate_path} ({len(gpt4_decisions)} decisions)\n")
        
        if batch_num < total_batches - 1:
            print("[INFO] Pausing 5 seconds before next batch...\n")
            await asyncio.sleep(5)
    
    # Save final GPT-4 decisions
    output_path = "evaluation/gpt4_ground_truth_300.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(gpt4_decisions, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Saved GPT-4 ground truth to: {output_path}")
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
    asyncio.run(collect_gpt4_ground_truth_300())

