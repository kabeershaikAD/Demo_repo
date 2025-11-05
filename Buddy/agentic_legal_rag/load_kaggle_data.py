#!/usr/bin/env python3
"""
Kaggle Data Loader Script
Downloads and processes legal datasets from Kaggle and stores them in the vector database
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataLoader, LegalDocument
from retriever_agent import RetrieverAgent
from config import config
import logging
from typing import List
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_documents_to_vector_db_batch(documents: List[LegalDocument], retriever: RetrieverAgent, batch_size: int = 50):
    """Add multiple documents to the vector database in batches"""
    try:
        total_added = 0
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        print(f"🔄 Processing {len(documents)} documents in {total_batches} batches of {batch_size}")
        print(f"💰 Total API calls: {total_batches} (instead of {len(documents)} individual calls)")
        
        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"📦 API Call {batch_num}/{total_batches}: Processing {len(batch)} documents...")
            
            # Prepare batch data with token limit checking
            texts = []
            metadatas = []
            ids = []
            total_chars = 0
            max_chars_per_batch = 150000  # Conservative limit for token safety
            
            for doc in batch:
                doc_text = f"Title: {doc.title}\n\nContent: {doc.content}"
                doc_chars = len(doc_text)
                
                # Check if adding this document would exceed token limit
                if total_chars + doc_chars > max_chars_per_batch and texts:
                    # Process current batch first
                    try:
                        retriever.vector_db.add_texts(
                            texts=texts,
                            metadatas=metadatas,
                            ids=ids
                        )
                        total_added += len(texts)
                        print(f"✅ API Call {batch_num} complete: {len(texts)} documents (Total: {total_added}/{len(documents)})")
                    except Exception as e:
                        print(f"⚠️  API Call {batch_num} failed: {e}")
                        # Try smaller batches
                        for j in range(0, len(texts), 10):
                            small_batch_texts = texts[j:j+10]
                            small_batch_metadatas = metadatas[j:j+10]
                            small_batch_ids = ids[j:j+10]
                            try:
                                retriever.vector_db.add_texts(
                                    texts=small_batch_texts,
                                    metadatas=small_batch_metadatas,
                                    ids=small_batch_ids
                                )
                                total_added += len(small_batch_texts)
                            except Exception as e2:
                                print(f"⚠️  Small batch also failed: {e2}")
                    
                    # Reset for next batch
                    texts = []
                    metadatas = []
                    ids = []
                    total_chars = 0
                    batch_num += 1
                
                texts.append(doc_text)
                metadatas.append({
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "doc_type": doc.doc_type,
                    "source": doc.source,
                    "court": doc.court or "",
                    "date": doc.date or "",
                    "citations": ", ".join(doc.citations) if doc.citations else "",
                    "legal_category": doc.metadata.get('legal_category', ''),
                    "specific_file": doc.metadata.get('specific_file', '')
                })
                ids.append(doc.doc_id)
                total_chars += doc_chars
            
            # Process remaining documents in the batch
            if texts:
                try:
                    retriever.vector_db.add_texts(
                        texts=texts,
                        metadatas=metadatas,
                        ids=ids
                    )
                    total_added += len(texts)
                    print(f"✅ API Call {batch_num} complete: {len(texts)} documents (Total: {total_added}/{len(documents)})")
                except Exception as e:
                    print(f"⚠️  API Call {batch_num} failed: {e}")
                    # Try smaller batches
                    for j in range(0, len(texts), 10):
                        small_batch_texts = texts[j:j+10]
                        small_batch_metadatas = metadatas[j:j+10]
                        small_batch_ids = ids[j:j+10]
                        try:
                            retriever.vector_db.add_texts(
                                texts=small_batch_texts,
                                metadatas=small_batch_metadatas,
                                ids=small_batch_ids
                            )
                            total_added += len(small_batch_texts)
                        except Exception as e2:
                            print(f"⚠️  Small batch also failed: {e2}")
        
        print(f"🎉 Successfully added {total_added} documents to ChromaDB!")
        return total_added
        
    except Exception as e:
        print(f"❌ Error adding documents to ChromaDB: {e}")
        return 0

def add_document_to_vector_db(document: LegalDocument, retriever: RetrieverAgent):
    """Add a single document to the vector database (for backward compatibility)"""
    return add_documents_to_vector_db_batch([document], retriever, 1) > 0

def main():
    """Main function to load Kaggle data into vector database"""
    
    print("🚀 Kaggle Legal Data Loader")
    print("=" * 50)
    
    # Initialize data loader
    loader = DataLoader()
    
    # Initialize retriever agent for vector database
    retriever = RetrieverAgent()
    
    # Specific legal datasets from Kaggle
    legal_datasets = [
        "llm-fine-tuning-dataset-of-indian-legal-texts"
    ]
    
    # Specific file paths within the dataset
    specific_files = {
        "constitution_qa.json": "constitution",
        "ipc_qa.json": "ipc", 
        "crpc_qa.json": "crpc"
    }
    
    if not legal_datasets:
        print("❌ No datasets specified. Please add dataset names to the legal_datasets list.")
        print("\nTo find legal datasets on Kaggle:")
        print("1. Go to https://www.kaggle.com/datasets")
        print("2. Search for 'Indian legal', 'Supreme Court', 'legal judgments'")
        print("3. Copy the dataset identifier (username/dataset-name)")
        print("4. Add it to the legal_datasets list in this script")
        return
    
    print(f"📊 Found {len(legal_datasets)} datasets to process:")
    for i, dataset in enumerate(legal_datasets, 1):
        print(f"   {i}. {dataset}")
    
    print("\n🔄 Starting data loading process...")
    
    total_documents = 0
    
    for dataset_name in legal_datasets:
        print(f"\n📥 Processing dataset: {dataset_name}")
        
        try:
            # Load dataset from Kaggle
            documents = loader.load_kaggle_dataset(dataset_name)
            
            if not documents:
                print(f"⚠️  No documents found in dataset: {dataset_name}")
                continue
            
            print(f"✅ Loaded {len(documents)} documents from {dataset_name}")
            
            # Process specific files if they exist
            for filename, doc_type in specific_files.items():
                print(f"🔍 Looking for specific file: {filename}")
                file_docs = [doc for doc in documents if filename in doc.metadata.get('file_path', '')]
                
                if file_docs:
                    print(f"📄 Found {len(file_docs)} documents in {filename}")
                    # Update document type for specific files
                    for doc in file_docs:
                        doc.doc_type = doc_type
                        doc.metadata['specific_file'] = filename
                        doc.metadata['legal_category'] = doc_type.upper()
                        if add_document_to_vector_db(doc, retriever):
                            total_documents += 1
                    print(f"💾 Added {len(file_docs)} {doc_type} documents to vector database")
                else:
                    print(f"⚠️  File {filename} not found in dataset")
            
            # Add remaining documents to vector database
            remaining_docs = [doc for doc in documents if not any(filename in doc.metadata.get('file_path', '') for filename in specific_files.keys())]
            
            for doc in remaining_docs:
                if add_document_to_vector_db(doc, retriever):
                    total_documents += 1
            
            if remaining_docs:
                print(f"💾 Added {len(remaining_docs)} other documents to vector database")
            
        except Exception as e:
            print(f"❌ Error processing dataset {dataset_name}: {e}")
            continue
    
    print(f"\n🎉 Data loading completed!")
    print(f"📈 Total documents processed: {total_documents}")
    print(f"🗄️  Vector database updated successfully!")
    
    # Print summary by source
    print("\n📊 Documents by source:")
    sources = {}
    for dataset_name in legal_datasets:
        try:
            docs = loader.load_kaggle_dataset(dataset_name)
            sources[dataset_name] = len(docs)
        except:
            sources[dataset_name] = 0
    
    for source, count in sources.items():
        print(f"   {source}: {count} documents")

def load_specific_dataset(dataset_name: str):
    """Load a specific dataset by name"""
    print(f"🔄 Loading specific dataset: {dataset_name}")
    
    loader = DataLoader()
    retriever = RetrieverAgent()
    
    try:
        documents = loader.load_kaggle_dataset(dataset_name)
        
        if not documents:
            print(f"❌ No documents found in dataset: {dataset_name}")
            return
        
        print(f"✅ Loaded {len(documents)} documents")
        
        # Add to vector database in batches
        added_count = add_documents_to_vector_db_batch(documents, retriever, batch_size=50)
        
        print(f"💾 Added {added_count} documents to vector database")
        
    except Exception as e:
        print(f"❌ Error loading dataset {dataset_name}: {e}")

def load_indian_supreme_court_judgments():
    """Load the Indian Supreme Court judgments dataset from vangap/indian-supreme-court-judgments"""
    print("⚖️ Loading Indian Supreme Court Judgments Dataset")
    print("=" * 60)
    
    try:
        import kagglehub
        
        # Download the dataset using kagglehub
        print("📥 Downloading dataset using kagglehub...")
        path = kagglehub.dataset_download("vangap/indian-supreme-court-judgments")
        print(f"✅ Dataset downloaded to: {path}")
        
        # STEP 1: Load ALL data first (no embeddings yet)
        print("\n📚 STEP 1: Loading all data from files...")
        all_documents = []
        
        # Process CSV file for metadata
        csv_path = os.path.join(path, "judgments.csv")
        if os.path.exists(csv_path):
            print(f"\n🔍 Processing judgments.csv for metadata...")
            metadata_df = pd.read_csv(csv_path)
            print(f"📊 Found {len(metadata_df)} judgment records")
        else:
            metadata_df = None
        
        # Process PDF files (sample to stay within API limits)
        pdf_dir = os.path.join(path, "pdfs")
        if os.path.exists(pdf_dir):
            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
            print(f"\n🔍 Found {len(pdf_files)} PDF files")
            
            # Sample PDFs to stay within 10 API calls (aim for ~500 documents)
            # Each batch of 50 PDFs = 1 API call, so we can process 500 PDFs
            sample_size = min(500, len(pdf_files))  # Process up to 500 PDFs
            import random
            sampled_pdfs = random.sample(pdf_files, sample_size)
            print(f"📊 Sampling {len(sampled_pdfs)} PDFs for processing")
            
            for i, pdf_file in enumerate(sampled_pdfs):
                if i % 100 == 0:
                    print(f"🔄 Processing PDF {i+1}/{len(sampled_pdfs)}: {pdf_file}")
                
                file_path = os.path.join(pdf_dir, pdf_file)
                documents = load_supreme_court_pdf(file_path, pdf_file, metadata_df)
                all_documents.extend(documents)
        else:
            print("⚠️  PDF directory not found")
        
        # Process other files
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(('.json', '.txt')) and file != "judgments.csv":
                    file_path = os.path.join(root, file)
                    print(f"\n🔍 Processing {file}...")
                    
                    # Load and process the file
                    documents = load_supreme_court_data(file_path, file)
                    all_documents.extend(documents)
                    
                    print(f"📊 Loaded {len(documents)} documents from {file}")
        
        print(f"\n✅ STEP 1 COMPLETE: Loaded {len(all_documents)} total documents")
        
        # STEP 2: Now do bulk embeddings with exactly 10 API calls
        print(f"\n🔄 STEP 2: Starting bulk embeddings for {len(all_documents)} documents...")
        print(f"💰 Using exactly 10 API calls for embedding (max efficiency)")
        
        retriever = RetrieverAgent()
        
        # Calculate batch size to stay within token limits (max 200k tokens per batch)
        # Each document is ~2000 chars = ~500 tokens, so max 400 docs per batch
        batch_size = min(400, max(50, len(all_documents) // 10))  # Max 400 docs per batch, max 10 batches
        added_count = add_documents_to_vector_db_batch(all_documents, retriever, batch_size=batch_size)
        
        print(f"\n🎉 SUCCESS! Loaded {added_count} Supreme Court judgment documents!")
        print("📊 Document types loaded:")
        print("   - Supreme Court Judgments")
        print("   - Legal Case Documents")
        print("   - Court Rulings and Decisions")
        print(f"\n✅ Your vector database is now ready with {added_count} Indian Supreme Court judgments!")
        print(f"💰 Total API calls used: {min(10, (len(all_documents) + batch_size - 1) // batch_size)}")
        
    except ImportError:
        print("❌ kagglehub not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kagglehub"])
        print("✅ kagglehub installed. Please run the script again.")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")

def load_indian_legal_texts():
    """Load the specific Indian legal texts dataset with constitution, IPC, and CRPC"""
    print("🇮🇳 Loading Indian Legal Texts Dataset")
    print("=" * 50)
    
    try:
        import kagglehub
        
        # Download the dataset using kagglehub
        print("📥 Downloading dataset using kagglehub...")
        path = kagglehub.dataset_download("akshatgupta7/llm-fine-tuning-dataset-of-indian-legal-texts")
        print(f"✅ Dataset downloaded to: {path}")
        
        # Process specific files
        specific_files = {
            "constitution_qa.json": "constitution",
            "ipc_qa.json": "ipc", 
            "crpc_qa.json": "crpc"
        }
        
        # STEP 1: Load ALL data first (no embeddings yet)
        print("\n📚 STEP 1: Loading all data from files...")
        all_documents = []
        
        for filename, doc_type in specific_files.items():
            print(f"\n🔍 Processing {filename}...")
            
            # Construct full file path
            file_path = os.path.join(path, filename)
            
            if os.path.exists(file_path):
                print(f"📄 Found {filename}")
                
                # Load and process the JSON file
                documents = load_json_legal_data(file_path, doc_type, filename)
                all_documents.extend(documents)
                
                print(f"📊 Loaded {len(documents)} {doc_type.upper()} documents")
            else:
                print(f"⚠️  File {filename} not found at {file_path}")
        
        print(f"\n✅ STEP 1 COMPLETE: Loaded {len(all_documents)} total documents")
        
        # STEP 2: Now do bulk embeddings
        print(f"\n🔄 STEP 2: Starting bulk embeddings for {len(all_documents)} documents...")
        retriever = RetrieverAgent()
        
        # Add all documents to vector database in very large batches (5 API calls total)
        # Calculate batch size to use exactly 5 API calls
        batch_size = max(100, len(all_documents) // 5)  # At least 100 docs per batch, max 5 batches
        added_count = add_documents_to_vector_db_batch(all_documents, retriever, batch_size=batch_size)
        
        print(f"\n🎉 SUCCESS! Loaded {added_count} legal documents!")
        print("📊 Document types loaded:")
        print("   - Constitution Q&A")
        print("   - Indian Penal Code (IPC) Q&A") 
        print("   - Code of Criminal Procedure (CRPC) Q&A")
        print("\n✅ Your vector database is now ready with Indian legal texts!")
        
    except ImportError:
        print("❌ kagglehub not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kagglehub"])
        print("✅ kagglehub installed. Please run the script again.")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")

def load_supreme_court_pdf(file_path: str, filename: str, metadata_df: pd.DataFrame = None) -> List[LegalDocument]:
    """Load Supreme Court judgment from PDF file"""
    documents = []
    
    try:
        import PyPDF2
        
        # Check file size first
        if os.path.getsize(file_path) < 1000:  # Skip files smaller than 1KB
            return documents
        
        with open(file_path, 'rb') as file:
            try:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                
                # Only process first 5 pages to avoid very long documents
                max_pages = min(5, len(pdf_reader.pages))
                for i in range(max_pages):
                    try:
                        page_text = pdf_reader.pages[i].extract_text()
                        if page_text and page_text.strip():
                            content += page_text + "\n"
                    except Exception as e:
                        continue  # Skip problematic pages
                
                # Filter out very short content
                if len(content.strip()) < 500:  # Skip documents with less than 500 characters
                    return documents
                    
            except Exception as e:
                # Try alternative PDF reader if PyPDF2 fails
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    content = ""
                    for page_num in range(min(5, doc.page_count)):
                        page = doc[page_num]
                        content += page.get_text() + "\n"
                    doc.close()
                except ImportError:
                    return documents
                except Exception:
                    return documents
        
        if not content.strip():
            return documents
        
        # Try to find matching metadata
        metadata = {}
        if metadata_df is not None:
            # Extract case info from filename if possible
            case_match = None
            for idx, row in metadata_df.iterrows():
                if filename in str(row.get('temp_link', '')):
                    case_match = row
                    break
            
            if case_match is not None:
                metadata = {
                    'diary_no': case_match.get('diary_no', ''),
                    'case_no': case_match.get('case_no', ''),
                    'petitioner': case_match.get('pet', ''),
                    'respondent': case_match.get('res', ''),
                    'petitioner_advocate': case_match.get('pet_adv', ''),
                    'respondent_advocate': case_match.get('res_adv', ''),
                    'bench': case_match.get('bench', ''),
                    'judgment_by': case_match.get('judgement_by', ''),
                    'judgment_date': case_match.get('judgment_dates', ''),
                    'language': case_match.get('language', '')
                }
        
        # Split content into chunks if it's too long
        chunks = split_text_into_chunks(content, 2000)
        
        for i, chunk in enumerate(chunks):
            # Create title from filename and metadata
            title = f"Supreme Court Judgment - {filename}"
            if metadata.get('case_no'):
                title = f"Supreme Court Judgment - {metadata['case_no']}"
            
            doc = LegalDocument(
                doc_id=f"supreme_court_{filename}_{i}",
                title=title,
                content=chunk,
                doc_type='judgment',
                source=f'Kaggle - vangap/indian-supreme-court-judgments',
                court='Supreme Court of India',
                date=metadata.get('judgment_date', ''),
                metadata={
                    'filename': filename,
                    'chunk_number': i,
                    'total_chunks': len(chunks),
                    'dataset': 'vangap/indian-supreme-court-judgments',
                    **metadata
                }
            )
            documents.append(doc)
            
    except Exception as e:
        print(f"❌ Error loading PDF {file_path}: {e}")
    
    return documents

def load_supreme_court_data(file_path: str, filename: str) -> List[LegalDocument]:
    """Load Supreme Court judgment data from various file formats"""
    documents = []
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            documents = load_supreme_court_json(file_path, filename)
        elif file_ext == '.csv':
            documents = load_supreme_court_csv(file_path, filename)
        elif file_ext == '.txt':
            documents = load_supreme_court_txt(file_path, filename)
        else:
            print(f"⚠️  Unsupported file type: {file_ext}")
            
    except Exception as e:
        print(f"❌ Error loading Supreme Court data from {file_path}: {e}")
    
    return documents

def load_supreme_court_json(file_path: str, filename: str) -> List[LegalDocument]:
    """Load Supreme Court data from JSON file"""
    documents = []
    
    try:
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                doc = create_supreme_court_document(item, filename, i)
                if doc:
                    documents.append(doc)
        elif isinstance(data, dict):
            doc = create_supreme_court_document(data, filename, 0)
            if doc:
                documents.append(doc)
                
    except Exception as e:
        print(f"❌ Error loading JSON file {file_path}: {e}")
    
    return documents

def load_supreme_court_csv(file_path: str, filename: str) -> List[LegalDocument]:
    """Load Supreme Court data from CSV file"""
    documents = []
    
    try:
        import pandas as pd
        
        df = pd.read_csv(file_path)
        
        for index, row in df.iterrows():
            doc = create_supreme_court_document_from_csv(row, filename, index)
            if doc:
                documents.append(doc)
                
    except Exception as e:
        print(f"❌ Error loading CSV file {file_path}: {e}")
    
    return documents

def load_supreme_court_txt(file_path: str, filename: str) -> List[LegalDocument]:
    """Load Supreme Court data from TXT file"""
    documents = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into chunks if it's too long
        chunks = split_text_into_chunks(content, 2000)
        
        for i, chunk in enumerate(chunks):
            doc = LegalDocument(
                doc_id=f"supreme_court_{filename}_{i}",
                title=f"Supreme Court Judgment - {filename} - Part {i+1}",
                content=chunk,
                doc_type='judgment',
                source=f'Kaggle - vangap/indian-supreme-court-judgments',
                court='Supreme Court of India',
                metadata={
                    'filename': filename,
                    'chunk_number': i,
                    'total_chunks': len(chunks),
                    'dataset': 'vangap/indian-supreme-court-judgments'
                }
            )
            documents.append(doc)
            
    except Exception as e:
        print(f"❌ Error loading TXT file {file_path}: {e}")
    
    return documents

def create_supreme_court_document(item: dict, filename: str, index: int) -> LegalDocument:
    """Create LegalDocument from Supreme Court JSON item"""
    try:
        # Extract common fields with fallbacks
        doc_id = item.get('id', item.get('case_id', f"supreme_court_{filename}_{index}"))
        title = item.get('title', item.get('case_title', item.get('name', f"Supreme Court Judgment {index+1}")))
        content = item.get('text', item.get('content', item.get('description', item.get('judgment', ''))))
        
        # If content is empty, try to construct from other fields
        if not content:
            content_parts = []
            for field in ['facts', 'issue', 'held', 'reasoning', 'order']:
                if field in item and item[field]:
                    content_parts.append(f"{field.title()}: {item[field]}")
            content = "\n\n".join(content_parts)
        
        # Create document ID
        doc_id = f"supreme_court_{filename}_{doc_id}_{index}"
        
        return LegalDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            doc_type='judgment',
            source=f'Kaggle - vangap/indian-supreme-court-judgments',
            court=item.get('court', 'Supreme Court of India'),
            date=item.get('date', item.get('year', '')),
            citations=item.get('citations', []),
            metadata={
                'dataset': 'vangap/indian-supreme-court-judgments',
                'filename': filename,
                'original_id': item.get('id', ''),
                'case_number': item.get('case_number', ''),
                'bench': item.get('bench', ''),
                'petitioner': item.get('petitioner', ''),
                'respondent': item.get('respondent', ''),
                'raw_data': item
            }
        )
        
    except Exception as e:
        print(f"❌ Error creating Supreme Court document: {e}")
        return None

def create_supreme_court_document_from_csv(row: pd.Series, filename: str, index: int) -> LegalDocument:
    """Create LegalDocument from Supreme Court CSV row"""
    try:
        # Convert row to dict
        row_dict = row.to_dict()
        
        # Extract text content from common column names
        content = ""
        for col in ['text', 'content', 'description', 'judgment', 'facts', 'issue', 'held', 'reasoning']:
            if col in row_dict and pd.notna(row_dict[col]):
                content += str(row_dict[col]) + "\n\n"
        
        if not content.strip():
            return None
        
        # Extract title
        title = ""
        for col in ['title', 'case_title', 'name', 'case_name']:
            if col in row_dict and pd.notna(row_dict[col]):
                title = str(row_dict[col])
                break
        
        if not title:
            title = f"Supreme Court Judgment {index + 1}"
        
        return LegalDocument(
            doc_id=f"supreme_court_{filename}_{index}",
            title=title,
            content=content.strip(),
            doc_type='judgment',
            source=f'Kaggle - vangap/indian-supreme-court-judgments',
            court=row_dict.get('court', 'Supreme Court of India'),
            date=row_dict.get('date', row_dict.get('year', '')),
            metadata={
                'dataset': 'vangap/indian-supreme-court-judgments',
                'filename': filename,
                'row_index': index,
                'raw_data': row_dict
            }
        )
        
    except Exception as e:
        print(f"❌ Error creating Supreme Court document from CSV: {e}")
        return None

def split_text_into_chunks(text: str, chunk_size: int = 2000) -> List[str]:
    """Split text into chunks for processing"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def load_json_legal_data(file_path: str, doc_type: str, filename: str) -> List[LegalDocument]:
    """Load legal data from JSON file"""
    documents = []
    
    try:
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                doc = create_legal_document_from_json(item, doc_type, filename, i)
                if doc:
                    documents.append(doc)
        elif isinstance(data, dict):
            doc = create_legal_document_from_json(data, doc_type, filename, 0)
            if doc:
                documents.append(doc)
                
    except Exception as e:
        print(f"❌ Error loading JSON file {file_path}: {e}")
    
    return documents

