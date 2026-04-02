"""
Multi-Model Benchmark -- evaluate all orchestrators on the same test queries.

Models benchmarked:
  1. Flan-T5-small  (80M)  -- iterative, locally trained
  2. Flan-T5-base   (250M) -- iterative, locally trained
  3. Flan-T5-large  (780M) -- iterative, locally trained
  4. GPT-3.5-turbo          -- iterative, zero-shot (API)
  5. GPT-4                  -- two-call, zero-shot (API)
  6. Rule-based             -- keyword heuristics
  7. No orchestration       -- always retriever+answering

For every (model, query) pair the benchmark records:
  - agent_sequence (predicted routing)
  - step_trace (per-step decisions for iterative models)
  - latency_ms
  - cost_usd
  - match_gpt4 (binary: does it agree with GPT-4 ground truth?)
  - RAS score, WAI score
"""

import asyncio
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config

GROUND_TRUTH_PATH = Path("data/expert_traces/training_data.jsonl")
STEPWISE_DATA_PATH = Path("data/expert_traces/stepwise_training_data.jsonl")
RESULTS_DIR = Path("evaluation/results")

TEST_QUERIES = [
    "What is Article 21?",
    "bail",
    "Compare Article 14 and Article 21",
    "How does writ jurisdiction work under Article 226?",
    "What are the fundamental rights in the Indian Constitution?",
    "Explain the doctrine of basic structure",
    "murder",
    "What is the procedure for filing a PIL?",
    "Difference between cognizable and non-cognizable offences",
    "Analyze the implications of Section 498A IPC",
    "What is anticipatory bail under Section 438 CrPC?",
    "right to education",
    "What are the powers of the Supreme Court under Article 32?",
    "Explain the concept of judicial review in India",
    "How to file an FIR?",
    "What is the difference between IPC and CrPC?",
    "Explain Article 370 and its abrogation",
    "What are the grounds for divorce under Hindu Marriage Act?",
    "consumer protection",
    "What is the role of the Attorney General of India?",
    "Explain the concept of res judicata",
    "What are the types of writs available under Indian Constitution?",
    "How does the POCSO Act protect children?",
    "cyber crime laws in India",
    "Explain the Right to Information Act 2005",
]


def load_ground_truth() -> Dict[str, List[str]]:
    gt = {}
    if not GROUND_TRUTH_PATH.exists():
        return gt
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            q = ex.get("query", "")
            seq = [a.strip() for a in ex["target"].split(",") if a.strip()]
            if q:
                gt[q] = seq
    return gt


def sequence_match(pred: List[str], gt: List[str]) -> bool:
    return pred == gt


def compute_ras(pred: List[str], gt: List[str]) -> float:
    if not gt:
        return 0.0
    correct = sum(1 for a in pred if a in gt)
    return correct / max(len(pred), len(gt))


def compute_wai(pred: List[str], gt: List[str]) -> float:
    if not gt:
        return 0.0
    pred_set = set(pred)
    gt_set = set(gt)
    if pred_set == gt_set:
        order_score = 1.0
        for i, a in enumerate(pred):
            if i < len(gt) and a != gt[i]:
                order_score -= 0.1
        return max(order_score, 0.5)
    intersection = pred_set & gt_set
    union = pred_set | gt_set
    jaccard = len(intersection) / len(union) if union else 0
    return jaccard * 0.8


async def benchmark_orchestrator(orch, queries, ground_truth, model_name):
    results = []
    for q in queries:
        start = time.time()
        try:
            analysis = await orch.analyze_query(q)
            seq = await orch.route_to_agents(q, analysis)
        except Exception as e:
            seq = ["retriever", "answering"]
            print(f"  [ERROR] {model_name} on '{q[:40]}': {e}")
        latency = (time.time() - start) * 1000

        gt = ground_truth.get(q, [])
        step_trace = getattr(orch, "_step_latencies", [])

        results.append({
            "query": q,
            "model": model_name,
            "predicted_sequence": seq,
            "ground_truth": gt,
            "exact_match": sequence_match(seq, gt) if gt else None,
            "ras": compute_ras(seq, gt) if gt else None,
            "wai": compute_wai(seq, gt) if gt else None,
            "latency_ms": round(latency, 1),
            "cost_usd": round(orch.cost_per_decision, 6),
            "num_steps": len(step_trace) if step_trace else 1,
            "step_latencies": [round(s, 1) for s in step_trace] if step_trace else [],
        })
    return results


