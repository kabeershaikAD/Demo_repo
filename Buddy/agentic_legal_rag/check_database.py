#!/usr/bin/env python3
"""
Database Analysis Script
Check what's in the vector database
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from retriever_agent import RetrieverAgent
from collections import Counter
import json

def analyze_database():
    """Analyze the vector database contents"""
    print("🔍 VECTOR DATABASE ANALYSIS")
    print("=" * 50)
    
    try:
        # Initialize retriever
        retriever = RetrieverAgent()
        collection = retriever.vector_db._collection
        
        # Get total count
        total_docs = collection.count()
        print(f"📊 TOTAL DOCUMENTS: {total_docs}")
        
        if total_docs == 0:
            print("❌ Database is empty!")
            return
        
        # Get all metadata to analyze
        print("\n🔄 Fetching all metadata...")
        all_docs = collection.get(include=['metadatas', 'documents'])
        
        # Analyze document types
        doc_types = Counter()
        sources = Counter()
        courts = Counter()
        
        for metadata in all_docs['metadatas']:
            doc_types[metadata.get('doc_type', 'unknown')] += 1
            sources[metadata.get('source', 'unknown')] += 1
            courts[metadata.get('court', 'unknown')] += 1
        
        print(f"\n📋 DOCUMENT TYPES:")
        for doc_type, count in doc_types.most_common():
            print(f"   {doc_type}: {count}")
        
        print(f"\n📚 SOURCES:")
        for source, count in sources.most_common():
            print(f"   {source}: {count}")
        
        print(f"\n⚖️ COURTS:")
        for court, count in courts.most_common(10):  # Top 10 courts
            print(f"   {court}: {count}")
        
        # Show sample documents
        print(f"\n🔍 SAMPLE DOCUMENTS (First 5):")
        for i in range(min(5, len(all_docs['documents']))):
            doc = all_docs['documents'][i]
            metadata = all_docs['metadatas'][i]
            
            print(f"\n--- Document {i+1} ---")
            print(f"ID: {metadata.get('doc_id', 'N/A')}")
            print(f"Title: {metadata.get('title', 'N/A')}")
            print(f"Type: {metadata.get('doc_type', 'N/A')}")
            print(f"Source: {metadata.get('source', 'N/A')}")
            print(f"Court: {metadata.get('court', 'N/A')}")
            print(f"Date: {metadata.get('date', 'N/A')}")
            print(f"Content Length: {len(doc) if doc else 0} characters")
            if doc:
                print(f"Content Preview: {doc[:300]}...")
        
        # Check for specific datasets
        print(f"\n🎯 DATASET ANALYSIS:")
        kaggle_docs = [m for m in all_docs['metadatas'] if 'Kaggle' in m.get('source', '')]
        print(f"   Kaggle datasets: {len(kaggle_docs)}")
        
        supreme_court_docs = [m for m in all_docs['metadatas'] if 'supreme_court' in m.get('doc_id', '')]
        print(f"   Supreme Court judgments: {len(supreme_court_docs)}")
        
        # Check content quality
        print(f"\n📈 CONTENT QUALITY:")
        content_lengths = [len(doc) for doc in all_docs['documents'] if doc]
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            min_length = min(content_lengths)
            max_length = max(content_lengths)
            print(f"   Average content length: {avg_length:.0f} characters")
            print(f"   Shortest content: {min_length} characters")
            print(f"   Longest content: {max_length} characters")
        
        print(f"\n✅ DATABASE ANALYSIS COMPLETE!")
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

if __name__ == "__main__":
    analyze_database()
