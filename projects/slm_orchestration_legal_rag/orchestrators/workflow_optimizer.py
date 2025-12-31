"""
PEARL: Workflow Optimization
Removes redundant agent calls and unnecessary steps

This implements the third component of PEARL:
1. Dependency pruning
2. Complexity-aware routing
3. Redundant agent call removal
"""

import logging
from typing import List, Dict, Any, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentDependency:
    """Represents agent dependencies"""
    agent: str
    requires: List[str]  # Agents that must run before this one
    optional_after: List[str]  # Agents that can run after this one
    conflicts_with: List[str]  # Agents that shouldn't run with this one

class WorkflowOptimizer:
    """
    Optimizes agent workflows by removing redundant calls and unnecessary steps.
    
    According to PEARL:
    - Dependency pruning: Remove agents that don't satisfy dependencies
    - Complexity-aware routing: Adjust workflow based on query complexity
    - Redundant call removal: Remove duplicate or unnecessary agent calls
    """
    
    def __init__(self):
        # Define agent dependencies
        self.dependencies = {
            "booster": AgentDependency(
                agent="booster",
                requires=[],
                optional_after=["retriever", "answering"],
                conflicts_with=[]
            ),
            "retriever": AgentDependency(
                agent="retriever",
                requires=[],
                optional_after=["answering", "verifier"],
                conflicts_with=[]
            ),
            "answering": AgentDependency(
                agent="answering",
                requires=["retriever"],  # Answering needs retrieval first
                optional_after=["verifier", "multilingual"],
                conflicts_with=[]
            ),
            "verifier": AgentDependency(
                agent="verifier",
                requires=["answering", "retriever"],  # Needs both
                optional_after=["multilingual"],
                conflicts_with=[]
            ),
            "multilingual": AgentDependency(
                agent="multilingual",
                requires=["answering"],  # Works on answer
                optional_after=[],
                conflicts_with=[]
            )
        }
    
    def optimize_workflow(
        self,
        agent_sequence: List[str],
        query: str,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Optimize agent workflow by:
        1. Removing redundant calls
        2. Ensuring dependencies are satisfied
        3. Pruning unnecessary agents based on complexity
        """
        
        # Step 1: Remove duplicates while preserving order
        optimized = self._remove_duplicates(agent_sequence)
        
        # Step 2: Ensure dependencies are satisfied
        optimized = self._enforce_dependencies(optimized)
        
        # Step 3: Complexity-aware pruning
        optimized = self._complexity_aware_pruning(optimized, query, analysis)
        
        # Step 4: Remove redundant calls
        optimized = self._remove_redundant_calls(optimized, analysis)
        
        logger.info(f"Workflow optimized: {agent_sequence} → {optimized}")
        
        return optimized
    
    def _remove_duplicates(self, sequence: List[str]) -> List[str]:
        """Remove duplicate agents while preserving order"""
        seen = set()
        result = []
        for agent in sequence:
            if agent not in seen:
                seen.add(agent)
                result.append(agent)
        return result
    
    def _enforce_dependencies(self, sequence: List[str]) -> List[str]:
        """Ensure all agent dependencies are satisfied"""
        result = []
        seen = set()
        
        for agent in sequence:
            if agent not in self.dependencies:
                # Unknown agent, skip or add at end
                if agent not in seen:
                    result.append(agent)
                    seen.add(agent)
                continue
            
            dep = self.dependencies[agent]
            
            # Check if all required agents are present
            missing_required = [req for req in dep.requires if req not in seen]
            
            if missing_required:
                # Add missing required agents first
                for req_agent in missing_required:
                    if req_agent not in seen:
                        result.append(req_agent)
                        seen.add(req_agent)
            
            # Add current agent
            if agent not in seen:
                result.append(agent)
                seen.add(agent)
        
        return result
    
    def _complexity_aware_pruning(self, sequence: List[str], query: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Prune agents based on query complexity.
        
        Simple queries don't need all agents.
        """
        complexity = analysis.get("complexity", "simple")
        reasoning_type = analysis.get("reasoning_type", "factual")
        
        # For very simple queries, minimal workflow
        if complexity == "simple" and reasoning_type == "factual":
            # Only need retriever and answering
            minimal = ["retriever", "answering"]
            return [a for a in sequence if a in minimal]
        
        # For moderate complexity, can skip some agents
        if complexity == "moderate":
            # Can skip multilingual if not needed
            if "multilingual" in sequence and not self._needs_multilingual(query):
                sequence = [a for a in sequence if a != "multilingual"]
        
        return sequence
    
    def _needs_multilingual(self, query: str) -> bool:
        """Check if query needs multilingual support"""
        # Simple heuristic: check for non-English characters or language indicators
        query_lower = query.lower()
        multilingual_indicators = ["hindi", "tamil", "telugu", "marathi", "gujarati", "bengali"]
        return any(indicator in query_lower for indicator in multilingual_indicators)
    
    def _remove_redundant_calls(self, sequence: List[str], analysis: Dict[str, Any]) -> List[str]:
        """
        Remove redundant agent calls based on analysis.
        
        Examples:
        - If query doesn't need enhancement, remove booster
        - If query doesn't need verification, remove verifier
        """
        requires_enhancement = analysis.get("requires_enhancement", False)
        requires_verification = analysis.get("requires_verification", False)
        
        optimized = sequence.copy()
        
        # Remove booster if not needed
        if not requires_enhancement and "booster" in optimized:
            # Check if query is already well-formed
            if self._is_well_formed_query(analysis):
                optimized.remove("booster")
                logger.info("Removed redundant booster call")
        
        # Remove verifier if not needed
        if not requires_verification and "verifier" in optimized:
            # Only remove if query is simple factual
            if analysis.get("complexity") == "simple" and analysis.get("reasoning_type") == "factual":
                optimized.remove("verifier")
                logger.info("Removed redundant verifier call")
        
        return optimized
    
    def _is_well_formed_query(self, analysis: Dict[str, Any]) -> bool:
        """Check if query is well-formed and doesn't need enhancement"""
        complexity = analysis.get("complexity", "simple")
        confidence = analysis.get("confidence", 0.0)
        
        # Well-formed if simple/moderate complexity and high confidence
        return complexity in ["simple", "moderate"] and confidence > 0.7
    
    def validate_workflow(self, sequence: List[str]) -> tuple[bool, List[str]]:
        """
        Validate workflow and return (is_valid, issues)
        """
        issues = []
        
        # Check for duplicate agents
        if len(sequence) != len(set(sequence)):
            issues.append("Duplicate agents in sequence")
        
        # Check dependencies
        seen = set()
        for agent in sequence:
            if agent in self.dependencies:
                dep = self.dependencies[agent]
                missing = [req for req in dep.requires if req not in seen]
                if missing:
                    issues.append(f"{agent} requires {missing} but they're not present")
            seen.add(agent)
        
        # Check conflicts
        for i, agent1 in enumerate(sequence):
            if agent1 in self.dependencies:
                dep1 = self.dependencies[agent1]
                for agent2 in sequence[i+1:]:
                    if agent2 in dep1.conflicts_with:
                        issues.append(f"{agent1} conflicts with {agent2}")
        
        return len(issues) == 0, issues








