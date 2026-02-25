"""
Dynamic Legal Database Updater for real-time law and judgment updates.
Uses Indian Kanoon API and automatically updates vector database.
"""
import asyncio
import aiohttp
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import feedparser
import requests
import sqlite3
from indian_legal_database import IndianLegalDatabase
from indian_kanoon_api import IndianKanoonAPI, KanoonDocument


class DynamicLegalUpdater:
    """Dynamic updater for Indian legal database with real-time monitoring using Indian Kanoon API."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.db = IndianLegalDatabase(config)
        self.rag_system = None
        self.kanoon_api = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Update intervals (in minutes)
        self.update_intervals = {
            "kanoon_updates": 30,    # Check Indian Kanoon every 30 minutes
            "vector_db_sync": 15,    # Sync vector DB every 15 minutes
            "full_scan": 1440       # Full scan once per day
        }
        
        # Last update timestamps
        self.last_update_times = {
            "kanoon_updates": datetime.now() - timedelta(hours=1),
            "vector_db_sync": datetime.now() - timedelta(minutes=30),
            "full_scan": datetime.now() - timedelta(days=1)
        }
        
        # Vector database update queue
        self.update_queue = []
        self.max_queue_size = 1000
        
    def setup_logging(self):
        """Setup logging for the dynamic updater."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        updater_logger = logging.getLogger("dynamic_updater")
        updater_logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_dir / "dynamic_updater.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        updater_logger.addHandler(file_handler)
        self.logger = updater_logger
    
    async def initialize(self, rag_system = None):
        """Initialize the dynamic updater."""
        try:
            self.rag_system = rag_system
            
            # Initialize Indian Kanoon API
            self.kanoon_api = IndianKanoonAPI(self.config)
            
            self.logger.info("Dynamic Legal Updater initialized with Indian Kanoon API")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize dynamic updater: {e}")
            return False
    
    async def start_monitoring(self):
        """Start continuous monitoring for legal updates."""
        self.logger.info("Starting dynamic legal monitoring with Indian Kanoon API...")
        
        # Run initial full update
        await self.full_update()
        
        # Start monitoring loop
        while True:
            try:
                current_time = datetime.now()
                
                # Check for Indian Kanoon updates
                if self._should_update("kanoon_updates", current_time):
                    await self.update_from_kanoon()
                    self.last_update_times["kanoon_updates"] = current_time
                
                # Sync vector database
                if self._should_update("vector_db_sync", current_time):
                    await self.sync_vector_database()
                    self.last_update_times["vector_db_sync"] = current_time
                
                # Full scan (daily)
                if self._should_update("full_scan", current_time):
                    await self.full_scan_kanoon()
                    self.last_update_times["full_scan"] = current_time
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def _should_update(self, update_type: str, current_time: datetime) -> bool:
        """Check if an update should be performed."""
        last_update = self.last_update_times[update_type]
        interval_minutes = self.update_intervals[update_type]
        return (current_time - last_update).total_seconds() >= (interval_minutes * 60)
    
    async def full_update(self):
        """Perform a full update of the legal database."""
        try:
            self.logger.info("Starting full legal database update...")
            
            # Get comprehensive data from Indian Kanoon
            documents = await self.kanoon_api.get_all_legal_data(max_documents_per_type=500)
            
            # Convert KanoonDocument to LegalDocument format
            legal_docs = []
            for doc in documents:
                legal_doc = {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "content": doc.content,
                    "doc_type": doc.doc_type,
                    "court": doc.court,
                    "date": doc.date,
                    "url": doc.url,
                    "source": "Indian Kanoon",
                    "citations": doc.citations,
                    "keywords": doc.keywords,
                    "hash": doc.hash
                }
                legal_docs.append(legal_doc)
            
            # Save to database
            added = self.db.save_documents(legal_docs)
            
            # Add to vector database
            if self.rag_system and added > 0:
                await self._update_vector_database(legal_docs)
            
            self.logger.info(f"Full update completed: {added} documents added")
            
            return {
                "success": True,
                "documents_added": added,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in full update: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_from_kanoon(self):
        """Update database with new documents from Indian Kanoon."""
        try:
            self.logger.info("Checking for new updates from Indian Kanoon...")
            
            # Get recent updates
            new_docs = await self.kanoon_api.check_for_new_updates(self.last_update_times["kanoon_updates"])
            
            if not new_docs:
                self.logger.info("No new documents found")
                return {"documents_added": 0}
            
            # Convert to legal document format
            legal_docs = []
            for doc in new_docs:
                legal_doc = {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "content": doc.content,
                    "doc_type": doc.doc_type,
                    "court": doc.court,
                    "date": doc.date,
                    "url": doc.url,
                    "source": "Indian Kanoon",
                    "citations": doc.citations,
                    "keywords": doc.keywords,
                    "hash": doc.hash
                }
                legal_docs.append(legal_doc)
            
            # Save to database
            added = self.db.save_documents(legal_docs)
            
            # Add to update queue for vector database
            if added > 0:
                self.update_queue.extend(legal_docs)
                if len(self.update_queue) > self.max_queue_size:
                    self.update_queue = self.update_queue[-self.max_queue_size:]
            
            self.logger.info(f"Updated with {added} new documents from Indian Kanoon")
            
            return {
                "source": "indian_kanoon",
                "documents_added": added,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error updating from Indian Kanoon: {e}")
            return {"source": "indian_kanoon", "error": str(e)}
    
    async def full_scan_kanoon(self):
        """Perform a full scan of Indian Kanoon for comprehensive updates."""
        try:
            self.logger.info("Starting full scan of Indian Kanoon...")
            
            # Get all legal data
            documents = await self.kanoon_api.get_all_legal_data(max_documents_per_type=1000)
            
            # Convert to legal document format
            legal_docs = []
            for doc in documents:
                legal_doc = {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "content": doc.content,
                    "doc_type": doc.doc_type,
                    "court": doc.court,
                    "date": doc.date,
                    "url": doc.url,
                    "source": "Indian Kanoon",
                    "citations": doc.citations,
                    "keywords": doc.keywords,
                    "hash": doc.hash
                }
                legal_docs.append(legal_doc)
            
            # Save to database
            added = self.db.save_documents(legal_docs)
            
            # Update vector database
            if self.rag_system and added > 0:
                await self._update_vector_database(legal_docs)
            
            self.logger.info(f"Full scan completed: {added} documents processed")
            
            return {
                "source": "full_scan",
                "documents_added": added,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in full scan: {e}")
            return {"source": "full_scan", "error": str(e)}
    
    async def sync_vector_database(self):
        """Sync vector database with queued updates."""
        try:
            if not self.update_queue:
                return {"documents_synced": 0}
            
            self.logger.info(f"Syncing {len(self.update_queue)} documents to vector database...")
            
            if not self.rag_system:
                self.logger.warning("RAG system not available for vector database sync")
                return {"documents_synced": 0}
            
            # Separate documents by type
            statute_docs = [doc for doc in self.update_queue if doc.get("doc_type") == "act"]
            case_law_docs = [doc for doc in self.update_queue if doc.get("doc_type") == "judgment"]
            
            synced_count = 0
            
            # Add statute documents
            if statute_docs:
                try:
                    await self.rag_system.add_documents(statute_docs, "statute")
                    synced_count += len(statute_docs)
                    self.logger.info(f"Added {len(statute_docs)} statute documents to vector database")
                except Exception as e:
                    self.logger.error(f"Error adding statute documents: {e}")
            
            # Add case law documents
            if case_law_docs:
                try:
                    await self.rag_system.add_documents(case_law_docs, "case_law")
                    synced_count += len(case_law_docs)
                    self.logger.info(f"Added {len(case_law_docs)} case law documents to vector database")
                except Exception as e:
                    self.logger.error(f"Error adding case law documents: {e}")
            
            # Clear the queue
            self.update_queue = []
            
            self.logger.info(f"Vector database sync completed: {synced_count} documents synced")
            
            return {
                "documents_synced": synced_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error syncing vector database: {e}")
            return {"error": str(e)}
    
    async def _update_vector_database(self, documents: List[Dict]):
        """Update vector database with new documents."""
        try:
            if not self.rag_system:
                return
            
            # Separate documents by type
            statute_docs = [doc for doc in documents if doc.get("doc_type") == "act"]
            case_law_docs = [doc for doc in documents if doc.get("doc_type") == "judgment"]
            
            # Add to RAG system
            if statute_docs:
                await self.rag_system.add_documents(statute_docs, "statute")
                self.logger.info(f"Added {len(statute_docs)} statute documents to RAG system")
            
            if case_law_docs:
                await self.rag_system.add_documents(case_law_docs, "case_law")
                self.logger.info(f"Added {len(case_law_docs)} case law documents to RAG system")
            
        except Exception as e:
            self.logger.error(f"Error updating vector database: {e}")
    
    def get_update_status(self) -> Dict:
        """Get current update status."""
        try:
            # Get database stats
            db_stats = self.db.get_database_stats()
            
            # Get recent update log
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT source, update_type, documents_added, timestamp
                FROM update_log
                ORDER BY timestamp DESC
                LIMIT 10
            ''')
            
            recent_updates = cursor.fetchall()
            conn.close()
            
            return {
                "database_stats": db_stats,
                "recent_updates": recent_updates,
                "update_intervals": self.update_intervals,
                "last_update_times": {k: v.isoformat() for k, v in self.last_update_times.items()},
                "queue_size": len(self.update_queue),
                "monitoring_active": True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting update status: {e}")
            return {"error": str(e)}
    
    async def force_update(self):
        """Force an immediate update from Indian Kanoon."""
        try:
            self.logger.info("Forcing immediate update from Indian Kanoon...")
            
            # Reset last update time to force update
            self.last_update_times["kanoon_updates"] = datetime.now() - timedelta(hours=2)
            
            # Perform update
            result = await self.update_from_kanoon()
            
            # Sync vector database
            await self.sync_vector_database()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in force update: {e}")
            return {"error": str(e)}
    
    async def get_database_size(self) -> Dict:
        """Get current database size and statistics."""
        try:
            stats = self.db.get_database_stats()
            
            # Add vector database info if available
            if self.rag_system:
                try:
                    vector_stats = await self.rag_system.get_database_stats()
                    stats["vector_database"] = vector_stats
                except Exception as e:
                    stats["vector_database"] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database size: {e}")
            return {"error": str(e)}


# Example usage
async def main():
    """Main function for testing the dynamic updater."""
    updater = DynamicLegalUpdater()
    
    # Initialize
    await updater.initialize()
    
    # Run full update
    print("Running full update...")
    results = await updater.full_update()
    print(f"Update results: {results}")
    
    # Get status
    status = updater.get_update_status()
    print(f"Update status: {status}")
    
    # Get database size
    size_info = await updater.get_database_size()
    print(f"Database size: {size_info}")


if __name__ == "__main__":
    asyncio.run(main())






















