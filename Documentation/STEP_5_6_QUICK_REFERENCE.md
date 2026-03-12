# Step-5 & Step-6 Quick Reference

## What's New

**Step-5: Intelligent Section Detection & Chunking**
- Detect tender sections (eligibility, technical, deadlines, penalties, etc.)
- Smart chunking: 800-1200 tokens, respects sentence boundaries
- Preserve section metadata throughout processing

**Step-6: FAISS Vector Indexing for Semantic Search**
- Generate embeddings (OpenAI or local models)
- Create FAISS indices for fast similarity search
- Query by section type (eligibility, penalties, deadlines, technical)

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New packages:
- `openai==1.3.5` - For embeddings
- `faiss-cpu==1.7.4` - Vector search
- `tiktoken==0.5.2` - Token counting
- `sentence-transformers==2.2.2` - Local embeddings
- `scikit-learn==1.3.2` - ML utilities
- `nltk==3.8.1` - NLP tokenization

### 2. Process a Tender

```python
from app.services.tender_processing_pipeline import TenderProcessingPipeline

# Initialize
pipeline = TenderProcessingPipeline(
    embedding_provider="sentence-transformers",  # No API key needed
    embedding_model="all-MiniLM-L6-v2"
)

# Process file
result = pipeline.process_file("tender.pdf", "tender_001")

# Result includes:
# - sections: Detected document sections
# - chunks: Semantically chunked content (800-1200 tokens)
# - embeddings: Vector embeddings for each chunk
# - statistics: Processing metrics
```

### 3. Search a Tender

```python
# Find similar content
results = pipeline.query_tender(
    tender_id="tender_001",
    query="What are the qualification requirements?",
    k=5,  # Top 5 results
    section_type="eligibility"  # Optional: filter by type
)

for result in results:
    print(f"Relevance: {result['similarity']:.1%}")
    print(f"Section: {result['section_type']}")
    print(f"Text: {result['text'][:100]}...")
```

---

## Core Components

### Section Detector

Identifies tender document sections with 8+ categories:

```python
from app.services.section_detector import SectionDetector, SectionType

detector = SectionDetector()
sections = detector.detect_sections(text)

# Available section types:
# - SectionType.ELIGIBILITY
# - SectionType.TECHNICAL_REQUIREMENTS
# - SectionType.COMMERCIAL_REQUIREMENTS
# - SectionType.DEADLINES
# - SectionType.PENALTIES
# - SectionType.EVALUATION_CRITERIA
# - SectionType.SCOPE
# - SectionType.DELIVERABLES
# - SectionType.OTHER
```

### Text Chunker

Breaks documents into semantic chunks (800-1200 tokens):

```python
from app.services.chunker import TextChunker, ChunkingStrategy

chunker = TextChunker(
    chunk_size_tokens=1000,    # Target size
    min_chunk_size=800,        # Minimum
    max_chunk_size=1200,       # Maximum
    overlap_tokens=100         # Context overlap
)

chunks = chunker.chunk_text(text, section_type, page_number)

# Each chunk has:
# - text: Content
# - tokens: Token count
# - section_type: Detected section
# - page: Original page number
# - within_limits: Is it 800-1200 tokens?
```

### Embedding Pipeline

Generate embeddings with multiple providers:

```python
from app.services.embeddings_pipeline import create_embedding_pipeline

# Option 1: OpenAI (requires API key)
pipeline = create_embedding_pipeline(
    provider_type="openai",
    model_name="text-embedding-3-small"
)

# Option 2: Local (no API key)
pipeline = create_embedding_pipeline(
    provider_type="sentence-transformers",
    model_name="all-MiniLM-L6-v2"
)

# Embed text
embeddings = pipeline.embed_texts(["text1", "text2", "text3"])
# Returns: (3, 384) array

# Embed query
query_emb = pipeline.embed_query("What is required?")
# Returns: (384,) array
```

### FAISS Index Manager

Create searchable vector indices:

```python
from app.services.faiss_manager import FAISSIndexManager, VectorStore

manager = FAISSIndexManager()

# Create index
manager.create_index("tender_001", dimension=384)

# Add embeddings
manager.add_embeddings("tender_001", embeddings, metadata)

# Search
results = manager.search("tender_001", query_embedding, k=5)

# Search by section
eligibility = manager.search_eligibility("tender_001", query_emb, k=5)
penalties = manager.search_penalties("tender_001", query_emb, k=5)
deadlines = manager.search_deadlines("tender_001", query_emb, k=5)

# Save/load
manager.save_index("tender_001")
manager.load_index("tender_001")
```

---

## Embedding Models

### OpenAI Models

| Model | Dimension | Speed | Quality | Cost |
|-------|-----------|-------|---------|------|
| text-embedding-3-small | 1536 | Fast | Excellent | $$ |
| text-embedding-3-large | 3072 | Slower | Best | $$$$ |

### Local Models (SentenceTransformers)

| Model | Dimension | Speed | Quality |
|-------|-----------|-------|---------|
| all-MiniLM-L6-v2 | 384 | ⚡⚡⚡ Fast | ✓ Good |
| all-mpnet-base-v2 | 768 | ⚡⚡ Medium | ✓✓ Better |
| paraphrase-MiniLM-L6-v2 | 384 | ⚡⚡⚡ Fast | ✓ Good (paraphrase) |

**Recommendation for Step-5/6 demo: Use `all-MiniLM-L6-v2` (no API key, fast)**

---

## Common Tasks

### Task 1: Detect All Sections

```python
from app.services.section_detector import SectionDetector

detector = SectionDetector()
sections = detector.detect_sections(tender_text)

for section in sections:
    print(f"{section['header']} ({section['section_type'].value})")
    print(f"  Confidence: {section['confidence']:.0%}")
```

