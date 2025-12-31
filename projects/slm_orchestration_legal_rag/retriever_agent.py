"""
Retriever Agent Module for Agentic Legal RAG
Handles document retrieval with cross-linking between statutes and judgments
Uses existing ChromaDB from Indian Law Voicebot
"""

import logging
import json
import re
import time
import os
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer, util

from config import config
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrievedDocument:
    """Retrieved document with metadata"""
    doc_id: str
    content: str
    title: str
    doc_type: str
    source: str
    similarity_score: float
    court: Optional[str] = None
    date: Optional[str] = None
    citations: List[str] = None
    section: Optional[str] = None
    act: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.citations is None:
            self.citations = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CrossLink:
    """Cross-link between statutes and judgments"""
    statute_doc_id: str
    judgment_doc_id: str
    link_type: str  # 'cites', 'references', 'amends', 'interprets'
    confidence: float
    context: str

@dataclass
class RetrievalResult:
    """Result of document retrieval"""
    statutes: List[RetrievedDocument]
    judgments: List[RetrievedDocument]
    cross_links: List[CrossLink]
    total_retrieved: int
    avg_similarity: float
    retrieval_time: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class CitationExtractor:
    """Extracts legal citations from text"""
    
    def __init__(self):
        # Common Indian legal citation patterns
        self.citation_patterns = [
            # Section citations: "Section 302 IPC", "S. 498A CrPC"
            r'(?:Section|Sec\.|S\.)\s*(\d+[A-Za-z]*)\s*(?:of\s+the\s+)?([A-Z]+)',
            # Article citations: "Article 21", "Art. 14"
            r'(?:Article|Art\.)\s*(\d+[A-Za-z]*)',
            # Case citations: "AIR 2023 SC 123", "(2023) 1 SCC 1"
            r'(?:AIR|SCC|Bom|Del|Mad|Cal|Guj|Ker|Punj|Raj|Ori|Pat|All|MP|HP|J&K|Chh|Jhark|Uttarakhand|Tripura|Mizoram|Manipur|Meghalaya|Nagaland|Arunachal|Sikkim|Goa|Lakshadweep|Andaman|Daman|Diu|Puducherry|Chandigarh|Delhi)\s*\d{4}\s*(?:SC|HC|Bom|Del|Mad|Cal|Guj|Ker|Punj|Raj|Ori|Pat|All|MP|HP|J&K|Chh|Jhark|Uttarakhand|Tripura|Mizoram|Manipur|Meghalaya|Nagaland|Arunachal|Sikkim|Goa|Lakshadweep|Andaman|Daman|Diu|Puducherry|Chandigarh|Delhi)\s*\d+',
            # Judgment citations: "2023 SCC Online SC 123"
            r'\d{4}\s*SCC\s*Online\s*(?:SC|HC|Bom|Del|Mad|Cal|Guj|Ker|Punj|Raj|Ori|Pat|All|MP|HP|J&K|Chh|Jhark|Uttarakhand|Tripura|Mizoram|Manipur|Meghalaya|Nagaland|Arunachal|Sikkim|Goa|Lakshadweep|Andaman|Daman|Diu|Puducherry|Chandigarh|Delhi)\s*\d+'
        ]
    
    def extract_citations(self, text: str) -> List[str]:
        """Extract all legal citations from text"""
        citations = []
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    citations.append(' '.join(match))
                else:
                    citations.append(match)
        return list(set(citations))  # Remove duplicates

class CrossLinker:
    """Finds cross-links between statutes and judgments"""
    
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
        self.citation_extractor = CitationExtractor()
    
    def find_cross_links(self, statutes: List[RetrievedDocument], judgments: List[RetrievedDocument]) -> List[CrossLink]:
        """Find cross-links between statutes and judgments"""
        cross_links = []
        
        for judgment in judgments:
            judgment_citations = self.citation_extractor.extract_citations(judgment.content)
            
            for statute in statutes:
                # Check if judgment cites this statute
                statute_citations = self.citation_extractor.extract_citations(statute.content)
                
                # Find common citations
                common_citations = set(judgment_citations) & set(statute_citations)
                
                if common_citations:
                    # Calculate confidence based on citation overlap
                    confidence = len(common_citations) / max(len(judgment_citations), 1)
                    
                    cross_link = CrossLink(
                        statute_doc_id=statute.doc_id,
                        judgment_doc_id=judgment.doc_id,
                        link_type='cites',
                        confidence=confidence,
                        context=f"Common citations: {', '.join(common_citations)}"
                    )
                    cross_links.append(cross_link)
        
        return cross_links

