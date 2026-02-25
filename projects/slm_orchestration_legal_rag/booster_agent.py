"""
Prompt Booster Agent Module for Agentic Legal RAG
Uses Flan-T5 SLM to generate structured JSON decisions for query enhancement
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time

# Transformers imports (optional)
try:
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    T5ForConditionalGeneration = None
    T5Tokenizer = None
    torch = None

from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BoosterDecision:
    """Structured decision from Prompt Booster"""
    need_boost: bool
    boosted_query: str
    retrieval_mode: str  # "statutes", "judgments", "both"
    top_k: int
    require_human_review: bool
    confidence: float = 0.0
    reasoning: str = ""

class PromptBooster:
    """SLM-based query enhancement agent that generates structured JSON decisions"""
    
    def __init__(self, model_name: str = None, force_rule_based: bool = False):
        self.model_name = model_name or "google/flan-t5-small"
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        self.force_rule_based = force_rule_based
        
        if not self.force_rule_based:
            self._initialize_model()
        else:
            logger.info("Using rule-based enhancement for Indian legal context")
        
        # JSON prompt template for structured output
        self.json_prompt_template = self._initialize_json_prompt()
        
        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'json_parsing_success': 0,
            'json_parsing_failures': 0,
            'avg_processing_time': 0.0
        }
        
        logger.info("PromptBooster initialized for structured JSON output")
    
    def _initialize_model(self):
        """Initialize the Flan-T5 model"""
        try:
            if TRANSFORMERS_AVAILABLE:
                logger.info(f"Loading Flan-T5 model: {self.model_name}")
                self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
                self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
                self.model.to(self.device)
                logger.info(f"Flan-T5 model loaded successfully on {self.device}")
            else:
                self.model = None
                self.tokenizer = None
                logger.warning("Transformers not available. Using rule-based fallback mode.")
            
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            self.model = None
            self.tokenizer = None
            logger.warning("Flan-T5 model not loaded. Using fallback mode.")
    
    def _initialize_json_prompt(self) -> str:
        """Initialize the JSON prompt template for structured output"""
        return """Task: Analyze legal query and output ONLY valid JSON.

CRITICAL: Output must be valid JSON with exactly these fields:
- need_boost: boolean
- boosted_query: string  
- retrieval_mode: "statutes" or "judgments" or "both"
- top_k: number 1-20
- require_human_review: boolean

Rules:
1. Output ONLY the JSON object, no other text
2. All field names must be in double quotes
3. Boolean values must be true/false (not True/False)
4. String values must be in double quotes
5. Numbers must not be in quotes

Examples:

Query: "377 rights"
{"need_boost": true, "boosted_query": "Section 377 Indian Penal Code Supreme Court judgments", "retrieval_mode": "both", "top_k": 8, "require_human_review": false}

Query: "privacy article"  
{"need_boost": true, "boosted_query": "Article 21 Constitution right to privacy Supreme Court cases", "retrieval_mode": "judgments", "top_k": 6, "require_human_review": false}

Query: "What is the punishment for murder under Indian law?"
{"need_boost": false, "boosted_query": "", "retrieval_mode": "statutes", "top_k": 5, "require_human_review": false}

