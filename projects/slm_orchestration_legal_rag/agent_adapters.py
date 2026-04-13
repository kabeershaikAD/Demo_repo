"""
Agent Adapters for SLM Orchestration Framework.

Each adapter wraps a ReAct agent and provides a simple ``process()`` API
that the orchestration app can call.  The adapter extracts the structured
output from ``AgentResult`` and also stores the reasoning trace so the UI
can display it.
"""

import asyncio
import logging
from typing import Dict, Any, List

from core.base_react_agent import AgentResult

logger = logging.getLogger(__name__)


class AgentAdapter:
    """Base adapter that wraps a ReAct agent."""

    def __init__(self, agent):
        self.agent = agent
        self.initialized = False
        self.last_trace: List = []

    async def initialize(self):
        if hasattr(self.agent, "_initialize_model"):
            self.agent._initialize_model()
        elif hasattr(self.agent, "initialize"):
            await self.agent.initialize()
        self.initialized = True

    async def process(self, *args, **kwargs):
        raise NotImplementedError


class BoosterAdapter(AgentAdapter):
    """Adapter for the Booster ReAct agent."""

    def __init__(self, agent):
        super().__init__(agent)
        from booster_agent import BoosterReActAgent, PromptBooster
        if isinstance(agent, PromptBooster):
            self._react = BoosterReActAgent(agent)
        else:
            self._react = None

    async def process(self, query: str) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()

        if self._react is not None:
            try:
                result: AgentResult = await self._react.run({"query": query})
                self.last_trace = result.reasoning_trace
                out = result.output
                out.setdefault("boosted_query", query)
                out.setdefault("retrieval_mode", "both")
                out.setdefault("top_k", 5)
                out.setdefault("confidence", 0.7)
                out.setdefault("reasoning", "ReAct agent")
                return out
            except Exception as e:
                logger.error(f"BoosterReAct failed, using fallback: {e}")

        if hasattr(self.agent, "generate_decision"):
            decision = self.agent.generate_decision(query)
            boosted = decision.boosted_query if decision.need_boost else query
            return {
                "boosted_query": boosted or query,
                "retrieval_mode": getattr(decision, "retrieval_mode", "both"),
                "top_k": getattr(decision, "top_k", 5),
                "confidence": getattr(decision, "confidence", 0.7),
                "reasoning": getattr(decision, "reasoning", "Query enhanced"),
                "require_human_review": getattr(decision, "require_human_review", False),
            }
        return {
            "boosted_query": query,
            "retrieval_mode": "both",
            "top_k": 5,
            "confidence": 0.5,
            "reasoning": "No enhancement available",
        }


