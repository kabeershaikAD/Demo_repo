"""
Base ReAct Agent for PEARL framework.

Implements the Thought -> Action -> Observation loop using Groq LLM
(llama-3.1-8b-instant) for reasoning.  Concrete agents subclass this
and register domain-specific tools.
"""

import json
import logging
import re
import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable

from core.tools import Tool, ToolRegistry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ReActStep:
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str


@dataclass
class AgentResult:
    output: Dict[str, Any]
    reasoning_trace: List[ReActStep]
    tools_used: List[str]
    steps_taken: int
    confidence: float
    duration_ms: float


# ---------------------------------------------------------------------------
# LLM helper  (Groq / llama-3.1-8b-instant)
# ---------------------------------------------------------------------------

_groq_client = None


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        try:
            from groq import Groq
            from config import config
            _groq_client = Groq(api_key=config.api.GROQ_API_KEY)
        except Exception as e:
            logger.warning(f"Groq client unavailable: {e}")
    return _groq_client


async def groq_chat(system: str, user: str, temperature: float = 0.0) -> str:
    """Send a chat completion request to Groq and return the text."""
    client = _get_groq_client()
    if client is None:
        return ""
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=512,
        )
        text = resp.choices[0].message.content.strip()
        return text
    except Exception as e:
        logger.error(f"Groq chat error: {e}")
        return ""


# ---------------------------------------------------------------------------
# Base ReAct Agent
# ---------------------------------------------------------------------------

