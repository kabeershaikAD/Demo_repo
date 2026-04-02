"""
Touchpoint Comparison -- per-query, per-step side-by-side view across all models.

Reads benchmark_results.json and produces:
  1. A formatted console report (step-by-step trace per query)
  2. A CSV for easy import into spreadsheets / PPT
  3. A JSON report for programmatic consumption
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path("evaluation/results")
INPUT_FILE = RESULTS_DIR / "benchmark_results.json"


def load_results():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def group_by_query(results):
    groups = defaultdict(list)
    for r in results:
        groups[r["query"]].append(r)
    return groups


def format_sequence(seq, max_steps=6):
    cells = []
    for i in range(max_steps):
        cells.append(seq[i] if i < len(seq) else "-")
    return cells


def print_touchpoint_report(results):
    groups = group_by_query(results)
    max_steps = 6

    for query, rows in groups.items():
        print(f'\nQUERY: "{query}"')
        print("=" * 120)

        header_parts = [f"{'Model':<25}"]
        for i in range(1, max_steps + 1):
            header_parts.append(f"{'Step'+str(i):>12}")
        header_parts.extend([f"{'Match':>7}", f"{'RAS':>6}", f"{'Lat(ms)':>9}", f"{'Cost($)':>8}"])
        print("".join(header_parts))
        print("-" * 120)

        for r in rows:
            steps = format_sequence(r["predicted_sequence"], max_steps)
            match_str = "YES" if r.get("exact_match") else ("NO" if r.get("exact_match") is not None else "N/A")
            ras_str = f"{r['ras']:.2f}" if r.get("ras") is not None else "N/A"
            parts = [f"{r['model']:<25}"]
            for s in steps:
                parts.append(f"{s:>12}")
            parts.extend([f"{match_str:>7}", f"{ras_str:>6}", f"{r['latency_ms']:>9.1f}", f"${r['cost_usd']:>7.4f}"])
            print("".join(parts))

        if rows and rows[0].get("ground_truth"):
            gt_steps = format_sequence(rows[0]["ground_truth"], max_steps)
            parts = [f"{'[GROUND TRUTH]':<25}"]
            for s in gt_steps:
                parts.append(f"{s:>12}")
            parts.extend([f"{'---':>7}", f"{'1.00':>6}", f"{'---':>9}", f"{'---':>8}"])
            print("".join(parts))

        print()


def save_csv(results):
    out = RESULTS_DIR / "touchpoint_comparison.csv"
    max_steps = 6
    headers = ["query", "model"] + [f"step_{i}" for i in range(1, max_steps + 1)] + [
        "exact_match", "ras", "wai", "latency_ms", "cost_usd"
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in results:
            steps = format_sequence(r["predicted_sequence"], max_steps)
            w.writerow([
                r["query"],
                r["model"],
                *steps,
                r.get("exact_match", ""),
                r.get("ras", ""),
                r.get("wai", ""),
                r["latency_ms"],
                r["cost_usd"],
            ])
    print(f"CSV saved to {out}")


def save_summary_report(results):
    groups = group_by_query(results)
    report = {}
    for query, rows in groups.items():
        report[query] = {
            "ground_truth": rows[0].get("ground_truth", []),
            "models": {}
        }
        for r in rows:
            report[query]["models"][r["model"]] = {
                "sequence": r["predicted_sequence"],
                "exact_match": r.get("exact_match"),
                "ras": r.get("ras"),
                "wai": r.get("wai"),
                "latency_ms": r["latency_ms"],
                "cost_usd": r["cost_usd"],
            }
    out = RESULTS_DIR / "touchpoint_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"JSON report saved to {out}")


def main():
    if not INPUT_FILE.exists():
        print(f"No benchmark results found at {INPUT_FILE}.")
        print("Run evaluation/multi_model_benchmark.py first.")
        return

    results = load_results()
    print(f"Loaded {len(results)} results")
    print_touchpoint_report(results)
    save_csv(results)
    save_summary_report(results)


if __name__ == "__main__":
    main()
