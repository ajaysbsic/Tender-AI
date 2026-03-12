# STEP-9 INTEGRATION GUIDE

**Get Step-9 Running in Your Environment**

---

## 🚀 Quick Integration (10 minutes)

### Step 1: Install Dependencies

```bash
# Install reportlab for PDF generation
pip install reportlab

# Verify installation
python -c "import reportlab; print('ReportLab installed:', reportlab.Version)"
```

### Step 2: Include API Router

Edit `app/main.py`:

```python
from fastapi import FastAPI
from app.routes.evaluations import router as evaluations_router

app = FastAPI(
    title="Tender-AI",
    description="AI-powered tender evaluation system",
    version="1.0.0"
)

# Include evaluation endpoints
app.include_router(evaluations_router)

# Your other routes...
```

### Step 3: Test API Endpoints

```bash
# Start the backend
cd d:\AI Projects\Tender-AI\backend
python -m uvicorn app.main:app --reload

# In another terminal, test
curl http://localhost:8000/api/evaluations/list
```

### Step 4: Generate Sample PDF

```bash
# Run the demo
python step9_demo.py

# Check generated PDFs
ls -la demo_tender_*_report.pdf
```

---

## 📋 Pre-Integration Checklist

Before integrating Step-9, ensure you have:

- [ ] **Backend running**: `uvicorn app.main:app --reload`
- [ ] **Dependencies installed**: `pip install reportlab`
- [ ] **Database setup**: TenderEvaluation table exists
- [ ] **Step-8 working**: Scoring engine produces TenderScore objects
- [ ] **FastAPI structure**: app/main.py exists with FastAPI app
- [ ] **Routes folder**: app/routes/ directory exists

---

## 🔧 Full Integration Steps

### Step 1: Install ReportLab

```bash
# Using pip
pip install reportlab

# Using poetry (if using poetry)
poetry add reportlab

# Using conda
conda install reportlab
```

### Step 2: Copy Files

Files should already be in place:
- ✅ `app/services/report_generator.py` - Report generation
- ✅ `app/routes/evaluations.py` - API endpoints
- ✅ `tests/test_step9_evaluations.py` - Unit tests
- ✅ `step9_demo.py` - Demonstration script

### Step 3: Register Router in FastAPI

**File: `app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Step-9 router
from app.routes.evaluations import router as evaluations_router

# Create FastAPI app
app = FastAPI(
    title="Tender-AI",
    description="AI-powered tender evaluation system",
    version="1.0.0"
)

# Add CORS middleware (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== STEP-9 INTEGRATION =====
# Include evaluation endpoints
app.include_router(evaluations_router)

# Include other routers...
# app.include_router(other_router)

@app.get("/")
def read_root():
    return {"message": "Tender-AI Backend", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 4: Implement Score Reconstruction

**File: `app/routes/evaluations.py`**

The helper function `_reconstruct_tender_score()` needs to be implemented to load TenderScore from database.

```python
# In app/routes/evaluations.py, find:
def _reconstruct_tender_score(evaluation: TenderEvaluation) -> TenderScore:
    """Reconstruct TenderScore from database evaluation"""
    
    # Option 1: If storing as JSON
    if hasattr(evaluation, 'tender_score_json'):
        import json
        score_dict = json.loads(evaluation.tender_score_json)
        return TenderScore(**score_dict)
    
    # Option 2: If using a to_tender_score() method
    if hasattr(evaluation, 'to_tender_score'):
        return evaluation.to_tender_score()
    
    # Option 3: Manual reconstruction from individual fields
    # (implement based on your database schema)
    
    raise NotImplementedError("Score reconstruction not implemented")
```

### Step 5: Set Up Database Model

**File: `app/models.py`** (add to existing models)

```python
from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime

class TenderEvaluation(Base):
    __tablename__ = "tender_evaluations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String, unique=True, index=True)
    
    # Scores
    overall_score = Column(Float)
    bid_recommendation = Column(String)  # BID, NO_BID, CONDITIONAL
    
    # Store full TenderScore as JSON
    tender_score_json = Column(JSON)
    
    # Metadata
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Method to reconstruct TenderScore
    def to_tender_score(self) -> 'TenderScore':
        """Reconstruct TenderScore from stored JSON"""
        import json
        from app.services.scoring_models import TenderScore
        
        score_dict = json.loads(self.tender_score_json)
        return TenderScore(**score_dict)
```

### Step 6: Store Scores in Database

After scoring a tender, save the result:

```python
import json
from app.database import SessionLocal
from app.models import TenderEvaluation
from app.services.scoring_engine import TenderScoringEngine

# Score the tender
engine = TenderScoringEngine()
tender_score = engine.score_tender(...)

