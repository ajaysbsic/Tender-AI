# Tender-AI
AI-powered Tender/RFP Analyzer for SMEs that extracts eligibility, requirements, risks, deadlines, and effort scores from documents—helping teams quickly decide whether to bid.

## 📋 Project Roadmap Status

| Phase | Step | Component | Status |
|-------|------|-----------|--------|
| Foundation | 1-3 | Backend Core, Extraction | ✅ Complete |
| Intelligence | 4-6 | LLM Integration, Scoring | ✅ Complete |
| Frontend UI | 7-10 | Angular Dashboard, Components | ✅ Complete |
| **Integration** | **11** | **API + UX Progress Tracking** | **✅ Complete** |
| **Localization** | **12** | **i18n/RTL Support** | **✅ Complete** |

### Phase Summaries

- **Steps 1-3**: Backend parsing, extraction, and document processing pipeline
- **Steps 4-6**: LLM integration with Claude/GPT, prompt templates, scoring engine
- **Steps 7-10**: Angular frontend with dashboard, upload, evaluations, profile management
- **Step 11** ✅: Full API integration with progress tracking and real-time UX
- **Step 12** ✅: Multi-language support (English/Arabic) with RTL layout

---

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