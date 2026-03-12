# TenderIQ – AI Tender / RFP Evaluation SaaS

## 1. Product Overview

**TenderIQ** is an AI-powered SaaS that helps companies decide **within minutes** whether a Tender / RFP is worth bidding on.

**Core Value Proposition:**

> "Know in 5 minutes whether a tender is worth bidding. Avoid wasted effort and hidden risks."

This product targets **SMEs and mid-sized companies** (IT services, construction, EPC, infrastructure vendors) that evaluate multiple tenders regularly and lose time and money due to manual analysis.

---

## 2. Target Users

* Tender / Bid Managers
* Proposal Managers
* Business Development Teams
* SME Owners

---

## 3. MVP FEATURES (NON‑NEGOTIABLE)

### 3.1 Upload Tender / RFP

* Supported formats: **PDF, DOCX**
* File size: Up to **50–100 pages**
* Secure upload and storage

---

### 3.2 AI Extraction Engine

The system must extract and structure the following:

* **Eligibility criteria**
* **Mandatory documents**
* **Technical requirements**
* **Commercial requirements**
* **Deadlines & submission dates**
* **Penalties, risks & disqualifying clauses**

---

### 3.3 Eligibility Verdict

The system provides a clear verdict:

* ✔ **Eligible**
* ❌ **Not Eligible**
* ⚠ **Partially Eligible**

Each verdict includes:

* Clause-by-clause reasoning
* Highlighted missing or risky requirements

---

### 3.4 Effort & Risk Scoring

**Effort Score:**

* Low / Medium / High

**Risk Score:**

* Low / Medium / High

Scoring is generated using:

* Rule-based logic
* AI-generated explanations for transparency

---

### 3.5 Downloadable Summary

* Downloadable **PDF / DOC** report
* Management-ready format
* Includes verdict, scores, risks, and checklist

---

## 4. Technology Stack

### 4.1 Backend (Python)

* **FastAPI** – REST APIs
* **Celery / BackgroundTasks** – Async document processing
* **PostgreSQL** (production) / **SQLite** (local)

---

### 4.2 AI Stack

* LLM: **GPT‑4 / Claude / Mixtral (configurable)**
* **LangChain or LlamaIndex** – prompt pipelines
* **FAISS** – vector database for embeddings

---

### 4.3 Document Processing

* **pdfplumber** – PDF text extraction
* **python-docx** – DOCX parsing
* **OCR (optional later)** – for scanned documents

---

### 4.4 Frontend

* **Angular** (Admin UI)
* Flow: Upload → Processing → Results → Download
* Simple, functional UI (no heavy animations)

---

## 5. System Architecture & Flow

### 5.1 High-Level Flow

1. User uploads tender document
2. Backend parses and chunks content
3. Text embeddings stored in FAISS
4. AI pipeline processes content section-wise
5. Rule engine calculates eligibility, effort & risk
6. Final structured evaluation generated
7. Report displayed & downloadable

---

## 6. AI STRATEGY (CRITICAL DESIGN)

❌ **Do NOT use single-step summarization**

### 6.1 Pipeline Prompt Strategy

#### Step 1: Section Detection

* Identify tender sections:

  * Eligibility
  * Scope of Work
  * Technical Criteria
  * Commercial Terms
  * Submission Instructions
  * Penalties & Risks

#### Step 2: Clause Extraction

* Extract atomic clauses per section
* Normalize clauses into structured bullets

#### Step 3: Eligibility Reasoning

* Compare clauses against company profile
* Identify:

  * Missing certifications
  * Turnover mismatch
  * Experience gaps

#### Step 4: Scoring Logic

* Rule-based scoring (deterministic)
* AI-generated explanation (interpretive)

This hybrid approach ensures **reliability + explainability**.

---

## 7. Data Model (Simplified)

### 7.1 CompanyProfile

* Name
* Industry
* Annual Turnover
* Certifications
* Past Project Experience

### 7.2 Tender

* File metadata
* Extracted sections
* Key deadlines

### 7.3 Evaluation

* EligibilityResult
* RiskScore
* EffortScore
* MissingDocuments
* AIReasoning

---

## 8. Project Execution Plan (21 Days)

### Week 1 – Core Foundations

* File upload & validation
* Document parsing (PDF/DOCX)
* Chunking & embedding
* FAISS indexing

