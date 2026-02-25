#!/usr/bin/env python3
"""
Consolidate Multiple ChromaDB Instances
Merges all ChromaDB data from different locations into a single unified ChromaDB
"""

import os
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Any
import logging

# Add the projects/slm_orchestration_legal_rag directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
slm_project_path = os.path.join(project_root, 'projects', 'slm_orchestration_legal_rag')
sys.path.insert(0, slm_project_path)

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaDBConsolidator:
    """Consolidate multiple ChromaDB instances into one"""
    
    def __init__(self, output_path: str = "./chroma_db_consolidated"):
        self.output_path = output_path
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=config.api.OPENAI_API_KEY
        )
        
        # ChromaDB locations to consolidate
        self.chromadb_locations = [
            "./chroma_db_",
            "./Buddy/agentic_legal_rag/chroma_db_",
            "./Buddy/Indian-Law-Voicebot/chroma_db_"
        ]
        
        # Also read from SQLite database
        self.sqlite_db_path = "./indian_legal_db.sqlite"
        
        # Create output directory
        os.makedirs(output_path, exist_ok=True)
        
        # Initialize output ChromaDB using LangChain (compatible with retriever)
        # Note: We'll create it fresh each time to ensure proper embedding
        self.output_path = output_path
        self.output_vectorstore = None  # Will be created when adding documents
        self.embedding_model_initialized = False
        
        logger.info(f"Output ChromaDB will be created at: {output_path}")
    
    def read_sqlite_documents(self) -> List[Dict[str, Any]]:
        """Read documents from SQLite database"""
        documents = []
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT doc_id, title, content, doc_type, source, court, date FROM legal_documents")
            rows = cursor.fetchall()
            
            logger.info(f"Reading {len(rows)} documents from SQLite database")
            
            for row in rows:
                doc_id, title, content, doc_type, source, court, date = row
                
                # Format document text
                doc_text = f"Title: {title}\n\nContent: {content}"
                
                documents.append({
                    'id': f"sqlite_{doc_id}",
                    'text': doc_text,
                    'metadata': {
                        'doc_id': doc_id,
                        'title': title,
                        'doc_type': doc_type or 'document',
                        'source': source or 'Unknown',
                        'court': court or '',
                        'date': date or '',
                        'source_db': 'sqlite'
                    }
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error reading SQLite database: {e}")
        
        return documents
    
    def read_chromadb(self, db_path: str) -> List[Dict[str, Any]]:
        """Read all documents from a ChromaDB instance"""
        documents = []
        
        try:
            if not os.path.exists(db_path):
                logger.warning(f"ChromaDB path does not exist: {db_path}")
                return documents
            
            # Method 1: Try using ChromaDB client directly
            try:
                client = chromadb.PersistentClient(path=db_path)
                collections = client.list_collections()
                
                logger.info(f"Found {len(collections)} collections in {db_path}")
                
                for collection in collections:
                    logger.info(f"  Reading collection: {collection.name}")
                    
                    try:
                        # Get all documents - ChromaDB's get() method retrieves all if no filters
                        results = collection.get()
                        
                        if results and 'ids' in results and len(results['ids']) > 0:
                            total = len(results['ids'])
                            logger.info(f"    Found {total} documents")
                            
                            for i in range(total):
                                doc_id = results['ids'][i]
                                doc_text = results['documents'][i] if 'documents' in results and i < len(results['documents']) else ""
                                metadata = results['metadatas'][i] if 'metadatas' in results and i < len(results['metadatas']) else {}
                                
                                # Create unique ID
                                unique_id = f"{collection.name}_{doc_id}_{hash(db_path)}"
                                
                                documents.append({
                                    'id': unique_id,
                                    'text': doc_text,
                                    'metadata': metadata or {},
                                    'source_db': db_path,
                                    'source_collection': collection.name
                                })
                        else:
                            logger.info(f"    Collection {collection.name} is empty")
                                
                    except Exception as e:
                        logger.error(f"    Error reading collection {collection.name}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not read ChromaDB client at {db_path}: {e}")
                # Method 2: Try using LangChain Chroma (limited - can't get all docs easily)
                logger.info(f"Trying alternative method for {db_path}")
        
        except Exception as e:
            logger.error(f"Error reading ChromaDB at {db_path}: {e}")
        
        return documents
    
    def consolidate(self) -> Dict[str, Any]:
        """Consolidate all ChromaDB instances"""
        logger.info("=" * 60)
        logger.info("CHROMADB CONSOLIDATION")
        logger.info("=" * 60)
        
        all_documents = []
        stats = {
            'source_dbs': {},
            'total_documents': 0,
            'duplicates_removed': 0
        }
        
        # Read from all ChromaDB locations
        for db_path in self.chromadb_locations:
            logger.info(f"\nReading from: {db_path}")
            docs = self.read_chromadb(db_path)
            stats['source_dbs'][db_path] = len(docs)
            all_documents.extend(docs)
            logger.info(f"  Extracted {len(docs)} documents")
        
        # Also read from SQLite database
        logger.info(f"\nReading from SQLite database: {self.sqlite_db_path}")
        sqlite_docs = self.read_sqlite_documents()
        stats['source_dbs']['sqlite'] = len(sqlite_docs)
        all_documents.extend(sqlite_docs)
        logger.info(f"  Extracted {len(sqlite_docs)} documents from SQLite")
        
        logger.info(f"\nTotal documents collected: {len(all_documents)}")
        
        # Remove duplicates based on content hash or text
        seen_texts = set()
        unique_documents = []
        
        for doc in all_documents:
            text_hash = hash(doc['text'])
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_documents.append(doc)
            else:
                stats['duplicates_removed'] += 1
        
        logger.info(f"Unique documents after deduplication: {len(unique_documents)}")
        logger.info(f"Duplicates removed: {stats['duplicates_removed']}")
        
        # Add to output ChromaDB using LangChain
        logger.info(f"\nAdding documents to consolidated ChromaDB...")
        
        # Initialize the vectorstore (will create collection if it doesn't exist)
        if self.output_vectorstore is None:
            logger.info("Creating consolidated ChromaDB collection...")
            self.output_vectorstore = Chroma(
                collection_name="langchain",
                embedding_function=self.embedding_model,
                persist_directory=self.output_path
            )
        
        batch_size = 100
        total_added = 0
        
        for i in range(0, len(unique_documents), batch_size):
            batch = unique_documents[i:i+batch_size]
            
            texts = [doc['text'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]
            ids = [doc['id'] for doc in batch]
            
            try:
                # Use LangChain Chroma's add_texts method
                # This will automatically create embeddings using the embedding function
                new_ids = self.output_vectorstore.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                total_added += len(batch)
                logger.info(f"  Added batch {i//batch_size + 1}: {len(batch)} documents (Total: {total_added})")
            except Exception as e:
                logger.error(f"  Error adding batch {i//batch_size + 1}: {e}")
                import traceback
                traceback.print_exc()
                # Continue with next batch
                continue
        
        stats['total_documents'] = total_added
        
        logger.info(f"\nFinal consolidated database contains: {total_added} documents")
        
        # Verify the database
        logger.info("\nVerifying consolidated database...")
        try:
            # Try a test query to verify embeddings were created
            test_results = self.output_vectorstore.similarity_search_with_score("test", k=1)
            if test_results:
                logger.info(f"  Verification: Database is searchable (found {len(test_results)} test results)")
            else:
                logger.warning("  Verification: Database created but no test results found")
        except Exception as e:
            logger.warning(f"  Verification warning: {e}")
        
        return stats
    
    def test_consolidated_db(self, test_query: str = "Article 21"):
        """Test the consolidated database"""
        logger.info(f"\nTesting consolidated database with query: '{test_query}'")
        
        try:
            # Use LangChain Chroma for testing (same collection name as output)
            vectorstore = Chroma(
                collection_name="langchain",  # Same as output collection
                embedding_function=self.embedding_model,
                persist_directory=self.output_path
            )
            
            results = vectorstore.similarity_search_with_score(test_query, k=5)
            
            logger.info(f"Found {len(results)} results:")
            for i, (doc, score) in enumerate(results, 1):
                logger.info(f"  {i}. Score: {score:.4f}")
                logger.info(f"     Content: {doc.page_content[:100]}...")
                if doc.metadata:
                    logger.info(f"     Metadata: {doc.metadata}")
                    
        except Exception as e:
            logger.error(f"Error testing consolidated DB: {e}")

def main():
    """Main consolidation function"""
    
    # Create consolidator
    consolidator = ChromaDBConsolidator(output_path="./chroma_db_consolidated")
    
    # Consolidate
    stats = consolidator.consolidate()
    
    # Print summary
    print("\n" + "=" * 60)
    print("CONSOLIDATION SUMMARY")
    print("=" * 60)
    print(f"Total documents consolidated: {stats['total_documents']}")
    print(f"Duplicates removed: {stats['duplicates_removed']}")
    print(f"\nSource databases:")
    for db_path, count in stats['source_dbs'].items():
        print(f"  {db_path}: {count} documents")
    print(f"\nOutput location: ./chroma_db_consolidated")
    print("=" * 60)
    
    # Test
    consolidator.test_consolidated_db()
    
    print("\nConsolidation complete!")
    print("\nTo use this consolidated database, update retriever_agent.py:")
    print("  Change: self.chroma_db_path = './chroma_db_'")
    print("  To:     self.chroma_db_path = './chroma_db_consolidated'")
    print("\nOr update the path in Buddy/agentic_legal_rag/retriever_agent.py")

if __name__ == "__main__":
    main()
