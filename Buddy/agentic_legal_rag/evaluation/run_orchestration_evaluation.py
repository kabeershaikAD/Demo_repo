"""
Main Orchestration Evaluation Script
Runs comprehensive evaluation of all orchestrators
"""

import asyncio
import logging
from pathlib import Path

# Import orchestrators
from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator
from orchestrators.gpt4_orchestrator import GPT4Orchestrator
from orchestrators.rule_orchestrator import RuleBasedOrchestrator
from orchestrators.no_orchestrator import NoOrchestrator

from orchestration_test_dataset import OrchestrationTestDataset
from orchestration_metrics import OrchestrationEvaluator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run comprehensive orchestration evaluation"""
    
    print("🚀 Starting SLM Orchestration Evaluation")
    print("=" * 50)
    
    # 1. Generate test dataset
    print("\n📊 Generating test dataset...")
    dataset = OrchestrationTestDataset()
    dataset.export_to_json("evaluation/orchestration_test_dataset.json")
    print(f"✅ Generated {len(dataset.test_cases)} test cases")
    
    # 2. Initialize orchestrators
    print("\n🤖 Initializing orchestrators...")
    
    config = {
        "model_name": "google/flan-t5-small",
        "openai_api_key": "your-key-here"  # Replace with actual key
    }
    
    orchestrators = {
        "FlanT5": FlanT5Orchestrator(config),
        "GPT4": GPT4Orchestrator(config),
        "RuleBased": RuleBasedOrchestrator(config),
        "NoOrchestration": NoOrchestrator(config)
    }
    
    # Initialize Flan-T5
    print("  Initializing Flan-T5...")
    await orchestrators["FlanT5"].initialize()
    
    print("  ✅ All orchestrators ready")
    
    # 3. Run evaluation
    print("\n🔬 Running evaluation...")
    
    evaluator = OrchestrationEvaluator("evaluation/orchestration_test_dataset.json")
    results = await evaluator.compare_orchestrators(orchestrators)
    
    # 4. Generate report
    print("\n📝 Generating report...")
    evaluator.generate_report("evaluation/orchestration_evaluation_report.md")
    
    # 5. Print summary
    print("\n📈 Results Summary:")
    print(evaluator.generate_comparison_table())
    
    print("\n✅ Evaluation complete!")
    print("📄 Check 'evaluation/orchestration_evaluation_report.md' for full report")

if __name__ == "__main__":
    asyncio.run(main())
