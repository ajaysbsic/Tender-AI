# Step-5 & Step-6 Installation & Setup Guide

## Prerequisites

- Python 3.11+
- Virtual environment (already set up from earlier steps)
- Backend directory structure from Step-3 & Step-4

---

## Step 1: Install Dependencies

### Option A: Full Installation (Recommended)

```bash
cd backend

# Activate virtual environment
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install all requirements (includes Step-5/6 packages)
pip install -r requirements.txt

# Verify installations
python -c "import faiss, tiktoken, sentence_transformers; print('✓ All packages installed')"
```

### Option B: Minimal Installation (Local embeddings only, no API)

If you don't have OpenAI API key and don't want to install tiktoken:

```bash
pip install faiss-cpu==1.7.4
pip install sentence-transformers==2.2.2
pip install nltk==3.8.1
pip install scikit-learn==1.3.2
```

### Option C: Development Installation

For active development with latest pre-releases:

```bash
pip install --upgrade \
  faiss-cpu \
  sentence-transformers \
  openai \
  tiktoken \
  nltk
```

---

## Step 2: Verify Installation

```bash
# Check each package
python -c "import faiss; print(f'✓ FAISS {faiss.__version__}')"
python -c "import tiktoken; print(f'✓ Tiktoken {tiktoken.__version__}')"
python -c "from sentence_transformers import SentenceTransformer; print('✓ SentenceTransformers')"
python -c "import nltk; print('✓ NLTK')"

# Download NLTK data (one-time)
python -m nltk.downloader punkt
```

---

## Step 3: Setup Environment Variables

### For OpenAI Embeddings (Optional)

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# Windows CMD
set OPENAI_API_KEY=sk-...

# macOS/Linux
export OPENAI_API_KEY="sk-..."

# Verify
python -c "import os; print(os.getenv('OPENAI_API_KEY', 'NOT SET')[:10])"
```

### For CUDA GPU Support (Optional)

If you have NVIDIA GPU:

```bash
# Replace faiss-cpu with faiss-gpu
pip uninstall faiss-cpu
pip install faiss-gpu

# Verify GPU support
python -c "import faiss; print(f'GPU support: {faiss.get_num_gpus()}')"
```

---

## Step 4: Run Verification Script

Create `verify_setup.py`:

```python
#!/usr/bin/env python
"""Verify Step-5 & Step-6 installation."""

import sys
import os

print("\n" + "="*60)
print("Step-5 & Step-6 Installation Verification")
print("="*60 + "\n")

checks = []

# Check 1: Python version
try:
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"✓ Python {version.major}.{version.minor}")
        checks.append(True)
    else:
        print(f"✗ Python {version.major}.{version.minor} (need 3.11+)")
        checks.append(False)
except Exception as e:
    print(f"✗ Python check failed: {e}")
    checks.append(False)

# Check 2: FAISS
try:
    import faiss
    print(f"✓ FAISS {faiss.__version__}")
    checks.append(True)
except ImportError:
    print("✗ FAISS not installed")
    checks.append(False)

# Check 3: SentenceTransformers
try:
    from sentence_transformers import SentenceTransformer
    print("✓ SentenceTransformers")
    checks.append(True)
except ImportError:
    print("✗ SentenceTransformers not installed")
    checks.append(False)

# Check 4: OpenAI (optional)
try:
    import openai
    has_key = bool(os.getenv('OPENAI_API_KEY'))
    status = "✓ OpenAI (API key set)" if has_key else "⚠ OpenAI (no API key)"
    print(status)
    checks.append(True)
except ImportError:
    print("⚠ OpenAI not installed (optional)")
    checks.append(True)

# Check 5: Tiktoken (optional)
try:
    import tiktoken
    print("✓ Tiktoken")
    checks.append(True)
except ImportError:
    print("⚠ Tiktoken not installed (optional, using fallback)")
    checks.append(True)

# Check 6: NLTK data
try:
    import nltk
    nltk.data.find('tokenizers/punkt')
    print("✓ NLTK punkt tokenizer")
    checks.append(True)
except LookupError:
    print("⚠ NLTK punkt not downloaded (downloading...)")
    import nltk
    nltk.download('punkt', quiet=True)
    checks.append(True)
except Exception as e:
    print(f"✗ NLTK check failed: {e}")
    checks.append(False)

# Check 7: Core modules
try:
    from app.services.section_detector import SectionDetector
    from app.services.chunker import TextChunker
    from app.services.embeddings_pipeline import EmbeddingPipeline
    from app.services.faiss_manager import FAISSIndexManager
    from app.services.tender_processing_pipeline import TenderProcessingPipeline
    print("✓ All core modules imported")
    checks.append(True)
except ImportError as e:
    print(f"✗ Core modules import failed: {e}")
    checks.append(False)

# Summary
print("\n" + "-"*60)
passed = sum(checks)
total = len(checks)
print(f"Checks passed: {passed}/{total}")

if passed == total:
    print("\n✅ Installation verified successfully!")
    print("\nYou can now run:")
    print("  python step56_demo.py")
    sys.exit(0)
else:
    print("\n⚠️  Some checks failed. Please review above.")
    sys.exit(1)
```

Run it:

```bash
python verify_setup.py
```

---

## Step 5: Download Embedding Models (First Time)

When you use SentenceTransformers, models are auto-downloaded:

```python
from sentence_transformers import SentenceTransformer

# First run: Downloads ~50MB model (one-time)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Subsequent runs: Uses cached model
embeddings = model.encode(["text1", "text2"])
```

To pre-download models:

```bash
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('✓ Model downloaded')
"
```

---

## Step 6: Configure FAISS Index Directory

Default location: `faiss_indices/`

To use custom location:

```python
from app.services.faiss_manager import FAISSIndexManager

manager = FAISSIndexManager(index_dir="/path/to/faiss_indices")
```

Or via environment variable:

```bash
# Windows
set FAISS_INDEX_DIR=D:\Tender-AI\faiss_indices

# macOS/Linux
export FAISS_INDEX_DIR=/path/to/faiss_indices
```

---

## Step 7: Test Installation

### Quick Test

```python
from app.services.section_detector import SectionDetector
from app.services.chunker import TextChunker

# Test section detection
text = "1. ELIGIBILITY REQUIREMENTS\n\nCompany must be ISO certified."
sections = SectionDetector.detect_sections(text)
print(f"✓ Detected {len(sections)} sections")

# Test chunking
chunker = TextChunker()
chunks = chunker.chunk_text(text)
print(f"✓ Created {len(chunks)} chunks")
```

### Full Test

```bash
# Run interactive demo
python step56_demo.py

# Select option 7 to run all demos
```

---

## Step 8: Database Setup (Optional)

If using with database backend:

```bash
cd backend

# Create migration for new tables
alembic revision --autogenerate -m "Add Step-5/6 models"

# Apply migration
alembic upgrade head
```

New tables created:
- `tender_chunks` - Chunked content
- `tender_embeddings` - Embeddings
- `faiss_indices` - FAISS metadata

---

## Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'faiss'"

**Solution:**
```bash
pip install faiss-cpu
# or for GPU
pip install faiss-gpu
```

### Issue 2: "Failed to import SentenceTransformer"

**Solution:**
```bash
pip install sentence-transformers
```

### Issue 3: "OPENAI_API_KEY not provided"

**Solution:**
```bash
# Option 1: Set environment variable
export OPENAI_API_KEY="sk-..."

# Option 2: Use local embeddings
pipeline = TenderProcessingPipeline(
    embedding_provider="sentence-transformers"
)
```

### Issue 4: "NLTK punkt not found"

**Solution:**
```bash
python -m nltk.downloader punkt
```

### Issue 5: "FAISS initialization failed on GPU"

**Solution:**
```bash
# Fall back to CPU
pip uninstall faiss-gpu
pip install faiss-cpu
```

### Issue 6: Out of memory when processing large file

**Solution:**
Use Step-4 streaming approach:
```python
from app.services.parser import DocumentParser

for page in DocumentParser.stream_pdf_pages("large.pdf"):
    # Process one page at a time
    chunks = chunker.chunk_text(page['text'])
