"""
Legal document parser supporting multiple formats.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import PyPDF2
import docx
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from loguru import logger


class LegalDocumentParser:
    """Parser for various legal document formats."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logger.bind(component="LegalParser")
        
        # Legal document patterns
        self.legal_patterns = {
            "section_header": r'(?i)(?:section|art\.?|article)\s+(\d+[a-z]?)',
            "subsection": r'(?i)(?:subsection|clause)\s+\(([a-z0-9]+)\)',
            "case_citation": r'(?i)([A-Za-z]+ v\. [A-Za-z]+|\d+ [A-Za-z]+ \d+)',
            "court_name": r'(?i)(supreme court|high court|district court|tribunal)',
            "date_pattern": r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
            "act_name": r'(?i)([A-Za-z\s]+(?:Act|Code|Regulation|Amendment))\s+of\s+\d{4}'
        }
    
    async def parse_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a document and extract content and metadata."""
        try:
            file_extension = file_path.suffix.lower()
            self.logger.info(f"Parsing {file_path.name} ({file_extension})")
            
            if file_extension == '.pdf':
                return await self._parse_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return await self._parse_docx(file_path)
            elif file_extension == '.txt':
                return await self._parse_txt(file_path)
            elif file_extension in ['.html', '.htm']:
                return await self._parse_html(file_path)
            elif file_extension == '.xml':
                return await self._parse_xml(file_path)
            else:
                self.logger.warning(f"Unsupported file format: {file_extension}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return None
    
    async def _parse_pdf(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse PDF documents."""
        try:
            content = ""
            metadata = {}
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata.update({
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "creator": pdf_reader.metadata.get("/Creator", ""),
                        "created_date": pdf_reader.metadata.get("/CreationDate", ""),
                        "modified_date": pdf_reader.metadata.get("/ModDate", "")
                    })
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                # Extract legal-specific information
                legal_metadata = self._extract_legal_metadata(content)
                
                return {
                    "content": content.strip(),
                    "title": metadata.get("title", file_path.stem),
                    "author": metadata.get("author", ""),
                    "created_date": metadata.get("created_date"),
                    "modified_date": metadata.get("modified_date"),
                    "page_count": len(pdf_reader.pages),
                    "language": self._detect_language(content),
                    "legal_metadata": legal_metadata
                }
                
        except Exception as e:
            self.logger.error(f"Error parsing PDF {file_path}: {e}")
            return None
    
    async def _parse_docx(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse DOCX documents."""
        try:
            doc = docx.Document(file_path)
            
            # Extract text content
            content = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content += paragraph.text + "\n"
            
            # Extract metadata
            metadata = {
                "title": doc.core_properties.title or file_path.stem,
                "author": doc.core_properties.author or "",
                "created_date": doc.core_properties.created,
                "modified_date": doc.core_properties.modified,
                "last_modified_by": doc.core_properties.last_modified_by or ""
            }
            
            # Extract legal-specific information
            legal_metadata = self._extract_legal_metadata(content)
            
            return {
                "content": content.strip(),
                "title": metadata["title"],
                "author": metadata["author"],
                "created_date": metadata["created_date"],
                "modified_date": metadata["modified_date"],
                "page_count": self._estimate_page_count(content),
                "language": self._detect_language(content),
                "legal_metadata": legal_metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing DOCX {file_path}: {e}")
            return None
    
    async def _parse_txt(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse plain text documents."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Extract legal-specific information
            legal_metadata = self._extract_legal_metadata(content)
            
            return {
                "content": content.strip(),
                "title": file_path.stem,
                "author": "",
                "created_date": None,
                "modified_date": None,
                "page_count": self._estimate_page_count(content),
                "language": self._detect_language(content),
                "legal_metadata": legal_metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing TXT {file_path}: {e}")
            return None
    
    async def _parse_html(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse HTML documents."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            content = soup.get_text(separator='\n', strip=True)
            
            # Extract metadata from HTML
            title = ""
            if soup.title:
                title = soup.title.string.strip()
            
            # Extract legal-specific information
            legal_metadata = self._extract_legal_metadata(content)
            
            return {
                "content": content.strip(),
                "title": title or file_path.stem,
                "author": "",
                "created_date": None,
                "modified_date": None,
                "page_count": self._estimate_page_count(content),
                "language": self._detect_language(content),
                "legal_metadata": legal_metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML {file_path}: {e}")
            return None
    
    async def _parse_xml(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse XML documents."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract text content
            content = ET.tostring(root, method='text', encoding='unicode')
            
            # Extract metadata from XML
            title = root.get('title', file_path.stem)
            
            # Extract legal-specific information
            legal_metadata = self._extract_legal_metadata(content)
            
            return {
                "content": content.strip(),
                "title": title,
                "author": "",
                "created_date": None,
                "modified_date": None,
                "page_count": self._estimate_page_count(content),
                "language": self._detect_language(content),
                "legal_metadata": legal_metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing XML {file_path}: {e}")
            return None
    
    def _extract_legal_metadata(self, content: str) -> Dict[str, Any]:
        """Extract legal-specific metadata from content."""
        legal_metadata = {}
        
        # Extract sections
        sections = re.findall(self.legal_patterns["section_header"], content)
        if sections:
            legal_metadata["sections"] = list(set(sections))
        
        # Extract subsections
        subsections = re.findall(self.legal_patterns["subsection"], content)
        if subsections:
            legal_metadata["subsections"] = list(set(subsections))
        
        # Extract case citations
        case_citations = re.findall(self.legal_patterns["case_citation"], content)
        if case_citations:
            legal_metadata["case_citations"] = list(set(case_citations))
        
        # Extract court names
        courts = re.findall(self.legal_patterns["court_name"], content)
        if courts:
            legal_metadata["courts"] = list(set(courts))
        
        # Extract dates
        dates = re.findall(self.legal_patterns["date_pattern"], content)
        if dates:
            legal_metadata["dates"] = list(set(dates))
        
        # Extract act names
        acts = re.findall(self.legal_patterns["act_name"], content)
        if acts:
            legal_metadata["acts"] = list(set(acts))
        
        return legal_metadata
    
    def _detect_language(self, content: str) -> str:
        """Simple language detection based on common words."""
        # This is a simple implementation - in production, use a proper language detection library
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        hindi_words = ['और', 'या', 'लेकिन', 'में', 'पर', 'को', 'के', 'लिए', 'साथ', 'द्वारा']
        
        content_lower = content.lower()
        english_count = sum(1 for word in english_words if word in content_lower)
        hindi_count = sum(1 for word in hindi_words if word in content_lower)
        
        if hindi_count > english_count:
            return "hi"
        else:
            return "en"
    
    def _estimate_page_count(self, content: str) -> int:
        """Estimate page count based on content length."""
        # Rough estimate: 2000 characters per page
        return max(1, len(content) // 2000)
