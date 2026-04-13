"""
Citation Verifier Module for Agentic Legal RAG
Verifies claims against retrieved documents using semantic similarity
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    util = None

try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAIEmbeddings = None

from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """Result of citation verification"""
    claim_text: str
    supported: bool
    confidence: float
    supporting_docs: List[str]
    best_match_doc: Optional[str]
    similarity_scores: Dict[str, float]
    verification_method: str  # 'semantic', 'keyword', 'hybrid'

class CitationVerifier:
    """Verifies claims against retrieved documents"""
    
    def __init__(self):
        self.embedding_model = None
        # Prefer local SentenceTransformer (free, no API) over OpenAI
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                model_name = getattr(config.model, "CITATION_VERIFICATION_MODEL",
                                     config.model.EMBEDDING_MODEL_NAME)
                self.embedding_model = SentenceTransformer(model_name)
                logger.info(f"Using local SentenceTransformer ({model_name}) for citation verification - no API cost")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer: {e}")

        if self.embedding_model is None and OPENAI_AVAILABLE:
            try:
                self.embedding_model = OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=config.api.OPENAI_API_KEY,
                )
                logger.info("Using OpenAI embeddings for citation verification (fallback)")
            except Exception as e:
                logger.warning(f"Could not load OpenAI embedding model: {e}")

        if self.embedding_model is None:
            logger.warning("No embedding models available. Using keyword-only verification.")
        
        self.similarity_threshold = 0.40
        
        # Performance metrics
        self.metrics = {
            'total_claims': 0,
            'verified_claims': 0,
            'unverified_claims': 0,
            'avg_verification_time': 0.0,
            'semantic_verifications': 0,
            'keyword_verifications': 0
        }
        
        logger.info("CitationVerifier initialized")

    def _normalize_doc(self, doc: Any, index: int) -> Dict[str, Any]:
        """Ensure each doc is a dict with content and doc_id (handle str or object)."""
        if isinstance(doc, dict):
            return dict(doc)
        if isinstance(doc, str):
            return {"content": doc, "doc_id": f"doc_{index}", "title": ""}
        if hasattr(doc, "__dict__"):
            d = getattr(doc, "__dict__", {})
            return {"content": d.get("content", ""), "doc_id": d.get("doc_id", f"doc_{index}"), "title": d.get("title", "")}
        return {"content": str(doc), "doc_id": f"doc_{index}", "title": ""}

    def verify(self, claims: List[Dict[str, Any]], retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify claims against retrieved documents
        
        Args:
            claims: List of claims from AnsweringAgent
            retrieved_docs: Retrieved documents from RetrieverAgent
            
        Returns:
            List of verified claims with support status
        """
        import time
        start_time = time.time()
        retrieved_docs = [self._normalize_doc(d, i) for i, d in enumerate(retrieved_docs or [])]
        
        # Handle case where claims is empty but we have documents
        if not claims:
            if not retrieved_docs:
                logger.warning("No claims or documents to verify")
                return []
            else:
                # If no specific claims, create a generic verification for document quality
                logger.info("No specific claims to verify, checking document quality")
                return self._verify_document_quality(retrieved_docs)
        
        if not retrieved_docs:
            logger.warning("No documents to verify claims against")
            return []
        
        try:
            # Pre-compute document embeddings for efficiency
            doc_embeddings = self._compute_document_embeddings(retrieved_docs)
            
            verified_claims = []
            
            for claim in claims:
                claim_text = claim.get('text', '')
                if not claim_text:
                    continue
                
                # Verify claim against documents
                verification_result = self._verify_single_claim(
                    claim_text, 
                    retrieved_docs, 
                    doc_embeddings
                )
                
                # Convert to expected format
                verified_claim = {
                    'text': claim_text,
                    'supported': verification_result.supported,
                    'confidence': verification_result.confidence,
                    'best_doc': verification_result.best_match_doc,
                    'similarity_score': verification_result.confidence,
                    'supporting_docs': verification_result.supporting_docs,
                    'verification_method': verification_result.verification_method
                }
                
                verified_claims.append(verified_claim)
            
            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(verified_claims, processing_time)
            
            logger.info(f"Verified {len(verified_claims)} claims in {processing_time:.2f}s")
            return verified_claims
            
        except Exception as e:
            logger.error(f"Error in citation verification: {e}")
            # Return claims with default verification status
            return [{
                'text': claim.get('text', ''),
                'supported': False,
                'confidence': 0.0,
                'best_doc': None,
                'similarity_score': 0.0,
                'supporting_docs': [],
                'verification_method': 'error'
            } for claim in claims]
    
    def _compute_document_embeddings(self, retrieved_docs: List[Dict[str, Any]]):
        """Compute embeddings for all retrieved documents"""
        try:
            if not self.embedding_model:
                return None
            
            doc_texts = [doc.get('content', '') for doc in retrieved_docs]
            
            if hasattr(self.embedding_model, 'embed_documents'):
                # OpenAI embeddings
                embeddings = self.embedding_model.embed_documents(doc_texts)
                return np.array(embeddings)
            elif hasattr(self.embedding_model, 'encode'):
                # SentenceTransformer embeddings
                embeddings = self.embedding_model.encode(doc_texts, convert_to_tensor=True)
                return embeddings
            else:
                return None
        except Exception as e:
            logger.error(f"Error computing document embeddings: {e}")
            return None
    
    def _verify_single_claim(self, claim_text: str, retrieved_docs: List[Dict[str, Any]], doc_embeddings) -> VerificationResult:
        """Verify a single claim against retrieved documents"""
        try:
            if not self.embedding_model or doc_embeddings is None:
                return VerificationResult(
                    claim_text=claim_text,
                    supported=False,
                    confidence=0.0,
                    supporting_docs=[],
                    best_match_doc=None,
                    similarity_scores={},
                    verification_method='error'
                )
            
            # Compute claim embedding
            if hasattr(self.embedding_model, 'embed_query'):
                # OpenAI embeddings
                claim_embedding = np.array(self.embedding_model.embed_query(claim_text))
            elif hasattr(self.embedding_model, 'encode'):
                # SentenceTransformer embeddings
                claim_embedding = self.embedding_model.encode([claim_text], convert_to_tensor=True)
            else:
                return VerificationResult(
                    claim_text=claim_text,
                    supported=False,
                    confidence=0.0,
                    supporting_docs=[],
                    best_match_doc=None,
                    similarity_scores={},
                    verification_method='error'
                )
            
            if hasattr(doc_embeddings, 'size') and doc_embeddings.size == 0:
                return VerificationResult(
                    claim_text=claim_text,
                    supported=False,
                    confidence=0.0,
                    supporting_docs=[],
                    best_match_doc=None,
                    similarity_scores={},
                    verification_method='error'
                )
            
            # Calculate semantic similarities
            if hasattr(util, 'pytorch_cos_sim'):
                # SentenceTransformer similarity
                similarities = util.pytorch_cos_sim(claim_embedding, doc_embeddings)[0]
            else:
                # NumPy cosine similarity for OpenAI embeddings
                similarities = np.dot(claim_embedding, doc_embeddings.T) / (
                    np.linalg.norm(claim_embedding) * np.linalg.norm(doc_embeddings, axis=1)
                )
            
            # Find best matches
            best_match_idx = similarities.argmax().item()
            best_similarity = similarities[best_match_idx].item()
            
            # Check for General Knowledge tag
            is_general_knowledge = "[General Knowledge]" in claim_text or "[general knowledge]" in claim_text.lower()
            gk_bonus = 0.20 if is_general_knowledge else 0.0

            adjusted_similarity = best_similarity + gk_bonus
            supported = adjusted_similarity >= self.similarity_threshold

            supporting_docs = []
            similarity_scores = {}

            for i, doc in enumerate(retrieved_docs):
                similarity = similarities[i].item()
                similarity_scores[doc.get('doc_id', f'doc_{i}')] = similarity
                if similarity >= self.similarity_threshold:
                    supporting_docs.append(doc.get('doc_id', f'doc_{i}'))

            verification_method = 'semantic'

            if not supported:
                keyword_result = self._verify_with_keywords(claim_text, retrieved_docs)
                kw_score = keyword_result.confidence if keyword_result.supported else 0.0
                combined = max(best_similarity, kw_score) + gk_bonus
                if combined >= self.similarity_threshold:
                    supported = True
                    confidence = min(combined, 1.0)
                    supporting_docs = keyword_result.supporting_docs or supporting_docs
                    verification_method = 'hybrid'
                else:
                    confidence = min(max(best_similarity + gk_bonus, kw_score), 1.0)
            else:
                confidence = min(adjusted_similarity, 1.0)
            
            return VerificationResult(
                claim_text=claim_text,
                supported=supported,
                confidence=confidence,
                supporting_docs=supporting_docs,
                best_match_doc=retrieved_docs[best_match_idx].get('doc_id', f'doc_{best_match_idx}') if retrieved_docs else None,
                similarity_scores=similarity_scores,
                verification_method=verification_method
            )
            
        except Exception as e:
            logger.error(f"Error verifying claim: {e}")
            return VerificationResult(
                claim_text=claim_text,
                supported=False,
                confidence=0.0,
                supporting_docs=[],
                best_match_doc=None,
                similarity_scores={},
                verification_method='error'
            )
    
    def _verify_with_keywords(self, claim_text: str, retrieved_docs: List[Dict[str, Any]]) -> VerificationResult:
        """Verify claim using keyword matching as fallback"""
        try:
            # Extract keywords from claim
            claim_keywords = self._extract_keywords(claim_text)
            
            best_match_score = 0.0
            best_match_doc = None
            supporting_docs = []
            similarity_scores = {}
            
            for i, doc in enumerate(retrieved_docs):
                doc_content = doc.get('content', '').lower()
                doc_keywords = self._extract_keywords(doc_content)
                
                # Calculate keyword overlap
                common_keywords = set(claim_keywords) & set(doc_keywords)
                total_keywords = set(claim_keywords) | set(doc_keywords)
                
                if total_keywords:
                    keyword_score = len(common_keywords) / len(total_keywords)
                else:
                    keyword_score = 0.0
                
                similarity_scores[doc.get('doc_id', f'doc_{i}')] = keyword_score
                
                legal_terms = ['article', 'section', 'act', 'court', 'supreme',
                               'constitution', 'law', 'rights', 'judgment', 'writ',
                               'habeas', 'corpus', 'mandamus', 'PIL', 'fundamental']
                lt_hits = sum(1 for t in legal_terms if t in doc_content and t in claim_text.lower())
                keyword_score = keyword_score + (lt_hits * 0.05)

                if keyword_score > best_match_score:
                    best_match_score = keyword_score
                    best_match_doc = doc.get('doc_id', f'doc_{i}')
                
                # Consider as supporting if keyword overlap is significant
                if keyword_score >= 0.3:  # Lower threshold for keyword matching
                    supporting_docs.append(doc.get('doc_id', f'doc_{i}'))
            
            # Determine if claim is supported
            supported = best_match_score >= 0.3  # Lower threshold for keyword matching
            
            return VerificationResult(
                claim_text=claim_text,
                supported=supported,
                confidence=best_match_score,
                supporting_docs=supporting_docs,
                best_match_doc=best_match_doc,
                similarity_scores=similarity_scores,
                verification_method='keyword'
            )
            
        except Exception as e:
            logger.error(f"Error in keyword verification: {e}")
            return VerificationResult(
                claim_text=claim_text,
                supported=False,
                confidence=0.0,
                supporting_docs=[],
                best_match_doc=None,
                similarity_scores={},
                verification_method='error'
            )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        # Remove common words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Extract words (simple approach)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        return keywords
    
    def _update_metrics(self, verified_claims: List[Dict[str, Any]], processing_time: float):
        """Update performance metrics"""
        self.metrics['total_claims'] += len(verified_claims)
        
        verified_count = sum(1 for claim in verified_claims if claim.get('supported', False))
        self.metrics['verified_claims'] += verified_count
        self.metrics['unverified_claims'] += len(verified_claims) - verified_count
        
        # Update average verification time
        total_claims = self.metrics['total_claims']
        current_avg = self.metrics['avg_verification_time']
        self.metrics['avg_verification_time'] = (
            (current_avg * (total_claims - len(verified_claims)) + processing_time) / total_claims
        )
        
        # Update verification method counts
        for claim in verified_claims:
            method = claim.get('verification_method', 'unknown')
            if method == 'semantic':
                self.metrics['semantic_verifications'] += 1
            elif method == 'keyword':
                self.metrics['keyword_verifications'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'total_claims': 0,
            'verified_claims': 0,
            'unverified_claims': 0,
            'avg_verification_time': 0.0,
            'semantic_verifications': 0,
            'keyword_verifications': 0
        }
        logger.info("CitationVerifier metrics reset")
    
    def _verify_document_quality(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify document quality when no specific claims are provided"""
        try:
            quality_checks = []
            
            for i, doc in enumerate(retrieved_docs):
                # Basic quality checks
                content = doc.get('content', '')
                title = doc.get('title', '')
                
                # Check if document has meaningful content
                has_content = len(content.strip()) > 50
                has_title = len(title.strip()) > 0
                
                # Check for legal relevance indicators
                legal_indicators = ['section', 'article', 'act', 'law', 'court', 'judgment', 'statute']
                has_legal_content = any(indicator in content.lower() for indicator in legal_indicators)
                
                # Calculate quality score
                quality_score = 0.0
                if has_content:
                    quality_score += 0.4
                if has_title:
                    quality_score += 0.2
                if has_legal_content:
                    quality_score += 0.4
                
                quality_check = {
                    'text': f"Document {i+1} quality check",
                    'supported': quality_score >= 0.6,  # At least 60% quality
                    'confidence': quality_score,
                    'best_doc': doc.get('doc_id', f'doc_{i}'),
                    'similarity_score': quality_score,
                    'supporting_docs': [doc.get('doc_id', f'doc_{i}')] if quality_score >= 0.6 else [],
                    'verification_method': 'quality_check'
                }
                
                quality_checks.append(quality_check)
            
            return quality_checks
            
        except Exception as e:
            logger.error(f"Error in document quality verification: {e}")
            return []
    
    def set_similarity_threshold(self, threshold: float):
        """Set similarity threshold for verification"""
        self.similarity_threshold = threshold
        logger.info(f"Similarity threshold set to {threshold}")
    
    def verify_single_claim(self, claim_text: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify a single claim (convenience method)"""
        verified_claims = self.verify([{'text': claim_text}], retrieved_docs)
        return verified_claims[0] if verified_claims else {
            'text': claim_text,
            'supported': False,
            'confidence': 0.0,
            'best_doc': None,
            'similarity_score': 0.0,
            'supporting_docs': [],
            'verification_method': 'error'
        }



# ---------------------------------------------------------------------------
# ReAct wrapper  (uses the existing CitationVerifier under the hood)
# ---------------------------------------------------------------------------

import json as _json
from core.tools import Tool, ToolRegistry
from core.base_react_agent import BaseReActAgent, AgentResult, groq_chat

_VERIFIER_SYSTEM = (
    "You are a Legal Citation Verification Agent. Your job is to verify "
    "that each claim in a legal answer is supported by the retrieved "
    "source documents.\n"
    "You should check each claim, find supporting evidence, and flag "
    "any unsupported or inaccurate claims."
)


class VerifierReActAgent(BaseReActAgent):
    """ReAct agent that wraps the existing CitationVerifier capabilities."""

    def __init__(self, verifier: "CitationVerifier"):
        tools = ToolRegistry()
        super().__init__(
            name="VerifierAgent",
            system_prompt=_VERIFIER_SYSTEM,
            tools=tools,
            max_steps=2,
            direct_tool_execution=True,
        )
        self._verifier = verifier
        self._verification_results = []
        self._register_tools()

    def _register_tools(self):
        self.tools.register(Tool(
            name="verify_claims",
            description=(
                "Verify all claims in the answer against retrieved documents "
                "using semantic similarity. Returns per-claim verification."
            ),
            parameters={"claims": "list of claim dicts", "documents": "list of doc dicts"},
            func=self._tool_verify,
        ))
        self.tools.register(Tool(
            name="find_evidence",
            description=(
                "Search the retrieved documents for text that supports or "
                "contradicts a specific claim."
            ),
            parameters={"claim_text": "str"},
            func=self._tool_find_evidence,
        ))
        self.tools.register(Tool(
            name="flag_issues",
            description=(
                "Summarize verification issues and produce a final "
                "verification score and report."
            ),
            parameters={},
            func=self._tool_flag_issues,
        ))

    async def _tool_verify(self, claims=None, documents=None, **kw) -> str:
        if claims is None:
            claims = self._context_claims
        if documents is None:
            documents = self._context_docs
        normalized_docs = [
            self._verifier._normalize_doc(d, i)
            for i, d in enumerate(documents)
        ]
        if not claims:
            return _json.dumps({"verified": 0, "total": 0, "message": "No claims to verify"})
        results = self._verifier.verify(claims, normalized_docs)
        self._verification_results = results if isinstance(results, list) else []
        supported = sum(1 for r in self._verification_results if isinstance(r, dict) and r.get("supported"))
        return _json.dumps({
            "verified": supported,
            "total": len(self._verification_results),
            "details": [
                {
                    "supported": r.get("supported", False),
                    "confidence": round(r.get("confidence", 0), 3),
                }
                for r in self._verification_results[:5]
                if isinstance(r, dict)
            ],
        })

    async def _tool_find_evidence(self, claim_text: str = "", **kw) -> str:
        docs = self._context_docs
        if not docs:
            return "No documents available to search."
        evidence_snippets = []
        claim_lower = claim_text.lower()
        keywords = [w for w in claim_lower.split() if len(w) > 3]
        for d in docs[:5]:
            content = (d.get("content", "") or d.get("snippet", "")).lower()
            matches = sum(1 for kw in keywords if kw in content)
            if matches >= 2:
                raw = d.get("content", "") or d.get("snippet", "")
                evidence_snippets.append({
                    "doc_id": d.get("doc_id", "?"),
                    "snippet": raw[:200],
                    "keyword_matches": matches,
                })
        if not evidence_snippets:
            return "No strong evidence found for this claim."
        return _json.dumps(evidence_snippets[:3])

    async def _tool_flag_issues(self, **kw) -> str:
        results = self._verification_results
        if not results:
            return _json.dumps({"issues": [], "score": 0.5})
        issues = []
        for i, r in enumerate(results):
            if isinstance(r, dict) and not r.get("supported", False):
                issues.append(f"Claim {i+1} not supported (confidence {r.get('confidence', 0):.2f})")
        scores = [r.get("confidence", 0.5) for r in results if isinstance(r, dict)]
        avg = sum(scores) / len(scores) if scores else 0.5
        return _json.dumps({"issues": issues, "score": round(avg, 3)})

    # -- hooks --------------------------------------------------------------

    def _build_task_prompt(self, context):
        answer = context.get("answer", "")
        claims = context.get("claims", [])
        docs = context.get("documents", [])
        self._context_claims = claims
        self._context_docs = docs
        claim_count = len(claims) if claims else 0
        return (
            f"Verify the claims in this legal answer against {len(docs)} "
            f"retrieved documents.\n"
            f"Answer excerpt: \"{answer[:300]}...\"\n"
            f"Number of claims to verify: {claim_count}\n"
            f"You MUST use the verify_claims tool first, then give Final Answer."
        )

    def _extract_final_output(self, answer_text, context):
        answer = context.get("answer", "")
        try:
            data = _json.loads(answer_text)
            score = data.get("score", data.get("verification_score", 0.5))
        except _json.JSONDecodeError:
            score = 0.5
        results = self._verification_results
        supported = sum(1 for r in results if isinstance(r, dict) and r.get("supported"))
        return {
            "verified_answer": answer,
            "verification_score": score,
            "claims_verified": supported,
            "total_claims": len(results),
            "issues": [],
            "confidence": score,
        }

    def _fallback(self, context):
        answer = context.get("answer", "")
        claims = context.get("claims", [])
        docs = context.get("documents", [])
        normalized_docs = [
            self._verifier._normalize_doc(d, i)
            for i, d in enumerate(docs)
        ]
        try:
            results = self._verifier.verify(claims, normalized_docs)
            if isinstance(results, list) and results:
                scores = [r.get("confidence", 0.5) for r in results if isinstance(r, dict)]
                score = sum(scores) / len(scores) if scores else 0.5
                supported = sum(1 for r in results if isinstance(r, dict) and r.get("supported"))
            else:
                score = 0.5
                supported = 0
                results = []
        except Exception:
            score = 0.5
            supported = 0
            results = []
        return {
            "verified_answer": answer,
            "verification_score": score,
            "claims_verified": supported,
            "total_claims": len(results),
            "issues": [],
            "confidence": score,
        }
