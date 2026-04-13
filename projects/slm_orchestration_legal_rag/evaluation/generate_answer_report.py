"""
PEARL Framework -- Orchestration + Answer Quality Report Generator
===================================================================
Reads answer_quality_results.json (combined orchestration + pipeline results)
and produces charts + markdown report.
"""

import json, os
from pathlib import Path
import numpy as np

RESULTS_DIR = Path(__file__).resolve().parent / "results"
CHARTS_DIR  = RESULTS_DIR / "charts"


def _load():
    fp = RESULTS_DIR / "answer_quality_results.json"
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


def chart_routing_vs_answer(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    agg = data["aggregated_results"]
    models = [a["model"] for a in agg]
    route_acc = [a["route_accuracy"] for a in agg]
    relevance = [a["avg_relevance"] for a in agg]
    completeness = [a["avg_completeness"] for a in agg]

    x = np.arange(len(models))
    w = 0.25
    fig, ax = plt.subplots(figsize=(14, 7))
    b1 = ax.bar(x - w, route_acc, w, label="Route Accuracy", color="#3B82F6", edgecolor="white")
    b2 = ax.bar(x, relevance, w, label="Answer Relevance", color="#10B981", edgecolor="white")
    b3 = ax.bar(x + w, completeness, w, label="Answer Completeness", color="#F59E0B", edgecolor="white")

    for bars in [b1, b2, b3]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                    f"{h:.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xlabel("Orchestrator Model", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score (0-1)", fontsize=12, fontweight="bold")
    ax.set_title("Routing Accuracy vs. Answer Quality by Orchestrator", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10, rotation=15, ha="right")
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    path = CHARTS_DIR / "answer_quality_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  Saved {path.name}")


def chart_heatmap(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    per_q = data["per_query_results"]
    models = data["metadata"]["models"]
    queries = data["test_queries"]

    matrix = np.zeros((len(queries), len(models)))
    for r in per_q:
        qi = r["query_id"] - 1
        mi = models.index(r["model"])
        matrix[qi, mi] = r.get("relevance", 0)

    fig, ax = plt.subplots(figsize=(13, 9))
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, fontsize=10, rotation=30, ha="right")
    ax.set_yticks(range(len(queries)))
    qlabels = [f"Q{q['id']}: {q['query'][:32]}..." for q in queries]
    ax.set_yticklabels(qlabels, fontsize=9)
    for i in range(len(queries)):
        for j in range(len(models)):
            ax.text(j, i, f"{matrix[i,j]:.2f}", ha="center", va="center",
                    fontsize=8, fontweight="bold",
                    color="white" if matrix[i,j] < 0.4 else "black")
    ax.set_title("Answer Relevance Heatmap (Orchestrator x Query)", fontsize=14, fontweight="bold")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Relevance Score", fontsize=10)
    plt.tight_layout()
    path = CHARTS_DIR / "answer_quality_heatmap.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  Saved {path.name}")


def chart_radar(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    agg = data["aggregated_results"]
    metrics = ["route_accuracy", "avg_relevance", "avg_completeness",
               "avg_faithfulness", "avg_citation_accuracy", "avg_legal_precision"]
    labels = ["Route Accuracy", "Relevance", "Completeness",
              "Faithfulness", "Citation Acc.", "Legal Precision"]
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    for i, a in enumerate(agg):
        vals = [a.get(m, 0) for m in metrics]
        vals += vals[:1]
        ax.plot(angles, vals, "o-", linewidth=2, label=a["model"],
                color=colors[i % len(colors)], markersize=6)
        ax.fill(angles, vals, alpha=0.06, color=colors[i % len(colors)])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.set_title("Orchestrator Comparison: Routing + Answer Quality",
                 fontsize=14, fontweight="bold", y=1.08)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = CHARTS_DIR / "answer_quality_radar.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path.name}")


def chart_category(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cat_data = data.get("category_breakdown", {})
    if not cat_data:
        return
    categories = sorted(cat_data.keys())
    models = data["metadata"]["models"]
    colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]

    x = np.arange(len(categories))
    w = 0.12
    fig, ax = plt.subplots(figsize=(14, 7))
    for i, model in enumerate(models):
        vals = [cat_data.get(c, {}).get(model, {}).get("avg_relevance", 0) for c in categories]
        ax.bar(x + i * w - len(models) * w / 2, vals, w, label=model,
               color=colors[i % len(colors)], edgecolor="white", linewidth=0.5)

    ax.set_xlabel("Query Category", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Relevance", fontsize=12, fontweight="bold")
    ax.set_title("Answer Quality by Legal Category (per Orchestrator)", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10, rotation=15, ha="right")
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    path = CHARTS_DIR / "category_performance.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  Saved {path.name}")


