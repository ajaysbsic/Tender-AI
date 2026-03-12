# Step-3: Tender Upload & Async Processing Pipeline

## Overview
The tender upload and async processing pipeline enables SMEs to:
1. Upload tender/RFP documents (PDF/DOCX)
2. Store them safely with proper metadata
3. Process them asynchronously in background
4. Poll processing status
5. Retrieve results when ready

## Architecture

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ POST /tender/upload (multipart)
       ▼
┌─────────────────────────┐
│  FastAPI Tender Router  │
│  - Validate file        │
│  - Save file securely   │
│  - Create DB record     │
│  - Queue async task     │
└──────┬──────────────────┘
       │
       ├─► Returns: tender_id + status
       │
       └─► BackgroundTasks / Celery
           │
           ▼
       ┌─────────────────┐
       │  process_tender │
       │      _task      │
       │  (Celery/BG)    │
       │                 │
       │  1. Parse doc   │
       │  2. Extract     │
       │     sections    │
       │  3. Store to DB │
       │  4. Update      │
       │     status      │
       └─────────────────┘
       
┌─────────────────────────┐
│ Status Polling          │
│ GET /tender/{id}/status │
└─────────────────────────┘
       │
       ▼ Returns: "processing" → "completed" → Evaluation
```

## API Endpoints

### 1. Upload Tender Document
**Endpoint:** `POST /tender/upload`

**Authentication:** Required (Bearer token)

**Request:**
```http
Content-Type: multipart/form-data

