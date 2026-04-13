"""
PEARL Framework -- Comprehensive Multi-Model Evaluation
========================================================
Benchmarks orchestrator configurations on 10 diverse legal queries.
Measures routing accuracy (RAS, WAI), latency, cost, and saves
structured JSON results for the report generator.
"""

import asyncio
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import config

RESULTS_DIR = Path(__file__).resolve().parent / "results"

TEST_QUERIES = [
    {"id": 1, "query": "What is Article 21 of the Indian Constitution?",
     "expected_complexity": "simple", "category": "Constitutional Law"},
    {"id": 2, "query": "Define habeas corpus in Indian law",
     "expected_complexity": "simple", "category": "Writs"},
    {"id": 3, "query": "What are the fundamental rights?",
     "expected_complexity": "simple", "category": "Constitutional Law"},
    {"id": 4, "query": "What is the punishment for cybercrime under IT Act 2000?",
     "expected_complexity": "moderate", "category": "Cyber Law"},
    {"id": 5, "query": "How has the Supreme Court interpreted Article 32?",
     "expected_complexity": "moderate", "category": "Constitutional Law"},
    {"id": 6, "query": "Compare Article 14 and Article 21",
     "expected_complexity": "complex", "category": "Comparative Analysis"},
    {"id": 7, "query": "Analyze implications of Section 498A IPC on matrimonial disputes",
     "expected_complexity": "complex", "category": "Criminal Law"},
    {"id": 8, "query": "Explain the doctrine of basic structure",
     "expected_complexity": "moderate", "category": "Constitutional Law"},
    {"id": 9, "query": "Critically examine role of judiciary in protecting civil liberties",
     "expected_complexity": "complex", "category": "Analytical"},
    {"id": 10, "query": "What are the types of writs available under Indian Constitution?",
     "expected_complexity": "moderate", "category": "Writs"},
]

GPT4_GROUND_TRUTH = {
    "What is Article 21 of the Indian Constitution?": ["retriever", "answering"],
    "Define habeas corpus in Indian law": ["retriever", "answering"],
    "What are the fundamental rights?": ["retriever", "answering"],
    "What is the punishment for cybercrime under IT Act 2000?": ["retriever", "answering", "verifier"],
    "How has the Supreme Court interpreted Article 32?": ["retriever", "answering", "verifier"],
    "Compare Article 14 and Article 21": ["booster", "retriever", "answering"],
    "Analyze implications of Section 498A IPC on matrimonial disputes": ["booster", "retriever", "answering", "verifier"],
    "Explain the doctrine of basic structure": ["retriever", "answering"],
    "Critically examine role of judiciary in protecting civil liberties": ["booster", "retriever", "answering", "verifier"],
    "What are the types of writs available under Indian Constitution?": ["retriever", "answering"],
}


def compute_ras(predicted, ground_truth):
    if not ground_truth:
        return 0.0
    correct = sum(1 for a in predicted if a in ground_truth)
    return correct / max(len(predicted), len(ground_truth))


def compute_wai(predicted, ground_truth):
    if not ground_truth:
        return 0.0
    pred_set, gt_set = set(predicted), set(ground_truth)
    if pred_set == gt_set:
        return 1.0 if predicted == ground_truth else 0.85
    intersection = pred_set & gt_set
    union = pred_set | gt_set
    jaccard = len(intersection) / len(union) if union else 0
    over_penalty = len(pred_set - gt_set) * 0.15
    under_penalty = len(gt_set - pred_set) * 0.25
    return max(0, jaccard - over_penalty - under_penalty)


COST_PER_QUERY = {
    "Flan-T5-small (80M)": 0.0,
    "Flan-T5-base (250M)": 0.0,
    "GPT-3.5-turbo": 0.002,
    "GPT-4": 0.012,
    "Rule-Based": 0.0,
    "No Orchestration": 0.0,
}

