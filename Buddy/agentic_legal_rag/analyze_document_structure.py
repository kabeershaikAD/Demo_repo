#!/usr/bin/env python3
"""
Analyze Document Structure in Vector Database
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever_agent import RetrieverAgent

def analyze_document_structure():
    """Analyze what's actually stored in the database"""
    print("🔍 ANALYZING DOCUMENT STRUCTURE")
    print("=" * 50)
    
    try:
        retriever = RetrieverAgent()
        collection = retriever.vector_db._collection
        
        # Get sample documents from different sources
        print("📊 Getting sample documents...")
        
        # Test query to get mixed results
        results = retriever.retrieve('pocso act', k=10)
        
        print(f"\n📋 RETRIEVAL RESULTS:")
        print(f"Total retrieved: {results.total_retrieved}")
        print(f"Judgments: {len(results.judgments)}")
        print(f"Statutes: {len(results.statutes)}")
        
        # Analyze judgment documents
        print(f"\n⚖️ SUPREME COURT JUDGMENTS ANALYSIS:")
        for i, doc in enumerate(results.judgments[:3]):
            print(f"\n--- Judgment {i+1} ---")
            print(f"Title: {doc.title}")
            print(f"Source: {doc.source}")
            print(f"Content Length: {len(doc.content)}")
            print(f"Content Preview: {doc.content[:300]}...")
            print(f"Metadata: {doc.metadata}")
        
        # Analyze statute documents  
        print(f"\n📜 STATUTE DOCUMENTS ANALYSIS:")
        for i, doc in enumerate(results.statutes[:3]):
            print(f"\n--- Statute {i+1} ---")
            print(f"Title: {doc.title}")
            print(f"Source: {doc.source}")
            print(f"Content Length: {len(doc.content)}")
            print(f"Content Preview: {doc.content[:300]}...")
            print(f"Metadata: {doc.metadata}")
        
        # Check what's in the raw database
        print(f"\n🗄️ RAW DATABASE SAMPLE:")
        all_docs = collection.get(limit=3, include=['documents', 'metadatas'])
        for i, (doc, metadata) in enumerate(zip(all_docs['documents'], all_docs['metadatas'])):
            print(f"\n--- Raw Document {i+1} ---")
            print(f"Metadata: {metadata}")
            print(f"Content: {doc[:200]}...")
        
    except Exception as e:
        print(f"❌ Error analyzing structure: {e}")

if __name__ == "__main__":
    analyze_document_structure()
