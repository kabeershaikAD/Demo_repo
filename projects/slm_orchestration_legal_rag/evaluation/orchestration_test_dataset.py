"""
Orchestration Test Dataset Generator
Creates comprehensive test dataset for evaluating orchestration quality
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class OrchestrationTestCase:
    """Single test case for orchestration evaluation"""
    id: int
    query: str
    complexity: str  # simple, moderate, complex
    reasoning_type: str  # factual, analytical, comparative, procedural
    expected_agents: List[str]
    reasoning: str  # Why this routing is correct
    category: str  # For analysis

class OrchestrationTestDataset:
    """Generate comprehensive orchestration test dataset"""
    
    def __init__(self):
        self.test_cases = []
        self._generate_test_cases()
    
    def _generate_test_cases(self):
        """Generate all test cases"""
        
        # Category 1: Simple Factual Queries (40 cases)
        simple_factual = [
            OrchestrationTestCase(
                id=1,
                query="What is Section 302 of the Indian Penal Code?",
                complexity="simple",
                reasoning_type="factual",
                expected_agents=["retriever", "answering"],
                reasoning="Simple definition query needs only retrieval and generation",
                category="simple_factual"
            ),
            OrchestrationTestCase(
                id=2,
                query="Define theft under IPC",
                complexity="simple",
                reasoning_type="factual",
                expected_agents=["retriever", "answering"],
                reasoning="Direct definition question",
                category="simple_factual"
            ),
            OrchestrationTestCase(
                id=3,
                query="What is Article 21?",
                complexity="simple",
                reasoning_type="factual",
                expected_agents=["retriever", "answering"],
                reasoning="Basic constitutional question",
                category="simple_factual"
            ),
            OrchestrationTestCase(
                id=4,
                query="Define bail",
                complexity="simple",
                reasoning_type="factual",
                expected_agents=["retriever", "answering"],
                reasoning="Simple legal term definition",
                category="simple_factual"
            ),
            OrchestrationTestCase(
                id=5,
                query="What is FIR?",
                complexity="simple",
                reasoning_type="factual",
                expected_agents=["retriever", "answering"],
                reasoning="Basic procedural term",
                category="simple_factual"
            ),
            # Add 35 more simple factual cases...
        ]
        
        # Category 2: Complex Comparative Queries (30 cases)
        complex_comparative = [
            OrchestrationTestCase(
                id=41,
                query="Compare bail provisions in IPC versus CrPC and explain the implications for undertrial prisoners",
                complexity="complex",
                reasoning_type="comparative",
                expected_agents=["booster", "retriever", "answering", "verifier"],
                reasoning="Complex comparison needs query enhancement, thorough retrieval, comprehensive generation, and verification",
                category="complex_comparative"
            ),
            OrchestrationTestCase(
                id=42,
                query="What are the differences between civil and criminal contempt of court?",
                complexity="complex",
                reasoning_type="comparative",
                expected_agents=["booster", "retriever", "answering", "verifier"],
                reasoning="Comparative analysis requires enhancement and verification",
                category="complex_comparative"
            ),
            # Add 28 more comparative cases...
        ]
        
        # Category 3: Analytical Queries (30 cases)
        analytical = [
            OrchestrationTestCase(
                id=71,
                query="Analyze the impact of Article 370 abrogation on constitutional law",
                complexity="complex",
                reasoning_type="analytical",
                expected_agents=["booster", "retriever", "answering", "verifier"],
                reasoning="Deep analysis requires enhancement, comprehensive retrieval, careful generation, and fact verification",
                category="analytical"
            ),
            OrchestrationTestCase(
                id=72,
                query="Explain the implications of the recent Supreme Court judgment on privacy rights",
                complexity="complex",
                reasoning_type="analytical",
                expected_agents=["booster", "retriever", "answering", "verifier"],
                reasoning="Analytical query needs full pipeline with verification",
                category="analytical"
            ),
            # Add 28 more analytical cases...
        ]
        
        # Category 4: Procedural Queries (30 cases)
        procedural = [
            OrchestrationTestCase(
                id=101,
                query="How to file a PIL in Supreme Court?",
                complexity="moderate",
                reasoning_type="procedural",
                expected_agents=["booster", "retriever", "answering"],
                reasoning="Procedural question benefits from enhancement and needs accurate retrieval",
                category="procedural"
            ),
            OrchestrationTestCase(
                id=102,
                query="What is the process for obtaining anticipatory bail?",
                complexity="moderate",
                reasoning_type="procedural",
                expected_agents=["booster", "retriever", "answering"],
                reasoning="Procedural query needs enhancement for clarity",
                category="procedural"
            ),
            # Add 28 more procedural cases...
        ]
        
        # Category 5: Multilingual Queries (20 cases)
        multilingual = [
            OrchestrationTestCase(
                id=131,
                query="अनुच्छेद 21 क्या है?",
                complexity="simple",
                reasoning_type="factual",
                expected_agents=["multilingual", "retriever", "answering"],
                reasoning="Hindi query needs translation before processing",
                category="multilingual"
            ),
            OrchestrationTestCase(
                id=132,
                query="What is Article 21?",
                complexity="simple",
                reasoning_type="factual",
                expected_agents=["retriever", "answering"],
                reasoning="English query doesn't need translation",
                category="multilingual"
            ),
            # Add 18 more multilingual cases...
        ]
        
        # Category 6: Edge Cases (20 cases)
        edge_cases = [
            OrchestrationTestCase(
                id=151,
                query="",
                complexity="invalid",
                reasoning_type="error",
                expected_agents=[],
                reasoning="Empty query should be rejected",
                category="edge_case"
            ),
            OrchestrationTestCase(
                id=152,
                query="a" * 1000,  # Very long query
                complexity="simple",
                reasoning_type="factual",
                expected_agents=["booster", "retriever", "answering"],
                reasoning="Extremely long query needs enhancement to extract key points",
                category="edge_case"
            ),
            OrchestrationTestCase(
                id=153,
                query="???",
                complexity="invalid",
                reasoning_type="error",
                expected_agents=[],
                reasoning="Nonsensical query should be rejected",
                category="edge_case"
            ),
            # Add 17 more edge cases...
        ]
        
        # Combine all categories
        self.test_cases = (
            simple_factual +
            complex_comparative +
            analytical +
            procedural +
            multilingual +
            edge_cases
        )
    
    def export_to_json(self, filepath: str):
        """Export dataset to JSON"""
        data = [asdict(tc) for tc in self.test_cases]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_by_category(self, category: str) -> List[OrchestrationTestCase]:
        """Get test cases by category"""
        return [tc for tc in self.test_cases if tc.category == category]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        from collections import Counter
        
        return {
            "total_cases": len(self.test_cases),
            "by_complexity": dict(Counter(tc.complexity for tc in self.test_cases)),
            "by_reasoning_type": dict(Counter(tc.reasoning_type for tc in self.test_cases)),
            "by_category": dict(Counter(tc.category for tc in self.test_cases)),
            "by_agent_count": dict(Counter(len(tc.expected_agents) for tc in self.test_cases))
        }

# Generate and export
if __name__ == "__main__":
    dataset = OrchestrationTestDataset()
    dataset.export_to_json("evaluation/orchestration_test_dataset.json")
    print(f"Generated {len(dataset.test_cases)} test cases")
    print("\nDataset Statistics:")
    print(json.dumps(dataset.get_statistics(), indent=2))