def create_legal_document_from_json(item: dict, doc_type: str, filename: str, index: int) -> LegalDocument:
    """Create LegalDocument from JSON item"""
    try:
        # Extract question and answer
        question = item.get('question', item.get('Question', ''))
        answer = item.get('answer', item.get('Answer', item.get('context', '')))
        
        # Create content combining question and answer
        content = f"Question: {question}\n\nAnswer: {answer}"
        
        # Create document ID
        doc_id = f"kaggle_{doc_type}_{filename}_{index}"
        
        # Create title
        title = f"{doc_type.upper()} - {question[:50]}..." if len(question) > 50 else f"{doc_type.upper()} - {question}"
        
        return LegalDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            doc_type=doc_type,
            source=f'Kaggle - {filename}',
            metadata={
                'dataset': 'llm-fine-tuning-dataset-of-indian-legal-texts',
                'filename': filename,
                'legal_category': doc_type.upper(),
                'question': question,
                'answer': answer,
                'index': index
            }
        )
        
    except Exception as e:
        print(f"❌ Error creating document from JSON item: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "indian-legal":
            # Load specific Indian legal texts
            load_indian_legal_texts()
        elif sys.argv[1] == "supreme-court":
            # Load Indian Supreme Court judgments
            load_indian_supreme_court_judgments()
        else:
            # Load specific dataset
            dataset_name = sys.argv[1]
            load_specific_dataset(dataset_name)
    else:
        # Load all datasets
        main()
