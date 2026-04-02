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

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    HUGGINGFACE_EMBEDDINGS_AVAILABLE = True
except ImportError:
    HUGGINGFACE_EMBEDDINGS_AVAILABLE = False
    HuggingFaceEmbeddings = None

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
        use_local = getattr(config.model, "USE_LOCAL_EMBEDDINGS", False)
        if use_local and HUGGINGFACE_EMBEDDINGS_AVAILABLE:
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=config.model.EMBEDDING_MODEL_NAME,
            )
            logger.info(f"Using local embeddings: {config.model.EMBEDDING_MODEL_NAME} (no API cost)")
        else:
            self.embedding_model = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=config.api.OPENAI_API_KEY,
            )
            if use_local:
                logger.warning("Local embeddings requested but langchain_huggingface not installed, using OpenAI")
        
        # Initialize ChromaDB connection (catch Rust panic / corrupted DB)
        def _connect_chroma(path):
            return Chroma(
                collection_name="langchain",
                embedding_function=self.embedding_model,
                persist_directory=path
            )
        fallback_paths = [
            os.path.join(current_dir, "chroma_db_"),
            os.path.abspath(os.path.join(current_dir, "..", "..", "chroma_db_")),
            "./chroma_db_",
        ]
        self.vector_db = None
        try:
            self.vector_db = _connect_chroma(self.chroma_db_path)
            if "consolidated" in str(self.chroma_db_path):
                logger.info(f"Successfully connected to consolidated ChromaDB at {self.chroma_db_path}")
            else:
                logger.info(f"Connected to ChromaDB at {self.chroma_db_path}")
        except BaseException as e:
            logger.warning(f"ChromaDB failed at {self.chroma_db_path}: {e}")
            for path in fallback_paths:
                if not path or not os.path.exists(path):
                    continue
                try:
                    self.vector_db = _connect_chroma(path)
                    self.chroma_db_path = path
                    logger.info(f"Connected to ChromaDB at fallback: {self.chroma_db_path}")
                    break
                except BaseException:
                    continue
            if self.vector_db is None:
                logger.error("Could not connect to any ChromaDB")
        
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
            
            # Convert to RetrievedDocument objects with quality filtering
            MAX_L2_DISTANCE = 0.85
            retrieved_docs = []
            seen_content = set()
            for doc, score in search_results:
                # Quality gate: skip docs with high L2 distance
                if score > MAX_L2_DISTANCE:
                    logger.debug(f"Skipping doc (distance {score:.3f} > {MAX_L2_DISTANCE})")
                    continue

                # Deduplication: skip if content already seen
                content_hash = hash(doc.page_content[:200])
                if content_hash in seen_content:
                    continue
                seen_content.add(content_hash)

                doc_type = self._classify_document_type(doc)
                
                similarity = max(1.0 - score, 0.0)
                retrieved_doc = RetrievedDocument(
                    doc_id=doc.metadata.get('id', f"doc_{len(retrieved_docs)}"),
                    content=doc.page_content,
                    title=doc.metadata.get('title', 'Untitled'),
                    doc_type=doc_type,
                    source=doc.metadata.get('source', 'Unknown'),
                    similarity_score=round(similarity, 4),
                    court=doc.metadata.get('court'),
                    date=doc.metadata.get('date'),
                    section=doc.metadata.get('section'),
                    act=doc.metadata.get('act'),
                    metadata=doc.metadata
                )
                
                retrieved_doc.citations = self.citation_extractor.extract_citations(doc.page_content)
                retrieved_docs.append(retrieved_doc)
            
            if not retrieved_docs:
                logger.warning(f"All {len(search_results)} results filtered out (distance > {MAX_L2_DISTANCE})")
            
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



# ---------------------------------------------------------------------------
# ReAct wrapper  (uses the existing RetrieverAgent under the hood)
# ---------------------------------------------------------------------------

import json as _json
from core.tools import Tool, ToolRegistry
from core.base_react_agent import BaseReActAgent, AgentResult, groq_chat

_RETRIEVER_SYSTEM = (
    "You are a Legal Document Retrieval Agent in an Indian legal RAG system. "
    "Your job is to search the legal database (ChromaDB) and return the most "
    "relevant statutes and judgments for the user's query.\n"
    "If the first search returns low-quality results, you should refine the "
    "search query and try again."
)