Query: "{query}"
JSON:"""
    
    def generate_decision(self, query: str) -> BoosterDecision:
        """
        Generate a structured decision for query processing
        
        Args:
            query: Original user query
            
        Returns:
            BoosterDecision: Structured decision with all required fields
        """
        start_time = time.time()
        
        try:
            if self.model and self.tokenizer and not self.force_rule_based:
                # Use SLM for structured JSON generation
                decision = self._generate_with_slm(query)
            else:
                # Use rule-based fallback
                decision = self._generate_with_rules(query)
            
            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(True, processing_time)
            
            logger.info(f"Decision generated in {processing_time:.2f}s")
            return decision
            
        except Exception as e:
            logger.error(f"Error generating decision: {e}")
            processing_time = time.time() - start_time
            self._update_metrics(False, processing_time)
            
            # Return fallback decision
            return self._create_fallback_decision(query)
    
    def _generate_with_slm(self, query: str) -> BoosterDecision:
        """Generate decision using SLM with structured JSON output"""
        try:
            # Prepare input text with JSON prompt
            input_text = self.json_prompt_template.format(query=query)
            logger.debug(f"SLM input: {input_text[:200]}...")
            
            # Tokenize input
            inputs = self.tokenizer.encode(input_text, return_tensors="pt", max_length=1024, truncation=True)
            inputs = inputs.to(self.device)
            
            # Generate structured output with better parameters for JSON generation
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=256,  # Reduced length for more focused output
                    num_beams=1,  # Use greedy decoding for more consistent output
                    early_stopping=True,
                    temperature=0.0,  # Zero temperature for deterministic output
                    do_sample=False,  # Disable sampling for more deterministic output
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,  # Higher repetition penalty
                    no_repeat_ngram_size=2,  # Avoid repeating 2-grams
                    length_penalty=1.0  # No length penalty
                )
            
            # Decode output
            raw_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.debug(f"SLM raw output: {raw_output}")
            
            # Clean the output - remove the input prompt part
            if "JSON:" in raw_output:
                raw_output = raw_output.split("JSON:")[-1].strip()
            
            # Extract JSON from output
            json_output = self._extract_json_from_output(raw_output)
            logger.debug(f"Extracted JSON: {json_output}")
            
            # Parse JSON and create decision
            decision_data = json.loads(json_output)
            
            # Validate the decision data
            if not isinstance(decision_data, dict):
                raise ValueError("Decision data is not a dictionary")
            
            # Ensure all required fields are present and valid
            need_boost = bool(decision_data.get('need_boost', False))
            boosted_query = str(decision_data.get('boosted_query', ''))
            retrieval_mode = str(decision_data.get('retrieval_mode', 'both'))
            top_k = int(decision_data.get('top_k', 5))
            require_human_review = bool(decision_data.get('require_human_review', False))
            
            # Validate retrieval_mode
            if retrieval_mode not in ['statutes', 'judgments', 'both']:
                logger.warning(f"Invalid retrieval_mode '{retrieval_mode}', defaulting to 'both'")
                retrieval_mode = 'both'
            
            # Validate top_k
            if not isinstance(top_k, int) or top_k < 1 or top_k > 20:
                logger.warning(f"Invalid top_k '{top_k}', defaulting to 5")
                top_k = 5
            
            return BoosterDecision(
                need_boost=need_boost,
                boosted_query=boosted_query,
                retrieval_mode=retrieval_mode,
                top_k=top_k,
                require_human_review=require_human_review,
                confidence=0.8,  # Default confidence for SLM
                reasoning="Generated by SLM"
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in SLM generation: {e}")
            return self._generate_with_rules(query)
        except Exception as e:
            logger.error(f"Error in SLM generation: {e}")
            return self._generate_with_rules(query)
    
    def _generate_with_rules(self, query: str) -> BoosterDecision:
        """Generate decision using rule-based approach"""
        query_lower = query.lower()
        
        # Determine if query needs boosting
        needs_boost = self._needs_boosting(query_lower)
        
        # Generate boosted query if needed
        if needs_boost:
            boosted_query = self._create_boosted_query(query)
        else:
            boosted_query = ""
        
        # Determine retrieval mode
        retrieval_mode = self._determine_retrieval_mode(query_lower)
        
        # Determine top_k
        top_k = self._determine_top_k(query_lower)
        
        # Determine if human review is required
        require_human_review = self._requires_human_review(query_lower)
        
        return BoosterDecision(
            need_boost=needs_boost,
            boosted_query=boosted_query,
            retrieval_mode=retrieval_mode,
            top_k=top_k,
            require_human_review=require_human_review,
            confidence=0.7,  # Rule-based confidence
            reasoning="Generated by rule-based system"
        )
    
    def _extract_json_from_output(self, raw_output: str) -> str:
        """Extract JSON from raw model output with improved pattern matching"""
        logger.debug(f"Raw SLM output: {raw_output}")
        
        # Clean the output first
        cleaned_output = raw_output.strip()
        
        # Try multiple JSON extraction patterns
        patterns = [
            # Pattern 1: Look for complete JSON object with all required fields
            r'\{[^{}]*"need_boost"[^{}]*"boosted_query"[^{}]*"retrieval_mode"[^{}]*"top_k"[^{}]*"require_human_review"[^{}]*\}',
            # Pattern 2: Look for JSON object starting with need_boost
            r'\{[^{}]*"need_boost"[^{}]*\}',
            # Pattern 3: Look for any JSON-like structure with braces
            r'\{[^{}]*\}',
            # Pattern 4: Look for JSON with nested structures (more permissive)
            r'\{.*?\}',
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, cleaned_output, re.DOTALL)
            if match:
                json_candidate = match.group(0)
                logger.debug(f"Pattern {i+1} matched: {json_candidate}")
                
                # Try to parse and validate the JSON
                try:
                    parsed = json.loads(json_candidate)
                    # Check if it has the required fields
                    required_fields = ['need_boost', 'boosted_query', 'retrieval_mode', 'top_k', 'require_human_review']
                    if all(field in parsed for field in required_fields):
                        logger.debug(f"Valid JSON extracted: {json_candidate}")
                        return json_candidate
                except json.JSONDecodeError:
                    logger.debug(f"JSON parsing failed for pattern {i+1}: {json_candidate}")
                    continue
        
        # If no valid JSON found, try to construct one from partial matches
        logger.warning("No valid JSON found in SLM output, attempting to construct from partial matches")
        
        # Extract individual field values using regex
        field_patterns = {
            'need_boost': r'"need_boost"\s*:\s*(true|false)',
            'boosted_query': r'"boosted_query"\s*:\s*"([^"]*)"',
            'retrieval_mode': r'"retrieval_mode"\s*:\s*"(statutes|judgments|both)"',
            'top_k': r'"top_k"\s*:\s*(\d+)',
            'require_human_review': r'"require_human_review"\s*:\s*(true|false)'
        }
        
        extracted_fields = {}
        for field, pattern in field_patterns.items():
            match = re.search(pattern, cleaned_output, re.IGNORECASE)
            if match:
                try:
                    if field in ['need_boost', 'require_human_review']:
                        extracted_fields[field] = match.group(1).lower() == 'true'
                    elif field == 'top_k':
                        extracted_fields[field] = int(match.group(1))
                    else:
                        extracted_fields[field] = match.group(1)
                except (ValueError, AttributeError) as e:
                    logger.debug(f"Error extracting field {field}: {e}")
                    continue
        
        # Construct JSON from extracted fields
        if extracted_fields:
            constructed_json = {
                'need_boost': extracted_fields.get('need_boost', False),
                'boosted_query': extracted_fields.get('boosted_query', ''),
                'retrieval_mode': extracted_fields.get('retrieval_mode', 'both'),
                'top_k': extracted_fields.get('top_k', 5),
                'require_human_review': extracted_fields.get('require_human_review', False)
            }
            logger.info(f"Constructed JSON from partial matches: {constructed_json}")
            return json.dumps(constructed_json)
        
        # Final fallback: return default JSON
        logger.warning("Failed to extract any JSON from SLM output, using fallback")
        return '{"need_boost": false, "boosted_query": "", "retrieval_mode": "both", "top_k": 5, "require_human_review": false}'
    
    def _needs_boosting(self, query_lower: str) -> bool:
        """Determine if query needs boosting based on patterns"""
        # Short queries need boosting
        if len(query_lower.split()) <= 3:
            return True
        
        # Queries with vague terms need boosting
        vague_terms = ['rights', 'law', 'act', 'section', 'article', 'case', 'court']
        if any(term in query_lower for term in vague_terms) and len(query_lower.split()) <= 5:
            return True
        
        # Queries with specific legal references don't need boosting
        # But short queries like "article 21" still need boosting for better retrieval
        specific_terms = ['section 302', 'ipc', 'constitution', 'supreme court']
        if any(term in query_lower for term in specific_terms):
            return False
        
        # Short article queries need boosting
        if 'article' in query_lower and len(query_lower.split()) <= 3:
            return True
        
        return False
    
    def _create_boosted_query(self, query: str) -> str:
        """Create a boosted query based on patterns"""
        query_lower = query.lower()
        
        # Specific legal pattern matching for better retrieval
        if '377' in query_lower or '377 rights' in query_lower:
            return "Section 377 of the Indian Penal Code, Supreme Court judgments after 2018, constitutional validity"
        
        if 'privacy' in query_lower and 'article' in query_lower:
            return "Article 21 of the Constitution of India, right to privacy, Supreme Court cases after 2017, Puttaswamy judgment"
        
        if 'ipc' in query_lower and 'theft' in query_lower:
            return "Section 378 theft and Section 379 punishment under the Indian Penal Code"
        
        if 'murder' in query_lower:
            return "Section 302 murder punishment under Indian Penal Code, criminal law"
        
        if 'fundamental rights' in query_lower:
            return "Fundamental rights under Constitution of India, Articles 14-32, constitutional law"
        
        # POCSO Act patterns
        if 'pocso' in query_lower:
            return "Protection of Children from Sexual Offences Act 2012, POCSO Act, child protection laws"
        
        if 'sedition' in query_lower:
            return "Section 124A Indian Penal Code sedition law, Supreme Court judgments, constitutional validity"
        
        if 'dowry' in query_lower:
            return "Dowry Prohibition Act 1961, Section 498A IPC domestic violence, dowry death"
        
        if 'aadhaar' in query_lower:
            return "Aadhaar Act 2016, privacy rights, Supreme Court Puttaswamy judgment, biometric data"
        
        if ('rti' in query_lower and 'article' not in query_lower) or 'right to information' in query_lower:
            return "Right to Information Act 2005, RTI Act, transparency, public information"
        
        if 'consumer' in query_lower:
            return "Consumer Protection Act 2019, consumer rights, redressal mechanisms, unfair trade practices"
        
        if 'labour' in query_lower or 'worker' in query_lower:
            return "Indian labour laws, Industrial Disputes Act, worker rights, employment law"
        
        if 'property' in query_lower:
            return "Property law in India, Transfer of Property Act, inheritance, succession law"
        
        if 'criminal procedure' in query_lower:
            return "Criminal Procedure Code 1973, CrPC, criminal procedure, investigation, trial"
        
        if 'evidence' in query_lower:
            return "Indian Evidence Act 1872, evidence law, admissibility, witness testimony"
        
        if 'contract' in query_lower:
            return "Indian Contract Act 1872, contract law, breach of contract, consideration"
        
        if 'divorce' in query_lower:
            return "Hindu Marriage Act 1955, Special Marriage Act 1954, divorce law, alimony, child custody"
        
        if 'tax' in query_lower:
            return "Income Tax Act 1961, GST Act, tax law, tax compliance, tax evasion"
        
        if 'environment' in query_lower:
            return "Environmental Protection Act 1986, environmental law, pollution control, climate change"
        
        if 'bail' in query_lower:
            return "Bail provisions under Criminal Procedure Code, types of bail, anticipatory bail"
        
        if 'cyber crime' in query_lower or 'cybercrime' in query_lower:
            return "Information Technology Act 2000, cybercrime laws, digital evidence, online offences"
        
        if 'article 21' in query_lower:
            return "Article 21 Constitution of India, right to life and personal liberty, fundamental rights, Maneka Gandhi case, Puttaswamy judgment"
        
        if 'section 302' in query_lower:
            return "Section 302 Indian Penal Code, murder punishment, criminal law, homicide"
        
        if 'section 124a' in query_lower:
            return "Section 124A Indian Penal Code, sedition law, freedom of speech, constitutional validity"
        
        # Generic enhancement with more specific legal context
        return f"Indian legal aspects of {query} including relevant statutes and case law"
    
    def _determine_retrieval_mode(self, query_lower: str) -> str:
        """Determine retrieval mode based on query content"""
        # If query mentions specific sections or articles, focus on statutes
        if any(term in query_lower for term in ['section', 'article', 'act', 'ipc', 'constitution']):
            return 'statutes'
        
        # If query mentions cases or judgments, focus on judgments
        if any(term in query_lower for term in ['case', 'judgment', 'court', 'supreme court', 'high court']):
            return 'judgments'
        
        # Default to both
        return 'both'
    
    def _determine_top_k(self, query_lower: str) -> int:
        """Determine top_k based on query complexity"""
        # Complex queries need more results
        if len(query_lower.split()) > 8:
            return 10
        
        # Simple queries need fewer results
        if len(query_lower.split()) <= 3:
            return 5
        
        # Default
        return 8
    
    def _requires_human_review(self, query_lower: str) -> bool:
        """Determine if human review is required"""
        # Sensitive topics require human review
        sensitive_topics = ['rape', 'murder', 'terrorism', 'sedition', 'contempt']
        if any(topic in query_lower for topic in sensitive_topics):
            return True
        
        # Very vague queries require human review
        if len(query_lower.split()) <= 2:
            return True
        
        return False
    
    def _create_fallback_decision(self, query: str) -> BoosterDecision:
        """Create a fallback decision when all else fails"""
        return BoosterDecision(
            need_boost=False,
            boosted_query="",
            retrieval_mode="both",
            top_k=5,
            require_human_review=True,
            confidence=0.0,
            reasoning="Fallback decision due to error"
        )
    
    def fallback_policy(self, query: str, boosted_query: str, retrieval_scores: list) -> str:
        """
        Fallback policy to choose between original and boosted query based on retrieval scores
        
        Args:
            query: Original query
            boosted_query: Boosted query
            retrieval_scores: List of similarity scores from retrieval
            
        Returns:
            str: The better query to use
        """
        if not retrieval_scores:
            return query
        
        # Calculate average score
        avg_score = sum(retrieval_scores) / len(retrieval_scores)
        
        # More lenient threshold - only revert if scores are very low
        if avg_score < 0.15:  # Reduced from 0.3 to 0.15
            logger.info("Reverting to original query due to very low retrieval scores")
            return query
        
        # If boosted query produces decent scores, use it
        if avg_score > 0.25:  # Reduced from 0.5 to 0.25
            return boosted_query
        
        # Default to boosted query for better legal context
        return boosted_query
    
    def _update_metrics(self, success: bool, processing_time: float):
        """Update performance metrics"""
        self.metrics['total_queries'] += 1
        
        if success:
            self.metrics['json_parsing_success'] += 1
        else:
            self.metrics['json_parsing_failures'] += 1
        
        # Update average processing time
        total_queries = self.metrics['total_queries']
        current_avg = self.metrics['avg_processing_time']
        self.metrics['avg_processing_time'] = (
            (current_avg * (total_queries - 1) + processing_time) / total_queries
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'total_queries': 0,
            'json_parsing_success': 0,
            'json_parsing_failures': 0,
            'avg_processing_time': 0.0
        }
        logger.info("PromptBooster metrics reset")
