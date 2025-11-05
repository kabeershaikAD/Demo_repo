#!/usr/bin/env python3
"""
Data Bootstrap Script for Training Query Booster SLM
Generates structured JSON training data using rule-based heuristics and optional GPT refinement
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Optional imports for GPT refinement
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import pipeline
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup bootstrap-specific logging
bootstrap_logger = logging.getLogger('bootstrap')
bootstrap_handler = logging.FileHandler('logs/data_bootstrap.log')
bootstrap_handler.setLevel(logging.INFO)
bootstrap_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
bootstrap_handler.setFormatter(bootstrap_formatter)
bootstrap_logger.addHandler(bootstrap_handler)
bootstrap_logger.setLevel(logging.INFO)

@dataclass
class QueryDecision:
    """Structured decision for a query"""
    query: str
    need_boost: bool
    boosted_query: str
    retrieval_mode: str
    top_k: int
    require_human_review: bool
    confidence: float
    reasoning: str
    method: str  # "rule_based" or "gpt_refined"

class QueryBootstrapGenerator:
    """Generates training data for Query Booster SLM"""
    
    def __init__(self, use_gpt_refinement: bool = False, openai_api_key: str = None):
        self.use_gpt_refinement = use_gpt_refinement
        self.openai_api_key = openai_api_key
        self.gpt_model = "gpt-3.5-turbo"
        
        # Initialize OpenAI if available and requested
        if self.use_gpt_refinement and OPENAI_AVAILABLE and openai_api_key:
            openai.api_key = openai_api_key
            bootstrap_logger.info("OpenAI API initialized for GPT refinement")
        elif self.use_gpt_refinement and not OPENAI_AVAILABLE:
            bootstrap_logger.warning("OpenAI not available, falling back to rule-based only")
            self.use_gpt_refinement = False
        elif self.use_gpt_refinement and not openai_api_key:
            bootstrap_logger.warning("No OpenAI API key provided, falling back to rule-based only")
            self.use_gpt_refinement = False
        
        # Legal query patterns for rule-based classification
        self.legal_patterns = {
            'statute_keywords': [
                'article', 'section', 'act', 'code', 'ipc', 'constitution', 'statute',
                'provision', 'clause', 'subsection', 'schedule', 'rule', 'regulation'
            ],
            'judgment_keywords': [
                'judgment', 'case', 'court', 'supreme court', 'high court', 'district court',
                'sessions court', 'tribunal', 'verdict', 'decision', 'order', 'decree',
                'precedent', 'ruling', 'bench', 'judge'
            ],
            'sensitive_topics': [
                'rape', 'murder', 'terrorism', 'sedition', 'contempt', 'defamation',
                'hate speech', 'cyber crime', 'domestic violence', 'child abuse'
            ],
            'vague_terms': [
                'rights', 'law', 'legal', 'help', 'advice', 'information', 'query',
                'question', 'doubt', 'confusion', 'issue', 'problem'
            ]
        }
        
        bootstrap_logger.info(f"QueryBootstrapGenerator initialized with GPT refinement: {self.use_gpt_refinement}")
    
    def apply_rules(self, query: str) -> Dict[str, Any]:
        """
        Generate JSON decision using rule-based heuristics
        
        Args:
            query: Raw legal query
            
        Returns:
            Dict containing structured decision
        """
        query_lower = query.lower().strip()
        
        # Determine if query needs boosting
        need_boost = self._needs_boosting(query_lower)
        
        # Generate boosted query if needed
        if need_boost:
            boosted_query = self._create_boosted_query(query)
        else:
            boosted_query = ""
        
        # Determine retrieval mode
        retrieval_mode = self._determine_retrieval_mode(query_lower)
        
        # Determine top_k
        top_k = self._determine_top_k(query_lower)
        
        # Determine if human review is required
        require_human_review = self._requires_human_review(query_lower)
        
        # Calculate confidence
        confidence = self._calculate_confidence(query_lower, need_boost, retrieval_mode)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(query_lower, need_boost, retrieval_mode, top_k)
        
        decision = {
            "query": query,
            "need_boost": need_boost,
            "boosted_query": boosted_query,
            "retrieval_mode": retrieval_mode,
            "top_k": top_k,
            "require_human_review": require_human_review,
            "confidence": confidence,
            "reasoning": reasoning,
            "method": "rule_based"
        }
        
        bootstrap_logger.info(f"Rule-based decision for '{query}': need_boost={need_boost}, mode={retrieval_mode}")
        return decision
    
    def refine_with_teacher(self, query: str, draft_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine the decision using GPT teacher model
        
        Args:
            query: Original query
            draft_json: Rule-based decision
            
        Returns:
            Refined decision
        """
        if not self.use_gpt_refinement:
            return draft_json
        
        try:
            # Create prompt for GPT refinement
            prompt = self._create_gpt_prompt(query, draft_json)
            
            # Call GPT API
            response = openai.ChatCompletion.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "You are a legal query enhancement expert. Refine the given JSON decision for better legal retrieval."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse GPT response
            gpt_response = response.choices[0].message.content.strip()
            refined_json = self._parse_gpt_response(gpt_response, draft_json)
            
            bootstrap_logger.info(f"GPT refinement completed for '{query}'")
            return refined_json
            
        except Exception as e:
            bootstrap_logger.error(f"GPT refinement failed for '{query}': {e}")
            return draft_json
    
    def _needs_boosting(self, query_lower: str) -> bool:
        """Determine if query needs boosting"""
        # Very short queries need boosting
        if len(query_lower.split()) <= 2:
            return True
        
        # Queries with vague terms need boosting
        if any(term in query_lower for term in self.legal_patterns['vague_terms']):
            if len(query_lower.split()) <= 5:
                return True
        
        # Queries that are too generic
        if query_lower in ['law', 'legal', 'rights', 'help', 'advice']:
            return True
        
        # Well-formed queries don't need boosting
        if any(term in query_lower for term in ['section', 'article', 'act', 'constitution']):
            if len(query_lower.split()) >= 4:
                return False
        
        return False
    
    def _create_boosted_query(self, query: str) -> str:
        """Create enhanced version of the query"""
        query_lower = query.lower()
        
        # Pattern-based enhancements
        if '377' in query_lower or '377 rights' in query_lower:
            return "Section 377 of the Indian Penal Code, Supreme Court judgments after 2018, constitutional validity"
        
        if 'privacy' in query_lower and 'article' in query_lower:
            return "Article 21 of the Constitution of India, right to privacy, Supreme Court cases after 2017, Puttaswamy judgment"
        
        if 'ipc' in query_lower and 'theft' in query_lower:
            return "Section 378 theft and Section 379 punishment under the Indian Penal Code, criminal law"
        
        if 'murder' in query_lower and 'punishment' in query_lower:
            return "Section 302 murder punishment under Indian Penal Code, criminal procedure, sentencing"
        
        if 'fundamental rights' in query_lower:
            return "Fundamental rights under Constitution of India, Articles 14-32, constitutional law, Supreme Court cases"
        
        if 'sedition' in query_lower and 'supreme court' in query_lower:
            return "Section 124A sedition law, Supreme Court judgments, constitutional validity, free speech"
        
        if 'dowry' in query_lower and 'prohibition' in query_lower:
            return "Dowry Prohibition Act 1961, Section 498A IPC, domestic violence, women's rights"
        
        if 'article 21' in query_lower and 'life' in query_lower:
            return "Article 21 right to life and personal liberty, Constitution of India, Supreme Court interpretations"
        
        # Generic enhancement
        return f"Indian legal aspects of {query} including relevant statutes, case law, and legal precedents"
    
    def _determine_retrieval_mode(self, query_lower: str) -> str:
        """Determine retrieval mode based on query content"""
        # Check for statute-specific terms
        statute_terms = sum(1 for term in self.legal_patterns['statute_keywords'] if term in query_lower)
        judgment_terms = sum(1 for term in self.legal_patterns['judgment_keywords'] if term in query_lower)
        
        if statute_terms > judgment_terms:
            return 'statutes'
        elif judgment_terms > statute_terms:
            return 'judgments'
        else:
            return 'both'
    
    def _determine_top_k(self, query_lower: str) -> int:
        """Determine appropriate top_k value"""
        word_count = len(query_lower.split())
        
        if word_count <= 3:
            return 5
        elif word_count <= 6:
            return 8
        else:
            return 10
    
    def _requires_human_review(self, query_lower: str) -> bool:
        """Determine if human review is required"""
        # Sensitive topics require human review
        if any(topic in query_lower for topic in self.legal_patterns['sensitive_topics']):
            return True
        
        # Very vague queries require human review
        if len(query_lower.split()) <= 2:
            return True
        
        # Queries asking for legal advice
        if any(phrase in query_lower for phrase in ['should i', 'can i', 'is it legal', 'advice', 'help me']):
            return True
        
        return False
    
    def _calculate_confidence(self, query_lower: str, need_boost: bool, retrieval_mode: str) -> float:
        """Calculate confidence score for the decision"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for specific legal terms
        if any(term in query_lower for term in ['section', 'article', 'act', 'constitution']):
            confidence += 0.2
        
        # Boost confidence for clear retrieval mode
        if retrieval_mode in ['statutes', 'judgments']:
            confidence += 0.1
        
        # Reduce confidence for very vague queries
        if len(query_lower.split()) <= 3:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_reasoning(self, query_lower: str, need_boost: bool, retrieval_mode: str, top_k: int) -> str:
        """Generate human-readable reasoning for the decision"""
        reasons = []
        
        if need_boost:
            reasons.append("Query is vague or too short, needs enhancement")
        else:
            reasons.append("Query is well-formed, no enhancement needed")
        
        if retrieval_mode == 'statutes':
            reasons.append("Query mentions specific legal provisions, focusing on statutes")
        elif retrieval_mode == 'judgments':
            reasons.append("Query mentions court cases or judgments, focusing on case law")
        else:
            reasons.append("Query is general, searching both statutes and judgments")
        
        reasons.append(f"Retrieving top {top_k} documents based on query complexity")
        
        return "; ".join(reasons)
    
    def _create_gpt_prompt(self, query: str, draft_json: Dict[str, Any]) -> str:
        """Create prompt for GPT refinement"""
        return f"""
