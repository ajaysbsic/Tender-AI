# TenderIQ – Document Intelligence Deep Dive

This document is a **technical deep-dive** covering the three most critical systems of TenderIQ:

1. PDF Parsing & Chunking (real-world tenders)
2. FAISS Embeddings & Query Design
3. Scoring Engine (real Python code)

This is implementation-focused and assumes **Python + FastAPI backend**.

---

## 1️⃣ PDF PARSING + CHUNKING STRATEGY (REAL PDFs)

### 1.1 Reality of Tender PDFs

Real tender documents are:

* 50–300 pages
* Mixed text + tables
* Inconsistent headings
* Often poorly formatted

❌ Do NOT chunk by page
❌ Do NOT chunk by fixed token size only

We chunk **semantically + structurally**.

---

### 1.2 Parsing Strategy

**Libraries**

* `pdfplumber` (primary)
* `python-docx` (DOCX)

**Extraction Rules**

* Extract text page-by-page
* Preserve headings where possible
* Ignore headers/footers

```python
import pdfplumber

def extract_pages(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append({
                "page": i + 1,
                "text": text.strip()
            })
    return pages
```

---

### 1.3 Section-Aware Chunking

We detect **section boundaries** before chunking.

**Common Section Signals**

* ALL CAPS headings
* Numbered headings (1., 1.1, 2.3)
* Keywords: ELIGIBILITY, SCOPE, TERMS, PENALTY

```python
import re

SECTION_PATTERN = re.compile(r"^(\d+\.?\d*|[A-Z ]{5,})")

def split_by_sections(pages):
    sections = {}
    current_section = "GENERAL"

    for page in pages:
        for line in page['text'].split('\n'):
            if SECTION_PATTERN.match(line.strip()):
                current_section = line.strip()[:100]
                sections[current_section] = []
            sections.setdefault(current_section, []).append(line)

    return {k: '\n'.join(v) for k, v in sections.items()}
```

---

### 1.4 Token-Safe Chunking

After section split, chunk safely for LLMs.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=150
)

def chunk_section(text):
    return splitter.split_text(text)
```

---

## 2️⃣ FAISS EMBEDDINGS + QUERY DESIGN

### 2.1 Why FAISS (and not DB search)

* Semantic similarity
* Clause-level retrieval
* Fast local search

---

### 2.2 Embedding Strategy

* One embedding per **chunk**
* Metadata stored alongside:

  * section_name
  * page_range

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

embeddings = OpenAIEmbeddings()

vector_store = FAISS.from_texts(
    texts=chunks,
    embedding=embeddings,
    metadatas=metadata
)
```

---

### 2.3 Query Design (IMPORTANT)

❌ Bad Query:

> "What is the eligibility?"

✅ Good Queries (examples):

* "minimum turnover eligibility requirement"
* "mandatory certifications required"
* "reasons for bid disqualification"

---

### 2.4 Retrieval Example

```python
retriever = vector_store.as_retriever(search_kwargs={"k": 6})

results = retriever.get_relevant_documents(
    "eligibility criteria for bidder"
)

context = "\n".join([r.page_content for r in results])
```

This `context` is passed into **pipeline prompts**, not the whole document.

---

## 3️⃣ SCORING ENGINE (REAL PYTHON)

This engine is **deterministic first**, AI second.

---

### 3.1 Eligibility Scoring

```python
ELIGIBILITY_POINTS = 10

VERDICT_THRESHOLDS = {
    "eligible": 0.8,
    "partial": 0.5
}


def calculate_eligibility(clauses):
    total = len(clauses) * ELIGIBILITY_POINTS
    scored = 0

    for c in clauses:
        if c['status'] == 'eligible':
            scored += ELIGIBILITY_POINTS
        elif c['status'] == 'partially_eligible':
            scored += ELIGIBILITY_POINTS / 2

    ratio = scored / total if total else 0

    if ratio >= VERDICT_THRESHOLDS['eligible']:
        verdict = 'eligible'
    elif ratio >= VERDICT_THRESHOLDS['partial']:
        verdict = 'partially_eligible'
    else:
        verdict = 'not_eligible'

    return verdict, round(ratio * 100)
```

---

### 3.2 Risk Scoring

```python
RISK_RULES = {
    'penalty_clause': 2,
    'short_deadline': 2,
    'high_emd': 2,
    'complex_scope': 1
}


def calculate_risk(flags):
    score = sum(RISK_RULES.get(f, 0) for f in flags)

    if score <= 2:
        level = 'low'
    elif score <= 5:
        level = 'medium'
    else:
        level = 'high'

    return score, level
```

---

### 3.3 Effort Scoring

```python
EFFORT_RULES = {
    'many_documents': 2,
    'multi_location': 2,
    'high_experience_required': 1,
    'high_turnover_required': 1
}


def calculate_effort(flags):
    score = sum(EFFORT_RULES.get(f, 0) for f in flags)

    if score <= 2:
        level = 'low'
    elif score <= 4:
        level = 'medium'
    else:
        level = 'high'

    return score, level
```

---

## 4️⃣ How These Three Work Together

1. PDF parsed → section-aware chunks
2. Chunks embedded & indexed in FAISS
3. Targeted semantic queries retrieve clauses
4. AI evaluates clause status
5. Scoring engine computes verdicts
6. Results returned to frontend

---

## 5️⃣ Final Engineering Advice (Read This)

* Build **eligibility-only flow first**
* Ignore OCR until customer asks
* Store everything (for explainability)
* Deterministic rules earn trust

This document completes the **core intelligence layer** of TenderIQ.