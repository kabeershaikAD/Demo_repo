#!/usr/bin/env python3
"""
Legal Data Preprocessing Module
Handles cleaning, chunking, and text normalization
"""

import os
import sys
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from dataclasses import dataclass
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import spacy
from bs4 import BeautifulSoup

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessedDocument:
    """Processed document structure"""
    doc_id: str
    title: str
    content: str
    chunks: List[Dict[str, Any]]
    source_url: str
    source_type: str
    section_article: Optional[str] = None
    date: Optional[str] = None
    doc_type: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TextCleaner:
    """Handles text cleaning and normalization"""
    
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            logger.warning("NLTK data download failed - using basic tokenization")
        
        # Initialize spaCy model (optional)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found - using basic tokenization")
            self.nlp = None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = self._remove_html_tags(text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common legal headers/footers
        text = self._remove_headers_footers(text)
        
        # Normalize legal citations
        text = self._normalize_citations(text)
        
        # Remove page numbers and line numbers
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'^\d+\s*', '', text, flags=re.MULTILINE)
        
        # Clean up punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\']', ' ', text)
        
        return text.strip()
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags"""
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()
    
    def _remove_headers_footers(self, text: str) -> str:
        """Remove common legal document headers and footers"""
        patterns = [
            r'©.*?Government of India.*?\n',
            r'Page \d+ of \d+.*?\n',
            r'IN THE SUPREME COURT OF INDIA.*?\n',
            r'IN THE HIGH COURT OF.*?\n',
            r'BEFORE.*?JUDGE.*?\n',
            r'CASE NO\.?\s*\d+.*?\n',
            r'CRIMINAL APPEAL NO\.?\s*\d+.*?\n',
            r'CIVIL APPEAL NO\.?\s*\d+.*?\n',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        return text
    
    def _normalize_citations(self, text: str) -> str:
        """Normalize legal citations"""
        # Normalize case citations
        text = re.sub(r'(\d{4})\s*SCC\s*(\d+)', r'\1 SCC \2', text)
        text = re.sub(r'(\d{4})\s*AIR\s*(\d+)', r'\1 AIR \2', text)
        text = re.sub(r'(\d{4})\s*SC\s*(\d+)', r'\1 SC \2', text)
        
        # Normalize section references
        text = re.sub(r'Section\s+(\d+)', r'Section \1', text, flags=re.IGNORECASE)
        text = re.sub(r'Article\s+(\d+)', r'Article \1', text, flags=re.IGNORECASE)
        
        return text

class TextChunker:
    """Handles text chunking with overlap"""
    
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.cleaner = TextCleaner()
    
    def chunk_text(self, text: str, title: str = "") -> List[Dict[str, Any]]:
        """Chunk text into overlapping segments"""
        if not text:
            return []
        
        # Clean text first
        clean_text = self.cleaner.clean_text(text)
        
        # Split into sentences with fallback
        try:
            sentences = sent_tokenize(clean_text)
        except:
            # Fallback to simple sentence splitting
            sentences = self._simple_sentence_split(clean_text)
        
        chunks = []
        current_chunk = ""
        current_length = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            # If adding this sentence would exceed chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk.strip(), 
                    title, 
                    chunk_id,
                    len(chunks)
                ))
                chunk_id += 1
                
                # Start new chunk with overlap
                current_chunk = self._get_overlap_text(current_chunk, self.overlap) + " " + sentence
                current_length = len(current_chunk.split())
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(self._create_chunk(
                current_chunk.strip(), 
                title, 
                chunk_id,
                len(chunks)
            ))
        
        return chunks
    
    def _create_chunk(self, text: str, title: str, chunk_id: int, total_chunks: int) -> Dict[str, Any]:
        """Create a chunk dictionary"""
        return {
            'chunk_id': f"{title}_{chunk_id}" if title else f"chunk_{chunk_id}",
            'text': text,
            'title': title,
            'chunk_index': chunk_id,
            'total_chunks': total_chunks + 1,
            'word_count': len(text.split()),
            'char_count': len(text)
        }
    
    def _get_overlap_text(self, text: str, overlap_words: int) -> str:
        """Get overlap text from the end of current chunk"""
        words = text.split()
        if len(words) <= overlap_words:
            return text
        return " ".join(words[-overlap_words:])
    
    def _simple_sentence_split(self, text: str) -> List[str]:
        """Simple sentence splitting fallback when NLTK fails"""
        # Split on common sentence endings
        import re
        sentences = re.split(r'[.!?]+', text)
        # Clean up and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

class LegalDocumentProcessor:
    """Main document processor"""
    
    def __init__(self, chunk_size: int = 800, overlap: int = 100):
        self.cleaner = TextCleaner()
        self.chunker = TextChunker(chunk_size, overlap)
    
    def process_document(self, doc_data: Dict[str, Any]) -> ProcessedDocument:
        """Process a single document"""
        try:
            # Clean content
            clean_content = self.cleaner.clean_text(doc_data.get('content', ''))
            
            if len(clean_content) < 50:  # Skip very short documents
                return None
            
            # Generate document ID
            doc_id = self._generate_doc_id(doc_data)
            
            # Chunk the content
            chunks = self.chunker.chunk_text(clean_content, doc_data.get('title', ''))
            
            # Create processed document
            processed_doc = ProcessedDocument(
                doc_id=doc_id,
                title=doc_data.get('title', 'Unknown Document'),
                content=clean_content,
                chunks=chunks,
                source_url=doc_data.get('source_url', ''),
                source_type=doc_data.get('source_type', 'unknown'),
                section_article=doc_data.get('section_article'),
                date=doc_data.get('date'),
                doc_type=doc_data.get('doc_type', 'document'),
                metadata=doc_data.get('metadata', {})
            )
            
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return None
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[ProcessedDocument]:
        """Process multiple documents"""
        processed_docs = []
        
        for i, doc_data in enumerate(documents):
            try:
                processed_doc = self.process_document(doc_data)
                if processed_doc:
                    processed_docs.append(processed_doc)
                    
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(documents)} documents")
                    
            except Exception as e:
                logger.error(f"Error processing document {i}: {e}")
                continue
        
        return processed_docs
    
    def _generate_doc_id(self, doc_data: Dict[str, Any]) -> str:
        """Generate unique document ID"""
        title = doc_data.get('title', 'unknown')
        source_type = doc_data.get('source_type', 'unknown')
        
        # Create a simple hash-based ID
        import hashlib
        content_hash = hashlib.md5(
            f"{title}_{source_type}_{doc_data.get('source_url', '')}".encode()
        ).hexdigest()[:8]
        
        return f"{source_type}_{content_hash}"
    
    def save_processed_data(self, processed_docs: List[ProcessedDocument], output_file: str = "data/processed_legal_data.json"):
        """Save processed data to JSON file"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            data = []
            for doc in processed_docs:
                data.append({
                    'doc_id': doc.doc_id,
                    'title': doc.title,
                    'content': doc.content,
                    'chunks': doc.chunks,
                    'source_url': doc.source_url,
                    'source_type': doc.source_type,
                    'section_article': doc.section_article,
                    'date': doc.date,
                    'doc_type': doc.doc_type,
                    'metadata': doc.metadata
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(processed_docs)} processed documents to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving processed data: {e}")

def main():
    """Main function for testing preprocessor"""
    # Load scraped data
    with open("data/scraped_legal_data.json", 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    # Process documents
    processor = LegalDocumentProcessor(chunk_size=800, overlap=100)
    processed_docs = processor.process_documents(scraped_data)
    
    print(f"Processed {len(processed_docs)} documents")
    
    # Save processed data
    processor.save_processed_data(processed_docs)
    
    # Print sample
    for i, doc in enumerate(processed_docs[:2]):
        print(f"\n--- Processed Document {i+1} ---")
        print(f"Title: {doc.title}")
        print(f"Chunks: {len(doc.chunks)}")
        print(f"First chunk: {doc.chunks[0]['text'][:200]}...")

if __name__ == "__main__":
    main()
