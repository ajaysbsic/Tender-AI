# Step-7 Quick Reference

## 🎯 What is Step-7?

AI-powered extraction of tender information into structured JSON using 4 LLM pipelines.

---

## ⚡ Quick Start

### 1. Install
```bash
pip install -r requirements.txt  # LangChain already added
```

### 2. Set API Key
```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Run Demo
```bash
python step7_demo.py
```

### 4. Use in Code
```python
from app.services.tender_analyzer import TenderAnalyzer

analyzer = TenderAnalyzer()
result = analyzer.analyze_tender(
    tender_id="RFP-2024-001",
    tender_text=document,
    company_profile=company_info
)

print(result.overall_recommendation)  # BID / NO_BID / CONDITIONAL
```

---

## 📦 4 Pipelines

| Pipeline | Input | Output | Purpose |
|----------|-------|--------|---------|
| **Clause Extractor** | Tender text | Clauses + requirements | Extract what must be delivered |
| **Eligibility Evaluator** | Requirements + company | Eligibility score | Can we bid? (0-100%) |
| **Risk Analyzer** | Tender clauses | Risks + severity | What could go wrong? (0-100 score) |
| **Effort Estimator** | Deliverables | Hours + cost + timeline | How long? How much? |

---

## 🔧 Import Cheat Sheet

```python
# Individual pipelines
from app.services.clause_extractor import ClauseExtractor
from app.services.eligibility_evaluator import EligibilityEvaluator
from app.services.risk_analyzer import RiskAnalyzer
from app.services.effort_estimator import EffortEstimator

# Integrated analyzer (recommended)
from app.services.tender_analyzer import TenderAnalyzer

# Schemas & validation
from app.services.ai_schemas import (
    ClauseExtractionOutput,
    EligibilityReasoningOutput,
    RiskIdentificationOutput,
    EffortEstimationOutput,
    validate_output,
)

# LLM client
from app.services.llm_client import (
    LLMClient,
    LLMConfig,
    LLMProvider,
    LLMModel,
)

# Prompts
from app.services.prompts import PromptManager
```

---

## 📊 Input/Output Formats

### Input
```python
{
    "tender_id": "RFP-2024-001",
    "tender_text": "Full tender document text...",
    "company_profile": {
        "name": "Company",
        "years_in_business": 7,
        "expertise_areas": ["Python", "AI"],
        "team_size": 50,
        ...
    }
}
```

### Output (Integrated Analysis)
```python
{
    "overall_recommendation": "BID|NO_BID|CONDITIONAL",
    "feasibility_score": 75.0,          # 0-100
    "risk_adjusted_score": 68.0,        # 0-100
    "eligibility": {...},               # Full eligibility result
    "risks": {...},                     # Full risk analysis
    "effort": {...},                    # Full effort estimate
    "clauses": {...},                   # Full clause extraction
    "must_dos_before_bid": [...]        # Action items
}
```

---

## 🎯 Common Use Cases

### Get Bid Recommendation (Quick)
```python
from app.services.tender_analyzer import get_bid_recommendation

recommendation = get_bid_recommendation(tender_id, text, profile)
# Returns: {"recommendation": "BID", "feasibility_score": 75, ...}
```

### Extract Clauses Only
```python
from app.services.clause_extractor import ClauseExtractor

extractor = ClauseExtractor()
result = extractor.extract_clauses(tender_id, text)
# Returns: ClauseExtractionOutput with all clauses
```

### Check Eligibility
```python
from app.services.eligibility_evaluator import EligibilityEvaluator

evaluator = EligibilityEvaluator()
result = evaluator.evaluate_eligibility(tender_id, requirements, profile)
# Returns: EligibilityReasoningOutput with score (0-100)
```

### Identify Risks
```python
from app.services.risk_analyzer import RiskAnalyzer

analyzer = RiskAnalyzer()
result = analyzer.analyze_risks(tender_id, text)
# Returns: RiskIdentificationOutput with all risks + severity
```

### Estimate Effort
```python
from app.services.effort_estimator import EffortEstimator

estimator = EffortEstimator()
result = estimator.estimate_effort(tender_id, scope, requirements)
# Returns: EffortEstimationOutput with hours + cost + timeline
```

---

## 🔑 Key Concepts

### Confidence Scores (0-1)
- ✓ 0.9+ = Highly confident
- ✓ 0.7-0.9 = Reasonably confident
- ⚠️ 0.5-0.7 = Uncertain, may need review
- ❌ <0.5 = Low confidence, recommend human review

### Risk Scores (0-100)
- 0-20 = Low risk ✓
- 21-40 = Medium-low risk
- 41-60 = Medium risk ⚠️
- 61-80 = High risk ⚠️
- 81-100 = Critical risk ❌

### Eligibility Verdict
- "eligible" = Meets all key requirements ✓
- "partially_eligible" = Meets most, has addressable gaps
- "not_eligible" = Critical gaps block bidding ❌

### Bid Recommendation
- "BID" = Go ahead, favorable profile
- "CONDITIONAL" = Can bid if mitigations in place
- "NO_BID" = Major issues, don't bid

---

## 🛠️ Configuration

### Change LLM Provider
```python
from app.services.llm_client import LLMConfig, LLMProvider, LLMModel

