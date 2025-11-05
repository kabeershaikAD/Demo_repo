"""
Citation Verifier Agent for ensuring all outputs are backed by retrieved sources.
"""
import re
from typing import Dict, Any, List, Tuple, Optional
from .base_agent import BaseAgent, AgentResponse
from datetime import datetime
import json


class CitationVerifier(BaseAgent):
    """Agent that verifies citations and ensures all claims are backed by sources."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("CitationVerifier", config)
        self.citation_patterns = {
            "case_citation": r"(?i)([A-Za-z]+ v\. [A-Za-z]+|\d+ [A-Za-z]+ \d+)",
            "statute_citation": r"(?i)(section \d+|art\. \d+|§\s*\d+)",
            "year_pattern": r"(19|20)\d{2}",
            "court_pattern": r"(?i)(supreme court|high court|district court|tribunal)",
            "source_reference": r"(?i)(source \d+|document \d+)"
        }
        
    async def initialize(self) -> bool:
        """Initialize the citation verifier."""
        try:
            self.logger.info("Citation Verifier initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Citation Verifier: {e}")
            return False
    
    async def process(self, input_data: Any) -> AgentResponse:
        """Verify citations in the generated answer."""
        try:
            if isinstance(input_data, dict):
                answer = input_data.get("answer", "")
                retrieved_docs = input_data.get("retrieved_documents", [])
                citations = input_data.get("citations", [])
            else:
                raise ValueError("Input must be a dict with 'answer' and 'retrieved_documents'")
            
            if not answer.strip():
                return AgentResponse(
                    success=False,
                    data=None,
                    metadata={},
                    timestamp=datetime.now(),
                    agent_name=self.name,
                    error_message="Empty answer provided"
                )
            
            # Verify citations
            verification_result = await self._verify_citations(answer, retrieved_docs, citations)
            
            # Check for unsupported claims
            unsupported_claims = await self._find_unsupported_claims(answer, retrieved_docs)
            
            # Calculate verification score
            verification_score = self._calculate_verification_score(verification_result, unsupported_claims)
            
            result = {
                "verification_passed": verification_score >= 0.7,
                "verification_score": verification_score,
                "verified_citations": verification_result["verified_citations"],
                "unverified_citations": verification_result["unverified_citations"],
                "unsupported_claims": unsupported_claims,
                "recommendations": self._generate_recommendations(verification_result, unsupported_claims)
            }
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={
                    "total_citations": len(verification_result["verified_citations"]) + len(verification_result["unverified_citations"]),
                    "verification_threshold": 0.7,
                    "answer_length": len(answer),
                    "sources_available": len(retrieved_docs)
                },
                timestamp=datetime.now(),
                agent_name=self.name
            )
            
        except Exception as e:
            self.logger.error(f"Error verifying citations: {e}")
            return AgentResponse(
                success=False,
                data=None,
                metadata={},
                timestamp=datetime.now(),
                agent_name=self.name,
                error_message=str(e)
            )
    
    async def _verify_citations(self, answer: str, retrieved_docs: List[Dict], citations: List[Dict]) -> Dict[str, List]:
        """Verify that all citations in the answer are supported by retrieved documents."""
        verified_citations = []
        unverified_citations = []
        
        # Extract all citations from the answer
        found_citations = self._extract_citations_from_text(answer)
        
        # Check each citation against retrieved documents
        for citation in found_citations:
            is_verified = await self._verify_single_citation(citation, retrieved_docs)
            
            if is_verified:
                verified_citations.append({
                    "text": citation["text"],
                    "type": citation["type"],
                    "position": citation["position"],
                    "verified": True
                })
            else:
                unverified_citations.append({
                    "text": citation["text"],
                    "type": citation["type"],
                    "position": citation["position"],
                    "verified": False
                })
        
        # Also check provided citations
        for citation in citations:
            if isinstance(citation, dict):
                citation_text = citation.get("text", "")
                if citation_text and citation_text not in [c["text"] for c in verified_citations + unverified_citations]:
                    is_verified = await self._verify_single_citation(
                        {"text": citation_text, "type": "provided"}, 
                        retrieved_docs
                    )
                    
                    if is_verified:
                        verified_citations.append({
                            "text": citation_text,
                            "type": "provided",
                            "verified": True
                        })
                    else:
                        unverified_citations.append({
                            "text": citation_text,
                            "type": "provided",
                            "verified": False
                        })
        
        return {
            "verified_citations": verified_citations,
            "unverified_citations": unverified_citations
        }
    
    def _extract_citations_from_text(self, text: str) -> List[Dict]:
        """Extract citations from the given text."""
        citations = []
        
        for pattern_name, pattern in self.citation_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                citations.append({
                    "text": match.group(),
                    "type": pattern_name,
                    "position": match.start()
                })
        
        return citations
    
    async def _verify_single_citation(self, citation: Dict, retrieved_docs: List[Dict]) -> bool:
        """Verify if a single citation is supported by retrieved documents."""
        citation_text = citation["text"].lower()
        
        # Check if citation appears in any retrieved document
        for doc in retrieved_docs:
            if isinstance(doc, dict):
                content = doc.get("content", "").lower()
                if citation_text in content:
                    return True
            else:
                content = str(doc).lower()
                if citation_text in content:
                    return True
        
        return False
    
    async def _find_unsupported_claims(self, answer: str, retrieved_docs: List[Dict]) -> List[Dict]:
        """Find claims in the answer that are not supported by retrieved documents."""
        unsupported_claims = []
        
        # Split answer into sentences
        sentences = re.split(r'[.!?]+', answer)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:  # Skip very short sentences
                continue
            
            # Check if sentence contains factual claims
            if self._contains_factual_claim(sentence):
                # Check if claim is supported by retrieved documents
                is_supported = await self._is_claim_supported(sentence, retrieved_docs)
                
                if not is_supported:
                    unsupported_claims.append({
                        "sentence": sentence,
                        "position": i,
                        "claim_type": self._classify_claim_type(sentence)
                    })
        
        return unsupported_claims
    
    def _contains_factual_claim(self, sentence: str) -> bool:
        """Check if a sentence contains factual claims that need verification."""
        # Look for indicators of factual claims
        claim_indicators = [
            r'\b(?:is|are|was|were|has|have|had|will|would|can|could|should|must)\b',
            r'\b(?:according to|based on|research shows|studies indicate)\b',
            r'\b(?:section \d+|article \d+|case \w+)\b',
            r'\b(?:court|judge|ruling|decision|precedent)\b',
            r'\b(?:law|statute|regulation|amendment)\b'
        ]
        
        for pattern in claim_indicators:
            if re.search(pattern, sentence, re.IGNORECASE):
                return True
        
        return False
    
    async def _is_claim_supported(self, claim: str, retrieved_docs: List[Dict]) -> bool:
        """Check if a claim is supported by retrieved documents."""
        claim_lower = claim.lower()
        
        # Extract key terms from the claim
        key_terms = re.findall(r'\b\w{4,}\b', claim_lower)  # Words with 4+ characters
        
        for doc in retrieved_docs:
            if isinstance(doc, dict):
                content = doc.get("content", "").lower()
            else:
                content = str(doc).lower()
            
            # Check if most key terms appear in the document
            matching_terms = sum(1 for term in key_terms if term in content)
            if matching_terms >= len(key_terms) * 0.6:  # 60% of key terms match
                return True
        
        return False
    
    def _classify_claim_type(self, sentence: str) -> str:
        """Classify the type of claim made in the sentence."""
        if re.search(r'\b(?:section|article|statute)\b', sentence, re.IGNORECASE):
            return "legal_provision"
        elif re.search(r'\b(?:case|court|judge|ruling)\b', sentence, re.IGNORECASE):
            return "case_law"
        elif re.search(r'\b(?:law|regulation|amendment)\b', sentence, re.IGNORECASE):
            return "legal_principle"
        else:
            return "general_claim"
    
    def _calculate_verification_score(self, verification_result: Dict, unsupported_claims: List) -> float:
        """Calculate overall verification score."""
        total_citations = len(verification_result["verified_citations"]) + len(verification_result["unverified_citations"])
        
        if total_citations == 0:
            # No citations found - check for unsupported claims
            if len(unsupported_claims) == 0:
                return 0.5  # Neutral score for claims without citations
            else:
                return 0.3  # Lower score for unsupported claims
        
        # Calculate score based on verified citations and unsupported claims
        verified_ratio = len(verification_result["verified_citations"]) / total_citations
        unsupported_penalty = min(0.3, len(unsupported_claims) * 0.1)
        
        score = verified_ratio - unsupported_penalty
        return max(0.0, min(1.0, score))
    
    def _generate_recommendations(self, verification_result: Dict, unsupported_claims: List) -> List[str]:
        """Generate recommendations for improving citation verification."""
        recommendations = []
        
        unverified_count = len(verification_result["unverified_citations"])
        unsupported_count = len(unsupported_claims)
        
        if unverified_count > 0:
            recommendations.append(f"Verify {unverified_count} unverified citations with reliable sources")
        
        if unsupported_count > 0:
            recommendations.append(f"Support {unsupported_count} unsupported claims with evidence from retrieved documents")
        
        if unverified_count == 0 and unsupported_count == 0:
            recommendations.append("All citations are properly verified and claims are well-supported")
        
        return recommendations