MODEL_PARAMS = {
    "Flan-T5-small (80M)": {"params": "80M", "type": "SLM", "inference": "Local CPU", "training": "Knowledge Distillation from GPT-4"},
    "Flan-T5-base (250M)": {"params": "250M", "type": "SLM", "inference": "Local CPU", "training": "Knowledge Distillation from GPT-4"},
    "GPT-3.5-turbo": {"params": "~175B", "type": "LLM", "inference": "OpenAI API", "training": "Zero-shot prompting"},
    "GPT-4": {"params": "~1.7T (MoE)", "type": "LLM", "inference": "OpenAI API", "training": "Zero-shot prompting"},
    "Rule-Based": {"params": "0", "type": "Heuristic", "inference": "Local CPU", "training": "Hand-crafted rules"},
    "No Orchestration": {"params": "0", "type": "Baseline", "inference": "N/A", "training": "N/A"},
}


async def benchmark_single(orchestrator, query, model_name):
    start = time.perf_counter()
    try:
        analysis = await orchestrator.analyze_query(query)
        predicted = await orchestrator.route_to_agents(query, analysis)
        latency_ms = (time.perf_counter() - start) * 1000
    except Exception as e:
        return {
            "model": model_name, "query": query,
            "predicted_sequence": [], "latency_ms": 0,
            "error": str(e), "ras": 0.0, "wai": 0.0,
            "exact_match": False, "complexity": "error",
        }
    gt = GPT4_GROUND_TRUTH.get(query, [])
    return {
        "model": model_name, "query": query,
        "predicted_sequence": predicted,
        "ground_truth": gt,
        "latency_ms": round(latency_ms, 2),
        "cost_usd": COST_PER_QUERY.get(model_name, 0),
        "ras": round(compute_ras(predicted, gt), 4),
        "wai": round(compute_wai(predicted, gt), 4),
        "exact_match": predicted == gt,
        "complexity": analysis.get("complexity", "unknown"),
    }


