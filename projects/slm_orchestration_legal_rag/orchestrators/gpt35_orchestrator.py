"""
GPT-3.5-turbo Orchestrator -- zero-shot iterative orchestration via API.

Uses the same iterative prompt format as the SLM orchestrators for a fair
comparison, but calls GPT-3.5-turbo instead of a local model.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional

from core.base_orchestrator import BaseOrchestrator, OrchestrationDecision

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

VALID_AGENTS = {"booster", "retriever", "answering", "verifier"}
MAX_STEPS = 6

SYSTEM_PROMPT = """You are an orchestrator for a multi-agent legal RAG system.

Available agents:
- booster: Improves vague or short queries with legal terminology before retrieval
- retriever: Searches the legal document database for relevant passages
- answering: Generates a comprehensive answer from retrieved documents
- verifier: Validates citations and cross-checks facts in the answer

At each step you see the user's query and the agents already called.
Respond with EXACTLY ONE word: the next agent to call, or "done" to stop.

Routing guidelines:
- Simple factual queries: retriever -> answering -> done
- Vague / short queries (< 5 words): booster first
- Complex / comparative queries: booster -> retriever -> answering -> verifier -> done
- Queries needing citation checks: add verifier before done
- Never call the same agent twice
- Always include retriever and answering"""


class GPT35Orchestrator(BaseOrchestrator):
    """
    GPT-3.5-turbo orchestrator using iterative step-by-step routing.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("openai_api_key")
        self.model = "gpt-3.5-turbo"
        self.cost_per_1k_input = 0.0005
        self.cost_per_1k_output = 0.0015
        self.total_api_cost = 0.0
        self._step_latencies: List[float] = []

        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai package not installed")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        self.client = OpenAI(api_key=self.api_key)

    async def analyze_query(self, query: str) -> Dict[str, Any]:
        return {"complexity": "unknown", "reasoning_type": "unknown", "confidence": 0.5}

    async def route_to_agents(self, query: str, analysis: Dict) -> List[str]:
        history: List[str] = []
        self._step_latencies = []
        total_start = time.time()

        for step_num in range(1, MAX_STEPS + 1):
            hist_str = ", ".join(history) if history else "none"
            user_msg = f"Query: \"{query}\"\nAgents called so far: [{hist_str}]\nWhat is the next agent to call?"

            step_start = time.time()
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    temperature=0.0,
                    max_tokens=10,
                )
                step_ms = (time.time() - step_start) * 1000
                self._step_latencies.append(step_ms)

                usage = resp.usage
                cost = (usage.prompt_tokens / 1000 * self.cost_per_1k_input +
                        usage.completion_tokens / 1000 * self.cost_per_1k_output)
                self.total_api_cost += cost

                raw = resp.choices[0].message.content.strip().lower()
            except Exception as e:
                logger.error(f"GPT-3.5 API error at step {step_num}: {e}")
                break

            next_action = None
            for token in list(VALID_AGENTS) + ["done"]:
                if token in raw:
                    next_action = token
                    break
            if next_action is None:
                next_action = "done"

            logger.info(f"  Step {step_num}: [{hist_str}] -> {raw} (parsed: {next_action}, {step_ms:.0f}ms)")

            if next_action == "done":
                break
            if next_action in VALID_AGENTS and next_action not in history:
                history.append(next_action)
            elif next_action in history:
                continue
            else:
                break

        if "retriever" not in history:
            history.insert(0, "retriever")
        if "answering" not in history:
            pos = history.index("retriever") + 1
            history.insert(pos, "answering")

        total_ms = (time.time() - total_start) * 1000
        self._record_decision(self.total_api_cost, total_ms)
        logger.info(f"  Final: {history} ({total_ms:.0f}ms, ${self.total_api_cost:.4f})")
        return history

    async def execute_workflow(self, query: str, agent_sequence: List[str]) -> Dict:
        return {"query": query, "agent_sequence": agent_sequence, "orchestrator": "GPT35"}

    @property
    def cost_per_decision(self) -> float:
        if self.total_decisions == 0:
            return 0.003
        return self.total_api_cost / self.total_decisions

    @property
    def requires_api(self) -> bool:
        return True

    def get_metrics(self) -> Dict[str, Any]:
        base = super().get_metrics()
        base.update({
            "model_name": self.model,
            "total_api_cost": self.total_api_cost,
            "step_latencies_ms": self._step_latencies,
            "orchestration_type": "iterative_api",
        })
        return base
