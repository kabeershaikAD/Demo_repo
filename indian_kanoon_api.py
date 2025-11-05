"""
Indian Kanoon API Client for comprehensive legal data extraction.
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
import hashlib
from dataclasses import dataclass


@dataclass
class KanoonDocument:
    """Data class for Indian Kanoon documents."""
    doc_id: str
    title: str
    content: str
    doc_type: str  # 'judgment', 'act', 'amendment'
    court: str
    date: str
    url: str
    citations: List[str]
    keywords: List[str]
    hash: str
    metadata: Dict[str, Any]


class IndianKanoonAPI:
    """Comprehensive Indian Kanoon API client."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.base_url = "https://indiankanoon.org"
        self.api_endpoints = {
            "search": f"{self.base_url}/search/",
            "judgment": f"{self.base_url}/doc/",
            "act": f"{self.base_url}/act/",
            "recent": f"{self.base_url}/recent/",
            "browse": f"{self.base_url}/browse/"
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.max_concurrent = 5
        
        # Document types and their search patterns
        self.document_types = {
            "judgments": {
                "search_terms": [
                    "supreme court judgment",
                    "high court judgment", 
                    "district court judgment",
                    "tribunal judgment",
                    "constitutional law",
                    "criminal law",
                    "civil law",
                    "commercial law",
                    "family law",
                    "labor law",
                    "intellectual property",
                    "tax law",
                    "environmental law",
                    "cyber law"
                ],
                "courts": [
                    "Supreme Court of India",
                    "Delhi High Court",
                    "Bombay High Court", 
                    "Madras High Court",
                    "Karnataka High Court",
                    "Kerala High Court",
                    "Punjab and Haryana High Court",
                    "Calcutta High Court",
                    "Allahabad High Court",
                    "Gujarat High Court"
                ]
            },
            "acts": {
                "search_terms": [
                    "constitution of india",
                    "criminal procedure code",
                    "indian penal code",
                    "evidence act",
                    "contract act",
                    "companies act",
                    "patent act",
                    "copyright act",
                    "trademark act",
                    "income tax act",
                    "gst act",
                    "environment protection act",
                    "information technology act",
                    "hindu marriage act",
                    "industrial disputes act"
                ]
            }
        }
        
    def setup_logging(self):
        """Setup logging for the API client."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        api_logger = logging.getLogger("indian_kanoon_api")
        api_logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_dir / "indian_kanoon_api.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        api_logger.addHandler(file_handler)
        self.logger = api_logger
    
    async def get_all_legal_data(self, max_documents_per_type: int = 1000) -> List[KanoonDocument]:
        """Get comprehensive legal data from Indian Kanoon."""
        try:
            self.logger.info("Starting comprehensive data extraction from Indian Kanoon...")
            
            all_documents = []
            
            # Get judgments
            self.logger.info("Extracting judgments...")
            judgments = await self.get_all_judgments(max_documents_per_type)
            all_documents.extend(judgments)
            
            # Get acts
            self.logger.info("Extracting acts...")
            acts = await self.get_all_acts(max_documents_per_type)
            all_documents.extend(acts)
            
            # Get recent updates
            self.logger.info("Extracting recent updates...")
            recent = await self.get_recent_updates(max_documents_per_type // 4)
            all_documents.extend(recent)
            
            self.logger.info(f"Total documents extracted: {len(all_documents)}")
            return all_documents
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive data extraction: {e}")
            return []
    
    async def get_all_judgments(self, max_documents: int = 1000) -> List[KanoonDocument]:
        """Get all judgments from Indian Kanoon."""
        documents = []
        
        try:
            # Use semaphore for rate limiting
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            # Create tasks for different search terms
            tasks = []
            for search_term in self.document_types["judgments"]["search_terms"]:
                task = self._search_judgments_with_semaphore(semaphore, search_term, max_documents // len(self.document_types["judgments"]["search_terms"]))
                tasks.append(task)
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for result in results:
                if isinstance(result, list):
                    documents.extend(result)
                elif isinstance(result, Exception):
                    self.logger.warning(f"Error in judgment search: {result}")
            
            # Remove duplicates based on doc_id
            unique_docs = {}
            for doc in documents:
                unique_docs[doc.doc_id] = doc
            
            self.logger.info(f"Extracted {len(unique_docs)} unique judgments")
            return list(unique_docs.values())
            
        except Exception as e:
            self.logger.error(f"Error getting all judgments: {e}")
            return []
    
    async def _search_judgments_with_semaphore(self, semaphore: asyncio.Semaphore, search_term: str, max_documents: int) -> List[KanoonDocument]:
        """Search judgments with semaphore for rate limiting."""
        async with semaphore:
            return await self._search_judgments(search_term, max_documents)
    
    async def _search_judgments(self, search_term: str, max_documents: int) -> List[KanoonDocument]:
        """Search for judgments using a specific term."""
        documents = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Search for judgments
                search_url = f"{self.api_endpoints['search']}?formInput={search_term}&type=judgments"
                
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find judgment links
                        judgment_links = soup.find_all('a', href=re.compile(r'/doc/\d+'))
                        
                        # Limit to max_documents
                        judgment_links = judgment_links[:max_documents]
                        
                        # Process each judgment
                        for link in judgment_links:
                            try:
                                doc_url = f"{self.base_url}{link['href']}"
                                doc_id = link['href'].split('/')[-1]
                                
                                # Fetch judgment content
                                doc = await self._fetch_judgment_document(session, doc_url, doc_id)
                                if doc:
                                    documents.append(doc)
                                
                                # Rate limiting
                                await asyncio.sleep(self.request_delay)
                                
                            except Exception as e:
                                self.logger.warning(f"Error processing judgment {link['href']}: {e}")
                                continue
                    else:
                        self.logger.warning(f"Failed to search judgments for '{search_term}': {response.status}")
            
        except Exception as e:
            self.logger.error(f"Error searching judgments for '{search_term}': {e}")
        
        return documents
    
    async def _fetch_judgment_document(self, session: aiohttp.ClientSession, url: str, doc_id: str) -> Optional[KanoonDocument]:
        """Fetch a specific judgment document."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else f"Judgment {doc_id}"
                    
                    # Extract content
                    content_elem = soup.find('div', class_='judgments') or soup.find('div', {'id': 'content'})
                    if not content_elem:
                        content_elem = soup.find('div', class_='doc_content')
                    
                    content = content_elem.get_text().strip() if content_elem else ""
                    
                    if not content or len(content) < 200:
                        return None
                    
                    # Extract court information
                    court = self._extract_court_from_content(soup, title)
                    
                    # Extract date
                    date = self._extract_date_from_content(soup)
                    
                    # Extract citations
                    citations = self._extract_citations(content)
                    
                    # Generate keywords
                    keywords = self._extract_keywords(content, title)
                    
                    # Generate hash
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Extract metadata
                    metadata = self._extract_metadata(soup)
                    
                    return KanoonDocument(
                        doc_id=doc_id,
                        title=title,
                        content=content,
                        doc_type="judgment",
                        court=court,
                        date=date,
                        url=url,
                        citations=citations,
                        keywords=keywords,
                        hash=content_hash,
                        metadata=metadata
                    )
                
        except Exception as e:
            self.logger.warning(f"Error fetching judgment {doc_id}: {e}")
        
        return None
    
    async def get_all_acts(self, max_documents: int = 1000) -> List[KanoonDocument]:
        """Get all acts from Indian Kanoon."""
        documents = []
        
        try:
            # Use semaphore for rate limiting
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            # Create tasks for different search terms
            tasks = []
            for search_term in self.document_types["acts"]["search_terms"]:
                task = self._search_acts_with_semaphore(semaphore, search_term, max_documents // len(self.document_types["acts"]["search_terms"]))
                tasks.append(task)
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for result in results:
                if isinstance(result, list):
                    documents.extend(result)
                elif isinstance(result, Exception):
                    self.logger.warning(f"Error in act search: {result}")
            
            # Remove duplicates based on doc_id
            unique_docs = {}
            for doc in documents:
                unique_docs[doc.doc_id] = doc
            
            self.logger.info(f"Extracted {len(unique_docs)} unique acts")
            return list(unique_docs.values())
            
        except Exception as e:
            self.logger.error(f"Error getting all acts: {e}")
            return []
    
    async def _search_acts_with_semaphore(self, semaphore: asyncio.Semaphore, search_term: str, max_documents: int) -> List[KanoonDocument]:
        """Search acts with semaphore for rate limiting."""
        async with semaphore:
            return await self._search_acts(search_term, max_documents)
    
    async def _search_acts(self, search_term: str, max_documents: int) -> List[KanoonDocument]:
        """Search for acts using a specific term."""
        documents = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Search for acts
                search_url = f"{self.api_endpoints['search']}?formInput={search_term}&type=acts"
                
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find act links
                        act_links = soup.find_all('a', href=re.compile(r'/act/\d+'))
                        
                        # Limit to max_documents
                        act_links = act_links[:max_documents]
                        
                        # Process each act
                        for link in act_links:
                            try:
                                doc_url = f"{self.base_url}{link['href']}"
                                doc_id = link['href'].split('/')[-1]
                                
                                # Fetch act content
                                doc = await self._fetch_act_document(session, doc_url, doc_id)
                                if doc:
                                    documents.append(doc)
                                
                                # Rate limiting
                                await asyncio.sleep(self.request_delay)
                                
                            except Exception as e:
                                self.logger.warning(f"Error processing act {link['href']}: {e}")
                                continue
                    else:
                        self.logger.warning(f"Failed to search acts for '{search_term}': {response.status}")
            
        except Exception as e:
            self.logger.error(f"Error searching acts for '{search_term}': {e}")
        
        return documents
    
    async def _fetch_act_document(self, session: aiohttp.ClientSession, url: str, doc_id: str) -> Optional[KanoonDocument]:
        """Fetch a specific act document."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else f"Act {doc_id}"
                    
                    # Extract content
                    content_elem = soup.find('div', class_='act') or soup.find('div', {'id': 'content'})
                    if not content_elem:
                        content_elem = soup.find('div', class_='doc_content')
                    
                    content = content_elem.get_text().strip() if content_elem else ""
                    
                    if not content or len(content) < 200:
                        return None
                    
                    # Extract court information (acts are from Parliament)
                    court = "Parliament of India"
                    
                    # Extract date
                    date = self._extract_date_from_content(soup)
                    
                    # Extract citations
                    citations = self._extract_citations(content)
                    
                    # Generate keywords
                    keywords = self._extract_keywords(content, title)
                    
                    # Generate hash
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    # Extract metadata
                    metadata = self._extract_metadata(soup)
                    
                    return KanoonDocument(
                        doc_id=doc_id,
                        title=title,
                        content=content,
                        doc_type="act",
                        court=court,
                        date=date,
                        url=url,
                        citations=citations,
                        keywords=keywords,
                        hash=content_hash,
                        metadata=metadata
                    )
                
        except Exception as e:
            self.logger.warning(f"Error fetching act {doc_id}: {e}")
        
        return None
    
    async def get_recent_updates(self, max_documents: int = 100) -> List[KanoonDocument]:
        """Get recent updates from Indian Kanoon."""
        documents = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check recent judgments
                recent_url = f"{self.api_endpoints['recent']}judgments"
                
                async with session.get(recent_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find recent judgment links
                        judgment_links = soup.find_all('a', href=re.compile(r'/doc/\d+'))
                        
                        # Limit to max_documents
                        judgment_links = judgment_links[:max_documents]
                        
                        # Process each recent judgment
                        for link in judgment_links:
                            try:
                                doc_url = f"{self.base_url}{link['href']}"
                                doc_id = link['href'].split('/')[-1]
                                
                                # Fetch judgment content
                                doc = await self._fetch_judgment_document(session, doc_url, doc_id)
                                if doc:
                                    documents.append(doc)
                                
                                # Rate limiting
                                await asyncio.sleep(self.request_delay)
                                
                            except Exception as e:
                                self.logger.warning(f"Error processing recent judgment {link['href']}: {e}")
                                continue
                    else:
                        self.logger.warning(f"Failed to get recent updates: {response.status}")
            
        except Exception as e:
            self.logger.error(f"Error getting recent updates: {e}")
        
        return documents
    
    def _extract_court_from_content(self, soup: BeautifulSoup, title: str) -> str:
        """Extract court name from content."""
        # Check for court information in the page
        court_elem = soup.find('div', class_='court') or soup.find('span', class_='court')
        if court_elem:
            return court_elem.get_text().strip()
        
        # Check title for court names
        title_lower = title.lower()
        
        if "supreme court" in title_lower:
            return "Supreme Court of India"
        elif "high court" in title_lower:
            if "delhi" in title_lower:
                return "Delhi High Court"
            elif "bombay" in title_lower:
                return "Bombay High Court"
            elif "madras" in title_lower:
                return "Madras High Court"
            elif "karnataka" in title_lower:
                return "Karnataka High Court"
            elif "kerala" in title_lower:
                return "Kerala High Court"
            elif "punjab" in title_lower or "haryana" in title_lower:
                return "Punjab and Haryana High Court"
            elif "calcutta" in title_lower:
                return "Calcutta High Court"
            elif "allahabad" in title_lower:
                return "Allahabad High Court"
            elif "gujarat" in title_lower:
                return "Gujarat High Court"
            else:
                return "High Court"
        elif "district court" in title_lower:
            return "District Court"
        elif "tribunal" in title_lower:
            return "Tribunal"
        else:
            return "Unknown Court"
    
    def _extract_date_from_content(self, soup: BeautifulSoup) -> str:
        """Extract date from content."""
        # Look for date elements
        date_elem = soup.find('div', class_='date') or soup.find('span', class_='date')
        if date_elem:
            return date_elem.get_text().strip()
        
        # Look for date patterns in text
        date_patterns = [
            r'\d{1,2}[-\/]\d{1,2}[-\/]\d{4}',
            r'\d{4}[-\/]\d{1,2}[-\/]\d{1,2}',
            r'\d{1,2}\s+\w+\s+\d{4}'
        ]
        
        text = soup.get_text()
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return datetime.now().strftime("%Y-%m-%d")
    
    def _extract_citations(self, content: str) -> List[str]:
        """Extract citations from content."""
        citations = []
        
        # Case citation patterns
        case_patterns = [
            r'([A-Z][a-z]+ v\. [A-Z][a-z]+)',
            r'(\d+ [A-Z][a-z]+ \d+)',
            r'([A-Z][a-z]+ v\. [A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ v\. [A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        # Section citation patterns
        section_patterns = [
            r'(Section \d+[a-z]?)',
            r'(Article \d+[a-z]?)',
            r'(Clause \d+[a-z]?)',
            r'(Rule \d+[a-z]?)',
            r'(Schedule \d+[a-z]?)'
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        # Act citation patterns
        act_patterns = [
            r'([A-Z][a-z]+ Act, \d{4})',
            r'([A-Z][a-z]+ Code, \d{4})',
            r'([A-Z][a-z]+ Rules, \d{4})'
        ]
        
        for pattern in act_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        return list(set(citations))  # Remove duplicates
    
    def _extract_keywords(self, content: str, title: str) -> List[str]:
        """Extract keywords from content and title."""
        # Legal keywords
        legal_keywords = [
            'constitution', 'fundamental rights', 'directive principles',
            'criminal', 'civil', 'commercial', 'family', 'labor',
            'patent', 'copyright', 'trademark', 'intellectual property',
            'tax', 'gst', 'income tax', 'environment', 'cyber law',
            'supreme court', 'high court', 'district court', 'tribunal',
            'judgment', 'ruling', 'decision', 'precedent', 'act', 'statute',
            'amendment', 'notification', 'order', 'writ', 'petition',
            'appeal', 'revision', 'review', 'bail', 'anticipatory bail',
            'habeas corpus', 'mandamus', 'prohibition', 'certiorari',
            'quashing', 'stay', 'injunction', 'damages', 'compensation'
        ]
        
        text = (title + " " + content).lower()
        found_keywords = []
        
        for keyword in legal_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from the document."""
        metadata = {}
        
        # Extract judges
        judges_elem = soup.find('div', class_='judges') or soup.find('span', class_='judges')
        if judges_elem:
            metadata['judges'] = judges_elem.get_text().strip()
        
        # Extract parties
        parties_elem = soup.find('div', class_='parties') or soup.find('span', class_='parties')
        if parties_elem:
            metadata['parties'] = parties_elem.get_text().strip()
        
        # Extract case number
        case_no_elem = soup.find('div', class_='case_no') or soup.find('span', class_='case_no')
        if case_no_elem:
            metadata['case_number'] = case_no_elem.get_text().strip()
        
        # Extract act references
        act_refs = soup.find_all('a', href=re.compile(r'/act/'))
        if act_refs:
            metadata['act_references'] = [ref.get_text().strip() for ref in act_refs]
        
        return metadata
    
    async def check_for_new_updates(self, last_check_time: datetime) -> List[KanoonDocument]:
        """Check for new updates since last check."""
        try:
            self.logger.info(f"Checking for new updates since {last_check_time}")
            
            # Get recent updates
            recent_docs = await self.get_recent_updates(max_documents=50)
            
            # Filter documents newer than last check
            new_docs = []
            for doc in recent_docs:
                try:
                    doc_date = datetime.strptime(doc.date, "%Y-%m-%d")
                    if doc_date > last_check_time:
                        new_docs.append(doc)
                except ValueError:
                    # If date parsing fails, include the document
                    new_docs.append(doc)
            
            self.logger.info(f"Found {len(new_docs)} new documents")
            return new_docs
            
        except Exception as e:
            self.logger.error(f"Error checking for new updates: {e}")
            return []


# Example usage
async def main():
    """Main function for testing the Indian Kanoon API."""
    api = IndianKanoonAPI()
    
    # Get all legal data
    print("Fetching all legal data from Indian Kanoon...")
    documents = await api.get_all_legal_data(max_documents_per_type=100)
    
    print(f"Fetched {len(documents)} documents")
    
    # Show sample documents
    for i, doc in enumerate(documents[:5]):
        print(f"\nDocument {i+1}:")
        print(f"  Title: {doc.title}")
        print(f"  Type: {doc.doc_type}")
        print(f"  Court: {doc.court}")
        print(f"  Date: {doc.date}")
        print(f"  Citations: {len(doc.citations)}")
        print(f"  Keywords: {len(doc.keywords)}")


if __name__ == "__main__":
    asyncio.run(main())


















