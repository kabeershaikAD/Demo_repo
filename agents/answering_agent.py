"""
Answering Agent with plug-and-play LLM support for generating grounded legal answers.
"""
import openai
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent, AgentResponse
from datetime import datetime
import json
import re


class AnsweringAgent(BaseAgent):
    """Agent that generates final answers using retrieved legal documents."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Answering", config)
        self.llm_client = None
        self.model_name = None
        self.temperature = 0.1
        self.max_tokens = 1000
        
    async def initialize(self) -> bool:
        """Initialize the LLM client based on configuration."""
        try:
            self.model_name = self.config.get("model_name", "gpt-3.5-turbo")
            self.temperature = self.config.get("temperature", 0.1)
            self.max_tokens = self.config.get("max_tokens", 1000)
            
            # Initialize OpenAI client
            api_key = self.config.get("openai_api_key")
            if not api_key:
                raise ValueError("OpenAI API key not provided")
            
            openai.api_key = api_key
            self.llm_client = openai
            
            self.logger.info(f"Initialized Answering Agent with model: {self.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Answering Agent: {e}")
            return False
    
    async def process(self, input_data: Any) -> AgentResponse:
        """Generate answer based on query and retrieved documents."""
        try:
            # Parse input data
            if isinstance(input_data, dict):
                query = input_data.get("query", "")
                retrieved_docs = input_data.get("retrieved_documents", [])
                context = input_data.get("context", "")
            else:
                raise ValueError("Input must be a dict with 'query' and 'retrieved_documents'")
            
            if not query.strip():
                return AgentResponse(
                    success=False,
                    data=None,
                    metadata={},
                    timestamp=datetime.now(),
                    agent_name=self.name,
                    error_message="Empty query provided"
                )
            
            # Prepare context from retrieved documents
            context_text = self._prepare_context(retrieved_docs, context)
            
            # Generate answer
            answer = await self._generate_answer(query, context_text, retrieved_docs)
            
            # Extract citations
            citations = self._extract_citations(answer, retrieved_docs)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(answer, retrieved_docs)
            
            result = {
                "answer": answer,
                "citations": citations,
                "confidence_score": confidence,
                "sources_used": len(retrieved_docs),
                "query": query
            }
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={
                    "model_used": self.model_name,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "context_length": len(context_text),
                    "answer_length": len(answer)
                },
                timestamp=datetime.now(),
                agent_name=self.name
            )
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            return AgentResponse(
                success=False,
                data=None,
                metadata={},
                timestamp=datetime.now(),
                agent_name=self.name,
                error_message=str(e)
            )
    
    def _prepare_context(self, retrieved_docs: List[Dict], additional_context: str = "") -> str:
        """Prepare context from retrieved documents."""
        context_parts = []
        
        # Add additional context if provided
        if additional_context.strip():
            context_parts.append(f"Additional Context: {additional_context}")
        
        # Add retrieved documents
        for i, doc in enumerate(retrieved_docs, 1):
            if isinstance(doc, dict):
                content = doc.get("content", "")
                source = doc.get("source", f"Document {i}")
                doc_type = doc.get("doc_type", "legal_document")
            else:
                content = str(doc)
                source = f"Document {i}"
                doc_type = "legal_document"
            
            if content.strip():
                context_parts.append(f"Source {i} ({source} - {doc_type}):\n{content}\n")
        
        return "\n".join(context_parts)
    
    async def _generate_answer(self, query: str, context: str, retrieved_docs: List[Dict]) -> str:
        """Generate answer using the LLM."""
        try:
            # Create system prompt for legal answering
            system_prompt = """You are a legal expert AI assistant. Your task is to provide accurate, well-reasoned legal answers based on the provided legal documents and context.

