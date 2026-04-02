"""
Tool abstraction for PEARL ReAct agents.
Each tool wraps a concrete capability (search, generate, verify) that an agent
can invoke during its Thought-Action-Observation loop.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Callable, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, str]
    func: Callable  # async def func(**kwargs) -> str


class ToolRegistry:
    """Stores the set of tools available to a single agent."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def schema_prompt(self) -> str:
        """Return a formatted string describing all tools for the LLM system prompt."""
        lines = []
        for t in self._tools.values():
            params = ", ".join(f"{k}: {v}" for k, v in t.parameters.items())
            lines.append(f"  {t.name}({params}) - {t.description}")
        return "\n".join(lines)
