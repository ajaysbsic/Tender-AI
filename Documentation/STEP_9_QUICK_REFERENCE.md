# STEP-9 Quick Reference

**Evaluation Retrieval & Report Generation**

---

## 🚀 Quick Start (5 minutes)

### Installation

```bash
# Install required dependency
pip install reportlab
```

### Generate PDF Report

```python
from app.services.report_generator import generate_tender_report
from app.services.scoring_models import TenderScore

# You have a TenderScore from Step-8
tender_score = scoring_engine.score_tender(...)

# Generate PDF
pdf_buffer = generate_tender_report(
    tender_score=tender_score,
    company_name="Your Company Name"
)

# Save to file
with open("tender_report.pdf", "wb") as f:
    f.write(pdf_buffer.getvalue())
```

---

## 📍 API Endpoints

### Get Evaluation (Full)
```bash
curl "http://api.tender-ai.local/api/evaluations/tender/TENDER-001"
```

**Response:**
```json
{
  "tender_id": "TENDER-001",
  "overall_score": 83.5,
  "bid_recommendation": "BID",
  "scores": {
    "eligibility": {"score": 95.0, "category": "ELIGIBLE"},
    "risk": {"score": 25.0, "category": "LOW"},
    "effort": {"score": 30.0, "category": "LOW"}
  }
}
```

### Get Eligibility Details
```bash
curl "http://api.tender-ai.local/api/evaluations/tender/TENDER-001/eligibility"
```

**Response:** Requirement-by-requirement assessment

### Get Risk Assessment
```bash
curl "http://api.tender-ai.local/api/evaluations/tender/TENDER-001/risk"
```

**Response:** Risk breakdown with deal-breakers

### Get Effort Estimate
```bash
curl "http://api.tender-ai.local/api/evaluations/tender/TENDER-001/effort"
```

**Response:** Resource requirements and timeline

### Download PDF Report
```bash
curl -O "http://api.tender-ai.local/api/evaluations/tender/TENDER-001/report/pdf?company_name=Acme%20Corp"
```

**Response:** PDF file (application/pdf)

### Get Text Summary
```bash
curl "http://api.tender-ai.local/api/evaluations/tender/TENDER-001/report/summary"
```

**Response:** Executive summary in JSON

### List Evaluations
```bash
# Get all BID recommendations
curl "http://api.tender-ai.local/api/evaluations/list?status=BID&limit=50"

# Get CONDITIONAL evaluations
curl "http://api.tender-ai.local/api/evaluations/list?status=CONDITIONAL&limit=50"

# Get all NO_BID
curl "http://api.tender-ai.local/api/evaluations/list?status=NO_BID&limit=100"
```

---

## 📊 Score Thresholds & Translation

### Eligibility → Category

| Score Range | Category | Verdict |
|-------------|----------|---------|
| ≥ 90% | ELIGIBLE | ✓ Excellent fit |
| 70-89% | PARTIALLY_ELIGIBLE | ⚠ Viable with gaps |
| < 70% | NOT_ELIGIBLE | ✗ Not recommended |

### Risk → Category

| Score Range | Category | Verdict |
|-------------|----------|---------|
| 0-40 | LOW | ✓ Manageable |
| 40-70 | MEDIUM | ⚠ Requires planning |
| 70-100 | HIGH | ✗ Significant concerns |

### Effort → Category

| Score Range | Category | Verdict |
|-------------|----------|---------|
| 0-35 | LOW | ✓ Modest requirements |
| 35-65 | MEDIUM | ⚠ Substantial effort |
| 65-100 | HIGH | 🚨 Major undertaking |

### Overall Score → Recommendation

| Score Range | Recommendation | Decision |
|-------------|-----------------|----------|
| ≥ 75 | BID | → Proceed with bid |
| 50-74 | CONDITIONAL | → Review carefully |
| < 50 | NO_BID | → Pass opportunity |

---

## 🎨 PDF Report Structure

```
Title Page
  ├─ Tender ID
  ├─ Overall Score (83.5/100)
  ├─ Recommendation (BID ✓ / CONDITIONAL ⚠ / NO_BID ✗)
  └─ Summary Box (color-coded)

Executive Summary
  ├─ Dimension scores table
  ├─ Key findings (top 3 strengths)
  └─ Key concerns (top 3 weaknesses)

Detailed Analysis
  ├─ Eligibility verdict + reasoning
  ├─ Risk verdict + deal-breakers
  └─ Effort verdict + resource summary

Requirement Assessment (Clause-level)
  └─ Table of all requirements with:
      ├─ Requirement text
      ├─ Met? (✓ Yes / ✗ No)
      └─ Assessment reasoning

Risk Assessment Details
  ├─ Risk distribution (critical/high/medium/low count)
  ├─ Top risks (top 5)
  └─ Deal-breaker risks (if any)

Effort & Resources
  ├─ Total hours
  ├─ Timeline (days)
  ├─ Team size
  ├─ Estimated cost
  └─ Complexity factors

Strategic Recommendations
  ├─ Critical action items
  ├─ Final recommendation
  └─ Next steps
```

---

## 💡 Common Use Cases

