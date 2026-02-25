"""
Agent Adapters for SLM Orchestration Framework
Makes existing agents compatible with the orchestration interface
"""

import asyncio
from typing import Dict, Any, List

class AgentAdapter:
    """Base adapter for making existing agents compatible with orchestration"""
    
    def __init__(self, agent):
        self.agent = agent
        self.initialized = False
    
    async def initialize(self):
        """Initialize the underlying agent"""
        if hasattr(self.agent, '_initialize_model'):
            self.agent._initialize_model()
        elif hasattr(self.agent, 'initialize'):
            await self.agent.initialize()
        self.initialized = True
    
    async def process(self, *args, **kwargs):
        """Process method - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process method")

class BoosterAdapter(AgentAdapter):
    """Adapter for PromptBooster agent"""
    
    async def process(self, query: str) -> Dict[str, Any]:
        """Process query using booster agent"""
        if not self.initialized:
            await self.initialize()
        
        # Use the existing booster's enhance_query method
        if hasattr(self.agent, 'enhance_query'):
            result = self.agent.enhance_query(query)
            return {
                "boosted_query": result.get("boosted_query", query),
                "confidence": result.get("confidence", 0.7),
                "reasoning": result.get("reasoning", "Query enhanced")
            }
        else:
            # Fallback
            return {
                "boosted_query": query,
                "confidence": 0.5,
                "reasoning": "No enhancement available"
            }

class RetrieverAdapter(AgentAdapter):
    """Adapter for RetrieverAgent"""
    
    async def process(self, query: str) -> Dict[str, Any]:
        """Process query using retriever agent"""
        if not self.initialized:
            await self.initialize()
        
        # Use the existing retriever's retrieve method
        if hasattr(self.agent, 'retrieve'):
            result = self.agent.retrieve(query, k=5)
            # Combine statutes and judgments into a single documents list
            all_documents = []
            if hasattr(result, 'statutes'):
                all_documents.extend(result.statutes)
            if hasattr(result, 'judgments'):
                all_documents.extend(result.judgments)
            
            # Convert RetrievedDocument objects to dictionaries
            documents = []
            for doc in all_documents:
                if hasattr(doc, '__dict__'):
                    doc_dict = doc.__dict__
                else:
                    doc_dict = {
                        'doc_id': getattr(doc, 'doc_id', 'unknown'),
                        'content': getattr(doc, 'content', ''),
                        'title': getattr(doc, 'title', 'Untitled'),
                        'doc_type': getattr(doc, 'doc_type', 'document'),
                        'similarity_score': getattr(doc, 'similarity_score', 0.0)
                    }
                documents.append(doc_dict)
            
            return {
                "documents": documents,
                "scores": [doc.get('similarity_score', 0.0) for doc in documents],
                "metadata": result.metadata if hasattr(result, 'metadata') else {}
            }
        else:
            return {
                "documents": [],
                "scores": [],
                "metadata": []
            }

class AnsweringAdapter(AgentAdapter):
    """Adapter for AnsweringAgent"""
    
    async def process(self, query: str, documents: List[Dict] = None) -> Dict[str, Any]:
        """Process query using answering agent"""
        if not self.initialized:
            await self.initialize()
        
        # Use the existing answering agent's generate_answer method
        if hasattr(self.agent, 'generate_answer'):
            # The method expects: user_query, enhanced_query, retrieved_docs
            result = self.agent.generate_answer(query, query, documents or [])
            return {
                "answer": result.get("answer_text", "No answer generated"),
                "citations": result.get("sources", []),
                "confidence": result.get("confidence_score", 0.5)
            }
        else:
            return {
                "answer": "Answer generation not available",
                "citations": [],
                "confidence": 0.0
            }

class VerifierAdapter(AgentAdapter):
    """Adapter for CitationVerifier"""
    
    async def process(self, answer: str, citations: List[Dict] = None) -> Dict[str, Any]:
        """Process answer using verifier agent"""
        if not self.initialized:
            await self.initialize()
        
        # Use the existing verifier's verify method
        # The verifier expects: claims (List[Dict]) and retrieved_docs (List[Dict])
        if hasattr(self.agent, 'verify'):
            try:
                # Convert citations to claims format if needed
                claims = []
                if citations:
                    # If citations are already in the right format, use them
                    if isinstance(citations[0], dict) and 'text' in citations[0]:
                        claims = citations
                    else:
                        # Convert citation list to claims format
                        for citation in citations:
                            if isinstance(citation, dict):
                                claims.append({
                                    'text': citation.get('title', citation.get('text', '')),
                                    'citations': [citation.get('doc_id', '')],
                                    'score': citation.get('similarity_score', 0.5)
                                })
                
                # Use citations as retrieved_docs for verification
                retrieved_docs = citations or []
                
                # Call verifier
                result = self.agent.verify(claims, retrieved_docs)
                
                # Process result - verifier returns List[Dict], not a single dict
                if isinstance(result, list) and result:
                    # Calculate average verification score
                    scores = [r.get('confidence', 0.5) if isinstance(r, dict) else 0.5 for r in result]
                    verification_score = sum(scores) / len(scores) if scores else 0.5
                    
                    # Check if all claims are supported
                    supported = all(r.get('supported', False) if isinstance(r, dict) else False for r in result)
                    
                    return {
                        "verified_answer": answer,
                        "verification_score": verification_score,
                        "claims_verified": len([r for r in result if isinstance(r, dict) and r.get('supported', False)]),
                        "total_claims": len(result),
                        "issues": []
                    }
                else:
                    # No claims to verify - use default confidence
                    # If we have citations but no claims, give moderate confidence
                    if citations and len(citations) > 0:
                        verification_score = 0.6  # Moderate confidence when citations exist
                    else:
                        verification_score = 0.5  # Default when no citations
                    
                    return {
                        "verified_answer": answer,
                        "verification_score": verification_score,
                        "claims_verified": 0,
                        "total_claims": 0,
                        "issues": ["No claims to verify"]
                    }
            except Exception as e:
                # If verification fails, return answer as-is
                return {
                    "verified_answer": answer,
                    "verification_score": 0.5,
                    "claims_verified": 0,
                    "total_claims": 0,
                    "issues": [f"Verification error: {str(e)}"]
                }
        else:
            return {
                "verified_answer": answer,
                "verification_score": 0.5,
                "claims_verified": 0,
                "total_claims": 0,
                "issues": []
            }

class MultilingualAdapter(AgentAdapter):
    """Adapter for MultilingualAgent"""
    
    async def process(self, query: str) -> Dict[str, Any]:
        """Process query using multilingual agent"""
        if not self.initialized:
            await self.initialize()
        
        # Use the existing multilingual agent's detect_and_translate method
        if hasattr(self.agent, 'detect_and_translate'):
            result = self.agent.detect_and_translate(query)
            return {
                "language": result.get("language", "en"),
                "translated_query": result.get("translated_query", query),
                "confidence": result.get("confidence", 0.8)
            }
        else:
            return {
                "language": "en",
                "translated_query": query,
                "confidence": 0.5
            }
