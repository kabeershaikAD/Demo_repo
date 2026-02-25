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
    from sentence_transformers import SentenceTransformer, util
    from langchain_openai import OpenAIEmbeddings
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    OPENAI_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    OPENAI_AVAILABLE = False
    np = None
    SentenceTransformer = None
    util = None
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
        if OPENAI_AVAILABLE:
            try:
                self.embedding_model = OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=config.api.OPENAI_API_KEY
                )
                logger.info("Using OpenAI embeddings for citation verification")
            except Exception as e:
                logger.warning(f"Could not load OpenAI embedding model: {e}")
                self.embedding_model = None
        elif SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(config.model.EMBEDDING_MODEL_NAME)
                logger.info("Using SentenceTransformer embeddings for citation verification")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
        else:
            self.embedding_model = None
            logger.warning("No embedding models available. Using fallback verification.")
        
        self.similarity_threshold = config.retrieval.CITATION_THRESHOLD
        
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
            
            # Check if claim is supported
            supported = best_similarity >= self.similarity_threshold
            
            # Find all supporting documents
            supporting_docs = []
            similarity_scores = {}
            
            for i, doc in enumerate(retrieved_docs):
                similarity = similarities[i].item()
                similarity_scores[doc.get('doc_id', f'doc_{i}')] = similarity
                
                if similarity >= self.similarity_threshold:
                    supporting_docs.append(doc.get('doc_id', f'doc_{i}'))
            
            # Determine verification method
            verification_method = 'semantic'
            
            # If semantic verification fails, try keyword matching
            if not supported:
                keyword_result = self._verify_with_keywords(claim_text, retrieved_docs)
                if keyword_result.supported:
                    supported = True
                    confidence = keyword_result.confidence
                    supporting_docs = keyword_result.supporting_docs
                    verification_method = 'hybrid'
                else:
                    confidence = best_similarity
            else:
                confidence = best_similarity
            
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
