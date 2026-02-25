"""
Test suite for retrieval functionality
"""

import pytest
from retriever_agent import RetrievedDocument, RetrievalResult, CitationExtractor, CrossLinker
from sentence_transformers import SentenceTransformer

class TestRetrievedDocument:
    """Test RetrievedDocument class"""
    
    def test_retrieved_document_creation(self):
        """Test RetrievedDocument creation"""
        doc = RetrievedDocument(
            doc_id="test_1",
            content="Test content",
            title="Test Title",
            doc_type="statute",
            source="test",
            similarity_score=0.85
        )
        
        assert doc.doc_id == "test_1"
        assert doc.content == "Test content"
        assert doc.doc_type == "statute"
        assert doc.citations == []
        assert doc.metadata == {}
    
    def test_retrieved_document_with_metadata(self):
        """Test RetrievedDocument with metadata"""
        doc = RetrievedDocument(
            doc_id="test_2",
            content="Test content",
            title="Test Title",
            doc_type="judgment",
            source="test",
            similarity_score=0.9,
            court="Supreme Court",
            date="2023-01-01",
            citations=["case1", "case2"],
            metadata={"key": "value"}
        )
        
        assert doc.court == "Supreme Court"
        assert doc.date == "2023-01-01"
        assert doc.citations == ["case1", "case2"]
        assert doc.metadata == {"key": "value"}

class TestRetrievalResult:
    """Test RetrievalResult class"""
    
    def test_retrieval_result_creation(self):
        """Test RetrievalResult creation"""
        statutes = [
            RetrievedDocument("stat1", "content1", "title1", "statute", "test", 0.8)
        ]
        judgments = [
            RetrievedDocument("judg1", "content2", "title2", "judgment", "test", 0.9)
        ]
        
        result = RetrievalResult(
            statutes=statutes,
            judgments=judgments,
            cross_links=[],
            total_retrieved=2,
            avg_similarity=0.85,
            retrieval_time=0.1
        )
        
        assert len(result.statutes) == 1
        assert len(result.judgments) == 1
        assert result.total_retrieved == 2
        assert result.avg_similarity == 0.85
        assert result.cross_links == []
        assert result.metadata == {}

class TestCitationExtractor:
    """Test citation extractor"""
    
    def test_extract_citations(self):
        """Test citation extraction"""
        extractor = CitationExtractor()
        
        text = "Section 302 of the Indian Penal Code and Article 21 of the Constitution."
        citations = extractor.extract_citations(text)
        
        assert len(citations) > 0
        assert any(c['type'] == 'ipc_section' for c in citations)
        assert any(c['type'] == 'constitutional_article' for c in citations)
    
    def test_extract_statute_citations(self):
        """Test statute citation extraction"""
        extractor = CitationExtractor()
        
        text = "Section 302 IPC and Article 21 Constitution"
        citations = extractor.extract_statute_citations(text)
        
        assert len(citations) > 0
        assert any("302" in citation for citation in citations)
        assert any("21" in citation for citation in citations)
    
    def test_ipc_patterns(self):
        """Test IPC citation patterns"""
        extractor = CitationExtractor()
        
        test_cases = [
            "Section 302 of the Indian Penal Code",
            "IPC Section 420",
            "S. 302 IPC"
        ]
        
        for text in test_cases:
            citations = extractor.extract_citations(text)
            assert len(citations) > 0
    
    def test_constitutional_patterns(self):
        """Test constitutional citation patterns"""
        extractor = CitationExtractor()
        
        test_cases = [
            "Article 21 of the Constitution",
            "Art. 21 Constitution",
            "Constitution Article 21"
        ]
        
        for text in test_cases:
            citations = extractor.extract_citations(text)
            assert len(citations) > 0

class TestCrossLinker:
    """Test cross-linker"""
    
    def test_cross_linker_initialization(self):
        """Test cross-linker initialization"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        cross_linker = CrossLinker(embedding_model)
        
        assert cross_linker.embedding_model is not None
        assert cross_linker.similarity_threshold > 0
    
    def test_citations_match(self):
        """Test citation matching"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        cross_linker = CrossLinker(embedding_model)
        
        judgment_citation = {
            'text': 'Section 302 IPC',
            'type': 'ipc_section',
            'value': '302'
        }
        statute_citation = "Section 302 of the Indian Penal Code"
        
        match = cross_linker._citations_match(judgment_citation, statute_citation)
        assert match is True
    
    def test_calculate_citation_confidence(self):
        """Test citation confidence calculation"""
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        cross_linker = CrossLinker(embedding_model)
        
        judgment_citation = {'text': 'Section 302 IPC'}
        statute_citation = "Section 302 of the Indian Penal Code"
        
        judgment_doc = RetrievedDocument("judg1", "content", "title", "judgment", "test", 0.9)
        statute_doc = RetrievedDocument("stat1", "content", "title", "statute", "test", 0.8)
        
        confidence = cross_linker._calculate_citation_confidence(
            judgment_citation, statute_citation, judgment_doc, statute_doc
        )
        
        assert 0.0 <= confidence <= 1.0

if __name__ == "__main__":
    pytest.main([__file__])