### Week 2 – Intelligence Layer

* Prompt pipelines
* Clause extraction
* Eligibility & scoring logic
* Angular UI (upload + results)

### Week 3 – Monetization & Launch

* PDF/DOC report generation
* Stripe payment integration
* Basic authentication
* Outreach & demos

---

## 9. Tech & Project Types Involved

* **AI / LLM Engineering**
* **Backend API Development (Python)**
* **Asynchronous Processing**
* **Document Intelligence**
* **Vector Search & Embeddings**
* **B2B SaaS Architecture**
* **Angular Frontend Development**

---

## 10. Common Failure Points (Avoid These)

* Generic tender summarization
* No deterministic scoring rules
* No clear eligibility verdict
* Over-engineering UI
* Targeting everyone instead of a niche

---

## 11. Final Notes

TenderIQ is **not a generic AI tool**. It is a **decision-making system** combining deterministic rules with AI reasoning.

Success depends on:

* Clear verdicts
* Trustworthy explanations
* Focused B2B targeting

This MVP is **solo-buildable**, scalable, and monetizable within weeks.

---

## 12. Detailed AI Prompt Templates (Production-Ready)

### 12.1 Section Detection Prompt

**System Prompt:**

> You are a senior bid manager who understands tender/RFP documents across industries.

**User Prompt:**

> Given the following tender text, identify and extract sections under these headings:
>
> * Eligibility Criteria
> * Scope of Work
> * Technical Requirements
> * Commercial Requirements
> * Submission Instructions
> * Penalties & Risks
>
> Return the output strictly in JSON with section names as keys and extracted text as values.

---

### 12.2 Clause Extraction Prompt

**System Prompt:**

> You are an expert compliance analyst.

**User Prompt:**

> From the following section text, extract individual atomic clauses.
>
> Rules:
>
> * Each clause must represent ONE requirement
> * Use simple language
> * Do not summarize
>
> Return JSON array of clauses.

---

### 12.3 Eligibility Reasoning Prompt

**System Prompt:**

> You are an AI compliance auditor.

**User Prompt:**

> Company Profile:
> {company_profile_json}
>
> Tender Eligibility Clauses:
> {eligibility_clauses_json}
>
> For each clause, determine:
>
> * status: Eligible / Not Eligible / Partially Eligible
> * reason: short, clear explanation
>
> Return structured JSON.

---

### 12.4 Risk & Effort Explanation Prompt

**System Prompt:**

> You are a senior risk analyst.

**User Prompt:**

> Given the extracted clauses, missing requirements, and deadlines, explain:
>
> * Overall Risk Level (Low/Medium/High)
> * Overall Effort Level (Low/Medium/High)
>
> Explain reasoning in 5–7 bullet points.

---

## 13. Scoring Logic (Deterministic + AI)

### 13.1 Eligibility Score

* Each mandatory eligibility clause = 10 points
* Fully matched clause = +10
* Partially matched clause = +5
* Missing clause = 0

**Verdict Rules:**

* ≥80% → Eligible
* 50–79% → Partially Eligible
* <50% → Not Eligible

---

### 13.2 Risk Score Rules

* Penalty clauses present → +2 risk each
* Short submission deadline (<7 days) → +2
* Heavy EMD / Bank Guarantee → +2
* Complex technical compliance → +1

**Risk Levels:**

* 0–2 → Low
* 3–5 → Medium
* > 5 → High

---

### 13.3 Effort Score Rules

* Document count >15 → +2
* Multi-location execution → +2
* Past experience >5 years required → +1
* High turnover requirement → +1

**Effort Levels:**

* 0–2 → Low
* 3–4 → Medium
* > 4 → High

---

## 14. Backend API Design (FastAPI)

### 14.1 Core APIs

* POST /auth/login
* POST /company-profile
* POST /tender/upload
* GET /tender/{id}/status
* GET /tender/{id}/evaluation
* GET /tender/{id}/report

---

### 14.2 Background Job Flow (Celery)

1. Upload triggers async job
2. Parse & chunk document
3. Generate embeddings & store in FAISS
4. Run AI prompt pipelines
5. Apply scoring rules
6. Store evaluation results
7. Notify frontend

---

## 15. Background Processing Architecture

