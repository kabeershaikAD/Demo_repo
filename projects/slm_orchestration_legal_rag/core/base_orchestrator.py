"""
Base Orchestrator Interface for SLM Orchestration Framework
All orchestrators must implement this interface for fair comparison
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

@dataclass
class OrchestrationDecision:
    """Standardized decision format from any orchestrator"""
    agent_sequence: List[str]
    reasoning: str
    confidence: float
    complexity: str  # simple, moderate, complex
    cost_usd: float
    latency_ms: float
    metadata: Dict[str, Any]

class BaseOrchestrator(ABC):
    """Base interface that all orchestrators must implement"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.total_decisions = 0
        self.total_cost = 0.0
        self.total_latency = 0.0
        
    @abstractmethod
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query complexity and requirements"""
        pass
    
    @abstractmethod
    async def route_to_agents(self, query: str, analysis: Dict) -> List[str]:
        """Determine which agents to use and in what order"""
        pass
    
    @abstractmethod
    async def execute_workflow(self, query: str, agent_sequence: List[str]) -> Dict:
        """Execute the agent workflow"""
        pass
    
    @property
    @abstractmethod
    def cost_per_decision(self) -> float:
        """Cost in USD per orchestration decision"""
        pass
    
    @property
    @abstractmethod
    def requires_api(self) -> bool:
        """Whether this orchestrator requires external API"""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics"""
        return {
            "orchestrator": self.name,
            "total_decisions": self.total_decisions,
            "total_cost_usd": round(self.total_cost, 4),
            "avg_cost_per_decision": round(self.cost_per_decision, 4),
            "avg_latency_ms": round(self.total_latency / max(self.total_decisions, 1), 2),
            "total_latency_ms": round(self.total_latency, 2),
            "requires_api": self.requires_api
        }
    
    def _record_decision(self, cost: float, latency: float):
        """Record decision metrics"""
        self.total_decisions += 1
        self.total_cost += cost
        self.total_latency += latency