# Store in database
db = SessionLocal()
evaluation = TenderEvaluation(
    tender_id=tender_score.tender_id,
    overall_score=tender_score.overall_score,
    bid_recommendation=tender_score.bid_recommendation,
    tender_score_json=json.dumps(tender_score.dict()),  # Serialize to JSON
)
db.add(evaluation)
db.commit()
db.refresh(evaluation)

print(f"Evaluation stored for {tender_score.tender_id}")
```

### Step 7: Test Integration

```bash
# 1. Start backend
python -m uvicorn app.main:app --reload

# 2. In new terminal, test the endpoint
curl -X GET "http://localhost:8000/api/evaluations/list" | python -m json.tool

# 3. Test PDF generation
curl -X GET "http://localhost:8000/api/evaluations/tender/TENDER-001/report/pdf" \
  -H "Accept: application/pdf" \
  --output test_report.pdf

# 4. Test list endpoint with filtering
curl -X GET "http://localhost:8000/api/evaluations/list?status=BID&limit=10"
```

---

## 🧪 Verify Integration

### Run Unit Tests

```bash
# Run all Step-9 tests
pytest tests/test_step9_evaluations.py -v

# Run specific test
pytest tests/test_step9_evaluations.py::TestReportGenerator::test_pdf_generation_returns_bytesio -v

# Run with coverage report
pytest tests/test_step9_evaluations.py --cov=app.services.report_generator --cov=app.routes.evaluations --cov-report=html
```

### Run Demo Script

```bash
# Generate sample reports and show API responses
python step9_demo.py

# Check generated files
ls -lh demo_tender_*.pdf
```

### Manual API Testing

```python
# test_integration.py
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. List evaluations
print("1. Listing evaluations...")
response = requests.get(f"{BASE_URL}/api/evaluations/list")
print(f"Status: {response.status_code}")
print(f"Results: {response.json()}")

# 2. Get specific evaluation
print("\n2. Getting specific evaluation...")
response = requests.get(f"{BASE_URL}/api/evaluations/tender/TENDER-001")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(json.dumps(response.json(), indent=2))

# 3. Download PDF
print("\n3. Downloading PDF report...")
response = requests.get(
    f"{BASE_URL}/api/evaluations/tender/TENDER-001/report/pdf",
    params={"company_name": "Test Company"}
)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"File size: {len(response.content)} bytes")

if response.status_code == 200:
    with open("test_report.pdf", "wb") as f:
        f.write(response.content)
    print("✓ PDF saved to test_report.pdf")
```

---

## 🔗 Endpoint Examples

### Retrieve Full Evaluation

```bash
curl -X GET "http://localhost:8000/api/evaluations/tender/TENDER-001"
```

**Response:**
```json
{
  "tender_id": "TENDER-001",
  "tender_title": "Web Application Development RFP",
  "overall_score": 83.5,
  "bid_recommendation": "BID",
  "scores": {
    "eligibility": {
      "score": 95.0,
      "category": "ELIGIBLE"
    },
    "risk": {
      "score": 25.0,
      "category": "LOW"
    },
    "effort": {
      "score": 30.0,
      "category": "LOW"
    }
  },
  "summary": "RECOMMEND: This is a strong opportunity to bid on...",
  "strengths": ["Strong eligibility profile", ...],
  "weaknesses": ["Tight timeline could be challenging"],
  "critical_items": ["Confirm team availability..."]
}
```

### Get Eligibility Assessment

```bash
curl -X GET "http://localhost:8000/api/evaluations/tender/TENDER-001/eligibility"
```

**Response includes:**
- Eligibility category
- Score percentage
- Requirements met count
- List of all requirements with reasoning

### Get Risk Assessment

```bash
curl -X GET "http://localhost:8000/api/evaluations/tender/TENDER-001/risk"
```

**Response includes:**
- Risk category (LOW/MEDIUM/HIGH)
- Risk score
- Risk distribution (critical/high/medium/low count)
- Top risks
- Deal-breaker risks

### Get Effort Assessment

```bash
curl -X GET "http://localhost:8000/api/evaluations/tender/TENDER-001/effort"
```

**Response includes:**
- Effort category
- Effort score
- Resource requirements (hours, days, team size, cost)
- Complexity factors

### Download PDF Report

```bash
curl -X GET "http://localhost:8000/api/evaluations/tender/TENDER-001/report/pdf?company_name=Acme%20Corp" \
  --output report.pdf
