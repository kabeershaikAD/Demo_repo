#!/usr/bin/env python3
"""
Fixed Supreme Court Data Loader
Handles corrupted PDFs and implements robust processing
"""

import os
import sys
from pathlib import Path
import random
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_loader import LegalDocument
from retriever_agent import RetrieverAgent
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_supreme_court_pdf_robust(file_path: str, filename: str, metadata_df: pd.DataFrame = None) -> list:
    """Robust PDF loading with multiple fallback methods"""
    documents = []
    
    try:
        # Check file size first
        if os.path.getsize(file_path) < 2000:  # Skip files smaller than 2KB
            return documents
        
        content = ""
        
        # Method 1: Try PyMuPDF (most robust)
        try:
            import fitz
            doc = fitz.open(file_path)
            for page_num in range(min(3, doc.page_count)):  # Only first 3 pages
                page = doc[page_num]
                page_text = page.get_text()
                if page_text and page_text.strip():
                    content += page_text + "\n"
            doc.close()
        except Exception as e:
            logger.debug(f"PyMuPDF failed for {filename}: {e}")
            
            # Method 2: Try PyPDF2 as fallback
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for i in range(min(3, len(pdf_reader.pages))):
                        try:
                            page_text = pdf_reader.pages[i].extract_text()
                            if page_text and page_text.strip():
                                content += page_text + "\n"
                        except:
                            continue
            except Exception as e2:
                logger.debug(f"PyPDF2 also failed for {filename}: {e2}")
                return documents
        
        # Filter out very short content
        if len(content.strip()) < 800:  # Skip documents with less than 800 characters
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
        
        # Split content into smaller chunks for better embedding
        chunks = split_text_into_chunks(content, 1500)  # Smaller chunks
        
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
                source='Kaggle - vangap/indian-supreme-court-judgments',
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
        logger.debug(f"Error loading PDF {file_path}: {e}")
    
    return documents

def split_text_into_chunks(text: str, chunk_size: int = 1500) -> list:
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

def add_documents_to_vector_db_smart(documents: list, retriever: RetrieverAgent, max_batch_size: int = 200):
    """Smart batching that respects token limits"""
    try:
        total_added = 0
        batch_num = 1
        current_batch = []
        current_chars = 0
        max_chars_per_batch = 100000  # Conservative limit
        
        print(f"🔄 Processing {len(documents)} documents with smart batching...")
        
        for i, doc in enumerate(documents):
            doc_text = f"Title: {doc.title}\n\nContent: {doc.content}"
            doc_chars = len(doc_text)
            
            # Check if adding this document would exceed limits
            if (current_chars + doc_chars > max_chars_per_batch or 
                len(current_batch) >= max_batch_size) and current_batch:
                
                # Process current batch
                try:
                    texts = [f"Title: {d.title}\n\nContent: {d.content}" for d in current_batch]
                    metadatas = [{
                        "doc_id": d.doc_id,
                        "title": d.title,
                        "doc_type": d.doc_type,
                        "source": d.source,
                        "court": d.court or "",
                        "date": d.date or "",
                        "citations": ", ".join(d.citations) if d.citations else "",
                        "dataset": d.metadata.get('dataset', ''),
                        "filename": d.metadata.get('filename', ''),
                        "case_no": d.metadata.get('case_no', ''),
                        "petitioner": d.metadata.get('petitioner', ''),
                        "respondent": d.metadata.get('respondent', '')
                    } for d in current_batch]
                    ids = [d.doc_id for d in current_batch]
                    
                    retriever.vector_db.add_texts(
                        texts=texts,
                        metadatas=metadatas,
                        ids=ids
                    )
                    
                    total_added += len(current_batch)
                    print(f"✅ Batch {batch_num}: {len(current_batch)} documents (Total: {total_added})")
                    batch_num += 1
                    
                except Exception as e:
                    print(f"⚠️ Batch {batch_num} failed: {e}")
                    # Try smaller batches
                    for j in range(0, len(current_batch), 50):
                        small_batch = current_batch[j:j+50]
                        try:
                            texts = [f"Title: {d.title}\n\nContent: {d.content}" for d in small_batch]
                            metadatas = [{
                                "doc_id": d.doc_id,
                                "title": d.title,
                                "doc_type": d.doc_type,
                                "source": d.source,
                                "court": d.court or "",
                                "date": d.date or "",
                                "citations": ", ".join(d.citations) if d.citations else "",
                                "dataset": d.metadata.get('dataset', ''),
                                "filename": d.metadata.get('filename', ''),
                                "case_no": d.metadata.get('case_no', ''),
                                "petitioner": d.metadata.get('petitioner', ''),
                                "respondent": d.metadata.get('respondent', '')
                            } for d in small_batch]
                            ids = [d.doc_id for d in small_batch]
                            
                            retriever.vector_db.add_texts(
                                texts=texts,
                                metadatas=metadatas,
                                ids=ids
                            )
                            total_added += len(small_batch)
                            print(f"✅ Small batch: {len(small_batch)} documents")
                        except Exception as e2:
                            print(f"⚠️ Small batch also failed: {e2}")
                
                # Reset for next batch
                current_batch = []
                current_chars = 0
            
            current_batch.append(doc)
            current_chars += doc_chars
            
            if i % 100 == 0:
                print(f"🔄 Processed {i+1}/{len(documents)} documents...")
        
        # Process remaining documents
        if current_batch:
            try:
                texts = [f"Title: {d.title}\n\nContent: {d.content}" for d in current_batch]
                metadatas = [{
                    "doc_id": d.doc_id,
                    "title": d.title,
                    "doc_type": d.doc_type,
                    "source": d.source,
                    "court": d.court or "",
                    "date": d.date or "",
                    "citations": ", ".join(d.citations) if d.citations else "",
                    "dataset": d.metadata.get('dataset', ''),
                    "filename": d.metadata.get('filename', ''),
                    "case_no": d.metadata.get('case_no', ''),
                    "petitioner": d.metadata.get('petitioner', ''),
                    "respondent": d.metadata.get('respondent', '')
                } for d in current_batch]
                ids = [d.doc_id for d in current_batch]
                
                retriever.vector_db.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                total_added += len(current_batch)
                print(f"✅ Final batch: {len(current_batch)} documents (Total: {total_added})")
                
            except Exception as e:
                print(f"⚠️ Final batch failed: {e}")
        
        print(f"🎉 Successfully added {total_added} Supreme Court documents!")
        return total_added
        
    except Exception as e:
        print(f"❌ Error in smart batching: {e}")
        return 0

