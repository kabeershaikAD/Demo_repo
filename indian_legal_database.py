"""
Indian Legal Database Manager for comprehensive law and case management.
"""
import asyncio
import aiohttp
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass
import sqlite3
import hashlib


@dataclass
class LegalDocument:
    """Data class for legal documents."""
    doc_id: str
    title: str
    content: str
    doc_type: str  # 'act', 'judgment', 'amendment', 'notification'
    court: str
    date: str
    url: str
    source: str
    citations: List[str]
    keywords: List[str]
    hash: str


class IndianLegalDatabase:
    """Comprehensive Indian legal database with dynamic updates."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.db_path = Path("indian_legal_db.sqlite")
        self.data_dir = Path("indian_legal_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Data sources configuration
        self.sources = {
            "indian_kanoon": {
                "base_url": "https://indiankanoon.org",
                "search_url": "https://indiankanoon.org/search/",
                "judgment_url": "https://indiankanoon.org/doc/",
                "act_url": "https://indiankanoon.org/act/",
                "enabled": True
            },
            "manupatra": {
                "base_url": "https://www.manupatra.com",
                "search_url": "https://www.manupatra.com/search",
                "enabled": True
            },
            "scc_online": {
                "base_url": "https://www.scconline.com",
                "search_url": "https://www.scconline.com/search",
                "enabled": True
            },
            "live_law": {
                "base_url": "https://www.livelaw.in",
                "rss_url": "https://www.livelaw.in/feed",
                "enabled": True
            },
            "bar_and_bench": {
                "base_url": "https://www.barandbench.com",
                "rss_url": "https://www.barandbench.com/feed",
                "enabled": True
            }
        }
        
        # Legal document categories
        self.categories = {
            "constitutional_law": ["constitution", "fundamental rights", "directive principles"],
            "criminal_law": ["ipc", "criminal procedure", "evidence act", "crpc"],
            "civil_law": ["civil procedure", "contract act", "tort", "property"],
            "commercial_law": ["companies act", "sebi", "insolvency", "banking"],
            "family_law": ["hindu marriage", "divorce", "custody", "adoption"],
            "labor_law": ["industrial disputes", "wages", "employment", "trade unions"],
            "intellectual_property": ["patent", "copyright", "trademark", "design"],
            "tax_law": ["income tax", "gst", "customs", "excise"],
            "environmental_law": ["environment", "pollution", "forest", "wildlife"],
            "cyber_law": ["information technology", "cyber crime", "data protection"]
        }
        
        # Initialize database
        self.init_database()
        
    def setup_logging(self):
        """Setup logging for the database manager."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        db_logger = logging.getLogger("indian_legal_database")
        db_logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_dir / "indian_legal_database.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        db_logger.addHandler(file_handler)
        self.logger = db_logger
    
    def init_database(self):
        """Initialize SQLite database for legal documents."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS legal_documents (
                    doc_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    court TEXT,
                    date TEXT,
                    url TEXT UNIQUE,
                    source TEXT,
                    citations TEXT,
                    keywords TEXT,
                    hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_categories (
                    doc_id TEXT,
                    category TEXT,
                    confidence REAL,
                    FOREIGN KEY (doc_id) REFERENCES legal_documents (doc_id)
                )
            ''')
            
            # Create citations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT,
                    cited_doc_id TEXT,
                    citation_text TEXT,
                    citation_type TEXT,
                    FOREIGN KEY (doc_id) REFERENCES legal_documents (doc_id)
                )
            ''')
            
            # Create update log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS update_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    update_type TEXT,
                    documents_added INTEGER,
                    documents_updated INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_type ON legal_documents (doc_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_court ON legal_documents (court)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON legal_documents (date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON legal_documents (source)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
    
    async def scrape_indian_kanoon(self, max_pages: int = 100) -> List[LegalDocument]:
        """Scrape documents from Indian Kanoon."""
        documents = []
        
        try:
            self.logger.info("Starting Indian Kanoon scraping...")
            
            # Search for different types of legal documents
            search_queries = [
                "supreme court judgment",
                "high court judgment",
                "constitutional law",
                "criminal law",
                "civil law",
                "commercial law",
                "family law",
                "labor law",
                "intellectual property",
                "tax law"
            ]
            
            for query in search_queries:
                self.logger.info(f"Searching for: {query}")
                
                # Search for judgments
                judgment_docs = await self._search_kanoon_judgments(query, max_pages // len(search_queries))
                documents.extend(judgment_docs)
                
                # Search for acts
                act_docs = await self._search_kanoon_acts(query, max_pages // len(search_queries))
                documents.extend(act_docs)
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(2)
            
            self.logger.info(f"Scraped {len(documents)} documents from Indian Kanoon")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error scraping Indian Kanoon: {e}")
            return []
    
    async def _search_kanoon_judgments(self, query: str, max_pages: int) -> List[LegalDocument]:
        """Search for judgments on Indian Kanoon."""
        documents = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for page in range(1, max_pages + 1):
                    search_url = f"https://indiankanoon.org/search/?formInput={query}&type=judgments&page={page}"
                    
                    async with session.get(search_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find judgment links
                            judgment_links = soup.find_all('a', href=re.compile(r'/doc/\d+'))
                            
                            for link in judgment_links:
                                try:
                                    doc_url = f"https://indiankanoon.org{link['href']}"
                                    doc_id = link['href'].split('/')[-1]
                                    
                                    # Fetch judgment content
                                    doc = await self._fetch_kanoon_document(session, doc_url, doc_id, "judgment")
                                    if doc:
                                        documents.append(doc)
                                    
                                    # Add delay
                                    await asyncio.sleep(1)
                                    
                                except Exception as e:
                                    self.logger.warning(f"Error processing judgment link: {e}")
                                    continue
                        else:
                            self.logger.warning(f"Failed to fetch page {page}: {response.status}")
                            break
                        
                        # Add delay between pages
                        await asyncio.sleep(2)
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error searching Kanoon judgments: {e}")
            return []
    
    async def _search_kanoon_acts(self, query: str, max_pages: int) -> List[LegalDocument]:
        """Search for acts on Indian Kanoon."""
        documents = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for page in range(1, max_pages + 1):
                    search_url = f"https://indiankanoon.org/search/?formInput={query}&type=acts&page={page}"
                    
                    async with session.get(search_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find act links
                            act_links = soup.find_all('a', href=re.compile(r'/act/\d+'))
                            
                            for link in act_links:
                                try:
                                    doc_url = f"https://indiankanoon.org{link['href']}"
                                    doc_id = link['href'].split('/')[-1]
                                    
                                    # Fetch act content
                                    doc = await self._fetch_kanoon_document(session, doc_url, doc_id, "act")
                                    if doc:
                                        documents.append(doc)
                                    
                                    # Add delay
                                    await asyncio.sleep(1)
                                    
                                except Exception as e:
                                    self.logger.warning(f"Error processing act link: {e}")
                                    continue
                        else:
                            self.logger.warning(f"Failed to fetch page {page}: {response.status}")
                            break
                        
                        # Add delay between pages
                        await asyncio.sleep(2)
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error searching Kanoon acts: {e}")
            return []
    
    async def _fetch_kanoon_document(self, session: aiohttp.ClientSession, url: str, doc_id: str, doc_type: str) -> Optional[LegalDocument]:
        """Fetch a specific document from Indian Kanoon."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else f"Document {doc_id}"
                    
                    # Extract content
                    content_elem = soup.find('div', class_='judgments') or soup.find('div', class_='act')
                    if not content_elem:
                        content_elem = soup.find('div', {'id': 'content'})
                    
                    content = content_elem.get_text().strip() if content_elem else ""
                    
                    if not content or len(content) < 100:
                        return None
                    
                    # Extract court information
                    court = "Unknown"
                    court_elem = soup.find('div', class_='court')
                    if court_elem:
                        court = court_elem.get_text().strip()
                    
                    # Extract date
                    date = ""
                    date_elem = soup.find('div', class_='date')
                    if date_elem:
                        date = date_elem.get_text().strip()
                    
                    # Extract citations
                    citations = self._extract_citations(content)
                    
                    # Generate keywords
                    keywords = self._extract_keywords(content)
                    
                    # Generate hash
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    return LegalDocument(
                        doc_id=doc_id,
                        title=title,
                        content=content,
                        doc_type=doc_type,
                        court=court,
                        date=date,
                        url=url,
                        source="Indian Kanoon",
                        citations=citations,
                        keywords=keywords,
                        hash=content_hash
                    )
                
        except Exception as e:
            self.logger.warning(f"Error fetching document {doc_id}: {e}")
        
        return None
    
    def _extract_citations(self, content: str) -> List[str]:
        """Extract citations from document content."""
        citations = []
        
        # Case citation patterns
        case_patterns = [
            r'([A-Z][a-z]+ v\. [A-Z][a-z]+)',
            r'(\d+ [A-Z][a-z]+ \d+)',
            r'([A-Z][a-z]+ v\. [A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        # Section citation patterns
        section_patterns = [
            r'(Section \d+[a-z]?)',
            r'(Article \d+[a-z]?)',
            r'(Clause \d+[a-z]?)'
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        return list(set(citations))  # Remove duplicates
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from document content."""
        # Legal keywords
        legal_keywords = [
            'constitution', 'fundamental rights', 'directive principles',
            'criminal', 'civil', 'commercial', 'family', 'labor',
            'patent', 'copyright', 'trademark', 'intellectual property',
            'tax', 'gst', 'income tax', 'environment', 'cyber law',
            'supreme court', 'high court', 'district court', 'tribunal',
            'judgment', 'ruling', 'decision', 'precedent', 'act', 'statute'
        ]
        
        content_lower = content.lower()
        found_keywords = []
        
        for keyword in legal_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    async def scrape_legal_news(self) -> List[LegalDocument]:
        """Scrape legal news from RSS feeds."""
        documents = []
        
        try:
            self.logger.info("Starting legal news scraping...")
            
            # RSS feeds for legal news
            rss_feeds = [
                "https://www.livelaw.in/feed",
                "https://www.barandbench.com/feed",
                "https://www.manupatra.com/rss",
                "https://www.scconline.com/rss"
            ]
            
            for feed_url in rss_feeds:
                try:
                    feed_docs = await self._scrape_rss_feed(feed_url)
                    documents.extend(feed_docs)
                except Exception as e:
                    self.logger.warning(f"Error scraping RSS feed {feed_url}: {e}")
                    continue
            
            self.logger.info(f"Scraped {len(documents)} news documents")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error scraping legal news: {e}")
            return []
    
    async def _scrape_rss_feed(self, feed_url: str) -> List[LegalDocument]:
        """Scrape a single RSS feed."""
        documents = []
        
        try:
            import feedparser
            
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                try:
                    # Extract content
                    content = entry.get('summary', entry.get('description', ''))
                    
                    # Try to get full content
                    full_content = await self._fetch_full_content(entry.get('link', ''))
                    if full_content:
                        content = full_content
                    
                    if len(content) < 100:
                        continue
                    
                    # Create document
                    doc_id = hashlib.md5(entry.get('link', '').encode()).hexdigest()[:12]
                    
                    doc = LegalDocument(
                        doc_id=doc_id,
                        title=entry.get('title', ''),
                        content=content,
                        doc_type='news',
                        court='News',
                        date=entry.get('published', ''),
                        url=entry.get('link', ''),
                        source=feed.feed.get('title', 'RSS Feed'),
                        citations=self._extract_citations(content),
                        keywords=self._extract_keywords(content),
                        hash=hashlib.md5(content.encode()).hexdigest()
                    )
                    
                    documents.append(doc)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing RSS entry: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing RSS feed {feed_url}: {e}")
        
        return documents
    
    async def _fetch_full_content(self, url: str) -> Optional[str]:
        """Fetch full content from a URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text content
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return text[:5000]  # Limit content length
                        
        except Exception as e:
            self.logger.warning(f"Error fetching full content from {url}: {e}")
        
        return None
    
    def save_documents(self, documents: List[LegalDocument]) -> int:
        """Save documents to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            
            for doc in documents:
                try:
                    # Check if document already exists
                    cursor.execute('SELECT doc_id FROM legal_documents WHERE doc_id = ?', (doc.doc_id,))
                    if cursor.fetchone():
                        continue
                    
                    # Insert document
                    cursor.execute('''
                        INSERT INTO legal_documents 
                        (doc_id, title, content, doc_type, court, date, url, source, citations, keywords, hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        doc.doc_id,
                        doc.title,
                        doc.content,
                        doc.doc_type,
                        doc.court,
                        doc.date,
                        doc.url,
                        doc.source,
                        json.dumps(doc.citations),
                        json.dumps(doc.keywords),
                        doc.hash
                    ))
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"Error saving document {doc.doc_id}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved {saved_count} documents to database")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Error saving documents: {e}")
            return 0
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total documents
            cursor.execute('SELECT COUNT(*) FROM legal_documents')
            total_docs = cursor.fetchone()[0]
            
            # Documents by type
            cursor.execute('SELECT doc_type, COUNT(*) FROM legal_documents GROUP BY doc_type')
            doc_types = dict(cursor.fetchall())
            
            # Documents by court
            cursor.execute('SELECT court, COUNT(*) FROM legal_documents GROUP BY court')
            courts = dict(cursor.fetchall())
            
            # Documents by source
            cursor.execute('SELECT source, COUNT(*) FROM legal_documents GROUP BY source')
            sources = dict(cursor.fetchall())
            
            # Recent updates
            cursor.execute('SELECT COUNT(*) FROM legal_documents WHERE created_at > datetime("now", "-7 days")')
            recent_docs = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_documents": total_docs,
                "document_types": doc_types,
                "courts": courts,
                "sources": sources,
                "recent_documents": recent_docs,
                "database_size": self.db_path.stat().st_size if self.db_path.exists() else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    async def update_database(self) -> Dict:
        """Update database with new documents."""
        try:
            self.logger.info("Starting database update...")
            
            update_results = {
                "timestamp": datetime.now().isoformat(),
                "sources_updated": [],
                "documents_added": 0,
                "errors": []
            }
            
            # Scrape Indian Kanoon
            try:
                kanoon_docs = await self.scrape_indian_kanoon(max_pages=50)
                if kanoon_docs:
                    added = self.save_documents(kanoon_docs)
                    update_results["documents_added"] += added
                    update_results["sources_updated"].append("Indian Kanoon")
            except Exception as e:
                update_results["errors"].append(f"Indian Kanoon: {str(e)}")
            
            # Scrape legal news
            try:
                news_docs = await self.scrape_legal_news()
                if news_docs:
                    added = self.save_documents(news_docs)
                    update_results["documents_added"] += added
                    update_results["sources_updated"].append("Legal News")
            except Exception as e:
                update_results["errors"].append(f"Legal News: {str(e)}")
            
            # Log update
            self._log_update(update_results)
            
            return update_results
            
        except Exception as e:
            self.logger.error(f"Error updating database: {e}")
            return {"error": str(e)}
    
    def _log_update(self, update_results: Dict):
        """Log database update results."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO update_log (source, update_type, documents_added, documents_updated)
                VALUES (?, ?, ?, ?)
            ''', (
                json.dumps(update_results["sources_updated"]),
                "full_update",
                update_results["documents_added"],
                0
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error logging update: {e}")
    
    def search_documents(self, query: str, doc_type: str = None, court: str = None, limit: int = 100) -> List[Dict]:
        """Search documents in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build search query
            search_query = '''
                SELECT doc_id, title, content, doc_type, court, date, url, source, citations, keywords
                FROM legal_documents
                WHERE (title LIKE ? OR content LIKE ? OR keywords LIKE ?)
            '''
            
            params = [f'%{query}%', f'%{query}%', f'%{query}%']
            
            if doc_type:
                search_query += ' AND doc_type = ?'
                params.append(doc_type)
            
            if court:
                search_query += ' AND court LIKE ?'
                params.append(f'%{court}%')
            
            search_query += ' ORDER BY date DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(search_query, params)
            results = cursor.fetchall()
            
            conn.close()
            
            # Convert to list of dictionaries
            documents = []
            for row in results:
                documents.append({
                    "doc_id": row[0],
                    "title": row[1],
                    "content": row[2][:500] + "..." if len(row[2]) > 500 else row[2],
                    "doc_type": row[3],
                    "court": row[4],
                    "date": row[5],
                    "url": row[6],
                    "source": row[7],
                    "citations": json.loads(row[8]) if row[8] else [],
                    "keywords": json.loads(row[9]) if row[9] else []
                })
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return []


# Example usage
async def main():
    """Main function for testing the Indian Legal Database."""
    db = IndianLegalDatabase()
    
    # Update database
    print("Updating Indian Legal Database...")
    results = await db.update_database()
    print(f"Update results: {results}")
    
    # Get database stats
    stats = db.get_database_stats()
    print(f"Database stats: {stats}")
    
    # Search documents
    search_results = db.search_documents("patent", doc_type="judgment", limit=10)
    print(f"Found {len(search_results)} patent-related judgments")


if __name__ == "__main__":
    asyncio.run(main())


















