"""
Main Orchestration Evaluation Script
Runs comprehensive evaluation of all orchestrators
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config
from config import config

# Import orchestrators
from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator
from orchestrators.rule_orchestrator import RuleBasedOrchestrator
from orchestrators.no_orchestrator import NoOrchestrator

# Conditional GPT4 import
try:
    from orchestrators.gpt4_orchestrator import GPT4Orchestrator
    GPT4_AVAILABLE = True
except ImportError:
    GPT4_AVAILABLE = False
    print("⚠️  GPT4Orchestrator not available (openai not installed or API key missing)")

from evaluation.orchestration_test_dataset import OrchestrationTestDataset
from evaluation.orchestration_metrics import OrchestrationEvaluator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Run comprehensive orchestration evaluation"""
    
    print("Starting SLM Orchestration Evaluation")
    print("=" * 50)
    
    # 1. Load test dataset (prefer 300-query dataset, then GPT-4 ground truth, then default)
    print("\n[INFO] Loading test dataset...")
    
    # Priority order:
    # 1. Full 300-query evaluation dataset (from IndicLegalQA)
    # 2. GPT-4 ground truth dataset
    # 3. Default test dataset
    full_dataset_path = "data/legal_queries_300_evaluation.json"
    gpt4_ground_truth_path = "evaluation/orchestration_test_dataset_gpt4_ground_truth.json"
    default_path = "evaluation/orchestration_test_dataset.json"
    
    if os.path.exists(full_dataset_path):
        test_dataset_path = full_dataset_path
        with open(test_dataset_path, 'r', encoding='utf-8') as f:
            import json
            test_data = json.load(f)
        print(f"[OK] Using full 300-query evaluation dataset: {test_dataset_path}")
        print(f"[INFO] Total test cases: {len(test_data)}")
    elif os.path.exists(gpt4_ground_truth_path):
        test_dataset_path = gpt4_ground_truth_path
        print(f"[OK] Using GPT-4 ground truth dataset: {test_dataset_path}")
    else:
        print(f"[WARNING] Full dataset not found, generating default dataset...")
        dataset = OrchestrationTestDataset()
        test_dataset_path = default_path
        dataset.export_to_json(test_dataset_path)
        print(f"[OK] Generated {len(dataset.test_cases)} test cases")
    
    # 2. Initialize orchestrators
    print("\n[INFO] Initializing orchestrators...")
    
    # Build config dict from config object
    config_dict = {
        "model_name": config.model.BOOSTER_MODEL_NAME,
        "openai_api_key": config.api.OPENAI_API_KEY,
        "groq_api_key": config.api.GROQ_API_KEY,
        "database": config.database,
        "retrieval": config.retrieval
    }
    
    orchestrators = {
        "FlanT5": FlanT5Orchestrator(config_dict),
        "RuleBased": RuleBasedOrchestrator(config_dict),
        "NoOrchestration": NoOrchestrator(config_dict)
    }
    
    # Add GPT4 if available
    if GPT4_AVAILABLE:
        try:
            orchestrators["GPT4"] = GPT4Orchestrator(config_dict)
            print("  [OK] GPT-4 orchestrator initialized")
        except Exception as e:
            logger.warning(f"Could not initialize GPT4Orchestrator: {e}")
            print(f"  [WARNING] GPT-4 orchestrator not available: {e}")
    
    # Initialize Flan-T5
    print("  Initializing Flan-T5...")
    try:
        await orchestrators["FlanT5"].initialize()
        print("  [OK] Flan-T5 initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Flan-T5: {e}")
        print("  [WARNING] Flan-T5 initialization failed, continuing with other orchestrators...")
    
    print("  [OK] Orchestrators ready")
    
    # 3. Run evaluation
    print("\n[INFO] Running evaluation...")
    
    evaluator = OrchestrationEvaluator(test_dataset_path)
    results = await evaluator.compare_orchestrators(orchestrators)
    
    # 4. Generate report
    print("\n[INFO] Generating report...")
    report_path = "evaluation/orchestration_evaluation_report.md"
    evaluator.generate_report(report_path)
    
    # 5. Print summary
    print("\n[RESULTS] Results Summary:")
    print(evaluator.generate_comparison_table())
    
    print("\n[OK] Evaluation complete!")
    print(f"[INFO] Check '{report_path}' for full report")

if __name__ == "__main__":
    asyncio.run(main())
