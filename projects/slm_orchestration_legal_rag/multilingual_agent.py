"""
Multilingual Agent Module for Agentic Legal RAG
Handles language detection and translation for Indian languages
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time

# Translation imports (optional)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None
    AutoTokenizer = None
    AutoModelForSeq2SeqLM = None

from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LanguageDetectionResult:
    """Result of language detection"""
    language: str
    confidence: float
    is_english: bool
    detected_script: str

@dataclass
class TranslationResult:
    """Result of translation"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    processing_time: float

class MultilingualAgent:
    """Handles multilingual processing for Indian languages"""
    
    def __init__(self):
        # API PLACEHOLDER: Set your translation API keys here
        self.translation_model = None
        self.language_detector = None
        self._initialize_models()
        
        # Supported Indian languages
        self.supported_languages = {
            'hi': 'Hindi',
            'bn': 'Bengali', 
            'te': 'Telugu',
            'mr': 'Marathi',
            'ta': 'Tamil',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'or': 'Odia',
            'as': 'Assamese',
            'ne': 'Nepali',
            'ur': 'Urdu',
            'en': 'English'
        }
        
        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'translations_performed': 0,
            'language_detections': 0,
            'avg_processing_time': 0.0,
            'supported_language_queries': 0
        }
        
        logger.info("MultilingualAgent initialized")
    
    def _initialize_models(self):
        """Initialize translation and language detection models"""
        try:
            # Initialize translation pipeline
            # API PLACEHOLDER: Replace with actual model loading
            # self.translation_model = pipeline(
            #     "translation",
            #     model=config.TRANSLATION_MODEL,
            #     tokenizer=config.TRANSLATION_MODEL
            # )
            
            # For now, use a simple fallback
            self.translation_model = None
            logger.warning("Translation model not loaded. Using fallback mode.")
            
        except Exception as e:
            logger.error(f"Error initializing translation models: {e}")
            self.translation_model = None
    
    def detect_language(self, text: str) -> LanguageDetectionResult:
        """
        Detect the language of input text
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageDetectionResult: Language detection information
        """
        try:
            # Simple language detection based on script patterns
            script = self._detect_script(text)
            language = self._script_to_language(script)
            confidence = self._calculate_confidence(text, script)
            
            result = LanguageDetectionResult(
                language=language,
                confidence=confidence,
                is_english=(language == 'en'),
                detected_script=script
            )
            
            # Update metrics
            self.metrics['language_detections'] += 1
            
            logger.info(f"Language detected: {language} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            return LanguageDetectionResult(
                language='en',
                confidence=0.0,
                is_english=True,
                detected_script='latin'
            )
    
    def translate_text(self, text: str, source_lang: str = None, target_lang: str = 'en') -> TranslationResult:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language (auto-detect if None)
            target_lang: Target language (default: English)
            
        Returns:
            TranslationResult: Translation information
        """
        start_time = time.time()
        
        try:
            # Auto-detect source language if not provided
            if not source_lang:
                detection_result = self.detect_language(text)
                source_lang = detection_result.language
            
            # Check if translation is needed
            if source_lang == target_lang:
                return TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_language=source_lang,
                    target_language=target_lang,
                    confidence=1.0,
                    processing_time=time.time() - start_time
                )
            
            # Perform translation
            if self.translation_model:
                # API PLACEHOLDER: Use actual translation model
                # translated_text = self.translation_model(text, src_lang=source_lang, tgt_lang=target_lang)
                translated_text = self._fallback_translation(text, source_lang, target_lang)
            else:
                translated_text = self._fallback_translation(text, source_lang, target_lang)
            
            processing_time = time.time() - start_time
            
            result = TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_lang,
                confidence=0.8,  # Default confidence for fallback
                processing_time=processing_time
            )
            
            # Update metrics
            self.metrics['translations_performed'] += 1
            self.metrics['total_queries'] += 1
            
            logger.info(f"Translated from {source_lang} to {target_lang} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in translation: {e}")
            processing_time = time.time() - start_time
            return TranslationResult(
                original_text=text,
                translated_text=text,  # Return original on error
                source_language=source_lang or 'unknown',
                target_language=target_lang,
                confidence=0.0,
                processing_time=processing_time
            )
    
    def process_query(self, query: str, user_language: str = None) -> Dict[str, Any]:
        """
        Process a multilingual query
        
        Args:
            query: User query in any supported language
            user_language: Preferred language for response
            
        Returns:
            Dict containing processed query and language info
        """
        try:
            # Detect language
            detection_result = self.detect_language(query)
            
            # Translate to English if needed
            if not detection_result.is_english:
                translation_result = self.translate_text(query, detection_result.language, 'en')
                processed_query = translation_result.translated_text
            else:
                processed_query = query
                translation_result = None
            
            # Determine response language
            response_language = user_language or detection_result.language
            
            result = {
                'original_query': query,
                'processed_query': processed_query,
                'detected_language': detection_result.language,
                'language_confidence': detection_result.confidence,
                'translation_performed': translation_result is not None,
                'response_language': response_language,
                'is_english': detection_result.is_english
            }
            
            if translation_result:
                result['translation_result'] = {
                    'original_text': translation_result.original_text,
                    'translated_text': translation_result.translated_text,
                    'confidence': translation_result.confidence,
                    'processing_time': translation_result.processing_time
                }
            
            # Update metrics
            self.metrics['total_queries'] += 1
            if detection_result.language in self.supported_languages:
                self.metrics['supported_language_queries'] += 1
            
            logger.info(f"Processed query in {detection_result.language}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing multilingual query: {e}")
            return {
                'original_query': query,
                'processed_query': query,
                'detected_language': 'en',
                'language_confidence': 0.0,
                'translation_performed': False,
                'response_language': 'en',
                'is_english': True,
                'error': str(e)
            }
    
    def _detect_script(self, text: str) -> str:
        """Detect the script used in the text"""
        # Check for Devanagari (Hindi, Marathi, Sanskrit)
        if re.search(r'[\u0900-\u097F]', text):
            return 'devanagari'
        
        # Check for Bengali
        if re.search(r'[\u0980-\u09FF]', text):
            return 'bengali'
        
        # Check for Telugu
        if re.search(r'[\u0C00-\u0C7F]', text):
            return 'telugu'
        
        # Check for Tamil
        if re.search(r'[\u0B80-\u0BFF]', text):
            return 'tamil'
        
        # Check for Gujarati
        if re.search(r'[\u0A80-\u0AFF]', text):
            return 'gujarati'
        
        # Check for Kannada
        if re.search(r'[\u0C80-\u0CFF]', text):
            return 'kannada'
        
        # Check for Malayalam
        if re.search(r'[\u0D00-\u0D7F]', text):
            return 'malayalam'
        
        # Check for Punjabi (Gurmukhi)
        if re.search(r'[\u0A00-\u0A7F]', text):
            return 'gurmukhi'
        
        # Check for Odia
        if re.search(r'[\u0B00-\u0B7F]', text):
            return 'odia'
        
        # Check for Assamese
        if re.search(r'[\u0980-\u09FF]', text) and 'অ' in text:
            return 'assamese'
        
        # Check for Urdu (Arabic script)
        if re.search(r'[\u0600-\u06FF]', text):
            return 'arabic'
        
        # Default to Latin (English)
        return 'latin'
    
    def _script_to_language(self, script: str) -> str:
        """Map script to language code"""
        script_to_lang = {
            'devanagari': 'hi',  # Hindi (default for Devanagari)
            'bengali': 'bn',
            'telugu': 'te',
            'tamil': 'ta',
            'gujarati': 'gu',
            'kannada': 'kn',
            'malayalam': 'ml',
            'gurmukhi': 'pa',
            'odia': 'or',
            'assamese': 'as',
            'arabic': 'ur',
            'latin': 'en'
        }
        return script_to_lang.get(script, 'en')
    
    def _calculate_confidence(self, text: str, script: str) -> float:
        """Calculate confidence score for language detection"""
        if script == 'latin':
            # Check if it's actually English
            english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            words = text.lower().split()
            english_word_count = sum(1 for word in words if word in english_words)
            return min(english_word_count / max(len(words), 1), 1.0)
        else:
            # Higher confidence for non-Latin scripts
            return 0.9
    
    def _fallback_translation(self, text: str, source_lang: str, target_lang: str) -> str:
        """Fallback translation method"""
        # Simple fallback - return original text with a note
        if source_lang == target_lang:
            return text
        
        # API PLACEHOLDER: Implement actual translation
        # For now, return a placeholder
        return f"[TRANSLATION NEEDED: {text} from {source_lang} to {target_lang}]"
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported"""
        return language_code in self.supported_languages
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'total_queries': 0,
            'translations_performed': 0,
            'language_detections': 0,
            'avg_processing_time': 0.0,
            'supported_language_queries': 0
        }
        logger.info("MultilingualAgent metrics reset")