file: <binary PDF/DOCX file>
```

**Response (200 OK):**
```json
{
  "tender_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "uploaded",
  "message": "Tender uploaded successfully. Processing started."
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Only PDF and DOCX files are supported"
}
```

```json
{
  "detail": "Please create a company profile first"
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

---

### 2. Poll Tender Status
**Endpoint:** `GET /tender/{tender_id}/status`

**Authentication:** Required (Bearer token)

**Response (200 OK):**
```json
{
  "tender_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "filename": "RFP_2024_Q1.pdf",
  "uploaded_at": "2026-01-22T13:25:45.123456",
  "processed_at": null
}
```

**Status Values:**
- `uploaded` - File received, waiting to process
- `processing` - Currently extracting document
- `completed` - Done, results available via `/evaluation`
- `failed` - Error occurred during processing

**Response (404 Not Found):**
```json
{
  "detail": "Tender not found"
}
```

---

### 3. Get Tender Evaluation
**Endpoint:** `GET /tender/{tender_id}/evaluation`

**Authentication:** Required (Bearer token)

**Response (200 OK):**
```json
{
  "tender_id": "550e8400-e29b-41d4-a716-446655440000",
  "eligibility_verdict": "eligible",
  "eligibility_score": 85,
  "risk_score": 45,
  "risk_level": "medium",
  "effort_score": 60,
  "effort_level": "medium",
  "ai_summary": "Strong technical fit. EMD and timeline manageable.",
  "missing_documents": ["Financial statements", "Bank guarantee"],
  "risk_factors": ["Aggressive timeline", "EMD requirement"],
  "clause_evaluations": [...],
  "created_at": "2026-01-22T13:26:45.123456"
}
```

**Response (400 Bad Request - Still Processing):**
```json
{
  "detail": "Tender processing status: processing"
}
```

## File Upload Flow

### 1. Validation
```python
# Content-type check
✓ application/pdf
✓ application/vnd.openxmlformats-officedocument.wordprocessingml.document
✗ text/plain (rejected)

# Company profile verification
✓ User has company profile
✗ No company profile (rejected)

# File size check (configured in settings)
✓ Under MAX_FILE_SIZE_MB
✗ Over limit (rejected)
```

### 2. Secure File Storage
```
uploads/
├── {uuid}_RFP_2024_Q1.pdf        # Original filename preserved
├── {uuid}_tender_doc.docx
└── {uuid}_scope_tender.pdf

Benefits:
- UUID prefix prevents collisions
- Original filename preserved for user reference
- Organized in single directory
- Easy to delete when tender record deleted
```

### 3. Database Record Creation
```sql
INSERT INTO tenders (
  id, user_id, company_id, original_filename, 
  file_path, status, uploaded_at
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  '...',
  '...',
  'RFP_2024_Q1.pdf',
  'uploads/550e8400-e29b-41d4-a716-446655440000_RFP_2024_Q1.pdf',
  'UPLOADED',
  NOW()
);
```

### 4. Queue Background Task
```python
# FastAPI BackgroundTasks
background_tasks.add_task(
    process_tender_task,
    tender_id="550e8400-e29b-41d4-a716-446655440000"
)

# Returns immediately to user
# Task runs in background thread
```

## Background Processing (Celery/FastAPI)

### Current Implementation: FastAPI BackgroundTasks
- **Pros:** No external dependencies (Redis not required)
- **Cons:** Tasks lost on server restart
- **Use Case:** Development and simple deployments

### Alternative: Celery with Redis
- **Pros:** Persistent, scalable, production-ready
- **Cons:** Requires Redis setup
- **Configuration:** Update `CELERY_BROKER_URL` in `.env`

### Processing Pipeline

```python
# Stage 1: Document Parsing
- Read file from disk
- Extract text using pdfplumber (PDF) or python-docx (DOCX)
- Return pages with text content

# Stage 2: Section Detection
- Analyze text patterns
- Identify section headers (e.g., "SCOPE", "REQUIREMENTS", "TERMS")
- Split content by sections
- Save sections to database

# Stage 3: Update Status (Placeholder for AI)
# TODO: Once AI logic ready:
# - Extract clauses from each section
# - Evaluate eligibility against company profile
# - Calculate risk and effort scores
# - Generate evaluation report

# Stage 4: Mark Complete
- Update tender.status = COMPLETED
- Set tender.processed_at = now()
- Make results available via evaluation endpoint
```

## Error Handling

### Graceful Degradation
```python
try:
    # Process tender
    tender.status = PROCESSING
    pages = parse_document(file_path)
    sections = split_by_sections(pages)
    save_sections(sections)
    tender.status = COMPLETED
except Exception as e:
    # Log error
    logger.error(f"Error: {e}")
    # Mark failed but don't crash
    tender.status = FAILED
    db.commit()
    # Optionally retry (Celery max_retries=3)
```

### User Feedback
- Upload returns immediately with `tender_id`
- User polls status endpoint in frontend
- Frontend shows progress: "Uploaded → Processing → Completed"
- If failed, status shows "failed", user can retry upload

## Development Testing

### Quick Test with cURL
```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
# Copy access_token from response

# 3. Create company
curl -X POST http://localhost:8000/company/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Company","industry":"IT"}'

# 4. Upload tender
curl -X POST http://localhost:8000/tender/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/tender.pdf"
# Copy tender_id from response

# 5. Poll status
curl -X GET "http://localhost:8000/tender/<tender_id>/status" \
  -H "Authorization: Bearer <token>"

# 6. Get evaluation (when status = completed)
curl -X GET "http://localhost:8000/tender/<tender_id>/evaluation" \
  -H "Authorization: Bearer <token>"
```

### Run Test Suite
```bash
cd backend
.venv\Scripts\pytest tests/test_tender_upload.py -v
```

## Configuration

### Environment Variables (.env)
```env
# File Upload
MAX_FILE_SIZE_MB=500
UPLOAD_DIR=uploads

# Document Processing
CHUNK_SIZE=1200
CHUNK_OVERLAP=150

# Async Processing
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# LLM (for future AI pipeline)
LLM_PROVIDER=  # Leave empty until Step-5
```

## Next Steps

### Step-4: AI Logic Implementation
- Implement `ai_extractor.py` with LLM calls
- Integrate clause extraction and eligibility evaluation
- Replace TODOs in `process_tender_task`

### Step-5: Scoring & Report Generation
- Integrate `scoring.py` calculations
- Generate PDF/DOCX bid recommendation reports

### Step-6: Frontend Integration
- Build React/Vue interface for upload
- Real-time status polling UI
- Results dashboard

## Monitoring

### Check Logs
```bash
# FastAPI logs (in terminal running server)
INFO:     Uvicorn running on http://0.0.0.0:8000

# Application logs
cd backend
.venv\Scripts\python -c "
import logging
logging.basicConfig(level=logging.INFO)
from app.workers.tasks import process_tender_task
print('Celery task configured')
"
```

### Database Inspection
```bash
# Check tender status
sqlite3 tenderiq.db
> SELECT id, status, uploaded_at, processed_at FROM tenders;

# Check sections extracted
> SELECT section_name FROM tender_sections WHERE tender_id='...';
```

## Security Considerations

✅ **Implemented:**
- File type validation (PDF/DOCX only)
- File size limits (configurable)
- User authorization (only see own tenders)
- Secure filename generation (UUID prefix)
- Safe file storage on disk

⚠️ **To Implement:**
- Scan uploaded files for malware (ClamAV)
- Encrypt files at rest
- Set file permissions (not readable by other users)
- Rate limiting on uploads
- Audit logging

## Performance Notes

### Current Bottlenecks
1. Document parsing (large PDFs may take 10-30 seconds)
2. Section detection (regex-based, may miss complex layouts)
3. Sequential processing (one tender at a time with BackgroundTasks)

### Optimization Opportunities
1. Use Celery for parallel processing (multiple workers)
2. Implement document caching (same RFP uploaded multiple times)
3. Add progress webhooks (notify frontend during processing)
4. Optimize regex patterns for section detection

---

**Status: ✅ Step-3 Complete**
- Multipart file upload: ✅
- Safe file storage: ✅
- Tender record creation: ✅
- Background processing: ✅
- Status polling: ✅
- Error handling: ✅
- Tests: ✅
- Documentation: ✅

**Next: Step-4 - AI Logic Implementation (when ready)**
