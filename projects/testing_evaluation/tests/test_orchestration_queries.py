"""
Test script to demonstrate different orchestration patterns
Run this to see how SLM orchestrates different query types
"""
import asyncio
import sys
import os

# Add the projects/slm_orchestration_legal_rag directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
slm_project_path = os.path.join(project_root, 'projects', 'slm_orchestration_legal_rag')
sys.path.insert(0, slm_project_path)

from slm_orchestration_app import SLMOrchestrationApp

# 5 Different queries that should trigger different orchestration patterns
DEMO_QUERIES = [
    {
        "query": "What is Section 302 of the Indian Penal Code?",
        "expected_type": "Simple Factual",
        "expected_sequence": ["retriever", "answering"],
        "description": "Well-formed, specific query - should skip booster"
    },
    {
        "query": "what is 21",
        "expected_type": "Vague/Short",
        "expected_sequence": ["booster", "retriever", "answering"],
        "description": "Very short, vague query - should use booster first"
    },
    {
        "query": "Analyze the legal implications of the recent Supreme Court judgment on privacy rights and how it affects data protection laws in India",
        "expected_type": "Complex Analytical",
        "expected_sequence": ["booster", "retriever", "answering", "verifier"],
        "description": "Complex analytical query - should use full pipeline with verifier"
    },
    {
        "query": "What is the difference between murder and culpable homicide under Indian law?",
        "expected_type": "Comparative",
        "expected_sequence": ["booster", "retriever", "answering", "verifier"],
        "description": "Comparative query - should use verifier for accuracy"
    },
    {
        "query": "How to file a First Information Report (FIR) in India?",
        "expected_type": "Procedural",
        "expected_sequence": ["booster", "retriever", "answering"],
        "description": "Procedural 'how to' query - booster but no verifier"
    }
]

async def test_orchestration():
    """Test orchestration with different query types"""
    
    print("=" * 70)
    print("SLM ORCHESTRATION DEMONSTRATION")
    print("Testing Flan-T5-small's ability to route different query types")
    print("=" * 70)
    
    # Initialize app
    print("\n🔧 Initializing SLM Orchestration App...")
    app = SLMOrchestrationApp(orchestrator_type="flan_t5")
    await app.initialize()
    print("✅ Initialized!\n")
    
    # Test each query
    for i, test_case in enumerate(DEMO_QUERIES, 1):
        print("\n" + "=" * 70)
        print(f"QUERY {i}: {test_case['expected_type']}")
        print("=" * 70)
        print(f"Query: {test_case['query']}")
        print(f"Expected: {test_case['description']}")
        print(f"Expected Sequence: {' → '.join(test_case['expected_sequence'])}")
        print("-" * 70)
        
        # Process query
        result = await app.process_query(test_case['query'])
        
        # Display results
        orchestration = result.get("orchestration", {})
        analysis = orchestration.get("analysis", {})
        agent_sequence = orchestration.get("agent_sequence", [])
        
        print(f"\n📊 SLM Analysis:")
        print(f"   Complexity: {analysis.get('complexity', 'unknown')}")
        print(f"   Reasoning Type: {analysis.get('reasoning_type', 'unknown')}")
        print(f"   SLM Confidence: {analysis.get('confidence', 0):.1%}")
        print(f"   Requires Enhancement: {analysis.get('requires_enhancement', False)}")
        print(f"   Requires Verification: {analysis.get('requires_verification', False)}")
        
        print(f"\n🎯 Agent Sequence (SLM Decision):")
        print(f"   {' → '.join(agent_sequence)}")
        
        # Compare with expected
        if agent_sequence == test_case['expected_sequence']:
            print(f"\n✅ MATCH! Sequence matches expected pattern")
        else:
            print(f"\n⚠️  DIFFERENT! Expected: {' → '.join(test_case['expected_sequence'])}")
            print(f"   Got: {' → '.join(agent_sequence)}")
        
        print(f"\n💡 Answer Confidence: {result.get('confidence', 0):.1%}")
        print(f"📚 Citations: {len(result.get('citations', []))}")
        
        # Brief answer preview
        answer = result.get('answer', '')[:150]
        print(f"\n📝 Answer Preview: {answer}...")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nSummary:")
    print("The SLM orchestrator should have shown different agent sequences")
    print("for different query types, demonstrating adaptive routing!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_orchestration())