config = LLMConfig(
    provider=LLMProvider.ANTHROPIC,        # or OPENAI
    model=LLMModel.CLAUDE_3_SONNET,        # or GPT4_TURBO
    temperature=0.0,                       # Deterministic
)

from app.services.tender_analyzer import TenderAnalyzer
analyzer = TenderAnalyzer(llm_client=LLMClient(config))
```

### Set Default Configuration
```python
from app.services.llm_client import LLMClientFactory

default_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model=LLMModel.GPT35_TURBO,  # Cheaper
)

LLMClientFactory.set_default_config(default_config)
```

---

## 📊 Schema Overview

### ClauseExtractionOutput
```
├── clauses[]: Extracted clauses
│   ├── clause_number: "1.2"
│   ├── requirements[]: Requirements in clause
│   │   ├── requirement_text: "..."
│   │   ├── type: "mandatory"
│   │   ├── category: "deliverable"
│   │   ├── measurable: true
│   │   └── metric: "..."
│   ├── penalty_applies: true
│   └── dependencies: ["1.1", "2.1"]
├── extraction_confidence: 0.92
└── extraction_notes: [...]
```

### EligibilityReasoningOutput
```
├── requirement_evaluations[]:
│   ├── requirement_id: "R1"
│   ├── company_meets: true/false
│   ├── reasoning: "Detailed analysis..."
│   ├── confidence: 0.85
│   └── recommendation: "accept|conditional|reject"
├── eligibility_score: 85.0 (0-100)
├── overall_eligibility_verdict: "eligible"
└── critical_gaps: [...]
```

### RiskIdentificationOutput
```
├── risks[]:
│   ├── risk_title: "Tight timeline"
│   ├── severity: "high"
│   ├── probability: "medium"
│   ├── deal_breaker: false
│   ├── mitigations: ["..."]
│   └── business_impact: "..."
├── risk_score: 65.0 (0-100)
├── overall_risk_level: "high"
└── deal_breaker_risks: [...]
```

### EffortEstimationOutput
```
├── work_packages[]:
│   ├── package_name: "Development"
│   ├── estimated_hours: 320.0
│   ├── effort_range_low: 240
│   ├── effort_range_high: 400
│   ├── effort_level: "high"
│   └── required_skills: [...]
├── total_estimated_hours: 1240
├── timeline: { days: 22, critical_path_days: 18 }
├── cost: { estimated_cost: 124000, labor_cost: 96000 }
└── estimation_confidence: 0.78
```

---

## ⚠️ Important Reminders

1. **NO Summarization** - All analysis is clause-level, not summaries
2. **Structured JSON Only** - Never free-form text output
3. **Confidence Required** - Include confidence/severity scores
4. **Error Handling** - All pipelines handle errors gracefully
5. **Logging** - Enable debug logging with `export DEBUG=1`

---

## 🔍 Error Handling

```python
try:
    result = analyzer.analyze_tender(tender_id, text, profile)
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"LLM error (check API key): {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## 🚀 Next Steps

1. ✅ Step-7 Implementation COMPLETE
2. ⏳ Create database models for storing results
3. ⏳ Create API endpoints for each pipeline
4. ⏳ Create web dashboard for visualization
5. ⏳ Integrate with Steps 1-6 workflow

---

## 📞 Debugging

```bash
# Check imports
python -c "from app.services.tender_analyzer import TenderAnalyzer; print('OK')"

# Run demo
python step7_demo.py

# Test specific pipeline
python -c "from app.services.clause_extractor import ClauseExtractor; print('OK')"

# Enable debug logging
export DEBUG=1
python your_script.py
```

---

## 🎓 Learning Resources

- Full docs: [STEP_7_DOCUMENTATION.md](STEP_7_DOCUMENTATION.md)
- Demo code: [step7_demo.py](step7_demo.py)
- Schemas: [ai_schemas.py](app/services/ai_schemas.py)
- LLM config: [llm_client.py](app/services/llm_client.py)
- Prompts: [prompts.py](app/services/prompts.py)

---

**Version**: 1.0  
**Status**: ✅ Production Ready  
**Last Updated**: 2024
