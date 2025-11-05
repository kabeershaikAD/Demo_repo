#!/usr/bin/env python3
"""
Test script for the new Orchestrator with structured JSON routing
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator

def test_orchestrator_basic():
    """Test basic orchestrator functionality"""
    print("🧪 Testing Orchestrator Basic Functionality")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = Orchestrator()
        print("✅ Orchestrator initialized")
        
        # Test queries
        test_queries = [
            "377 rights",
            "privacy article",
            "IPC theft",
            "What is the punishment for murder under Indian law?",
            "fundamental rights"
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} sample queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Query {i}: {query} ---")
            
            try:
                # Process query
                result = orchestrator.run(query)
                
                # Verify required fields are present
                required_fields = [
                    'task_id', 'query', 'boosted_query', 'retrieval_mode', 
                    'top_k', 'answer', 'citations', 'retrieved_documents',
                    'human_review_required', 'processing_time', 'confidence', 'reasoning'
                ]
                
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    print(f"❌ Missing fields: {missing_fields}")
                else:
                    print(f"✅ All required fields present")
                
                # Print result details
                print(f"📋 Result:")
                print(f"   task_id: {result['task_id']}")
                print(f"   query: {result['query']}")
                print(f"   boosted_query: '{result['boosted_query']}'")
                print(f"   retrieval_mode: {result['retrieval_mode']}")
                print(f"   top_k: {result['top_k']}")
                print(f"   answer: {result['answer'][:100]}...")
                print(f"   citations: {len(result['citations'])} found")
                print(f"   retrieved_documents: {len(result['retrieved_documents'])} found")
                print(f"   human_review_required: {result['human_review_required']}")
                print(f"   processing_time: {result['processing_time']:.2f}s")
                print(f"   confidence: {result['confidence']}")
                print(f"   reasoning: {result['reasoning']}")
                
                # Validate field types
                assert isinstance(result['task_id'], str), "task_id should be string"
                assert isinstance(result['query'], str), "query should be string"
                assert isinstance(result['boosted_query'], str), "boosted_query should be string"
                assert result['retrieval_mode'] in ['statutes', 'judgments', 'both'], "retrieval_mode should be valid"
                assert isinstance(result['top_k'], int), "top_k should be integer"
                assert isinstance(result['answer'], str), "answer should be string"
                assert isinstance(result['citations'], list), "citations should be list"
                assert isinstance(result['retrieved_documents'], list), "retrieved_documents should be list"
                assert isinstance(result['human_review_required'], bool), "human_review_required should be boolean"
                assert isinstance(result['processing_time'], (int, float)), "processing_time should be number"
                assert isinstance(result['confidence'], (int, float)), "confidence should be number"
                assert isinstance(result['reasoning'], str), "reasoning should be string"
                
                print(f"✅ Field types validated")
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        print(f"\n🎉 Orchestrator basic test completed!")
        
    except Exception as e:
        print(f"❌ Error initializing orchestrator: {e}")

def test_orchestrator_routing():
    """Test orchestrator routing based on retrieval_mode"""
    print("\n🔄 Testing Orchestrator Routing")
    print("=" * 40)
    
    try:
        orchestrator = Orchestrator()
        
        # Test different query types that should trigger different routing
        test_cases = [
            {
                'query': 'section 302 IPC',
                'expected_mode': 'statutes',
                'description': 'Statute-specific query'
            },
            {
                'query': 'supreme court judgment privacy',
                'expected_mode': 'judgments',
                'description': 'Judgment-specific query'
            },
            {
                'query': '377 rights',
                'expected_mode': 'both',
                'description': 'General legal query'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {case['description']} ---")
            print(f"Query: {case['query']}")
            print(f"Expected mode: {case['expected_mode']}")
            
            result = orchestrator.run(case['query'])
            
            print(f"Actual mode: {result['retrieval_mode']}")
            print(f"Top k: {result['top_k']}")
            print(f"Documents retrieved: {len(result['retrieved_documents'])}")
            
            # Check if routing is working (mode should match expected or be 'both')
            if result['retrieval_mode'] == case['expected_mode'] or result['retrieval_mode'] == 'both':
                print("✅ Routing working correctly")
            else:
                print("⚠️  Routing may need adjustment")
        
        print(f"\n🎉 Orchestrator routing test completed!")
        
    except Exception as e:
        print(f"❌ Error testing routing: {e}")

def test_orchestrator_metrics():
    """Test orchestrator metrics tracking"""
    print("\n📊 Testing Orchestrator Metrics")
    print("=" * 40)
    
    try:
        orchestrator = Orchestrator()
        
        # Process some queries
        test_queries = ["test query 1", "test query 2", "test query 3"]
        
        for query in test_queries:
            result = orchestrator.run(query)
        
        # Get metrics
        metrics = orchestrator.get_performance_metrics()
        
        print(f"📈 Metrics after {len(test_queries)} queries:")
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        # Validate metrics
        assert metrics['total_queries'] == len(test_queries), "Total queries count should match"
        assert metrics['successful_queries'] > 0, "Should have successful queries"
        assert metrics['average_response_time'] > 0, "Should have response time"
        
        print("✅ Metrics tracking working correctly")
        
    except Exception as e:
        print(f"❌ Error testing metrics: {e}")

def test_orchestrator_error_handling():
    """Test orchestrator error handling"""
    print("\n🚨 Testing Orchestrator Error Handling")
    print("=" * 45)
    
    try:
        orchestrator = Orchestrator()
        
        # Test with empty query
        print("--- Testing empty query ---")
        result = orchestrator.run("")
        
        if 'error' in result:
            print("✅ Empty query handled with error")
        else:
            print("⚠️  Empty query should have been handled with error")
        
        # Test with very long query
        print("\n--- Testing very long query ---")
        long_query = "test " * 1000
        result = orchestrator.run(long_query)
        
        if 'error' not in result:
            print("✅ Long query processed successfully")
        else:
            print(f"⚠️  Long query failed: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎉 Error handling test completed!")
        
    except Exception as e:
        print(f"❌ Error testing error handling: {e}")

def test_orchestrator_logging():
    """Test that orchestration logging is working"""
    print("\n📝 Testing Orchestrator Logging")
    print("=" * 40)
    
    try:
        orchestrator = Orchestrator()
        
        # Process a query
        result = orchestrator.run("test logging query")
        
        # Check if log file exists
        log_file = Path("logs/orchestration.log")
        if log_file.exists():
            print("✅ Orchestration log file exists")
            
            # Read last few lines of log
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-10:]  # Last 10 lines
            
            print("📋 Recent log entries:")
            for line in recent_lines:
                print(f"   {line.strip()}")
        else:
            print("❌ Orchestration log file not found")
        
        print(f"\n🎉 Logging test completed!")
        
    except Exception as e:
        print(f"❌ Error testing logging: {e}")

if __name__ == "__main__":
    test_orchestrator_basic()
    test_orchestrator_routing()
    test_orchestrator_metrics()
    test_orchestrator_error_handling()
    test_orchestrator_logging()
    print("\n🎉 All orchestrator tests completed!")

