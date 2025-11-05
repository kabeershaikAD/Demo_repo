#!/usr/bin/env python3
"""
Test Boosted Prompts with Better Display
Shows the actual enhanced queries from the orchestrator
"""

import time
from orchestrator import Orchestrator

def test_boosted_prompts():
    """Test boosted prompts with better display"""
    
    print("🚀 TESTING BOOSTED PROMPTS")
    print("=" * 60)
    
    # Initialize orchestrator
    print("\n🔧 Initializing Orchestrator...")
    orchestrator = Orchestrator()
    print("✅ Ready!")
    
    # Test queries
    test_queries = [
        "What is Article 21?",
        "Murder punishment",
        "Fundamental rights",
        "What is IPC section 302?",
        "Right to life"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"🔍 TEST #{i}")
        print(f"📝 Original Query: '{query}'")
        print(f"{'='*60}")
        
        try:
            # Process through orchestrator to get the full result
            result = orchestrator.process_query(query)
            
            # Extract enhanced query from agent results
            enhanced_query = result.agent_results.get('enhanced_query', 'Not found')
            
            print(f"🚀 Enhanced Query: '{enhanced_query}'")
            print(f"📊 Status: {result.status.value}")
            print(f"⏱️  Processing Time: {result.processing_time:.2f}s")
            print(f"🎯 Confidence: {result.confidence_score:.2f}")
            
            # Show the difference
            if query.lower() != enhanced_query.lower():
                print(f"\n📈 IMPROVEMENT:")
                print(f"   Original:  {query}")
                print(f"   Enhanced:  {enhanced_query}")
                print(f"   Difference: {len(enhanced_query) - len(query)} characters")
            else:
                print(f"\n📊 No enhancement applied")
            
            # Show citations if any
            if result.citations:
                print(f"\n📚 Citations: {len(result.citations)} claims verified")
                for j, citation in enumerate(result.citations[:2], 1):  # Show first 2
                    print(f"   {j}. {citation.get('text', 'N/A')[:50]}... ({'✅' if citation.get('supported', False) else '❌'})")
            else:
                print(f"\n📚 Citations: None verified")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print(f"\n⏳ Waiting 1 second...")
        time.sleep(1)
    
    print(f"\n🎉 Testing complete!")

if __name__ == "__main__":
    test_boosted_prompts()
