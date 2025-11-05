#!/usr/bin/env python3
"""
Diagnose Retriever Issues
Check what's wrong with the retriever and consolidated ChromaDB
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Buddy', 'agentic_legal_rag'))

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import config
import chromadb

def diagnose_retriever():
    """Diagnose retriever issues"""
    
    print("=" * 60)
    print("RETRIEVER DIAGNOSTICS")
    print("=" * 60)
    
    # Check paths
    print("\n1. Checking ChromaDB paths...")
    paths_to_check = [
        "./chroma_db_consolidated",
        "./Buddy/agentic_legal_rag/chroma_db_consolidated",
        "../../chroma_db_consolidated",
        "./chroma_db_",
        "./Buddy/agentic_legal_rag/chroma_db_"
    ]
    
    for path in paths_to_check:
        exists = os.path.exists(path)
        print(f"  {path}: {'EXISTS' if exists else 'NOT FOUND'}")
    
    # Check consolidated database
    print("\n2. Checking consolidated ChromaDB...")
    consolidated_path = "./chroma_db_consolidated"
    
    if os.path.exists(consolidated_path):
        try:
            # Check using ChromaDB client directly
            client = chromadb.PersistentClient(path=consolidated_path)
            collections = client.list_collections()
            
            print(f"  Found {len(collections)} collections:")
            for collection in collections:
                count = collection.count()
                print(f"    - {collection.name}: {count} documents")
                
                # Try to get a sample
                if count > 0:
                    sample = collection.get(limit=1)
                    if sample and 'ids' in sample and len(sample['ids']) > 0:
                        print(f"      Sample ID: {sample['ids'][0]}")
                        if 'documents' in sample and len(sample['documents']) > 0:
                            print(f"      Sample doc preview: {sample['documents'][0][:100]}...")
        except Exception as e:
            print(f"  Error checking ChromaDB client: {e}")
        
        # Check using LangChain Chroma
        print("\n3. Testing LangChain Chroma connection...")
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
            
            # Try a search
            print("  Testing search with query: 'Article 21'")
            results = vectorstore.similarity_search_with_score("Article 21", k=5)
            print(f"  Found {len(results)} results")
            
            if results:
                for i, (doc, score) in enumerate(results, 1):
                    print(f"\n  Result {i}:")
                    print(f"    Score: {score:.4f}")
                    print(f"    Content preview: {doc.page_content[:150]}...")
                    print(f"    Metadata: {doc.metadata}")
            else:
                print("  WARNING: No results found!")
                print("  This suggests the database might not be properly indexed")
                
        except Exception as e:
            print(f"  Error with LangChain Chroma: {e}")
            import traceback
            traceback.print_exc()
    
    # Check retriever agent
    print("\n4. Testing RetrieverAgent...")
    try:
        from retriever_agent import RetrieverAgent
        
        retriever = RetrieverAgent()
        print(f"  ChromaDB path: {retriever.chroma_db_path}")
        print(f"  Vector DB initialized: {retriever.vector_db is not None}")
        
        if retriever.vector_db:
            print("  Testing retrieval...")
            result = retriever.retrieve("Article 21", k=5)
            print(f"  Retrieved {len(result.statutes) + len(result.judgments)} documents")
            print(f"    Statutes: {len(result.statutes)}")
            print(f"    Judgments: {len(result.judgments)}")
            
            if len(result.statutes) == 0 and len(result.judgments) == 0:
                print("  WARNING: Retriever returned 0 documents!")
        else:
            print("  ERROR: Vector DB is None!")
            
    except Exception as e:
        print(f"  Error testing RetrieverAgent: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Diagnostics complete")
    print("=" * 60)

if __name__ == "__main__":
    diagnose_retriever()