class BaseReActAgent:
    """
    Base class for all ReAct agents.

    Subclasses must:
      1. Call ``super().__init__(...)`` with a name, tool registry, and
         system prompt.
      2. Register tools via ``self.tools.register(Tool(...))``.
      3. Override ``_build_task_prompt(context)`` to describe the current
         task from the context dictionary.
      4. Override ``_extract_final_output(answer_text, context)`` to convert
         the LLM final-answer string into a structured dict.
      5. Optionally override ``_fallback(context)`` for non-LLM behaviour.
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: Optional[ToolRegistry] = None,
        max_steps: int = 3,
        direct_tool_execution: bool = False,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or ToolRegistry()
        self.max_steps = max_steps
        self.direct_tool_execution = direct_tool_execution

    # ---- public API -------------------------------------------------------

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        start = time.time()
        history: List[ReActStep] = []
        tools_used: List[str] = []

        task_prompt = self._build_task_prompt(context)

        # Direct execution mode: skip LLM, execute primary tool immediately
        if self.direct_tool_execution and self.tools.names():
            primary = self.tools.names()[0]
            tool = self.tools.get(primary)
            tool_input = self._default_tool_input(context)

            logger.info("[%s] Direct execution: %s", self.name, primary)
            try:
                observation = await tool.func(**tool_input)
                tools_used.append(primary)
            except Exception as e:
                observation = f"Tool error: {e}"

            step = ReActStep(
                thought=f"Executing {primary} to process the query.",
                action=primary,
                action_input=tool_input,
                observation=str(observation)[:2000],
            )
            history.append(step)

            output = self._extract_final_output(str(observation), context)
            duration = (time.time() - start) * 1000
            return AgentResult(
                output=output,
                reasoning_trace=history,
                tools_used=tools_used,
                steps_taken=1,
                confidence=output.get("confidence", 0.7),
                duration_ms=round(duration, 1),
            )

        for step_idx in range(self.max_steps):
            user_msg = self._compose_user_message(task_prompt, history)

            if step_idx == self.max_steps - 1 and history:
                user_msg += (
                    "\n\nCRITICAL: This is your FINAL step. You MUST respond "
                    "with Final Answer: now. Summarize your results as JSON."
                )

            sys_msg = self._compose_system_message()

            raw = await groq_chat(sys_msg, user_msg)
            if not raw:
                logger.warning(f"[{self.name}] Empty LLM response at step {step_idx}")
                break

            parsed = self._parse_llm_output(raw)
            logger.info("[%s] Step %d parsed: action=%s, has_final=%s",
                        self.name, step_idx, parsed.get("action", "N/A"),
                        bool(parsed.get("final_answer")))

            if parsed.get("final_answer") and not tools_used and self.tools.names():
                first_tool = self.tools.names()[0]
                logger.info("[%s] Forcing tool '%s' (no tools used yet)", self.name, first_tool)
                parsed = {
                    "thought": parsed.get("final_answer", "Need to use primary tool first."),
                    "action": first_tool,
                    "action_input": self._default_tool_input(context),
                }

            if parsed.get("final_answer"):
                output = self._extract_final_output(
                    parsed["final_answer"], context
                )
                duration = (time.time() - start) * 1000
                return AgentResult(
                    output=output,
                    reasoning_trace=history,
                    tools_used=tools_used,
                    steps_taken=step_idx + 1,
                    confidence=output.get("confidence", 0.7),
                    duration_ms=round(duration, 1),
                )

            thought = parsed.get("thought", "")
            action_name = parsed.get("action", "")
            action_input = parsed.get("action_input", {})

            logger.info("[%s] Executing tool: %s", self.name, action_name)
            tool = self.tools.get(action_name)
            if tool is None:
                observation = f"Unknown tool '{action_name}'. Available: {self.tools.names()}"
            else:
                try:
                    observation = await tool.func(**action_input)
                    tools_used.append(action_name)
                except Exception as e:
                    observation = f"Tool error: {e}"

            history.append(
                ReActStep(
                    thought=thought,
                    action=action_name,
                    action_input=action_input,
                    observation=str(observation)[:2000],
                )
            )

        logger.info(f"[{self.name}] Max steps reached, using fallback")
        output = self._fallback(context)
        duration = (time.time() - start) * 1000
        return AgentResult(
            output=output,
            reasoning_trace=history,
            tools_used=tools_used,
            steps_taken=self.max_steps,
            confidence=output.get("confidence", 0.5),
            duration_ms=round(duration, 1),
        )

    # ---- prompt construction ----------------------------------------------

    def _compose_system_message(self) -> str:
        tool_block = self.tools.schema_prompt()
        return (
            f"{self.system_prompt}\n\n"
            "You have access to the following tools:\n"
            f"{tool_block}\n\n"
            "Respond in EXACTLY one of two formats:\n\n"
            "FORMAT 1 (use a tool):\n"
            "Thought: <your reasoning>\n"
            "Action: <tool_name>\n"
            "Action Input: <json object with parameters>\n\n"
            "FORMAT 2 (you are done):\n"
            "Thought: <your reasoning>\n"
            "Final Answer: <json object with your output>\n\n"
            "IMPORTANT: Always start with Thought. "
            "Action Input and Final Answer MUST be valid JSON. "
            "You MUST use at least one tool before giving Final Answer. "
            "After using a tool, you may give Final Answer on your next step."
        )

    def _compose_user_message(
        self, task: str, history: List[ReActStep]
    ) -> str:
        parts = [f"Task: {task}"]
        for i, step in enumerate(history, 1):
            parts.append(f"\nStep {i}:")
            parts.append(f"Thought: {step.thought}")
            parts.append(f"Action: {step.action}")
            parts.append(f"Action Input: {json.dumps(step.action_input)}")
            parts.append(f"Observation: {step.observation}")
        if history:
            parts.append("\nContinue from here:")
        return "\n".join(parts)

    # ---- response parsing -------------------------------------------------

    def _parse_llm_output(self, raw: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        thought_m = re.search(r"Thought:\s*(.+?)(?=\n(?:Action|Final))", raw, re.S)
        if thought_m:
            result["thought"] = thought_m.group(1).strip()

        final_m = re.search(r"Final Answer:\s*(.+)", raw, re.S)
        if final_m:
            result["final_answer"] = final_m.group(1).strip()
            return result

        action_m = re.search(r"Action:\s*(\S+)", raw)
        if action_m:
            result["action"] = action_m.group(1).strip()

        input_m = re.search(r"Action Input:\s*(.+?)(?=\n(?:Observation|$))", raw, re.S)
        if input_m:
            raw_input = input_m.group(1).strip()
            try:
                result["action_input"] = json.loads(raw_input)
            except json.JSONDecodeError:
                result["action_input"] = {"raw": raw_input}

        if not result.get("action"):
            result["final_answer"] = raw.strip()

        return result

    def _default_tool_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return default input for the first tool when forcing tool use."""
        return {"query": context.get("query", context.get("answer", ""))}

    # ---- subclass hooks ---------------------------------------------------

    def _build_task_prompt(self, context: Dict[str, Any]) -> str:
        raise NotImplementedError

    def _extract_final_output(
        self, answer_text: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"error": "No output produced", "confidence": 0.0}
