"""
SLM Orchestration Framework - Main Application
Demonstrates Flan-T5-small orchestrating multi-agent legal RAG system
with support for all orchestrator types including iterative SLM orchestrators.
"""

import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path
import argparse
import torch

from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator
from orchestrators.gpt4_orchestrator import GPT4Orchestrator
from orchestrators.rule_orchestrator import RuleBasedOrchestrator
from orchestrators.no_orchestrator import NoOrchestrator
from orchestrators.iterative_slm_orchestrator import IterativeSLMOrchestrator
from orchestrators.gpt35_orchestrator import GPT35Orchestrator

from booster_agent import PromptBooster
from retriever_agent import RetrieverAgent
from answering_agent import AnsweringAgent
from citation_verifier import CitationVerifier
from multilingual_agent import MultilingualAgent

from agent_adapters import (
    BoosterAdapter, RetrieverAdapter, AnsweringAdapter,
    VerifierAdapter, MultilingualAdapter
)

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ORCHESTRATOR_CHOICES = [
    "flan_t5", "iterative_small", "iterative_base", "iterative_large",
    "gpt4", "gpt35", "rule", "none",
]


class SLMOrchestrationApp:
    """
    Main application demonstrating SLM orchestration.

    Supports all orchestrator types for comparison:
      iterative_small  -- Flan-T5-small  (80M) trained iterative orchestrator
      iterative_base   -- Flan-T5-base (250M) trained iterative orchestrator
      iterative_large  -- Flan-T5-large (780M) trained iterative orchestrator
      flan_t5          -- Original Flan-T5-small classifier orchestrator
      gpt4             -- GPT-4 zero-shot baseline
      gpt35            -- GPT-3.5-turbo zero-shot baseline
      rule             -- Keyword rule-based
      none             -- No orchestration (always retriever+answering)
    """

    def __init__(self, orchestrator_type: str = "flan_t5"):
        self.orchestrator_type = orchestrator_type
        self.orchestrator = None
        self.agents = {}
        self.app_config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        return {
            "model_name": "google/flan-t5-small",
            "openai_api_key": config.api.OPENAI_API_KEY,
            "groq_api_key": config.api.GROQ_API_KEY,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        }

    async def initialize(self):
        print(f"Initializing SLM Orchestration App with '{self.orchestrator_type}'")

        otype = self.orchestrator_type
        cfg = self.app_config

        if otype == "iterative_small":
            path = Path(__file__).resolve().parent / "models" / "iterative_small"
            model = str(path) if path.exists() else "google/flan-t5-small"
            self.orchestrator = IterativeSLMOrchestrator(cfg, model_path=model)
        elif otype == "iterative_base":
            path = Path(__file__).resolve().parent / "models" / "iterative_base"
            model = str(path) if path.exists() else "google/flan-t5-small"
            self.orchestrator = IterativeSLMOrchestrator(cfg, model_path=model)
        elif otype == "iterative_large":
            path = Path(__file__).resolve().parent / "models" / "iterative_large"
            model = str(path) if path.exists() else "google/flan-t5-large"
            self.orchestrator = IterativeSLMOrchestrator(cfg, model_path=model)
        elif otype == "flan_t5":
            self.orchestrator = FlanT5Orchestrator(cfg)
        elif otype == "gpt4":
            self.orchestrator = GPT4Orchestrator(cfg)
        elif otype == "gpt35":
            self.orchestrator = GPT35Orchestrator(cfg)
        elif otype == "rule":
            self.orchestrator = RuleBasedOrchestrator(cfg)
        elif otype == "none":
            self.orchestrator = NoOrchestrator(cfg)
        else:
            raise ValueError(f"Unknown orchestrator type: {otype}. Choose from {ORCHESTRATOR_CHOICES}")

        if self.orchestrator and hasattr(self.orchestrator, "initialize"):
            await self.orchestrator.initialize()

        print("  Initializing agents...")
        self.agents = {
            "booster": BoosterAdapter(PromptBooster()),
            "retriever": RetrieverAdapter(RetrieverAgent()),
            "answering": AnsweringAdapter(AnsweringAgent()),
            "verifier": VerifierAdapter(CitationVerifier()),
            "multilingual": MultilingualAdapter(MultilingualAgent()),
        }

        for name, agent in self.agents.items():
            try:
                await agent.initialize()
                print(f"    [OK] {name} agent ready")
            except Exception as e:
                print(f"    [FAIL] {name}: {e}")

        print("All systems ready!")

    async def process_query(self, query: str) -> Dict[str, Any]:
        print(f"\nProcessing query: {query}")

        print("  Analyzing query...")
        analysis = await self.orchestrator.analyze_query(query)
        print(f"    Complexity: {analysis.get('complexity', 'unknown')}")

        print("  Determining agent sequence...")
        agent_sequence = await self.orchestrator.route_to_agents(query, analysis)
        print(f"    Sequence: {' -> '.join(agent_sequence)}")

        print("  Executing workflow...")
        result = await self._execute_agent_workflow(query, agent_sequence)

        answer_confidence = result.get("answer_confidence", result.get("confidence", 0.5))
        verification_score = result.get("verification_score")
        if verification_score is None:
            verification_score = answer_confidence

        slm_confidence = analysis.get("confidence", 0.7)
        doc_count = len(result.get("documents", []))

        if doc_count > 0:
            docs = result.get("documents", [])
            if docs and any(d.get("similarity_score", 0) > 0 for d in docs):
                avg_sim = sum(d.get("similarity_score", 0.0) for d in docs) / len(docs)
                doc_confidence = min(doc_count / 5.0, 1.0) * 0.4 + min(max(avg_sim, 0), 1) * 0.6
            else:
                doc_confidence = min(doc_count / 5.0, 1.0)
        else:
            doc_confidence = 0.0

        slm_confidence = min(max(slm_confidence, 0), 1)
        verification_score = min(max(verification_score, 0), 1)
        doc_confidence = min(max(doc_confidence, 0), 1)

        overall_confidence = slm_confidence * 0.30 + verification_score * 0.45 + doc_confidence * 0.25
        overall_confidence = min(max(overall_confidence, 0), 1)
        result["confidence"] = overall_confidence

        result["orchestration"] = {
            "orchestrator": self.orchestrator_type,
            "analysis": analysis,
            "agent_sequence": agent_sequence,
            "metrics": self.orchestrator.get_metrics(),
        }
        return result

    async def _execute_agent_workflow(self, query: str, agent_sequence: List[str]) -> Dict[str, Any]:
        context = {"query": query, "documents": [], "answer": "", "citations": []}
        reasoning_traces = {}

        for agent_name in agent_sequence:
            if agent_name not in self.agents:
                print(f"    [?] Unknown agent: {agent_name}")
                continue

            print(f"    Running {agent_name}...")
            try:
                agent = self.agents[agent_name]
                if agent_name == "booster":
                    result = await agent.process(query)
                    context["enhanced_query"] = result.get("boosted_query", query)
                    context["top_k"] = result.get("top_k", 5)
                    context["retrieval_mode"] = result.get("retrieval_mode", "both")
                elif agent_name == "retriever":
                    search_query = context.get("enhanced_query", query)
                    k = context.get("top_k", 5)
                    filters = None
                    rm = context.get("retrieval_mode", "both")
                    if rm and rm != "both":
                        filters = {"doc_type": rm}
                    result = await agent.process(search_query, k=k, filters=filters)
                    context["documents"] = result.get("documents", [])
                elif agent_name == "answering":
                    result = await agent.process(context["query"], context["documents"])
                    context["answer"] = result.get("answer", "")
                    context["citations"] = result.get("citations", [])
                    context["answer_confidence"] = result.get("confidence", 0.5)
                    context["claims"] = result.get("claims", [])
                elif agent_name == "verifier":
                    claims = context.get("claims")
                    docs = context.get("documents", [])
                    result = await agent.process(context["answer"], context["citations"], claims=claims, retrieved_docs=docs)
                    context["verified_answer"] = result.get("verified_answer", context["answer"])
                    context["verification_score"] = result.get("verification_score", 0.0)
                    context["claims_verified"] = result.get("claims_verified", 0)
                    context["total_claims"] = result.get("total_claims", 0)
                    context["verification_issues"] = result.get("issues", [])
                elif agent_name == "multilingual":
                    result = await agent.process(query)
                    context["language"] = result.get("language", "en")
                    context["translated_query"] = result.get("translated_query", query)
                trace = getattr(agent, "last_trace", [])
                if trace:
                    reasoning_traces[agent_name] = [
                        {"thought": s.thought, "action": s.action,
                         "action_input": s.action_input,
                         "observation": str(s.observation)[:500]}
                        for s in trace
                    ]
                print(f"      [OK] {agent_name} completed ({len(trace)} reasoning steps)")
            except Exception as e:
                print(f"      [FAIL] {agent_name}: {e}")
                continue

        return {
            "query": query,
            "answer": context.get("verified_answer", context.get("answer", "")),
            "citations": context.get("citations", []),
            "documents": context.get("documents", []),
            "confidence": context.get("verification_score", context.get("answer_confidence", 0.5)),
            "answer_confidence": context.get("answer_confidence", 0.5),
            "verification_score": context.get("verification_score", None),
            "agent_sequence": agent_sequence,
            "reasoning_traces": reasoning_traces,
            "claims_verified": context.get("claims_verified", 0),
            "total_claims": context.get("total_claims", 0),
            "verification_issues": context.get("verification_issues", []),
        }

    async def run_demo(self):
        demo_queries = [
            "What is Article 21 of the Indian Constitution?",
            "Compare bail provisions in IPC versus CrPC",
            "How to file a PIL in Supreme Court?",
            "Analyze the impact of recent privacy law changes",
        ]

        print("\nRunning Demo Queries")
        print("=" * 50)

        for i, query in enumerate(demo_queries, 1):
            print(f"\n--- Demo Query {i} ---")
            result = await self.process_query(query)
            ans = result["answer"][:200] + "..." if len(result.get("answer", "")) > 200 else result.get("answer", "")
            print(f"\nAnswer: {ans}")
            print(f"Citations: {len(result['citations'])}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Agents Used: {' -> '.join(result['agent_sequence'])}")

    def get_orchestration_metrics(self) -> Dict[str, Any]:
        if self.orchestrator:
            return self.orchestrator.get_metrics()
        return {}


async def main():
    parser = argparse.ArgumentParser(description="SLM Orchestration Framework")
    parser.add_argument(
        "--orchestrator",
        choices=ORCHESTRATOR_CHOICES,
        default="flan_t5",
        help="Orchestrator type to use",
    )
    parser.add_argument("--query", type=str, help="Single query to process")
    parser.add_argument("--demo", action="store_true", help="Run demo queries")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")

    args = parser.parse_args()
    app = SLMOrchestrationApp(args.orchestrator)
    await app.initialize()

    if args.query:
        result = await app.process_query(args.query)
        print(f"\nResult: {result['answer']}")
    elif args.demo:
        await app.run_demo()
    elif args.interactive:
        print("\nInteractive Mode - Type 'quit' to exit")
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == "quit":
                break
            if query:
                result = await app.process_query(query)
                print(f"\nAnswer: {result['answer']}")
    else:
        await app.run_demo()


if __name__ == "__main__":
    asyncio.run(main())





