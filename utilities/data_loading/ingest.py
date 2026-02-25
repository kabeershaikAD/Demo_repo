#!/usr/bin/env python3
"""
Legal Data Ingestion Pipeline
Main orchestrator for scraping → preprocessing → embedding → loading into ChromaDB
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import LegalDataScraper
from preprocess import LegalDocumentProcessor
from embed import EmbeddingProcessor
from load_chroma import ChromaDBManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LegalDataIngestionPipeline:
    """Main ingestion pipeline orchestrator"""
    
    def __init__(self, 
                 chunk_size: int = 800, 
                 overlap: int = 100,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 collection_name: str = "legal_documents"):
        
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        
        # Initialize components
        self.scraper = LegalDataScraper()
        self.processor = LegalDocumentProcessor(chunk_size, overlap)
        self.embedder = EmbeddingProcessor(embedding_model)
        self.chroma_manager = ChromaDBManager(collection_name)
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
    
    def run_full_pipeline(self, 
                         sources: Optional[List[str]] = None,
                         clear_existing: bool = False,
                         save_intermediate: bool = True) -> Dict[str, Any]:
        """Run the complete ingestion pipeline"""
        
        start_time = time.time()
        pipeline_stats = {
            'start_time': datetime.now().isoformat(),
            'sources': sources or ['all'],
            'chunk_size': self.chunk_size,
            'overlap': self.overlap,
            'embedding_model': self.embedding_model,
            'collection_name': self.collection_name
        }
        
        try:
            # Step 1: Scrape data
            logger.info("=" * 60)
            logger.info("STEP 1: SCRAPING LEGAL DATA")
            logger.info("=" * 60)
            
            scraped_docs = self.scraper.scrape_all_sources(sources)
            pipeline_stats['scraped_documents'] = len(scraped_docs)
            
            if not scraped_docs:
                logger.warning("No documents scraped. Pipeline stopping.")
                return pipeline_stats
            
            logger.info(f"Scraped {len(scraped_docs)} documents")
            
            if save_intermediate:
                self.scraper.save_scraped_data(scraped_docs, "data/scraped_legal_data.json")
                logger.info("Saved scraped data to data/scraped_legal_data.json")
            
            # Step 2: Preprocess data
            logger.info("=" * 60)
            logger.info("STEP 2: PREPROCESSING DATA")
            logger.info("=" * 60)
            
            # Convert to dict format for processor
            scraped_data = []
            for doc in scraped_docs:
                scraped_data.append({
                    'title': doc.title,
                    'content': doc.content,
                    'source_url': doc.source_url,
                    'source_type': doc.source_type,
                    'section_article': doc.section_article,
                    'date': doc.date,
                    'doc_type': doc.doc_type,
                    'metadata': doc.metadata
                })
            
            processed_docs = self.processor.process_documents(scraped_data)
            pipeline_stats['processed_documents'] = len(processed_docs)
            pipeline_stats['total_chunks'] = sum(len(doc.chunks) for doc in processed_docs)
            
            logger.info(f"Processed {len(processed_docs)} documents into {pipeline_stats['total_chunks']} chunks")
            
            if save_intermediate:
                self.processor.save_processed_data(processed_docs, "data/processed_legal_data.json")
                logger.info("Saved processed data to data/processed_legal_data.json")
            
            # Step 3: Generate embeddings
            logger.info("=" * 60)
            logger.info("STEP 3: GENERATING EMBEDDINGS")
            logger.info("=" * 60)
            
            # Pass ProcessedDocument objects directly to embedder
            embedding_data = self.embedder.process_documents(processed_docs)
            pipeline_stats['embedding_chunks'] = len(embedding_data)
            
            logger.info(f"Generated embeddings for {len(embedding_data)} chunks")
            
            # Calculate similarities
            embedding_data = self.embedder.calculate_similarities(embedding_data)
            
            if save_intermediate:
                self.embedder.save_embeddings(embedding_data, "data/legal_embeddings.json")
                logger.info("Saved embeddings to data/legal_embeddings.json")
            
            # Step 4: Load into ChromaDB
            logger.info("=" * 60)
            logger.info("STEP 4: LOADING INTO CHROMADB")
            logger.info("=" * 60)
            
            # Convert to dict format for ChromaDB
            embedding_dicts = []
            for item in embedding_data:
                embedding_dicts.append({
                    'doc_id': item.doc_id,
                    'chunk_id': item.chunk_id,
                    'text': item.text,
                    'embedding': item.embedding.tolist(),
                    'metadata': item.metadata,
                    'similarity_scores': item.similarity_scores
                })
            
            if clear_existing:
                self.chroma_manager.loader.clear_collection()
            
            self.chroma_manager.loader.load_embeddings(embedding_dicts)
            chroma_stats = self.chroma_manager.loader.get_collection_stats()
            pipeline_stats['chroma_documents'] = chroma_stats.get('total_documents', 0)
            
            logger.info(f"Loaded {pipeline_stats['chroma_documents']} documents into ChromaDB")
            
            # Step 5: Test search
            logger.info("=" * 60)
            logger.info("STEP 5: TESTING SEARCH")
            logger.info("=" * 60)
            
            test_queries = [
                "article 21 constitution",
                "section 302 ipc murder",
                "fundamental rights",
                "supreme court judgment"
            ]
            
            search_results = {}
            for query in test_queries:
                results = self.chroma_manager.test_search(query)
                search_results[query] = len(results)
                logger.info(f"Query '{query}': {len(results)} results")
            
            pipeline_stats['search_results'] = search_results
            
            # Pipeline complete
            end_time = time.time()
            pipeline_stats['end_time'] = datetime.now().isoformat()
            pipeline_stats['total_time_seconds'] = end_time - start_time
            pipeline_stats['status'] = 'success'
            
            logger.info("=" * 60)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info(f"Total time: {pipeline_stats['total_time_seconds']:.2f} seconds")
            logger.info(f"Documents processed: {pipeline_stats['processed_documents']}")
            logger.info(f"Chunks created: {pipeline_stats['total_chunks']}")
            logger.info(f"Embeddings generated: {pipeline_stats['embedding_chunks']}")
            logger.info(f"ChromaDB documents: {pipeline_stats['chroma_documents']}")
            
            return pipeline_stats
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            pipeline_stats['status'] = 'failed'
            pipeline_stats['error'] = str(e)
            pipeline_stats['end_time'] = datetime.now().isoformat()
            pipeline_stats['total_time_seconds'] = time.time() - start_time
            return pipeline_stats
    
    def run_from_existing(self, 
                         embedding_file: str = "data/legal_embeddings.json",
                         clear_existing: bool = False) -> Dict[str, Any]:
        """Run pipeline from existing embedding file"""
        
        start_time = time.time()
        
        try:
            logger.info(f"Loading embeddings from {embedding_file}")
            
            # Load embeddings
            with open(embedding_file, 'r', encoding='utf-8') as f:
                embedding_data = json.load(f)
            
            # Load into ChromaDB
            self.chroma_manager.loader.load_embeddings(embedding_data)
            chroma_stats = self.chroma_manager.loader.get_collection_stats()
            
            end_time = time.time()
            
            stats = {
                'start_time': datetime.now().isoformat(),
                'embedding_file': embedding_file,
                'chroma_documents': chroma_stats.get('total_documents', 0),
                'total_time_seconds': end_time - start_time,
                'status': 'success'
            }
            
            logger.info(f"Successfully loaded {stats['chroma_documents']} documents into ChromaDB")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to load from existing file: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'total_time_seconds': time.time() - start_time
            }

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='Legal Data Ingestion Pipeline')
    
    parser.add_argument('--sources', nargs='+', 
                       choices=['indiacode', 'constitution', 'github', 'zenodo', 'ildc', 'kaggle', 'huggingface', 'lawsum'],
                       help='Sources to scrape (default: all)')
    
    parser.add_argument('--chunk-size', type=int, default=800,
                       help='Chunk size in tokens (default: 800)')
    
    parser.add_argument('--overlap', type=int, default=100,
                       help='Overlap between chunks (default: 100)')
    
    parser.add_argument('--embedding-model', default='sentence-transformers/all-MiniLM-L6-v2',
                       help='Embedding model to use')
    
    parser.add_argument('--collection-name', default='legal_documents',
                       help='ChromaDB collection name')
    
    parser.add_argument('--clear-existing', action='store_true',
                       help='Clear existing collection before loading')
    
    parser.add_argument('--from-existing', type=str,
                       help='Load from existing embedding file instead of scraping')
    
    parser.add_argument('--save-intermediate', action='store_true', default=True,
                       help='Save intermediate files')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = LegalDataIngestionPipeline(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        embedding_model=args.embedding_model,
        collection_name=args.collection_name
    )
    
    # Run pipeline
    if args.from_existing:
        stats = pipeline.run_from_existing(args.from_existing, args.clear_existing)
    else:
        stats = pipeline.run_full_pipeline(
            sources=args.sources,
            clear_existing=args.clear_existing,
            save_intermediate=args.save_intermediate
        )
    
    # Save pipeline stats
    with open('logs/pipeline_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Status: {stats.get('status', 'unknown')}")
    print(f"Total time: {stats.get('total_time_seconds', 0):.2f} seconds")
    
    if stats.get('status') == 'success':
        print(f"Documents processed: {stats.get('processed_documents', 0)}")
        print(f"Chunks created: {stats.get('total_chunks', 0)}")
        print(f"ChromaDB documents: {stats.get('chroma_documents', 0)}")
    else:
        print(f"Error: {stats.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