### Use Case 1: Get Quick Score
```python
response = requests.get("/api/evaluations/tender/TENDER-001")
print(f"Score: {response['overall_score']}/100")
print(f"Recommendation: {response['bid_recommendation']}")
```

### Use Case 2: Check Requirements Met
```python
response = requests.get("/api/evaluations/tender/TENDER-001/eligibility")
requirements = response['eligibility']['requirements']

for req in requirements:
    status = "✓" if req['met'] else "✗"
    print(f"{status} {req['text']}")
```

### Use Case 3: Identify Risks
```python
response = requests.get("/api/evaluations/tender/TENDER-001/risk")
risks = response['risk']

print(f"Risk Category: {risks['category']}")
for risk in risks['top_risks']:
    print(f"  - {risk}")
```

### Use Case 4: Estimate Resources
```python
response = requests.get("/api/evaluations/tender/TENDER-001/effort")
effort = response['effort']['resources']

print(f"Estimated Hours: {effort['total_hours']}")
print(f"Timeline: {effort['total_days']} days")
print(f"Team Size: {effort['team_size']} people")
print(f"Estimated Cost: ${effort['estimated_cost']:,.0f}")
```

### Use Case 5: Generate & Download Report
```python
import requests

response = requests.get(
    "/api/evaluations/tender/TENDER-001/report/pdf",
    params={"company_name": "Acme Corp"}
)

with open("report.pdf", "wb") as f:
    f.write(response.content)
```

### Use Case 6: Find All BID Opportunities
```python
response = requests.get(
    "/api/evaluations/list",
    params={"status": "BID", "limit": 50}
)

print(f"Found {response['total_count']} bid opportunities")

for tender in response['results']:
    print(f"{tender['tender_id']}: {tender['overall_score']}/100")
```

---

## 🔧 Customization

### Change Business Language

Edit `BusinessLanguageTranslator` in `report_generator.py`:

```python
class BusinessLanguageTranslator:
    @staticmethod
    def eligibility_verdict(score: float, category: str) -> Dict[str, str]:
        verdict_map = {
            "ELIGIBLE": {
                "title": "✓ YOUR CUSTOM TITLE",
                "headline": "Your custom headline",
                "summary": f"Custom message for {score}%",
                "action": "Your recommended action",
            },
            ...
        }
```

### Change PDF Styling

Edit `_setup_styles()` in `ReportGenerator`:

```python
def _setup_styles(self):
    styles = getSampleStyleSheet()
    
    # Customize colors, fonts, sizes
    styles.add(ParagraphStyle(
        name='TitleMain',
        fontSize=32,  # Increase size
        textColor=HexColor('#FF0000'),  # Change color
        fontName='Times-Bold',  # Change font
    ))
```

### Change Score Thresholds

Edit scoring thresholds in `scoring_models.py`:

```python
# Example: Change eligibility threshold from 90% to 85%
class EligibilityScore:
    def get_category(self, score: float):
        if score >= 85:  # Changed from 90
            return EligibilityCategory.ELIGIBLE
        elif score >= 70:
            return EligibilityCategory.PARTIALLY_ELIGIBLE
        else:
            return EligibilityCategory.NOT_ELIGIBLE
```

---

## ⚠️ Common Issues

### Issue: PDF won't open
**Solution:** Verify PDF generation completed successfully. Check file size >1KB.

### Issue: API returns 404
**Solution:** Confirm tender_id exists in database and has evaluation result.

### Issue: Special characters appear wrong in PDF
**Solution:** Ensure UTF-8 encoding. Update font if needed.

### Issue: Business language doesn't match our style
**Solution:** Customize BusinessLanguageTranslator class with your own templates.

### Issue: Report takes too long to generate
**Solution:** Consider async processing for large reports. Optimize image sizes.

---

## 📈 Performance Tips

1. **Cache Generated Reports**
   ```python
   # Store PDF in cache to avoid regenerating
   if cache.has(f"report_{tender_id}"):
       return cache.get(f"report_{tender_id}")
   ```

2. **Async Report Generation**
   ```python
   # For large reports, use FastAPI background tasks
   async def generate_report_async(tender_id: str, background_tasks):
       background_tasks.add_task(generate_and_email_report, tender_id)
       return {"status": "generating"}
   ```

3. **Streaming Large Downloads**
   ```python
   # Already implemented - uses StreamingResponse
   # Handles large PDFs efficiently
   ```

---

## 🧪 Run Tests

```bash
# Run all Step-9 tests
pytest tests/test_step9_evaluations.py -v

# Run specific test
pytest tests/test_step9_evaluations.py::TestReportGenerator::test_pdf_generation_returns_bytesio -v

# Run with coverage
pytest tests/test_step9_evaluations.py --cov=app.services.report_generator --cov=app.routes.evaluations
```

---

## 📞 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: reportlab` | `pip install reportlab` |
| PDF is empty | Verify TenderScore has all required fields |
| API endpoint 404 | Check router is registered in FastAPI app |
| Encoding errors | Use UTF-8; avoid special chars in file paths |
| Memory usage high | Stream reports; don't load full PDF in memory |

---

## 🎯 Next Steps

1. Register router in FastAPI main app
2. Add database persistence for evaluations
3. Create frontend to display results
4. Set up PDF archival/storage
5. Implement email notifications

---

**Last Updated:** January 22, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅
