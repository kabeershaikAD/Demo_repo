"""
Rule-Based Orchestrator - Lower bound baseline
Demonstrates that simple rules are fast and free but lack flexibility
"""

import logging
import re
from typing import Dict, List, Any, Optional

from core.base_orchestrator import BaseOrchestrator, OrchestrationDecision

logger = logging.getLogger(__name__)

class RuleBasedOrchestrator(BaseOrchestrator):
    """
    Simple rule-based orchestration using if-then logic.
    
    This serves as a lower-bound baseline showing that:
    1. Simple rules are fast and free
    2. But lack flexibility for complex queries
    3. Cannot adapt to novel query patterns
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rules = self._initialize_rules()
        
    def _initialize_rules(self) -> List[Dict]:
        """Define routing rules"""
        return [
            {
                "name": "simple_factual",
                "condition": lambda q: len(q.split()) < 10 and "?" in q,
                "agents": ["retriever", "answering"],
                "description": "Short factual questions"
            },
            {
                "name": "comparison",
                "condition": lambda q: any(word in q.lower() for word in ["compare", "difference", "vs", "versus"]),
                "agents": ["booster", "retriever", "answering", "verifier"],
                "description": "Comparative queries need full pipeline"
            },
            {
                "name": "complex_analytical",
                "condition": lambda q: any(word in q.lower() for word in ["analyze", "explain", "implications", "impact"]),
                "agents": ["booster", "retriever", "answering", "verifier"],
                "description": "Analytical queries need enhancement and verification"
            },
            {
                "name": "definition",
                "condition": lambda q: any(phrase in q.lower() for phrase in ["what is", "define", "definition of"]),
                "agents": ["retriever", "answering"],
                "description": "Definition queries are straightforward"
            },
            {
                "name": "procedural",
                "condition": lambda q: any(word in q.lower() for word in ["how to", "procedure", "steps", "process"]),
                "agents": ["booster", "retriever", "answering"],
                "description": "Procedural queries benefit from enhancement"
            },

            {
                "name": "default",
                "condition": lambda q: True,  # Catch-all
                "agents": ["retriever", "answering"],
                "description": "Default routing"
            }
        ]
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query using simple heuristics"""
        import time
        start = time.time()
        
        word_count = len(query.split())
        has_question_mark = "?" in query
        
        # Simple complexity estimation
        if word_count < 10:
            complexity = "simple"
        elif word_count < 20:
            complexity = "moderate"
        else:
            complexity = "complex"
        
        # Determine reasoning type
        query_lower = query.lower()
        if any(word in query_lower for word in ["what is", "define", "definition"]):
            reasoning_type = "factual"
        elif any(word in query_lower for word in ["compare", "difference", "vs", "versus"]):
            reasoning_type = "comparative"
        elif any(word in query_lower for word in ["how to", "procedure", "steps", "process"]):
            reasoning_type = "procedural"
        else:
            reasoning_type = "analytical"
        
        latency_ms = (time.time() - start) * 1000
        self._record_decision(0.0, latency_ms)  # Rules are free
        
        return {
            "complexity": complexity,
            "reasoning_type": reasoning_type,
            "word_count": word_count,
            "has_question": has_question_mark,
            "confidence": 0.8,  # Rules are deterministic
            "_metrics": {
                "latency_ms": latency_ms,
                "cost_usd": 0.0
            }
        }
    
    async def route_to_agents(self, query: str, analysis: Dict) -> List[str]:
        """Route using if-then rules"""
        import time
        start = time.time()
        
        # Try each rule in order
        for rule in self.rules:
            if rule["condition"](query):
                agent_sequence = rule["agents"]
                
                latency_ms = (time.time() - start) * 1000
                self._record_decision(0.0, latency_ms)
                
                logger.debug(f"Rule '{rule['name']}' matched: {rule['description']}")
                return agent_sequence
        
        # Should never reach here due to catch-all rule
        return ["retriever", "answering"]
    
    async def execute_workflow(self, query: str, agent_sequence: List[str]) -> Dict:
        """Execute the agent workflow (placeholder - actual implementation in main app)"""
        return {
            "query": query,
            "agent_sequence": agent_sequence,
            "status": "workflow_executed",
            "orchestrator": "RuleBased"
        }
    
    @property
    def cost_per_decision(self) -> float:
        return 0.0  # Rules are free
    
    @property
    def requires_api(self) -> bool:
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rule-based specific metrics"""
        base_metrics = super().get_metrics()
        base_metrics.update({
            "orchestrator": "Rule-Based",
            "num_rules": len(self.rules),
            "rule_names": [rule["name"] for rule in self.rules],
            "api_dependency": False
        })
        return base_metrics
    
    def visualize_rules(self) -> str:
        """Show all routing rules"""
        output = "Rule-Based Orchestrator Rules:\n"
        output += "=" * 40 + "\n"
        
        for rule in self.rules:
            output += f"Rule: {rule['name']}\n"
            output += f"  Description: {rule['description']}\n"
            output += f"  Agents: {' → '.join(rule['agents'])}\n\n"
        
        return output
    
    def test_rule_coverage(self, test_queries: List[str]) -> Dict:
        """Test which rules are triggered by test queries"""
        rule_usage = {rule['name']: 0 for rule in self.rules}
        
        for query in test_queries:
            for rule in self.rules:
                if rule['condition'](query):
                    rule_usage[rule['name']] += 1
                    break
        
        return rule_usage