* FastAPI handles request
* Celery worker handles heavy AI tasks
* Redis / RabbitMQ as broker
* Results persisted in DB

---

## 16. Angular Frontend Flow

### Pages

* Login
* Company Profile Setup
* Tender Upload
* Processing Status
* Evaluation Dashboard
* Report Download

### UI Principles

* Minimal UI
* Clear verdict badges
* Clause-level expandable details

---

## 17. Final Execution Notes

This system deliberately combines:

* Deterministic rules (trust)
* AI reasoning (speed & flexibility)

This is what differentiates TenderIQ from generic AI summarizers and makes it sellable to real businesses.

---

## 18. Database Schema (Production-Ready, Simple)

### 18.1 Core Tables

#### company_profiles

* id (UUID, PK)
* name (varchar)
* industry (varchar)
* annual_turnover (numeric)
* certifications (text[])
* past_experience_years (int)
* created_at (timestamp)

---

#### tenders

* id (UUID, PK)
* company_id (FK → company_profiles.id)
* original_filename (varchar)
* file_path (varchar)
* status (enum: uploaded, processing, completed, failed)
* uploaded_at (timestamp)

---

#### tender_sections

* id (UUID, PK)
* tender_id (FK)
* section_name (varchar)
* section_text (text)

---

#### evaluations

* id (UUID, PK)
* tender_id (FK)
* eligibility_verdict (enum: eligible, partially_eligible, not_eligible)
* eligibility_score (int)
* risk_score (int)
* risk_level (enum: low, medium, high)
* effort_score (int)
* effort_level (enum: low, medium, high)
* ai_summary (text)
* created_at (timestamp)

---

#### clause_evaluations

* id (UUID, PK)
* evaluation_id (FK)
* clause_text (text)
* status (enum: eligible, partially_eligible, not_eligible)
* reason (text)

---

### 18.2 Alembic Migration Example

```python
# alembic revision -m "create company_profiles"
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'company_profiles',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('industry', sa.String()),
        sa.Column('annual_turnover', sa.Numeric()),
        sa.Column('certifications', sa.ARRAY(sa.String())),
        sa.Column('past_experience_years', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('company_profiles')
```

---

## 19. First Working Prompt (Minimal, Reliable)

### Eligibility Clause Extraction Prompt

```text
System:
You are a senior tender compliance officer.

User:
Extract ONLY eligibility-related clauses from the text below.
Rules:
- One requirement per bullet
- Do not summarize
- Do not merge clauses

Tender Text:
{chunk_text}

Return JSON array of strings.
```

---

## 20. FastAPI Code Skeleton (Runnable MVP)

### 20.1 Project Structure

```
backend/
 ├── app/
 │   ├── main.py
 │   ├── api/
 │   │   ├── tender.py
 │   │   └── company.py
 │   ├── core/
 │   │   ├── config.py
 │   │   └── celery_app.py
 │   ├── services/
 │   │   ├── parser.py
 │   │   ├── embeddings.py
 │   │   ├── ai_pipeline.py
 │   │   └── scoring.py
 │   └── models/
 │       └── tables.py
 └── alembic/
```

---

### 20.2 main.py

```python
from fastapi import FastAPI
from app.api import tender, company

app = FastAPI(title="TenderIQ")

app.include_router(company.router, prefix="/company")
app.include_router(tender.router, prefix="/tender")
```

---

### 20.3 Tender Upload API

```python
from fastapi import APIRouter, UploadFile, BackgroundTasks
from app.services.parser import parse_document
from app.core.celery_app import process_tender

router = APIRouter()

@router.post("/upload")
def upload_tender(file: UploadFile, background_tasks: BackgroundTasks):
    tender_id = save_file(file)
    background_tasks.add_task(process_tender.delay, tender_id)
    return {"tender_id": tender_id, "status": "processing"}
```

---

### 20.4 Celery Task

```python
from app.services.ai_pipeline import run_pipeline
from app.services.scoring import calculate_scores

@app.task
def process_tender(tender_id):
    sections = run_pipeline(tender_id)
    scores = calculate_scores(sections)
    save_evaluation(tender_id, scores)
```

---

## 21. Execution Guidance (IMPORTANT)

Start with:

* PDF only (no OCR)
* Eligibility section only
* One company profile

Expand later.

This keeps scope under control and gets you to **first paying customer faster**.