# TenderIQ Backend

FastAPI-based backend for the TenderIQ tender/RFP analyzer.

## Quick Start

### 1. Python Version

Use **Python 3.11** (recommended). Psycopg2 wheels for PostgreSQL are not available on 3.14 yet.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
# If you need PostgreSQL on Python 3.11, also install:
# pip install psycopg2-binary==2.9.9
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup

```bash
# Run migrations
alembic upgrade head
```

### 4. Start Services

#### API Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Celery Worker (async processing)
```bash
celery -A app.workers.tasks worker --loglevel=info
```

#### Redis (message broker)
```bash
# Install and start Redis locally or use Docker
docker run -p 6379:6379 redis:latest
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Company Profile
- `POST /company/profile` - Create company profile
- `GET /company/profile` - Get company profile
- `PUT /company/profile` - Update company profile

### Tender Management
- `POST /tender/upload` - Upload tender document
- `GET /tender/{tender_id}/status` - Get processing status
- `GET /tender/{tender_id}/evaluation` - Get evaluation results

### Health
- `GET /health` - Health check
- `GET /` - Root endpoint with API info

## Architecture

### Components

**FastAPI Main App** (`app/main.py`)
- REST API with CORS support
- Database session management
- Route registration

**Database** (`app/core/database.py`)
- SQLAlchemy ORM
- PostgreSQL/SQLite support
- Session factory

**Models** (`app/models/`)
- `tables.py` - SQLAlchemy database models
- `schemas.py` - Pydantic request/response schemas

**Services** (`app/services/`)
- `parser.py` - Document parsing (PDF/DOCX)
- `embeddings.py` - FAISS vector indexing
- `ai_extractor.py` - LLM-based extraction pipeline
- `scoring.py` - Deterministic scoring engine

**API Routes** (`app/api/`)
- `auth.py` - Authentication endpoints
- `company.py` - Company profile endpoints
- `tender.py` - Tender upload & evaluation endpoints

**Workers** (`app/workers/`)
- `tasks.py` - Celery async tasks for tender processing

## Processing Pipeline

**Current State (Phase 1):**
1. **Document Ingestion** ✅ - Parse PDF/DOCX
2. **Section Detection** ✅ - Identify tender sections
3. **Storage** ✅ - Persist sections to database

**TODO (Phase 2 - AI Logic):**
4. Clause Extraction - Extract requirements using LLM
5. Eligibility Evaluation - Compare against company profile
6. Scoring - Rule-based effort/risk scoring
7. Result Storage - Persist evaluation results

### AI Logic Implementation

The following services have stub implementations ready for AI logic:
- `app/services/ai_extractor.py` - 4-stage LLM pipeline (TODO)
- `app/services/embeddings.py` - Vector embeddings & FAISS (TODO)
- `app/services/scoring.py` - Rule-based scoring (implemented)

## Configuration

See `.env.example` for all available options.

### Key Settings

- `DATABASE_URL` - Database connection string
- `OPENAI_API_KEY` - OpenAI API key for LLM
- `CELERY_BROKER_URL` - Redis connection for task queue
- `LLM_MODEL` - Model to use (gpt-4, gpt-3.5-turbo, claude-3, etc.)

## Database Schema

### Core Tables
- `users` - User accounts
- `company_profiles` - Company information
- `tenders` - Uploaded tender documents
- `tender_sections` - Extracted sections
- `clauses` - Individual requirements
- `evaluations` - Tender analysis results
- `clause_evaluations` - Clause-by-clause analysis

See `alembic/versions/001_initial_schema.py` for full schema.

## Development

### Running Tests (TBD)
```bash
pytest
```

### Creating New Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Debugging

Enable debug logging in `.env`:
```
DEBUG=True
```

Check logs for processing errors:
```bash
# API logs
# Celery logs (separate terminal)
```

## Production Deployment

1. Use PostgreSQL instead of SQLite
2. Set `DEBUG=False`
3. Configure proper `SECRET_KEY`
4. Use environment-specific `.env` file
5. Deploy Celery worker as separate service
6. Use production WSGI server (Gunicorn)
7. Set up Redis for Celery broker

## Troubleshooting

**LLM API timeout:** Increase timeout in `ai_extractor.py`
**PDF parsing issues:** Check if pdfplumber supports your PDF format
**Celery not processing:** Verify Redis is running and accessible
**Database migrations fail:** Check `DATABASE_URL` and connection permissions

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