class RetrieverAdapter(AgentAdapter):
    """Adapter for the Retriever ReAct agent."""

    def __init__(self, agent):
        super().__init__(agent)
        from retriever_agent import RetrieverReActAgent, RetrieverAgent
        if isinstance(agent, RetrieverAgent):
            self._react = RetrieverReActAgent(agent)
        else:
            self._react = None

    async def process(self, query: str, k: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()

        if self._react is not None:
            try:
                ctx = {"query": query, "top_k": k}
                if filters and filters.get("doc_type"):
                    ctx["retrieval_mode"] = filters["doc_type"]
                result: AgentResult = await self._react.run(ctx)
                self.last_trace = result.reasoning_trace
                out = result.output
                out.setdefault("documents", [])
                out.setdefault("scores", [])
                out.setdefault("metadata", {})
                return out
            except Exception as e:
                logger.error(f"RetrieverReAct failed, using fallback: {e}")

        if hasattr(self.agent, "retrieve"):
            result = self.agent.retrieve(query, k=k, filters=filters)
            all_documents = []
            if hasattr(result, "statutes"):
                all_documents.extend(result.statutes)
            if hasattr(result, "judgments"):
                all_documents.extend(result.judgments)
            documents = []
            for doc in all_documents:
                if hasattr(doc, "__dict__"):
                    doc_dict = doc.__dict__
                else:
                    doc_dict = {
                        "doc_id": getattr(doc, "doc_id", "unknown"),
                        "content": getattr(doc, "content", ""),
                        "title": getattr(doc, "title", "Untitled"),
                        "doc_type": getattr(doc, "doc_type", "document"),
                        "similarity_score": getattr(doc, "similarity_score", 0.0),
                    }
                documents.append(doc_dict)
            return {
                "documents": documents,
                "scores": [doc.get("similarity_score", 0.0) for doc in documents],
                "metadata": result.metadata if hasattr(result, "metadata") else {},
            }
        return {"documents": [], "scores": [], "metadata": {}}


class AnsweringAdapter(AgentAdapter):
    """Adapter for the Answering ReAct agent."""

    def __init__(self, agent):
        super().__init__(agent)
        from answering_agent import AnsweringReActAgent, AnsweringAgent
        if isinstance(agent, AnsweringAgent):
            self._react = AnsweringReActAgent(agent)
        else:
            self._react = None

    async def process(self, query: str, documents: List[Dict] = None) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()

        if self._react is not None:
            try:
                ctx = {"query": query, "documents": documents or []}
                result: AgentResult = await self._react.run(ctx)
                self.last_trace = result.reasoning_trace
                out = result.output
                out.setdefault("answer", "No answer generated")
                out.setdefault("citations", [])
                out.setdefault("confidence", 0.5)
                out.setdefault("claims", [])
                return out
            except Exception as e:
                logger.error(f"AnsweringReAct failed, using fallback: {e}")

        if hasattr(self.agent, "generate_answer"):
            result = self.agent.generate_answer(query, query, documents or [])
            claims = result.get("claims", [])
            if claims and not isinstance(claims[0], dict):
                claims = [
                    {"text": getattr(c, "text", str(c)),
                     "citations": getattr(c, "cited_doc_ids", [])}
                    for c in claims
                ]
            return {
                "answer": result.get("answer_text", "No answer generated"),
                "citations": result.get("sources", []),
                "confidence": result.get("confidence_score", 0.5),
                "claims": claims,
            }
        return {"answer": "Answer generation not available", "citations": [], "confidence": 0.0, "claims": []}


class VerifierAdapter(AgentAdapter):
    """Adapter for the Verifier ReAct agent."""

    def __init__(self, agent):
        super().__init__(agent)
        from citation_verifier import VerifierReActAgent, CitationVerifier
        if isinstance(agent, CitationVerifier):
            self._react = VerifierReActAgent(agent)
        else:
            self._react = None

    async def process(self, answer: str, citations: List[Dict] = None,
                      claims: List[Dict] = None, retrieved_docs: List[Dict] = None) -> Dict[str, Any]:
        if not self.initialized:
            await self.initialize()

        if self._react is not None:
            try:
                ctx = {
                    "answer": answer,
                    "claims": claims or [],
                    "documents": retrieved_docs or citations or [],
                }
                result: AgentResult = await self._react.run(ctx)
                self.last_trace = result.reasoning_trace
                out = result.output
                out.setdefault("verified_answer", answer)
                out.setdefault("verification_score", 0.5)
                out.setdefault("claims_verified", 0)
                out.setdefault("total_claims", 0)
                out.setdefault("issues", [])
                return out
            except Exception as e:
                logger.error(f"VerifierReAct failed, using fallback: {e}")

        if hasattr(self.agent, "verify"):
            try:
                use_explicit = claims and retrieved_docs and len(claims) > 0 and len(retrieved_docs) > 0
                if not use_explicit:
                    claims = []
                    if citations:
                        for citation in citations:
                            if isinstance(citation, dict):
                                claims.append({
                                    "text": citation.get("title", citation.get("text", "")),
                                    "citations": [citation.get("doc_id", "")],
                                })
                    retrieved_docs = citations or []
                result = self.agent.verify(claims, retrieved_docs)
                if isinstance(result, list) and result:
                    scores = [r.get("confidence", 0.5) for r in result if isinstance(r, dict)]
                    verification_score = sum(scores) / len(scores) if scores else 0.5
                    return {
                        "verified_answer": answer,
                        "verification_score": verification_score,
                        "claims_verified": len([r for r in result if isinstance(r, dict) and r.get("supported")]),
                        "total_claims": len(result),
                        "issues": [],
                    }
                return {
                    "verified_answer": answer,
                    "verification_score": 0.5,
                    "claims_verified": 0,
                    "total_claims": 0,
                    "issues": ["No claims to verify"],
                }
            except Exception as e:
                return {
                    "verified_answer": answer,
                    "verification_score": 0.5,
                    "claims_verified": 0,
                    "total_claims": 0,
                    "issues": [f"Verification error: {str(e)}"],
                }
        return {
            "verified_answer": answer,
            "verification_score": 0.5,
            "claims_verified": 0,
            "total_claims": 0,
            "issues": [],
        }


