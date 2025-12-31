"""
No-Orchestration Baseline - Single-path RAG
Demonstrates the value of multi-agent orchestration by showing performance without it
"""

import logging
from typing import Dict, List, Any, Optional

from core.base_orchestrator import BaseOrchestrator, OrchestrationDecision

logger = logging.getLogger(__name__)

class NoOrchestrator(BaseOrchestrator):
    """
    Single-path RAG without orchestration.
    
    This baseline shows:
    1. What performance looks like without intelligent routing
    2. Always uses the same agent sequence
    3. No adaptation to query complexity
    4. Demonstrates the value of orchestration
    
    Pipeline: retriever → answering (always)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.fixed_sequence = ["retriever", "answering"]
        
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Minimal analysis - just return query as-is"""
        import time
        start = time.time()
        
        latency_ms = (time.time() - start) * 1000
        self._record_decision(0.0, latency_ms)
        
        return {
            "complexity": "unknown",  # No analysis
            "reasoning": "No orchestration - fixed pipeline",
            "confidence": 1.0,  # Always confident in fixed approach
            "_metrics": {
                "latency_ms": latency_ms,
                "cost_usd": 0.0
            }
        }
    
    async def route_to_agents(self, query: str, analysis: Dict) -> List[str]:
        """Always return fixed sequence"""
        import time
        start = time.time()
        
        self._record_decision(0.0, (time.time() - start) * 1000)
        
        logger.debug(f"No orchestration: using fixed sequence {self.fixed_sequence}")
        return self.fixed_sequence
    
    async def execute_workflow(self, query: str, agent_sequence: List[str]) -> Dict:
        """Execute simple retrieve → generate"""
        return {
            "query": query,
            "agent_sequence": agent_sequence,
            "status": "workflow_executed",
            "orchestrator": "NoOrchestration"
        }
    
    @property
    def cost_per_decision(self) -> float:
        return 0.0  # No orchestration cost
    
    @property
    def requires_api(self) -> bool:
        return False  # No orchestration API needed
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get no-orchestration specific metrics"""
        base_metrics = super().get_metrics()
        base_metrics.update({
            "orchestrator": "No Orchestration (Single RAG)",
            "fixed_sequence": self.fixed_sequence,
            "orchestration_type": "none",
            "api_dependency": False
        })
        return base_metrics
