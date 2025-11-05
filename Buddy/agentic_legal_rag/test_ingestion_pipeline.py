#!/usr/bin/env python3
"""
Test script for the Legal Data Ingestion Pipeline
Demonstrates the complete pipeline with sample data
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingest import LegalDataIngestionPipeline

def test_pipeline():
    """Test the ingestion pipeline with sample data"""
    
    print("🧪 TESTING LEGAL DATA INGESTION PIPELINE")
    print("=" * 60)
    
    # Initialize pipeline with smaller parameters for testing
    pipeline = LegalDataIngestionPipeline(
        chunk_size=500,  # Smaller chunks for testing
        overlap=50,      # Smaller overlap
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        collection_name="test_legal_documents"
    )
    
    # Test with Constitution and Hugging Face (most reliable sources)
    sources = ['constitution', 'huggingface']
    
    print(f"📋 Testing with sources: {', '.join(sources)}")
    print(f"📏 Chunk size: 500 tokens")
    print(f"🔄 Overlap: 50 tokens")
    print(f"🤖 Embedding model: all-MiniLM-L6-v2")
    print()
    
    try:
        # Run the pipeline
        stats = pipeline.run_full_pipeline(
            sources=sources,
            clear_existing=True,
            save_intermediate=True
        )
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 PIPELINE RESULTS")
        print("=" * 60)
        
        if stats.get('status') == 'success':
            print("✅ Pipeline completed successfully!")
            print(f"⏱️  Total time: {stats.get('total_time_seconds', 0):.2f} seconds")
            print(f"📄 Documents scraped: {stats.get('scraped_documents', 0)}")
            print(f"🔧 Documents processed: {stats.get('processed_documents', 0)}")
            print(f"📦 Total chunks: {stats.get('total_chunks', 0)}")
            print(f"🧠 Embeddings generated: {stats.get('embedding_chunks', 0)}")
            print(f"💾 ChromaDB documents: {stats.get('chroma_documents', 0)}")
            
            # Test search functionality
            print("\n🔍 TESTING SEARCH FUNCTIONALITY")
            print("-" * 40)
            
            test_queries = [
                "article 21 constitution",
                "fundamental rights",
                "supreme court"
            ]
            
            for query in test_queries:
                results = pipeline.chroma_manager.test_search(query)
                print(f"Query: '{query}' → {len(results)} results")
                
        else:
            print("❌ Pipeline failed!")
            print(f"Error: {stats.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    
    return stats.get('status') == 'success'

def test_individual_components():
    """Test individual pipeline components"""
    
    print("\n🔧 TESTING INDIVIDUAL COMPONENTS")
    print("=" * 60)
    
    # Test scraper
    print("1. Testing Scraper...")
    try:
        from scraper import LegalDataScraper
        scraper = LegalDataScraper()
        docs = scraper.scrape_all_sources(['constitution'])
        print(f"   ✅ Scraper: {len(docs)} documents")
    except Exception as e:
        print(f"   ❌ Scraper failed: {e}")
    
    # Test preprocessor
    print("2. Testing Preprocessor...")
    try:
        from preprocess import LegalDocumentProcessor
        processor = LegalDocumentProcessor(chunk_size=500, overlap=50)
        
        # Create sample data
        sample_data = [{
            'title': 'Test Document',
            'content': 'This is a test legal document with some content about fundamental rights and constitutional provisions.',
            'source_url': 'https://example.com',
            'source_type': 'test',
            'doc_type': 'document'
        }]
        
        processed = processor.process_documents(sample_data)
        print(f"   ✅ Preprocessor: {len(processed)} documents, {sum(len(doc.chunks) for doc in processed)} chunks")
    except Exception as e:
        print(f"   ❌ Preprocessor failed: {e}")
    
    # Test embedder
    print("3. Testing Embedder...")
    try:
        from embed import EmbeddingProcessor
        embedder = EmbeddingProcessor()
        
        # Test single embedding
        embedding = embedder.embedder.generate_single_embedding("Test text for embedding")
        print(f"   ✅ Embedder: Generated embedding with shape {embedding.shape}")
    except Exception as e:
        print(f"   ❌ Embedder failed: {e}")
    
    # Test ChromaDB loader
    print("4. Testing ChromaDB Loader...")
    try:
        from load_chroma import ChromaDBManager
        manager = ChromaDBManager("test_collection")
        stats = manager.loader.get_collection_stats()
        print(f"   ✅ ChromaDB: Connected to collection with {stats.get('total_documents', 0)} documents")
    except Exception as e:
        print(f"   ❌ ChromaDB failed: {e}")

def main():
    """Main test function"""
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("🚀 LEGAL DATA INGESTION PIPELINE TEST")
    print("=" * 60)
    print("This test will:")
    print("1. Test individual components")
    print("2. Run a small-scale pipeline test")
    print("3. Verify search functionality")
    print()
    
    # Test individual components first
    test_individual_components()
    
    # Ask user if they want to run full pipeline test
    print("\n" + "=" * 60)
    response = input("Run full pipeline test? This will download data and generate embeddings. (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        success = test_pipeline()
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print("Your ingestion pipeline is ready to use.")
            print("\nNext steps:")
            print("1. Run: python ingest.py --sources constitution")
            print("2. Test with your existing RAG system")
            print("3. Add more sources as needed")
        else:
            print("\n❌ TESTS FAILED!")
            print("Check the logs for more details.")
    else:
        print("\n✅ Component tests completed.")
        print("Run 'python ingest.py' when ready for full pipeline.")

if __name__ == "__main__":
    main()






