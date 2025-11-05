#!/usr/bin/env python3
"""
Setup script to download required NLTK data
"""

import nltk
import sys

def download_nltk_data():
    """Download required NLTK data"""
    print("Downloading NLTK data...")
    
    try:
        # Download punkt tokenizer
        print("Downloading punkt...")
        nltk.download('punkt', quiet=False)
        
        # Download punkt_tab (newer version)
        print("Downloading punkt_tab...")
        nltk.download('punkt_tab', quiet=False)
        
        # Download stopwords
        print("Downloading stopwords...")
        nltk.download('stopwords', quiet=False)
        
        print("NLTK data downloaded successfully!")
        return True
        
    except Exception as e:
        print(f"Error downloading NLTK data: {e}")
        return False

def test_nltk():
    """Test NLTK functionality"""
    print("\nTesting NLTK functionality...")
    
    try:
        from nltk.tokenize import sent_tokenize
        
        test_text = "This is a test sentence. This is another sentence! And one more?"
        sentences = sent_tokenize(test_text)
        
        print(f"NLTK working! Tokenized into {len(sentences)} sentences:")
        for i, sentence in enumerate(sentences, 1):
            print(f"   {i}. {sentence}")
        
        return True
        
    except Exception as e:
        print(f"NLTK test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("NLTK SETUP FOR LEGAL DATA INGESTION PIPELINE")
    print("=" * 60)
    
    # Download NLTK data
    success = download_nltk_data()
    
    if success:
        # Test NLTK
        test_success = test_nltk()
        
        if test_success:
            print("\nNLTK setup completed successfully!")
            print("You can now run the ingestion pipeline without NLTK errors.")
        else:
            print("\nNLTK data downloaded but testing failed.")
            print("The pipeline will use fallback tokenization.")
    else:
        print("\nNLTK setup failed.")
        print("The pipeline will use fallback tokenization methods.")
    
    print("\nNext steps:")
    print("1. Run: python demo_ingestion.py")
    print("2. Run: python ingest.py --sources constitution")

if __name__ == "__main__":
    main()
