# Step-8 Quick Reference Guide

## 5-Minute Overview

**Step-8** adds deterministic, explainable scoring to Tender-AI:

```python
# 1. Get Step-7 analysis results
analysis = tender_analyzer.analyze(chunks, tender_id)

# 2. Score the tender
engine = TenderScoringEngine()
tender_score = engine.score_tender(
    tender_id,
    analysis.eligibility,
    analysis.risks,
    analysis.effort,
)

# 3. Make decision
if tender_score.bid_recommendation == "BID":
    print(f"✓ Recommend BID: {tender_score.overall_score:.0f}/100")
    print(f"Strengths: {', '.join(tender_score.strengths)}")
else:
    print(f"✗ Recommend NO_BID")
    print(f"Issues: {', '.join(tender_score.critical_items)}")
```

---

## Three Scoring Dimensions

| Dimension | Input | Output | Thresholds |
|-----------|-------|--------|-----------|
| **Eligibility** | Requirements met/not | 0-100% + Category | Eligible ≥90%, Partial 70-89%, Not <70% |
| **Risk** | Severity + Probability | 0-100 + Category | Low 0-33, Medium 34-66, High 67-100 |
| **Effort** | Hours + Timeline + Cost | 0-100 + Category | Low 0-33, Medium 34-66, High 67-100 |

---

## Scoring Output

```python
TenderScore
├── overall_score: 78.5        # 0-100 weighted average
├── bid_recommendation: "BID"  # BID | NO_BID | CONDITIONAL
├── eligibility: EligibilityScore
│   ├── eligibility_score: 95%
│   ├── category: "ELIGIBLE"
│   └── critical_gaps: []
├── risk: RiskScore
│   ├── risk_score: 35         # 0-100, lower is better
│   ├── risk_category: "LOW"
│   └── deal_breakers: []
├── effort: EffortScore
│   ├── effort_score: 48       # 0-100, lower is better
│   ├── effort_category: "MEDIUM"
│   └── complexity_factors: ["High effort: 1200 hours"]
├── strengths: ["✓ Meets all mandatory", "✓ Low risk"]
├── weaknesses: ["⚠ Tight timeline"]
└── critical_items: ["🔴 Resolve tech mismatch"]
```

---

## Quick Usage

### Individual Scoring
```python
from app.services.scoring_engine import (
    score_eligibility,
    score_risks,
    score_effort,
)

# Score one dimension
elig = score_eligibility(eligibility_result)
risk = score_risks(risk_result)
effort = score_effort(effort_result)

print(f"{elig.eligibility_score:.0f}% eligible")
print(f"{risk.risk_score:.0f}/100 risk")
print(f"{effort.effort_score:.0f}/100 effort")
```

### Integrated Scoring
```python
from app.services.scoring_engine import score_tender

# Score complete tender
tender_score = score_tender(
    "TENDER_001",
    eligibility_result,
    risk_result,
    effort_result,
)

print(f"Overall: {tender_score.overall_score:.0f}")
print(f"Decision: {tender_score.bid_recommendation}")
```

---

## Configuration

### Default (Balanced)
```python
ScoringConfig()

# 35% eligibility, 35% risk, 30% effort
# Risk: 60% severity, 40% probability
# Effort: 50% hours, 30% timeline, 20% cost
```

### Risk-Averse
```python
ScoringConfig(
    risk_weight=0.40,
    risk_severity_weight=0.70,
)
```

### Cost-Sensitive
```python
ScoringConfig(
    effort_weight=0.40,
    effort_cost_weight=0.35,
)
```

---

## Recommendation Logic

```
Eligibility    Risk         Effort       → Recommendation
────────────────────────────────────────────────────────
NOT_ELIGIBLE   Any          Any          → NO_BID
Eligible       HIGH + Deal  Any          → NO_BID
Any            HIGH         HIGH         → NO_BID
Eligible       LOW/MED      LOW/MED      → BID
Any            MED          Any          → CONDITIONAL
Score >= 75                             → BID
Score >= 50                             → CONDITIONAL
Score < 50                              → NO_BID
```

---

## Common Scenarios

