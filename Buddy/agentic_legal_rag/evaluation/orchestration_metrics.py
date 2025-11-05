"""
Orchestration Metrics Evaluator
Comprehensive evaluation of orchestration quality, not just end-to-end answer quality
"""

import json
import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class OrchestrationMetrics:
    """Comprehensive metrics for orchestration evaluation"""
    
    # Accuracy Metrics
    routing_accuracy: float = 0.0  # % correct agent selections
    sequence_accuracy: float = 0.0  # % correct agent sequences
    complexity_classification_accuracy: float = 0.0
    
    # Performance Metrics
    avg_decision_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Cost Metrics
    total_cost_usd: float = 0.0
    avg_cost_per_decision: float = 0.0
    cost_per_1000_decisions: float = 0.0
    
    # Efficiency Metrics
    unnecessary_agent_calls: int = 0  # Called agents that weren't needed
    missed_necessary_agents: int = 0  # Didn't call agents that were needed
    optimal_routing_rate: float = 0.0
    
    # Reliability Metrics
    error_rate: float = 0.0
    fallback_rate: float = 0.0  # % times fell back to default
    
    # Confidence Calibration
    confidence_scores: List[float] = field(default_factory=list)
    actual_accuracies: List[float] = field(default_factory=list)
    calibration_error: float = 0.0
    
    # Metadata
    total_decisions: int = 0
    orchestrator_name: str = ""
    requires_api: bool = False

