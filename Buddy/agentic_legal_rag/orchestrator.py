"""
Orchestrator Module for Agentic Legal RAG
Manages the coordination between all agents and implements decision logic
"""

import logging
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from pathlib import Path

from config import config
from booster_agent import PromptBooster, BoosterDecision
from retriever_agent import RetrieverAgent
from answering_agent import AnsweringAgent
from citation_verifier import CitationVerifier
from multilingual_agent import MultilingualAgent
from updater import DynamicUpdater

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup orchestration-specific logging
orchestration_logger = logging.getLogger('orchestration')
orchestration_handler = logging.FileHandler('logs/orchestration.log')
orchestration_handler.setLevel(logging.INFO)
orchestration_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
orchestration_handler.setFormatter(orchestration_formatter)
orchestration_logger.addHandler(orchestration_handler)
orchestration_logger.setLevel(logging.INFO)

class AgentStatus(Enum):
    """Status of individual agents"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    DISABLED = "disabled"

class TaskStatus(Enum):
    """Status of overall task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"

@dataclass
class AgentState:
    """State of an individual agent"""
    agent_id: str
    agent_type: str
    status: AgentStatus
    last_activity: float
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}

@dataclass
class TaskContext:
    """Context for a processing task"""
    task_id: str
    user_query: str
    enhanced_query: Optional[str] = None
    language: str = "en"
    user_context: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: float = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TaskResult:
    """Result of a processing task"""
    task_id: str
    status: TaskStatus
    final_answer: Optional[str] = None
    citations: List[Dict[str, Any]] = None
    retrieved_documents: List[Dict[str, Any]] = None
    confidence_score: float = 0.0
    human_review_required: bool = False
    error_message: Optional[str] = None
    processing_time: float = 0.0
    agent_results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.citations is None:
            self.citations = []
        if self.retrieved_documents is None:
            self.retrieved_documents = []
        if self.agent_results is None:
            self.agent_results = {}

