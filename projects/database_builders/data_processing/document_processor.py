"""
Document processor for legal documents with support for multiple formats.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from loguru import logger
import asyncio

from .legal_parser import LegalDocumentParser
from .text_chunker import TextChunker
from config import settings


class DocumentProcessor:
    """Main document processor for legal documents."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.parser = LegalDocumentParser(config)
        self.chunker = TextChunker(config)
        self.logger = logger.bind(component="DocumentProcessor")
        
    async def process_documents(self, 
                              input_path: Union[str, Path], 
                              output_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
        """Process documents from input path and return processed chunks."""
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input path does not exist: {input_path}")
            
            self.logger.info(f"Processing documents from: {input_path}")
            
            # Find all supported documents
            documents = await self._find_documents(input_path)
            self.logger.info(f"Found {len(documents)} documents to process")
            
            # Process each document
            processed_chunks = []
            for doc_path in documents:
                try:
                    chunks = await self._process_single_document(doc_path)
                    processed_chunks.extend(chunks)
                    self.logger.info(f"Processed {len(chunks)} chunks from {doc_path.name}")
                except Exception as e:
                    self.logger.error(f"Failed to process {doc_path}: {e}")
                    continue
            
            # Save processed chunks if output path provided
            if output_path:
                await self._save_processed_chunks(processed_chunks, output_path)
            
            self.logger.info(f"Processing complete. Generated {len(processed_chunks)} chunks")
            return processed_chunks
            
        except Exception as e:
            self.logger.error(f"Error processing documents: {e}")
            raise
    
    async def _find_documents(self, input_path: Path) -> List[Path]:
        """Find all supported document files in the input path."""
        supported_extensions = {'.pdf', '.txt', '.docx', '.doc', '.html', '.xml'}
        documents = []
        
        if input_path.is_file():
            if input_path.suffix.lower() in supported_extensions:
                documents.append(input_path)
        else:
            # Recursively find documents
            for ext in supported_extensions:
                documents.extend(input_path.rglob(f"*{ext}"))
        
        return documents
    
    async def _process_single_document(self, doc_path: Path) -> List[Dict[str, Any]]:
        """Process a single document and return chunks."""
        try:
            # Parse the document
            parsed_content = await self.parser.parse_document(doc_path)
            
            if not parsed_content:
                self.logger.warning(f"No content extracted from {doc_path}")
                return []
            
            # Extract metadata
            metadata = self._extract_metadata(doc_path, parsed_content)
            
            # Chunk the content
            chunks = await self.chunker.chunk_text(
                parsed_content["content"],
                metadata=metadata
            )
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error processing {doc_path}: {e}")
            return []
    
    def _extract_metadata(self, doc_path: Path, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from document path and content."""
        metadata = {
            "source": str(doc_path),
            "filename": doc_path.name,
            "file_extension": doc_path.suffix.lower(),
            "file_size": doc_path.stat().st_size,
            "title": parsed_content.get("title", doc_path.stem),
            "doc_type": self._classify_document_type(parsed_content),
            "language": parsed_content.get("language", "en"),
            "created_date": parsed_content.get("created_date"),
            "modified_date": parsed_content.get("modified_date"),
            "author": parsed_content.get("author"),
            "page_count": parsed_content.get("page_count", 0)
        }
        
        # Add legal-specific metadata
        if "legal_metadata" in parsed_content:
            metadata.update(parsed_content["legal_metadata"])
        
        return metadata
    
    def _classify_document_type(self, parsed_content: Dict[str, Any]) -> str:
        """Classify the type of legal document."""
        content = parsed_content.get("content", "").lower()
        title = parsed_content.get("title", "").lower()
        
        # Check for specific legal document types
        if any(term in content for term in ["section", "article", "clause", "subsection"]):
            if any(term in content for term in ["act", "statute", "law"]):
                return "statute"
            else:
                return "regulation"
        
        if any(term in content for term in ["judgment", "ruling", "decision", "court"]):
            return "judgment"
        
        if any(term in content for term in ["amendment", "amended"]):
            return "amendment"
        
        if any(term in content for term in ["precedent", "case law", "legal precedent"]):
            return "precedent"
        
        return "legal_document"
    
    async def _save_processed_chunks(self, chunks: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
        """Save processed chunks to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Saved {len(chunks)} chunks to {output_path}")
    
    async def process_legal_corpus(self, corpus_path: Union[str, Path]) -> Dict[str, Any]:
        """Process an entire legal corpus and return statistics."""
        try:
            corpus_path = Path(corpus_path)
            self.logger.info(f"Processing legal corpus: {corpus_path}")
            
            # Process all documents
            all_chunks = await self.process_documents(corpus_path)
            
            # Calculate statistics
            stats = self._calculate_corpus_statistics(all_chunks)
            
            self.logger.info(f"Corpus processing complete. {stats['total_chunks']} chunks from {stats['total_documents']} documents")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error processing corpus: {e}")
            raise
    
    def _calculate_corpus_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for the processed corpus."""
        if not chunks:
            return {
                "total_chunks": 0,
                "total_documents": 0,
                "document_types": {},
                "total_characters": 0,
                "average_chunk_size": 0
            }
        
        # Count documents and types
        documents = set()
        doc_types = {}
        total_chars = 0
        
        for chunk in chunks:
            source = chunk.get("source", "unknown")
            documents.add(source)
            
            doc_type = chunk.get("doc_type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            content = chunk.get("content", "")
            total_chars += len(content)
        
        return {
            "total_chunks": len(chunks),
            "total_documents": len(documents),
            "document_types": doc_types,
            "total_characters": total_chars,
            "average_chunk_size": total_chars / len(chunks) if chunks else 0,
            "chunk_size_distribution": self._calculate_chunk_size_distribution(chunks)
        }
    
    def _calculate_chunk_size_distribution(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of chunk sizes."""
        size_ranges = {
            "small (< 500 chars)": 0,
            "medium (500-1000 chars)": 0,
            "large (1000-2000 chars)": 0,
            "very large (> 2000 chars)": 0
        }
        
        for chunk in chunks:
            content = chunk.get("content", "")
            length = len(content)
            
            if length < 500:
                size_ranges["small (< 500 chars)"] += 1
            elif length < 1000:
                size_ranges["medium (500-1000 chars)"] += 1
            elif length < 2000:
                size_ranges["large (1000-2000 chars)"] += 1
            else:
                size_ranges["very large (> 2000 chars)"] += 1
        
        return size_ranges
