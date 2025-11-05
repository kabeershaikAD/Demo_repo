#!/usr/bin/env python3
"""
Legal Data Embedding Module
Generates embeddings using sentence-transformers
"""

import os
import sys
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingData:
    """Structure for embedding data"""
    doc_id: str
    chunk_id: str
    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    similarity_scores: Optional[Dict[str, float]] = None

class LegalEmbedder:
    """Handles embedding generation for legal documents"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.model.to(self.device)
            logger.info(f"Model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            # Generate embeddings in batches
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_tensor=True,
                    show_progress_bar=True
                )
                
                # Convert to numpy and add to results
                all_embeddings.append(batch_embeddings.cpu().numpy())
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            # Concatenate all embeddings
            embeddings = np.vstack(all_embeddings)
            logger.info(f"Generated embeddings shape: {embeddings.shape}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        try:
            embedding = self.model.encode([text], convert_to_tensor=True)
            return embedding.cpu().numpy()[0]
        except Exception as e:
            logger.error(f"Error generating single embedding: {e}")
            raise

class EmbeddingProcessor:
    """Main embedding processor"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = LegalEmbedder(model_name)
    
    def process_documents(self, processed_docs) -> List[EmbeddingData]:
        """Process documents and generate embeddings"""
        embedding_data = []
        
        for doc in processed_docs:
            try:
                doc_id = doc.doc_id
                title = doc.title
                chunks = doc.chunks
                
                logger.info(f"Processing document: {title}")
                
                # Generate embeddings for each chunk
                for chunk in chunks:
                    chunk_id = chunk['chunk_id']
                    text = chunk['text']
                    
                    # Create combined text for embedding
                    combined_text = f"Title: {title}\n\nContent: {text}"
                    
                    # Generate embedding
                    embedding = self.embedder.generate_single_embedding(combined_text)
                    
                    # Create metadata
                    metadata = {
                        'doc_id': doc_id,
                        'chunk_id': chunk_id,
                        'title': title,
                        'source_url': getattr(doc, 'source_url', ''),
                        'source_type': getattr(doc, 'source_type', 'unknown'),
                        'section_article': getattr(doc, 'section_article', ''),
                        'date': getattr(doc, 'date', ''),
                        'doc_type': getattr(doc, 'doc_type', 'document'),
                        'chunk_index': chunk.get('chunk_index', 0),
                        'total_chunks': chunk.get('total_chunks', 1),
                        'word_count': chunk.get('word_count', 0),
                        'char_count': chunk.get('char_count', 0),
                        'model_name': self.embedder.model_name,
                        **getattr(doc, 'metadata', {})
                    }
                    
                    # Create embedding data
                    embedding_item = EmbeddingData(
                        doc_id=doc_id,
                        chunk_id=chunk_id,
                        text=text,
                        embedding=embedding,
                        metadata=metadata
                    )
                    
                    embedding_data.append(embedding_item)
                
            except Exception as e:
                logger.error(f"Error processing document {getattr(doc, 'title', 'Unknown')}: {e}")
                continue
        
        return embedding_data
    
    def calculate_similarities(self, embedding_data: List[EmbeddingData]) -> List[EmbeddingData]:
        """Calculate similarity scores between embeddings"""
        try:
            logger.info("Calculating similarity scores...")
            
            # Extract embeddings
            embeddings = np.array([item.embedding for item in embedding_data])
            
            # Calculate cosine similarity matrix
            similarity_matrix = cosine_similarity(embeddings)
            
            # Add similarity scores to each item
            for i, item in enumerate(embedding_data):
                # Get similarities to other documents (excluding self)
                similarities = {}
                for j, other_item in enumerate(embedding_data):
                    if i != j:
                        similarities[other_item.doc_id] = float(similarity_matrix[i][j])
                
                # Sort by similarity and keep top 10
                top_similarities = dict(sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:10])
                item.similarity_scores = top_similarities
            
            logger.info("Similarity scores calculated")
            return embedding_data
            
        except Exception as e:
            logger.error(f"Error calculating similarities: {e}")
            return embedding_data
    
    def save_embeddings(self, embedding_data: List[EmbeddingData], output_file: str = "data/legal_embeddings.json"):
        """Save embeddings to file"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Convert embeddings to serializable format
            data = []
            for item in embedding_data:
                data.append({
                    'doc_id': item.doc_id,
                    'chunk_id': item.chunk_id,
                    'text': item.text,
                    'embedding': item.embedding.tolist(),
                    'metadata': item.metadata,
                    'similarity_scores': item.similarity_scores
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(embedding_data)} embeddings to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
    
    def load_embeddings(self, input_file: str) -> List[EmbeddingData]:
        """Load embeddings from file"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            embedding_data = []
            for item in data:
                embedding_item = EmbeddingData(
                    doc_id=item['doc_id'],
                    chunk_id=item['chunk_id'],
                    text=item['text'],
                    embedding=np.array(item['embedding']),
                    metadata=item['metadata'],
                    similarity_scores=item.get('similarity_scores')
                )
                embedding_data.append(embedding_item)
            
            logger.info(f"Loaded {len(embedding_data)} embeddings from {input_file}")
            return embedding_data
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return []

def main():
    """Main function for testing embedder"""
    # Load processed data
    with open("data/processed_legal_data.json", 'r', encoding='utf-8') as f:
        processed_data = json.load(f)
    
    # Process embeddings
    processor = EmbeddingProcessor()
    embedding_data = processor.process_documents(processed_data)
    
    # Calculate similarities
    embedding_data = processor.calculate_similarities(embedding_data)
    
    # Save embeddings
    processor.save_embeddings(embedding_data)
    
    print(f"Generated embeddings for {len(embedding_data)} chunks")
    
    # Print sample
    for i, item in enumerate(embedding_data[:2]):
        print(f"\n--- Embedding {i+1} ---")
        print(f"Doc ID: {item.doc_id}")
        print(f"Chunk ID: {item.chunk_id}")
        print(f"Text: {item.text[:100]}...")
        print(f"Embedding shape: {item.embedding.shape}")

if __name__ == "__main__":
    main()
