"""
Retriever Agent for legal document retrieval using FAISS vector store.
"""
import faiss
import numpy as np
import pickle
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from .base_agent import BaseAgent, AgentResponse
from datetime import datetime
import os


class RetrieverAgent(BaseAgent):
    """Agent responsible for retrieving relevant legal documents from vector store."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Retriever", config)
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.index_path = None
        
    async def initialize(self) -> bool:
        """Initialize the embedding model and load/create FAISS index."""
        try:
            # Initialize embedding model
            model_name = self.config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            self.logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            
            # Set up index path
            vector_db_dir = self.config.get("vector_db_dir", "vector_db")
            self.index_path = Path(vector_db_dir) / "legal_documents.index"
            
            # Load or create index
            if self.index_path.exists():
                await self._load_index()
                self.logger.info(f"Loaded existing index with {len(self.documents)} documents")
            else:
                await self._create_empty_index()
                self.logger.info("Created new empty index")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Retriever: {e}")
            return False
    
    async def process(self, input_data: Any) -> AgentResponse:
        """Retrieve relevant documents based on the query."""
        try:
            if isinstance(input_data, str):
                query = input_data
                top_k = self.config.get("top_k", 5)
            elif isinstance(input_data, dict):
                query = input_data.get("query", "")
                top_k = input_data.get("top_k", self.config.get("top_k", 5))
            else:
                raise ValueError("Input must be a string query or dict with 'query' key")
            
            if not query.strip():
                return AgentResponse(
                    success=False,
                    data=None,
                    metadata={},
                    timestamp=datetime.now(),
                    agent_name=self.name,
                    error_message="Empty query provided"
                )
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Search the index
            if self.index is None or self.index.ntotal == 0:
                return AgentResponse(
                    success=True,
                    data={"documents": [], "scores": []},
                    metadata={"total_docs": 0, "query": query},
                    timestamp=datetime.now(),
                    agent_name=self.name
                )
            
            # Perform similarity search
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            # Retrieve documents and metadata
            retrieved_docs = []
            retrieved_scores = []
            retrieved_metadata = []
            
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):  # Valid index
                    retrieved_docs.append(self.documents[idx])
                    retrieved_scores.append(float(score))
                    retrieved_metadata.append(self.metadata[idx] if idx < len(self.metadata) else {})
            
            # Filter by similarity threshold if configured
            similarity_threshold = self.config.get("similarity_threshold", 0.0)
            filtered_results = [
                (doc, score, meta) for doc, score, meta in 
                zip(retrieved_docs, retrieved_scores, retrieved_metadata)
                if score >= similarity_threshold
            ]
            
            if filtered_results:
                filtered_docs, filtered_scores, filtered_metadata = zip(*filtered_results)
            else:
                filtered_docs, filtered_scores, filtered_metadata = [], [], []
            
            result = {
                "documents": list(filtered_docs),
                "scores": list(filtered_scores),
                "metadata": list(filtered_metadata),
                "total_found": len(filtered_docs),
                "query": query
            }
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={
                    "total_docs_in_index": len(self.documents),
                    "top_k_requested": top_k,
                    "similarity_threshold": similarity_threshold,
                    "embedding_model": self.config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
                },
                timestamp=datetime.now(),
                agent_name=self.name
            )
            
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return AgentResponse(
                success=False,
                data=None,
                metadata={},
                timestamp=datetime.now(),
                agent_name=self.name,
                error_message=str(e)
            )
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add new documents to the vector store."""
        try:
            if not documents:
                return True
            
            # Extract text and metadata
            texts = []
            metadata = []
            
            for doc in documents:
                text = doc.get("content", "")
                if text.strip():
                    texts.append(text)
                    metadata.append({
                        "source": doc.get("source", "unknown"),
                        "doc_type": doc.get("doc_type", "unknown"),
                        "title": doc.get("title", ""),
                        "date": doc.get("date", ""),
                        "url": doc.get("url", ""),
                        "page_number": doc.get("page_number", 0),
                        "chunk_id": doc.get("chunk_id", "")
                    })
            
            if not texts:
                self.logger.warning("No valid documents to add")
                return True
            
            # Generate embeddings
            self.logger.info(f"Generating embeddings for {len(texts)} documents...")
            embeddings = self.embedding_model.encode(texts)
            
            # Add to existing index or create new one
            if self.index is None:
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            self.index.add(embeddings.astype('float32'))
            
            # Update document and metadata lists
            self.documents.extend(texts)
            self.metadata.extend(metadata)
            
            # Save index
            await self._save_index()
            
            self.logger.info(f"Successfully added {len(texts)} documents to index")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")
            return False
    
    async def _load_index(self) -> None:
        """Load existing FAISS index and metadata."""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load documents and metadata
            docs_path = self.index_path.with_suffix('.docs.pkl')
            meta_path = self.index_path.with_suffix('.meta.pkl')
            
            if docs_path.exists():
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
            
            if meta_path.exists():
                with open(meta_path, 'rb') as f:
                    self.metadata = pickle.load(f)
            
        except Exception as e:
            self.logger.error(f"Error loading index: {e}")
            await self._create_empty_index()
    
    async def _save_index(self) -> None:
        """Save FAISS index and metadata."""
        try:
            if self.index is not None:
                # Save FAISS index
                faiss.write_index(self.index, str(self.index_path))
                
                # Save documents and metadata
                docs_path = self.index_path.with_suffix('.docs.pkl')
                meta_path = self.index_path.with_suffix('.meta.pkl')
                
                with open(docs_path, 'wb') as f:
                    pickle.dump(self.documents, f)
                
                with open(meta_path, 'wb') as f:
                    pickle.dump(self.metadata, f)
                
        except Exception as e:
            self.logger.error(f"Error saving index: {e}")
    
    async def _create_empty_index(self) -> None:
        """Create an empty FAISS index."""
        self.index = None
        self.documents = []
        self.metadata = []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        if self.index is None:
            return {"total_documents": 0, "index_type": "None"}
        
        return {
            "total_documents": self.index.ntotal,
            "index_type": type(self.index).__name__,
            "dimension": self.index.d if hasattr(self.index, 'd') else "Unknown",
            "is_trained": self.index.is_trained if hasattr(self.index, 'is_trained') else "Unknown"
        }
    
    async def clear_index(self) -> bool:
        """Clear all documents from the index."""
        try:
            await self._create_empty_index()
            await self._save_index()
            self.logger.info("Index cleared successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing index: {e}")
            return False
