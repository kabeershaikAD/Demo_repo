"""
PEARL Complete Pipeline Runner
Runs all PEARL components: trace collection, training, and evaluation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from training.collect_expert_traces import ExpertTraceCollector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run complete PEARL pipeline"""
    
    print("="*60)
    print("PEARL Pipeline: Expert Trace Collection")
    print("="*60)
    
    # Step 1: Collect expert traces
    print("\n[Step 1/4] Collecting expert traces from GPT-4...")
    
    collector = ExpertTraceCollector()
    await collector.initialize()
    
    # Load queries
    queries_file = project_root / "data" / "query_booster_500.jsonl"
    if queries_file.exists():
        queries = []
        import json
        with open(queries_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                queries.append(data.get("query", ""))
        logger.info(f"Loaded {len(queries)} queries from {queries_file}")
    else:
        # Use sample queries
        queries = [
            "What is Article 21?",
            "What is Section 302 of IPC?",
            "Compare Article 19 and Article 21",
            "How to file an FIR?",
            "Analyze the implications of Section 377",
            "What are the rights of an accused?",
            "Difference between murder and culpable homicide",
            "Procedure for bail application",
            "What is the punishment for theft?",
            "Rights of women under Indian Constitution"
        ]
        logger.info(f"Using {len(queries)} sample queries")
    
    # Collect traces (limit to 10 for testing, remove limit for full collection)
    test_queries = queries[:10] if len(queries) > 10 else queries
    await collector.collect_batch(test_queries, batch_size=2)
    
    # Save results
    collector.save_traces("expert_traces.jsonl")
    collector.save_training_format("training_data.jsonl")
    stats = collector.save_statistics()
    
    print(f"\n✅ Expert trace collection complete!")
    print(f"   - Traces collected: {stats['total_traces_collected']}")
    print(f"   - Success rate: {stats['success_rate']:.1%}")
    print(f"   - Total cost: ${stats['total_cost']:.4f}")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Review collected traces: data/expert_traces/expert_traces.jsonl")
    print("2. Train Flan-T5 model:")
    print("   python training/knowledge_distillation.py --data data/expert_traces/training_data.jsonl")
    print("3. Run evaluation:")
    print("   python evaluation/run_orchestration_evaluation.py")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())








