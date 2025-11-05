"""
Tests for individual agents.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from agents import PromptBoosterAgent, RetrieverAgent, AnsweringAgent, CitationVerifier


class TestPromptBoosterAgent:
    """Test cases for Prompt Booster Agent."""
    
    @pytest.fixture
    def agent(self):
        return PromptBoosterAgent()
    
    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initialization."""
        # Mock the model loading to avoid actual model download
        with patch('agents.prompt_booster_agent.T5Tokenizer') as mock_tokenizer, \
             patch('agents.prompt_booster_agent.T5ForConditionalGeneration') as mock_model:
            
            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            
            result = await agent.initialize()
            assert result is True
            assert agent.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_query_enhancement(self, agent):
        """Test query enhancement functionality."""
        # Mock the model and tokenizer
        agent.model = Mock()
        agent.tokenizer = Mock()
        agent.is_initialized = True
        
        # Mock tokenizer output
        agent.tokenizer.return_value = Mock()
        agent.tokenizer.return_value.to.return_value = Mock()
        
        # Mock model output
        mock_output = Mock()
        mock_output[0] = Mock()
        agent.tokenizer.decode.return_value = "Enhanced legal query about patent requirements"
        agent.model.generate.return_value = mock_output
        
        result = await agent.process("What are patent requirements?")
        
        assert result.success is True
        assert "enhanced_query" in result.data
        assert "legal_entities" in result.data
        assert "search_keywords" in result.data


class TestRetrieverAgent:
    """Test cases for Retriever Agent."""
    
    @pytest.fixture
    def agent(self):
        return RetrieverAgent()
    
    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initialization."""
        with patch('agents.retriever_agent.SentenceTransformer') as mock_embedding:
            mock_embedding.return_value = Mock()
            
            result = await agent.initialize()
            assert result is True
            assert agent.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_document_retrieval(self, agent):
        """Test document retrieval functionality."""
        # Mock the embedding model and index
        agent.embedding_model = Mock()
        agent.embedding_model.encode.return_value = [[0.1, 0.2, 0.3]]
        agent.index = Mock()
        agent.index.search.return_value = ([[0.8, 0.7]], [[0, 1]])
        agent.documents = ["Document 1", "Document 2"]
        agent.metadata = [{"source": "doc1.pdf"}, {"source": "doc2.pdf"}]
        agent.is_initialized = True
        
        result = await agent.process("test query")
        
        assert result.success is True
        assert "documents" in result.data
        assert "scores" in result.data


class TestAnsweringAgent:
    """Test cases for Answering Agent."""
    
    @pytest.fixture
    def agent(self):
        return AnsweringAgent({"openai_api_key": "test_key"})
    
    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initialization."""
        with patch('agents.answering_agent.openai') as mock_openai:
            result = await agent.initialize()
            assert result is True
            assert agent.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_answer_generation(self, agent):
        """Test answer generation functionality."""
        agent.llm_client = Mock()
        agent.is_initialized = True
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a legal answer based on the provided documents."
        agent.llm_client.ChatCompletion.acreate.return_value = mock_response
        
        input_data = {
            "query": "What are patent requirements?",
            "retrieved_documents": [{"content": "Patent law content..."}]
        }
        
        result = await agent.process(input_data)
        
        assert result.success is True
        assert "answer" in result.data
        assert "citations" in result.data
        assert "confidence_score" in result.data


class TestCitationVerifier:
    """Test cases for Citation Verifier."""
    
    @pytest.fixture
    def agent(self):
        return CitationVerifier()
    
    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initialization."""
        result = await agent.initialize()
        assert result is True
        assert agent.is_initialized is True
    
    @pytest.mark.asyncio
    async def test_citation_verification(self, agent):
        """Test citation verification functionality."""
        agent.is_initialized = True
        
        input_data = {
            "answer": "According to Section 1 of the Patent Act, patents are granted for inventions.",
            "retrieved_documents": [{"content": "Section 1 of the Patent Act states that patents are granted for inventions."}]
        }
        
        result = await agent.process(input_data)
        
        assert result.success is True
        assert "verification_passed" in result.data
        assert "verification_score" in result.data
        assert "verified_citations" in result.data


if __name__ == "__main__":
    pytest.main([__file__])
