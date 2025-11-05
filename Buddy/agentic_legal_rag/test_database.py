#!/usr/bin/env python3
"""
Test script to verify the vector database is working with legal data
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever_agent import RetrieverAgent
from answering_agent import AnsweringAgent

def test_database():
    """Test the loaded legal database"""
    print("🧪 Testing Legal Database")
    print("=" * 50)
    
    try:
        # Initialize agents
        retriever = RetrieverAgent()
        answering_agent = AnsweringAgent()
        
        print("✅ Agents initialized successfully")
        
        # Test queries
        test_queries = [
            "What is Article 21 of the Constitution?",
            "What is Section 302 of IPC?",
            "What are the fundamental rights?",
            "What is the punishment for murder?",
            "What is the right to life and liberty?"
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} sample queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Query {i}: {query} ---")
            
            try:
                # Get relevant documents
                result = retriever.retrieve(query, k=3)
                relevant_docs = result.statutes + result.judgments
                
                if relevant_docs:
                    print(f"📄 Found {len(relevant_docs)} relevant documents")
                    
                    # Show first document preview
                    first_doc = relevant_docs[0]
                    print(f"📋 Top result: {first_doc.title}")
                    print(f"📂 Source: {first_doc.source}")
                    print(f"🏷️  Type: {first_doc.doc_type}")
                    print(f"📝 Preview: {first_doc.content[:200]}...")
                    
                    # Convert documents to the format expected by answering agent
                    doc_dicts = []
                    for doc in relevant_docs:
                        doc_dict = {
                            'content': doc.content,
                            'title': doc.title,
                            'doc_type': doc.doc_type,
                            'source': doc.source,
                            'similarity_score': doc.similarity_score,
                            'metadata': doc.metadata or {}
                        }
                        doc_dicts.append(doc_dict)
                    
                    # Generate answer
                    result = answering_agent.generate_answer(query, query, doc_dicts)
                    answer = result.get('answer_text', 'No answer generated')
                    print(f"💬 Answer: {answer[:300]}...")
                    
                    # Show additional info if available
                    if 'claims' in result and result['claims']:
                        print(f"📋 Claims: {len(result['claims'])} found")
                    if 'sources' in result and result['sources']:
                        print(f"📚 Sources: {len(result['sources'])} found")
                    
                else:
                    print("❌ No relevant documents found")
                    
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        print(f"\n🎉 Database test completed!")
        
    except Exception as e:
        print(f"❌ Error initializing agents: {e}")

def check_database_stats():
    """Check database statistics"""
    print("\n📊 Database Statistics")
    print("=" * 30)
    
    try:
        retriever = RetrieverAgent()
        
        # Get collection info
        collection = retriever.vector_db._collection
        count = collection.count()
        
        print(f"📚 Total documents: {count}")
        
        # Get sample of documents
        sample_docs = collection.get(limit=5)
        if sample_docs and 'metadatas' in sample_docs:
            print(f"\n📋 Sample documents:")
            for i, metadata in enumerate(sample_docs['metadatas'][:3], 1):
                print(f"  {i}. {metadata.get('title', 'No title')}")
                print(f"     Type: {metadata.get('doc_type', 'Unknown')}")
                print(f"     Source: {metadata.get('source', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error checking database stats: {e}")

if __name__ == "__main__":
    check_database_stats()
    test_database()
