# Kaggle Integration Guide

This guide explains how to download legal datasets from Kaggle and integrate them into your vector database.

## Prerequisites

1. **Kaggle Account**: Create a free account at [kaggle.com](https://www.kaggle.com)
2. **Kaggle API Key**: 
   - Go to your Kaggle account settings
   - Click "Create API Token" 
   - Download the `kaggle.json` file
   - Place it in `C:\Users\<YourUsername>\.kaggle\` (Windows) or `~/.kaggle/` (Mac/Linux)

## Installation

Install the Kaggle API:
```bash
pip install kaggle
```

## Usage

### Method 1: Using the Loader Script

1. **Find Legal Datasets on Kaggle**:
   - Go to [kaggle.com/datasets](https://www.kaggle.com/datasets)
   - Search for terms like:
     - "Indian legal"
     - "Supreme Court"
     - "legal judgments"
     - "Indian law"
     - "court cases"

2. **Add Dataset to Script**:
   - Edit `load_kaggle_data.py`
   - Add dataset names to the `legal_datasets` list:
   ```python
   legal_datasets = [
       "username/dataset-name-1",
       "username/dataset-name-2",
       # Add more datasets here
   ]
   ```

3. **Run the Script**:
   ```bash
   python load_kaggle_data.py
   ```

### Method 2: Load Specific Dataset

```bash
python load_kaggle_data.py "username/dataset-name"
```

### Method 3: Programmatic Usage

```python
from data_loader import DataLoader, DocumentToVectorDB

# Initialize loaders
loader = DataLoader()
vector_converter = DocumentToVectorDB()

# Load specific dataset
documents = loader.load_kaggle_dataset("username/dataset-name")

# Add to vector database
for doc in documents:
    vector_converter.add_document_to_chromadb(doc)
```

## Supported File Types

The Kaggle loader supports:
- **JSON**: Legal documents with structured data
- **CSV**: Tabular legal data
- **TXT**: Plain text legal documents
- **PDF**: Legal documents in PDF format

## Data Processing

The loader automatically:
1. Downloads datasets from Kaggle
2. Processes different file formats
3. Extracts text content
4. Splits large documents into chunks
5. Creates standardized `LegalDocument` objects
6. Adds metadata for tracking

## Example Legal Datasets

Here are some popular legal datasets you can try:

1. **Indian Legal Documents Corpus (ILDC)**
   - Search: "Indian Legal Documents Corpus"
   - Contains: 35k+ Indian legal judgments

2. **Supreme Court Cases**
   - Search: "Supreme Court India"
   - Contains: Court judgments and cases

3. **Legal Text Datasets**
   - Search: "legal text corpus"
   - Contains: Various legal documents

## Troubleshooting

### Common Issues

1. **Kaggle API Not Found**:
   - Ensure `kaggle.json` is in the correct location
   - Check file permissions

2. **Dataset Download Fails**:
   - Verify dataset name format: "username/dataset-name"
   - Check if dataset is public
   - Ensure you have internet connection

3. **Memory Issues**:
   - Large datasets are automatically chunked
   - Process datasets one at a time if needed

### Error Messages

- `"Kaggle API not installed"`: Run `pip install kaggle`
- `"Authentication failed"`: Check your `kaggle.json` file
- `"Dataset not found"`: Verify the dataset name and availability

## Integration with Existing System

The Kaggle loader integrates seamlessly with your existing system:

- Uses the same `LegalDocument` structure
- Stores data in the same ChromaDB instance
- Follows the same metadata format
- Works with existing retrieval and answering agents

## Best Practices

1. **Start Small**: Test with small datasets first
2. **Check Quality**: Review downloaded data before processing
3. **Monitor Storage**: Large datasets can consume significant disk space
4. **Regular Updates**: Re-run the loader periodically for new data
5. **Backup**: Keep backups of your vector database

## Next Steps

After loading Kaggle data:

1. **Test Retrieval**: Query your system to ensure data is accessible
2. **Update Indexes**: Rebuild vector indexes if needed
3. **Monitor Performance**: Check system performance with new data
4. **Evaluate Quality**: Test answer quality with new documents

## Support

If you encounter issues:

1. Check the logs in `logs/` directory
2. Verify your Kaggle API setup
3. Ensure sufficient disk space
4. Check internet connectivity

The system will automatically handle most errors and provide detailed logging for troubleshooting.
