"""
Test suite for citation verifier functionality
"""

import pytest
from citation_verifier import (
    VerificationResult, CitationVerification, ClaimExtractor, 
    SimilarityVerifier, KeywordVerifier, CitationVerifier
)
from retriever_agent import RetrievedDocument
from sentence_transformers import SentenceTransformer

class TestClaimExtractor:
    """Test claim extractor"""
    
    def test_extract_claims(self):
        """Test claim extraction"""
        extractor = ClaimExtractor()
        
        answer_text = "Article 21 guarantees the right to life. This is a fundamental right. The Supreme Court has interpreted this broadly."
        claims = extractor.extract_claims(answer_text)
        
        assert len(claims) > 0
        assert all(len(claim) > 10 for claim in claims)  # Should extract meaningful claims
    
    def test_extract_claims_empty(self):
        """Test claim extraction with empty text"""
        extractor = ClaimExtractor()
        
        claims = extractor.extract_claims("")
        assert claims == []
    
    def test_extract_claims_short(self):
        """Test claim extraction with short text"""
        extractor = ClaimExtractor()
        
        claims = extractor.extract_claims("Short text.")
        assert len(claims) <= 1

class TestSimilarityVerifier:
    """Test similarity verifier"""
    
    def test_verify_claim_similarity(self):
        """Test claim similarity verification"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        verifier = SimilarityVerifier(embedding_model)
        
        claim = "Article 21 guarantees the right to life"
        documents = [
            RetrievedDocument(
                doc_id="doc1",
                content="Article 21 of the Constitution guarantees the right to life and personal liberty",
                title="Constitution Article 21",
                doc_type="statute",
                source="test",
                similarity_score=0.9
            )
        ]
        
        result = verifier.verify_claim_similarity(claim, documents)
        
        assert isinstance(result, VerificationResult)
        assert result.claim_text == claim
        assert result.is_supported is True
        assert result.similarity_score > 0.5
        assert result.verification_method == "similarity"
    
    def test_verify_claim_similarity_no_docs(self):
        """Test claim verification with no documents"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        verifier = SimilarityVerifier(embedding_model)
        
        claim = "Test claim"
        result = verifier.verify_claim_similarity(claim, [])
        
        assert result.is_supported is False
        assert result.similarity_score == 0.0
        assert "No documents available" in result.error_message
    
    def test_extract_relevant_excerpt(self):
        """Test relevant excerpt extraction"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        verifier = SimilarityVerifier(embedding_model)
        
        content = "This is a long legal document about Article 21 of the Constitution which guarantees fundamental rights to all citizens."
        claim = "Article 21 fundamental rights"
        
        excerpt = verifier._extract_relevant_excerpt(content, claim)
        
        assert len(excerpt) > 0
        assert len(excerpt) <= 200  # Should respect max_length

class TestKeywordVerifier:
    """Test keyword verifier"""
    
    def test_verify_claim_keywords(self):
        """Test claim verification using keywords"""
        verifier = KeywordVerifier()
        
        claim = "Article 21 guarantees fundamental rights"
        documents = [
            RetrievedDocument(
                doc_id="doc1",
                content="Article 21 of the Constitution guarantees the right to life and personal liberty as fundamental rights",
                title="Constitution Article 21",
                doc_type="statute",
                source="test",
                similarity_score=0.9
            )
        ]
        
        result = verifier.verify_claim_keywords(claim, documents)
        
        assert isinstance(result, VerificationResult)
        assert result.claim_text == claim
        assert result.is_supported is True
        assert result.similarity_score > 0.5
        assert result.verification_method == "keyword"
    
    def test_calculate_keyword_score(self):
        """Test keyword score calculation"""
        verifier = KeywordVerifier()
        
        claim = "Article 21 fundamental rights"
        doc_content = "Article 21 of the Constitution guarantees fundamental rights to all citizens"
        
        score = verifier._calculate_keyword_score(claim, doc_content)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.3  # Should have reasonable overlap
    
    def test_extract_keyword_excerpt(self):
        """Test keyword-based excerpt extraction"""
        verifier = KeywordVerifier()
        
        content = "This document discusses Article 21 of the Constitution. Article 21 guarantees fundamental rights to all citizens. This is an important constitutional provision."
        claim = "Article 21 fundamental rights"
        
        excerpt = verifier._extract_keyword_excerpt(content, claim)
        
        assert len(excerpt) > 0
        assert "Article 21" in excerpt

class TestCitationVerifier:
    """Test main citation verifier"""
    
    def test_verify_citations(self):
        """Test citation verification"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        verifier = CitationVerifier(embedding_model)
        
        answer_text = "Article 21 guarantees the right to life. This is a fundamental right."
        documents = [
            RetrievedDocument(
                doc_id="doc1",
                content="Article 21 of the Constitution guarantees the right to life and personal liberty",
                title="Constitution Article 21",
                doc_type="statute",
                source="test",
                similarity_score=0.9
            )
        ]
        
        result = verifier.verify_citations(answer_text, documents)
        
        assert isinstance(result, CitationVerification)
        assert result.total_claims > 0
        assert result.supported_claims >= 0
        assert result.unsupported_claims >= 0
        assert 0.0 <= result.overall_confidence <= 1.0
    
    def test_verify_claim(self):
        """Test single claim verification"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        verifier = CitationVerifier(embedding_model)
        
        claim = "Article 21 guarantees fundamental rights"
        documents = [
            RetrievedDocument(
                doc_id="doc1",
                content="Article 21 of the Constitution guarantees the right to life and personal liberty",
                title="Constitution Article 21",
                doc_type="statute",
                source="test",
                similarity_score=0.9
            )
        ]
        
        result = verifier.verify_claim(claim, documents)
        
        assert isinstance(result, VerificationResult)
        assert result.claim_text == claim
        assert result.verification_confidence >= 0.0
    
    def test_get_verification_stats(self):
        """Test verification statistics"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        verifier = CitationVerifier(embedding_model)
        
        stats = verifier.get_verification_stats()
        
        assert isinstance(stats, dict)
        assert 'total_verifications' in stats
        assert 'successful_verifications' in stats
        assert 'failed_verifications' in stats
        assert 'avg_confidence' in stats

if __name__ == "__main__":
    pytest.main([__file__])

