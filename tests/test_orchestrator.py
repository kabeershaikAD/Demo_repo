"""
Tests for the main orchestrator.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from orchestrator import AgenticLegalRAG


class TestAgenticLegalRAG:
    """Test cases for the main orchestrator."""
    
    @pytest.fixture
    def rag_system(self):
        return AgenticLegalRAG()
    
    @pytest.mark.asyncio
    async def test_initialization(self, rag_system):
        """Test system initialization."""
        with patch('orchestrator.PromptBoosterAgent') as mock_booster, \
             patch('orchestrator.RetrieverAgent') as mock_retriever, \
             patch('orchestrator.AnsweringAgent') as mock_answering, \
             patch('orchestrator.CitationVerifier') as mock_verifier:
            
            # Mock agent initialization
            mock_booster.return_value.initialize = AsyncMock(return_value=True)
            mock_retriever.return_value.initialize = AsyncMock(return_value=True)
            mock_answering.return_value.initialize = AsyncMock(return_value=True)
            mock_verifier.return_value.initialize = AsyncMock(return_value=True)
            
            result = await rag_system.initialize()
            assert result is True
            assert rag_system.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_query_processing(self, rag_system):
        """Test query processing pipeline."""
        # Mock all agents
        mock_booster = Mock()
        mock_booster.execute = AsyncMock(return_value=Mock(
            success=True,
            data={"enhanced_query": "Enhanced query", "legal_entities": [], "search_keywords": []},
            metadata={}
        ))
        
        mock_retriever = Mock()
        mock_retriever.execute = AsyncMock(return_value=Mock(
            success=True,
            data={"documents": [{"content": "Legal content"}], "scores": [0.8]},
            metadata={}
        ))
        
        mock_answering = Mock()
        mock_answering.execute = AsyncMock(return_value=Mock(
            success=True,
            data={"answer": "Legal answer", "citations": [], "confidence_score": 0.9},
            metadata={}
        ))
        
        mock_verifier = Mock()
        mock_verifier.execute = AsyncMock(return_value=Mock(
            success=True,
            data={"verification_passed": True, "verification_score": 0.8},
            metadata={}
        ))
        
        # Set up agents
        rag_system.agents = {
            "prompt_booster": mock_booster,
            "retriever": mock_retriever,
            "answering": mock_answering,
            "citation_verifier": mock_verifier
        }
        rag_system.is_initialized = True
        
        result = await rag_system.process_query("What are patent requirements?")
        
        assert result["success"] is True
        assert "answer" in result
        assert "enhanced_query" in result
        assert "verification" in result
    
    @pytest.mark.asyncio
    async def test_document_addition(self, rag_system):
        """Test document addition functionality."""
        mock_retriever = Mock()
        mock_retriever.add_documents = AsyncMock(return_value=True)
        
        rag_system.agents = {"retriever": mock_retriever}
        
        documents = [{"content": "Legal document content", "title": "Test Document"}]
        result = await rag_system.add_documents(documents)
        
        assert result is True
        mock_retriever.add_documents.assert_called_once_with(documents)
    
    @pytest.mark.asyncio
    async def test_system_status(self, rag_system):
        """Test system status retrieval."""
        mock_agent = Mock()
        mock_agent.get_status.return_value = {"name": "test", "is_initialized": True}
        
        rag_system.agents = {"test_agent": mock_agent}
        rag_system.is_initialized = True
        
        status = await rag_system.get_system_status()
        
        assert status["system_initialized"] is True
        assert "test_agent" in status["agents"]


if __name__ == "__main__":
    pytest.main([__file__])