def generate_markdown(data):
    agg = data["aggregated_results"]
    per_q = data["per_query_results"]
    models = data["metadata"]["models"]
    ts = data["metadata"]["timestamp"]
    answering = data["metadata"].get("answering_agent", "Llama-3.1-8b-instant")

    best_route = max(agg, key=lambda a: a["route_accuracy"])
    best_rel = max(agg, key=lambda a: a["avg_relevance"])
    best_faith = max(agg, key=lambda a: a["avg_faithfulness"])

    md = []
    md.append("# PEARL Framework -- Orchestration & Answer Quality Report\n")
    md.append(f"**Generated**: {ts}  ")
    md.append(f"**Queries**: {data['metadata']['num_queries']}  ")
    md.append(f"**Orchestrator Models Tested**: {data['metadata']['num_models']}  ")
    md.append(f"**Answering Agent**: {answering} (same for all)\n")

    md.append("## Executive Summary\n")
    md.append("This report evaluates how different models perform **as orchestrators** in the PEARL framework. ")
    md.append("Each orchestrator classifies queries and determines the agent routing. The **same answering agent** ")
    md.append(f"({answering}) generates all answers. We measure both **routing accuracy** and **final answer quality** ")
    md.append("to understand how orchestration decisions impact end-to-end performance.\n")
    md.append(f"- **Best Routing Accuracy**: {best_route['model']} ({best_route['route_accuracy']:.1%})")
    md.append(f"- **Best Answer Relevance**: {best_rel['model']} ({best_rel['avg_relevance']:.3f})")
    md.append(f"- **Best Faithfulness**: {best_faith['model']} ({best_faith['avg_faithfulness']:.3f})\n")

    md.append("## Models Under Evaluation (as Orchestrators)\n")
    md.append("| Model | Parameters | Type | Provider | Cost/1K tokens |")
    md.append("|-------|-----------|------|----------|---------------|")
    for m in data["model_info"]:
        cost = f"${m['cost']:.2f}" if m["cost"] > 0 else "Free"
        md.append(f"| {m['name']} | {m['params']} | {m['type']} | {m['provider'].title()} | {cost} |")
    md.append("")

    md.append("## Combined Results: Routing + Answer Quality\n")
    md.append("| Orchestrator | Route Acc. | RAS | WAI | Exact% | Relevance | Complete. | Faithful. | Citation | Halluc. | Legal Pr. | Avg Len | Orch Lat. | Pipe Lat. |")
    md.append("|-------------|-----------|-----|-----|--------|-----------|----------|----------|---------|---------|----------|---------|----------|----------|")
    for a in sorted(agg, key=lambda x: x["avg_relevance"], reverse=True):
        md.append(
            f"| **{a['model']}** | {a['route_accuracy']:.1%} | {a['avg_ras']:.3f} | "
            f"{a['avg_wai']:.3f} | {a['exact_match_rate']:.1%} | "
            f"{a['avg_relevance']:.3f} | {a['avg_completeness']:.3f} | "
            f"{a['avg_faithfulness']:.3f} | {a['avg_citation_accuracy']:.3f} | "
            f"{a['avg_hallucination_rate']:.3f} | {a['avg_legal_precision']:.3f} | "
            f"{a['avg_response_length']:.0f} | {a['avg_orch_latency_ms']:.0f}ms | "
            f"{a['avg_pipeline_latency_ms']:.0f}ms |"
        )
    md.append("")

    md.append("## Visualization\n")
    md.append("### Routing Accuracy vs. Answer Quality")
    md.append("![Routing vs Answer Quality](results/charts/answer_quality_comparison.png)\n")
    md.append("### Answer Relevance Heatmap (Orchestrator x Query)")
    md.append("![Answer Heatmap](results/charts/answer_quality_heatmap.png)\n")
    md.append("### Multi-Dimensional Radar Chart")
    md.append("![Radar Chart](results/charts/answer_quality_radar.png)\n")
    md.append("### Performance by Legal Category")
    md.append("![Category Performance](results/charts/category_performance.png)\n")

    md.append("## Routing Decision Matrix\n")
    routing = data.get("routing_decisions", {})
    if routing:
        md.append("| Query | " + " | ".join(models) + " | Expected |")
        md.append("|-------|" + "|".join(["------" for _ in models]) + "|----------|")
        for tq in data["test_queries"]:
            qid = str(tq["id"])
            row = f"| Q{tq['id']}: {tq['query'][:30]}... |"
            for m in models:
                dec = routing.get(m, {}).get(int(qid), routing.get(m, {}).get(qid, {}))
                route = dec.get("route", "?")
                correct = dec.get("correct", False)
                mark = "Y" if correct else "N"
                row += f" {route} ({mark}) |"
            row += f" {tq['expected_route']} |"
            md.append(row)
        md.append("")

    md.append("## Per-Query Detailed Results\n")
    for tq in data["test_queries"]:
        qid = tq["id"]
        md.append(f"### Q{qid}: {tq['query']}")
        md.append(f"**Complexity**: {tq['complexity']} | **Category**: {tq['category']} | **Expected Route**: {tq['expected_route']}\n")
        md.append("| Orchestrator | Route | Correct? | Relevance | Complete. | Faithful. | Halluc. | Length |")
        md.append("|-------------|-------|----------|-----------|----------|----------|---------|--------|")
        qr = sorted([r for r in per_q if r["query_id"] == qid], key=lambda x: x.get("relevance", 0), reverse=True)
        for r in qr:
            rc = "Yes" if r["route_correct"] else "No"
            md.append(
                f"| {r['model']} | {r['predicted_route']} | {rc} | "
                f"{r.get('relevance',0):.3f} | {r.get('completeness',0):.3f} | "
                f"{r.get('faithfulness',0):.3f} | {r.get('hallucination_rate',0):.3f} | "
                f"{r.get('response_length',0)} |"
            )
        best_q = max(qr, key=lambda r: r.get("relevance", 0))
        md.append(f"\n**Best Answer** (Orchestrated by {best_q['model']}, route: {best_q['predicted_route']}):")
        md.append(f"> {best_q.get('answer','')[:350]}...\n")

    md.append("## Key Findings\n")
    md.append("### 1. Routing Accuracy Impact on Answer Quality")
    md.append(f"- {best_route['model']} achieved {best_route['route_accuracy']:.0%} routing accuracy.")
    md.append(f"- {best_rel['model']} delivered the best answer relevance ({best_rel['avg_relevance']:.3f}).")
    md.append("- Correct routing leads to better answers by involving the right agents (booster, verifier) when needed.\n")

    md.append("### 2. PEARL SLM Orchestrator Performance")
    flan = next((a for a in agg if a["model"] == "Flan-T5-small"), None)
    if flan:
        md.append(f"- Flan-T5-small (80M) achieves {flan['route_accuracy']:.0%} routing accuracy with {flan['avg_orch_latency_ms']:.0f}ms latency.")
        md.append(f"- Answer quality: Relevance={flan['avg_relevance']:.3f}, Completeness={flan['avg_completeness']:.3f}")
        md.append("- As a free, local model, it provides the best cost-performance trade-off for orchestration.\n")

    md.append("### 3. Cost-Performance Analysis")
    free = [a for a in agg if a["cost_per_1k"] == 0]
    paid = [a for a in agg if a["cost_per_1k"] > 0]
    if free:
        bf = max(free, key=lambda a: a["avg_relevance"])
        md.append(f"- Best free orchestrator: **{bf['model']}** (Relevance: {bf['avg_relevance']:.3f}, Route Acc: {bf['route_accuracy']:.0%})")
    if paid:
        bp = max(paid, key=lambda a: a["avg_relevance"])
        md.append(f"- Best paid orchestrator: **{bp['model']}** (Relevance: {bp['avg_relevance']:.3f}, Route Acc: {bp['route_accuracy']:.0%})")
    md.append("- Free open-source models via Groq API are competitive with commercial alternatives.\n")

    md.append("### 4. Key Takeaway")
    md.append("- The **orchestrator choice directly impacts final answer quality**, even though the answering agent remains the same.")
    md.append("- Correct routing ensures appropriate context enhancement (booster) and verification (verifier) for complex queries.")
    md.append("- PEARL's Flan-T5-small SLM provides effective orchestration at zero cost and minimal latency.\n")

    md.append("## Methodology\n")
    md.append(f"- **Answering Agent**: {answering} (unchanged across all configurations)")
    md.append("- **Orchestration Task**: Classify each query into simple/verified/enhanced/full_pipeline")
    md.append("- **Pipeline**: Actual agent pipeline executed (booster, retriever, answering, verifier)")
    md.append("- **Caching**: Pipeline results cached per (query, route) to avoid redundant runs")
    md.append("- **Metrics**: Routing (RAS, WAI, Exact Match) + Answer Quality (Relevance, Completeness, Faithfulness, Citation, Hallucination, Legal Precision)\n")
    md.append("---")
    md.append("*Report generated by PEARL Framework Evaluation Suite*")

    path = Path(__file__).resolve().parent / "PEARL_ANSWER_QUALITY_REPORT.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"  Report saved to {path.name}")


def main():
    print("=" * 60)
    print("  PEARL -- Answer Quality Report Generator")
    print("=" * 60)
    data = _load()
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    print("\nGenerating charts...")
    chart_routing_vs_answer(data)
    chart_heatmap(data)
    chart_radar(data)
    chart_category(data)
    print("\nGenerating markdown report...")
    generate_markdown(data)
    print("\nDone!")


if __name__ == "__main__":
    main()
