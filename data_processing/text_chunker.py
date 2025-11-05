"""
Text chunker for legal documents with intelligent splitting strategies.
"""
import re
from typing import List, Dict, Any, Optional
from loguru import logger


class TextChunker:
    """Intelligent text chunker for legal documents."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.chunk_overlap = self.config.get("chunk_overlap", 200)
        self.min_chunk_size = self.config.get("min_chunk_size", 100)
        self.logger = logger.bind(component="TextChunker")
        
        # Legal document splitting patterns
        self.split_patterns = [
            r'\n\s*(?:Section|Art\.?|Article)\s+\d+',  # Section headers
            r'\n\s*(?:Subsection|Clause)\s+\([a-z0-9]+\)',  # Subsection headers
            r'\n\s*\(\d+\)',  # Numbered paragraphs
            r'\n\s*[A-Z][a-z]+ v\. [A-Z][a-z]+',  # Case citations
            r'\n\s*[IVX]+\.',  # Roman numerals
            r'\n\s*[a-z]\)',  # Lettered items
            r'\n\s*\d+\.',  # Numbered items
            r'\n\s*[A-Z][A-Z\s]+:',  # All caps headers
            r'\n\s*--- Page \d+ ---',  # Page breaks
            r'\n\s*CHAPTER\s+\d+',  # Chapter headers
            r'\n\s*PART\s+[IVX]+',  # Part headers
        ]
        
        # Patterns that should not be split
        self.preserve_patterns = [
            r'\([^)]*\)',  # Parentheses content
            r'"[^"]*"',  # Quoted text
            r'[A-Z][a-z]+ v\. [A-Z][a-z]+',  # Case names
            r'Section \d+[a-z]?',  # Section references
        ]
    
    async def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Chunk text using intelligent splitting strategies."""
        try:
            if not text or not text.strip():
                return []
            
            metadata = metadata or {}
            self.logger.info(f"Chunking text of length {len(text)} characters")
            
            # Clean and preprocess text
            cleaned_text = self._clean_text(text)
            
            # Try different chunking strategies
            chunks = await self._chunk_by_legal_structure(cleaned_text, metadata)
            
            if not chunks:
                # Fallback to simple chunking
                chunks = await self._chunk_by_size(cleaned_text, metadata)
            
            # Post-process chunks
            chunks = await self._post_process_chunks(chunks, metadata)
            
            self.logger.info(f"Generated {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error chunking text: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for chunking."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Normalize line breaks
        text = re.sub(r'\r\n', '\n', text)
        
        # Remove page numbers and headers
        text = re.sub(r'--- Page \d+ ---', '', text)
        
        return text.strip()
    
    async def _chunk_by_legal_structure(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text based on legal document structure."""
        chunks = []
        
        # Find all split points
        split_points = self._find_split_points(text)
        
        if not split_points:
            return []
        
        # Create chunks between split points
        start = 0
        chunk_id = 0
        
        for i, split_point in enumerate(split_points):
            end = split_point
            
            # Check if chunk is within size limits
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunk = await self._create_chunk(
                    chunk_text, 
                    start, 
                    end, 
                    chunk_id, 
                    metadata
                )
                chunks.append(chunk)
                chunk_id += 1
                
                # Set next start with overlap
                start = max(start + 1, end - self.chunk_overlap)
        
        # Handle remaining text
        if start < len(text):
            remaining_text = text[start:].strip()
            if len(remaining_text) >= self.min_chunk_size:
                chunk = await self._create_chunk(
                    remaining_text,
                    start,
                    len(text),
                    chunk_id,
                    metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    def _find_split_points(self, text: str) -> List[int]:
        """Find optimal split points in the text."""
        split_points = []
        
        for pattern in self.split_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                # Check if this is a good split point
                if self._is_good_split_point(text, match.start()):
                    split_points.append(match.start())
        
        # Sort and remove duplicates
        split_points = sorted(list(set(split_points)))
        
        # Filter split points that are too close together
        filtered_points = []
        last_point = 0
        
        for point in split_points:
            if point - last_point >= self.min_chunk_size:
                filtered_points.append(point)
                last_point = point
        
        return filtered_points
    
    def _is_good_split_point(self, text: str, position: int) -> bool:
        """Check if a position is a good split point."""
        # Don't split in the middle of preserved patterns
        for pattern in self.preserve_patterns:
            for match in re.finditer(pattern, text):
                if match.start() < position < match.end():
                    return False
        
        # Check if we're at a natural break
        if position > 0 and position < len(text):
            char_before = text[position - 1]
            char_after = text[position]
            
            # Good break points
            if char_before in '\n' and char_after.isupper():
                return True
            if char_before in '.!?' and char_after in ' \n':
                return True
        
        return False
    
    async def _chunk_by_size(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback chunking by size."""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                search_start = max(start, end - 200)
                sentence_end = self._find_sentence_end(text, search_start, end)
                if sentence_end > start:
                    end = sentence_end
            
            chunk_text = text[start:end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunk = await self._create_chunk(
                    chunk_text,
                    start,
                    end,
                    chunk_id,
                    metadata
                )
                chunks.append(chunk)
                chunk_id += 1
            
            # Move start with overlap
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def _find_sentence_end(self, text: str, start: int, end: int) -> int:
        """Find the end of a sentence within the given range."""
        # Look for sentence endings
        for i in range(end - 1, start, -1):
            if text[i] in '.!?' and i + 1 < len(text) and text[i + 1] in ' \n':
                return i + 1
        
        return end
    
    async def _create_chunk(self, 
                          content: str, 
                          start: int, 
                          end: int, 
                          chunk_id: int, 
                          metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chunk with metadata."""
        chunk = {
            "chunk_id": f"{metadata.get('source', 'unknown')}_{chunk_id}",
            "content": content,
            "start_position": start,
            "end_position": end,
            "length": len(content),
            "word_count": len(content.split()),
            "source": metadata.get("source", "unknown"),
            "doc_type": metadata.get("doc_type", "legal_document"),
            "title": metadata.get("title", ""),
            "filename": metadata.get("filename", ""),
            "page_number": self._estimate_page_number(content, metadata),
            "chunk_type": self._classify_chunk_type(content),
            "legal_entities": self._extract_legal_entities(content)
        }
        
        # Add any additional metadata
        for key, value in metadata.items():
            if key not in chunk:
                chunk[key] = value
        
        return chunk
    
    def _estimate_page_number(self, content: str, metadata: Dict[str, Any]) -> int:
        """Estimate page number based on content position."""
        # This is a simple estimation - in practice, you'd track page breaks
        start_pos = metadata.get("start_position", 0)
        estimated_page = (start_pos // 2000) + 1
        return min(estimated_page, metadata.get("page_count", 1))
    
    def _classify_chunk_type(self, content: str) -> str:
        """Classify the type of legal content in the chunk."""
        content_lower = content.lower()
        
        if re.search(r'\b(?:section|art\.?|article)\s+\d+', content_lower):
            return "section"
        elif re.search(r'\b(?:subsection|clause)\s+\([a-z0-9]+\)', content_lower):
            return "subsection"
        elif re.search(r'\b[A-Z][a-z]+ v\. [A-Z][a-z]+', content):
            return "case_law"
        elif re.search(r'\b(?:court|judge|ruling|decision)', content_lower):
            return "judgment"
        elif re.search(r'\b(?:act|statute|law|regulation)', content_lower):
            return "statute"
        else:
            return "general"
    
    def _extract_legal_entities(self, content: str) -> List[str]:
        """Extract legal entities from the chunk."""
        entities = []
        
        # Extract section references
        sections = re.findall(r'\b(?:section|art\.?|article)\s+(\d+[a-z]?)', content, re.IGNORECASE)
        entities.extend([f"Section {s}" for s in sections])
        
        # Extract case names
        cases = re.findall(r'\b([A-Z][a-z]+ v\. [A-Z][a-z]+)', content)
        entities.extend(cases)
        
        # Extract act names
        acts = re.findall(r'\b([A-Z][a-z\s]+(?:Act|Code|Regulation))\s+of\s+\d{4}', content)
        entities.extend(acts)
        
        return list(set(entities))
    
    async def _post_process_chunks(self, chunks: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Post-process chunks to ensure quality."""
        processed_chunks = []
        
        for chunk in chunks:
            # Skip chunks that are too short or empty
            if len(chunk["content"].strip()) < self.min_chunk_size:
                continue
            
            # Add chunk-level metadata
            chunk["processing_timestamp"] = metadata.get("processing_timestamp")
            chunk["chunk_index"] = len(processed_chunks)
            
            processed_chunks.append(chunk)
        
        return processed_chunks