```

**Returns:** PDF file with professional report

### List All Evaluations

```bash
curl -X GET "http://localhost:8000/api/evaluations/list?status=BID&limit=50&offset=0"
```

**Response includes:**
- Total count
- Pagination info
- List of evaluations with summary data

---

## 🔧 Configuration

### Customize Business Language

Edit `app/services/report_generator.py`:

```python
class BusinessLanguageTranslator:
    @staticmethod
    def eligibility_verdict(score: float, category: str) -> Dict[str, str]:
        verdict_map = {
            EligibilityCategory.ELIGIBLE.value: {
                "title": "✓ YOUR_TITLE",  # Customize
                "headline": "Your custom headline",  # Customize
                "summary": f"Your message for {score}%",  # Customize
                "action": "Your action",  # Customize
            },
            ...
        }
```

### Adjust Score Thresholds

Edit `app/services/scoring_models.py`:

```python
# Change eligibility threshold from 90% to 85%
if score >= 85:  # Changed from 90
    category = EligibilityCategory.ELIGIBLE
elif score >= 70:
    category = EligibilityCategory.PARTIALLY_ELIGIBLE
```

### Customize PDF Styling

Edit `report_generator.py` `_setup_styles()` method:

```python
styles.add(ParagraphStyle(
    name='TitleMain',
    fontSize=32,  # Increase from 28
    textColor=HexColor('#FF0000'),  # Change color
    fontName='Times-Bold',  # Change font
))
```

---

## ⚠️ Common Integration Issues

### Issue 1: ImportError - No module named 'reportlab'

**Error:**
```
ModuleNotFoundError: No module named 'reportlab'
```

**Solution:**
```bash
pip install reportlab
python -c "import reportlab; print('OK')"
```

### Issue 2: Router not registered

**Error:**
```
No route for GET /api/evaluations/list
```

**Solution:** Make sure to include router in `app/main.py`:
```python
from app.routes.evaluations import router as evaluations_router
app.include_router(evaluations_router)
```

### Issue 3: Database connection error

**Error:**
```
SQLAlchemy connection error
```

**Solution:** Ensure database is running and connection string is correct in `app/database.py`

### Issue 4: PDF generation fails

**Error:**
```
Failed to generate PDF report
```

**Solution:**
- Verify TenderScore has all required fields
- Check that BytesIO buffer is properly initialized
- Review error logs for specific issue

### Issue 5: 404 on evaluation endpoint

**Error:**
```
Tender TENDER-001 not found
```

**Solution:**
- Verify tender_id exists in database
- Check TenderEvaluation record exists
- Ensure evaluation has been scored and stored

---

## 📦 Required Files Checklist

Verify these files exist:

- [ ] `app/services/report_generator.py` (950 lines)
- [ ] `app/routes/evaluations.py` (500 lines)
- [ ] `tests/test_step9_evaluations.py` (420 lines)
- [ ] `step9_demo.py` (450 lines)
- [ ] `STEP_9_DOCUMENTATION.md` (800 lines)
- [ ] `STEP_9_QUICK_REFERENCE.md` (200 lines)
- [ ] `STEP_9_SUMMARY.md` (this file)

---

## 🎯 Next Integration Steps

### Immediate (This Week)

1. ✅ Install reportlab
2. ✅ Register router in FastAPI
3. ✅ Implement score reconstruction
4. ✅ Test API endpoints
5. ✅ Run unit tests

### Short Term (Next Week)

1. Set up frontend UI
2. Create report download page
3. Add email notifications
4. Implement report caching

### Long Term (Next Month)

1. Advanced analytics dashboard
2. Comparative tender analysis
3. Custom report templates
4. Multi-language support

---

## 📊 Integration Verification

After integration, verify:

- ✓ Endpoints respond with 200 OK
- ✓ PDF files are generated
- ✓ Unit tests pass
- ✓ Error handling works
- ✓ Database persistence working
- ✓ Streaming downloads efficient

---

## 📞 Support

If you encounter issues:

1. Check **STEP_9_QUICK_REFERENCE.md** for common issues
2. Review **STEP_9_DOCUMENTATION.md** for detailed explanation
3. Run **step9_demo.py** to verify system works
4. Check test cases in **test_step9_evaluations.py**
5. Review error logs for specific details

---

## ✅ Integration Checklist

```
[ ] Install reportlab: pip install reportlab
[ ] Copy files to correct locations
[ ] Import router in app/main.py
[ ] Register router with FastAPI app
[ ] Implement _reconstruct_tender_score()
[ ] Create/migrate TenderEvaluation table
[ ] Run unit tests: pytest tests/test_step9_evaluations.py
[ ] Run demo: python step9_demo.py
[ ] Test API endpoints manually
[ ] Verify PDF generation works
[ ] Check database persistence
[ ] Document any customizations
[ ] Deploy to production
```

---

**Integration Time Estimate:** 30-60 minutes  
**Complexity:** Medium  
**Risk Level:** Low  

*Ready for deployment* ✅
