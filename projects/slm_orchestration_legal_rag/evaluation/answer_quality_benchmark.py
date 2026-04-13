"""
PEARL Framework -- Orchestration + Answer Quality Benchmark
=============================================================
Tests different models AS ORCHESTRATORS, runs the actual agent pipeline
with the SAME answering agent (Llama-3.1-8b), and evaluates both:
  1. Routing accuracy  (RAS, WAI, exact match)
  2. Answer quality    (relevance, completeness, faithfulness, etc.)

Models used as orchestrators:
  - Flan-T5-small (80M)     -- Our trained SLM (local, free)
  - Llama-3.1-8b-instant    -- Groq API (free)
  - Llama-3.3-70b-versatile -- Groq API (free)
  - Qwen3-32b               -- Groq API (free)
  - GPT-4o-mini              -- OpenAI API
  - GPT-3.5-turbo            -- OpenAI API

Answering agent: Always Llama-3.1-8b via Groq (unchanged)
"""

import asyncio, json, time, re, sys, os
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import config

import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("booster_agent").setLevel(logging.WARNING)
logging.getLogger("retriever_agent").setLevel(logging.WARNING)
logging.getLogger("answering_agent").setLevel(logging.WARNING)
logging.getLogger("citation_verifier").setLevel(logging.WARNING)
logging.getLogger("orchestrators").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

RESULTS_DIR = Path(__file__).resolve().parent / "results"

ROUTE_TO_SEQUENCE = {
    "simple":        ["retriever", "answering"],
    "verified":      ["retriever", "answering", "verifier"],
    "enhanced":      ["booster", "retriever", "answering"],
    "full_pipeline": ["booster", "retriever", "answering", "verifier"],
}

CLASSIFICATION_PROMPT = (
    "You are a legal query router. Classify the complexity of this legal query "
    "into exactly ONE of these categories:\n"
    "- simple: basic factual legal questions\n"
    "- verified: questions needing factual verification\n"
    "- enhanced: questions needing context enhancement or comparison\n"
    "- full_pipeline: complex analytical questions needing all processing\n\n"
    "Respond with ONLY one word: simple, verified, enhanced, or full_pipeline\n\n"
    "Query: {query}\n\nClassification:"
)

TEST_QUERIES = [
    {"id": 1, "query": "What is Article 21 of the Indian Constitution?",
     "expected_route": "simple", "complexity": "simple", "category": "Constitutional Law",
     "key_terms": ["Article 21", "right to life", "personal liberty", "Maneka Gandhi", "due process"]},
    {"id": 2, "query": "Define habeas corpus in Indian law",
     "expected_route": "simple", "complexity": "simple", "category": "Writs",
     "key_terms": ["habeas corpus", "writ", "Article 32", "Article 226", "unlawful detention"]},
    {"id": 3, "query": "What are the fundamental rights?",
     "expected_route": "simple", "complexity": "simple", "category": "Constitutional Law",
     "key_terms": ["Part III", "Article 14", "Article 19", "Article 21", "equality", "freedom"]},
    {"id": 4, "query": "What is the punishment for cybercrime under IT Act 2000?",
     "expected_route": "verified", "complexity": "moderate", "category": "Cyber Law",
     "key_terms": ["IT Act 2000", "Section 43", "Section 66", "Section 67", "hacking", "cyber terrorism"]},
    {"id": 5, "query": "How has the Supreme Court interpreted Article 32?",
     "expected_route": "verified", "complexity": "moderate", "category": "Constitutional Law",
     "key_terms": ["Article 32", "writ jurisdiction", "fundamental rights", "Romesh Thappar"]},
    {"id": 6, "query": "Compare Article 14 and Article 21",
     "expected_route": "enhanced", "complexity": "complex", "category": "Comparative Analysis",
     "key_terms": ["Article 14", "Article 21", "equality", "life and liberty", "reasonable classification"]},
    {"id": 7, "query": "Analyze implications of Section 498A IPC on matrimonial disputes",
     "expected_route": "full_pipeline", "complexity": "complex", "category": "Criminal Law",
     "key_terms": ["Section 498A", "IPC", "cruelty", "dowry", "misuse", "Arnesh Kumar"]},
    {"id": 8, "query": "Explain the doctrine of basic structure",
     "expected_route": "verified", "complexity": "moderate", "category": "Constitutional Law",
     "key_terms": ["basic structure", "Kesavananda Bharati", "Article 368", "amendment power"]},
    {"id": 9, "query": "Critically examine role of judiciary in protecting civil liberties",
     "expected_route": "full_pipeline", "complexity": "complex", "category": "Analytical",
     "key_terms": ["judiciary", "civil liberties", "PIL", "judicial activism", "Article 21"]},
    {"id": 10, "query": "What are the types of writs available under Indian Constitution?",
     "expected_route": "verified", "complexity": "moderate", "category": "Writs",
     "key_terms": ["habeas corpus", "mandamus", "certiorari", "prohibition", "quo warranto"]},
]

