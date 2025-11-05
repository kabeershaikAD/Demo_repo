# Legal Data Ingestion Pipeline

A comprehensive modular pipeline for scraping, processing, and ingesting legal data from multiple sources into your existing ChromaDB instance.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline (scrapes all sources)
python ingest.py

# Run with specific sources
python ingest.py --sources constitution huggingface

# Run with custom parameters
python ingest.py --chunk-size 1000 --overlap 150 --clear-existing
```

## 📁 Pipeline Architecture

```
scraper.py     → Downloads data from legal sources
preprocess.py  → Cleans, chunks, and normalizes text
embed.py       → Generates embeddings using sentence-transformers
load_chroma.py → Loads embeddings into your existing ChromaDB
ingest.py      → Main orchestrator CLI
```

## 🔧 Supported Sources

| Source | Description | Status |
|--------|-------------|--------|
| **IndiaCode** | Central Acts from indiacode.nic.in | ✅ Implemented |
| **Constitution** | Constitution of India | ✅ Implemented |
| **GitHub** | Indian Law JSON repositories | 🔄 Partial |
| **Zenodo** | Annotated Central Acts Dataset | ✅ Implemented |
| **ILDC** | Indian Legal Documents Corpus | 🔄 Partial |
| **Kaggle** | Legal datasets via Kaggle API | ✅ Implemented |
| **Hugging Face** | Legal datasets via datasets library | ✅ Implemented |
| **LawSum** | Legal summarization corpora | ✅ Implemented |

## 📊 Data Flow

```
Raw Sources → Scraping → Preprocessing → Embedding → ChromaDB
     ↓            ↓           ↓            ↓          ↓
  HTML/JSON → Clean Text → Chunks → Vectors → Searchable
```

## 🛠️ Usage Examples

### Basic Usage

```bash
# Run complete pipeline
python ingest.py

# Clear existing data and reload
python ingest.py --clear-existing

# Use specific sources only
python ingest.py --sources constitution indiacode
```

### Advanced Usage

```bash
# Custom chunking parameters
python ingest.py --chunk-size 1000 --overlap 150

# Different embedding model
python ingest.py --embedding-model sentence-transformers/all-mpnet-base-v2

# Custom collection name
python ingest.py --collection-name my_legal_docs

# Load from existing embeddings
python ingest.py --from-existing data/legal_embeddings.json
```

### Programmatic Usage

```python
from ingest import LegalDataIngestionPipeline

# Initialize pipeline
pipeline = LegalDataIngestionPipeline(
    chunk_size=800,
    overlap=100,
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    collection_name="legal_documents"
)

# Run full pipeline
stats = pipeline.run_full_pipeline(
    sources=['constitution', 'huggingface'],
    clear_existing=True,
    save_intermediate=True
)

print(f"Processed {stats['processed_documents']} documents")
print(f"Created {stats['total_chunks']} chunks")
print(f"Loaded {stats['chroma_documents']} into ChromaDB")
```

## 📋 Configuration

### Chunking Parameters

- `--chunk-size`: Number of tokens per chunk (default: 800)
- `--overlap`: Overlap between chunks (default: 100)

### Embedding Parameters

- `--embedding-model`: Sentence transformer model (default: all-MiniLM-L6-v2)
- Available models:
  - `sentence-transformers/all-MiniLM-L6-v2` (fast, good quality)
  - `sentence-transformers/all-mpnet-base-v2` (better quality, slower)
  - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (multilingual)

### ChromaDB Parameters

- `--collection-name`: Name of ChromaDB collection (default: legal_documents)
- `--clear-existing`: Clear existing collection before loading

## 📁 Output Files

The pipeline creates several intermediate files:

```
data/
├── scraped_legal_data.json      # Raw scraped data
├── processed_legal_data.json    # Cleaned and chunked data
└── legal_embeddings.json        # Generated embeddings

logs/
├── ingestion.log                # Pipeline logs
└── pipeline_stats.json         # Pipeline statistics
```

## 🔍 Testing the Pipeline

```bash
# Test with a small subset
python ingest.py --sources constitution --chunk-size 500

# Test search functionality
python -c "
from load_chroma import ChromaDBManager
manager = ChromaDBManager()
results = manager.test_search('article 21 constitution')
print(f'Found {len(results)} results')
"
```

## 🚨 Troubleshooting

### Common Issues

1. **Memory Issues**: Reduce `--chunk-size` or process sources individually
2. **API Rate Limits**: Add delays in scraper.py for external APIs
3. **ChromaDB Errors**: Check if collection exists and is accessible
4. **Missing Dependencies**: Run `pip install -r requirements.txt`

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python ingest.py --sources constitution
```

## 📈 Performance Tips

1. **Batch Processing**: The pipeline processes data in batches for memory efficiency
2. **Parallel Processing**: Consider running multiple sources in parallel
3. **Incremental Updates**: Use `--from-existing` to skip scraping
4. **GPU Acceleration**: Install CUDA for faster embedding generation

## 🔧 Customization

### Adding New Sources

1. Create a new scraper class in `scraper.py`
2. Implement the scraping logic
3. Add to `LegalDataScraper.scrapers` dictionary
4. Test with `python ingest.py --sources your_new_source`

### Custom Preprocessing

1. Modify `TextCleaner` class in `preprocess.py`
2. Add custom cleaning rules
3. Adjust chunking strategy in `TextChunker`

### Custom Embeddings

1. Change embedding model in `embed.py`
2. Modify `LegalEmbedder` class
3. Update model loading logic

## 📊 Monitoring

The pipeline provides detailed logging and statistics:

- **Real-time Progress**: See progress for each step
- **Performance Metrics**: Processing time, memory usage
- **Quality Metrics**: Chunk counts, embedding dimensions
- **Search Testing**: Automatic search functionality testing

## 🔒 Security Notes

- **API Keys**: Store sensitive API keys in environment variables
- **Rate Limiting**: Built-in delays to respect API limits
- **Data Privacy**: All processing is done locally
- **ChromaDB Security**: Uses your existing ChromaDB configuration

## 📚 Integration with Existing System

This pipeline integrates seamlessly with your existing Agentic Legal RAG system:

1. **Uses Existing ChromaDB**: Loads into your current collection
2. **Compatible Format**: Maintains existing document structure
3. **No Conflicts**: Works alongside existing data
4. **Easy Testing**: Test with your existing search queries

## 🎯 Next Steps

1. **Run Initial Pipeline**: Start with `python ingest.py --sources constitution`
2. **Test Integration**: Verify with your existing RAG system
3. **Scale Up**: Add more sources gradually
4. **Monitor Performance**: Check logs and statistics
5. **Customize**: Modify for your specific needs

---

**Ready to ingest legal data? Run `python ingest.py` and watch the magic happen!** 🚀






