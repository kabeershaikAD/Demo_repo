"""
ReAct-style Research Agent - Uses tools in a loop to answer legal questions.
One LLM that can call search_legal_docs, rewrite_query, generate_answer, verify_claims, detect_language.
"""

import asyncio
import json
import re
import logging
from typing import Dict, Any, List, Optional

from agent_tools import AgentToolRunner, TOOL_SCHEMAS

logger = logging.getLogger(__name__)

REACT_PROMPT = """You are a legal research assistant. Answer the user question using the tools below. You may call tools multiple times (e.g. search, then rewrite and search again, then generate answer, then verify).

Tools:
- search_legal_docs(query, k=5): Search legal database. Returns list of documents.
- rewrite_query(query): Rewrite vague query for better search.
- generate_answer(query, documents): Generate answer from retrieved documents.
- verify_claims(answer, claims, documents): Verify answer against documents.
- detect_language(query): Detect query language.

Respond with exactly one of:
1) Action: <tool_name>
Action Input: <json with params>
2) Final Answer: <your answer to the user>

Current step: {step}. You have already taken these steps:
{history}

User question: {query}
"""


class ResearchAgent:
    def __init__(self, tool_runner: AgentToolRunner, llm_invoke_fn):
        self.tool_runner = tool_runner
        self.llm_invoke = llm_invoke_fn
        self.max_steps = 8

    async def run(self, query: str) -> Dict[str, Any]:
        self.tool_runner.set_context(query)
        history = []
        for step in range(1, self.max_steps + 1):
            prompt = REACT_PROMPT.format(step=step, history="\n".join(history) or "None yet.", query=query)
            response = await self.llm_invoke(prompt)
            response = (response or "").strip()
            if "Final Answer:" in response:
                final = response.split("Final Answer:")[-1].strip()
                ctx = self.tool_runner.get_context()
                return {
                    "answer": final,
                    "citations": ctx.get("citations", []),
                    "documents": ctx.get("documents", []),
                    "confidence": 0.7,
                    "agent_sequence": ["research_agent"],
                    "research_steps": step,
                    "history": history,
                }
            action_match = re.search(r"Action:\s*(\w+)", response, re.I)
            input_match = re.search(r"Action Input:\s*(\{.*?\})", response, re.DOTALL | re.I)
            if not action_match:
                history.append("No valid action; assuming done.")
                ctx = self.tool_runner.get_context()
                return {"answer": ctx.get("answer", "I could not complete the research."), "citations": ctx.get("citations", []), "documents": ctx.get("documents", []), "confidence": 0.5, "agent_sequence": ["research_agent"], "research_steps": step, "history": history}
            tool_name = action_match.group(1).strip()
            try:
                inp = json.loads(input_match.group(1)) if input_match else {}
            except json.JSONDecodeError:
                inp = {}
            obs = await self.tool_runner.run_tool(tool_name, **inp)
            history.append(f"Step {step}: Action={tool_name}, Observation={obs[:500]}")
        ctx = self.tool_runner.get_context()
        return {"answer": ctx.get("answer", "Max steps reached."), "citations": ctx.get("citations", []), "documents": ctx.get("documents", []), "confidence": 0.5, "agent_sequence": ["research_agent"], "research_steps": self.max_steps, "history": history}