### ✓ Strong BID (All Green)
```
Eligibility: 95% ELIGIBLE ✓
Risk: 30 LOW ✓
Effort: 40 MEDIUM ✓
→ BID: 78/100
```

### ⚠ CONDITIONAL (Mixed)
```
Eligibility: 75% PARTIALLY ELIGIBLE
Risk: 50 MEDIUM
Effort: 55 MEDIUM
→ CONDITIONAL: 58/100 (Review needed)
```

### ✗ NO_BID (Red Flags)
```
Eligibility: 60% NOT ELIGIBLE
Risk: 75 HIGH
Effort: 80 HIGH
→ NO_BID: 28/100
Critical: Tech stack gap, unrealistic timeline
```

---

## Testing

### Run All Tests
```bash
pytest tests/test_scoring_engine.py -v
```

### Test Individual Components
```bash
# Eligibility tests only
pytest tests/test_scoring_engine.py::TestEligibilityScorer -v

# Risk tests only
pytest tests/test_scoring_engine.py::TestRiskScorer -v

# Effort tests only
pytest tests/test_scoring_engine.py::TestEffortScorer -v

# Determinism tests
pytest tests/test_scoring_engine.py::TestDeterminism -v
```

### Run Demo
```bash
python step8_demo.py
```

---

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `scoring_models.py` | 315 | Data models and schemas |
| `scoring_engine.py` | 680 | Scoring logic (4 classes) |
| `test_scoring_engine.py` | 420 | Unit tests (33 cases) |
| `STEP_8_DOCUMENTATION.md` | 1,800+ | Full documentation |
| `step8_demo.py` | 450 | Demonstrations |
| `STEP_8_SUMMARY.md` | 300+ | Implementation summary |

---

## Key Properties

✅ **Deterministic**: Same input = same output (testable)
✅ **Explainable**: Every score has detailed reasoning
✅ **Configurable**: Thresholds and weights adjustable
✅ **Typed**: Full type hints with Pydantic validation
✅ **Logged**: Built-in logging support
✅ **Fast**: <100ms for complete tender scoring
✅ **Tested**: 33 unit tests, all passing

---

## Common Issues

**Q: Score doesn't match my expectation?**
A: Check `scoring_logic` field - it shows exact calculation

**Q: How to customize for my organization?**
A: Create custom `ScoringConfig` with your weights/thresholds

**Q: Why is risk inverted?**
A: High risk = low score (higher risk reduces bid score)

**Q: Can I change thresholds?**
A: Yes, all thresholds are in `ScoringConfig.eligibility_thresholds`, `risk_thresholds`, `effort_thresholds`

---

## Integration Points

```
Backend API
├─ /api/tender/{id}/analyze      ← Step-7 (AI extraction)
├─ /api/tender/{id}/score        ← Step-8 (SCORING) ← You are here
└─ /api/tender/{id}/decision     ← Bid/No-bid decision

Database
├─ Tender documents
├─ Step-7 analysis results
└─ Step-8 scores ← Store here

Frontend Dashboard
├─ Component scores visualization
├─ BID/NO_BID recommendation
└─ Strengths/weaknesses display
```

---

## Next: API Integration

To expose scoring via REST API:

```python
from fastapi import FastAPI
from app.services.scoring_engine import TenderScoringEngine

@app.post("/api/tender/{tender_id}/score")
def score_tender_endpoint(tender_id: str, analysis: AnalysisResult):
    engine = TenderScoringEngine()
    tender_score = engine.score_tender(
        tender_id,
        analysis.eligibility,
        analysis.risks,
        analysis.effort,
    )
    return tender_score
```

---

## Reference Links

- **Full Documentation**: See `STEP_8_DOCUMENTATION.md`
- **Implementation Summary**: See `STEP_8_SUMMARY.md`
- **Unit Tests**: See `tests/test_scoring_engine.py`
- **Demo**: Run `python step8_demo.py`

---

## Support

For detailed information on:
- **Scoring formulas**: See STEP_8_DOCUMENTATION.md → "Key Formulas"
- **Configuration options**: See STEP_8_DOCUMENTATION.md → "Configuration"
- **Testing**: See STEP_8_DOCUMENTATION.md → "Testing"
- **Integration**: See STEP_8_DOCUMENTATION.md → "Integration with Step-7"

