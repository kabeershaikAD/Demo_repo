"""
Diagnostic script to check retriever issues
"""
import sys
import os

# Add the projects/slm_orchestration_legal_rag directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
slm_project_path = os.path.join(project_root, 'projects', 'slm_orchestration_legal_rag')
sys.path.insert(0, slm_project_path)

print("=" * 60)
print("DIAGNOSING RETRIEVER ISSUES")
print("=" * 60)

# 1. Check API Key
print("\n1. Checking API Key Configuration...")
try:
    from config import config
    groq_key = config.api.GROQ_API_KEY
    openai_key = config.api.OPENAI_API_KEY
    
    print(f"   GROQ_API_KEY: {'[SET]' if groq_key else '[NOT SET]'}")
    print(f"   OPENAI_API_KEY: {'[SET]' if openai_key else '[NOT SET]'}")
    
    if not openai_key:
        print("\n   WARNING: OpenAI API key is required for embeddings!")
        print("   The retriever uses OpenAI embeddings to search ChromaDB.")
        print("   Set OPENAI_API_KEY environment variable or in config.py")
except Exception as e:
    print(f"   ERROR: Error loading config: {e}")

# 2. Check ChromaDB Path
print("\n2. Checking ChromaDB Path...")
current_dir = os.getcwd()
consolidated_path = os.path.join(current_dir, "chroma_db_consolidated")

if os.path.exists(consolidated_path):
    print(f"   [FOUND] {consolidated_path}")
    # Check if it has files
    files = os.listdir(consolidated_path)
    print(f"   Files in directory: {len(files)}")
    for f in files[:5]:
        print(f"     - {f}")
else:
    print(f"   [NOT FOUND] {consolidated_path}")
    print(f"   Current directory: {current_dir}")

# 3. Try to connect to ChromaDB
print("\n3. Testing ChromaDB Connection...")
try:
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    
    if not openai_key:
        print("   [SKIP] Skipping connection test (no OpenAI API key)")
    else:
        embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=openai_key
        )
        
        vector_db = Chroma(
            collection_name="langchain",
            embedding_function=embedding_model,
            persist_directory=consolidated_path
        )
        
        print("   [SUCCESS] Connected to ChromaDB")
        
        # Try to get collection count
        try:
            collection = vector_db._collection
            count = collection.count()
            print(f"   Collection count: {count} documents")
            
            if count == 0:
                print("   [WARNING] Collection is empty!")
                print("   You need to add documents to ChromaDB first.")
            else:
                # Try a test search
                print("\n4. Testing Search...")
                test_query = "IPC section 302"
                print(f"   Query: '{test_query}'")
                results = vector_db.similarity_search_with_score(test_query, k=3)
                print(f"   Results: {len(results)} documents found")
                
                if results:
                    print("   [SUCCESS] Search is working!")
                    for i, (doc, score) in enumerate(results[:2], 1):
                        print(f"   {i}. Score: {score:.3f}, Title: {doc.metadata.get('title', 'N/A')}")
                else:
                    print("   [WARNING] No results found for test query")
                    
        except Exception as e:
            print(f"   [ERROR] Error accessing collection: {e}")
            
except Exception as e:
    print(f"   [ERROR] Connection failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)

