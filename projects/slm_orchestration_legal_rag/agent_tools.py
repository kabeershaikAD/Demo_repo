"""
Agent Tools for PEARL - Expose pipeline capabilities as callable tools.
Used by the ReAct research agent to decide when to search, rewrite, verify, etc.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

TOOL_SCHEMAS = [
    {"name": "search_legal_docs", "description": "Search the legal document database. Returns relevant statutes and judgments.", "parameters": {"query": "str", "k": "int (default 5)"}},
    {"name": "rewrite_query", "description": "Rewrite or expand a vague query into a clearer legal search query.", "parameters": {"query": "str"}},
    {"name": "generate_answer", "description": "Generate a legal answer from the user query and retrieved documents.", "parameters": {"query": "str", "documents": "list"}},
    {"name": "verify_claims", "description": "Verify that claims in an answer are supported by retrieved documents.", "parameters": {"answer": "str", "claims": "list", "documents": "list"}},
    {"name": "detect_language", "description": "Detect the language of the user query.", "parameters": {"query": "str"}},
]


class AgentToolRunner:
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self._context = {"documents": [], "claims": []}

    def set_context(self, query: str, documents: Optional[List[Dict]] = None):
        self._context = {"query": query, "documents": documents or [], "claims": []}

    async def run_tool(self, name: str, **kwargs) -> str:
        try:
            if name == "search_legal_docs":
                query = kwargs.get("query", self._context.get("query", ""))
                k = int(kwargs.get("k", 5))
                retriever = self.agents.get("retriever")
                if not retriever: return "Error: Retriever not available."
                result = await retriever.process(query, k=k)
                docs = result.get("documents", [])
                self._context["documents"] = docs
                return "Retrieved " + str(len(docs)) + " documents. " + "; ".join([d.get("title", "?")[:50] for d in docs[:5]])
            if name == "rewrite_query":
                query = kwargs.get("query", self._context.get("query", ""))
                booster = self.agents.get("booster")
                if not booster: return "Rewritten: " + query
                result = await booster.process(query)
                self._context["enhanced_query"] = result.get("boosted_query", query)
                return "Rewritten query: " + result.get("boosted_query", query)
            if name == "generate_answer":
                query = kwargs.get("query", self._context.get("query", ""))
                documents = kwargs.get("documents") or self._context.get("documents", [])
                answering = self.agents.get("answering")
                if not answering: return "Error: Answering agent not available."
                result = await answering.process(query, documents)
                self._context["answer"] = result.get("answer", "")
                self._context["citations"] = result.get("citations", [])
                self._context["claims"] = result.get("claims", [])
                return "Answer: " + (result.get("answer", "")[:1500] or "No answer.")
            if name == "verify_claims":
                answer = kwargs.get("answer") or self._context.get("answer", "")
                claims = kwargs.get("claims") or self._context.get("claims", [])
                documents = kwargs.get("documents") or self._context.get("documents", [])
                verifier = self.agents.get("verifier")
                if not verifier: return "Verifier not available."
                result = await verifier.process(answer, citations=documents, claims=claims or None, retrieved_docs=documents or None)
                return "Verification score: " + str(round(result.get("verification_score", 0.5), 2))
            if name == "detect_language":
                query = kwargs.get("query", self._context.get("query", ""))
                multi = self.agents.get("multilingual")
                if not multi: return "Language: en"
                result = await multi.process(query)
                return "Language: " + result.get("language", "en") + "; Translated: " + (result.get("translated_query", "")[:100] or query[:100])
            return "Unknown tool: " + name
        except Exception as e:
            logger.exception("Tool %s failed", name)
            return "Error: " + str(e)

    def get_context(self):
        return dict(self._context)
