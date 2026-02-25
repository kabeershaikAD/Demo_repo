"""
SLM Orchestration Framework - Main Application
Demonstrates Flan-T5-small orchestrating multi-agent legal RAG system
"""

import asyncio
import logging
from typing import Dict, Any, List
import argparse
import torch

# Import orchestrators
from orchestrators.flan_t5_orchestrator import FlanT5Orchestrator
from orchestrators.gpt4_orchestrator import GPT4Orchestrator
from orchestrators.rule_orchestrator import RuleBasedOrchestrator
from orchestrators.no_orchestrator import NoOrchestrator

# Import existing agents (from your current project)
from booster_agent import PromptBooster
from retriever_agent import RetrieverAgent
from answering_agent import AnsweringAgent
from citation_verifier import CitationVerifier
from multilingual_agent import MultilingualAgent

# Import adapters to make agents compatible
from agent_adapters import (
    BoosterAdapter, RetrieverAdapter, AnsweringAdapter, 
    VerifierAdapter, MultilingualAdapter
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SLMOrchestrationApp:
    """
    Main application demonstrating SLM orchestration.
    
    This is the key contribution: showing that Flan-T5-small (80M parameters)
    can effectively orchestrate multi-agent systems as an alternative to
    expensive GPT-4 orchestration.
    """
    
    def __init__(self, orchestrator_type: str = "flan_t5"):
        self.orchestrator_type = orchestrator_type
        self.orchestrator = None
        self.agents = {}
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration"""
        return {
            "model_name": "google/flan-t5-small",
            "openai_api_key": "your-key-here",  # Replace with actual key
            "groq_api_key": "your-groq-key-here",  # Replace with actual key
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }
    
    async def initialize(self):
        """Initialize orchestrator and agents"""
        print(f"🚀 Initializing SLM Orchestration App with {self.orchestrator_type}")
        
        # Initialize orchestrator
        if self.orchestrator_type == "flan_t5":
            self.orchestrator = FlanT5Orchestrator(self.config)
        elif self.orchestrator_type == "gpt4":
            self.orchestrator = GPT4Orchestrator(self.config)
        elif self.orchestrator_type == "rule":
            self.orchestrator = RuleBasedOrchestrator(self.config)
        elif self.orchestrator_type == "none":
            self.orchestrator = NoOrchestrator(self.config)
        else:
            raise ValueError(f"Unknown orchestrator type: {self.orchestrator_type}")
        
        await self.orchestrator.initialize()
        
        # Initialize agents with adapters
        print("  Initializing agents...")
        self.agents = {
            "booster": BoosterAdapter(PromptBooster()),
            "retriever": RetrieverAdapter(RetrieverAgent()),
            "answering": AnsweringAdapter(AnsweringAgent()),
            "verifier": VerifierAdapter(CitationVerifier()),
            "multilingual": MultilingualAdapter(MultilingualAgent())
        }
        
        # Initialize each agent
        for name, agent in self.agents.items():
            try:
                await agent.initialize()
                print(f"    ✅ {name} agent ready")
            except Exception as e:
                print(f"    ❌ Failed to initialize {name}: {e}")
        
        print("✅ All systems ready!")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query using SLM orchestration"""
        
        print(f"\n🔍 Processing query: {query}")
        
        # Step 1: Orchestrator analyzes query
        print("  📊 Analyzing query...")
        analysis = await self.orchestrator.analyze_query(query)
        print(f"    Complexity: {analysis.get('complexity', 'unknown')}")
        print(f"    Reasoning: {analysis.get('reasoning_type', 'unknown')}")
        print(f"    Confidence: {analysis.get('confidence', 0):.2f}")
        
        # Step 2: Orchestrator determines agent sequence
        print("  🎯 Determining agent sequence...")
        agent_sequence = await self.orchestrator.route_to_agents(query, analysis)
        print(f"    Sequence: {' → '.join(agent_sequence)}")
        
        # Step 3: Execute agent workflow
        print("  ⚙️ Executing workflow...")
        result = await self._execute_agent_workflow(query, agent_sequence)
        
        # Step 4: Calculate overall confidence (combine SLM confidence with verification)
        # Get confidence from answering agent - prefer answer_confidence if available
        answer_confidence = result.get("answer_confidence", result.get("confidence", 0.5))
        
        # Get verification score if verifier was used, otherwise use answer confidence
        verification_score = result.get("verification_score")
        if verification_score is None:
            verification_score = answer_confidence
        
        slm_confidence = analysis.get('confidence', 0.7)
        doc_count = len(result.get("documents", []))
        
        # Document confidence: based on both count and quality
        if doc_count > 0:
            docs = result.get("documents", [])
            if docs and any(d.get('similarity_score', 0) > 0 for d in docs):
                avg_similarity = sum(d.get('similarity_score', 0.0) for d in docs) / len(docs)
                # Normalize similarity (it's already 0-1, but ensure it's reasonable)
                normalized_similarity = min(max(avg_similarity, 0.0), 1.0)
                doc_confidence = (min(doc_count / 5.0, 1.0) * 0.4) + (normalized_similarity * 0.6)  # Favor quality
            else:
                doc_confidence = min(doc_count / 5.0, 1.0)  # Just based on count
        else:
            doc_confidence = 0.0  # No documents = 0 confidence
        
        # Ensure all confidence values are reasonable (0-1)
        slm_confidence = min(max(slm_confidence, 0.0), 1.0)
        verification_score = min(max(verification_score, 0.0), 1.0)
        doc_confidence = min(max(doc_confidence, 0.0), 1.0)
        
        # Weighted confidence: 30% SLM orchestration, 45% answer quality, 25% document support
        # Balanced weights to reflect all components fairly
        overall_confidence = (slm_confidence * 0.30) + (verification_score * 0.45) + (doc_confidence * 0.25)
        
        # Ensure final confidence is reasonable
        overall_confidence = min(max(overall_confidence, 0.0), 1.0)
        result["confidence"] = overall_confidence
        
        # Step 5: Add orchestration metadata
        result["orchestration"] = {
            "orchestrator": self.orchestrator_type,
            "analysis": analysis,
            "agent_sequence": agent_sequence,
            "metrics": self.orchestrator.get_metrics()
        }
        
        return result
    
    async def _execute_agent_workflow(self, query: str, agent_sequence: List[str]) -> Dict[str, Any]:
        """Execute the determined agent sequence"""
        
        context = {"query": query, "documents": [], "answer": "", "citations": []}
        
        for agent_name in agent_sequence:
            if agent_name not in self.agents:
                print(f"    ⚠️ Unknown agent: {agent_name}")
                continue
            
            print(f"    🔧 Running {agent_name}...")
            
            try:
                agent = self.agents[agent_name]
                
                if agent_name == "booster":
                    result = await agent.process(query)
                    context["enhanced_query"] = result.get("boosted_query", query)
                    
                elif agent_name == "retriever":
                    search_query = context.get("enhanced_query", query)
                    result = await agent.process(search_query)
                    context["documents"] = result.get("documents", [])
                    
                elif agent_name == "answering":
                    result = await agent.process(context["query"], context["documents"])
                    context["answer"] = result.get("answer", "")
                    context["citations"] = result.get("citations", [])
                    context["answer_confidence"] = result.get("confidence", 0.5)  # Store confidence from answering agent
                    
                elif agent_name == "verifier":
                    result = await agent.process(context["answer"], context["citations"])
                    context["verified_answer"] = result.get("verified_answer", context["answer"])
                    context["verification_score"] = result.get("verification_score", 0.0)
                    
                elif agent_name == "multilingual":
                    result = await agent.process(query)
                    context["language"] = result.get("language", "en")
                    context["translated_query"] = result.get("translated_query", query)
                
                print(f"      ✅ {agent_name} completed")
                
            except Exception as e:
                print(f"      ❌ {agent_name} failed: {e}")
                continue
        
        return {
            "query": query,
            "answer": context.get("verified_answer", context.get("answer", "")),
            "citations": context.get("citations", []),
            "documents": context.get("documents", []),
            "confidence": context.get("verification_score", context.get("answer_confidence", 0.5)),
            "answer_confidence": context.get("answer_confidence", 0.5),
            "verification_score": context.get("verification_score", None),
            "agent_sequence": agent_sequence
        }
    
    async def run_demo(self):
        """Run demonstration queries"""
        
        demo_queries = [
            "What is Article 21 of the Indian Constitution?",
            "Compare bail provisions in IPC versus CrPC",
            "How to file a PIL in Supreme Court?",
            "अनुच्छेद 21 क्या है?",  # Hindi
            "Analyze the impact of recent privacy law changes"
        ]
        
        print("\n🎯 Running Demo Queries")
        print("=" * 50)
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n--- Demo Query {i} ---")
            result = await self.process_query(query)
            
            print(f"\n📝 Answer: {result['answer'][:200]}...")
            print(f"🔗 Citations: {len(result['citations'])}")
            print(f"📊 Confidence: {result['confidence']:.2f}")
            print(f"⚙️ Agents Used: {' → '.join(result['agent_sequence'])}")
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get current orchestration metrics"""
        if self.orchestrator:
            return self.orchestrator.get_metrics()
        return {}

async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description="SLM Orchestration Framework")
    parser.add_argument(
        "--orchestrator", 
        choices=["flan_t5", "gpt4", "rule", "none"],
        default="flan_t5",
        help="Orchestrator type to use"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Single query to process"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo queries"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    # Initialize app
    app = SLMOrchestrationApp(args.orchestrator)
    await app.initialize()
    
    if args.query:
        # Process single query
        result = await app.process_query(args.query)
        print(f"\n📝 Result: {result['answer']}")
        
    elif args.demo:
        # Run demo
        await app.run_demo()
        
    elif args.interactive:
        # Interactive mode
        print("\n💬 Interactive Mode - Type 'quit' to exit")
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break
            if query:
                result = await app.process_query(query)
                print(f"\nAnswer: {result['answer']}")
    
    else:
        # Default: run demo
        await app.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