class OrchestrationEvaluator:
    """Evaluate orchestration quality"""
    
    def __init__(self, test_dataset_path: str):
        with open(test_dataset_path, 'r', encoding='utf-8') as f:
            self.test_cases = json.load(f)
        
        self.results = {}
    
    async def evaluate_orchestrator(
        self, 
        orchestrator: Any,
        name: str
    ) -> OrchestrationMetrics:
        """Evaluate a single orchestrator"""
        
        print(f"\nEvaluating {name}...")
        
        metrics = OrchestrationMetrics(orchestrator_name=name)
        latencies = []
        costs = []
        
        correct_routing = 0
        correct_sequences = 0
        correct_complexity = 0
        
        for i, test_case in enumerate(self.test_cases):
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(self.test_cases)}")
            
            query = test_case["query"]
            expected_agents = test_case["expected_agents"]
            expected_complexity = test_case["complexity"]
            
            # Skip invalid test cases
            if expected_complexity == "invalid":
                continue
            
            try:
                # Measure orchestration decision
                start_time = time.time()
                
                analysis = await orchestrator.analyze_query(query)
                predicted_agents = await orchestrator.route_to_agents(query, analysis)
                
                latency_ms = (time.time() - start_time) * 1000
                latencies.append(latency_ms)
                
                # Extract cost if available
                cost = analysis.get("_metrics", {}).get("cost_usd", 0.0)
                costs.append(cost)
                
                # Check routing correctness (set comparison)
                if set(predicted_agents) == set(expected_agents):
                    correct_routing += 1
                
                # Check sequence correctness (order matters)
                if predicted_agents == expected_agents:
                    correct_sequences += 1
                
                # Check complexity classification
                predicted_complexity = analysis.get("complexity", "")
                if predicted_complexity == expected_complexity:
                    correct_complexity += 1
                
                # Check for unnecessary/missed agents
                unnecessary = len(set(predicted_agents) - set(expected_agents))
                missed = len(set(expected_agents) - set(predicted_agents))
                
                metrics.unnecessary_agent_calls += unnecessary
                metrics.missed_necessary_agents += missed
                
                # Record confidence for calibration
                confidence = analysis.get("confidence", 0.5)
                metrics.confidence_scores.append(confidence)
                
                # Calculate actual accuracy for this decision
                actual_accuracy = 1.0 if predicted_agents == expected_agents else 0.0
                metrics.actual_accuracies.append(actual_accuracy)
                
            except Exception as e:
                logger.error(f"Error on case {i}: {e}")
                metrics.error_rate += 1
        
        # Calculate final metrics
        valid_cases = len([tc for tc in self.test_cases if tc["complexity"] != "invalid"])
        
        metrics.routing_accuracy = correct_routing / valid_cases if valid_cases > 0 else 0.0
        metrics.sequence_accuracy = correct_sequences / valid_cases if valid_cases > 0 else 0.0
        metrics.complexity_classification_accuracy = correct_complexity / valid_cases if valid_cases > 0 else 0.0
        
        if latencies:
            metrics.avg_decision_latency_ms = np.mean(latencies)
            metrics.p50_latency_ms = np.percentile(latencies, 50)
            metrics.p95_latency_ms = np.percentile(latencies, 95)
            metrics.p99_latency_ms = np.percentile(latencies, 99)
        
        metrics.total_cost_usd = sum(costs)
        metrics.avg_cost_per_decision = np.mean(costs) if costs else 0.0
        metrics.cost_per_1000_decisions = metrics.avg_cost_per_decision * 1000
        
        metrics.optimal_routing_rate = correct_sequences / valid_cases if valid_cases > 0 else 0.0
        metrics.error_rate = metrics.error_rate / valid_cases if valid_cases > 0 else 0.0
        
        metrics.total_decisions = valid_cases
        metrics.requires_api = orchestrator.requires_api
        
        # Calculate calibration error
        if metrics.confidence_scores and metrics.actual_accuracies:
            metrics.calibration_error = self._calculate_calibration_error(
                metrics.confidence_scores, 
                metrics.actual_accuracies
            )
        
        self.results[name] = metrics
        
        return metrics
    
    def _calculate_calibration_error(self, confidences: List[float], accuracies: List[float]) -> float:
        """Calculate calibration error (ECE - Expected Calibration Error)"""
        if not confidences or not accuracies:
            return 0.0
        
        # Bin the confidence scores
        bins = np.linspace(0, 1, 11)  # 10 bins
        bin_accuracies = []
        bin_confidences = []
        bin_counts = []
        
        for i in range(len(bins) - 1):
            bin_mask = (np.array(confidences) >= bins[i]) & (np.array(confidences) < bins[i + 1])
            if i == len(bins) - 2:  # Last bin includes upper bound
                bin_mask = (np.array(confidences) >= bins[i]) & (np.array(confidences) <= bins[i + 1])
            
            if np.any(bin_mask):
                bin_accuracies.append(np.mean(np.array(accuracies)[bin_mask]))
                bin_confidences.append(np.mean(np.array(confidences)[bin_mask]))
                bin_counts.append(np.sum(bin_mask))
            else:
                bin_accuracies.append(0.0)
                bin_confidences.append(0.0)
                bin_counts.append(0)
        
        # Calculate ECE
        total_samples = sum(bin_counts)
        if total_samples == 0:
            return 0.0
        
        ece = 0.0
        for acc, conf, count in zip(bin_accuracies, bin_confidences, bin_counts):
            if count > 0:
                ece += (count / total_samples) * abs(acc - conf)
        
        return ece
    
    async def compare_orchestrators(
        self,
        orchestrators: Dict[str, Any]
    ) -> Dict[str, OrchestrationMetrics]:
        """Compare multiple orchestrators"""
        
        for name, orchestrator in orchestrators.items():
            await self.evaluate_orchestrator(orchestrator, name)
        
        return self.results
    
    def generate_comparison_table(self) -> str:
        """Generate markdown comparison table"""
        
        table = "| Metric | " + " | ".join(self.results.keys()) + " |\n"
        table += "|" + "---|" * (len(self.results) + 1) + "\n"
        
        metrics_to_compare = [
            ("Routing Accuracy", "routing_accuracy", "{:.1%}"),
            ("Sequence Accuracy", "sequence_accuracy", "{:.1%}"),
            ("Complexity Accuracy", "complexity_classification_accuracy", "{:.1%}"),
            ("Avg Latency (ms)", "avg_decision_latency_ms", "{:.1f}"),
            ("P95 Latency (ms)", "p95_latency_ms", "{:.1f}"),
            ("Cost per Decision", "avg_cost_per_decision", "${:.5f}"),
            ("Cost per 1000", "cost_per_1000_decisions", "${:.2f}"),
            ("Optimal Routing", "optimal_routing_rate", "{:.1%}"),
            ("Error Rate", "error_rate", "{:.1%}"),
            ("Requires API", "requires_api", "{}"),
        ]
        
        for metric_name, metric_key, fmt in metrics_to_compare:
            row = f"| {metric_name} |"
            for orch_name, metrics in self.results.items():
                value = getattr(metrics, metric_key)
                row += f" {fmt.format(value)} |"
            table += row + "\n"
        
        return table
    
    def generate_report(self, output_path: str):
        """Generate comprehensive comparison report"""
        
        report = f"""# SLM Orchestration Evaluation Report

## Executive Summary
This report compares different orchestration strategies for multi-agent legal AI systems.

**Key Findings:**
- **Flan-T5-small (80M params)**: {self.results.get('FlanT5', {}).get('routing_accuracy', 0):.1%} routing accuracy
- **GPT-4 (1.7T params)**: {self.results.get('GPT4', {}).get('routing_accuracy', 0):.1%} routing accuracy  
- **Cost Reduction**: {self._calculate_cost_reduction():.0f}x cheaper with Flan-T5
- **Latency Improvement**: {self._calculate_latency_improvement():.0f}x faster with Flan-T5

## Comparison Table
{self.generate_comparison_table()}

## Detailed Analysis

"""
        
        for name, metrics in self.results.items():
            report += f"""### {name}

**Accuracy:**
- Routing Accuracy: {metrics.routing_accuracy:.1%}
- Sequence Accuracy: {metrics.sequence_accuracy:.1%}
- Complexity Classification: {metrics.complexity_classification_accuracy:.1%}

**Performance:**
- Average Latency: {metrics.avg_decision_latency_ms:.1f}ms
- P95 Latency: {metrics.p95_latency_ms:.1f}ms
- P99 Latency: {metrics.p99_latency_ms:.1f}ms

**Cost:**
- Total Cost: ${metrics.total_cost_usd:.4f}
- Per Decision: ${metrics.avg_cost_per_decision:.5f}
- Per 1000 Decisions: ${metrics.cost_per_1000_decisions:.2f}

**Efficiency:**
- Unnecessary Agent Calls: {metrics.unnecessary_agent_calls}
- Missed Necessary Agents: {metrics.missed_necessary_agents}
- Optimal Routing Rate: {metrics.optimal_routing_rate:.1%}

**Reliability:**
- Error Rate: {metrics.error_rate:.1%}
- Calibration Error: {metrics.calibration_error:.3f}

---

"""
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to {output_path}")
    
    def _calculate_cost_reduction(self) -> float:
        """Calculate cost reduction of Flan-T5 vs GPT-4"""
        flan_cost = self.results.get('FlanT5', {}).get('avg_cost_per_decision', 0)
        gpt4_cost = self.results.get('GPT4', {}).get('avg_cost_per_decision', 0)
        
        if gpt4_cost > 0:
            return gpt4_cost / max(flan_cost, 0.0001)  # Avoid division by zero
        return 1.0
    
    def _calculate_latency_improvement(self) -> float:
        """Calculate latency improvement of Flan-T5 vs GPT-4"""
        flan_latency = self.results.get('FlanT5', {}).get('avg_decision_latency_ms', 0)
        gpt4_latency = self.results.get('GPT4', {}).get('avg_decision_latency_ms', 0)
        
        if flan_latency > 0:
            return gpt4_latency / flan_latency
        return 1.0
