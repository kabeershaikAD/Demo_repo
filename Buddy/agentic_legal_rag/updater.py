"""
Dynamic Updater Module for Agentic Legal RAG
Manages dynamic ingestion of new legal data from various sources
"""

import logging
import time
import json
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import schedule
import threading

from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UpdateSource:
    """Configuration for an update source"""
    name: str
    url: str
    api_key: str = None
    update_frequency: int = 3600  # seconds
    last_updated: datetime = None
    enabled: bool = True
    source_type: str = 'api'  # 'api', 'rss', 'scraper'
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class UpdateResult:
    """Result of an update operation"""
    source_name: str
    success: bool
    documents_added: int
    documents_updated: int
    documents_removed: int
    processing_time: float
    error_message: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DynamicUpdater:
    """Manages dynamic updates of legal data"""
    
    def __init__(self):
        self.sources = self._initialize_sources()
        self.update_thread = None
        self.running = False
        
        # Performance metrics
        self.metrics = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'total_documents_added': 0,
            'total_documents_updated': 0,
            'last_update_time': None,
            'avg_update_time': 0.0
        }
        
        logger.info("DynamicUpdater initialized")
    
    def _initialize_sources(self) -> List[UpdateSource]:
        """Initialize update sources using FREE and OPEN data sources"""
        sources = [
            # FREE: ILDC Dataset (35k+ judgments)
            UpdateSource(
                name="ILDC Dataset",
                url="https://zenodo.org/record/4599830/files/ILDC_single.zip",
                update_frequency=86400,  # 24 hours (daily check)
                source_type='dataset',
                metadata={
                    'description': 'Indian Legal Documents Corpus - 35k+ judgments',
                    'format': 'JSON',
                    'size': '~2GB',
                    'free': True,
                    'bulk_download': True
                }
            ),
            
            # FREE: Legislative.gov.in (Bare Acts, Constitution)
            UpdateSource(
                name="Legislative.gov.in",
                url="https://legislative.gov.in/",
                update_frequency=43200,  # 12 hours
                source_type='scraper',
                metadata={
                    'description': 'Official legislative website - Bare Acts, Constitution, Amendments',
                    'sections': ['constitution', 'bare-acts', 'amendments'],
                    'free': True,
                    'official': True
                }
            ),
            
            # FREE: Supreme Court RSS
            UpdateSource(
                name="Supreme Court RSS",
                url="https://main.sci.gov.in/rss/judgments.xml",
                update_frequency=7200,  # 2 hours
                source_type='rss',
                metadata={
                    'description': 'Supreme Court judgments RSS feed',
                    'free': True,
                    'official': True
                }
            ),
            
            # FREE: High Court Websites (PDFs)
            UpdateSource(
                name="High Courts PDFs",
                url="https://www.hc.tn.gov.in/judis/",
                update_frequency=14400,  # 4 hours
                source_type='scraper',
                metadata={
                    'description': 'High Court judgment PDFs',
                    'courts': ['Madras', 'Delhi', 'Bombay', 'Calcutta', 'Karnataka'],
                    'free': True,
                    'official': True
                }
            ),
            
            # OPTIONAL: Indian Kanoon (for incremental updates only)
            UpdateSource(
                name="Indian Kanoon (Incremental)",
                url="https://api.indiankanoon.org/search/",
                api_key=config.api.INDIAN_KANOON_API_KEY,
                update_frequency=3600,  # 1 hour
                source_type='api',
                enabled=False,  # Disabled by default
                metadata={
                    'description': 'Indian Kanoon API for fresh judgments only',
                    'usage': 'incremental_updates',
                    'free_tier': True,
                    'bulk_download': False
                }
            )
        ]
        
        return sources
    
    def start_auto_updates(self):
        """Start automatic updates in background thread"""
        if self.running:
            logger.warning("Auto updates already running")
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._run_auto_updates, daemon=True)
        self.update_thread.start()
        logger.info("Auto updates started")
    
    def stop_auto_updates(self):
        """Stop automatic updates"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("Auto updates stopped")
    
    def _run_auto_updates(self):
        """Run automatic updates in background"""
        while self.running:
            try:
                # Check each source for updates
                for source in self.sources:
                    if not source.enabled:
                        continue
                    
                    # Check if it's time to update
                    if self._should_update_source(source):
                        self._update_source(source)
                
                # Sleep for a minute before checking again
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in auto update loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def _should_update_source(self, source: UpdateSource) -> bool:
        """Check if a source should be updated"""
        if not source.last_updated:
            return True
        
        time_since_update = datetime.now() - source.last_updated
        return time_since_update.total_seconds() >= source.update_frequency
    
    def _update_source(self, source: UpdateSource) -> UpdateResult:
        """Update a specific source"""
        start_time = time.time()
        
        try:
            logger.info(f"Updating source: {source.name}")
            
            if source.source_type == 'dataset':
                result = self._update_from_dataset(source)
            elif source.source_type == 'scraper':
                result = self._update_from_scraper(source)
            elif source.source_type == 'rss':
                result = self._update_from_rss(source)
            elif source.source_type == 'api':
                result = self._update_from_api(source)
            else:
                result = UpdateResult(
                    source_name=source.name,
                    success=False,
                    documents_added=0,
                    documents_updated=0,
                    documents_removed=0,
                    processing_time=time.time() - start_time,
                    error_message=f"Unknown source type: {source.source_type}"
                )
            
            # Update source timestamp
            source.last_updated = datetime.now()
            
            # Update metrics
            self._update_metrics(result)
            
            logger.info(f"Updated {source.name}: {result.documents_added} added, {result.documents_updated} updated")
            return result
            
        except Exception as e:
            logger.error(f"Error updating source {source.name}: {e}")
            result = UpdateResult(
                source_name=source.name,
                success=False,
                documents_added=0,
                documents_updated=0,
                documents_removed=0,
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
            self._update_metrics(result)
            return result
    
    def _update_from_dataset(self, source: UpdateSource) -> UpdateResult:
        """Update from dataset source (ILDC)"""
        try:
            logger.info(f"Processing dataset: {source.name}")
            
            # For ILDC dataset, we would:
            # 1. Download the dataset if not exists
            # 2. Extract and parse JSON files
            # 3. Process judgments and add to database
            
            documents_added = 0
            documents_updated = 0
            
            # API PLACEHOLDER: Implement ILDC dataset processing
            # if source.name == "ILDC Dataset":
            #     documents_added = self._process_ildc_dataset(source)
            
            logger.info(f"Dataset {source.name} processed: {documents_added} documents")
            
            return UpdateResult(
                source_name=source.name,
                success=True,
                documents_added=documents_added,
                documents_updated=documents_updated,
                documents_removed=0,
                processing_time=time.time() - time.time(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Dataset update failed: {e}")
    
    def _update_from_scraper(self, source: UpdateSource) -> UpdateResult:
        """Update from scraper source (legislative.gov.in, court websites)"""
        try:
            logger.info(f"Scraping: {source.name}")
            
            documents_added = 0
            documents_updated = 0
            
            # API PLACEHOLDER: Implement web scraping
            # if source.name == "Legislative.gov.in":
            #     documents_added = self._scrape_legislative_website(source)
            # elif source.name == "High Courts PDFs":
            #     documents_added = self._scrape_high_court_pdfs(source)
            
            logger.info(f"Scraped {source.name}: {documents_added} documents")
            
            return UpdateResult(
                source_name=source.name,
                success=True,
                documents_added=documents_added,
                documents_updated=documents_updated,
                documents_removed=0,
                processing_time=time.time() - time.time(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Scraper update failed: {e}")
    
    def _update_from_api(self, source: UpdateSource) -> UpdateResult:
        """Update from API source (Indian Kanoon - incremental only)"""
        try:
            # Only for incremental updates, not bulk download
            if not source.api_key or source.api_key == "YOUR_INDIAN_KANOON_API_KEY_HERE":
                logger.warning(f"API key not configured for {source.name}")
                return UpdateResult(
                    source_name=source.name,
                    success=False,
                    documents_added=0,
                    documents_updated=0,
                    documents_removed=0,
                    processing_time=0.0,
                    error_message="API key not configured"
                )
            
            # API PLACEHOLDER: Implement incremental API calls
            # headers = {'Authorization': f'Bearer {source.api_key}'} if source.api_key else {}
            # response = requests.get(source.url, headers=headers, timeout=30)
            # response.raise_for_status()
            # data = response.json()
            
            documents_added = 0
            documents_updated = 0
            
            # API PLACEHOLDER: Process incremental updates only
            # for doc in data.get('documents', []):
            #     if self._process_document(doc, source):
            #         documents_added += 1
            
            return UpdateResult(
                source_name=source.name,
                success=True,
                documents_added=documents_added,
                documents_updated=documents_updated,
                documents_removed=0,
                processing_time=time.time() - time.time(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"API update failed: {e}")
    
    def _update_from_rss(self, source: UpdateSource) -> UpdateResult:
        """Update from RSS source"""
        try:
            # API PLACEHOLDER: Implement RSS parsing
            # import feedparser
            # feed = feedparser.parse(source.url)
            
            # For now, simulate RSS update
            documents_added = 0
            documents_updated = 0
            
            return UpdateResult(
                source_name=source.name,
                success=True,
                documents_added=documents_added,
                documents_updated=documents_updated,
                documents_removed=0,
                processing_time=time.time() - time.time(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"RSS update failed: {e}")
    
    def _process_document(self, doc: Dict[str, Any], source: UpdateSource) -> bool:
        """Process a single document from update source"""
        try:
            # API PLACEHOLDER: Implement document processing
            # This would involve:
            # 1. Extracting document metadata
            # 2. Chunking the content
            # 3. Generating embeddings
            # 4. Adding to vector database
            # 5. Updating metadata database
            
            logger.debug(f"Processing document from {source.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return False
    
    def manual_update(self, source_name: str = None) -> List[UpdateResult]:
        """Manually trigger updates"""
        results = []
        
        if source_name:
            # Update specific source
            source = next((s for s in self.sources if s.name == source_name), None)
            if source:
                results.append(self._update_source(source))
            else:
                logger.error(f"Source not found: {source_name}")
        else:
            # Update all enabled sources
            for source in self.sources:
                if source.enabled:
                    results.append(self._update_source(source))
        
        return results
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status"""
        status = {
            'auto_updates_running': self.running,
            'sources': [],
            'metrics': self.metrics.copy()
        }
        
        for source in self.sources:
            source_status = {
                'name': source.name,
                'enabled': source.enabled,
                'last_updated': source.last_updated.isoformat() if source.last_updated else None,
                'next_update': self._get_next_update_time(source),
                'source_type': source.source_type
            }
            status['sources'].append(source_status)
        
        return status
    
    def _get_next_update_time(self, source: UpdateSource) -> Optional[str]:
        """Get next scheduled update time for source"""
        if not source.last_updated:
            return datetime.now().isoformat()
        
        next_update = source.last_updated + timedelta(seconds=source.update_frequency)
        return next_update.isoformat()
    
    def _update_metrics(self, result: UpdateResult):
        """Update performance metrics"""
        self.metrics['total_updates'] += 1
        
        if result.success:
            self.metrics['successful_updates'] += 1
        else:
            self.metrics['failed_updates'] += 1
        
        self.metrics['total_documents_added'] += result.documents_added
        self.metrics['total_documents_updated'] += result.documents_updated
        self.metrics['last_update_time'] = result.timestamp.isoformat()
        
        # Update average update time
        total_updates = self.metrics['total_updates']
        current_avg = self.metrics['avg_update_time']
        self.metrics['avg_update_time'] = (
            (current_avg * (total_updates - 1) + result.processing_time) / total_updates
        )
    
    def add_source(self, source: UpdateSource):
        """Add a new update source"""
        self.sources.append(source)
        logger.info(f"Added new source: {source.name}")
    
    def remove_source(self, source_name: str):
        """Remove an update source"""
        self.sources = [s for s in self.sources if s.name != source_name]
        logger.info(f"Removed source: {source_name}")
    
    def enable_source(self, source_name: str):
        """Enable a source"""
        source = next((s for s in self.sources if s.name == source_name), None)
        if source:
            source.enabled = True
            logger.info(f"Enabled source: {source_name}")
        else:
            logger.error(f"Source not found: {source_name}")
    
    def disable_source(self, source_name: str):
        """Disable a source"""
        source = next((s for s in self.sources if s.name == source_name), None)
        if source:
            source.enabled = False
            logger.info(f"Disabled source: {source_name}")
        else:
            logger.error(f"Source not found: {source_name}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'total_documents_added': 0,
            'total_documents_updated': 0,
            'last_update_time': None,
            'avg_update_time': 0.0
        }
        logger.info("DynamicUpdater metrics reset")
