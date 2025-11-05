#!/usr/bin/env python3
"""
Comprehensive test script for the complete agentic legal RAG system
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator
from booster_agent import PromptBooster

def test_complete_system():
    """Test the complete system with sample queries"""
    print("🧪 Testing Complete Agentic Legal RAG System")
    print("=" * 60)
    
    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized")
        
        # Test queries that should demonstrate different behaviors
        test_queries = [
            {
                'query': '377 rights',
                'description': 'Short query that should be boosted',
                'expected_boost': True
            },
            {
                'query': 'privacy article',
                'description': 'Vague query that should be boosted',
                'expected_boost': True
            },
            {
                'query': 'IPC theft',
                'description': 'Legal query that should be boosted',
                'expected_boost': True
            },
            {
                'query': 'What is the punishment for murder under Indian law?',
                'description': 'Complete query that may not need boosting',
                'expected_boost': False
            },
            {
                'query': 'section 302 of Indian Penal Code punishment',
                'description': 'Specific legal query',
                'expected_boost': False
            }
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} comprehensive queries...")
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"--- Test Case {i}: {test_case['description']} ---")
            print(f"Query: {test_case['query']}")
            print(f"Expected boost: {test_case['expected_boost']}")
            print(f"{'='*60}")
            
            try:
                # Process query through orchestrator
                result = orchestrator.run(test_case['query'])
                
                # Analyze results
                print(f"\n📋 Results Analysis:")
                print(f"   Task ID: {result['task_id']}")
                print(f"   Original Query: {result['query']}")
                print(f"   Boosted Query: '{result['boosted_query']}'")
                print(f"   Need Boost: {bool(result['boosted_query'])}")
                print(f"   Retrieval Mode: {result['retrieval_mode']}")
                print(f"   Top K: {result['top_k']}")
                print(f"   Documents Retrieved: {len(result['retrieved_documents'])}")
                print(f"   Citations: {len(result['citations'])}")
                print(f"   Human Review Required: {result['human_review_required']}")
                print(f"   Processing Time: {result['processing_time']:.2f}s")
                print(f"   Confidence: {result['confidence']:.2f}")
                print(f"   Reasoning: {result['reasoning']}")
                
                # Show answer preview
                answer = result['answer']
                if answer:
                    print(f"\n💬 Answer Preview:")
                    print(f"   {answer[:200]}{'...' if len(answer) > 200 else ''}")
                else:
                    print(f"\n💬 Answer: No answer generated")
                
                # Show retrieved documents preview
                if result['retrieved_documents']:
                    print(f"\n📚 Retrieved Documents Preview:")
                    for j, doc in enumerate(result['retrieved_documents'][:3], 1):
                        print(f"   {j}. {doc.get('title', 'No title')}")
                        print(f"      Type: {doc.get('doc_type', 'Unknown')}")
                        print(f"      Score: {doc.get('similarity_score', 0):.3f}")
                        print(f"      Preview: {doc.get('content', '')[:100]}...")
                
                # Validate expectations
                actual_boost = bool(result['boosted_query'])
                if actual_boost == test_case['expected_boost']:
                    print(f"\n✅ Boost expectation met")
                else:
                    print(f"\n⚠️  Boost expectation not met (expected: {test_case['expected_boost']}, actual: {actual_boost})")
                
                # Check if system is working as expected
                if result['retrieved_documents']:
                    print(f"✅ Document retrieval working")
                else:
                    print(f"⚠️  No documents retrieved")
                
                if result['answer'] and result['answer'] != "UNVERIFIED: human review required":
                    print(f"✅ Answer generation working")
                else:
                    print(f"⚠️  Answer generation may need attention")
                
    except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        print(f"\n🎉 Complete system test finished!")
    
    except Exception as e:
        print(f"❌ Error in complete system test: {e}")

def test_booster_standalone():
    """Test the booster agent standalone"""
    print("\n🔧 Testing Booster Agent Standalone")
    print("=" * 50)
    
    try:
        booster = PromptBooster(force_rule_based=True)
        
        test_queries = [
            "377 rights",
            "privacy article",
            "IPC theft",
            "What is the punishment for murder under Indian law?",
            "fundamental rights"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Query {i}: {query} ---")
            
            decision = booster.generate_decision(query)
            
            print(f"   need_boost: {decision.need_boost}")
            print(f"   boosted_query: '{decision.boosted_query}'")
            print(f"   retrieval_mode: {decision.retrieval_mode}")
            print(f"   top_k: {decision.top_k}")
            print(f"   require_human_review: {decision.require_human_review}")
            print(f"   confidence: {decision.confidence}")
            print(f"   reasoning: {decision.reasoning}")
        
        print(f"\n✅ Booster agent standalone test completed!")
        
    except Exception as e:
        print(f"❌ Error testing booster standalone: {e}")

def test_system_metrics():
    """Test system metrics and performance"""
    print("\n📊 Testing System Metrics")
    print("=" * 40)
    
    try:
        orchestrator = Orchestrator()
        
        # Process multiple queries
        test_queries = [
            "377 rights",
            "privacy article", 
            "IPC theft",
            "murder punishment",
            "fundamental rights"
        ]
        
        for query in test_queries:
            result = orchestrator.run(query)
        
        # Get performance metrics
        metrics = orchestrator.get_performance_metrics()
        
        print(f"📈 System Performance Metrics:")
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        # Get agent status
        agent_status = orchestrator.get_agent_status()
        print(f"\n🤖 Agent Status:")
        for agent_id, status in agent_status.items():
            print(f"   {agent_id}: {status.status.value}")
        
        # Get system health
        health = orchestrator.get_system_health()
        print(f"\n🏥 System Health:")
        print(f"   Total Agents: {health['total_agents']}")
        print(f"   Healthy Agents: {health['healthy_agents']}")
        print(f"   Health Percentage: {health['health_percentage']:.1f}%")
        
        print(f"\n✅ System metrics test completed!")
        
    except Exception as e:
        print(f"❌ Error testing system metrics: {e}")

def test_logging_system():
    """Test that logging is working properly"""
    print("\n📝 Testing Logging System")
    print("=" * 40)
    
    try:
        orchestrator = Orchestrator()
        
        # Process a query to generate logs
        result = orchestrator.run("test logging query")
        
        # Check orchestration log
        orchestration_log = Path("logs/orchestration.log")
        if orchestration_log.exists():
            print("✅ Orchestration log file exists")
            
            # Read log content
            with open(orchestration_log, 'r') as f:
                log_content = f.read()
            
            # Check for expected log entries
            expected_entries = [
                "Starting query processing",
                "Getting decision from Prompt Booster",
                "Retrieving documents",
                "Verifying citations",
                "Query processed successfully"
            ]
            
            found_entries = []
            for entry in expected_entries:
                if entry in log_content:
                    found_entries.append(entry)
            
            print(f"📋 Found log entries: {len(found_entries)}/{len(expected_entries)}")
            for entry in found_entries:
                print(f"   ✅ {entry}")
            
            missing_entries = [entry for entry in expected_entries if entry not in found_entries]
            for entry in missing_entries:
                print(f"   ❌ {entry}")
            else:
            print("❌ Orchestration log file not found")
        
        print(f"\n✅ Logging system test completed!")
        
    except Exception as e:
        print(f"❌ Error testing logging system: {e}")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive System Tests")
    print("=" * 60)
    
    test_complete_system()
    test_booster_standalone()
    test_system_metrics()
    test_logging_system()
    
    print("\n🎉 All comprehensive tests completed!")
    print("=" * 60)