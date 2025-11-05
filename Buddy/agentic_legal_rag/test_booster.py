#!/usr/bin/env python3
"""
Test script for the new PromptBooster with structured JSON output
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from booster_agent import PromptBooster, BoosterDecision

def test_booster_json_output():
    """Test that PromptBooster generates proper JSON output"""
    print("🧪 Testing PromptBooster JSON Output")
    print("=" * 50)
    
    try:
        # Initialize booster
        booster = PromptBooster(force_rule_based=True)  # Use rule-based for testing
        print("✅ PromptBooster initialized")
        
        # Test queries
        test_queries = [
            "377 rights",
            "privacy article", 
            "IPC theft",
            "What is the punishment for murder under Indian law?",
            "fundamental rights",
            "section 302"
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} sample queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Query {i}: {query} ---")
            
            try:
                # Generate decision
                decision = booster.generate_decision(query)
                
                # Verify all required fields are present
                required_fields = ['need_boost', 'boosted_query', 'retrieval_mode', 'top_k', 'require_human_review']
                missing_fields = [field for field in required_fields if not hasattr(decision, field)]
                
                if missing_fields:
                    print(f"❌ Missing fields: {missing_fields}")
                else:
                    print(f"✅ All required fields present")
                
                # Print decision details
                print(f"📋 Decision:")
                print(f"   need_boost: {decision.need_boost}")
                print(f"   boosted_query: '{decision.boosted_query}'")
                print(f"   retrieval_mode: {decision.retrieval_mode}")
                print(f"   top_k: {decision.top_k}")
                print(f"   require_human_review: {decision.require_human_review}")
                print(f"   confidence: {decision.confidence}")
                print(f"   reasoning: {decision.reasoning}")
                
                # Validate field types
                assert isinstance(decision.need_boost, bool), "need_boost should be boolean"
                assert isinstance(decision.boosted_query, str), "boosted_query should be string"
                assert decision.retrieval_mode in ['statutes', 'judgments', 'both'], "retrieval_mode should be one of: statutes, judgments, both"
                assert isinstance(decision.top_k, int), "top_k should be integer"
                assert isinstance(decision.require_human_review, bool), "require_human_review should be boolean"
                assert 0 <= decision.confidence <= 1, "confidence should be between 0 and 1"
                
                print(f"✅ Field types validated")
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        print(f"\n🎉 Booster JSON output test completed!")
        
    except Exception as e:
        print(f"❌ Error initializing booster: {e}")

def test_fallback_policy():
    """Test the fallback policy functionality"""
    print("\n🔄 Testing Fallback Policy")
    print("=" * 30)
    
    try:
        booster = PromptBooster(force_rule_based=True)
        
        # Test cases for fallback policy
        test_cases = [
            {
                'query': 'test query',
                'boosted_query': 'enhanced test query',
                'retrieval_scores': [0.8, 0.7, 0.6],  # Good scores
                'expected': 'enhanced test query'
            },
            {
                'query': 'test query',
                'boosted_query': 'enhanced test query',
                'retrieval_scores': [0.2, 0.1, 0.3],  # Poor scores
                'expected': 'test query'
            },
            {
                'query': 'test query',
                'boosted_query': 'enhanced test query',
                'retrieval_scores': [0.4, 0.5, 0.6],  # Medium scores
                'expected': 'test query'
            },
            {
                'query': 'test query',
                'boosted_query': 'enhanced test query',
                'retrieval_scores': [],  # Empty scores
                'expected': 'test query'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i} ---")
            print(f"Query: {case['query']}")
            print(f"Boosted: {case['boosted_query']}")
            print(f"Scores: {case['retrieval_scores']}")
            
            result = booster.fallback_policy(
                case['query'],
                case['boosted_query'],
                case['retrieval_scores']
            )
            
            print(f"Result: {result}")
            print(f"Expected: {case['expected']}")
            
            if result == case['expected']:
                print("✅ Fallback policy working correctly")
            else:
                print("❌ Fallback policy not working as expected")
        
        print(f"\n🎉 Fallback policy test completed!")
        
    except Exception as e:
        print(f"❌ Error testing fallback policy: {e}")

def test_booster_metrics():
    """Test booster metrics tracking"""
    print("\n📊 Testing Booster Metrics")
    print("=" * 30)
    
    try:
        booster = PromptBooster(force_rule_based=True)
        
        # Reset metrics
        booster.reset_metrics()
        
        # Process some queries
        test_queries = ["test query 1", "test query 2", "test query 3"]
        
        for query in test_queries:
            decision = booster.generate_decision(query)
        
        # Get metrics
        metrics = booster.get_metrics()
        
        print(f"📈 Metrics after {len(test_queries)} queries:")
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        # Validate metrics
        assert metrics['total_queries'] == len(test_queries), "Total queries count should match"
        assert metrics['json_parsing_success'] > 0, "Should have successful parsing"
        assert metrics['avg_processing_time'] > 0, "Should have processing time"
        
        print("✅ Metrics tracking working correctly")
        
    except Exception as e:
        print(f"❌ Error testing metrics: {e}")

if __name__ == "__main__":
    test_booster_json_output()
    test_fallback_policy()
    test_booster_metrics()
    print("\n🎉 All booster tests completed!")