Guidelines:
1. Base your answer strictly on the provided legal documents and context
2. If the context doesn't contain enough information to answer the query, clearly state this
3. Provide specific citations to relevant sections, cases, or statutes when possible
4. Use clear, professional legal language
5. Structure your answer logically with clear reasoning
6. If there are conflicting sources, acknowledge the conflict
7. Always indicate the level of certainty in your answer

Format your response as:
- Direct answer to the query
- Legal reasoning based on the sources
- Specific citations where applicable
- Any limitations or uncertainties"""

            # Create user prompt
            user_prompt = f"""Query: {query}

Legal Context and Sources:
{context}

Please provide a comprehensive legal answer based on the above context. Include specific citations to relevant sources."""

            # Make API call
            response = await self.llm_client.ChatCompletion.acreate(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            return f"I apologize, but I encountered an error while generating the answer: {str(e)}"
    
    def _extract_citations(self, answer: str, retrieved_docs: List[Dict]) -> List[Dict]:
        """Extract citations from the generated answer."""
        citations = []
        
        # Look for citation patterns in the answer
        citation_patterns = [
            r'\(Source \d+\)',
            r'\(Document \d+\)',
            r'\[Source \d+\]',
            r'\[Document \d+\]',
            r'\([^)]*section \d+[^)]*\)',
            r'\([^)]*art\. \d+[^)]*\)',
            r'\([^)]*case [^)]*\)'
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            for match in matches:
                citations.append({
                    "text": match,
                    "type": "source_reference",
                    "position": answer.find(match)
                })
        
        # Add document references
        for i, doc in enumerate(retrieved_docs, 1):
            if isinstance(doc, dict):
                source = doc.get("source", f"Document {i}")
                doc_type = doc.get("doc_type", "legal_document")
                citations.append({
                    "text": f"Source {i}",
                    "source": source,
                    "doc_type": doc_type,
                    "type": "document_reference"
                })
        
        return citations
    
    def _calculate_confidence(self, answer: str, retrieved_docs: List[Dict]) -> float:
        """Calculate confidence score for the generated answer."""
        if not answer or not retrieved_docs:
            return 0.0
        
        # Base confidence on various factors
        confidence_factors = []
        
        # Length of answer (longer answers often more comprehensive)
        answer_length = len(answer.split())
        if answer_length > 50:
            confidence_factors.append(0.3)
        elif answer_length > 20:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)
        
        # Number of sources used
        num_sources = len(retrieved_docs)
        if num_sources >= 3:
            confidence_factors.append(0.3)
        elif num_sources >= 2:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(0.1)
        
        # Presence of citations
        if "Source" in answer or "Document" in answer:
            confidence_factors.append(0.2)
        
        # Presence of legal terminology
        legal_terms = ["section", "article", "statute", "case", "court", "law", "legal", "jurisdiction"]
        legal_term_count = sum(1 for term in legal_terms if term.lower() in answer.lower())
        if legal_term_count >= 3:
            confidence_factors.append(0.2)
        elif legal_term_count >= 1:
            confidence_factors.append(0.1)
        
        # Calculate final confidence
        confidence = min(1.0, sum(confidence_factors))
        return round(confidence, 2)
    
    async def generate_follow_up_questions(self, query: str, answer: str) -> List[str]:
        """Generate follow-up questions based on the query and answer."""
        try:
            follow_up_prompt = f"""Based on this legal query and answer, suggest 3 relevant follow-up questions that would help the user explore the topic further.

Query: {query}
Answer: {answer}

Generate follow-up questions that:
1. Explore related legal aspects
2. Ask for clarification on specific points
3. Request examples or case studies
4. Inquire about practical implications

Format as a simple list, one question per line."""

            response = await self.llm_client.ChatCompletion.acreate(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": follow_up_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            follow_up_text = response.choices[0].message.content.strip()
            questions = [q.strip() for q in follow_up_text.split('\n') if q.strip()]
            return questions[:3]  # Return top 3 questions
            
        except Exception as e:
            self.logger.error(f"Error generating follow-up questions: {e}")
            return []