Please refine this legal query decision for better retrieval:

Original Query: "{query}"

Current Decision:
- need_boost: {draft_json['need_boost']}
- boosted_query: "{draft_json['boosted_query']}"
- retrieval_mode: {draft_json['retrieval_mode']}
- top_k: {draft_json['top_k']}
- require_human_review: {draft_json['require_human_review']}

Please provide a refined JSON response with the same structure, improving:
1. The boosted_query to be more specific and legally precise
2. The retrieval_mode if needed
3. The top_k value if appropriate
4. The reasoning for the decision

Respond with only the JSON object, no additional text.
"""
    
    def _parse_gpt_response(self, gpt_response: str, fallback_json: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GPT response and merge with fallback"""
        try:
            # Extract JSON from response
            json_start = gpt_response.find('{')
            json_end = gpt_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = gpt_response[json_start:json_end]
                refined = json.loads(json_str)
                
                # Merge with fallback, keeping original query
                refined['query'] = fallback_json['query']
                refined['method'] = 'gpt_refined'
                
                return refined
        except Exception as e:
            bootstrap_logger.error(f"Failed to parse GPT response: {e}")
        
        # Return fallback with method updated
        fallback_json['method'] = 'gpt_refined'
        return fallback_json
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a single query through the pipeline"""
        bootstrap_logger.info(f"Processing query: {query}")
        
        # Step 1: Apply rule-based heuristics
        rule_based_decision = self.apply_rules(query)
        
        # Step 2: Optionally refine with GPT
        if self.use_gpt_refinement:
            final_decision = self.refine_with_teacher(query, rule_based_decision)
        else:
            final_decision = rule_based_decision
        
        bootstrap_logger.info(f"Final decision for '{query}': {final_decision['method']}")
        return final_decision

def save_jsonl(data: List[Dict[str, Any]], path: str):
    """Save dataset in JSONL format"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    bootstrap_logger.info(f"Saved {len(data)} entries to {path}")