GROUND_TRUTH_SEQUENCES = {
    1: ["retriever", "answering"],
    2: ["retriever", "answering"],
    3: ["retriever", "answering"],
    4: ["retriever", "answering", "verifier"],
    5: ["retriever", "answering", "verifier"],
    6: ["booster", "retriever", "answering"],
    7: ["booster", "retriever", "answering", "verifier"],
    8: ["retriever", "answering"],
    9: ["booster", "retriever", "answering", "verifier"],
    10: ["retriever", "answering"],
}

VALID_ARTICLES = set(range(1, 396))
KNOWN_CASES = [
    "Kesavananda Bharati", "Maneka Gandhi", "Minerva Mills",
    "Golaknath", "ADM Jabalpur", "Romesh Thappar", "Vishaka",
    "Arnesh Kumar", "Navtej Singh Johar", "Puttaswamy",
    "S.R. Bommai", "Indira Gandhi", "I.R. Coelho",
    "M.C. Mehta", "Olga Tellis", "Bandhua Mukti Morcha",
    "D.K. Basu", "Hussainara Khatoon", "Shah Bano",
    "Shreya Singhal", "K.S. Puttaswamy", "Shayara Bano",
]

ORCHESTRATOR_MODELS = [
    {"name": "Flan-T5-small",  "provider": "local",  "model_id": "google/flan-t5-small", "params": "80M",  "type": "Trained SLM",     "cost": 0.0},
    {"name": "Llama-3.1-8b",   "provider": "groq",   "model_id": "llama-3.1-8b-instant", "params": "8B",   "type": "Open-Source SLM", "cost": 0.0},
    {"name": "Llama-3.3-70b",  "provider": "groq",   "model_id": "llama-3.3-70b-versatile", "params": "70B", "type": "Open-Source LLM", "cost": 0.0},
    {"name": "Qwen3-32b",      "provider": "groq",   "model_id": "qwen/qwen3-32b",       "params": "32B",  "type": "Open-Source LLM", "cost": 0.0},
    {"name": "GPT-4o-mini",    "provider": "openai", "model_id": "gpt-4o-mini",           "params": "~8B",  "type": "Commercial LLM", "cost": 0.15},
    {"name": "GPT-3.5-turbo",  "provider": "openai", "model_id": "gpt-3.5-turbo",         "params": "~175B","type": "Commercial LLM", "cost": 0.50},
]


# ---- Routing metrics ----

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


# ---- Answer quality metrics ----

def metric_relevance(answer, query, key_terms):
    if not answer:
        return 0.0
    al = answer.lower()
    qwords = set(w.lower() for w in query.split() if len(w) > 3)
    qhits = sum(1 for w in qwords if w in al)
    qs = qhits / max(len(qwords), 1)
    thits = sum(1 for t in key_terms if t.lower() in al)
    ts = thits / max(len(key_terms), 1)
    lok = 1.0 if len(answer.split()) >= 30 else len(answer.split()) / 30.0
    return round(min(1.0, qs * 0.3 + ts * 0.5 + lok * 0.2), 4)


def metric_completeness(answer, key_terms):
    if not answer:
        return 0.0
    al = answer.lower()
    hits = sum(1 for t in key_terms if t.lower() in al)
    return round(hits / max(len(key_terms), 1), 4)


