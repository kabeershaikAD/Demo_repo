#!/usr/bin/env python3
"""
Demo script for the Legal Data Ingestion Pipeline
Shows how to use the pipeline with sample data
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_data():
    """Create sample legal data for testing"""
    sample_data = [
        {
            "title": "Article 21 of the Indian Constitution",
            "content": "Article 21 of the Indian Constitution states: 'No person shall be deprived of his life or personal liberty except according to procedure established by law.' This fundamental right is considered the heart of the Constitution and has been interpreted by the Supreme Court to include various derived rights such as the right to live with dignity, right to health, right to education, and right to privacy.",
            "source_url": "https://legislative.gov.in/constitution-of-india",
            "source_type": "constitution",
            "section_article": "Article 21",
            "date": "1950-01-26",
            "doc_type": "constitution",
            "metadata": {"scraped_at": "2024-01-01T00:00:00Z"}
        },
        {
            "title": "Section 302 of the Indian Penal Code",
            "content": "Section 302 of the Indian Penal Code deals with the punishment for murder. It states that whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine. Murder is defined as the intentional killing of a person with malice aforethought.",
            "source_url": "https://www.indiacode.nic.in/show-data?actid=AC_CEN_0001_00000001",
            "source_type": "indiacode",
            "section_article": "Section 302",
            "date": "1860-10-06",
            "doc_type": "statute",
            "metadata": {"act": "Indian Penal Code", "year": 1860}
        },
        {
            "title": "Right to Information Act 2005",
            "content": "The Right to Information Act 2005 is a fundamental right under Article 19(1)(a) of the Constitution. It provides for setting out the practical regime of right to information for citizens to secure access to information under the control of public authorities, in order to promote transparency and accountability in the working of every public authority.",
            "source_url": "https://www.indiacode.nic.in/show-data?actid=AC_CEN_0001_00000001",
            "source_type": "indiacode",
            "section_article": "Section 1",
            "date": "2005-06-15",
            "doc_type": "statute",
            "metadata": {"act": "Right to Information Act", "year": 2005}
        }
    ]
    
    # Save sample data
    os.makedirs('data', exist_ok=True)
    with open('data/sample_legal_data.json', 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created sample data with {len(sample_data)} documents")
    return sample_data

def demo_preprocessing():
    """Demo the preprocessing step"""
    print("\n🔧 DEMO: PREPROCESSING")
    print("-" * 30)
    
    try:
        from preprocess import LegalDocumentProcessor
        
        # Load sample data
        with open('data/sample_legal_data.json', 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
        # Process documents
        processor = LegalDocumentProcessor(chunk_size=500, overlap=50)
        processed_docs = processor.process_documents(sample_data)
        
        print(f"✅ Processed {len(processed_docs)} documents")
        
        # Show chunking results
        total_chunks = sum(len(doc.chunks) for doc in processed_docs)
        print(f"✅ Created {total_chunks} chunks")
        
        # Show sample chunk
        if processed_docs and processed_docs[0].chunks:
            sample_chunk = processed_docs[0].chunks[0]
            print(f"✅ Sample chunk: {sample_chunk['text'][:100]}...")
        
        return processed_docs
        
    except Exception as e:
        print(f"❌ Preprocessing failed: {e}")
        return None

def demo_embedding():
    """Demo the embedding step"""
    print("\n🧠 DEMO: EMBEDDING GENERATION")
    print("-" * 30)
    
    try:
        from embed import EmbeddingProcessor
        
        # Load processed data
        with open('data/processed_legal_data.json', 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        # Generate embeddings
        embedder = EmbeddingProcessor()
        embedding_data = embedder.process_documents(processed_data)
        
        print(f"✅ Generated embeddings for {len(embedding_data)} chunks")
        
        # Show embedding info
        if embedding_data:
            sample_embedding = embedding_data[0]
            print(f"✅ Sample embedding shape: {sample_embedding.embedding.shape}")
            print(f"✅ Sample text: {sample_embedding.text[:100]}...")
        
        return embedding_data
        
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        return None

def demo_chroma_loading():
    """Demo the ChromaDB loading step"""
    print("\n💾 DEMO: CHROMADB LOADING")
    print("-" * 30)
    
    try:
        from load_chroma import ChromaDBManager
        
        # Load embeddings
        with open('data/legal_embeddings.json', 'r', encoding='utf-8') as f:
            embedding_data = json.load(f)
        
        # Load into ChromaDB
        manager = ChromaDBManager("demo_legal_docs")
        manager.loader.load_embeddings(embedding_data)
        
        # Get stats
        stats = manager.loader.get_collection_stats()
        print(f"✅ Loaded {stats.get('total_documents', 0)} documents into ChromaDB")
        
        # Test search
        results = manager.test_search("article 21 constitution")
        print(f"✅ Search test: Found {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB loading failed: {e}")
        return False

def demo_full_pipeline():
    """Demo the full pipeline"""
    print("\n🚀 DEMO: FULL PIPELINE")
    print("-" * 30)
    
    try:
        from ingest import LegalDataIngestionPipeline
        
        # Create sample data first
        create_sample_data()
        
        # Initialize pipeline
        pipeline = LegalDataIngestionPipeline(
            chunk_size=500,
            overlap=50,
            collection_name="demo_legal_docs"
        )
        
        # Run pipeline with sample data
        print("Running full pipeline...")
        
        # Step 1: Preprocess
        processed_docs = demo_preprocessing()
        if not processed_docs:
            return False
        
        # Step 2: Embed
        embedding_data = demo_embedding()
        if not embedding_data:
            return False
        
        # Step 3: Load into ChromaDB
        success = demo_chroma_loading()
        if not success:
            return False
        
        print("✅ Full pipeline completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Full pipeline failed: {e}")
        return False

def main():
    """Main demo function"""
    print("🎬 LEGAL DATA INGESTION PIPELINE DEMO")
    print("=" * 50)
    print("This demo shows how the ingestion pipeline works")
    print("with sample legal data.")
    print()
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Ask user what they want to demo
    print("What would you like to demo?")
    print("1. Create sample data")
    print("2. Test preprocessing")
    print("3. Test embedding")
    print("4. Test ChromaDB loading")
    print("5. Run full pipeline")
    print("6. All of the above")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == "1":
        create_sample_data()
    elif choice == "2":
        create_sample_data()
        demo_preprocessing()
    elif choice == "3":
        create_sample_data()
        demo_preprocessing()
        demo_embedding()
    elif choice == "4":
        create_sample_data()
        demo_preprocessing()
        demo_embedding()
        demo_chroma_loading()
    elif choice == "5":
        demo_full_pipeline()
    elif choice == "6":
        create_sample_data()
        demo_preprocessing()
        demo_embedding()
        demo_chroma_loading()
        print("\n🎉 All demos completed!")
    else:
        print("Invalid choice. Please run the script again.")
    
    print("\n" + "=" * 50)
    print("Demo completed! Check the 'data' folder for generated files.")

if __name__ == "__main__":
    main()






