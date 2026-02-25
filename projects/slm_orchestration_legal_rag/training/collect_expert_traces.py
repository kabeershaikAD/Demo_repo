"""
PEARL: Expert Trace Collection Pipeline
Captures orchestration traces from GPT-3.5/4 (teacher models) for knowledge distillation

This implements the first component of PEARL:
1. Capture expert orchestration traces from GPT-3.5/4 across 1,000+ queries
2. Store query-to-workflow pairs for training Flan-T5-small
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import with error handling - try multiple ways
GPT4Orchestrator = None
try:
    # Try direct import
    from orchestrators.gpt4_orchestrator import GPT4Orchestrator
except ImportError as e:
    try:
        # Try importing openai first, then orchestrator
        import openai
        from orchestrators.gpt4_orchestrator import GPT4Orchestrator
    except ImportError:
        logger.warning(f"Could not import GPT4Orchestrator: {e}")
        logger.warning("This is expected if dependencies are not installed.")
        GPT4Orchestrator = None

try:
    from config import config
except ImportError:
    # Fallback: try to load from config.py directly
    import importlib.util
    config_path = os.path.join(project_root, "config.py")
    if os.path.exists(config_path):
        spec = importlib.util.spec_from_file_location("config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        config = config_module
    else:
        raise ImportError("Could not find config.py")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpertTraceCollector:
    """
    Collects expert orchestration traces from GPT-4 for knowledge distillation.
    
    According to PEARL:
    - Captures expert orchestration traces from GPT-3.5/4 across 1,000+ queries
    - Generates query-to-workflow pairs
    - Stores traces in format suitable for training Flan-T5-small
    """
    
    def __init__(self, output_dir: str = "data/expert_traces"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize GPT-4 orchestrator (teacher model) - only if available
        self.teacher_orchestrator = None
        if GPT4Orchestrator is not None:
            try:
                # Get API key from config or environment
                api_key = getattr(config.api, 'OPENAI_API_KEY', None)
                if not api_key or api_key == "YOUR_OPENAI_API_KEY_HERE":
                    # Try environment variable
                    api_key = os.getenv("OPENAI_API_KEY")
                
                if not api_key:
                    raise ValueError("OpenAI API key not found in config or environment")
                
                gpt4_config = {
                    "openai_api_key": api_key,
                    "model": "gpt-4"
                }
                self.teacher_orchestrator = GPT4Orchestrator(gpt4_config)
                logger.info("GPT-4 orchestrator initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize GPT-4 orchestrator: {e}")
                logger.warning("Expert trace collection will not work without GPT-4 access")
                self.teacher_orchestrator = None
        
        self.traces = []
        self.stats = {
            "total_queries": 0,
            "successful_traces": 0,
            "failed_traces": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0
        }
    
    async def initialize(self):
        """Initialize the teacher orchestrator"""
        if self.teacher_orchestrator is None:
            raise RuntimeError(
                "GPT-4 orchestrator not available. "
                "Please ensure OpenAI API key is configured in config.py or config.env"
            )
        logger.info("Initializing GPT-4 teacher orchestrator...")
        await self.teacher_orchestrator.initialize()
        logger.info("Teacher orchestrator ready")
    
    async def collect_trace(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Collect a single expert trace from GPT-4
        
        Returns:
            Trace dict with:
            - query: Original query
            - analysis: GPT-4's query analysis
            - agent_sequence: Optimal agent sequence from GPT-4
            - workflow: Complete workflow representation
            - metadata: Cost, latency, confidence, etc.
        """
        try:
            start_time = time.time()
            
            # Get expert analysis from GPT-4
            analysis = await self.teacher_orchestrator.analyze_query(query)
            
            # Get expert routing decision
            agent_sequence = await self.teacher_orchestrator.route_to_agents(query, analysis)
            
            latency_ms = (time.time() - start_time) * 1000
            cost = analysis.get("_metrics", {}).get("cost_usd", 0.0)
            
            # Create trace
            trace = {
                "query": query,
                "analysis": {
                    "complexity": analysis.get("complexity"),
                    "reasoning_type": analysis.get("reasoning_type"),
                    "requires_enhancement": analysis.get("requires_enhancement"),
                    "requires_verification": analysis.get("requires_verification"),
                    "confidence": analysis.get("confidence", 0.0)
                },
                "agent_sequence": agent_sequence,
                "workflow": {
                    "agents": agent_sequence,
                    "estimated_steps": len(agent_sequence),
                    "complexity": analysis.get("complexity"),
                    "reasoning_type": analysis.get("reasoning_type")
                },
                "metadata": {
                    "latency_ms": latency_ms,
                    "cost_usd": cost,
                    "timestamp": time.time(),
                    "teacher_model": "gpt-4",
                    "trace_id": f"trace_{len(self.traces)}_{int(time.time())}"
                }
            }
            
            self.stats["successful_traces"] += 1
            self.stats["total_cost"] += cost
            
            return trace
            
        except Exception as e:
            logger.error(f"Error collecting trace for query '{query}': {e}")
            self.stats["failed_traces"] += 1
            return None
    
    async def collect_batch(self, queries: List[str], batch_size: int = 10):
        """
        Collect traces for a batch of queries
        
        Args:
            queries: List of queries to collect traces for
            batch_size: Number of queries to process in parallel
        """
        logger.info(f"Collecting expert traces for {len(queries)} queries...")
        
        self.stats["total_queries"] = len(queries)
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(queries) + batch_size - 1)//batch_size}")
            
            # Process batch
            tasks = [self.collect_trace(query) for query in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful traces
            for result in results:
                if isinstance(result, dict) and result is not None:
                    self.traces.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Exception in batch: {result}")
            
            # Save intermediate results
            if (i + batch_size) % 100 == 0:
                self.save_traces(f"intermediate_{i + batch_size}.jsonl")
                logger.info(f"Saved intermediate traces: {len(self.traces)} traces collected")
            
            # Rate limiting to avoid API limits
            await asyncio.sleep(1)
        
        logger.info(f"Collection complete: {len(self.traces)} traces collected")
    
    def save_traces(self, filename: str = "expert_traces.jsonl"):
        """Save traces to JSONL file (one trace per line)"""
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for trace in self.traces:
                f.write(json.dumps(trace, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(self.traces)} traces to {output_path}")
    
    def save_statistics(self, filename: str = "collection_stats.json"):
        """Save collection statistics"""
        output_path = self.output_dir / filename
        
        # Calculate average latency
        if self.traces:
            latencies = [t["metadata"]["latency_ms"] for t in self.traces]
            self.stats["avg_latency_ms"] = sum(latencies) / len(latencies)
        
        stats = {
            **self.stats,
            "success_rate": self.stats["successful_traces"] / max(self.stats["total_queries"], 1),
            "total_traces_collected": len(self.traces)
        }
        
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Statistics saved to {output_path}")
        return stats
    
    def format_for_training(self) -> List[Dict[str, Any]]:
        """
        Format traces for Flan-T5 training (query-to-workflow pairs)
        
        Returns:
            List of training examples in format:
            {
                "input": "Query: {query}\nAnalysis: {analysis}",
                "target": "{agent1},{agent2},{agent3}",
                "metadata": {...}
            }
        """
        training_examples = []
        
        for trace in self.traces:
            query = trace["query"]
            analysis = trace["analysis"]
            sequence = trace["agent_sequence"]
            
            # Format input prompt
            input_text = f"""Query: {query}

Complexity: {analysis.get('complexity', 'simple')}
Reasoning Type: {analysis.get('reasoning_type', 'factual')}
Requires Enhancement: {analysis.get('requires_enhancement', False)}
Requires Verification: {analysis.get('requires_verification', False)}

Determine the optimal agent sequence:"""
            
            # Format target (agent sequence as comma-separated)
            target_text = ",".join(sequence)
            
            training_example = {
                "input": input_text,
                "target": target_text,
                "query": query,
                "agent_sequence": sequence,
                "analysis": analysis,
                "metadata": trace["metadata"]
            }
            
            training_examples.append(training_example)
        
        return training_examples
    
    def save_training_format(self, filename: str = "training_data.jsonl"):
        """Save traces in training format"""
        training_examples = self.format_for_training()
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in training_examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(training_examples)} training examples to {output_path}")


async def main():
    """Main function to collect expert traces"""
    
    # Load queries from existing dataset or generate
    queries_file = Path("data/query_booster_500.jsonl")
    
    if queries_file.exists():
        queries = []
        with open(queries_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                queries.append(data.get("query", ""))
        logger.info(f"Loaded {len(queries)} queries from {queries_file}")
    else:
        # Fallback: use sample queries
        queries = [
            "What is Article 21?",
            "What is Section 302 of IPC?",
            "Compare Article 19 and Article 21",
            "How to file an FIR?",
            "Analyze the implications of Section 377",
            "What are the rights of an accused?",
            "Difference between murder and culpable homicide",
            "Procedure for bail application",
            "What is the punishment for theft?",
            "Rights of women under Indian Constitution"
        ]
        logger.info(f"Using {len(queries)} sample queries")
    
    # Initialize collector
    collector = ExpertTraceCollector()
    await collector.initialize()
    
    # Collect traces
    await collector.collect_batch(queries, batch_size=5)
    
    # Save results
    collector.save_traces("expert_traces.jsonl")
    collector.save_training_format("training_data.jsonl")
    stats = collector.save_statistics()
    
    print("\n" + "="*60)
    print("Expert Trace Collection Complete")
    print("="*60)
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Successful Traces: {stats['successful_traces']}")
    print(f"Failed Traces: {stats['failed_traces']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"Total Cost: ${stats['total_cost']:.4f}")
    print(f"Average Latency: {stats['avg_latency_ms']:.1f}ms")
    print(f"Traces Saved: {stats['total_traces_collected']}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