class RetrieverReActAgent(BaseReActAgent):
    """ReAct agent that wraps the existing RetrieverAgent capabilities."""

    def __init__(self, retriever: "RetrieverAgent"):
        tools = ToolRegistry()
        super().__init__(
            name="RetrieverAgent",
            system_prompt=_RETRIEVER_SYSTEM,
            tools=tools,
            max_steps=3,
            direct_tool_execution=True,
        )
        self._retriever = retriever
        self._last_docs = []
        self._register_tools()

    def _register_tools(self):
        self.tools.register(Tool(
            name="search_documents",
            description=(
                "Search the legal document database. Returns statutes and "
                "judgments matching the query. doc_type can be 'statutes', "
                "'judgments', or 'all'."
            ),
            parameters={"query": "str", "doc_type": "str (default 'all')", "k": "int (default 5)"},
            func=self._tool_search,
        ))
        self.tools.register(Tool(
            name="evaluate_results",
            description=(
                "Evaluate the quality of the retrieved documents. Checks "
                "coverage, similarity scores, and doc type diversity."
            ),
            parameters={},
            func=self._tool_evaluate,
        ))
        self.tools.register(Tool(
            name="search_web",
            description=(
                "Search the web for Indian legal information when the local "
                "database has no relevant results. Returns legal text from "
                "online sources. Use this when search_documents returns 0 "
                "results or very low scores."
            ),
            parameters={"query": "str"},
            func=self._tool_web_search,
        ))
        self.tools.register(Tool(
            name="refine_search",
            description=(
                "Generate a refined search query based on what is missing "
                "from the current results, then search again."
            ),
            parameters={"original_query": "str", "feedback": "str"},
            func=self._tool_refine,
        ))

    async def _tool_search(
        self, query: str = "", doc_type: str = "all", k: int = 5, **kw
    ) -> str:
        filters = None
        if doc_type and doc_type != "all":
            filters = {"doc_type": doc_type}
        k = int(k)
        result = self._retriever.retrieve(query, k=k, filters=filters)
        docs = []
        for d in (result.statutes + result.judgments):
            docs.append({
                "doc_id": d.doc_id,
                "title": (d.title or "")[:80],
                "doc_type": d.doc_type,
                "score": round(d.similarity_score, 3),
                "snippet": (d.content or "")[:200],
            })
        self._last_docs = docs
        if not docs:
            logger.info("No local docs passed quality filter, auto-falling back to web search")
            try:
                web_obs = await self._tool_web_search(query=query)
                docs = self._last_docs
                if docs:
                    summary = f"Local DB had no relevant results. Web search found {len(docs)} results."
                    titles = "; ".join(d["title"] for d in docs[:3])
                    summary += f" Top: {titles}"
                else:
                    summary = "No relevant documents found in local database or web search."
            except Exception as e:
                summary = f"No local results and web search failed: {e}"
        else:
            avg = sum(d["score"] for d in docs) / len(docs) if docs else 0
            summary = f"Found {len(docs)} relevant documents (avg similarity {avg:.3f})."
            titles = "; ".join(d["title"] for d in docs[:3])
            summary += f" Top results: {titles}"
            if avg < 0.3:
                summary += " WARNING: Scores are low. Consider using search_web for better results."
        return summary

    async def _tool_evaluate(self, **kw) -> str:
        docs = self._last_docs
        if not docs:
            return _json.dumps({"quality": "no_results", "suggestion": "try a broader search"})
        scores = [d["score"] for d in docs]
        avg = sum(scores) / len(scores)
        types = set(d["doc_type"] for d in docs)
        quality = "good" if avg > 0.4 else ("fair" if avg > 0.25 else "poor")
        return _json.dumps({
            "quality": quality,
            "doc_count": len(docs),
            "avg_score": round(avg, 3),
            "doc_types_found": list(types),
            "has_statutes": "statute" in " ".join(types).lower(),
            "has_judgments": "judgment" in " ".join(types).lower() or "case" in " ".join(types).lower(),
        })

    async def _tool_refine(
        self, original_query: str = "", feedback: str = "", **kw
    ) -> str:
        prompt = (
            f"The user asked: \"{original_query}\"\n"
            f"The current search results are insufficient: {feedback}\n"
            f"Rewrite the search query to find better legal documents. "
            f"Output ONLY the rewritten query."
        )
        refined = await groq_chat(
            "You rewrite legal search queries. Output ONLY the rewritten query.",
            prompt,
        )
        if refined:
            return await self._tool_search(query=refined, k=5)
        return "Could not refine query."

    async def _tool_web_search(self, query: str = "", **kw) -> str:
        """Search the web for Indian legal information."""
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    f"{query} Indian law legal",
                    max_results=3,
                    region="in-en",
                ))
            if not results:
                return "No web results found."
            docs = []
            for r in results:
                body = r.get("body", "")
                docs.append({
                    "doc_id": f"web_{len(docs)}",
                    "title": r.get("title", "")[:80],
                    "doc_type": "web_result",
                    "score": 0.6,
                    "snippet": body[:300],
                    "content": body[:200],
                    "source": r.get("href", ""),
                    "similarity_score": 0.6,
                })
            self._last_docs = docs
            titles = "; ".join(d["title"] for d in docs[:3])
            return f"Found {len(docs)} web results. Top: {titles}"
        except Exception as e:
            return f"Web search failed: {e}. Proceeding with available local results."

    # -- hooks --------------------------------------------------------------

    def _build_task_prompt(self, context):
        query = context.get("query", "")
        k = context.get("top_k", 5)
        mode = context.get("retrieval_mode", "all")
        return (
            f"Retrieve relevant legal documents for: \"{query}\"\n"
            f"Preferred doc type: {mode}, number of results: {k}.\n"
            f"Search the local database first. If results are good, give Final Answer.\n"
            f"If NO local docs found, the system will auto-search the web.\n"
            f"Once you have ANY results (local or web), give Final Answer immediately.\n"
            f"Do NOT refine if web search already returned results."
        )

    def _extract_final_output(self, answer_text, context):
        docs = self._last_docs
        return {
            "documents": docs,
            "scores": [d["score"] for d in docs],
            "metadata": {"total": len(docs)},
            "confidence": 0.7 if docs else 0.3,
        }

    def _fallback(self, context):
        query = context.get("query", "")
        k = context.get("top_k", 5)
        result = self._retriever.retrieve(query, k=k)
        docs = []
        for d in (result.statutes + result.judgments):
            docs.append({
                "doc_id": d.doc_id,
                "title": (d.title or "")[:80],
                "doc_type": d.doc_type,
                "score": round(d.similarity_score, 3),
                "snippet": (d.content or "")[:200],
            })
        if not docs:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        web_result = pool.submit(asyncio.run, self._tool_web_search(query=query)).result()
                else:
                    web_result = loop.run_until_complete(self._tool_web_search(query=query))
                docs = self._last_docs
            except Exception:
                pass
        return {
            "documents": docs,
            "scores": [d.get("score", 0) for d in docs],
            "metadata": {"total": len(docs), "source": "web" if docs and docs[0].get("doc_type") == "web_result" else "local"},
            "confidence": 0.4 if not docs else 0.5,
        }
