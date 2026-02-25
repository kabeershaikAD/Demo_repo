"""
Batch Evaluation Script for 300-Query Dataset
Processes queries in batches of 50 with concurrent processing to reduce costs and time
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator
from orchestrators.rule_orchestrator import RuleBasedOrchestrator
from orchestrators.no_orchestrator import NoOrchestrator
from evaluation.orchestration_metrics import OrchestrationMetrics, OrchestrationEvaluator

# Conditional GPT4 import
try:
    from orchestrators.gpt4_orchestrator import GPT4Orchestrator
    GPT4_AVAILABLE = True
except ImportError:
    GPT4_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_query_batch(
    orchestrator: Any,
    queries: List[Dict[str, Any]],
    batch_num: int,
    total_batches: int
) -> List[Dict[str, Any]]:
    """Process a batch of queries concurrently"""
    
    async def process_single_query(test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single query"""
        query = test_case["query"]
        expected_agents = test_case["expected_agents"]
        expected_complexity = test_case["complexity"]
        
        result = {
            "query": query,
            "expected_agents": expected_agents,
            "expected_complexity": expected_complexity,
            "test_case_id": test_case.get("id", 0),
            "success": False,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Analyze and route
            analysis = await orchestrator.analyze_query(query)
            predicted_agents = await orchestrator.route_to_agents(query, analysis)
            
            latency_ms = (time.time() - start_time) * 1000
            cost = analysis.get("_metrics", {}).get("cost_usd", 0.0)
            
            # Calculate correctness
            routing_correct = set(predicted_agents) == set(expected_agents)
            sequence_correct = predicted_agents == expected_agents
            complexity_correct = analysis.get("complexity", "") == expected_complexity
            
            result.update({
                "success": True,
                "predicted_agents": predicted_agents,
                "predicted_complexity": analysis.get("complexity", ""),
                "routing_correct": routing_correct,
                "sequence_correct": sequence_correct,
                "complexity_correct": complexity_correct,
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "confidence": analysis.get("confidence", 0.5),
                "unnecessary_agents": len(set(predicted_agents) - set(expected_agents)),
                "missed_agents": len(set(expected_agents) - set(predicted_agents))
            })
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error processing query '{query[:50]}...': {e}")
        
        return result
    
    # Process all queries in batch concurrently
    print(f"  Processing batch {batch_num}/{total_batches} ({len(queries)} queries)...")
    tasks = [process_single_query(tc) for tc in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_results = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Exception in batch: {r}")
        else:
            valid_results.append(r)
    
    return valid_results

async def evaluate_orchestrator_batch(
    orchestrator: Any,
    name: str,
    test_cases: List[Dict[str, Any]],
    batch_size: int = 50
) -> OrchestrationMetrics:
    """Evaluate orchestrator using batch processing"""
    
    print(f"\n{'='*60}")
    print(f"Evaluating {name}")
    print(f"{'='*60}")
    print(f"Total queries: {len(test_cases)}")
    print(f"Batch size: {batch_size}")
    print(f"Total batches: {(len(test_cases) + batch_size - 1) // batch_size}")
    
    metrics = OrchestrationMetrics(orchestrator_name=name)
    
    # Filter valid test cases
    valid_cases = [tc for tc in test_cases if tc.get("complexity") != "invalid"]
    
    # Process in batches
    all_results = []
    total_batches = (len(valid_cases) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(valid_cases))
        batch_cases = valid_cases[start_idx:end_idx]
        
        batch_results = await process_query_batch(
            orchestrator, 
            batch_cases, 
            batch_num + 1, 
            total_batches
        )
        
        all_results.extend(batch_results)
        
        # Progress update
        completed = len(all_results)
        print(f"  Completed: {completed}/{len(valid_cases)} queries")
        
        # Small delay between batches to avoid rate limits
        if batch_num < total_batches - 1:
            await asyncio.sleep(1)
    
    # Calculate metrics from results
    latencies = []
    costs = []
    correct_routing = 0
    correct_sequences = 0
    correct_complexity = 0
    
    predicted_agents_list = []
    expected_agents_list = []
    query_list = []
    
    for result in all_results:
        if not result.get("success"):
            metrics.error_rate += 1
            continue
        
        latencies.append(result.get("latency_ms", 0))
        costs.append(result.get("cost_usd", 0))
        
        if result.get("routing_correct"):
            correct_routing += 1
        if result.get("sequence_correct"):
            correct_sequences += 1
        if result.get("complexity_correct"):
            correct_complexity += 1
        
        metrics.unnecessary_agent_calls += result.get("unnecessary_agents", 0)
        metrics.missed_necessary_agents += result.get("missed_agents", 0)
        
        metrics.confidence_scores.append(result.get("confidence", 0.5))
        metrics.actual_accuracies.append(1.0 if result.get("sequence_correct") else 0.0)
        
        predicted_agents_list.append(result.get("predicted_agents", []))
        expected_agents_list.append(result.get("expected_agents", []))
        query_list.append(result.get("query", ""))
    
    # Calculate final metrics
    total_valid = len(all_results)
    
    metrics.routing_accuracy = correct_routing / total_valid if total_valid > 0 else 0.0
    metrics.sequence_accuracy = correct_sequences / total_valid if total_valid > 0 else 0.0
    metrics.complexity_classification_accuracy = correct_complexity / total_valid if total_valid > 0 else 0.0
    
    # Calculate PEARL metrics
    if predicted_agents_list and expected_agents_list:
        # Create temporary file for OrchestrationEvaluator initialization
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp:
            json.dump([{"query": "dummy", "expected_agents": [], "complexity": "simple"}], tmp)
            tmp_path = tmp.name
        
        try:
            evaluator = OrchestrationEvaluator(tmp_path)
            metrics.ras = evaluator._calculate_ras(predicted_agents_list, expected_agents_list)
            metrics.wai = evaluator._calculate_wai(predicted_agents_list, expected_agents_list, query_list)
        except Exception as e:
            logger.error(f"Error calculating RAS/WAI: {e}")
            # Fallback: use routing/sequence accuracy as RAS/WAI
            metrics.ras = metrics.routing_accuracy
            metrics.wai = metrics.sequence_accuracy
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    
    # Performance metrics
    if latencies:
        latencies.sort()
        metrics.avg_decision_latency_ms = sum(latencies) / len(latencies)
        metrics.p50_latency_ms = latencies[len(latencies) // 2]
        metrics.p95_latency_ms = latencies[int(len(latencies) * 0.95)]
        metrics.p99_latency_ms = latencies[int(len(latencies) * 0.99)]
    
    # Cost metrics
    metrics.total_cost_usd = sum(costs)
    metrics.avg_cost_per_decision = metrics.total_cost_usd / total_valid if total_valid > 0 else 0.0
    metrics.cost_per_1000_decisions = metrics.avg_cost_per_decision * 1000
    
    # Optimal routing rate
    metrics.optimal_routing_rate = correct_routing / total_valid if total_valid > 0 else 0.0
    
    # Error rate
    metrics.error_rate = metrics.error_rate / len(valid_cases) if len(valid_cases) > 0 else 0.0
    
    print(f"\n{name} Results:")
    print(f"  Routing Accuracy: {metrics.routing_accuracy:.1%}")
    print(f"  RAS: {metrics.ras:.1%}")
    print(f"  WAI: {metrics.wai:.1%}")
    print(f"  Avg Latency: {metrics.avg_decision_latency_ms:.1f}ms")
    print(f"  Total Cost: ${metrics.total_cost_usd:.4f}")
    
    return metrics

async def main():
    """Run batch evaluation on 300-query dataset"""
    
    print("="*60)
    print("Batch Evaluation - 300 Query Dataset")
    print("="*60)
    
    # Load 300-query dataset (prefer GPT-4 ground truth version)
    gpt4_ground_truth_path = "data/legal_queries_300_evaluation_gpt4_ground_truth.json"
    default_path = "data/legal_queries_300_evaluation.json"
    
    if os.path.exists(gpt4_ground_truth_path):
        dataset_path = gpt4_ground_truth_path
        print(f"[INFO] Using GPT-4 ground truth dataset: {dataset_path}")
    elif os.path.exists(default_path):
        dataset_path = default_path
        print(f"[INFO] Using default dataset: {dataset_path}")
    else:
        print(f"[ERROR] Dataset not found: {default_path}")
        return
    
    print(f"\n[INFO] Loading dataset: {dataset_path}")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"[OK] Loaded {len(test_cases)} test cases")
    
    # Initialize orchestrators
    print("\n[INFO] Initializing orchestrators...")
    
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
    if GPT4_AVAILABLE and config.api.OPENAI_API_KEY:
        try:
            orchestrators["GPT4"] = GPT4Orchestrator(config_dict)
            print("  [OK] GPT-4 orchestrator initialized")
        except Exception as e:
            logger.warning(f"Could not initialize GPT4Orchestrator: {e}")
            print(f"  [WARNING] GPT-4 not available: {e}")
    
    # Initialize Flan-T5
    print("  Initializing Flan-T5...")
    try:
        await orchestrators["FlanT5"].initialize()
        print("  [OK] Flan-T5 initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Flan-T5: {e}")
        print(f"  [WARNING] Flan-T5 initialization failed: {e}")
    
    print("  [OK] Orchestrators ready\n")
    
    # Evaluate each orchestrator
    results = {}
    batch_size = 50
    
    for name, orchestrator in orchestrators.items():
        try:
            metrics = await evaluate_orchestrator_batch(
                orchestrator,
                name,
                test_cases,
                batch_size=batch_size
            )
            results[name] = metrics
        except Exception as e:
            logger.error(f"Error evaluating {name}: {e}")
            print(f"[ERROR] Failed to evaluate {name}: {e}")
    
    # Generate report
    print("\n" + "="*60)
    print("Generating Evaluation Report")
    print("="*60)
    
    report_path = "evaluation/batch_evaluation_report.md"
    generate_report(results, test_cases, report_path)
    
    print(f"\n[OK] Evaluation complete!")
    print(f"[INFO] Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("Results Summary")
    print("="*60)
    print(generate_summary_table(results))

def generate_report(results: Dict[str, OrchestrationMetrics], test_cases: List[Dict], output_path: str):
    """Generate comprehensive evaluation report"""
    
    report = f"""# Batch Evaluation Report - 300 Query Dataset

## Executive Summary

This report presents evaluation results for orchestration strategies on a dataset of **{len(test_cases)} realistic legal queries** from IndicLegalQA.

**Evaluation Method**: Batch processing with {50} queries per batch, concurrent execution for efficiency.

**Key Findings:**
"""
    
    # Add key findings
    if "FlanT5" in results:
        flan_metrics = results["FlanT5"]
        report += f"- **Flan-T5 (Trained)**: {flan_metrics.routing_accuracy:.1%} routing accuracy, {flan_metrics.wai:.1%} WAI\n"
    
    if "GPT4" in results:
        gpt4_metrics = results["GPT4"]
        report += f"- **GPT-4 (Baseline)**: {gpt4_metrics.routing_accuracy:.1%} routing accuracy, {gpt4_metrics.wai:.1%} WAI\n"
    
    if "FlanT5" in results and "GPT4" in results:
        cost_reduction = results["GPT4"].total_cost_usd / results["FlanT5"].total_cost_usd if results["FlanT5"].total_cost_usd > 0 else float('inf')
        latency_improvement = results["GPT4"].avg_decision_latency_ms / results["FlanT5"].avg_decision_latency_ms if results["FlanT5"].avg_decision_latency_ms > 0 else 0
        report += f"- **Cost Reduction**: {cost_reduction:.0f}x cheaper with Flan-T5\n"
        report += f"- **Latency Improvement**: {latency_improvement:.1f}x faster with Flan-T5\n"
    
    report += "\n## Comparison Table\n\n"
    report += generate_summary_table(results)
    
    report += "\n## Detailed Analysis\n\n"
    
    for name, metrics in results.items():
        report += f"""### {name}

**Accuracy Metrics:**
- Routing Accuracy: {metrics.routing_accuracy:.1%}
- Sequence Accuracy: {metrics.sequence_accuracy:.1%}
- RAS (PEARL): {metrics.ras:.1%}
- WAI (PEARL): {metrics.wai:.1%}
- Complexity Classification: {metrics.complexity_classification_accuracy:.1%}

**Performance Metrics:**
- Average Latency: {metrics.avg_decision_latency_ms:.1f}ms
- P50 Latency: {metrics.p50_latency_ms:.1f}ms
- P95 Latency: {metrics.p95_latency_ms:.1f}ms
- P99 Latency: {metrics.p99_latency_ms:.1f}ms

**Cost Metrics:**
- Total Cost: ${metrics.total_cost_usd:.4f}
- Per Decision: ${metrics.avg_cost_per_decision:.5f}
- Per 1000 Decisions: ${metrics.cost_per_1000_decisions:.2f}

**Efficiency Metrics:**
- Unnecessary Agent Calls: {metrics.unnecessary_agent_calls}
- Missed Necessary Agents: {metrics.missed_necessary_agents}
- Optimal Routing Rate: {metrics.optimal_routing_rate:.1%}

**Reliability Metrics:**
- Error Rate: {metrics.error_rate:.1%}
- Calibration Error: {metrics.calibration_error:.3f}

---

"""
    
    report += f"""
## Dataset Information

- **Total Queries**: {len(test_cases)}
- **Source**: IndicLegalQA Dataset
- **Evaluation Method**: Batch processing ({50} queries per batch)
- **Concurrent Processing**: Enabled for efficiency

## Methodology

1. **Batch Processing**: Queries processed in batches of {50} to optimize API usage
2. **Concurrent Execution**: Multiple queries processed in parallel within each batch
3. **Metrics Calculation**: Standard PEARL metrics (RAS, WAI) applied
4. **Error Handling**: Robust error handling with fallback mechanisms

## Conclusion

This evaluation demonstrates the performance of different orchestration strategies on a realistic legal query dataset. The results show the trade-offs between accuracy, cost, and latency for each approach.

"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

def generate_summary_table(results: Dict[str, OrchestrationMetrics]) -> str:
    """Generate comparison table"""
    
    table = "| Metric | " + " | ".join(results.keys()) + " |\n"
    table += "|" + "|".join(["---"] * (len(results) + 1)) + "|\n"
    
    # Routing Accuracy
    table += "| Routing Accuracy | " + " | ".join([f"{r.routing_accuracy:.1%}" for r in results.values()]) + " |\n"
    
    # RAS
    table += "| RAS (PEARL) | " + " | ".join([f"{r.ras:.1%}" for r in results.values()]) + " |\n"
    
    # WAI
    table += "| WAI (PEARL) | " + " | ".join([f"{r.wai:.1%}" for r in results.values()]) + " |\n"
    
    # Latency
    table += "| Avg Latency (ms) | " + " | ".join([f"{r.avg_decision_latency_ms:.1f}" for r in results.values()]) + " |\n"
    
    # Cost
    table += "| Cost per Decision | " + " | ".join([f"${r.avg_cost_per_decision:.5f}" for r in results.values()]) + " |\n"
    
    # Total Cost
    table += "| Total Cost | " + " | ".join([f"${r.total_cost_usd:.4f}" for r in results.values()]) + " |\n"
    
    # Optimal Routing
    table += "| Optimal Routing | " + " | ".join([f"{r.optimal_routing_rate:.1%}" for r in results.values()]) + " |\n"
    
    # Error Rate
    table += "| Error Rate | " + " | ".join([f"{r.error_rate:.1%}" for r in results.values()]) + " |\n"
    
    return table

if __name__ == "__main__":
    asyncio.run(main())

