"""
Convert GPT-4 expert traces into step-by-step orchestration training data.

Each original trace (query -> agent_sequence) becomes N+1 training examples,
one per orchestration step plus a final "done" step.

Original:  query="bail", sequence=[booster, retriever, answering]
Becomes:
  "orchestrate: bail | history: none"                         -> "booster"
  "orchestrate: bail | history: booster"                      -> "retriever"
  "orchestrate: bail | history: booster,retriever"            -> "answering"
  "orchestrate: bail | history: booster,retriever,answering"  -> "done"
"""

import json
import random
from pathlib import Path
from collections import Counter


SEQUENCE_NORMALIZATION = {
    "retriever,verifier,answering": ["retriever", "answering", "verifier"],
    "booster,retriever,verifier,answering": ["booster", "retriever", "answering", "verifier"],
}


def normalize_sequence(seq_str):
    if seq_str in SEQUENCE_NORMALIZATION:
        return SEQUENCE_NORMALIZATION[seq_str]
    return [a.strip() for a in seq_str.split(",") if a.strip()]


def trace_to_steps(query, agent_sequence):
    steps = []
    for i, agent in enumerate(agent_sequence):
        history = agent_sequence[:i]
        hist_str = ",".join(history) if history else "none"
        steps.append({
            "input": f"orchestrate: {query} | history: {hist_str}",
            "target": agent,
            "query": query,
            "step": i + 1,
            "history": history,
        })
    final_hist = ",".join(agent_sequence)
    steps.append({
        "input": f"orchestrate: {query} | history: {final_hist}",
        "target": "done",
        "query": query,
        "step": len(agent_sequence) + 1,
        "history": agent_sequence,
    })
    return steps


def main():
    raw_path = Path("data/expert_traces/training_data.jsonl")
    synth_path = Path("data/expert_traces/classification_training_data_v2.jsonl")
    out_path = Path("data/expert_traces/stepwise_training_data.jsonl")

    all_steps = []

    # --- from original GPT-4 traces ---
    print("Processing original GPT-4 traces...")
    with open(raw_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            query = ex.get("query", "")
            seq = normalize_sequence(ex["target"])
            if query and seq:
                all_steps.extend(trace_to_steps(query, seq))

    # --- from synthetic / augmented data ---
    print("Processing augmented classification data...")
    CLASS_TO_SEQ = {
        "simple": ["retriever", "answering"],
        "verified": ["retriever", "answering", "verifier"],
        "enhanced": ["booster", "retriever", "answering"],
        "full_pipeline": ["booster", "retriever", "answering", "verifier"],
    }
    seen_queries = {s["query"] for s in all_steps}
    with open(synth_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            query = ex.get("query", "")
            cls = ex.get("target", "")
            if query and cls in CLASS_TO_SEQ and query not in seen_queries:
                seq = CLASS_TO_SEQ[cls]
                all_steps.extend(trace_to_steps(query, seq))
                seen_queries.add(query)

    random.shuffle(all_steps)

    # Stats
    target_counts = Counter(s["target"] for s in all_steps)
    print(f"\nStep-wise training data generated:")
    for t, c in sorted(target_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:15s}: {c}")
    print(f"  {'TOTAL':15s}: {len(all_steps)}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for s in all_steps:
            f.write(json.dumps(s) + "\n")
    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