class RetrieverAgent:
    """Agent responsible for document retrieval and cross-linking"""
    
    def __init__(self):
        # Use consolidated ChromaDB with all documents from multiple sources
        # This contains 21,444+ documents from all ChromaDB instances and SQLite
        # Try consolidated path first, fallback to original if not found
        
        # Determine the correct path based on current working directory
        # Get the project root (where consolidate_chromadb.py was run)
        current_dir = os.getcwd()
        self.chroma_db_path = None
        
        # Try to find project root by looking for consolidate script or chroma_db_consolidated
        project_root = None
        test_paths = [
            current_dir,  # Current directory
            os.path.join(current_dir, "..", ".."),  # Two levels up
            os.path.join(current_dir, ".."),  # One level up
        ]
        
        for test_root in test_paths:
            consolidated_path = os.path.join(test_root, "chroma_db_consolidated")
            if os.path.exists(consolidated_path):
                project_root = test_root
                self.chroma_db_path = os.path.abspath(consolidated_path)
                logger.info(f"Found consolidated ChromaDB at: {self.chroma_db_path}")
                break
        
        # Fallback to original if consolidated not found
        if self.chroma_db_path is None:
            # Try original paths
            original_paths = [
                "./chroma_db_",
                "../../chroma_db_",
                "../chroma_db_"
            ]
            for path in original_paths:
                if os.path.exists(path):
                    self.chroma_db_path = path
                    break
            else:
                self.chroma_db_path = "./chroma_db_"
            logger.warning(f"Consolidated ChromaDB not found, using: {self.chroma_db_path}")
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=config.api.OPENAI_API_KEY
        )
        
        # Initialize ChromaDB connection
        try:
            # Connect to the consolidated langchain collection
            self.vector_db = Chroma(
                collection_name="langchain",
                embedding_function=self.embedding_model,
                persist_directory=self.chroma_db_path
            )
            if "consolidated" in self.chroma_db_path:
                logger.info(f"Successfully connected to consolidated ChromaDB at {self.chroma_db_path}")
                logger.info("Consolidated database contains 21,444+ documents from all sources")
            else:
                logger.info(f"Connected to ChromaDB at {self.chroma_db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to consolidated ChromaDB: {e}")
            # Fallback: try the original path
            try:
                self.chroma_db_path = "./chroma_db_"
                self.vector_db = Chroma(
                    collection_name="langchain",
                    embedding_function=self.embedding_model,
                    persist_directory=self.chroma_db_path
                )
                logger.warning("Using fallback ChromaDB path")
            except Exception as e2:
                logger.error(f"Failed to connect to fallback ChromaDB: {e2}")
                self.vector_db = None
        
        self.cross_linker = CrossLinker()
        self.citation_extractor = CitationExtractor()
        
        # Performance metrics
        self.retrieval_metrics = {
            'total_queries': 0,
            'successful_retrievals': 0,
            'failed_retrievals': 0,
            'avg_retrieval_time': 0.0,
            'cross_links_found': 0
        }
        
        logger.info("RetrieverAgent initialized with existing ChromaDB")
    
    def retrieve(self, query: str, k: int = None, filters: Dict[str, Any] = None) -> RetrievalResult:
        """
        Retrieve documents for a query using existing ChromaDB
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            filters: Optional filters to apply
            
        Returns:
            RetrievalResult: Retrieved documents with cross-links
        """
        start_time = time.time()
        k = k or config.retrieval.RETRIEVAL_K
        
        if self.vector_db is None:
            logger.error("ChromaDB not available - vector_db is None")
            logger.error(f"ChromaDB path: {self.chroma_db_path}")
            return RetrievalResult(
                statutes=[],
                judgments=[],
                cross_links=[],
                total_retrieved=0,
                avg_similarity=0.0,
                retrieval_time=time.time() - start_time
            )
        
        try:
            # Search in the existing vector database
            logger.debug(f"Searching for query: '{query}' with k={k}")
            search_results = self.vector_db.similarity_search_with_score(query, k=k)
            
            logger.debug(f"Search returned {len(search_results)} results")
            
            if not search_results:
                logger.warning(f"No documents found for query: '{query}'")
                logger.warning(f"This might indicate:")
                logger.warning(f"  1. Database is empty or not properly indexed")
                logger.warning(f"  2. Embeddings were not created during consolidation")
                logger.warning(f"  3. Query doesn't match any documents")
                logger.warning(f"  4. Collection name mismatch")
            
            # Convert to RetrievedDocument objects
            retrieved_docs = []
            for doc, score in search_results:
                # Determine document type based on metadata or content
                doc_type = self._classify_document_type(doc)
                
                retrieved_doc = RetrievedDocument(
                    doc_id=doc.metadata.get('id', f"doc_{len(retrieved_docs)}"),
                    content=doc.page_content,
                    title=doc.metadata.get('title', 'Untitled'),
                    doc_type=doc_type,
                    source=doc.metadata.get('source', 'Unknown'),
                    similarity_score=1.0 - score,  # Convert distance to similarity
                    court=doc.metadata.get('court'),
                    date=doc.metadata.get('date'),
                    section=doc.metadata.get('section'),
                    act=doc.metadata.get('act'),
                    metadata=doc.metadata
                )
                
                # Extract citations
                retrieved_doc.citations = self.citation_extractor.extract_citations(doc.page_content)
                retrieved_docs.append(retrieved_doc)
            
            # Separate statutes and judgments
            statutes = [doc for doc in retrieved_docs if doc.doc_type == 'statute']
            judgments = [doc for doc in retrieved_docs if doc.doc_type == 'judgment']
            
            # Apply filters if provided
            if filters:
                statutes = self._apply_filters(statutes, filters)
                judgments = self._apply_filters(judgments, filters)
            
            # Find cross-links
            cross_links = self.cross_linker.find_cross_links(statutes, judgments)
            
            # Calculate metrics
            all_docs = statutes + judgments
            total_retrieved = len(all_docs)
            avg_similarity = (
                sum(doc.similarity_score for doc in all_docs) / total_retrieved
                if total_retrieved > 0 else 0.0
            )
            
            retrieval_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(True, retrieval_time, len(cross_links))
            
            logger.info(f"Retrieved {total_retrieved} documents in {retrieval_time:.2f}s")
            
            return RetrievalResult(
                statutes=statutes,
                judgments=judgments,
                cross_links=cross_links,
                total_retrieved=total_retrieved,
                avg_similarity=avg_similarity,
                retrieval_time=retrieval_time,
                metadata={
                    'query': query,
                    'filters_applied': filters is not None,
                    'cross_links_count': len(cross_links)
                }
            )
            
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            retrieval_time = time.time() - start_time
            self._update_metrics(False, retrieval_time, 0)
            
            return RetrievalResult(
                statutes=[],
                judgments=[],
                cross_links=[],
                total_retrieved=0,
                avg_similarity=0.0,
                retrieval_time=retrieval_time,
                metadata={'error': str(e)}
            )
    
    def _classify_document_type(self, doc) -> str:
        """Classify document as statute or judgment based on content and metadata"""
        content = doc.page_content.lower()
        metadata = doc.metadata
        
        # Check metadata first
        if 'type' in metadata:
            return metadata['type']
        
        # Check for judgment indicators
        judgment_indicators = [
            'judgment', 'case', 'court', 'petitioner', 'respondent',
            'appeal', 'writ', 'petition', 'order', 'decree'
        ]
        
        # Check for statute indicators
        statute_indicators = [
            'section', 'act', 'rule', 'regulation', 'provision',
            'clause', 'sub-section', 'article', 'schedule'
        ]
        
        judgment_score = sum(1 for indicator in judgment_indicators if indicator in content)
        statute_score = sum(1 for indicator in statute_indicators if indicator in content)
        
        if judgment_score > statute_score:
            return 'judgment'
        elif statute_score > judgment_score:
            return 'statute'
        else:
            # Default based on common patterns
            if any(word in content for word in ['court', 'case', 'judgment']):
                return 'judgment'
            else:
                return 'statute'
    
    def _apply_filters(self, documents: List[RetrievedDocument], filters: Dict[str, Any]) -> List[RetrievedDocument]:
        """Apply filters to retrieved documents"""
        filtered_docs = documents
        
        if 'doc_type' in filters:
            filtered_docs = [doc for doc in filtered_docs if doc.doc_type == filters['doc_type']]
        
        if 'min_similarity' in filters:
            filtered_docs = [doc for doc in filtered_docs if doc.similarity_score >= filters['min_similarity']]
        
        if 'court' in filters:
            filtered_docs = [doc for doc in filtered_docs if doc.court and filters['court'].lower() in doc.court.lower()]
        
        if 'date_range' in filters:
            # Simple date filtering (can be enhanced)
            start_date = filters['date_range'].get('start')
            end_date = filters['date_range'].get('end')
            if start_date or end_date:
                filtered_docs = [doc for doc in filtered_docs if self._is_date_in_range(doc.date, start_date, end_date)]
        
        return filtered_docs
    
    def _is_date_in_range(self, date_str: str, start_date: str, end_date: str) -> bool:
        """Check if date is within range (simplified implementation)"""
        if not date_str:
            return True  # Include documents without dates
        
        try:
            # Simple year extraction and comparison
            year = int(date_str.split('-')[0])
            if start_date:
                start_year = int(start_date.split('-')[0])
                if year < start_year:
                    return False
            if end_date:
                end_year = int(end_date.split('-')[0])
                if year > end_year:
                    return False
            return True
        except:
            return True  # Include if date parsing fails
    
    def _update_metrics(self, success: bool, retrieval_time: float, cross_links_count: int):
        """Update performance metrics"""
        self.retrieval_metrics['total_queries'] += 1
        if success:
            self.retrieval_metrics['successful_retrievals'] += 1
        else:
            self.retrieval_metrics['failed_retrievals'] += 1
        
        # Update average retrieval time
        total_queries = self.retrieval_metrics['total_queries']
        current_avg = self.retrieval_metrics['avg_retrieval_time']
        self.retrieval_metrics['avg_retrieval_time'] = (
            (current_avg * (total_queries - 1) + retrieval_time) / total_queries
        )
        
        # Update cross-links count
        self.retrieval_metrics['cross_links_found'] += cross_links_count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.retrieval_metrics.copy()
    
    def search_by_citation(self, citation: str, k: int = 5) -> List[RetrievedDocument]:
        """Search for documents by specific citation"""
        if not self.vector_db:
            return []
        
        try:
            # Search for the citation in the database
            results = self.vector_db.similarity_search_with_score(citation, k=k)
            
            documents = []
            for doc, score in results:
                # Check if citation appears in the document
                if citation.lower() in doc.page_content.lower():
                    retrieved_doc = RetrievedDocument(
                        doc_id=doc.metadata.get('id', f"doc_{len(documents)}"),
                        content=doc.page_content,
                        title=doc.metadata.get('title', 'Untitled'),
                        doc_type=self._classify_document_type(doc),
                        source=doc.metadata.get('source', 'Unknown'),
                        similarity_score=1.0 - score,
                        metadata=doc.metadata
                    )
                    documents.append(retrieved_doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching by citation: {e}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[RetrievedDocument]:
        """Get a specific document by ID"""
        if not self.vector_db:
            return None
        
        try:
            # This would require implementing a method to get by ID
            # For now, return None as ChromaDB doesn't have direct ID lookup
            logger.warning("Document lookup by ID not implemented for ChromaDB")
            return None
        except Exception as e:
            logger.error(f"Error getting document by ID: {e}")
            return None
