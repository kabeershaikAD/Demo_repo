"""
Dynamic Knowledge Updater Agent for real-time legal database updates.
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import feedparser
import requests
from bs4 import BeautifulSoup
import re


class UpdaterAgent:
    """Agent for dynamically updating legal knowledge base."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Update sources configuration
        self.sources = self.config.get("update_sources", {
            "supreme_court": {
                "rss_url": "https://main.sci.gov.in/rss/rss.xml",
                "base_url": "https://main.sci.gov.in",
                "enabled": True
            },
            "high_courts": {
                "rss_urls": [
                    "https://delhihighcourt.nic.in/rss.xml",
                    "https://bombayhighcourt.nic.in/rss.xml"
                ],
                "enabled": True
            },
            "legal_news": {
                "rss_urls": [
                    "https://www.livelaw.in/feed",
                    "https://www.barandbench.com/feed"
                ],
                "enabled": True
            }
        })
        
        # Update settings
        self.update_interval = self.config.get("update_interval", 3600)  # 1 hour
        self.max_documents_per_update = self.config.get("max_documents_per_update", 50)
        self.last_update = None
        
    def setup_logging(self):
        """Setup logging for the updater agent."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        updater_logger = logging.getLogger("updater_agent")
        updater_logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_dir / "updater_agent.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        updater_logger.addHandler(file_handler)
        self.logger = updater_logger
    
    async def initialize(self) -> bool:
        """Initialize the updater agent."""
        try:
            self.logger.info("Initializing Updater Agent...")
            
            # Create update history file
            self.history_file = Path("logs/update_history.json")
            if not self.history_file.exists():
                with open(self.history_file, 'w') as f:
                    json.dump({"updates": []}, f)
            
            self.logger.info("Updater Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Updater Agent: {e}")
            return False
    
    async def check_for_updates(self) -> Dict:
        """Check for new legal documents and updates."""
        try:
            self.logger.info("Checking for legal updates...")
            
            update_results = {
                "timestamp": datetime.now().isoformat(),
                "sources_checked": [],
                "new_documents": [],
                "errors": [],
                "total_new_documents": 0
            }
            
            # Check each enabled source
            for source_name, source_config in self.sources.items():
                if not source_config.get("enabled", False):
                    continue
                
                try:
                    source_result = await self._check_source(source_name, source_config)
                    update_results["sources_checked"].append(source_name)
                    update_results["new_documents"].extend(source_result.get("documents", []))
                    update_results["total_new_documents"] += len(source_result.get("documents", []))
                    
                except Exception as e:
                    error_msg = f"Error checking {source_name}: {str(e)}"
                    update_results["errors"].append(error_msg)
                    self.logger.error(error_msg)
            
            # Log update check
            self._log_update_check(update_results)
            
            return update_results
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "total_new_documents": 0
            }
    
    async def _check_source(self, source_name: str, source_config: Dict) -> Dict:
        """Check a specific source for updates."""
        if source_name == "supreme_court":
            return await self._check_supreme_court(source_config)
        elif source_name == "high_courts":
            return await self._check_high_courts(source_config)
        elif source_name == "legal_news":
            return await self._check_legal_news(source_config)
        else:
            return {"documents": [], "error": f"Unknown source: {source_name}"}
    
    async def _check_supreme_court(self, config: Dict) -> Dict:
        """Check Supreme Court RSS feed for new judgments."""
        try:
            rss_url = config.get("rss_url")
            base_url = config.get("base_url", "")
            
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            documents = []
            for entry in feed.entries[:self.max_documents_per_update]:
                # Extract judgment information
                doc = {
                    "title": entry.get("title", ""),
                    "content": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "date": entry.get("published", ""),
                    "source": "Supreme Court of India",
                    "doc_type": "judgment",
                    "court": "Supreme Court"
                }
                
                # Try to get full content
                full_content = await self._fetch_full_content(entry.get("link", ""))
                if full_content:
                    doc["content"] = full_content
                
                documents.append(doc)
            
            return {"documents": documents, "source": "supreme_court"}
            
        except Exception as e:
            return {"documents": [], "error": str(e)}
    
    async def _check_high_courts(self, config: Dict) -> Dict:
        """Check High Court RSS feeds for new judgments."""
        try:
            rss_urls = config.get("rss_urls", [])
            all_documents = []
            
            for rss_url in rss_urls:
                try:
                    feed = feedparser.parse(rss_url)
                    
                    for entry in feed.entries[:10]:  # Limit per court
                        doc = {
                            "title": entry.get("title", ""),
                            "content": entry.get("summary", ""),
                            "url": entry.get("link", ""),
                            "date": entry.get("published", ""),
                            "source": self._extract_court_name(rss_url),
                            "doc_type": "judgment",
                            "court": "High Court"
                        }
                        
                        all_documents.append(doc)
                        
                except Exception as e:
                    self.logger.warning(f"Error parsing {rss_url}: {e}")
                    continue
            
            return {"documents": all_documents, "source": "high_courts"}
            
        except Exception as e:
            return {"documents": [], "error": str(e)}
    
    async def _check_legal_news(self, config: Dict) -> Dict:
        """Check legal news feeds for relevant updates."""
        try:
            rss_urls = config.get("rss_urls", [])
            all_documents = []
            
            for rss_url in rss_urls:
                try:
                    feed = feedparser.parse(rss_url)
                    
                    for entry in feed.entries[:10]:  # Limit per source
                        # Filter for legal content
                        if self._is_legal_content(entry.get("title", ""), entry.get("summary", "")):
                            doc = {
                                "title": entry.get("title", ""),
                                "content": entry.get("summary", ""),
                                "url": entry.get("link", ""),
                                "date": entry.get("published", ""),
                                "source": self._extract_news_source(rss_url),
                                "doc_type": "news",
                                "court": "News"
                            }
                            
                            all_documents.append(doc)
                            
                except Exception as e:
                    self.logger.warning(f"Error parsing {rss_url}: {e}")
                    continue
            
            return {"documents": all_documents, "source": "legal_news"}
            
        except Exception as e:
            return {"documents": [], "error": str(e)}
    
    async def _fetch_full_content(self, url: str) -> Optional[str]:
        """Fetch full content from a URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract text content
                        text_content = soup.get_text(separator='\n', strip=True)
                        return text_content[:5000]  # Limit content length
                        
        except Exception as e:
            self.logger.warning(f"Error fetching content from {url}: {e}")
        
        return None
    
    def _extract_court_name(self, rss_url: str) -> str:
        """Extract court name from RSS URL."""
        if "delhihighcourt" in rss_url:
            return "Delhi High Court"
        elif "bombayhighcourt" in rss_url:
            return "Bombay High Court"
        elif "madras" in rss_url:
            return "Madras High Court"
        else:
            return "High Court"
    
    def _extract_news_source(self, rss_url: str) -> str:
        """Extract news source name from RSS URL."""
        if "livelaw" in rss_url:
            return "LiveLaw"
        elif "barandbench" in rss_url:
            return "Bar & Bench"
        else:
            return "Legal News"
    
    def _is_legal_content(self, title: str, content: str) -> bool:
        """Check if content is relevant to legal domain."""
        legal_keywords = [
            "court", "judgment", "ruling", "legal", "law", "statute", "act",
            "patent", "copyright", "trademark", "contract", "criminal", "civil",
            "constitutional", "supreme court", "high court", "tribunal"
        ]
        
        text = (title + " " + content).lower()
        return any(keyword in text for keyword in legal_keywords)
    
    async def process_new_documents(self, documents: List[Dict], 
                                  retriever_agent) -> Dict:
        """Process new documents and add them to the knowledge base."""
        try:
            self.logger.info(f"Processing {len(documents)} new documents...")
            
            # Separate documents by type
            statute_docs = [doc for doc in documents if doc.get("doc_type") == "statute"]
            case_law_docs = [doc for doc in documents if doc.get("doc_type") == "judgment"]
            
            # Add to appropriate indices
            statute_success = True
            case_law_success = True
            
            if statute_docs:
                statute_success = await retriever_agent.add_documents(statute_docs, "statute")
            
            if case_law_docs:
                case_law_success = await retriever_agent.add_documents(case_law_docs, "case_law")
            
            # Log the update
            self._log_document_update(documents, statute_success, case_law_success)
            
            return {
                "documents_processed": len(documents),
                "statute_documents": len(statute_docs),
                "case_law_documents": len(case_law_docs),
                "statute_success": statute_success,
                "case_law_success": case_law_success,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing new documents: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _log_update_check(self, update_results: Dict):
        """Log the update check results."""
        log_entry = {
            "timestamp": update_results["timestamp"],
            "sources_checked": len(update_results["sources_checked"]),
            "new_documents_found": update_results["total_new_documents"],
            "errors": len(update_results["errors"])
        }
        
        self.logger.info(f"Update check completed: {json.dumps(log_entry, indent=2)}")
    
    def _log_document_update(self, documents: List[Dict], 
                           statute_success: bool, case_law_success: bool):
        """Log document update process."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "documents_processed": len(documents),
            "statute_success": statute_success,
            "case_law_success": case_law_success
        }
        
        self.logger.info(f"Document update completed: {json.dumps(log_entry, indent=2)}")
    
    async def start_periodic_updates(self, retriever_agent, interval: int = None):
        """Start periodic updates in the background."""
        if interval:
            self.update_interval = interval
        
        self.logger.info(f"Starting periodic updates every {self.update_interval} seconds")
        
        while True:
            try:
                # Check for updates
                update_results = await self.check_for_updates()
                
                if update_results.get("total_new_documents", 0) > 0:
                    # Process new documents
                    await self.process_new_documents(
                        update_results["new_documents"], 
                        retriever_agent
                    )
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in periodic update: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def manual_update(self, retriever_agent) -> Dict:
        """Perform a manual update check and process."""
        try:
            self.logger.info("Performing manual update...")
            
            # Check for updates
            update_results = await self.check_for_updates()
            
            if update_results.get("total_new_documents", 0) > 0:
                # Process new documents
                process_results = await self.process_new_documents(
                    update_results["new_documents"], 
                    retriever_agent
                )
                
                return {
                    "update_check": update_results,
                    "document_processing": process_results,
                    "success": True
                }
            else:
                return {
                    "update_check": update_results,
                    "message": "No new documents found",
                    "success": True
                }
                
        except Exception as e:
            self.logger.error(f"Error in manual update: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def get_update_history(self) -> List[Dict]:
        """Get update history."""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            return history.get("updates", [])
        except Exception as e:
            self.logger.error(f"Error reading update history: {e}")
            return []
    
    def get_agent_status(self) -> Dict:
        """Get current agent status."""
        return {
            "name": "UpdaterAgent",
            "initialized": True,
            "sources_configured": len(self.sources),
            "enabled_sources": len([s for s in self.sources.values() if s.get("enabled", False)]),
            "update_interval": self.update_interval,
            "last_update": self.last_update
        }
