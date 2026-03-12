# Tender-AI Project Guide

## Overview
Tender-AI (TenderIQ) is an AI-assisted tender and RFP evaluation platform for SMEs. It helps teams decide quickly whether to bid by processing large tender documents and presenting structured outputs such as eligibility, risk, and effort indicators.

## Business Scope
- Reduce manual tender review time from days to minutes.
- Improve bid/no-bid decision quality.
- Provide transparent, auditable analysis outputs.
- Support multi-language user experience for broader accessibility.

## Current Product Scope
### Included
- User authentication (JWT).
- Company profile management.
- Tender upload (PDF/DOCX currently active in backend validation).
- Background processing via Celery task.
- Document parsing and section extraction pipeline.
- Tender status polling and processing states.
- Dashboard and evaluation pages in Angular frontend.
- Localization support (EN/AR/ES content present; RTL support integrated for Arabic).

### Current Runtime Behavior
The active upload processing path is currently parser-first:
1. Upload tender file.
2. Parse document text and split into sections.
3. Persist tender sections.
4. Mark tender processing status progression in backend.

AI extraction/scoring modules exist in the codebase but are not fully wired as the mandatory runtime path for every upload in the current flow.

## Technical Stack
### Backend
- FastAPI (Python)
- SQLAlchemy + Alembic
- Celery workers
- SQLite/PostgreSQL-compatible schema
- Parser libraries: `pdfplumber`, `python-docx`
- Optional AI pipeline services (LLM client, analyzers, scoring modules)

### Frontend
- Angular + TypeScript
- Angular Material
- RxJS polling + upload progress flow
- `ngx-translate` localization

### Data & Processing
- Relational DB tables for users, company profiles, tenders, sections, evaluations.
- Async task execution for long-running document processing.
- Status endpoint used by frontend polling to drive UI state.

## Key User Flow
1. Login.
2. Create/update company profile.
3. Upload tender document.
4. Track processing status from upload page.
5. View evaluation/dashboard outputs.

## Known Constraints and Notes
- Local dev often uses alternate ports; backend CORS has localhost wildcard support in code.
- Large uploads are supported in frontend validation and backend settings; practical throughput depends on machine and worker performance.
- AI model keys are only needed when LLM-dependent pipeline stages are actively used.

## Roadmap Direction
- Fully wire AI extraction and scoring into the primary upload pipeline.
- Expand OCR for scanned PDFs.
- Improve production deployment with managed DB/storage and robust observability.
- Add richer evaluation explainability and downloadable executive summaries.
