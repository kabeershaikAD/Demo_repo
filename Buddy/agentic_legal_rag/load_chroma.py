#!/usr/bin/env python3
"""
ChromaDB Loading Module
Loads embeddings and metadata into existing ChromaDB instance
"""

import os
import sys
import json
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaDBLoader:
    """Handles loading data into ChromaDB"""
    
    def __init__(self, collection_name: str = "legal_documents"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.vectorstore = None
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=config.database.CHROMA_DB_PATH
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Connected to existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Legal documents and embeddings"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            # Initialize LangChain Chroma for compatibility
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=OpenAIEmbeddings(api_key=config.api.OPENAI_API_KEY)
            )
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def load_embeddings(self, embedding_data: List[Dict[str, Any]], batch_size: int = 100):
        """Load embeddings into ChromaDB"""
        try:
            logger.info(f"Loading {len(embedding_data)} embeddings into ChromaDB...")
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            embeddings = []
            
            for item in embedding_data:
                try:
                    # Extract data (handle both dict and EmbeddingData object)
                    if hasattr(item, 'doc_id'):
                        # EmbeddingData object
                        doc_id = item.doc_id
                        chunk_id = item.chunk_id
                        text = item.text
                        embedding = item.embedding if isinstance(item.embedding, np.ndarray) else np.array(item.embedding)
                        metadata = item.metadata
                    else:
                        # Dictionary
                        doc_id = item['doc_id']
                        chunk_id = item['chunk_id']
                        text = item['text']
                        embedding = np.array(item['embedding'])
                        metadata = item['metadata']
                except Exception as e:
                    logger.error(f"Error processing embedding item: {e}")
                    logger.error(f"Item type: {type(item)}")
                    logger.error(f"Item attributes: {dir(item) if hasattr(item, '__dict__') else 'N/A'}")
                    continue
                
                # Create unique ID with timestamp to avoid duplicates
                import time
                unique_id = f"{doc_id}_{chunk_id}_{int(time.time() * 1000000)}"
                
                # Prepare document text
                doc_text = f"Title: {metadata.get('title', '')}\n\nContent: {text}"
                
                # Clean metadata to remove None values (ChromaDB doesn't accept None)
                clean_metadata = {k: v for k, v in metadata.items() if v is not None}
                
                # Add to lists
                documents.append(doc_text)
                metadatas.append(clean_metadata)
                ids.append(unique_id)
                embeddings.append(embedding.tolist())
            
            # Load in batches
            total_batches = (len(embedding_data) + batch_size - 1) // batch_size
            
            for i in range(0, len(embedding_data), batch_size):
                batch_end = min(i + batch_size, len(embedding_data))
                batch_docs = documents[i:batch_end]
                batch_metadatas = metadatas[i:batch_end]
                batch_ids = ids[i:batch_end]
                batch_embeddings = embeddings[i:batch_end]
                
                # Add batch to collection
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metadatas,
                    ids=batch_ids,
                    embeddings=batch_embeddings
                )
                
                logger.info(f"Loaded batch {i//batch_size + 1}/{total_batches}")
            
            logger.info(f"Successfully loaded {len(embedding_data)} embeddings into ChromaDB")
            
        except Exception as e:
            logger.error(f"Error loading embeddings into ChromaDB: {e}")
            raise
    
    def load_from_json(self, json_file: str, batch_size: int = 100):
        """Load embeddings from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                embedding_data = json.load(f)
            
            self.load_embeddings(embedding_data, batch_size)
            
        except Exception as e:
            logger.error(f"Error loading from JSON file {json_file}: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            
            # Get sample metadata to understand structure
            sample = self.collection.get(limit=1)
            
            stats = {
                'total_documents': count,
                'collection_name': self.collection_name,
                'sample_metadata_keys': list(sample['metadatas'][0].keys()) if sample['metadatas'] else []
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching collection: {e}")
            return []
    
    def clear_collection(self):
        """Clear all data from collection"""
        try:
            # Delete and recreate collection
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Legal documents and embeddings"}
            )
            logger.info(f"Cleared collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

class ChromaDBManager:
    """Manages ChromaDB operations"""
    
    def __init__(self, collection_name: str = "legal_documents"):
        self.loader = ChromaDBLoader(collection_name)
    
    def ingest_pipeline(self, embedding_file: str, clear_existing: bool = False):
        """Complete ingestion pipeline"""
        try:
            if clear_existing:
                logger.info("Clearing existing collection...")
                self.loader.clear_collection()
            
            logger.info(f"Starting ingestion from {embedding_file}")
            
            # Load embeddings
            self.loader.load_from_json(embedding_file)
            
            # Get stats
            stats = self.loader.get_collection_stats()
            logger.info(f"Ingestion complete. Stats: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in ingestion pipeline: {e}")
            raise
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            results = self.loader.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else 0.0
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []
    
    def test_search(self, query: str = "article 21 constitution"):
        """Test search functionality"""
        try:
            logger.info(f"Testing search with query: {query}")
            
            results = self.search_similar(query, n_results=3)
            
            logger.info(f"Found {len(results)} results:")
            for i, result in enumerate(results):
                logger.info(f"  {i+1}. {result['metadata'].get('title', 'Unknown')} (distance: {result['distance']:.3f})")
                logger.info(f"     {result['document'][:100]}...")
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing search: {e}")
            return []

def main():
    """Main function for testing ChromaDB loader"""
    # Test loading
    manager = ChromaDBManager()
    
    # Load embeddings if file exists
    embedding_file = "data/legal_embeddings.json"
    if os.path.exists(embedding_file):
        stats = manager.ingest_pipeline(embedding_file, clear_existing=True)
        print(f"Loaded {stats.get('total_documents', 0)} documents")
        
        # Test search
        results = manager.test_search("article 21 constitution")
        print(f"Search returned {len(results)} results")
    else:
        print(f"Embedding file {embedding_file} not found. Run embed.py first.")

if __name__ == "__main__":
    main()