```

---

## Performance Tuning

### For Development (Fast)

```bash
# Use minimal packages
pip install faiss-cpu sentence-transformers nltk

# Use fast embedding model
model = "all-MiniLM-L6-v2"  # 384 dims
```

### For Production (Accurate)

```bash
# Full installation with GPU support
pip install faiss-gpu openai tiktoken sentence-transformers

# Use better embedding model
model = "text-embedding-3-small"  # OpenAI, 1536 dims
```

### For Large-Scale (Optimized)

```bash
# With HNSW for faster search
from app.services.faiss_manager import FAISSIndexManager

manager = FAISSIndexManager()
manager.create_index(
    tender_id="large_tender",
    dimension=1536,
    index_type="hnsw"  # Hierarchical navigable small world
)
```

---

## Running the Demo

### Interactive Mode

```bash
python step56_demo.py

# Select option to run:
# 1. Section Detection
# 2. Text Chunking
# 3. Embeddings (Local)
# 4. FAISS Indexing
# 5. Complete Pipeline
# 6. Token Counting
# 7. Run all demos
```

### Programmatic Mode

```python
from step56_demo import (
    demo_section_detection,
    demo_text_chunking,
    demo_embeddings_local,
    demo_faiss_indexing,
    demo_complete_pipeline
)

demo_section_detection()
demo_text_chunking()
demo_embeddings_local()
demo_faiss_indexing()
demo_complete_pipeline()
```

---

## Docker Setup (Optional)

If using Docker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt

# Pre-download embedding model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY backend/ .

CMD ["python", "app/main.py"]
```

Build and run:

```bash
docker build -t tender-ai .
docker run -e OPENAI_API_KEY="sk-..." tender-ai
```

---

## Next Steps After Installation

1. **Verify Setup**
   ```bash
   python verify_setup.py
   ```

2. **Run Demo**
   ```bash
   python step56_demo.py
   ```

3. **Integrate with Backend**
   - Update `process_tender_task` in `workers/tasks.py`
   - Add database migrations
   - Configure API endpoints

4. **Move to Step-7**
   - AI extraction using chunks
   - LLM-based analysis
   - Bid scoring

---

## Support

### Documentation Files

- `STEP_5_6_DOCUMENTATION.md` - Full API reference
- `STEP_5_6_QUICK_REFERENCE.md` - Quick lookup
- `STEP_5_6_IMPLEMENTATION_SUMMARY.md` - Overview

### Getting Help

1. Check documentation files
2. Review module docstrings: `python -c "from app.services.chunker import TextChunker; help(TextChunker)"`
3. Run demo: `python step56_demo.py`
4. Check logs: Set `logging.basicConfig(level=logging.DEBUG)`

---

## Version Info

- **Release Date:** January 22, 2026
- **Python:** 3.11+
- **FAISS:** 1.7.4+
- **SentenceTransformers:** 2.2.2+
- **OpenAI:** 1.3.5+ (optional)
- **Status:** ✅ Production Ready

---

## Maintenance

### Update Packages

```bash
pip install --upgrade \
  faiss-cpu \
  sentence-transformers \
  openai \
  tiktoken \
  nltk
```

### Clear Cache

```python
# Clear embedding cache
pipeline.embedding_pipeline.clear_cache()

# Clear FAISS indices
from pathlib import Path
import shutil
shutil.rmtree("faiss_indices")
```

### Monitor Performance

```bash
# Monitor FAISS index size
ls -lh faiss_indices/

# Monitor memory usage
python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024**2:.1f}MB')
"
```

---

## Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] NLTK punkt downloaded
- [ ] FAISS verified (`python -c "import faiss"`)
- [ ] Core modules imported successfully
- [ ] Demo runs without errors (`python step56_demo.py`)
- [ ] (Optional) OpenAI API key set for `text-embedding-3-small`
- [ ] (Optional) CUDA GPU setup if using faiss-gpu
- [ ] Database migrations applied (if needed)

---

**Status:** ✅ Installation Guide Complete

Ready to proceed with Step-5 & Step-6 implementation!