def load_queries_from_file(file_path: str) -> List[str]:
    """Load queries from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        bootstrap_logger.info(f"Loaded {len(queries)} queries from {file_path}")
        return queries
    except FileNotFoundError:
        bootstrap_logger.error(f"Query file not found: {file_path}")
        return []

def main():
    """Main entry point for the bootstrap script"""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    bootstrap_logger.info("Starting Query Booster dataset bootstrap")
    
    # Sample queries (can be replaced with file loading)
    QUERIES = [
        "377 rights",
        "privacy article",
        "IPC theft",
        "punishment for murder",
        "fundamental rights under constitution",
        "Supreme Court case on sedition",
        "dowry prohibition act",
        "article 21 right to life",
        "section 302 IPC",
        "constitutional validity of Aadhaar",
        "right to information act",
        "consumer protection law",
        "labour law violations",
        "property dispute resolution",
        "criminal procedure code",
        "evidence act provisions",
        "contract law basics",
        "family law divorce",
        "taxation law compliance",
        "environmental protection act"
    ]
    
    # Configuration
    use_gpt_refinement = False  # Set to True if you have OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')  # Set your API key as environment variable
    
    # Initialize generator
    generator = QueryBootstrapGenerator(
        use_gpt_refinement=use_gpt_refinement,
        openai_api_key=openai_api_key
    )
    
    # Process all queries
    dataset = []
    start_time = time.time()
    
    for i, query in enumerate(QUERIES, 1):
        print(f"Processing query {i}/{len(QUERIES)}: {query}")
        
        try:
            decision = generator.process_query(query)
            dataset.append(decision)
            
            # Print progress
            print(f"  ✓ {decision['method']} - {decision['retrieval_mode']} - top_{decision['top_k']}")
            
        except Exception as e:
            bootstrap_logger.error(f"Error processing query '{query}': {e}")
            print(f"  ✗ Error: {e}")
    
    # Save dataset
    output_path = "data/query_booster.jsonl"
    save_jsonl(dataset, output_path)
    
    # Print summary
    processing_time = time.time() - start_time
    print(f"\n🎉 Dataset generation completed!")
    print(f"📊 Generated {len(dataset)} training examples")
    print(f"⏱️  Processing time: {processing_time:.2f}s")
    print(f"💾 Saved to: {output_path}")
    print(f"📝 Logs saved to: logs/data_bootstrap.log")
    
    # Print sample entries
    print(f"\n📋 Sample entries:")
    for i, entry in enumerate(dataset[:3], 1):
        print(f"\n--- Sample {i} ---")
        print(f"Query: {entry['query']}")
        print(f"Boosted: {entry['boosted_query']}")
        print(f"Mode: {entry['retrieval_mode']}")
        print(f"Top-K: {entry['top_k']}")
        print(f"Method: {entry['method']}")
    
    bootstrap_logger.info(f"Bootstrap completed: {len(dataset)} entries generated in {processing_time:.2f}s")

if __name__ == "__main__":
    main()

