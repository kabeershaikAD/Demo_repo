"""
GPT-4 Orchestrator - BASELINE for comparison
Demonstrates the cost-performance trade-offs of using large language models for orchestration
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional
import openai

from core.base_orchestrator import BaseOrchestrator, OrchestrationDecision

logger = logging.getLogger(__name__)

class GPT4Orchestrator(BaseOrchestrator):
    """
    GPT-4 based orchestration - BASELINE for comparison.
    
    This represents the current state-of-the-art approach used by
    AutoGen and MetaGPT frameworks.
    
    Key Characteristics:
    - High accuracy but expensive
    - Requires external API
    - Higher latency
    - Used as baseline for comparison
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("openai_api_key")
        self.model = config.get("model", "gpt-4")
        self.cost_per_1k_tokens = 0.03  # GPT-4 pricing (as of 2024)
        
        if not self.api_key:
            raise ValueError("OpenAI API key required for GPT-4 orchestrator")
        
        openai.api_key = self.api_key
        
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Use GPT-4 to analyze query complexity"""
        
        prompt = f"""
        Analyze this legal query and classify its complexity for multi-agent processing.
        
        Query: "{query}"
        
        Determine:
        1. Complexity level (simple/moderate/complex)
        2. Required reasoning type (factual/analytical/comparative/procedural)
        3. Estimated processing steps needed
        4. Whether query enhancement is needed
        5. Whether verification is needed
        
        Respond in JSON format:
        {{
            "complexity": "simple|moderate|complex",
            "reasoning_type": "factual|analytical|comparative|procedural",
            "estimated_steps": 1-5,
            "requires_enhancement": true|false,
            "requires_verification": true|false,
            "confidence": 0.0-1.0
        }}
        """
        
        start_time = time.time()
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert query analyzer for multi-agent legal systems."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Calculate cost
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1000) * self.cost_per_1k_tokens
            
            self._record_decision(cost, latency_ms)
            
            result = json.loads(response.choices[0].message.content)
            result["_metrics"] = {
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "tokens": tokens_used
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing query with GPT-4: {e}")
            return self._fallback_query_analysis(query)
    
    async def route_to_agents(self, query: str, analysis: Dict) -> List[str]:
        """Use GPT-4 to determine agent routing"""
        
        prompt = f"""
        Based on this query analysis, determine the optimal sequence of agents.
        
        Query: "{query}"
        Analysis: {json.dumps(analysis)}
        
        Available agents:
        - booster: Improves vague queries with legal terminology
        - retriever: Searches document database
        - answering: Creates comprehensive answers
        - verifier: Validates citations and facts
        - multilingual: Handles language detection and translation
        - updater: Checks for recent updates
        
        Routing rules:
        - Simple factual queries: retriever → answering
        - Complex analytical queries: booster → retriever → answering → verifier
        - Comparative queries: booster → retriever → answering → verifier
        - Multilingual queries: multilingual → booster → retriever → answering
        - Procedural queries: booster → retriever → answering
        
        Respond with JSON array of agent names in execution order:
        ["agent1", "agent2", "agent3"]
        """
        
        start_time = time.time()
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert agent router for legal AI systems."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            latency_ms = (time.time() - start_time) * 1000
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1000) * self.cost_per_1k_tokens
            
            self._record_decision(cost, latency_ms)
            
            agent_sequence = json.loads(response.choices[0].message.content)
            return agent_sequence
            
        except Exception as e:
            logger.error(f"Error routing with GPT-4: {e}")
            return self._fallback_routing(query, analysis)
    
    async def execute_workflow(self, query: str, agent_sequence: List[str]) -> Dict:
        """Execute the agent workflow (placeholder - actual implementation in main app)"""
        return {
            "query": query,
            "agent_sequence": agent_sequence,
            "status": "workflow_executed",
            "orchestrator": "GPT4"
        }
    
    def _fallback_query_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback analysis when API fails"""
        return {
            "complexity": "moderate",
            "reasoning_type": "factual",
            "estimated_steps": 3,
            "requires_enhancement": True,
            "requires_verification": True,
            "confidence": 0.5
        }
    
    def _fallback_routing(self, query: str, analysis: Dict) -> List[str]:
        """Fallback routing when API fails"""
        return ["retriever", "answering"]
    
    @property
    def cost_per_decision(self) -> float:
        """Average cost per orchestration decision"""
        if self.total_decisions == 0:
            return 0.02  # Estimated
        return self.total_cost / self.total_decisions
    
    @property
    def requires_api(self) -> bool:
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get GPT-4 specific metrics"""
        base_metrics = super().get_metrics()
        base_metrics.update({
            "model_name": self.model,
            "api_dependency": True,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "total_tokens": int(self.total_cost / self.cost_per_1k_tokens * 1000) if self.cost_per_1k_tokens > 0 else 0
        })
        return base_metrics
