# Step-3 Quick Reference Guide

## What Was Built

**Tender Upload & Async Processing Pipeline** for TenderIQ

- ✅ Multipart file upload (PDF/DOCX)
- ✅ Safe file storage with UUID naming
- ✅ Background document processing
- ✅ Real-time status polling
- ✅ User authorization & access control

---

## Running the Server

```bash
# Terminal 1: Start the FastAPI server
cd backend
.\start.ps1

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

---

## Quick Test Flow

```bash
# Terminal 2: Run integration test
cd ..
.venv\Scripts\python integration_test_step3.py
```

Or test manually with cURL:

```bash
# 1. Register
TOKEN=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@ex.com","password":"pass123"}' | jq -r '.id')

# 2. Login & get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@ex.com","password":"pass123"}' | jq -r '.access_token')

# 3. Create company
curl -s -X POST http://localhost:8000/company/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Company","industry":"IT"}' | jq

# 4. Upload tender
TENDER_ID=$(curl -s -X POST http://localhost:8000/tender/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@path/to/file.pdf" | jq -r '.tender_id')

# 5. Check status
curl -s -X GET "http://localhost:8000/tender/$TENDER_ID/status" \
  -H "Authorization: Bearer $TOKEN" | jq

# 6. Get results (when status=completed)
curl -s -X GET "http://localhost:8000/tender/$TENDER_ID/evaluation" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/register` | Create user account |
| POST | `/auth/login` | Get JWT token |
| POST | `/company/profile` | Create company profile |
| **POST** | **`/tender/upload`** | **Upload tender document** |
| **GET** | **`/tender/{id}/status`** | **Check processing status** |
| **GET** | **`/tender/{id}/evaluation`** | **Get evaluation results** |
| GET | `/health` | Server health check |
| GET | `/docs` | Interactive API documentation |

---

## Key Files

```
backend/
├── app/
│   ├── api/tender.py              ← Upload, status, evaluation endpoints
│   ├── workers/tasks.py           ← Background processing task
│   ├── services/parser.py         ← PDF/DOCX parsing
│   └── models/tables.py           ← Tender database model
├── uploads/                        ← Stores uploaded files
├── start.ps1                       ← Server startup script
├── STEP_3_TENDER_UPLOAD.md        ← Detailed API docs
└── integration_test_step3.py      ← Full test suite
```

---

## Status Values

| Status | Meaning |
|--------|---------|
| `uploaded` | File received, queued for processing |
| `processing` | Currently parsing document |
| `completed` | Done, results available |
| `failed` | Error occurred |

---

## Request Examples

### Upload Tender
```http
POST /tender/upload HTTP/1.1
Authorization: Bearer eyJ...
Content-Type: multipart/form-data

file: <binary PDF or DOCX>

Response:
{
  "tender_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "uploaded",
  "message": "Tender uploaded successfully. Processing started."
}
```

### Check Status
```http
GET /tender/550e8400-e29b-41d4-a716-446655440000/status HTTP/1.1
Authorization: Bearer eyJ...

Response:
{
  "tender_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "filename": "RFP_2024.pdf",
  "uploaded_at": "2026-01-22T13:25:45.123456",
  "processed_at": null
}
```

### Get Evaluation (when completed)
```http
GET /tender/550e8400-e29b-41d4-a716-446655440000/evaluation HTTP/1.1
Authorization: Bearer eyJ...

Response:
{
  "tender_id": "550e8400-e29b-41d4-a716-446655440000",
  "eligibility_verdict": "eligible",
  "eligibility_score": 85,
  "risk_score": 45,
  "effort_score": 60,
  ...
}
```

---

## Error Codes

| Code | Error | Solution |
|------|-------|----------|
| 200 | Success | - |
| 400 | Bad Request | Check file type (PDF/DOCX only) or company profile |
| 401 | Unauthorized | Missing or invalid token |
| 404 | Not Found | Tender doesn't exist or already deleted |
| 500 | Server Error | Check logs, restart server |

---

## Processing Pipeline

```
File Upload
    ↓
Save to disk (uploads/{uuid}_{filename})
    ↓
Create tender record (status=UPLOADED)
    ↓
Queue background task → Return to client immediately
    ↓
[Background]
Parse document (pdfplumber/python-docx)
    ↓
Detect sections (regex patterns)
    ↓
Save sections to database
    ↓
Update status=COMPLETED
    ↓
[Frontend]
Client polls status → sees COMPLETED
    ↓
Client calls /evaluation → gets results
```

---

## Troubleshooting

### Server won't start
```bash
# Check venv is installed
.\.venv\Scripts\python --version

# Check port 8000 is free
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F
```

### Upload fails with "Only PDF and DOCX"
- Verify file extension is `.pdf` or `.docx`
- Ensure Content-Type is set correctly

### Status stays "processing"
- Check backend logs for errors
- Verify file is readable in `uploads/` folder
- Restart server

### Can't find uploaded file
- Look in `backend/uploads/` folder
- Files named like: `550e8400...pdf`

---

## What's Next (Step-4)

The pipeline is ready for AI logic:

1. Implement `ai_extractor.py`
   - Extract clauses from sections
   - Evaluate eligibility
   - Identify risks

2. Update `process_tender_task`
   - Call AI extraction
   - Calculate scores
   - Generate evaluation

3. Test end-to-end with real RFPs

---

## Documentation

- **Full API Guide:** [STEP_3_TENDER_UPLOAD.md](backend/STEP_3_TENDER_UPLOAD.md)
- **Implementation Details:** [STEP_3_IMPLEMENTATION_SUMMARY.md](backend/STEP_3_IMPLEMENTATION_SUMMARY.md)
- **Complete Summary:** [STEP_3_COMPLETE.md](STEP_3_COMPLETE.md)
- **Test Suite:** [integration_test_step3.py](integration_test_step3.py)

---

## Summary

✅ **Tender Upload Pipeline: COMPLETE**

All endpoints working. Ready for AI integration in Step-4.

- Upload files: `POST /tender/upload`
- Check status: `GET /tender/{id}/status`
- Get results: `GET /tender/{id}/evaluation`

Test it: Run `integration_test_step3.py` or use `/docs` for interactive testing.

---

**Status: ✅ Step-3 COMPLETE** | **Next: Step-4 (AI Logic)**