def metric_citation_accuracy(answer):
    if not answer:
        return 0.0
    arts = re.findall(r"Article\s+(\d+[A-Z]?)", answer, re.IGNORECASE)
    secs = re.findall(r"Section\s+(\d+[A-Z]?)", answer, re.IGNORECASE)
    acts = re.findall(r"(?:Act|Code)[\s,]+(\d{4})", answer)
    total = len(arts) + len(secs) + len(acts)
    if total == 0:
        return 0.3
    valid = 0
    for a in arts:
        num = int(re.match(r"\d+", a).group())
        if num in VALID_ARTICLES:
            valid += 1
    valid += len(secs)
    for y in acts:
        if 1800 <= int(y) <= 2025:
            valid += 1
    return round(valid / total, 4)


def metric_hallucination(answer):
    if not answer or len(answer.split()) < 10:
        return 1.0
    arts = re.findall(r"Article\s+(\d+[A-Z]*)", answer, re.IGNORECASE)
    bad = sum(1 for a in arts if int(re.match(r"\d+", a).group()) > 395)
    cases = re.findall(r"(?:in the case of|landmark case)\s+[A-Z][a-z]+\s+(?:vs?\.?|versus)\s+[A-Z]", answer, re.IGNORECASE)
    known = sum(1 for c in KNOWN_CASES if c.lower() in answer.lower())
    unk = max(0, len(cases) - known)
    total = len(arts) + len(cases) + 1
    return round(min(1.0, (bad + unk) / total), 4)


def metric_legal_precision(answer, key_terms):
    if not answer:
        return 0.0
    al = answer.lower()
    hits = sum(1 for t in key_terms if t.lower() in al)
    ts = hits / max(len(key_terms), 1)
    arts = len(re.findall(r"Article\s+\d+", answer, re.IGNORECASE))
    secs = len(re.findall(r"Section\s+\d+", answer, re.IGNORECASE))
    cas = sum(1 for c in KNOWN_CASES if c.lower() in al)
    rs = min(1.0, (arts + secs + cas) / 5.0)
    return round(ts * 0.6 + rs * 0.4, 4)


def metric_faithfulness(answer, key_terms):
    if not answer:
        return 0.0
    h = metric_hallucination(answer)
    c = metric_citation_accuracy(answer)
    p = metric_legal_precision(answer, key_terms)
    return round((1.0 - h) * 0.4 + c * 0.3 + p * 0.3, 4)


def evaluate_answer(answer, query, key_terms):
    return {
        "relevance": metric_relevance(answer, query, key_terms),
        "completeness": metric_completeness(answer, key_terms),
        "faithfulness": metric_faithfulness(answer, key_terms),
        "citation_accuracy": metric_citation_accuracy(answer),
        "hallucination_rate": metric_hallucination(answer),
        "legal_precision": metric_legal_precision(answer, key_terms),
        "response_length": len(answer.split()),
    }


# ---- Orchestration calls ----

def _strip_thinking(text):
    if "<think>" in text and "</think>" in text:
        return text.split("</think>", 1)[-1].strip()
    if "<think>" in text:
        return re.sub(r"<think>.*", "", text, flags=re.DOTALL).strip()
    return text


def classify_with_groq(query, model_id):
    from groq import Groq
    client = Groq(api_key=config.api.GROQ_API_KEY)
    prompt = CLASSIFICATION_PROMPT.format(query=query)
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0, max_tokens=20,
    )
    lat = (time.perf_counter() - start) * 1000
    raw = _strip_thinking(resp.choices[0].message.content or "").strip().lower()
    for route in ["full_pipeline", "enhanced", "verified", "simple"]:
        if route in raw:
            return route, round(lat, 1)
    return "simple", round(lat, 1)


def classify_with_openai(query, model_id):
    from openai import OpenAI
    client = OpenAI(api_key=config.api.OPENAI_API_KEY)
    prompt = CLASSIFICATION_PROMPT.format(query=query)
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0, max_tokens=20,
    )
    lat = (time.perf_counter() - start) * 1000
    raw = resp.choices[0].message.content.strip().lower()
    for route in ["full_pipeline", "enhanced", "verified", "simple"]:
        if route in raw:
            return route, round(lat, 1)
    return "simple", round(lat, 1)


_flan_orch = None

async def _get_flan_orch():
    global _flan_orch
    if _flan_orch is None:
        from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator
        _flan_orch = FlanT5Orchestrator({"openai_api_key": config.api.OPENAI_API_KEY,
                                         "model_name": "google/flan-t5-small"})
    return _flan_orch

