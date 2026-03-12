# TenderIQ – MASTER SPECIFICATION (FOR COPILOT AGENT)

**Purpose of this document**
This is a **single, complete, unambiguous specification** that can be given to a Copilot / AI coding agent to generate the **entire TenderIQ system end-to-end**.

The agent should be able to:

* Generate backend (Python FastAPI)
* Generate AI services (LLM + embeddings)
* Generate database schema & migrations
* Generate Angular frontend (modern UI)
* Handle very large PDFs (1000+ pages)
* Keep system open for **multi-language PDFs and UI localization**

This document replaces all previous fragmented docs.

---

## 1️⃣ PRODUCT OVERVIEW

### Product Name

**TenderIQ**

### Problem

Companies waste days manually reading large tenders/RFPs and still don’t know:

* Are we eligible?
* What documents are missing?
* How risky or effort-heavy is this bid?

### Solution

AI-powered tender intelligence that:

* Ingests large tenders (PDF/DOCX, 1000+ pages)
* Extracts structured clauses
* Compares against company profile
* Gives **clear verdict + risk + effort score**

### Target Users

* Contractors
* EPC companies
* Tender consultants
* SMEs bidding on government tenders

---

## 2️⃣ HIGH-LEVEL ARCHITECTURE

### System Components

```
Angular Frontend (Web)
        ↓ REST API
FastAPI Backend (Python)
        ↓ Async Tasks
AI Processing Service
        ↓
PostgreSQL + FAISS
```

### Core Principles

* AI is **pipeline-based**, not summarization
* Scoring is **deterministic + explainable**
* UI is **business-first**, not technical
* System is **solo-founder friendly**

---

## 3️⃣ PROJECT STRUCTURE (FOR COPILOT)

### Root Repository Layout

```
tenderiq/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── ai/
│   │   ├── workers/
│   │   └── utils/
│   ├── migrations/
│   └── requirements.txt
│
├── frontend/
│   ├── src/app/
│   │   ├── core/
│   │   ├── pages/
│   │   ├── shared/
│   │   └── assets/i18n/
│   └── angular.json
│
├── ai-assets/
│   ├── prompts/
│   └── scoring/
│
└── README.md
```

Copilot should generate **all projects**.

---

## 4️⃣ BACKEND – FASTAPI (AUTHORITATIVE)

### Responsibilities

* Auth (basic JWT)
* Tender upload
* Job orchestration
* Result APIs
* Report generation

### Key Endpoints

```
POST   /auth/login
POST   /company-profile
POST   /tender/upload
GET    /tender/{id}/status
GET    /tender/{id}/evaluation
GET    /tender/{id}/report
```

### Async Processing

* Use **Celery or BackgroundTasks**
* Never block API thread

---

## 5️⃣ DATABASE (POSTGRESQL)

### Core Tables

**users**

* id (uuid)
* email
* password_hash

**company_profiles**

* id
* industry
* turnover
* certifications (json)
* experience_years

**tenders**

* id
* file_path
* language_detected
* status (uploaded, processing, completed, failed)

**sections**

* id
* tender_id
* section_type
* content

**clauses**

* id
* section_id
* text

**evaluations**

* tender_id
* eligibility_verdict
* effort_score
* risk_score

**clause_evaluations**

* clause_id
* verdict
* reason

Migrations must be included.

---

## 6️⃣ DOCUMENT INGESTION (CRITICAL)

### Supported Files

* PDF (1000+ pages)
* DOCX

### Strategy (MANDATORY)

1. Stream-based reading (no full memory load)
2. Page-by-page extraction
3. Header/footer removal
4. Language detection per page
5. Section detection using regex + LLM
6. Chunk size: 800–1200 tokens

### Libraries

* pdfplumber
* python-docx
* langdetect

OCR is optional (future).

---

## 7️⃣ EMBEDDINGS & VECTOR SEARCH

### Vector Store

* FAISS (local)

### Embedding Strategy

* One embedding per chunk
* Store chunk metadata (section, page)

### Query Types

* Eligibility requirements
* Submission deadlines
* Penalties

Copilot must generate FAISS indexing + querying code.

---

## 8️⃣ AI PIPELINE (NON-NEGOTIABLE)

❌ DO NOT use generic summarization

### Pipeline Stages

1. Section Detection
2. Clause Extraction
3. Eligibility Reasoning
4. Scoring Explanation

### LLM Options

* GPT-4 / Claude / Mixtral (configurable)

### Prompt Rules

* Output MUST be structured JSON
* Clause-level reasoning required

---

## 9️⃣ SCORING ENGINE (RULE-BASED)

### Eligibility Verdict

* ✔ Eligible
* ❌ Not Eligible
* ⚠ Partially Eligible

Based on % of mandatory clauses satisfied.

### Risk Score

* Missing documents
* Penalties
* Financial exposure

### Effort Score

* Number of documents
* Experience mismatch
* Bid complexity

Scores must be deterministic.

---

## 🔟 FRONTEND – ANGULAR (MODERN)

### UI Requirements

* Clean, modern, enterprise look
* Responsive
* Dark/light mode ready
* Component-based design

### Pages

* Login
* Company Profile
* Tender Upload
* Processing Screen
* Evaluation Dashboard

### UI Framework

* Angular + Material OR Tailwind

### Localization (MANDATORY)

* ngx-translate
* All strings externalized
* Future-ready for RTL

---

## 1️⃣1️⃣ END-TO-END FLOW

1. User logs in
2. Creates company profile
3. Uploads tender
4. System processes async
5. User sees verdict dashboard
6. User downloads report

No optional paths.

---

## 1️⃣2️⃣ NON-FUNCTIONAL REQUIREMENTS

* Handle large PDFs without crashing
* Graceful failures
* Progress status visible
* Logs for AI steps

---

## 1️⃣3️⃣ WHAT COPILOT MUST GENERATE

Copilot should:

* Generate all backend code
* Generate AI pipelines
* Generate Angular UI
* Generate DB migrations
* Generate README with run instructions

---

## FINAL INSTRUCTION TO COPILOT

> Build TenderIQ exactly as specified above.
> Do not simplify AI logic.
> Do not replace pipelines with summaries.
> Assume this is a production MVP.

---

**END OF MASTER SPECIFICATION**