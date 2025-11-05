#!/usr/bin/env python3
"""
Test script for the legal data ingestion pipeline
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config import config
        print("Config imported")
        
        from scraper import LegalDataScraper
        print("Scraper imported")
        
        from preprocess import LegalDocumentProcessor
        print("Preprocessor imported")
        
        from embed import EmbeddingProcessor
        print("Embedder imported")
        
        from load_chroma import ChromaDBLoader
        print("ChromaDB loader imported")
        
        from ingest import LegalDataIngestionPipeline
        print("Main pipeline imported")
        
        return True
        
    except Exception as e:
        print(f"Import failed: {e}")
        return False

def test_preprocessing():
    """Test preprocessing with sample data"""
    print("\nTesting preprocessing...")
    
    try:
        from preprocess import LegalDocumentProcessor
        
        # Create sample data
        sample_data = [
            {
                "title": "Test Article 21",
                "content": "Article 21 of the Indian Constitution states: 'No person shall be deprived of his life or personal liberty except according to procedure established by law.' This is a fundamental right.",
                "source_url": "https://example.com",
                "source_type": "constitution",
                "section_article": "Article 21",
                "date": "1950-01-26",
                "doc_type": "constitution"
            }
        ]
        
        # Process documents
        processor = LegalDocumentProcessor(chunk_size=200, overlap=50)
        processed_docs = processor.process_documents(sample_data)
        
        print(f"✅ Processed {len(processed_docs)} documents")
        
        if processed_docs:
            total_chunks = sum(len(doc.chunks) for doc in processed_docs)
            print(f"✅ Created {total_chunks} chunks")
            
            # Show sample chunk
            if processed_docs[0].chunks:
                sample_chunk = processed_docs[0].chunks[0]
                print(f"✅ Sample chunk: {sample_chunk['text'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Preprocessing failed: {e}")
        return False

def test_embedding():
    """Test embedding generation"""
    print("\n🧠 Testing embedding...")
    
    try:
        from embed import EmbeddingProcessor
        
        # Create sample processed data
        sample_processed = [
            {
                "title": "Test Article 21",
                "chunks": [
                    {
                        "text": "Article 21 of the Indian Constitution states: 'No person shall be deprived of his life or personal liberty except according to procedure established by law.'",
                        "metadata": {"chunk_id": 0, "source": "constitution"}
                    }
                ],
                "source_url": "https://example.com",
                "source_type": "constitution",
                "section_article": "Article 21",
                "date": "1950-01-26",
                "doc_type": "constitution"
            }
        ]
        
        # Generate embeddings
        embedder = EmbeddingProcessor()
        embedding_data = embedder.process_documents(sample_processed)
        
        print(f"✅ Generated embeddings for {len(embedding_data)} chunks")
        
        if embedding_data:
            sample_embedding = embedding_data[0]
            print(f"✅ Sample embedding shape: {sample_embedding.embedding.shape}")
            print(f"✅ Sample text: {sample_embedding.text[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        return False

def test_chroma_loading():
    """Test ChromaDB loading"""
    print("\n💾 Testing ChromaDB loading...")
    
    try:
        from load_chroma import ChromaDBLoader
        
        # Create sample embedding data
        sample_embeddings = [
            {
                "text": "Article 21 of the Indian Constitution states: 'No person shall be deprived of his life or personal liberty except according to procedure established by law.'",
                "embedding": [0.1] * 384,  # Mock embedding
                "metadata": {"chunk_id": 0, "source": "constitution", "title": "Test Article 21"}
            }
        ]
        
        # Load into ChromaDB
        loader = ChromaDBLoader("test_collection")
        loader.load_embeddings(sample_embeddings)
        
        # Get stats
        stats = loader.get_collection_stats()
        print(f"✅ Loaded {stats.get('total_documents', 0)} documents into ChromaDB")
        
        # Test search
        results = loader.test_search("article 21 constitution")
        print(f"✅ Search test: Found {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB loading failed: {e}")
        return False

def main():
    """Main test function"""
    print("TESTING LEGAL DATA INGESTION PIPELINE")
    print("=" * 50)
    
    # Test 1: Imports
    print("\n1. Testing imports...")
    imports_ok = test_imports()
    
    # Test 2: Preprocessing
    print("\n2. Testing preprocessing...")
    preprocess_ok = test_preprocessing()
    
    # Test 3: Embedding
    print("\n3. Testing embedding...")
    embedding_ok = test_embedding()
    
    # Test 4: ChromaDB loading
    print("\n4. Testing ChromaDB loading...")
    chroma_ok = test_chroma_loading()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print(f"Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"Preprocessing: {'✅ PASS' if preprocess_ok else '❌ FAIL'}")
    print(f"Embedding: {'✅ PASS' if embedding_ok else '❌ FAIL'}")
    print(f"ChromaDB: {'✅ PASS' if chroma_ok else '❌ FAIL'}")
    
    if all([imports_ok, preprocess_ok, embedding_ok, chroma_ok]):
        print("\n🎉 ALL TESTS PASSED!")
        print("Your ingestion pipeline is ready to use!")
        print("\nNext steps:")
        print("1. Run: python demo_ingestion.py")
        print("2. Run: python ingest.py --sources constitution")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Check the errors above and fix them.")
        print("\nIf NLTK issues persist, run: python setup_nltk.py")

if __name__ == "__main__":
    main()