def _release_flan_orch():
    global _flan_orch
    if _flan_orch is not None:
        del _flan_orch
        _flan_orch = None
        import gc; gc.collect()

async def classify_with_flan_t5(query):
    orch = await _get_flan_orch()
    start = time.perf_counter()
    analysis = await orch.analyze_query(query)
    agents = await orch.route_to_agents(query, analysis)
    lat = (time.perf_counter() - start) * 1000
    seq = tuple(agents)
    for route, s in ROUTE_TO_SEQUENCE.items():
        if tuple(s) == seq:
            return route, round(lat, 1)
    return "simple", round(lat, 1)


# ---- Pipeline execution ----

async def init_pipeline():
    """Initialize agents once, reuse for all pipeline runs."""
    from booster_agent import PromptBooster
    from retriever_agent import RetrieverAgent
    from answering_agent import AnsweringAgent
    from citation_verifier import CitationVerifier
    from agent_adapters import (
        BoosterAdapter, RetrieverAdapter,
        AnsweringAdapter, VerifierAdapter,
    )

    agents = {
        "booster": BoosterAdapter(PromptBooster()),
        "retriever": RetrieverAdapter(RetrieverAgent()),
        "answering": AnsweringAdapter(AnsweringAgent()),
        "verifier": VerifierAdapter(CitationVerifier()),
    }
    for name, a in agents.items():
        try:
            await a.initialize()
        except Exception as e:
            print(f"  [WARN] {name}: {e}")
    return agents


async def run_pipeline(query, route, agents):
    """Run the actual agent pipeline for a given route."""
    sequence = ROUTE_TO_SEQUENCE.get(route, ["retriever", "answering"])
    context = {"query": query, "documents": [], "answer": "", "citations": []}

    for agent_name in sequence:
        if agent_name not in agents:
            continue
        try:
            agent = agents[agent_name]
            if agent_name == "booster":
                r = await agent.process(query)
                context["enhanced_query"] = r.get("boosted_query", query)
                context["top_k"] = r.get("top_k", 5)
            elif agent_name == "retriever":
                sq = context.get("enhanced_query", query)
                r = await agent.process(sq, k=context.get("top_k", 5))
                context["documents"] = r.get("documents", [])
            elif agent_name == "answering":
                r = await agent.process(query, context["documents"])
                context["answer"] = r.get("answer", "")
                context["citations"] = r.get("citations", [])
                context["claims"] = r.get("claims", [])
            elif agent_name == "verifier":
                r = await agent.process(
                    context["answer"], context["citations"],
                    claims=context.get("claims"),
                    retrieved_docs=context.get("documents", []),
                )
                context["verification_score"] = r.get("verification_score", 0)
                context["verified_answer"] = r.get("verified_answer", context["answer"])
        except Exception as e:
            print(f"      [ERR] {agent_name}: {str(e)[:60]}")

    return {
        "answer": context.get("verified_answer", context.get("answer", "")),
        "documents": context.get("documents", []),
        "citations": context.get("citations", []),
        "verification_score": context.get("verification_score"),
        "sequence": sequence,
    }


# ---- Main benchmark ----