def load_supreme_court_judgments_fixed():
    """Load Supreme Court judgments with fixed processing"""
    print("⚖️ Loading Indian Supreme Court Judgments (FIXED VERSION)")
    print("=" * 60)
    
    try:
        import kagglehub
        
        # Check if dataset is already downloaded
        dataset_path = None
        try:
            dataset_path = kagglehub.dataset_download("vangap/indian-supreme-court-judgments")
            print(f"✅ Dataset found at: {dataset_path}")
        except:
            print("📥 Downloading dataset...")
            dataset_path = kagglehub.dataset_download("vangap/indian-supreme-court-judgments")
            print(f"✅ Dataset downloaded to: {dataset_path}")
        
        # Load CSV metadata
        csv_path = os.path.join(dataset_path, "judgments.csv")
        if os.path.exists(csv_path):
            print(f"📊 Loading metadata from {csv_path}...")
            metadata_df = pd.read_csv(csv_path)
            print(f"✅ Loaded {len(metadata_df)} judgment records")
        else:
            print("⚠️ No CSV metadata found")
            metadata_df = None
        
        # Process PDF files
        pdf_dir = os.path.join(dataset_path, "pdfs")
        if os.path.exists(pdf_dir):
            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
            print(f"📚 Found {len(pdf_files)} PDF files")
            
            # Sample more PDFs this time (1000 instead of 500)
            sample_size = min(1000, len(pdf_files))
            sampled_pdfs = random.sample(pdf_files, sample_size)
            print(f"📊 Processing {len(sampled_pdfs)} PDFs...")
            
            all_documents = []
            successful_files = 0
            
            for i, pdf_file in enumerate(sampled_pdfs):
                if i % 50 == 0:
                    print(f"🔄 Processing PDF {i+1}/{len(sampled_pdfs)}: {pdf_file}")
                
                file_path = os.path.join(pdf_dir, pdf_file)
                documents = load_supreme_court_pdf_robust(file_path, pdf_file, metadata_df)
                
                if documents:
                    all_documents.extend(documents)
                    successful_files += 1
            
            print(f"✅ Successfully processed {successful_files}/{len(sampled_pdfs)} PDF files")
            print(f"📄 Generated {len(all_documents)} document chunks")
            
            if all_documents:
                # Add to vector database with smart batching
                print(f"\n🔄 Adding documents to vector database...")
                retriever = RetrieverAgent()
                added_count = add_documents_to_vector_db_smart(all_documents, retriever)
                
                print(f"\n🎉 SUCCESS! Added {added_count} Supreme Court judgment documents!")
                print(f"📊 Total documents in database: {retriever.vector_db._collection.count()}")
            else:
                print("❌ No documents were successfully processed")
        else:
            print("❌ PDF directory not found")
            
    except Exception as e:
        print(f"❌ Error loading Supreme Court dataset: {e}")

if __name__ == "__main__":
    load_supreme_court_judgments_fixed()
