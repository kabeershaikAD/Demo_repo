"""
Prompt Booster Agent using Flan-T5-small for query enhancement.
"""
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from datetime import datetime
import re


class PromptBoosterAgent(BaseAgent):
    """Agent that enhances vague legal queries into precise, searchable forms."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("PromptBooster", config)
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    async def initialize(self) -> bool:
        """Initialize the Flan-T5 model and tokenizer."""
        try:
            self.logger.info("Loading Flan-T5-small model...")
            
            model_name = self.config.get("model_name", "google/flan-t5-small")
            self.tokenizer = T5Tokenizer.from_pretrained(model_name)
            self.model = T5ForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            self.model.to(self.device)
            self.model.eval()
            
            self.logger.info(f"Model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PromptBooster: {e}")
            return False
    
    async def process(self, input_data: Any) -> AgentResponse:
        """Process and enhance the input query."""
        try:
            if isinstance(input_data, str):
                query = input_data
            elif isinstance(input_data, dict) and "query" in input_data:
                query = input_data["query"]
            else:
                raise ValueError("Input must be a string query or dict with 'query' key")
            
            # Generate enhanced query
            enhanced_query = await self._enhance_query(query)
            
            # Extract legal entities and concepts
            entities = self._extract_legal_entities(enhanced_query)
            
            # Generate search keywords
            keywords = self._generate_keywords(enhanced_query)
            
            result = {
                "original_query": query,
                "enhanced_query": enhanced_query,
                "legal_entities": entities,
                "search_keywords": keywords,
                "confidence_score": self._calculate_confidence(enhanced_query, query)
            }
            
            return AgentResponse(
                success=True,
                data=result,
                metadata={
                    "model_used": "google/flan-t5-small",
                    "device": self.device,
                    "query_length": len(query),
                    "enhancement_ratio": len(enhanced_query) / len(query) if query else 1.0
                },
                timestamp=datetime.now(),
                agent_name=self.name
            )
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return AgentResponse(
                success=False,
                data=None,
                metadata={},
                timestamp=datetime.now(),
                agent_name=self.name,
                error_message=str(e)
            )
    
    async def _enhance_query(self, query: str) -> str:
        """Enhance the query using Flan-T5."""
        try:
            # Create prompt for query enhancement
            prompt = f"""
            Rewrite this legal query to be more specific and precise for legal document search:
            
            Original query: {query}
            
            Enhanced query:"""
            
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate enhanced query
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode output
            enhanced_query = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up the output
            enhanced_query = enhanced_query.strip()
            if enhanced_query.startswith("Enhanced query:"):
                enhanced_query = enhanced_query.replace("Enhanced query:", "").strip()
            
            return enhanced_query
            
        except Exception as e:
            self.logger.error(f"Error enhancing query: {e}")
            return query  # Return original if enhancement fails
    
    def _extract_legal_entities(self, query: str) -> List[str]:
        """Extract legal entities and concepts from the query."""
        entities = []
        
        # Common legal terms and patterns
        legal_patterns = [
            r'\b(?:section|art\.|article|clause|subsection)\s+\d+[a-z]?',
            r'\b(?:act|statute|law|regulation|amendment)\s+of\s+\d{4}',
            r'\b(?:supreme court|high court|district court|tribunal)',
            r'\b(?:plaintiff|defendant|appellant|respondent)',
            r'\b(?:contract|tort|criminal|civil|constitutional)',
            r'\b(?:liability|damages|compensation|injunction)',
            r'\b(?:copyright|patent|trademark|intellectual property)',
            r'\b(?:employment|labor|workplace|discrimination)',
            r'\b(?:family|divorce|custody|adoption)',
            r'\b(?:property|real estate|land|tenancy)'
        ]
        
        for pattern in legal_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))  # Remove duplicates
    
    def _generate_keywords(self, query: str) -> List[str]:
        """Generate search keywords from the enhanced query."""
        # Simple keyword extraction (can be enhanced with NLP libraries)
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:10]  # Return top 10 keywords
    
    def _calculate_confidence(self, enhanced_query: str, original_query: str) -> float:
        """Calculate confidence score for the enhancement."""
        if not original_query:
            return 0.0
        
        # Simple confidence based on length increase and legal terms
        length_ratio = len(enhanced_query) / len(original_query)
        legal_terms = len(self._extract_legal_entities(enhanced_query))
        
        # Normalize confidence between 0 and 1
        confidence = min(1.0, (length_ratio - 1) * 0.5 + legal_terms * 0.1)
        return round(confidence, 2)
