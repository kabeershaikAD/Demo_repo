"""
Debug script to test retriever agent and ChromaDB connection
"""
import sys
import os

# Add the projects/slm_orchestration_legal_rag directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
slm_project_path = os.path.join(project_root, 'projects', 'slm_orchestration_legal_rag')
sys.path.insert(0, slm_project_path)

from retriever_agent import RetrieverAgent
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_retriever():
    """Test the retriever agent"""
    print("=" * 60)
    print("Testing Retriever Agent")
    print("=" * 60)
    
    try:
        # Initialize retriever
        print("\n1. Initializing RetrieverAgent...")
        retriever = RetrieverAgent()
        
        print(f"   ChromaDB Path: {retriever.chroma_db_path}")
        print(f"   Vector DB: {retriever.vector_db}")
        
        if retriever.vector_db is None:
            print("   ❌ ERROR: Vector DB is None!")
            print("   This means ChromaDB connection failed.")
            return
        
        # Test query
        test_query = "IPC section 302"
        print(f"\n2. Testing retrieval with query: '{test_query}'")
        
        result = retriever.retrieve(test_query, k=5)
        
        print(f"\n3. Results:")
        print(f"   Total Retrieved: {result.total_retrieved}")
        print(f"   Statutes: {len(result.statutes)}")
        print(f"   Judgments: {len(result.judgments)}")
        print(f"   Retrieval Time: {result.retrieval_time:.2f}s")
        
        if result.total_retrieved == 0:
            print("\n   ❌ NO DOCUMENTS RETRIEVED!")
            print("\n   Possible issues:")
            print("   1. ChromaDB is empty or not properly indexed")
            print("   2. Collection name mismatch")
            print("   3. Embeddings not created")
            print("   4. Query doesn't match any documents")
            
            # Try to check collection
            try:
                collection = retriever.vector_db._collection
                count = collection.count()
                print(f"\n   Collection count: {count}")
                if count == 0:
                    print("   ⚠️  Collection is empty!")
            except Exception as e:
                print(f"   Error checking collection: {e}")
        else:
            print("\n   ✅ Documents retrieved successfully!")
            print("\n   Sample documents:")
            for i, doc in enumerate(result.statutes[:2] + result.judgments[:2], 1):
                print(f"   {i}. {doc.title} (Type: {doc.doc_type}, Score: {doc.similarity_score:.3f})")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retriever()