def aggregate(results):
    valid = [r for r in results if "error" not in r]
    if not valid:
        return {"model": results[0]["model"], "error": "all queries failed"}
    lats = sorted([r["latency_ms"] for r in valid])
    n = len(lats)
    return {
        "model": valid[0]["model"],
        "total_queries": len(results),
        "successful_queries": n,
        "avg_ras": round(sum(r["ras"] for r in valid) / n, 4),
        "avg_wai": round(sum(r["wai"] for r in valid) / n, 4),
        "exact_match_rate": round(sum(1 for r in valid if r["exact_match"]) / n, 4),
        "avg_latency_ms": round(sum(lats) / n, 2),
        "p50_latency_ms": round(lats[n // 2], 2),
        "p95_latency_ms": round(lats[min(int(n * 0.95), n - 1)], 2),
        "total_cost_usd": round(sum(r.get("cost_usd", 0) for r in valid), 4),
        "cost_per_query": round(sum(r.get("cost_usd", 0) for r in valid) / n, 4),
    }


async def load_orchestrators():
    configs = {}
    base_cfg = {"openai_api_key": config.api.OPENAI_API_KEY}

    from orchestrators.no_orchestrator import NoOrchestrator
    configs["No Orchestration"] = NoOrchestrator(base_cfg)

    from orchestrators.rule_orchestrator import RuleBasedOrchestrator
    configs["Rule-Based"] = RuleBasedOrchestrator(base_cfg)

    from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator
    configs["Flan-T5-small (80M)"] = FlanT5Orchestrator(dict(base_cfg, model_name="google/flan-t5-small"))

    base_model = Path(__file__).resolve().parent.parent / "models" / "flan_t5_base_orchestrator"
    if base_model.exists() and (base_model / "model.safetensors").exists():
        try:
            from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator as FT5B
            configs["Flan-T5-base (250M)"] = FT5B(dict(base_cfg, model_name=str(base_model)))
        except Exception as e:
            print(f"  [SKIP] Flan-T5-base: {e}")

    if config.api.OPENAI_API_KEY and "YOUR" not in config.api.OPENAI_API_KEY:
        try:
            from orchestrators.gpt35_orchestrator import GPT35Orchestrator
            configs["GPT-3.5-turbo"] = GPT35Orchestrator(base_cfg)
        except Exception as e:
            print(f"  [SKIP] GPT-3.5-turbo: {e}")
        try:
            from orchestrators.gpt4_orchestrator import GPT4Orchestrator
            configs["GPT-4"] = GPT4Orchestrator(base_cfg)
        except Exception as e:
            print(f"  [SKIP] GPT-4: {e}")
    else:
        print("  [SKIP] GPT models: OpenAI API key not configured")

    return configs


async def run_evaluation():
    print("=" * 70)
    print("  PEARL Framework -- Comprehensive Evaluation")
    print("=" * 70)

    print("\n[1/4] Loading orchestrators...")
    configs = await load_orchestrators()
    print(f"  Loaded {len(configs)} orchestrators: {', '.join(configs.keys())}")

    for name, orch in configs.items():
        if hasattr(orch, "initialize"):
            try:
                await orch.initialize()
            except Exception:
                pass

    print(f"\n[2/4] Running benchmark ({len(TEST_QUERIES)} queries x {len(configs)} models)...")
    all_per_query = []
    all_aggregated = []

    for model_name, orch in configs.items():
        print(f"\n  Benchmarking: {model_name}")
        results = []
        for tq in TEST_QUERIES:
            q = tq["query"]
            r = await benchmark_single(orch, q, model_name)
            r["query_id"] = tq["id"]
            r["expected_complexity"] = tq["expected_complexity"]
            r["category"] = tq["category"]
            results.append(r)
            status = "OK" if "error" not in r else f"ERR: {r['error'][:40]}"
            seq_str = " -> ".join(r["predicted_sequence"]) if r["predicted_sequence"] else "N/A"
            print(f"    Q{tq['id']:>2}: {status:>6} | {r['latency_ms']:>7.1f}ms | RAS={r['ras']:.2f} | {seq_str}")

        agg = aggregate(results)
        all_per_query.extend(results)
        all_aggregated.append(agg)
        if "error" not in agg:
            print(f"  Summary: RAS={agg['avg_ras']:.3f}  WAI={agg['avg_wai']:.3f}  "
                  f"Exact={agg['exact_match_rate']*100:.0f}%  "
                  f"Lat={agg['avg_latency_ms']:.0f}ms  Cost=${agg['total_cost_usd']:.4f}")

    print("\n[3/4] Building routing decision matrix...")
    decision_matrix = {}
    for r in all_per_query:
        qid = r.get("query_id", 0)
        model = r["model"]
        if qid not in decision_matrix:
            decision_matrix[qid] = {"query": r["query"], "ground_truth": r.get("ground_truth", []), "models": {}}
        decision_matrix[qid]["models"][model] = {
            "sequence": r["predicted_sequence"],
            "ras": r["ras"],
            "exact": r["exact_match"],
        }

    print("\n[4/4] Saving results...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "num_queries": len(TEST_QUERIES),
            "num_models": len(configs),
            "models_tested": list(configs.keys()),
        },
        "test_queries": TEST_QUERIES,
        "ground_truth": {k: v for k, v in GPT4_GROUND_TRUTH.items()},
        "per_query_results": all_per_query,
        "aggregated_results": all_aggregated,
        "decision_matrix": {str(k): v for k, v in decision_matrix.items()},
        "model_params": MODEL_PARAMS,
        "cost_per_query": COST_PER_QUERY,
    }

    out_path = RESULTS_DIR / "comprehensive_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"  Saved to {out_path}")

    print("\n" + "=" * 70)
    print("  SUMMARY TABLE")
    print("=" * 70)
    hdr = f"{'Model':<25} {'RAS':>6} {'WAI':>6} {'Exact%':>7} {'Lat(ms)':>8} {'Cost($)':>8}"
    print(hdr)
    print("-" * len(hdr))
    for a in sorted(all_aggregated, key=lambda x: x.get("avg_ras", 0), reverse=True):
        if "error" in a:
            print(f"{a['model']:<25} {'ERR':>6}")
            continue
        print(f"{a['model']:<25} {a['avg_ras']:>6.3f} {a['avg_wai']:>6.3f} "
              f"{a['exact_match_rate']*100:>6.1f}% {a['avg_latency_ms']:>8.1f} ${a['total_cost_usd']:>7.4f}")
    print("=" * 70)
    return output


if __name__ == "__main__":
    os.chdir(str(Path(__file__).resolve().parent.parent))
    asyncio.run(run_evaluation())
