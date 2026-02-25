"""
Step 2: Simplified Expert Trace Collection
Uses OpenAI API directly without full orchestrator import chain
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
import logging

# Try to import openai
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI package not found. Please install: pip install openai")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleExpertTraceCollector:
    """
    Simplified expert trace collector that uses OpenAI API directly
    """
    
    def __init__(self, output_dir: str = "data/expert_traces"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get API key from config or environment
        self.api_key = self._get_api_key()
        if self.api_key:
            openai.api_key = self.api_key
        
        self.traces = []
        self.stats = {
            "total_queries": 0,
            "successful_traces": 0,
            "failed_traces": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0
        }
    
    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from config or environment"""
        # Try config.py
        try:
            from config import config
            api_key = getattr(config.api, 'OPENAI_API_KEY', None)
            if api_key and api_key != "YOUR_OPENAI_API_KEY_HERE":
                return api_key
        except:
            pass
        
        # Try environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
        
        return None
    
    async def collect_trace(self, query: str) -> Optional[Dict[str, Any]]:
        """Collect expert trace using OpenAI API directly (async)"""
        
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI package not available")
            return None
        
        if not self.api_key:
            logger.error("OpenAI API key not found")
            return None
        
        try:
            start_time = time.time()
            
            # Use OpenAI API directly to get expert orchestration decision
            prompt = f"""Analyze this legal query and determine the optimal agent sequence for a multi-agent RAG system.

Query: "{query}"

Available agents:
- booster: Enhances vague queries
- retriever: Retrieves legal documents
- answering: Generates answers
- verifier: Verifies citations
- multilingual: Handles translation

Respond with JSON:
{{
    "complexity": "simple|moderate|complex",
    "reasoning_type": "factual|analytical|comparative|procedural",
    "requires_enhancement": true|false,
    "requires_verification": true|false,
    "agent_sequence": ["agent1", "agent2", ...],
    "confidence": 0.0-1.0
}}"""
            
            # Use async OpenAI client for parallel processing
            # Run synchronous call in thread pool to allow concurrency
            client = openai.OpenAI(api_key=self.api_key)
            
            # Run the API call in a thread to allow async concurrency
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert in multi-agent orchestration for legal RAG systems."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback: create basic analysis
                analysis = {
                    "complexity": "simple",
                    "reasoning_type": "factual",
                    "requires_enhancement": len(query.split()) <= 4,
                    "requires_verification": False,
                    "agent_sequence": ["retriever", "answering"],
                    "confidence": 0.7
                }
            
            # Calculate cost (approximate)
            cost = (response.usage.total_tokens / 1000) * 0.03  # GPT-4 pricing
            
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
                "agent_sequence": analysis.get("agent_sequence", ["retriever", "answering"]),
                "workflow": {
                    "agents": analysis.get("agent_sequence", []),
                    "estimated_steps": len(analysis.get("agent_sequence", [])),
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
    
    async def collect_batch(self, queries: List[str], batch_size: int = 500):
        """
        Collect traces for queries in batches of specified size.
        Processes queries in chunks and saves intermediate results.
        """
        logger.info(f"Collecting expert traces for {len(queries)} queries in batches of {batch_size}...")
        
        self.stats["total_queries"] = len(queries)
        
        # Process queries in batches
        total_batches = (len(queries) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(queries))
            batch_queries = queries[start_idx:end_idx]
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing Batch {batch_num + 1}/{total_batches} (queries {start_idx + 1}-{end_idx})")
            logger.info(f"{'='*60}")
            
            # Process queries in parallel (concurrent requests)
            # Use smaller concurrent batches to avoid rate limits
            # Process 20 queries concurrently at a time (within each 500-query batch)
            concurrent_batch_size = 20  # Process 20 queries in parallel at a time
            total_concurrent_batches = (len(batch_queries) + concurrent_batch_size - 1) // concurrent_batch_size
            
            for concurrent_batch_num in range(total_concurrent_batches):
                concurrent_start = concurrent_batch_num * concurrent_batch_size
                concurrent_end = min(concurrent_start + concurrent_batch_size, len(batch_queries))
                concurrent_queries = batch_queries[concurrent_start:concurrent_end]
                
                query_num_start = start_idx + concurrent_start + 1
                query_num_end = start_idx + concurrent_end
                
                logger.info(f"  Processing concurrent batch {concurrent_batch_num + 1}/{total_concurrent_batches} "
                          f"(queries {query_num_start}-{query_num_end}) - {len(concurrent_queries)} queries in parallel...")
                
                # Process all queries in this concurrent batch in parallel
                tasks = [self.collect_trace(query) for query in concurrent_queries]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect successful traces
                for result in results:
                    if isinstance(result, dict) and result is not None:
                        self.traces.append(result)
                    elif isinstance(result, Exception):
                        logger.error(f"  Error in concurrent batch: {result}")
                
                # Progress update
                logger.info(f"  ✅ Completed: {len(self.traces)} total traces collected so far")
                
                # Small delay between concurrent batches to respect rate limits
                if concurrent_batch_num < total_concurrent_batches - 1:
                    await asyncio.sleep(1)  # 1 second between concurrent batches
            
            # Save intermediate results after each batch
            batch_filename = f"expert_traces_batch_{batch_num + 1}.jsonl"
            self.save_traces(batch_filename)
            logger.info(f"✅ Saved batch {batch_num + 1} results: {len(self.traces)} total traces collected")
            
            # Save training format after each batch
            training_filename = f"training_data_batch_{batch_num + 1}.jsonl"
            training_data = self.format_for_training()
            training_path = self.output_dir / training_filename
            with open(training_path, 'w', encoding='utf-8') as f:
                for example in training_data:
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
            logger.info(f"✅ Saved training data for batch {batch_num + 1}")
            
            # Brief pause between batches
            if batch_num < total_batches - 1:
                logger.info(f"⏸️  Pausing 5 seconds before next batch...")
                await asyncio.sleep(5)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Collection complete: {len(self.traces)} traces collected from {len(queries)} queries")
        logger.info(f"{'='*60}")
    
    def save_traces(self, filename: str = "expert_traces.jsonl"):
        """Save traces to JSONL file"""
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for trace in self.traces:
                f.write(json.dumps(trace, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(self.traces)} traces to {output_path}")
    
    def format_for_training(self) -> List[Dict[str, Any]]:
        """Format traces for training"""
        training_examples = []
        
        for trace in self.traces:
            query = trace["query"]
            analysis = trace["analysis"]
            sequence = trace["agent_sequence"]
            
            input_text = f"""Query: {query}

Complexity: {analysis.get('complexity', 'simple')}
Reasoning Type: {analysis.get('reasoning_type', 'factual')}
Requires Enhancement: {analysis.get('requires_enhancement', False)}
Requires Verification: {analysis.get('requires_verification', False)}

Determine the optimal agent sequence:"""
            
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
        """Save in training format"""
        training_examples = self.format_for_training()
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in training_examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(training_examples)} training examples to {output_path}")
    
    def save_statistics(self, filename: str = "collection_stats.json"):
        """Save statistics"""
        output_path = self.output_dir / filename
        
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


async def main():
    """Main function"""
    
    print("="*60)
    print("STEP 2: Expert Trace Collection")
    print("="*60)
    
    if not OPENAI_AVAILABLE:
        print("\n❌ OpenAI package not available!")
        print("Please install: pip install openai")
        return
    
    # Load queries from the new 1200 training dataset
    queries_file = Path("data/legal_queries_1200_training.jsonl")
    queries = []
    
    if queries_file.exists():
        with open(queries_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                query = data.get("query", "")
                if query:
                    queries.append(query)
        print(f"\n✅ Loaded {len(queries)} queries from {queries_file}")
    else:
        # Fallback to old file if new one doesn't exist
        fallback_file = Path("data/query_booster_500.jsonl")
        if fallback_file.exists():
            with open(fallback_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    query = data.get("query", "")
                    if query:
                        queries.append(query)
            print(f"\n⚠️  Using fallback file: {fallback_file} ({len(queries)} queries)")
        else:
            # Use sample queries as last resort
            queries = [
                "What is Article 21?",
                "What is Section 302 of IPC?",
                "Compare Article 19 and Article 21",
                "How to file an FIR?",
                "Analyze the implications of Section 377"
            ]
            print(f"\n⚠️  Using {len(queries)} sample queries (dataset file not found)")
    
    # Use ALL queries for full trace collection (1,200 queries)
    test_queries = queries
    print(f"📊 Collecting traces for {len(test_queries)} queries")
    print(f"   Expected time: 4-5 hours")
    print(f"   Expected cost: ~${len(test_queries) * 0.007:.2f} (at ~$0.007 per trace)")
    
    # Initialize collector
    collector = SimpleExpertTraceCollector()
    
    if not collector.api_key:
        print("\n❌ OpenAI API key not found!")
        print("Please set OPENAI_API_KEY environment variable or configure in config.py")
        return
    
    print(f"✅ API key found: {collector.api_key[:10]}...")
    
    # Collect traces in batches of 500
    # 1200 queries = 3 batches (500 + 500 + 200)
    # Each batch processes queries in parallel (20 concurrent requests)
    # Each batch is saved separately for safety
    batch_size = 500
    concurrent_requests = 20  # Process 20 queries in parallel at a time
    print(f"\n📦 Processing {len(test_queries)} queries in batches of {batch_size}")
    print(f"   Total batches: {(len(test_queries) + batch_size - 1) // batch_size}")
    print(f"   Concurrent requests per batch: {concurrent_requests} (parallel processing)")
    print(f"   Intermediate saves after each batch")
    print(f"   Expected time: ~1-2 hours (much faster with parallel processing!)\n")
    
    await collector.collect_batch(test_queries, batch_size=batch_size)
    
    # Save final consolidated results (all batches combined)
    print("\n" + "="*60)
    print("Saving Final Consolidated Results")
    print("="*60)
    collector.save_traces("expert_traces.jsonl")
    collector.save_training_format("training_data.jsonl")
    stats = collector.save_statistics()
    
    print("\n" + "="*60)
    print("✅ Expert Trace Collection Complete!")
    print("="*60)
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Successful Traces: {stats['successful_traces']}")
    print(f"Failed Traces: {stats['failed_traces']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"Total Cost: ${stats['total_cost']:.4f}")
    print(f"Average Latency: {stats['avg_latency_ms']:.1f}ms")
    print(f"Traces Saved: {stats['total_traces_collected']}")
    print("="*60)
    
    if stats['successful_traces'] > 0:
        print("\n✅ Step 2 Complete! Ready for Step 3:")
        print("   python training/knowledge_distillation.py --data data/expert_traces/training_data.jsonl")

if __name__ == "__main__":
    asyncio.run(main())







