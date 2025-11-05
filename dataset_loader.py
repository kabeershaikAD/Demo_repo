"""
Dataset loader for ILDC judgments and Bare Acts text.
"""
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import requests
import zipfile
import os
from bs4 import BeautifulSoup
import re


class LegalDatasetLoader:
    """Loader for legal datasets including ILDC and Bare Acts."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.data_dir = Path(self.config.get("data_dir", "data"))
        self.data_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Dataset URLs and configurations
        self.datasets = {
            "ildc": {
                "name": "Indian Legal Documents Corpus",
                "url": "https://github.com/SupritiVijay/ILDC/archive/refs/heads/main.zip",
                "local_path": self.data_dir / "ildc",
                "enabled": True
            },
            "bare_acts": {
                "name": "Bare Acts Text",
                "url": "https://www.indiacode.nic.in/",
                "local_path": self.data_dir / "bare_acts",
                "enabled": True
            },
            "supreme_court": {
                "name": "Supreme Court Judgments",
                "url": "https://main.sci.gov.in/judgments",
                "local_path": self.data_dir / "supreme_court",
                "enabled": True
            }
        }
        
    def setup_logging(self):
        """Setup logging for the dataset loader."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        loader_logger = logging.getLogger("dataset_loader")
        loader_logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_dir / "dataset_loader.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        loader_logger.addHandler(file_handler)
        self.logger = loader_logger
    
    def load_ildc_dataset(self, limit: int = None) -> List[Dict]:
        """Load ILDC dataset."""
        try:
            self.logger.info("Loading ILDC dataset...")
            
            # Check if dataset exists locally
            ildc_path = self.datasets["ildc"]["local_path"]
            if not ildc_path.exists():
                self.logger.info("ILDC dataset not found locally, downloading...")
                self._download_ildc_dataset()
            
            # Load dataset files
            dataset_files = list(ildc_path.glob("**/*.json"))
            if not dataset_files:
                self.logger.error("No JSON files found in ILDC dataset")
                return []
            
            documents = []
            for file_path in dataset_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Process ILDC data format
                    if isinstance(data, list):
                        for item in data:
                            doc = self._process_ildc_document(item)
                            if doc:
                                documents.append(doc)
                    elif isinstance(data, dict):
                        doc = self._process_ildc_document(data)
                        if doc:
                            documents.append(doc)
                    
                    if limit and len(documents) >= limit:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error processing file {file_path}: {e}")
                    continue
            
            self.logger.info(f"Loaded {len(documents)} documents from ILDC dataset")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error loading ILDC dataset: {e}")
            return []
    
    def _download_ildc_dataset(self):
        """Download ILDC dataset from GitHub."""
        try:
            url = self.datasets["ildc"]["url"]
            zip_path = self.data_dir / "ildc.zip"
            
            self.logger.info(f"Downloading ILDC dataset from {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.data_dir)
            
            # Move extracted files to ildc directory
            extracted_dir = self.data_dir / "ILDC-main"
            if extracted_dir.exists():
                extracted_dir.rename(self.datasets["ildc"]["local_path"])
            
            # Clean up zip file
            zip_path.unlink()
            
            self.logger.info("ILDC dataset downloaded and extracted successfully")
            
        except Exception as e:
            self.logger.error(f"Error downloading ILDC dataset: {e}")
    
    def _process_ildc_document(self, data: Dict) -> Optional[Dict]:
        """Process a single ILDC document."""
        try:
            # Extract relevant fields from ILDC format
            doc = {
                "content": data.get("text", ""),
                "title": data.get("case_title", data.get("title", "")),
                "doc_type": "judgment",
                "source": "ILDC",
                "court": data.get("court", "Unknown"),
                "date": data.get("date", ""),
                "case_id": data.get("case_id", ""),
                "url": data.get("url", ""),
                "page_number": 1
            }
            
            # Clean and validate content
            if not doc["content"] or len(doc["content"]) < 100:
                return None
            
            # Extract case citations
            citations = self._extract_case_citations(doc["content"])
            doc["citations"] = citations
            
            return doc
            
        except Exception as e:
            self.logger.warning(f"Error processing ILDC document: {e}")
            return None
    
    def load_bare_acts_dataset(self, limit: int = None) -> List[Dict]:
        """Load Bare Acts dataset."""
        try:
            self.logger.info("Loading Bare Acts dataset...")
            
            # Check if dataset exists locally
            bare_acts_path = self.datasets["bare_acts"]["local_path"]
            if not bare_acts_path.exists():
                self.logger.info("Bare Acts dataset not found locally, downloading...")
                self._download_bare_acts_dataset()
            
            # Load dataset files
            dataset_files = list(bare_acts_path.glob("**/*.txt")) + list(bare_acts_path.glob("**/*.json"))
            if not dataset_files:
                self.logger.error("No files found in Bare Acts dataset")
                return []
            
            documents = []
            for file_path in dataset_files:
                try:
                    if file_path.suffix == '.json':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        doc = self._process_bare_act_json(data, file_path)
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        doc = self._process_bare_act_text(content, file_path)
                    
                    if doc:
                        documents.append(doc)
                    
                    if limit and len(documents) >= limit:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error processing file {file_path}: {e}")
                    continue
            
            self.logger.info(f"Loaded {len(documents)} documents from Bare Acts dataset")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error loading Bare Acts dataset: {e}")
            return []
    
    def _download_bare_acts_dataset(self):
        """Download Bare Acts dataset."""
        try:
            # Create sample Bare Acts data
            sample_acts = [
                {
                    "name": "Patents Act, 1970",
                    "sections": [
                        "Section 1. Short title and commencement.",
                        "Section 2. Definitions.",
                        "Section 3. What are not inventions."
                    ]
                },
                {
                    "name": "Copyright Act, 1957",
                    "sections": [
                        "Section 1. Short title, extent and commencement.",
                        "Section 2. Definitions.",
                        "Section 3. Meaning of copyright."
                    ]
                },
                {
                    "name": "Trademarks Act, 1999",
                    "sections": [
                        "Section 1. Short title, extent and commencement.",
                        "Section 2. Definitions.",
                        "Section 3. Prohibition of registration of certain marks."
                    ]
                }
            ]
            
            bare_acts_path = self.datasets["bare_acts"]["local_path"]
            bare_acts_path.mkdir(exist_ok=True)
            
            for act in sample_acts:
                act_file = bare_acts_path / f"{act['name'].replace(' ', '_').replace(',', '')}.json"
                with open(act_file, 'w', encoding='utf-8') as f:
                    json.dump(act, f, indent=2)
            
            self.logger.info("Sample Bare Acts dataset created")
            
        except Exception as e:
            self.logger.error(f"Error creating Bare Acts dataset: {e}")
    
    def _process_bare_act_json(self, data: Dict, file_path: Path) -> Optional[Dict]:
        """Process a Bare Act JSON file."""
        try:
            content = ""
            for section in data.get("sections", []):
                content += section + "\n\n"
            
            doc = {
                "content": content.strip(),
                "title": data.get("name", file_path.stem),
                "doc_type": "statute",
                "source": "Bare Acts",
                "court": "Parliament",
                "date": "",
                "url": "",
                "page_number": 1
            }
            
            return doc if content.strip() else None
            
        except Exception as e:
            self.logger.warning(f"Error processing Bare Act JSON: {e}")
            return None
    
    def _process_bare_act_text(self, content: str, file_path: Path) -> Optional[Dict]:
        """Process a Bare Act text file."""
        try:
            doc = {
                "content": content.strip(),
                "title": file_path.stem.replace('_', ' '),
                "doc_type": "statute",
                "source": "Bare Acts",
                "court": "Parliament",
                "date": "",
                "url": "",
                "page_number": 1
            }
            
            return doc if content.strip() else None
            
        except Exception as e:
            self.logger.warning(f"Error processing Bare Act text: {e}")
            return None
    
    def load_supreme_court_dataset(self, limit: int = None) -> List[Dict]:
        """Load Supreme Court judgments dataset."""
        try:
            self.logger.info("Loading Supreme Court dataset...")
            
            # Create sample Supreme Court data
            sample_judgments = [
                {
                    "title": "Diamond v. Chakrabarty",
                    "content": "In the case of Diamond v. Chakrabarty, the Supreme Court held that a live, human-made micro-organism is patentable subject matter under the Patent Act.",
                    "date": "1980-06-16",
                    "case_number": "447 U.S. 303"
                },
                {
                    "title": "K.S. Puttaswamy v. Union of India",
                    "content": "The Supreme Court in K.S. Puttaswamy v. Union of India held that the right to privacy is a fundamental right under Article 21 of the Constitution.",
                    "date": "2017-08-24",
                    "case_number": "Writ Petition (Civil) No. 494 of 2012"
                },
                {
                    "title": "Navtej Singh Johar v. Union of India",
                    "content": "The Supreme Court in Navtej Singh Johar v. Union of India decriminalized homosexuality by striking down Section 377 of the IPC.",
                    "date": "2018-09-06",
                    "case_number": "Writ Petition (Criminal) No. 76 of 2016"
                }
            ]
            
            documents = []
            for judgment in sample_judgments:
                doc = {
                    "content": judgment["content"],
                    "title": judgment["title"],
                    "doc_type": "judgment",
                    "source": "Supreme Court of India",
                    "court": "Supreme Court",
                    "date": judgment["date"],
                    "case_number": judgment["case_number"],
                    "url": "",
                    "page_number": 1
                }
                
                # Extract citations
                citations = self._extract_case_citations(doc["content"])
                doc["citations"] = citations
                
                documents.append(doc)
                
                if limit and len(documents) >= limit:
                    break
            
            self.logger.info(f"Loaded {len(documents)} documents from Supreme Court dataset")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error loading Supreme Court dataset: {e}")
            return []
    
    def _extract_case_citations(self, content: str) -> List[str]:
        """Extract case citations from content."""
        citations = []
        
        # Pattern for case citations
        case_patterns = [
            r'([A-Z][a-z]+ v\. [A-Z][a-z]+)',
            r'(\d+ [A-Z][a-z]+ \d+)',
            r'([A-Z][a-z]+ v\. [A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in case_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        return list(set(citations))  # Remove duplicates
    
    def load_all_datasets(self, limit_per_dataset: int = None) -> Dict[str, List[Dict]]:
        """Load all available datasets."""
        all_datasets = {}
        
        # Load each dataset
        for dataset_name, dataset_config in self.datasets.items():
            if not dataset_config.get("enabled", False):
                continue
            
            try:
                if dataset_name == "ildc":
                    documents = self.load_ildc_dataset(limit_per_dataset)
                elif dataset_name == "bare_acts":
                    documents = self.load_bare_acts_dataset(limit_per_dataset)
                elif dataset_name == "supreme_court":
                    documents = self.load_supreme_court_dataset(limit_per_dataset)
                else:
                    continue
                
                all_datasets[dataset_name] = documents
                self.logger.info(f"Loaded {len(documents)} documents from {dataset_name}")
                
            except Exception as e:
                self.logger.error(f"Error loading {dataset_name}: {e}")
                all_datasets[dataset_name] = []
        
        return all_datasets
    
    def get_dataset_statistics(self, datasets: Dict[str, List[Dict]]) -> Dict:
        """Get statistics for loaded datasets."""
        stats = {
            "total_documents": 0,
            "dataset_breakdown": {},
            "document_types": {},
            "courts": {},
            "date_range": {"earliest": None, "latest": None}
        }
        
        for dataset_name, documents in datasets.items():
            dataset_stats = {
                "document_count": len(documents),
                "avg_content_length": 0,
                "document_types": {},
                "courts": {}
            }
            
            if documents:
                # Calculate average content length
                total_length = sum(len(doc.get("content", "")) for doc in documents)
                dataset_stats["avg_content_length"] = total_length / len(documents)
                
                # Count document types
                for doc in documents:
                    doc_type = doc.get("doc_type", "unknown")
                    dataset_stats["document_types"][doc_type] = dataset_stats["document_types"].get(doc_type, 0) + 1
                    
                    court = doc.get("court", "unknown")
                    dataset_stats["courts"][court] = dataset_stats["courts"].get(court, 0) + 1
                    
                    # Update global stats
                    stats["document_types"][doc_type] = stats["document_types"].get(doc_type, 0) + 1
                    stats["courts"][court] = stats["courts"].get(court, 0) + 1
                    
                    # Update date range
                    date = doc.get("date", "")
                    if date:
                        if not stats["date_range"]["earliest"] or date < stats["date_range"]["earliest"]:
                            stats["date_range"]["earliest"] = date
                        if not stats["date_range"]["latest"] or date > stats["date_range"]["latest"]:
                            stats["date_range"]["latest"] = date
            
            stats["dataset_breakdown"][dataset_name] = dataset_stats
            stats["total_documents"] += len(documents)
        
        return stats
    
    def save_dataset(self, datasets: Dict[str, List[Dict]], filename: str = None):
        """Save loaded datasets to file."""
        if filename is None:
            filename = f"legal_datasets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_file = self.data_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(datasets, f, indent=2, default=str)
        
        self.logger.info(f"Datasets saved to {output_file}")
    
    def load_dataset_from_file(self, filename: str) -> Dict[str, List[Dict]]:
        """Load datasets from file."""
        input_file = self.data_dir / filename
        
        if not input_file.exists():
            self.logger.error(f"Dataset file not found: {input_file}")
            return {}
        
        with open(input_file, 'r', encoding='utf-8') as f:
            datasets = json.load(f)
        
        self.logger.info(f"Datasets loaded from {input_file}")
        return datasets


# Example usage
def main():
    """Main function for testing the dataset loader."""
    loader = LegalDatasetLoader()
    
    # Load all datasets
    datasets = loader.load_all_datasets(limit_per_dataset=10)
    
    # Get statistics
    stats = loader.get_dataset_statistics(datasets)
    
    print("Dataset Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Save datasets
    loader.save_dataset(datasets)


if __name__ == "__main__":
    main()
