#!/usr/bin/env python3
"""
AI Teacher Dataset Generator for Indian Legal Query Boosting
Generates 500 diverse Indian legal queries and their boosted versions using AI
"""

import os
import sys
import json
import logging
import random
from typing import List, Dict, Any, Tuple
from pathlib import Path
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Optional imports for AI teacher
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AITeacherDatasetGenerator:
    """AI Teacher for generating Indian legal query training data"""
    
    def __init__(self, use_openai: bool = True, openai_api_key: str = None):
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.openai_api_key = openai_api_key
        
        if self.use_openai and openai_api_key:
            openai.api_key = openai_api_key
        
        # Indian legal query templates and patterns
        self.query_templates = self._initialize_query_templates()
        self.legal_areas = self._initialize_legal_areas()
        self.boost_patterns = self._initialize_boost_patterns()
        
        logger.info(f"AI Teacher initialized - OpenAI: {self.use_openai}")
    
    def _initialize_query_templates(self) -> List[str]:
        """Initialize vague query templates for Indian legal context"""
        return [
            # Constitutional Law
            "What are my rights under {article}?",
            "Can I {action} under {article}?",
            "Is {action} constitutional?",
            "What does {article} say about {topic}?",
            "How does {article} protect {right}?",
            
            # Criminal Law
            "What is the punishment for {crime}?",
            "Is {action} a crime?",
            "What are the laws on {topic}?",
            "Can I be arrested for {action}?",
            "What happens if I {action}?",
            
            # Civil Law
            "How to {action}?",
            "What are my rights in {situation}?",
            "Can I {action} against {person}?",
            "What is the procedure for {process}?",
            "How to file {document}?",
            
            # Family Law
            "What are the grounds for {action}?",
            "How to get {document}?",
            "What are my rights in {relationship}?",
            "Can I {action} my {relative}?",
            "What is the law on {family_issue}?",
            
            # Property Law
            "How to {action} property?",
            "What are my rights as {role}?",
            "Can I {action} my {property}?",
            "What is the law on {property_issue}?",
            "How to resolve {property_dispute}?",
            
            # Labor Law
            "What are my rights as {worker}?",
            "Can my employer {action}?",
            "What is the law on {employment_issue}?",
            "How to file {complaint}?",
            "What are the working hours for {job}?",
            
            # Consumer Law
            "What are my rights as {consumer}?",
            "How to file {complaint} against {entity}?",
            "What is the law on {consumer_issue}?",
            "Can I get {compensation} for {problem}?",
            "What are the penalties for {violation}?",
            
            # Tax Law
            "What is the tax on {income}?",
            "How to file {tax_return}?",
            "What are the exemptions for {category}?",
            "Can I claim {deduction}?",
            "What is the penalty for {tax_violation}?",
            
            # General Legal
            "What is the law on {topic}?",
            "How to {action} legally?",
            "What are my rights regarding {issue}?",
            "Can I {action} without {requirement}?",
            "What is the procedure for {legal_process}?"
        ]
    
    def _initialize_legal_areas(self) -> Dict[str, List[str]]:
        """Initialize legal areas with specific Indian context"""
        return {
            "constitutional": [
                "Article 14", "Article 15", "Article 16", "Article 19", "Article 21", "Article 25", "Article 26",
                "Article 29", "Article 30", "Article 32", "Article 226", "Article 227", "Article 300A",
                "fundamental rights", "directive principles", "constitutional validity", "basic structure"
            ],
            "criminal": [
                "Section 302", "Section 304", "Section 307", "Section 376", "Section 420", "Section 498A",
                "Section 506", "Section 509", "Section 354", "Section 354A", "Section 354B", "Section 354C",
                "Section 354D", "Section 377", "Section 406", "Section 420", "Section 465", "Section 467",
                "Section 468", "Section 471", "Section 474", "Section 475", "Section 476", "Section 477",
                "murder", "rape", "theft", "cheating", "criminal breach of trust", "forgery", "criminal intimidation"
            ],
            "civil": [
                "Contract Act", "Specific Relief Act", "Limitation Act", "Evidence Act", "Civil Procedure Code",
                "contract", "tort", "negligence", "nuisance", "trespass", "defamation", "breach of contract"
            ],
            "family": [
                "Hindu Marriage Act", "Special Marriage Act", "Hindu Succession Act", "Guardians and Wards Act",
                "Protection of Women from Domestic Violence Act", "divorce", "maintenance", "custody", "adoption",
                "inheritance", "succession", "alimony", "domestic violence"
            ],
            "property": [
                "Transfer of Property Act", "Registration Act", "Stamp Act", "Land Acquisition Act",
                "property rights", "ownership", "possession", "lease", "mortgage", "sale", "gift", "will"
            ],
            "labor": [
                "Industrial Disputes Act", "Factories Act", "Minimum Wages Act", "Payment of Wages Act",
                "Employees' State Insurance Act", "Employees' Provident Fund Act", "Maternity Benefit Act",
                "wages", "working hours", "overtime", "leave", "termination", "retrenchment", "strike"
            ],
            "consumer": [
                "Consumer Protection Act", "Right to Information Act", "Competition Act", "Food Safety Act",
                "consumer rights", "defective goods", "deficiency in service", "unfair trade practice",
                "consumer forum", "compensation", "refund", "replacement"
            ],
            "tax": [
                "Income Tax Act", "GST Act", "Customs Act", "Central Excise Act", "Service Tax",
                "income tax", "GST", "TDS", "TCS", "tax return", "assessment", "appeal", "penalty"
            ]
        }
    
    def _initialize_boost_patterns(self) -> Dict[str, str]:
        """Initialize patterns for boosting queries"""
        return {
            "constitutional": "Constitution of India, {article}, Supreme Court judgments, High Court cases, constitutional law",
            "criminal": "Indian Penal Code, {section}, criminal law, Supreme Court cases, High Court judgments, criminal procedure",
            "civil": "Civil law, {act}, Supreme Court cases, High Court judgments, civil procedure, legal precedents",
            "family": "Family law, {act}, Supreme Court cases, High Court judgments, family court decisions, legal precedents",
            "property": "Property law, {act}, Supreme Court cases, High Court judgments, property rights, legal precedents",
            "labor": "Labor law, {act}, Supreme Court cases, High Court judgments, industrial disputes, legal precedents",
            "consumer": "Consumer law, {act}, Supreme Court cases, High Court judgments, consumer forum decisions, legal precedents",
            "tax": "Tax law, {act}, Supreme Court cases, High Court judgments, tax tribunal decisions, legal precedents"
        }
    
    def generate_vague_query(self) -> str:
        """Generate a vague Indian legal query"""
        template = random.choice(self.query_templates)
        legal_area = random.choice(list(self.legal_areas.keys()))
        
        # Fill in the template with Indian legal context
        if "{article}" in template:
            article = random.choice(self.legal_areas["constitutional"])
            template = template.replace("{article}", article)
        
        if "{section}" in template:
            section = random.choice(self.legal_areas["criminal"])
            template = template.replace("{section}", section)
        
        if "{act}" in template:
            act = random.choice(self.legal_areas[legal_area])
            template = template.replace("{act}", act)
        
        # Fill other placeholders with Indian context
        replacements = {
            "{action}": random.choice([
                "file a case", "get a divorce", "claim maintenance", "file a complaint", "get a stay order",
                "challenge the order", "appeal against", "get compensation", "claim damages", "get a bail"
            ]),
            "{topic}": random.choice([
                "right to privacy", "freedom of speech", "equality", "religious freedom", "property rights",
                "labor rights", "consumer rights", "tax obligations", "criminal liability", "civil liability"
            ]),
            "{right}": random.choice([
                "privacy", "speech", "equality", "religion", "property", "labor", "consumer", "life", "liberty"
            ]),
            "{crime}": random.choice([
                "murder", "rape", "theft", "cheating", "forgery", "criminal breach of trust", "criminal intimidation"
            ]),
            "{situation}": random.choice([
                "marriage", "divorce", "employment", "property dispute", "consumer complaint", "tax assessment"
            ]),
            "{person}": random.choice([
                "employer", "landlord", "tenant", "spouse", "neighbor", "business partner", "government"
            ]),
            "{process}": random.choice([
                "divorce", "property registration", "tax filing", "criminal trial", "civil suit", "appeal"
            ]),
            "{document}": random.choice([
                "divorce petition", "property deed", "tax return", "criminal complaint", "civil suit", "appeal"
            ]),
            "{relationship}": random.choice([
                "marriage", "parent-child", "employer-employee", "landlord-tenant", "buyer-seller"
            ]),
            "{relative}": random.choice([
                "spouse", "parent", "child", "sibling", "in-law"
            ]),
            "{family_issue}": random.choice([
                "divorce", "maintenance", "custody", "adoption", "inheritance", "domestic violence"
            ]),
            "{role}": random.choice([
                "owner", "tenant", "buyer", "seller", "employer", "employee", "consumer", "taxpayer"
            ]),
            "{property}": random.choice([
                "house", "land", "commercial property", "agricultural land", "flat", "shop"
            ]),
            "{property_issue}": random.choice([
                "ownership", "possession", "lease", "mortgage", "sale", "gift", "inheritance"
            ]),
            "{property_dispute}": random.choice([
                "boundary dispute", "ownership dispute", "possession dispute", "lease dispute", "inheritance dispute"
            ]),
            "{worker}": random.choice([
                "employee", "worker", "laborer", "contract worker", "temporary worker", "permanent worker"
            ]),
            "{employment_issue}": random.choice([
                "wages", "working hours", "overtime", "leave", "termination", "retrenchment", "strike"
            ]),
            "{complaint}": random.choice([
                "labor complaint", "consumer complaint", "criminal complaint", "civil suit", "appeal"
            ]),
            "{job}": random.choice([
                "factory worker", "office worker", "construction worker", "domestic worker", "driver"
            ]),
            "{consumer}": random.choice([
                "buyer", "customer", "user", "client", "purchaser"
            ]),
            "{entity}": random.choice([
                "seller", "manufacturer", "service provider", "government", "bank", "insurance company"
            ]),
            "{consumer_issue}": random.choice([
                "defective goods", "deficiency in service", "unfair trade practice", "overcharging", "false advertising"
            ]),
            "{compensation}": random.choice([
                "refund", "replacement", "damages", "compensation", "penalty"
            ]),
            "{problem}": random.choice([
                "defective product", "poor service", "overcharging", "false advertising", "delayed delivery"
            ]),
            "{violation}": random.choice([
                "consumer rights", "labor laws", "tax laws", "criminal laws", "civil laws"
            ]),
            "{income}": random.choice([
                "salary", "business income", "capital gains", "rental income", "interest income"
            ]),
            "{tax_return}": random.choice([
                "income tax return", "GST return", "TDS return", "advance tax", "self-assessment"
            ]),
            "{category}": random.choice([
                "senior citizen", "woman", "disabled person", "farmer", "small business", "startup"
            ]),
            "{deduction}": random.choice([
                "standard deduction", "medical expenses", "home loan interest", "education expenses", "charitable donations"
            ]),
            "{tax_violation}": random.choice([
                "non-filing", "under-reporting", "evasion", "non-payment", "late filing"
            ]),
            "{issue}": random.choice([
                "property rights", "labor rights", "consumer rights", "tax obligations", "criminal liability"
            ]),
            "{requirement}": random.choice([
                "permission", "license", "registration", "approval", "consent"
            ]),
            "{legal_process}": random.choice([
                "criminal trial", "civil suit", "appeal", "arbitration", "mediation", "conciliation"
            ])
        }
        
        # Apply replacements
        for placeholder, replacement in replacements.items():
            if placeholder in template:
                template = template.replace(placeholder, replacement)
        
        return template
    
    def generate_boosted_query_ai(self, vague_query: str) -> str:
        """Generate boosted query using AI teacher"""
        if not self.use_openai:
            return self._generate_boosted_query_rule_based(vague_query)
        
        try:
            prompt = f"""
You are an expert Indian legal researcher. Given a vague legal query, create a precise, detailed query that would retrieve the most relevant legal documents from an Indian legal database.

Vague Query: "{vague_query}"

Create a boosted query that:
1. Specifies relevant Indian legal acts, sections, and articles
2. Includes relevant court levels (Supreme Court, High Court, District Court)
3. Mentions specific legal concepts and terminology
4. Adds relevant timeframes or contexts
5. Uses proper legal language

The boosted query should be comprehensive but focused on Indian legal context. Do not include "India" in every query - focus on specific legal provisions, acts, and cases.

Boosted Query:"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert Indian legal researcher specializing in query enhancement for legal document retrieval."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"AI generation failed: {e}, falling back to rule-based")
            return self._generate_boosted_query_rule_based(vague_query)
    
    def _generate_boosted_query_rule_based(self, vague_query: str) -> str:
        """Generate boosted query using rule-based approach"""
        query_lower = vague_query.lower()
        
        # Determine legal area
        if any(term in query_lower for term in ["article", "constitution", "fundamental", "rights"]):
            area = "constitutional"
        elif any(term in query_lower for term in ["section", "crime", "criminal", "punishment", "arrest"]):
            area = "criminal"
        elif any(term in query_lower for term in ["marriage", "divorce", "family", "custody", "maintenance"]):
            area = "family"
        elif any(term in query_lower for term in ["property", "land", "house", "ownership"]):
            area = "property"
        elif any(term in query_lower for term in ["labor", "worker", "employee", "wages", "employment"]):
            area = "labor"
        elif any(term in query_lower for term in ["consumer", "buyer", "customer", "complaint"]):
            area = "consumer"
        elif any(term in query_lower for term in ["tax", "income", "gst", "return"]):
            area = "tax"
        else:
            area = "civil"
        
        # Generate boosted query
        if area == "constitutional":
            articles = random.sample(self.legal_areas["constitutional"][:10], 2)
            return f"{articles[0]} and {articles[1]} of Constitution of India, Supreme Court judgments, High Court cases, constitutional law, fundamental rights"
        elif area == "criminal":
            sections = random.sample(self.legal_areas["criminal"][:10], 2)
            return f"{sections[0]} and {sections[1]} of Indian Penal Code, criminal law, Supreme Court cases, High Court judgments, criminal procedure"
        elif area == "family":
            acts = random.sample(self.legal_areas["family"][:3], 1)
            return f"{acts[0]}, family law, Supreme Court cases, High Court judgments, family court decisions, legal precedents"
        elif area == "property":
            acts = random.sample(self.legal_areas["property"][:3], 1)
            return f"{acts[0]}, property law, Supreme Court cases, High Court judgments, property rights, legal precedents"
        elif area == "labor":
            acts = random.sample(self.legal_areas["labor"][:3], 1)
            return f"{acts[0]}, labor law, Supreme Court cases, High Court judgments, industrial disputes, legal precedents"
        elif area == "consumer":
            acts = random.sample(self.legal_areas["consumer"][:3], 1)
            return f"{acts[0]}, consumer law, Supreme Court cases, High Court judgments, consumer forum decisions, legal precedents"
        elif area == "tax":
            acts = random.sample(self.legal_areas["tax"][:3], 1)
            return f"{acts[0]}, tax law, Supreme Court cases, High Court judgments, tax tribunal decisions, legal precedents"
        else:
            return f"Civil law, Supreme Court cases, High Court judgments, civil procedure, legal precedents, {vague_query}"
    
    def determine_retrieval_mode(self, vague_query: str, boosted_query: str) -> str:
        """Determine retrieval mode based on query content"""
        query_lower = vague_query.lower()
        boosted_lower = boosted_query.lower()
        
        if any(term in query_lower for term in ["article", "constitution", "fundamental", "rights"]) or \
           any(term in boosted_lower for term in ["article", "constitution", "section", "act", "code"]):
            return "statutes"
        elif any(term in query_lower for term in ["case", "judgment", "court", "ruling", "precedent"]) or \
             any(term in boosted_lower for term in ["supreme court", "high court", "judgment", "case"]):
            return "judgments"
        else:
            return "both"
    
    def determine_top_k(self, vague_query: str, boosted_query: str) -> int:
        """Determine top_k based on query complexity"""
        query_length = len(vague_query.split())
        boosted_length = len(boosted_query.split())
        
        if query_length > 10 or boosted_length > 20:
            return random.choice([8, 10])
        elif query_length > 5 or boosted_length > 15:
            return random.choice([6, 8])
        else:
            return random.choice([5, 6])
    
    def determine_human_review(self, vague_query: str, boosted_query: str) -> bool:
        """Determine if human review is required"""
        sensitive_keywords = [
            "rape", "murder", "terrorism", "sedition", "contempt", "hate speech",
            "suicide", "euthanasia", "abortion", "euthanasia", "assisted suicide"
        ]
        
        query_lower = vague_query.lower()
        boosted_lower = boosted_query.lower()
        
        if any(keyword in query_lower for keyword in sensitive_keywords) or \
           any(keyword in boosted_lower for keyword in sensitive_keywords):
            return True
        
        if len(vague_query.split()) < 3:
            return True
        
        return False
    
    def generate_training_example(self) -> Dict[str, Any]:
        """Generate a single training example"""
        # Generate vague query
        vague_query = self.generate_vague_query()
        
        # Generate boosted query
        boosted_query = self.generate_boosted_query_ai(vague_query)
        
        # Determine other parameters
        retrieval_mode = self.determine_retrieval_mode(vague_query, boosted_query)
        top_k = self.determine_top_k(vague_query, boosted_query)
        require_human_review = self.determine_human_review(vague_query, boosted_query)
        
        # Determine need_boost
        need_boost = len(vague_query.split()) < 8 or any(term in vague_query.lower() for term in [
            "what", "how", "can", "is", "are", "rights", "law", "punishment", "procedure"
        ])
        
        return {
            "query": vague_query,
            "need_boost": need_boost,
            "boosted_query": boosted_query if need_boost else "",
            "retrieval_mode": retrieval_mode,
            "top_k": top_k,
            "require_human_review": require_human_review,
            "confidence": random.uniform(0.6, 0.9),
            "reasoning": f"Query classified as {retrieval_mode} retrieval with {'boosted' if need_boost else 'original'} query"
        }
    
    def generate_dataset(self, num_examples: int = 500, output_file: str = "data/ai_teacher_dataset.jsonl") -> str:
        """Generate complete training dataset"""
        logger.info(f"Generating {num_examples} training examples using AI teacher method...")
        
        # Create output directory
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Generate examples
        examples = []
        for i in range(num_examples):
            if i % 50 == 0:
                logger.info(f"Generated {i}/{num_examples} examples...")
            
            example = self.generate_training_example()
            examples.append(example)
            
            # Small delay to avoid rate limiting
            if self.use_openai and i % 10 == 0:
                time.sleep(0.1)
        
        # Save dataset
        with open(output_file, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        logger.info(f"Dataset saved to {output_file}")
        
        # Generate statistics
        self._generate_dataset_statistics(examples, output_file)
        
        return output_file
    
    def _generate_dataset_statistics(self, examples: List[Dict[str, Any]], output_file: str):
        """Generate and save dataset statistics"""
        stats = {
            "total_examples": len(examples),
            "boost_distribution": {
                "boosted": sum(1 for ex in examples if ex["need_boost"]),
                "not_boosted": sum(1 for ex in examples if not ex["need_boost"])
            },
            "retrieval_mode_distribution": {},
            "top_k_distribution": {},
            "human_review_distribution": {
                "required": sum(1 for ex in examples if ex["require_human_review"]),
                "not_required": sum(1 for ex in examples if not ex["require_human_review"])
            },
            "average_query_length": sum(len(ex["query"].split()) for ex in examples) / len(examples),
            "average_boosted_length": sum(len(ex["boosted_query"].split()) for ex in examples if ex["boosted_query"]) / max(1, sum(1 for ex in examples if ex["boosted_query"]))
        }
        
        # Count retrieval modes
        for example in examples:
            mode = example["retrieval_mode"]
            stats["retrieval_mode_distribution"][mode] = stats["retrieval_mode_distribution"].get(mode, 0) + 1
        
        # Count top_k values
        for example in examples:
            top_k = example["top_k"]
            stats["top_k_distribution"][str(top_k)] = stats["top_k_distribution"].get(str(top_k), 0) + 1
        
        # Save statistics
        stats_file = output_file.replace('.jsonl', '_stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dataset statistics saved to {stats_file}")
        
        # Print summary
        print(f"\n📊 Dataset Statistics:")
        print(f"   Total examples: {stats['total_examples']}")
        print(f"   Boost distribution: {stats['boost_distribution']}")
        print(f"   Retrieval modes: {stats['retrieval_mode_distribution']}")
        print(f"   Top-K distribution: {stats['top_k_distribution']}")
        print(f"   Human review: {stats['human_review_distribution']}")
        print(f"   Avg query length: {stats['average_query_length']:.1f} words")
        print(f"   Avg boosted length: {stats['average_boosted_length']:.1f} words")

def main():
    """Main function to generate dataset"""
    logger.info("🚀 AI Teacher Dataset Generator for Indian Legal Queries")
    logger.info("=" * 60)
    
    # Check if OpenAI is available
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        logger.warning("OpenAI API key not found. Using rule-based generation only.")
        use_openai = False
    else:
        use_openai = True
        logger.info("OpenAI API key found. Using AI teacher method.")
    
    # Initialize generator
    generator = AITeacherDatasetGenerator(use_openai=use_openai, openai_api_key=openai_key)
    
    # Generate dataset
    output_file = "data/ai_teacher_dataset.jsonl"
    dataset_path = generator.generate_dataset(num_examples=500, output_file=output_file)
    
    print(f"\n🎉 Dataset generation completed!")
    print(f"📁 Dataset saved to: {dataset_path}")
    print(f"📊 Statistics saved to: {dataset_path.replace('.jsonl', '_stats.json')}")
    
    # Show sample examples
    print(f"\n📋 Sample Examples:")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:  # Show first 3 examples
                break
            example = json.loads(line)
            print(f"\n--- Example {i+1} ---")
            print(f"Query: {example['query']}")
            print(f"Boosted: {example['boosted_query']}")
            print(f"Mode: {example['retrieval_mode']}, Top-K: {example['top_k']}")
            print(f"Need Boost: {example['need_boost']}, Human Review: {example['require_human_review']}")

if __name__ == "__main__":
    main()
