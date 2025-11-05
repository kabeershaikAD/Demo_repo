#!/usr/bin/env python3
"""
Demo script for Agentic Legal RAG System
Shows how the system behaves with different types of queries
"""

import sys
import os
import time
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import Orchestrator

def run_demo():
    """Run a comprehensive demo of the Agentic Legal RAG system"""
    
    print('AGENTIC LEGAL RAG SYSTEM DEMO')
    print('=' * 50)
    
    # Initialize the system
    print('Initializing system...')
    try:
        orchestrator = Orchestrator()
        print('System initialized successfully!')
    except Exception as e:
        print(f'Failed to initialize system: {e}')
        return
    
    # Demo queries with different characteristics
    demo_queries = [
        {
            'query': 'What is the punishment for murder?',
            'description': 'General legal question - should trigger statute retrieval'
        },
        {
            'query': '377 rights',
            'description': 'Short query - should be boosted and require human review'
        },
        {
            'query': 'privacy article 21',
            'description': 'Constitutional query - should focus on judgments'
        },
        {
            'query': 'IPC theft punishment',
            'description': 'Specific legal query - should focus on statutes'
        },
        {
            'query': 'Supreme Court judgment on fundamental rights',
            'description': 'Case law query - should focus on judgments'
        }
    ]
    
    print(f'\nTesting {len(demo_queries)} demo queries...')
    print('=' * 50)
    
    successful_queries = 0
    total_processing_time = 0
    
    for i, test_case in enumerate(demo_queries, 1):
        query = test_case['query']
        description = test_case['description']
        
        print(f'\n--- Query {i}: {query} ---')
        print(f'Description: {description}')
        
        start_time = time.time()
        
        try:
            result = orchestrator.run(query)
            processing_time = time.time() - start_time
            total_processing_time += processing_time
            successful_queries += 1
            
            print(f'Status: SUCCESS')
            print(f'Processing Time: {processing_time:.2f}s')
            print(f'Answer Length: {len(result.get("answer", ""))} characters')
            print(f'Documents Retrieved: {len(result.get("retrieved_documents", []))}')
            print(f'Citations: {len(result.get("citations", []))}')
            print(f'Human Review Required: {result.get("human_review_required", False)}')
            print(f'Retrieval Mode: {result.get("retrieval_mode", "N/A")}')
            print(f'Top-K: {result.get("top_k", "N/A")}')
            print(f'Boosted Query: {result.get("boosted_query", "N/A")}')
            
            # Show first 200 characters of answer
            answer = result.get('answer', '')
            if answer:
                print(f'Answer Preview: {answer[:200]}...')
            
            # Show some retrieved document titles
            docs = result.get('retrieved_documents', [])
            if docs:
                print(f'Sample Documents:')
                for j, doc in enumerate(docs[:3]):  # Show first 3 docs
                    title = doc.get('title', 'Untitled')
                    doc_type = doc.get('doc_type', 'unknown')
                    similarity = doc.get('similarity_score', 0)
                    print(f'   {j+1}. [{doc_type}] {title[:60]}... (similarity: {similarity:.3f})')
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f'Status: FAILED - {str(e)}')
            print(f'Processing Time: {processing_time:.2f}s')
    
    # Summary
    print('\nDEMO COMPLETE!')
    print('=' * 50)
    print(f'Summary:')
    print(f'   Successful Queries: {successful_queries}/{len(demo_queries)}')
    print(f'   Average Processing Time: {total_processing_time/successful_queries:.2f}s' if successful_queries > 0 else '   Average Processing Time: N/A')
    print(f'   Success Rate: {(successful_queries/len(demo_queries)*100):.1f}%')
    
    print(f'\nWhat to Expect from Your System:')
    print(f'   1. Intelligent Query Enhancement - Short queries get boosted')
    print(f'   2. Smart Document Retrieval - Different modes for different query types')
    print(f'   3. Comprehensive Answers - Detailed legal responses with citations')
    print(f'   4. Human Review Flagging - Sensitive queries flagged for review')
    print(f'   5. Performance Tracking - All actions logged and monitored')
    print(f'   6. Error Handling - Graceful fallbacks when issues occur')
    
    print(f'\nWeb Interface:')
    print(f'   The Streamlit app should be running at: http://localhost:8501')
    print(f'   You can interact with the system through the web interface!')

if __name__ == "__main__":
    run_demo()
