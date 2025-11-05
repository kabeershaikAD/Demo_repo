#!/usr/bin/env python3
"""
Fix and Re-index Consolidated ChromaDB
This script ensures the consolidated database is properly indexed and searchable
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Buddy', 'agentic_legal_rag'))

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import config
import chromadb

def fix_consolidated_db():
    """Fix the consolidated ChromaDB to ensure it's searchable"""
    
    print("=" * 60)
    print("FIXING CONSOLIDATED CHROMADB")
    print("=" * 60)
    
    consolidated_path = "./chroma_db_consolidated"
    
    if not os.path.exists(consolidated_path):
        print(f"ERROR: Consolidated database not found at {consolidated_path}")
        return
    
    print(f"\n1. Checking consolidated database...")
    
    # Check using ChromaDB client
    try:
        client = chromadb.PersistentClient(path=consolidated_path)
        collections = client.list_collections()
        
        print(f"   Found {len(collections)} collections:")
        for collection in collections:
            count = collection.count()
            print(f"     - {collection.name}: {count} documents")
            
            if count == 0:
                print(f"       WARNING: Collection {collection.name} is empty!")
            else:
                # Test query
                try:
                    results = collection.query(
                        query_texts=["Article 21"],
                        n_results=3
                    )
                    print(f"       Test query returned {len(results['ids'][0]) if results['ids'] else 0} results")
                except Exception as e:
                    print(f"       ERROR testing query: {e}")
                    
    except Exception as e:
        print(f"   Error checking ChromaDB: {e}")
    
    # Check using LangChain
    print(f"\n2. Testing LangChain Chroma connection...")
    try:
        embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=config.api.OPENAI_API_KEY
        )
        
        vectorstore = Chroma(
            collection_name="langchain",
            embedding_function=embedding_model,
            persist_directory=consolidated_path
        )
        
        # Try to get document count
        try:
            # This is tricky - Chroma doesn't expose count directly in LangChain
            # But we can test with a search
            print("   Testing search...")
            results = vectorstore.similarity_search_with_score("Article 21", k=5)
            print(f"   Found {len(results)} results")
            
            if results:
                print("   SUCCESS: Database is searchable!")
                for i, (doc, score) in enumerate(results[:3], 1):
                    print(f"     {i}. Score: {score:.4f}")
                    print(f"        Content: {doc.page_content[:100]}...")
            else:
                print("   WARNING: No results found - database may not be properly indexed")
                print("   This could mean:")
                print("     1. Documents were added but embeddings weren't created")
                print("     2. Collection name mismatch")
                print("     3. Documents were added to wrong collection")
                
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"   Error with LangChain: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 60)
    
    print("\nRECOMMENDATIONS:")
    print("1. If collection is empty or has 0 results:")
    print("   - Re-run consolidate_chromadb.py")
    print("   - Check that embeddings are being created")
    print("2. If path issues:")
    print("   - Update retriever_agent.py path resolution")
    print("   - Use absolute paths if relative paths fail")
    print("3. If collection name mismatch:")
    print("   - Ensure both creation and retrieval use 'langchain' collection")

if __name__ == "__main__":
    fix_consolidated_db()