async def run_benchmark():
    print("=" * 72)
    print("  PEARL -- Orchestration + Answer Quality Benchmark")
    print("  (Different models as orchestrators, same answering agent)")
    print("=" * 72)

    # Phase 1: Get routing decisions (lightweight, no pipeline agents needed)
    print("\n[1/4] Getting routing decisions from all orchestrator models...")
    routing_decisions = {}
    for minfo in ORCHESTRATOR_MODELS:
        name = minfo["name"]
        provider = minfo["provider"]
        mid = minfo["model_id"]
        print(f"\n  {name} ({minfo['params']}, {provider}):")
        routing_decisions[name] = {}

        for tq in TEST_QUERIES:
            q = tq["query"]
            try:
                if provider == "groq":
                    route, lat = classify_with_groq(q, mid)
                elif provider == "openai":
                    route, lat = classify_with_openai(q, mid)
                else:
                    route, lat = await classify_with_flan_t5(q)
            except Exception as e:
                print(f"    Q{tq['id']}: ERR {str(e)[:40]}")
                route, lat = "simple", 0
            gt_route = tq["expected_route"]
            match = "Y" if route == gt_route else "N"
            print(f"    Q{tq['id']:>2}: {route:<14} (expected: {gt_route:<14}) [{match}] {lat:>6.0f}ms")
            routing_decisions[name][tq["id"]] = {
                "route": route, "latency_ms": lat,
                "expected": gt_route, "correct": route == gt_route,
            }
            time.sleep(0.3)

    # Release Flan-T5 orchestrator to free memory before pipeline
    _release_flan_orch()
    import gc; gc.collect()

    print("\n[2/4] Initializing agent pipeline...")
    agents = await init_pipeline()
    print("  Agents ready.")

    # Phase 3: Run pipeline for unique (query, route) combinations
    print("\n[3/4] Running pipeline for unique (query, route) combinations...")
    needed_runs = {}
    for mname, decisions in routing_decisions.items():
        for qid, dec in decisions.items():
            key = (qid, dec["route"])
            if key not in needed_runs:
                needed_runs[key] = None

    total_runs = len(needed_runs)
    print(f"  {total_runs} unique pipeline runs needed (cached across models)")

    pipeline_cache = {}
    for idx, (key, _) in enumerate(needed_runs.items()):
        qid, route = key
        tq = next(t for t in TEST_QUERIES if t["id"] == qid)
        print(f"  [{idx+1}/{total_runs}] Q{qid} route={route}...", end=" ", flush=True)
        start = time.perf_counter()
        result = await run_pipeline(tq["query"], route, agents)
        plat = (time.perf_counter() - start) * 1000
        result["pipeline_latency_ms"] = round(plat, 1)
        pipeline_cache[key] = result
        ans_preview = result["answer"][:60].replace("\n", " ") if result["answer"] else "(empty)"
        print(f"OK {plat:>6.0f}ms | {ans_preview}...")
        time.sleep(0.5)

    # Phase 3: Combine routing + answer quality
    print("\n[4/4] Evaluating results...")
    all_results = []
    model_aggregates = []

    for minfo in ORCHESTRATOR_MODELS:
        name = minfo["name"]
        decisions = routing_decisions.get(name, {})
        model_results = []

        for tq in TEST_QUERIES:
            qid = tq["id"]
            dec = decisions.get(qid, {"route": "simple", "latency_ms": 0, "correct": False})
            route = dec["route"]
            gt_route = tq["expected_route"]
            gt_seq = GROUND_TRUTH_SEQUENCES[qid]
            pred_seq = ROUTE_TO_SEQUENCE.get(route, ["retriever", "answering"])

            pipe_result = pipeline_cache.get((qid, route), {})
            answer = pipe_result.get("answer", "")
            metrics = evaluate_answer(answer, tq["query"], tq["key_terms"])

            entry = {
                "model": name, "provider": minfo["provider"],
                "query_id": qid, "query": tq["query"],
                "complexity": tq["complexity"], "category": tq["category"],
                "predicted_route": route, "expected_route": gt_route,
                "route_correct": route == gt_route,
                "predicted_sequence": pred_seq,
                "ground_truth_sequence": gt_seq,
                "ras": round(compute_ras(pred_seq, gt_seq), 4),
                "wai": round(compute_wai(pred_seq, gt_seq), 4),
                "exact_match": pred_seq == gt_seq,
                "orchestration_latency_ms": dec["latency_ms"],
                "pipeline_latency_ms": pipe_result.get("pipeline_latency_ms", 0),
                "answer": answer[:3000],
                "num_documents": len(pipe_result.get("documents", [])),
                "verification_score": pipe_result.get("verification_score"),
                **metrics,
            }
            model_results.append(entry)
            all_results.append(entry)

        n = len(model_results)
        if n > 0:
            agg = {
                "model": name, "provider": minfo["provider"],
                "params": minfo["params"], "type": minfo["type"],
                "cost_per_1k": minfo["cost"],
                # Routing metrics
                "route_accuracy": round(sum(1 for r in model_results if r["route_correct"]) / n, 4),
                "avg_ras": round(sum(r["ras"] for r in model_results) / n, 4),
                "avg_wai": round(sum(r["wai"] for r in model_results) / n, 4),
                "exact_match_rate": round(sum(1 for r in model_results if r["exact_match"]) / n, 4),
                "avg_orch_latency_ms": round(sum(r["orchestration_latency_ms"] for r in model_results) / n, 1),
                # Answer quality metrics
                "avg_relevance": round(sum(r["relevance"] for r in model_results) / n, 4),
                "avg_completeness": round(sum(r["completeness"] for r in model_results) / n, 4),
                "avg_faithfulness": round(sum(r["faithfulness"] for r in model_results) / n, 4),
                "avg_citation_accuracy": round(sum(r["citation_accuracy"] for r in model_results) / n, 4),
                "avg_hallucination_rate": round(sum(r["hallucination_rate"] for r in model_results) / n, 4),
                "avg_legal_precision": round(sum(r["legal_precision"] for r in model_results) / n, 4),
                "avg_response_length": round(sum(r["response_length"] for r in model_results) / n, 1),
                "avg_pipeline_latency_ms": round(sum(r["pipeline_latency_ms"] for r in model_results) / n, 1),
            }
            model_aggregates.append(agg)

    # Category breakdown
    categories = {}
    for r in all_results:
        cat = r["category"]
        model = r["model"]
        if cat not in categories:
            categories[cat] = {}
        if model not in categories[cat]:
            categories[cat][model] = []
        categories[cat][model].append(r)

    category_summary = {}
    for cat, models_data in categories.items():
        category_summary[cat] = {}
        for model, results in models_data.items():
            n = len(results)
            category_summary[cat][model] = {
                "route_accuracy": round(sum(1 for r in results if r["route_correct"]) / n, 4),
                "avg_relevance": round(sum(r["relevance"] for r in results) / n, 4),
                "avg_completeness": round(sum(r["completeness"] for r in results) / n, 4),
                "avg_faithfulness": round(sum(r["faithfulness"] for r in results) / n, 4),
            }

    # Save
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "num_queries": len(TEST_QUERIES),
            "num_models": len(ORCHESTRATOR_MODELS),
            "models": [m["name"] for m in ORCHESTRATOR_MODELS],
            "evaluation_type": "orchestration_routing + pipeline_answer_quality",
            "answering_agent": "Llama-3.1-8b-instant (via Groq, unchanged)",
        },
        "model_info": ORCHESTRATOR_MODELS,
        "test_queries": [{k: v for k, v in tq.items()} for tq in TEST_QUERIES],
        "ground_truth_sequences": {str(k): v for k, v in GROUND_TRUTH_SEQUENCES.items()},
        "per_query_results": all_results,
        "aggregated_results": model_aggregates,
        "category_breakdown": category_summary,
        "routing_decisions": routing_decisions,
    }
    out_path = RESULTS_DIR / "answer_quality_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Results saved to {out_path}")

    # Summary
    print("\n" + "=" * 120)
    print("  COMBINED SUMMARY: ORCHESTRATION + ANSWER QUALITY")
    print("=" * 120)
    hdr = f"{'Model':<18} {'RouteAcc':>8} {'RAS':>6} {'WAI':>6} {'Exact%':>7} | {'Relev':>6} {'Compl':>6} {'Faith':>6} {'Citat':>6} {'Halluc':>6} {'LegPr':>6} {'Len':>5} | {'OrchLat':>8} {'PipeLat':>8}"
    print(hdr)
    print("-" * len(hdr))
    for a in sorted(model_aggregates, key=lambda x: x["avg_relevance"], reverse=True):
        print(
            f"{a['model']:<18} {a['route_accuracy']:>8.1%} {a['avg_ras']:>6.3f} "
            f"{a['avg_wai']:>6.3f} {a['exact_match_rate']*100:>6.1f}% | "
            f"{a['avg_relevance']:>6.3f} {a['avg_completeness']:>6.3f} "
            f"{a['avg_faithfulness']:>6.3f} {a['avg_citation_accuracy']:>6.3f} "
            f"{a['avg_hallucination_rate']:>6.3f} {a['avg_legal_precision']:>6.3f} "
            f"{a['avg_response_length']:>5.0f} | "
            f"{a['avg_orch_latency_ms']:>7.0f}ms {a['avg_pipeline_latency_ms']:>7.0f}ms"
        )
    print("=" * 120)


if __name__ == "__main__":
    os.chdir(str(Path(__file__).resolve().parent.parent))
    asyncio.run(run_benchmark())
