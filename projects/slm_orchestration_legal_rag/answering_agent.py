"""
Answering Agent Module for Agentic Legal RAG
Generates answers with citation-first policy and legal accuracy
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time

# LLM imports (optional)
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatGroq = None
    SystemMessage = None
    HumanMessage = None
    ChatPromptTemplate = None
    StrOutputParser = None

from config import config
from retriever_agent import RetrievedDocument, RetrievalResult

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LegalClaim:
    """A legal claim with supporting evidence"""
    text: str
    cited_doc_ids: List[str]
    support_confidence: float
    claim_type: str  # 'fact', 'interpretation', 'procedure', 'right', 'obligation'
    legal_basis: Optional[str] = None
    verification_status: str = 'pending'  # 'verified', 'unverified', 'pending'
    
@dataclass
class AnswerResult:
    """Result of answer generation"""
    answer_text: str
    claims: List[LegalClaim]
    sources: List[Dict[str, Any]]
    confidence_score: float
    human_review_required: bool
    processing_time: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AnsweringAgent:
    """Generate legal answers with proper citations"""
    
    def __init__(self):
        # API PLACEHOLDER: Set your Groq API key here
        self.api_key = config.api.GROQ_API_KEY

        self.model_name = config.model.LLM_ANSWERING_MODEL
        self.llm = None
        self._initialize_llm()
        
        # Legal answer templates
        self.templates = self._initialize_templates()
        
        # Performance metrics
        self.metrics = {
            'total_answers': 0,
            'successful_answers': 0,
            'failed_answers': 0,
            'avg_processing_time': 0.0,
            'citations_generated': 0
        }
        
        logger.info("AnsweringAgent initialized")
    
    def _initialize_llm(self):
        """Initialize the LLM for answer generation"""
        try:
            if LANGCHAIN_AVAILABLE and self.api_key and self.api_key != "YOUR_GROQ_API_KEY_HERE":
                self.llm = ChatGroq(
                    api_key=self.api_key,
                    model_name=self.model_name,
                    temperature=0.1  # Low temperature for legal accuracy
                )
                logger.info(f"Initialized LLM: {self.model_name}")
            else:
                if not LANGCHAIN_AVAILABLE:
                    logger.warning("LangChain not available. Using fallback mode.")
                else:
                    logger.warning("Groq API key not provided. Using fallback mode.")
                self.llm = None
                
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            self.llm = None
    
    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize legal answer templates"""
        return {
            'system_prompt': """You are an expert legal research assistant specializing in Indian law. 
Your role is to provide accurate legal information based on retrieved documents and verified legal knowledge.

CRITICAL RULES:
1. ONLY cite real, existing legal provisions (Articles, Sections, Acts)
2. DO NOT fabricate or invent Article/Section numbers
3. If documents are insufficient, use your verified knowledge of Indian law
4. Keep answers focused and factual - do NOT list random provision numbers
5. CITE: Use [doc_id] format for document-based claims, [General Knowledge] for other claims
6. If you are unsure about a specific provision number, describe the concept instead

RESPONSE FORMAT:
Provide a comprehensive legal answer with the following structure:
- **Legal Provisions:** [Specific articles, sections, acts with citations]
- **Key Points:** [Important details and interpretations]
- **Important Cases:** [Relevant landmark judgments if applicable]
- **Brief Explanation:** [Simple terms explanation]
- **Related Legal Concepts:** [Additional relevant information]

Start directly with the answer content - do not include "Answer:" as a heading.

QUALITY STANDARDS:
- Be comprehensive and detailed like a legal expert
- Use clear, professional language
- Structure information logically
- Provide practical insights
- Include relevant case law and precedents

Remember: Your goal is to provide the most helpful and accurate legal information possible.""",
            
            'human_template': """Query: {query}

Retrieved Legal Documents:
{documents}

Instructions:
1. If the documents contain relevant information, use it and cite with [doc_id]
2. If the documents don't contain sufficient information, use your knowledge of Indian law
3. Provide a comprehensive, detailed answer like a legal expert would
4. Include specific legal provisions, case law, and practical insights
5. Structure your answer clearly with proper headings

Please provide a comprehensive legal answer.""",
            
            'fallback_template': """Based on the available information, I can provide the following response:

Query: {query}

Retrieved Documents: {document_count} documents found

Note: This response is generated without LLM processing. For detailed legal analysis, please ensure the LLM is properly configured.

Key Points:
- Document retrieval completed successfully
- {document_count} relevant documents found
- Further analysis requires LLM integration

Please configure your API keys to enable full legal analysis."""
        }
    
    def generate_answer(self, user_query: str, enhanced_query: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a legal answer with proper citations
        
        Args:
            user_query: Original user query
            enhanced_query: Enhanced query from Prompt Booster
            retrieved_docs: Retrieved documents from Retriever Agent
            
        Returns:
            Dict containing answer_text, claims, sources, and metadata
        """
        start_time = time.time()
        
        try:
            if self.llm:
                # Use LLM for answer generation (even with 0 documents)
                answer_result = self._generate_with_llm(user_query, enhanced_query, retrieved_docs or [])
            else:
                # Use fallback template
                answer_result = self._generate_fallback(user_query, retrieved_docs or [])
            
            processing_time = time.time() - start_time
            answer_result['processing_time'] = processing_time
            
            # Update metrics
            self._update_metrics(True, processing_time, len(answer_result.get('claims', [])))
            
            logger.info(f"Answer generated in {processing_time:.2f}s")
            return answer_result
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            processing_time = time.time() - start_time
            self._update_metrics(False, processing_time, 0)
            
            return {
                'answer_text': f"I apologize, but I encountered an error while generating the answer: {str(e)}",
                'claims': [],
                'sources': [],
                'confidence_score': 0.0,
                'human_review_required': True,
                'processing_time': processing_time,
                'metadata': {'error': str(e)}
            }
    
    def _generate_with_llm(self, user_query: str, enhanced_query: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate answer using LLM"""
        try:
            # Format documents for LLM
            formatted_docs = self._format_documents_for_llm(retrieved_docs) if retrieved_docs else "No specific documents were retrieved from the database for this query."
            
            # Create prompt
            system_message = SystemMessage(content=self.templates['system_prompt'])
            human_message = HumanMessage(content=self.templates['human_template'].format(
                query=user_query,
                documents=formatted_docs
            ))
            
            # Generate response
            messages = [system_message, human_message]
            response = self.llm.invoke(messages)
            
            # Parse response
            answer_text = response.content
            
            # Extract claims and citations
            claims = self._extract_claims_from_response(answer_text, retrieved_docs)
            sources = self._extract_sources(retrieved_docs)
            
            # Calculate confidence
            confidence_score = self._calculate_confidence_score(claims, retrieved_docs)
            
            # Check if human review is required
            human_review_required = self._requires_human_review(claims, confidence_score)
            
            return {
                'answer_text': answer_text,
                'claims': claims,
                'sources': sources,
                'confidence_score': confidence_score,
                'human_review_required': human_review_required,
                'metadata': {
                    'enhanced_query': enhanced_query,
                    'llm_used': True,
                    'documents_used': len(retrieved_docs)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in LLM generation: {e}")
            raise
    
    def _generate_fallback(self, user_query: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback answer without LLM"""
        document_count = len(retrieved_docs)
        
        answer_text = self.templates['fallback_template'].format(
            query=user_query,
            document_count=document_count
        )
        
        # Create basic claims from retrieved documents
        claims = []
        for i, doc in enumerate(retrieved_docs[:3]):  # Limit to first 3 docs
            claim = LegalClaim(
                text=f"Document {i+1}: {doc.get('title', 'Untitled')}",
                cited_doc_ids=[doc.get('doc_id', f'doc_{i}')],
                support_confidence=0.5,  # Default confidence for fallback
                claim_type='fact',
                verification_status='pending'
            )
            claims.append(claim)
        
        return {
            'answer_text': answer_text,
            'claims': claims,
            'sources': self._extract_sources(retrieved_docs),
            'confidence_score': 0.3,  # Lower confidence for fallback
            'human_review_required': True,
            'metadata': {
                'llm_used': False,
                'fallback_mode': True,
                'documents_used': document_count
            }
        }
    
    def _format_documents_for_llm(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents for LLM input"""
        formatted_docs = []
        
        for i, doc in enumerate(retrieved_docs):
            doc_id = doc.get('doc_id', f'doc_{i}')
            title = doc.get('title', 'Untitled')
            content = doc.get('content', '')
            doc_type = doc.get('doc_type', 'document')
            
            formatted_doc = f"""
--- Document {i+1} (ID: {doc_id}) ---
Title: {title}
Type: {doc_type}
Content: {content[:500]}...
------------------------
"""
            formatted_docs.append(formatted_doc)
        
        return '\n'.join(formatted_docs)
    
    def _extract_claims_from_response(self, answer_text: str, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract claims and citations from LLM response"""
        claims = []
        
        # Find citation patterns [doc_id_chunkIndex]
        citation_pattern = r'\[([^\]]+)\]'
        citations = re.findall(citation_pattern, answer_text)
        
        # Create claims based on sentences with citations
        sentences = re.split(r'[.!?]+', answer_text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if sentence contains citations
            sentence_citations = re.findall(citation_pattern, sentence)
            
            if sentence_citations:
                claim = {
                    'text': sentence,
                    'citations': sentence_citations,
                    'score': 1.0 if sentence_citations else 0.0
                }
                claims.append(claim)
        
        return claims
    
    def _extract_sources(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from retrieved documents"""
        sources = []
        
        for doc in retrieved_docs:
            source = {
                'doc_id': doc.get('doc_id', 'unknown'),
                'title': doc.get('title', 'Untitled'),
                'doc_type': doc.get('doc_type', 'document'),
                'source': doc.get('source', 'Unknown'),
                'similarity_score': doc.get('similarity_score', 0.0),
                'court': doc.get('court'),
                'date': doc.get('date'),
                'section': doc.get('section'),
                'act': doc.get('act')
            }
            sources.append(source)
        
        return sources
    
    def _calculate_confidence_score(self, claims: List[Dict[str, Any]], retrieved_docs: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score"""
        if not claims:
            return 0.0
        
        # Base confidence on citation coverage
        total_claims = len(claims)
        cited_claims = sum(1 for claim in claims if claim.get('citations'))
        
        citation_confidence = cited_claims / total_claims if total_claims > 0 else 0.0
        
        # Boost confidence based on document quality
        doc_confidence = 0.0
        if retrieved_docs:
            avg_similarity = sum(doc.get('similarity_score', 0.0) for doc in retrieved_docs) / len(retrieved_docs)
            doc_confidence = avg_similarity
        
        # Weighted average: 70% citation confidence, 30% document confidence
        return (citation_confidence * 0.7) + (doc_confidence * 0.3)
    
    def _requires_human_review(self, claims: List[Dict[str, Any]], confidence_score: float) -> bool:
        """Determine if human review is required"""
        # Review required if confidence is low
        if confidence_score < config.retrieval.CITATION_THRESHOLD:
            
            return True
        
        # Review required if there are unverified claims
        unverified_claims = sum(1 for claim in claims if not claim.get('citations'))
        if unverified_claims > len(claims) * 0.3:  # More than 30% unverified
            return True
        
        return False
    
    def _update_metrics(self, success: bool, processing_time: float, citations_count: int):
        """Update performance metrics"""
        self.metrics['total_answers'] += 1
        if success:
            self.metrics['successful_answers'] += 1
        else:
            self.metrics['failed_answers'] += 1
        
        # Update average processing time
        total_answers = self.metrics['total_answers']
        current_avg = self.metrics['avg_processing_time']
        self.metrics['avg_processing_time'] = (
            (current_avg * (total_answers - 1) + processing_time) / total_answers
        )
        
        # Update citations count
        self.metrics['citations_generated'] += citations_count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'total_answers': 0,
            'successful_answers': 0,
            'failed_answers': 0,
            'avg_processing_time': 0.0,
            'citations_generated': 0
        }
        logger.info("AnsweringAgent metrics reset")


# ---------------------------------------------------------------------------
# ReAct wrapper  (uses the existing AnsweringAgent under the hood)
# ---------------------------------------------------------------------------

import json as _json
from core.tools import Tool, ToolRegistry
from core.base_react_agent import BaseReActAgent, AgentResult, groq_chat

_ANSWERING_SYSTEM = (
    "You are a Legal Answer Generation Agent in an Indian legal RAG system. "
    "Your job is to generate a comprehensive, well-cited legal answer based "
    "on retrieved documents.\n"
    "You should draft an answer, check whether it covers all aspects of the "
    "question, and refine it if needed."
)


class AnsweringReActAgent(BaseReActAgent):
    """ReAct agent that wraps the existing AnsweringAgent capabilities."""

    def __init__(self, answering_agent: "AnsweringAgent"):
        tools = ToolRegistry()
        super().__init__(
            name="AnsweringAgent",
            system_prompt=_ANSWERING_SYSTEM,
            tools=tools,
            max_steps=2,
            direct_tool_execution=True,
        )
        self._agent = answering_agent
        self._current_answer = ""
        self._current_claims = []
        self._register_tools()

    def _register_tools(self):
        self.tools.register(Tool(
            name="draft_answer",
            description=(
                "Generate an initial legal answer from the query and "
                "retrieved documents. Returns the answer text with citations."
            ),
            parameters={"query": "str"},
            func=self._tool_draft,
        ))
        self.tools.register(Tool(
            name="check_coverage",
            description=(
                "Check whether the current draft answer fully addresses all "
                "aspects of the user's query. Returns missing aspects."
            ),
            parameters={"query": "str", "answer": "str"},
            func=self._tool_check_coverage,
        ))
        self.tools.register(Tool(
            name="refine_answer",
            description=(
                "Improve the current answer by addressing the feedback. "
                "Returns the refined answer."
            ),
            parameters={"answer": "str", "feedback": "str"},
            func=self._tool_refine,
        ))

    async def _tool_draft(self, query: str = "", **kw) -> str:
        if self._current_answer:
            return f"Answer already drafted ({len(self._current_answer)} chars). Give Final Answer now."
        docs = self._context_docs
        import logging as _lg
        import time as _time
        _lg.getLogger(__name__).info("draft_answer: calling generate_answer with %d docs", len(docs) if docs else 0)
        result = self._agent.generate_answer(query, query, docs)
        _lg.getLogger(__name__).info("draft_answer: generate_answer returned OK")
        self._current_answer = result.get("answer_text", "")
        self._current_claims = result.get("claims", [])
        snippet = self._current_answer[:500]
        sources = result.get("sources", [])
        return (
            f"Draft answer ({len(self._current_answer)} chars, "
            f"{len(sources)} sources): {snippet}..."
        )

    async def _tool_check_coverage(
        self, query: str = "", answer: str = "", **kw
    ) -> str:
        if not answer:
            answer = self._current_answer
        prompt = (
            f"The user asked: \"{query}\"\n\n"
            f"The current answer is:\n{answer[:1500]}\n\n"
            f"Does this answer fully address all aspects of the question? "
            f"List any missing aspects or topics that should be covered. "
            f"If the answer is complete, say 'COMPLETE'."
        )
        resp = await groq_chat(
            "You evaluate legal answers for completeness. Be specific about what is missing.",
            prompt,
        )
        return resp or "COMPLETE"

    async def _tool_refine(
        self, answer: str = "", feedback: str = "", **kw
    ) -> str:
        if not answer:
            answer = self._current_answer
        docs_text = "\n".join(
            (d.get("content", "") or d.get("snippet", ""))[:300]
            for d in self._context_docs[:5]
        )
        prompt = (
            f"Improve this legal answer based on the feedback.\n\n"
            f"Current answer:\n{answer[:1500]}\n\n"
            f"Feedback: {feedback}\n\n"
            f"Available source documents:\n{docs_text[:2000]}\n\n"
            f"Write the improved answer with proper legal citations."
        )
        refined = await groq_chat(
            "You are a legal expert. Improve the answer. Include citations.",
            prompt,
        )
        if refined:
            self._current_answer = refined
        return f"Refined answer ({len(self._current_answer)} chars): {self._current_answer[:500]}..."

    # -- hooks --------------------------------------------------------------

    def _build_task_prompt(self, context):
        query = context.get("query", "")
        docs = context.get("documents", [])
        self._context_docs = docs
        doc_count = len(docs)
        return (
            f"Generate a comprehensive legal answer for: \"{query}\"\n"
            f"You have {doc_count} retrieved documents available.\n"
            f"You MUST use the draft_answer tool first. Then give Final Answer."
        )

    def _build_citations_from_docs(self):
        """Build citation dicts from retrieved documents for the UI."""
        citations = []
        for d in (self._context_docs or []):
            is_web = d.get("doc_type") == "web_result"
            citations.append({
                "doc_id": d.get("doc_id", ""),
                "title": d.get("title", "Unknown Source"),
                "source": d.get("source", "") if is_web else d.get("doc_type", "database"),
                "doc_type": d.get("doc_type", "document"),
                "similarity_score": d.get("similarity_score", d.get("score", 0.0)),
                "content": d.get("content", d.get("snippet", "")),
                "url": d.get("source", "") if is_web else "",
            })
        return citations

    def _extract_final_output(self, answer_text, context):
        try:
            data = _json.loads(answer_text)
            answer = data.get("answer", self._current_answer)
        except _json.JSONDecodeError:
            answer = self._current_answer
        if not answer:
            answer = answer_text
        claims = self._current_claims
        if claims and not isinstance(claims[0], dict):
            claims = [
                {"text": getattr(c, "text", str(c)),
                 "citations": getattr(c, "cited_doc_ids", [])}
                for c in claims
            ]
        return {
            "answer": answer,
            "citations": self._build_citations_from_docs(),
            "confidence": 0.7,
            "claims": claims,
        }

    def _fallback(self, context):
        if self._current_answer:
            return {
                "answer": self._current_answer,
                "citations": self._build_citations_from_docs(),
                "confidence": 0.5,
                "claims": self._current_claims if isinstance(self._current_claims, list) else [],
            }
        query = context.get("query", "")
        docs = context.get("documents", [])
        result = self._agent.generate_answer(query, query, docs)
        claims = result.get("claims", [])
        if claims and not isinstance(claims[0], dict):
            claims = [
                {"text": getattr(c, "text", str(c)),
                 "citations": getattr(c, "cited_doc_ids", [])}
                for c in claims
            ]
        return {
            "answer": result.get("answer_text", ""),
            "citations": result.get("sources", []),
            "confidence": result.get("confidence_score", 0.5),
            "claims": claims,
        }
