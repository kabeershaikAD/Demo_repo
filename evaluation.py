"""
Evaluation scripts for measuring system performance metrics.
"""
import asyncio
import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
from sklearn.metrics import precision_score, recall_score, ndcg_score
from sentence_transformers import SentenceTransformer
import re

from app import AgenticLegalRAG


class LegalRAGEvaluator:
    """Evaluator for the Agentic Legal RAG system."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.rag_system = None
        self.evaluation_results = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Evaluation metrics
        self.metrics = {
            "precision_at_k": [],
            "recall_at_k": [],
            "ndcg_at_k": [],
            "confidence_scores": [],
            "citation_accuracy": [],
            "verification_scores": [],
            "response_times": [],
            "hallucination_rates": []
        }
        
    def setup_logging(self):
        """Setup logging for the evaluator."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        evaluator_logger = logging.getLogger("evaluator")
        evaluator_logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_dir / "evaluation.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        evaluator_logger.addHandler(file_handler)
        self.logger = evaluator_logger
    
    async def initialize(self, rag_system: AgenticLegalRAG):
        """Initialize the evaluator with the RAG system."""
        self.rag_system = rag_system
        self.logger.info("Evaluator initialized")
    
    async def evaluate_query(self, query: str, expected_answer: str = None, 
                           expected_docs: List[str] = None, k_values: List[int] = None) -> Dict:
        """Evaluate a single query."""
        if k_values is None:
            k_values = [1, 3, 5, 10]
        
        start_time = datetime.now()
        
        try:
            # Process query
            result = await self.rag_system.process_query(query)
            
            if not result["success"]:
                return {
                    "query": query,
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Calculate metrics
            evaluation = {
                "query": query,
                "success": True,
                "response_time": response_time,
                "confidence_score": result.get("confidence_score", 0.0),
                "citations_count": len(result.get("citations", [])),
                "sources_used": result.get("sources_used", 0),
                "verification_passed": result.get("verification", {}).get("verification_passed", False),
                "verification_score": result.get("verification", {}).get("verification_score", 0.0),
                "precision_at_k": {},
                "recall_at_k": {},
                "ndcg_at_k": {},
                "citation_accuracy": 0.0,
                "hallucination_rate": 0.0
            }
            
            # Calculate precision, recall, and NDCG at different k values
            retrieved_docs = result.get("retrieved_documents", [])
            if expected_docs:
                for k in k_values:
                    precision, recall, ndcg = self._calculate_retrieval_metrics(
                        retrieved_docs, expected_docs, k
                    )
                    evaluation["precision_at_k"][f"p@{k}"] = precision
                    evaluation["recall_at_k"][f"r@{k}"] = recall
                    evaluation["ndcg_at_k"][f"ndcg@{k}"] = ndcg
            
            # Calculate citation accuracy
            evaluation["citation_accuracy"] = self._calculate_citation_accuracy(
                result.get("citations", []), retrieved_docs
            )
            
            # Calculate hallucination rate
            if expected_answer:
                evaluation["hallucination_rate"] = self._calculate_hallucination_rate(
                    result["answer"], expected_answer
                )
            
            # Store metrics
            self._store_metrics(evaluation)
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating query: {e}")
            return {
                "query": query,
                "success": False,
                "error": str(e)
            }
    
    def _calculate_retrieval_metrics(self, retrieved_docs: List[Dict], 
                                   expected_docs: List[str], k: int) -> Tuple[float, float, float]:
        """Calculate precision, recall, and NDCG at k."""
        if not retrieved_docs or not expected_docs:
            return 0.0, 0.0, 0.0
        
        # Get top-k retrieved documents
        top_k_docs = retrieved_docs[:k]
        retrieved_titles = [doc.get("title", "") for doc in top_k_docs]
        
        # Calculate precision
        relevant_retrieved = sum(1 for title in retrieved_titles if title in expected_docs)
        precision = relevant_retrieved / k if k > 0 else 0.0
        
        # Calculate recall
        total_relevant = len(expected_docs)
        recall = relevant_retrieved / total_relevant if total_relevant > 0 else 0.0
        
        # Calculate NDCG
        relevance_scores = [1 if title in expected_docs else 0 for title in retrieved_titles]
        if sum(relevance_scores) == 0:
            ndcg = 0.0
        else:
            # Ideal DCG for comparison
            ideal_relevance = [1] * min(len(expected_docs), k)
            ideal_dcg = self._calculate_dcg(ideal_relevance)
            actual_dcg = self._calculate_dcg(relevance_scores)
            ndcg = actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0
        
        return precision, recall, ndcg
    
    def _calculate_dcg(self, relevance_scores: List[int]) -> float:
        """Calculate Discounted Cumulative Gain."""
        dcg = 0.0
        for i, score in enumerate(relevance_scores):
            dcg += score / np.log2(i + 2)  # i+2 because log2(1) = 0
        return dcg
    
    def _calculate_citation_accuracy(self, citations: List[Dict], 
                                   retrieved_docs: List[Dict]) -> float:
        """Calculate citation accuracy."""
        if not citations:
            return 0.0
        
        valid_citations = 0
        total_citations = len(citations)
        
        for citation in citations:
            # Check if citation references a valid document
            doc_ref = citation.get("text", "")
            if doc_ref.startswith("[Doc "):
                # Extract document number
                match = re.search(r'\[Doc (\d+)\]', doc_ref)
                if match:
                    doc_num = int(match.group(1)) - 1  # Convert to 0-based index
                    if 0 <= doc_num < len(retrieved_docs):
                        valid_citations += 1
        
        return valid_citations / total_citations if total_citations > 0 else 0.0
    
    def _calculate_hallucination_rate(self, generated_answer: str, 
                                    expected_answer: str) -> float:
        """Calculate hallucination rate by comparing with expected answer."""
        # Simple word-level comparison
        generated_words = set(generated_answer.lower().split())
        expected_words = set(expected_answer.lower().split())
        
        if not generated_words:
            return 1.0
        
        # Calculate words that are in generated but not in expected
        hallucinated_words = generated_words - expected_words
        hallucination_rate = len(hallucinated_words) / len(generated_words)
        
        return min(1.0, hallucination_rate)
    
    def _store_metrics(self, evaluation: Dict):
        """Store evaluation metrics for analysis."""
        self.metrics["confidence_scores"].append(evaluation.get("confidence_score", 0.0))
        self.metrics["citation_accuracy"].append(evaluation.get("citation_accuracy", 0.0))
        self.metrics["verification_scores"].append(evaluation.get("verification_score", 0.0))
        self.metrics["response_times"].append(evaluation.get("response_time", 0.0))
        self.metrics["hallucination_rates"].append(evaluation.get("hallucination_rate", 0.0))
        
        # Store precision, recall, and NDCG metrics
        for k, precision in evaluation.get("precision_at_k", {}).items():
            if k not in self.metrics["precision_at_k"]:
                self.metrics["precision_at_k"][k] = []
            self.metrics["precision_at_k"][k].append(precision)
        
        for k, recall in evaluation.get("recall_at_k", {}).items():
            if k not in self.metrics["recall_at_k"]:
                self.metrics["recall_at_k"][k] = []
            self.metrics["recall_at_k"][k].append(recall)
        
        for k, ndcg in evaluation.get("ndcg_at_k", {}).items():
            if k not in self.metrics["ndcg_at_k"]:
                self.metrics["ndcg_at_k"][k] = []
            self.metrics["ndcg_at_k"][k].append(ndcg)
    
    async def evaluate_batch(self, test_queries: List[Dict]) -> Dict:
        """Evaluate a batch of test queries."""
        self.logger.info(f"Starting batch evaluation of {len(test_queries)} queries")
        
        results = []
        
        for i, test_case in enumerate(test_queries):
            self.logger.info(f"Evaluating query {i+1}/{len(test_queries)}")
            
            query = test_case["query"]
            expected_answer = test_case.get("expected_answer")
            expected_docs = test_case.get("expected_docs", [])
            
            result = await self.evaluate_query(query, expected_answer, expected_docs)
            results.append(result)
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics()
        
        evaluation_summary = {
            "total_queries": len(test_queries),
            "successful_queries": len([r for r in results if r.get("success", False)]),
            "aggregate_metrics": aggregate_metrics,
            "individual_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store evaluation results
        self.evaluation_results.append(evaluation_summary)
        
        return evaluation_summary
    
    def _calculate_aggregate_metrics(self) -> Dict:
        """Calculate aggregate metrics across all evaluations."""
        aggregate = {}
        
        # Basic metrics
        if self.metrics["confidence_scores"]:
            aggregate["avg_confidence"] = np.mean(self.metrics["confidence_scores"])
            aggregate["std_confidence"] = np.std(self.metrics["confidence_scores"])
        
        if self.metrics["citation_accuracy"]:
            aggregate["avg_citation_accuracy"] = np.mean(self.metrics["citation_accuracy"])
            aggregate["std_citation_accuracy"] = np.std(self.metrics["citation_accuracy"])
        
        if self.metrics["verification_scores"]:
            aggregate["avg_verification_score"] = np.mean(self.metrics["verification_scores"])
            aggregate["std_verification_score"] = np.std(self.metrics["verification_scores"])
        
        if self.metrics["response_times"]:
            aggregate["avg_response_time"] = np.mean(self.metrics["response_times"])
            aggregate["std_response_time"] = np.std(self.metrics["response_times"])
        
        if self.metrics["hallucination_rates"]:
            aggregate["avg_hallucination_rate"] = np.mean(self.metrics["hallucination_rates"])
            aggregate["std_hallucination_rate"] = np.std(self.metrics["hallucination_rates"])
        
        # Precision, Recall, and NDCG at different k values
        for k in self.metrics["precision_at_k"]:
            if self.metrics["precision_at_k"][k]:
                aggregate[f"avg_{k}"] = np.mean(self.metrics["precision_at_k"][k])
                aggregate[f"std_{k}"] = np.std(self.metrics["precision_at_k"][k])
        
        for k in self.metrics["recall_at_k"]:
            if self.metrics["recall_at_k"][k]:
                aggregate[f"avg_{k}"] = np.mean(self.metrics["recall_at_k"][k])
                aggregate[f"std_{k}"] = np.std(self.metrics["recall_at_k"][k])
        
        for k in self.metrics["ndcg_at_k"]:
            if self.metrics["ndcg_at_k"][k]:
                aggregate[f"avg_{k}"] = np.mean(self.metrics["ndcg_at_k"][k])
                aggregate[f"std_{k}"] = np.std(self.metrics["ndcg_at_k"][k])
        
        return aggregate
    
    def generate_evaluation_report(self) -> Dict:
        """Generate a comprehensive evaluation report."""
        if not self.evaluation_results:
            return {"error": "No evaluation results available"}
        
        # Combine all evaluation results
        all_results = []
        for eval_result in self.evaluation_results:
            all_results.extend(eval_result.get("individual_results", []))
        
        # Calculate overall metrics
        overall_metrics = self._calculate_aggregate_metrics()
        
        # Generate report
        report = {
            "evaluation_summary": {
                "total_evaluations": len(self.evaluation_results),
                "total_queries": sum(len(eval_result.get("individual_results", [])) 
                                   for eval_result in self.evaluation_results),
                "successful_queries": len([r for r in all_results if r.get("success", False)]),
                "success_rate": len([r for r in all_results if r.get("success", False)]) / len(all_results) if all_results else 0
            },
            "overall_metrics": overall_metrics,
            "detailed_results": self.evaluation_results,
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def save_evaluation_results(self, filename: str = None):
        """Save evaluation results to file."""
        if filename is None:
            filename = f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        results_file = Path("logs") / filename
        
        with open(results_file, 'w') as f:
            json.dump(self.evaluation_results, f, indent=2, default=str)
        
        self.logger.info(f"Evaluation results saved to {results_file}")
    
    def load_evaluation_results(self, filename: str):
        """Load evaluation results from file."""
        results_file = Path("logs") / filename
        
        if results_file.exists():
            with open(results_file, 'r') as f:
                self.evaluation_results = json.load(f)
            self.logger.info(f"Evaluation results loaded from {results_file}")
        else:
            self.logger.error(f"Results file not found: {results_file}")


# Example usage and test cases
async def main():
    """Main function for running evaluations."""
    # Initialize RAG system
    config = {
        "openai_api_key": "your-api-key-here",
        "booster_model": "google/flan-t5-small",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "llm_model": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 1000,
        "top_k": 5,
        "similarity_threshold": 0.3
    }
    
    rag_system = AgenticLegalRAG(config)
    await rag_system.initialize()
    
    # Initialize evaluator
    evaluator = LegalRAGEvaluator()
    await evaluator.initialize(rag_system)
    
    # Test queries
    test_queries = [
        {
            "query": "What is the definition of invention under patent law?",
            "expected_answer": "An invention is defined as a new product or process involving an inventive step and capable of industrial application.",
            "expected_docs": ["Patents Act 1970 - Section 2", "Patent Law Definitions"]
        },
        {
            "query": "What are the requirements for patentability?",
            "expected_answer": "The requirements for patentability include novelty, inventive step, and industrial applicability.",
            "expected_docs": ["Patents Act 1970 - Section 3", "Patent Requirements"]
        },
        {
            "query": "Can living organisms be patented?",
            "expected_answer": "Yes, living organisms can be patented if they are human-made and meet the patentability requirements.",
            "expected_docs": ["Diamond v. Chakrabarty Case Law", "Patent Law Cases"]
        }
    ]
    
    # Run evaluation
    results = await evaluator.evaluate_batch(test_queries)
    
    # Generate report
    report = evaluator.generate_evaluation_report()
    
    print("Evaluation Results:")
    print(json.dumps(report, indent=2))
    
    # Save results
    evaluator.save_evaluation_results()


if __name__ == "__main__":
    asyncio.run(main())
