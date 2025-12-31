"""
Test suite for prompt booster functionality
"""

import pytest
from booster_agent import PromptBooster, QueryEnhancement, QueryEnhancementAnalyzer

class TestPromptBooster:
    """Test prompt booster agent"""
    
    def test_enhance_query_rules(self):
        """Test query enhancement with rule-based method"""
        booster = PromptBooster()
        
        # Test query without jurisdiction context
        query = "What are tenant rights?"
        enhancement = booster.enhance_query(query)
        
        assert enhancement.original_query == query
        assert "Indian" in enhancement.enhanced_query or "legal" in enhancement.enhanced_query
        assert enhancement.confidence_score > 0
        assert enhancement.enhancement_type in ['jurisdiction_specific', 'statute_specific', 'fallback']
    
    def test_enhance_query_with_context(self):
        """Test query enhancement with context"""
        booster = PromptBooster()
        
        query = "How to get bail?"
        context = "criminal case"
        enhancement = booster.enhance_query(query, context)
        
        assert enhancement.original_query == query
        assert enhancement.confidence_score > 0
    
    def test_expand_abbreviations(self):
        """Test abbreviation expansion"""
        booster = PromptBooster()
        
        query = "What is IPC section 302?"
        enhanced = booster._expand_abbreviations(query)
        
        assert "Indian Penal Code" in enhanced or "IPC" in enhanced
        assert "302" in enhanced
    
    def test_has_jurisdiction_context(self):
        """Test jurisdiction context detection"""
        booster = PromptBooster()
        
        # Should have jurisdiction context
        assert booster._has_jurisdiction_context("What is Article 21 of the Constitution?")
        assert booster._has_jurisdiction_context("IPC section 302")
        
        # Should not have jurisdiction context
        assert not booster._has_jurisdiction_context("What are tenant rights?")
        assert not booster._has_jurisdiction_context("How to get bail?")
    
    def test_needs_legal_specificity(self):
        """Test legal specificity detection"""
        booster = PromptBooster()
        
        # Should need legal specificity
        assert booster._needs_legal_specificity("What are my rights?")
        assert booster._needs_legal_specificity("How to file a case?")
        
        # Should not need legal specificity
        assert not booster._needs_legal_specificity("IPC section 302 punishment")
        assert not booster._needs_legal_specificity("Article 21 Constitution")
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        booster = PromptBooster()
        
        original = "What are tenant rights?"
        enhanced = "Indian law tenant rights legal provisions"
        
        confidence = booster._calculate_confidence(original, enhanced)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.1  # Should have some confidence
    
    def test_batch_enhance(self):
        """Test batch enhancement"""
        booster = PromptBooster()
        
        queries = ["What is Article 21?", "How to get bail?", "Tenant rights"]
        enhancements = booster.batch_enhance(queries)
        
        assert len(enhancements) == len(queries)
        assert all(isinstance(enh, QueryEnhancement) for enh in enhancements)

class TestQueryEnhancementAnalyzer:
    """Test query enhancement analyzer"""
    
    def test_analyze_enhancement(self):
        """Test enhancement analysis"""
        analyzer = QueryEnhancementAnalyzer()
        
        enhancement = QueryEnhancement(
            original_query="test query",
            enhanced_query="enhanced test query",
            enhancement_type="legal_rewrite",
            confidence_score=0.8,
            reasoning="Test enhancement"
        )
        
        analysis = analyzer.analyze_enhancement(enhancement, 0.9)
        
        assert analysis['enhancement_type'] == "legal_rewrite"
        assert analysis['confidence_score'] == 0.8
        assert analysis['retrieval_quality'] == 0.9
        assert analysis['effectiveness'] == 0.8 * 0.9
    
    def test_get_enhancement_stats(self):
        """Test enhancement statistics"""
        analyzer = QueryEnhancementAnalyzer()
        
        # Add some test data
        enhancement1 = QueryEnhancement(
            original_query="query1",
            enhanced_query="enhanced1",
            enhancement_type="legal_rewrite",
            confidence_score=0.8,
            reasoning="test"
        )
        
        enhancement2 = QueryEnhancement(
            original_query="query2",
            enhanced_query="enhanced2",
            enhancement_type="jurisdiction_specific",
            confidence_score=0.6,
            reasoning="test"
        )
        
        analyzer.analyze_enhancement(enhancement1, 0.9)
        analyzer.analyze_enhancement(enhancement2, 0.7)
        
        stats = analyzer.get_enhancement_stats()
        
        assert stats['total_enhancements'] == 2
        assert stats['avg_effectiveness'] > 0
        assert stats['avg_confidence'] > 0

if __name__ == "__main__":
    pytest.main([__file__])