### Task 2: Chunk and Analyze

```python
from app.services.chunker import TextChunker

chunker = TextChunker()
chunks = chunker.chunk_text(text, section_type, page)

# Get stats
stats = chunker.get_chunking_statistics(chunks)
print(f"Chunks: {stats['total_chunks']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Avg chunk: {stats['avg_chunk_tokens']:.0f} tokens")
```

### Task 3: Create Searchable Index

```python
from app.services.tender_processing_pipeline import TenderProcessingPipeline

pipeline = TenderProcessingPipeline(
    embedding_provider="sentence-transformers"
)

result = pipeline.process_file("tender.pdf", "tender_001")

# Now searchable
results = pipeline.query_tender("tender_001", "deadline")
```

### Task 4: Find Specific Section Type

```python
# Get all chunks of type
eligibility_chunks = pipeline.get_section_content(
    "tender_001",
    "eligibility"
)

# Or search within type
results = pipeline.query_tender(
    "tender_001",
    query="What certifications?",
    section_type="eligibility",
    k=3
)
```

### Task 5: Compare Multiple Tenders

```python
# Process multiple tenders
tenders = ["rfp1.pdf", "rfp2.pdf", "rfp3.pdf"]
pipeline = TenderProcessingPipeline()

for tender_file in tenders:
    tender_id = tender_file.replace(".pdf", "")
    pipeline.process_file(tender_file, tender_id)

# Search across them
for tender_id in ["rfp1", "rfp2", "rfp3"]:
    results = pipeline.query_tender(
        tender_id,
        query="implementation deadline"
    )
    print(f"{tender_id}: {len(results)} results")
```

---

## Database Integration

### New Models

**TenderChunk** - Stores chunked content
```python
chunk = TenderChunk(
    tender_id=uuid,
    chunk_index=0,
    text="...",
    token_count=950,
    character_count=3800,
    section_type="eligibility",
    page_number=1,
    section_header="ELIGIBILITY REQUIREMENTS",
    confidence=0.85
)
```

**TenderEmbedding** - Stores embeddings
```python
embedding = TenderEmbedding(
    chunk_id=chunk.id,
    tender_id=tender.id,
    embedding_vector=[...],  # JSON array
    embedding_model="all-MiniLM-L6-v2",
    model_dimension=384
)
```

**FAISSIndex** - Metadata for FAISS indices
```python
index = FAISSIndex(
    tender_id=tender.id,
    index_path="faiss_indices/tender_001.index",
    embedding_model="all-MiniLM-L6-v2",
    model_dimension=384,
    total_chunks=50
)
```

---

## Performance Tips

### 1. Use Local Embeddings for Development
```python
# Fast, no API key, good quality for demo
pipeline = TenderProcessingPipeline(
    embedding_provider="sentence-transformers",
    embedding_model="all-MiniLM-L6-v2"
)
```

### 2. Batch Process Multiple Tenders
```python
# One pipeline for multiple files
pipeline = TenderProcessingPipeline()

for file in ["tender1.pdf", "tender2.pdf"]:
    result = pipeline.process_file(file, file.replace(".pdf", ""))
```

### 3. Use Section Filters for Precision
```python
# Search only in specific sections
results = pipeline.query_tender(
    "tender_001",
    "Can we extend deadline?",
    section_type="deadlines"  # Only deadlines
)
```

### 4. Increase Chunk Overlap for Context
```python
chunker = TextChunker(
    overlap_tokens=200  # Increase for more context
)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OpenAI key not found | Use `sentence-transformers` provider instead |
| FAISS import error | `pip install faiss-cpu` |
| Chunks too large | Decrease `max_chunk_size` parameter |
| Chunks too small | Increase `min_chunk_size` parameter |
| Poor section detection | Use custom LLM classifier for refinement |
| Out of memory | Process file in streaming mode (Step-4) |

---

## Demo

Run interactive demo:

```bash
python step56_demo.py
```

Includes:
1. Section detection
2. Text chunking
3. Embedding generation
4. FAISS indexing
5. Complete pipeline
6. Token counting comparison

---

## Next Steps

After Step-5 & Step-6, proceed to **Step-7: AI Extraction**

Use processed chunks for:
- Eligibility requirement extraction
- Company fit analysis
- Risk assessment
- Bid scoring

---

## Files Reference

| File | Purpose |
|------|---------|
| `section_detector.py` | Section detection (8+ types) |
| `chunker.py` | Text chunking (800-1200 tokens) |
| `embeddings_pipeline.py` | Embedding generation |
| `faiss_manager.py` | FAISS index management |
| `tender_processing_pipeline.py` | Full integration |
| `step56_demo.py` | Interactive demo |
| `STEP_5_6_DOCUMENTATION.md` | Full documentation |

---

## API Summary

```python
# Section Detection
sections = SectionDetector.detect_sections(text)
section_type, conf = SectionDetector._classify_section(header, content)

# Chunking
chunks = TextChunker.chunk_text(text, section_type, page)
chunks = TextChunker.chunk_section(header, content, section_type, page)

# Embeddings
embeddings = pipeline.embed_texts(texts)
query_emb = pipeline.embed_query("question")
similarity = pipeline.compute_similarity(query_emb, chunk_embeddings)

# FAISS
manager.create_index(tender_id, dimension)
manager.add_embeddings(tender_id, embeddings, metadata)
results = manager.search(tender_id, query_emb, k=5)
results = manager.search_eligibility(tender_id, query_emb, k=5)

# Integration
pipeline.process_file(file_path, tender_id)
results = pipeline.query_tender(tender_id, query, k=5, section_type="...")
chunks = pipeline.get_section_content(tender_id, section_type)
```

---

**Status:** ✅ Step-5 & Step-6 Complete

Next: Step-7 AI Extraction & Bid Analysis