class Orchestrator:
    """Main orchestrator for managing all agents"""
    
    def __init__(self):
        self.agents = {}
        self.agent_states = {}
        self.task_queue = []
        self.completed_tasks = []
        
        # Initialize all agents
        self._initialize_agents()
        
        # Performance tracking
        self.performance_metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'average_response_time': 0.0,
            'human_review_cases': 0,
            'json_parsing_failures': 0,
            'fallback_queries_used': 0
        }
        
        orchestration_logger.info("Orchestrator initialized with all agents")
        logger.info("Orchestrator initialized with all agents")
    
    def _initialize_agents(self):
        """Initialize all agents with proper error handling"""
        try:
            # Initialize Prompt Booster Agent
            self.agents['prompt_booster'] = PromptBooster()
            self.agent_states['prompt_booster'] = AgentState(
                agent_id='prompt_booster',
                agent_type='query_enhancement',
                status=AgentStatus.IDLE,
                last_activity=time.time()
            )
            logger.info("Prompt Booster Agent initialized")
            
            # Initialize Retriever Agent
            self.agents['retriever'] = RetrieverAgent()
            self.agent_states['retriever'] = AgentState(
                agent_id='retriever',
                agent_type='document_retrieval',
                status=AgentStatus.IDLE,
                last_activity=time.time()
            )
            logger.info("Retriever Agent initialized")
            
            # Initialize Answering Agent
            self.agents['answering'] = AnsweringAgent()
            self.agent_states['answering'] = AgentState(
                agent_id='answering',
                agent_type='answer_generation',
                status=AgentStatus.IDLE,
                last_activity=time.time()
            )
            logger.info("Answering Agent initialized")
            
            # Initialize Citation Verifier
            self.agents['citation_verifier'] = CitationVerifier()
            self.agent_states['citation_verifier'] = AgentState(
                agent_id='citation_verifier',
                agent_type='citation_verification',
                status=AgentStatus.IDLE,
                last_activity=time.time()
            )
            logger.info("Citation Verifier Agent initialized")
            
            # Initialize Multilingual Agent
            self.agents['multilingual'] = MultilingualAgent()
            self.agent_states['multilingual'] = AgentState(
                agent_id='multilingual',
                agent_type='language_processing',
                status=AgentStatus.IDLE,
                last_activity=time.time()
            )
            logger.info("Multilingual Agent initialized")
            
            # Initialize Dynamic Updater
            self.agents['updater'] = DynamicUpdater()
            self.agent_states['updater'] = AgentState(
                agent_id='updater',
                agent_type='data_updates',
                status=AgentStatus.IDLE,
                last_activity=time.time()
            )
            logger.info("Dynamic Updater Agent initialized")
            
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise
    
    def run(self, query: str, language: str = "en", user_context: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Main method to process a user query through the agentic pipeline with structured JSON routing
        
        Args:
            query: The user's legal question
            language: Language of the query (default: "en")
            user_context: Additional context about the user
            session_id: Session identifier
            
        Returns:
            Dict: Complete result with answer, citations, and metadata
        """
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        orchestration_logger.info(f"Starting query processing - Task ID: {task_id}, Query: {query[:100]}...")
        
        try:
            # Step 1: Get decision from Prompt Booster
            orchestration_logger.info(f"Step 1: Getting decision from Prompt Booster")
            decision = self.agents['prompt_booster'].generate_decision(query)
            
            # Log the decision
            orchestration_logger.info(f"Decision: need_boost={decision.need_boost}, retrieval_mode={decision.retrieval_mode}, top_k={decision.top_k}")
            
            # Step 2: Apply fallback policy if needed
            if decision.need_boost and decision.boosted_query:
                # Use boosted query for retrieval
                retrieval_query = decision.boosted_query
                orchestration_logger.info(f"Using boosted query: {retrieval_query}")
            else:
                # Use original query
                retrieval_query = query
                orchestration_logger.info(f"Using original query: {retrieval_query}")
            
            # Step 3: Retrieve documents based on decision
            orchestration_logger.info(f"Step 3: Retrieving documents with mode={decision.retrieval_mode}, k={decision.top_k}")
            retrieved_docs = self._retrieve_documents_with_mode(retrieval_query, decision.retrieval_mode, decision.top_k)
            
            # Step 4: Apply fallback policy if retrieval scores are poor
            if decision.need_boost and decision.boosted_query:
                retrieval_scores = [doc.get('similarity_score', 0.0) for doc in retrieved_docs]
                final_query = self.agents['prompt_booster'].fallback_policy(query, decision.boosted_query, retrieval_scores)
                
                if final_query != retrieval_query:
                    orchestration_logger.info(f"Fallback policy applied: reverting to original query")
                    retrieved_docs = self._retrieve_documents_with_mode(query, decision.retrieval_mode, decision.top_k)
                    self.performance_metrics['fallback_queries_used'] += 1
            
            # Step 5: Verify citations
            orchestration_logger.info(f"Step 5: Verifying citations")
            verified_citations = self._verify_citations(retrieved_docs)
            
            # Step 6: Generate answer if supported
            if hasattr(self.agents['answering'], 'generate_answer'):
                orchestration_logger.info(f"Step 6: Generating answer")
                answer_result = self.agents['answering'].generate_answer(query, retrieval_query, retrieved_docs)
                final_answer = answer_result.get('answer_text', '')
            else:
                orchestration_logger.info(f"Step 6: Answering agent not available, returning UNVERIFIED")
                final_answer = "UNVERIFIED: human review required"
            
            # Step 7: Determine if human review is required
            human_review_required = decision.require_human_review or any(not claim.get('supported', False) for claim in verified_citations)
            
            # Step 8: Assemble final result
            processing_time = time.time() - start_time
            
            if human_review_required:
                self.performance_metrics['human_review_cases'] += 1
                orchestration_logger.info(f"Human review required")
                # Log to human review queue
                self._log_human_review_case(task_id, query, decision, verified_citations, processing_time)
            result = {
                'task_id': task_id,
                'query': query,
                'boosted_query': decision.boosted_query if decision.need_boost else '',
                'retrieval_mode': decision.retrieval_mode,
                'top_k': decision.top_k,
                'answer': final_answer,
                'citations': verified_citations,
                'retrieved_documents': retrieved_docs,
                'human_review_required': human_review_required,
                'processing_time': processing_time,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning
            }
            
            # Update performance metrics
            self._update_performance_metrics(True, processing_time)
            
            orchestration_logger.info(f"Query processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_performance_metrics(False, processing_time)
            
            orchestration_logger.error(f"Error processing query: {e}")
            
            return {
                'task_id': task_id,
                'query': query,
                'error': str(e),
                'processing_time': processing_time,
                'human_review_required': True
            }
    
    def _retrieve_documents_with_mode(self, query: str, retrieval_mode: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve documents based on specific mode and top_k"""
        try:
            self._update_agent_status('retriever', AgentStatus.PROCESSING)
            
            # Use Retriever Agent to find relevant documents
            retrieval_result = self.agents['retriever'].retrieve(query, k=top_k)
            
            # Convert RetrievalResult to list format
            documents = []
            if hasattr(retrieval_result, 'statutes') and retrieval_mode in ['statutes', 'both']:
                for doc in retrieval_result.statutes:
                    documents.append({
                        'title': doc.title,
                        'content': doc.content,
                        'doc_type': doc.doc_type,
                        'source': doc.source,
                        'similarity_score': doc.similarity_score,
                        'court': doc.court,
                        'date': doc.date,
                        'section': doc.section,
                        'act': doc.act,
                        'metadata': doc.metadata
                    })
            
            if hasattr(retrieval_result, 'judgments') and retrieval_mode in ['judgments', 'both']:
                for doc in retrieval_result.judgments:
                    documents.append({
                        'title': doc.title,
                        'content': doc.content,
                        'doc_type': doc.doc_type,
                        'source': doc.source,
                        'similarity_score': doc.similarity_score,
                        'court': doc.court,
                        'date': doc.date,
                        'section': doc.section,
                        'act': doc.act,
                        'metadata': doc.metadata
                    })
            
            self._update_agent_status('retriever', AgentStatus.COMPLETED)
            return documents
            
        except Exception as e:
            logger.error(f"Document retrieval error: {e}")
            self._update_agent_status('retriever', AgentStatus.ERROR, str(e))
            return []
    
    
    def _verify_citations(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verify citations using Citation Verifier Agent"""
        try:
            self._update_agent_status('citation_verifier', AgentStatus.PROCESSING)
            
            # Use Citation Verifier to verify claims
            verified_claims = self.agents['citation_verifier'].verify(
                [],  # No specific claims to verify
                retrieved_docs
            )
            
            self._update_agent_status('citation_verifier', AgentStatus.COMPLETED)
            return verified_claims
            
        except Exception as e:
            logger.error(f"Citation verification error: {e}")
            self._update_agent_status('citation_verifier', AgentStatus.ERROR, str(e))
            return []
    
    
    def _update_agent_status(self, agent_id: str, status: AgentStatus, error_message: str = None):
        """Update agent status and performance metrics"""
        if agent_id in self.agent_states:
            self.agent_states[agent_id].status = status
            self.agent_states[agent_id].last_activity = time.time()
            if error_message:
                self.agent_states[agent_id].error_message = error_message
    
    def _update_performance_metrics(self, success: bool, processing_time: float):
        """Update performance metrics"""
        self.performance_metrics['total_queries'] += 1
        if success:
            self.performance_metrics['successful_queries'] += 1
        else:
            self.performance_metrics['failed_queries'] += 1
        
        # Update average response time
        total_queries = self.performance_metrics['total_queries']
        current_avg = self.performance_metrics['average_response_time']
        self.performance_metrics['average_response_time'] = (
            (current_avg * (total_queries - 1) + processing_time) / total_queries
        )
        
        orchestration_logger.info(f"Performance metrics updated - Total: {total_queries}, Success: {self.performance_metrics['successful_queries']}, Failed: {self.performance_metrics['failed_queries']}")
    
    def get_agent_status(self) -> Dict[str, AgentState]:
        """Get current status of all agents"""
        return self.agent_states.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def reset_agent(self, agent_id: str):
        """Reset a specific agent"""
        if agent_id in self.agent_states:
            self.agent_states[agent_id].status = AgentStatus.IDLE
            self.agent_states[agent_id].error_message = None
            logger.info(f"Agent {agent_id} reset successfully")
    
    def _log_human_review_case(self, task_id: str, query: str, decision: BoosterDecision, 
                              verified_citations: List[Dict[str, Any]], processing_time: float):
        """Log human review cases to CSV file"""
        try:
            import csv
            import os
            from datetime import datetime
            
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            # CSV file path
            csv_file = 'logs/pending_human_review.csv'
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(csv_file)
            
            # Prepare data for CSV
            review_data = {
                'timestamp': datetime.now().isoformat(),
                'task_id': task_id,
                'query': query,
                'boosted_query': decision.boosted_query if decision.need_boost else '',
                'retrieval_mode': decision.retrieval_mode,
                'top_k': decision.top_k,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning,
                'citations_count': len(verified_citations),
                'unsupported_citations': sum(1 for c in verified_citations if not c.get('supported', False)),
                'processing_time': processing_time,
                'require_human_review': decision.require_human_review
            }
            
            # Write to CSV
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=review_data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(review_data)
            
            orchestration_logger.info(f"Human review case logged to {csv_file}")
            
        except Exception as e:
            orchestration_logger.error(f"Failed to log human review case: {e}")

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        total_agents = len(self.agent_states)
        healthy_agents = sum(1 for state in self.agent_states.values() 
                           if state.status != AgentStatus.ERROR)
        
        return {
            'total_agents': total_agents,
            'healthy_agents': healthy_agents,
            'health_percentage': (healthy_agents / total_agents) * 100 if total_agents > 0 else 0,
            'performance_metrics': self.performance_metrics,
            'agent_statuses': {agent_id: state.status.value for agent_id, state in self.agent_states.items()}
        }