def aggregate_metrics(results: List[Dict]) -> Dict:
    scored = [r for r in results if r["ras"] is not None]
    n = len(scored)
    if n == 0:
        return {"n_queries": len(results), "n_scored": 0}
    return {
        "model": results[0]["model"],
        "n_queries": len(results),
        "n_scored": n,
        "exact_match_rate": round(sum(1 for r in scored if r["exact_match"]) / n, 3),
        "avg_ras": round(sum(r["ras"] for r in scored) / n, 3),
        "avg_wai": round(sum(r["wai"] for r in scored) / n, 3),
        "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / len(results), 1),
        "total_cost_usd": round(sum(r["cost_usd"] for r in results), 6),
        "avg_steps": round(sum(r["num_steps"] for r in results) / len(results), 1),
    }


def print_summary_table(all_agg):
    hdr = f"{'Model':<30} {'Exact%':>7} {'RAS':>6} {'WAI':>6} {'Lat(ms)':>8} {'Cost($)':>8} {'Steps':>5}"
    print("\n" + "=" * len(hdr))
    print(hdr)
    print("=" * len(hdr))
    for a in all_agg:
        if a["n_scored"] == 0:
            print(f"{a['model']:<30} {'N/A':>7} {'N/A':>6} {'N/A':>6} {a.get('avg_latency_ms', 0):>8.1f} {'$0':>8} {'?':>5}")
        else:
            print(f"{a['model']:<30} {a['exact_match_rate']*100:>6.1f}% {a['avg_ras']:>6.3f} {a['avg_wai']:>6.3f} {a['avg_latency_ms']:>8.1f} ${a['total_cost_usd']:>7.4f} {a['avg_steps']:>5.1f}")
    print("=" * len(hdr))


async def run_benchmark(model_configs: Dict[str, Any] = None):
    """
    model_configs: dict mapping model_name -> orchestrator instance
    If None, will attempt to load all available orchestrators.
    """
    ground_truth = load_ground_truth()
    print(f"Ground truth loaded: {len(ground_truth)} queries")
    print(f"Test queries: {len(TEST_QUERIES)}")
    gt_overlap = sum(1 for q in TEST_QUERIES if q in ground_truth)
    print(f"Overlap with ground truth: {gt_overlap}")

    if model_configs is None:
        model_configs = {}
        _load_available_orchestrators(model_configs)

    all_results = []
    all_agg = []

    for name, orch in model_configs.items():
        print(f"\nBenchmarking: {name}")
        try:
            if hasattr(orch, "initialize"):
                await orch.initialize()
        except Exception as e:
            print(f"  [SKIP] Could not initialise {name}: {e}")
            continue

        results = await benchmark_orchestrator(orch, TEST_QUERIES, ground_truth, name)
        all_results.extend(results)
        agg = aggregate_metrics(results)
        all_agg.append(agg)
        print(f"  Done: RAS={agg.get('avg_ras', 'N/A')}, latency={agg.get('avg_latency_ms', 0):.0f}ms")

    print_summary_table(all_agg)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    with open(RESULTS_DIR / "benchmark_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_agg, f, indent=2)
    print(f"\nResults saved to {RESULTS_DIR}/")

    return all_results, all_agg


def _load_available_orchestrators(configs: Dict):
    base_cfg = {"openai_api_key": config.api.OPENAI_API_KEY}

    from orchestrators.no_orchestrator import NoOrchestrator
    configs["No-Orchestration"] = NoOrchestrator(base_cfg)

    from orchestrators.rule_orchestrator import RuleBasedOrchestrator
    configs["Rule-Based"] = RuleBasedOrchestrator(base_cfg)

    small_path = Path("models/iterative_small")
    if small_path.exists():
        from orchestrators.iterative_slm_orchestrator import IterativeSLMOrchestrator
        configs["Flan-T5-small (80M)"] = IterativeSLMOrchestrator(base_cfg, model_path=str(small_path))

    base_path = Path("models/iterative_base")
    if base_path.exists():
        from orchestrators.iterative_slm_orchestrator import IterativeSLMOrchestrator
        configs["Flan-T5-base (250M)"] = IterativeSLMOrchestrator(base_cfg, model_path=str(base_path))

    large_path = Path("models/iterative_large")
    if large_path.exists():
        from orchestrators.iterative_slm_orchestrator import IterativeSLMOrchestrator
        configs["Flan-T5-large (780M)"] = IterativeSLMOrchestrator(base_cfg, model_path=str(large_path))

    if config.api.OPENAI_API_KEY and "YOUR" not in config.api.OPENAI_API_KEY:
        try:
            from orchestrators.gpt35_orchestrator import GPT35Orchestrator
            configs["GPT-3.5-turbo"] = GPT35Orchestrator(base_cfg)
        except Exception:
            pass

        try:
            from orchestrators.gpt4_orchestrator import GPT4Orchestrator
            configs["GPT-4"] = GPT4Orchestrator(base_cfg)
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(run_benchmark())
