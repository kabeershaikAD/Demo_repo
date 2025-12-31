"""
Orchestrators package for SLM Orchestration Framework
Contains different orchestration strategies for comparison
"""

# Lazy imports to avoid requiring torch/transformers at module level
# Import only when needed to prevent dependency issues

__all__ = [
    'FlanT5Orchestrator',
    'GPT4Orchestrator', 
    'RuleBasedOrchestrator',
    'NoOrchestrator',
    'WorkflowOptimizer'
]

def __getattr__(name):
    """Lazy import orchestrators only when accessed"""
    if name == 'FlanT5Orchestrator':
        from .flan_t5_orchestrator import FlanT5Orchestrator
        return FlanT5Orchestrator
    elif name == 'GPT4Orchestrator':
        from .gpt4_orchestrator import GPT4Orchestrator
        return GPT4Orchestrator
    elif name == 'RuleBasedOrchestrator':
        from .rule_orchestrator import RuleBasedOrchestrator
        return RuleBasedOrchestrator
    elif name == 'NoOrchestrator':
        from .no_orchestrator import NoOrchestrator
        return NoOrchestrator
    elif name == 'WorkflowOptimizer':
        from .workflow_optimizer import WorkflowOptimizer
        return WorkflowOptimizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
