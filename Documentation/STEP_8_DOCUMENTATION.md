# STEP-8: Scoring Engine Documentation

## Overview

The **Scoring Engine** is Tender-AI's deterministic, explainable scoring layer that converts Step-7 AI analysis results into actionable bid decisions. It provides three independent scoring dimensions (Eligibility, Risk, Effort) that feed into an integrated tender score and bid recommendation.

**Key Characteristics:**
- ✅ **Deterministic**: Same input always produces same output (no randomness, no LLM variability)
- ✅ **Explainable**: Every score includes detailed reasoning and calculation methodology
- ✅ **Unit-testable**: All functions are pure functions with clear inputs/outputs
- ✅ **Configurable**: Thresholds and weights can be customized via `ScoringConfig`
- ✅ **Transparent**: Shows component scores, intermediate calculations, and scoring logic

---

## Architecture

### Component Diagram

```
Step-7 AI Analysis Results
├─ Eligibility Evaluation (requirements met/not met)
├─ Risk Identification (severity × probability)
└─ Effort Estimation (hours, timeline, cost)
         ↓
         ├─────────────────────┬─────────────────────┬──────────────────────┐
         ↓                     ↓                     ↓                      ↓
    EligibilityScorer      RiskScorer          EffortScorer        TenderScoringEngine
         ↓                     ↓                     ↓                      ↓
  EligibilityScore        RiskScore           EffortScore           TenderScore
  (0-100%, Category)      (0-100, Category)   (0-100, Category)     + BID Recommendation
         ↓                     ↓                     ↓                      ↓
         └─────────────────────┴─────────────────────┴──────────────────────┘
                                    ↓
                         FINAL: TenderScore
                    (All scores + Recommendation)
                    (Strengths & Weaknesses)
```

### Scoring Modules

```
app/services/
├── scoring_models.py      # Data models and schemas
├── scoring_engine.py      # Scoring calculations
└── [other modules]

tests/
└── test_scoring_engine.py # Unit tests (40+ test cases)
```

---

## Scoring Dimensions

### 1. Eligibility Scoring

**Purpose**: Determine if company meets mandatory requirements

**Input**:
```python
EligibilityReasoningOutput
├── requirement_evaluations: List[RequirementEvaluation]
│   ├── requirement_id: str (e.g., "R1_mandatory")
│   ├── requirement_text: str (e.g., "ISO 9001 Certification")
│   ├── company_meets: bool
│   ├── reasoning: str
│   └── confidence: float (0-1)
└── eligibility_determination: str
```

**Calculation**:

```
1. Separate mandatory vs. optional requirements
2. Count met requirements: mandatory_met, optional_met
3. Calculate percentages:
   - Mandatory %: (mandatory_met / total_mandatory) × 100
   - Overall %: (total_met / total_requirements) × 100
4. Determine category based on mandatory %:
   - ELIGIBLE: ≥90%
   - PARTIALLY_ELIGIBLE: 70-89%
   - NOT_ELIGIBLE: <70%
5. Output: EligibilityScore with all metrics and reasoning
```

**Output**:
```python
EligibilityScore
├── eligibility_score: float (0-100, percentage)
├── category: EligibilityCategory (ELIGIBLE | PARTIALLY_ELIGIBLE | NOT_ELIGIBLE)
├── mandatory_percentage: float
├── overall_percentage: float
├── requirements_assessments: List[EligibilityRequirementAssessment]
├── critical_gaps: List[str] (unmet mandatory requirements)
├── met_requirements: List[str]
├── unmet_requirements: List[str]
├── scoring_logic: str (detailed explanation)
└── summary: str (executive summary)
```

**Example**:
```
Eligible: Company meets 95% of mandatory requirements (threshold: 90%)
- Met: ISO 9001, 5+ Years, Team Size
- Unmet: None
- Overall: 100% (3/3 requirements met)
```

**Thresholds** (configurable via `ScoringConfig`):
```python
ScoringConfig.eligibility_thresholds:
├── eligible_minimum: 90.0
└── partially_eligible_minimum: 70.0
```

---

### 2. Risk Scoring

**Purpose**: Assess likelihood and impact of identified risks

**Input**:
```python
RiskIdentificationOutput
├── total_risks_identified: int
├── critical_risks: int
├── high_risks: int
├── medium_risks: int
├── low_risks: int
└── risks: List[RiskAssessmentItem]
    ├── risk_title: str
    ├── severity: RiskSeverity (CRITICAL | HIGH | MEDIUM | LOW)
    ├── probability: str (high | medium | low)
    ├── deal_breaker: bool
    └── mitigation: str (optional)
```

**Calculation**:

```
1. Define weights:
   - Severity: CRITICAL=1.0, HIGH=0.75, MEDIUM=0.50, LOW=0.25
   - Probability: high=1.0, medium=0.6, low=0.3

2. For each risk, calculate impact:
   impact = (severity_weight × severity_factor + 
             probability_weight × probability_factor) × 100

   Where:
   - severity_factor = ScoringConfig.risk_severity_weight (default 60%)
   - probability_factor = ScoringConfig.risk_probability_weight (default 40%)

3. Average impacts:
   risk_score = Σ(impact) / num_risks (clamped to 0-100)

4. Determine category:
   - LOW: 0-33
   - MEDIUM: 34-66
   - HIGH: 67-100

5. Output: RiskScore with assessments and reasoning
```

**Output**:
```python
RiskScore
├── risk_score: float (0-100)
├── risk_category: RiskCategory (LOW | MEDIUM | HIGH)
├── total_risks: int
├── critical_count: int
├── high_count: int
├── medium_count: int
├── low_count: int
├── risk_assessments: List[RiskAssessment]
│   ├── risk_title: str
│   ├── severity: str
│   ├── probability: str
│   └── impact_score: float
├── top_risks: List[str]
├── deal_breakers: List[str]
├── scoring_logic: str (detailed explanation)
└── summary: str (executive summary)
```

**Example**:
```
Risk Profile: MEDIUM
- Total risks: 5
- Critical: 1, High: 2, Medium: 1, Low: 1
- Top risks: 
  1. Technology stack mismatch (HIGH, high probability)
  2. Tight timeline (HIGH, medium probability)
  3. Budget constraints (MEDIUM, medium probability)
- Deal-breakers: 1 (Technology mismatch)
- Risk score: 62.5/100
```

**Weighting Explanation**:

```
Example Risk: CRITICAL severity, HIGH probability
Calculation:
- Severity component: 1.0 × 60% = 0.60
- Probability component: 1.0 × 40% = 0.40
- Total: (0.60 + 0.40) × 100 = 100/100

Example Risk: MEDIUM severity, MEDIUM probability
Calculation:
- Severity component: 0.50 × 60% = 0.30
- Probability component: 0.6 × 40% = 0.24
- Total: (0.30 + 0.24) × 100 = 54/100
```

**Thresholds** (configurable):
```python
ScoringConfig.risk_thresholds:
├── low_maximum: 33.0
└── medium_maximum: 66.0
```

---

### 3. Effort Scoring

**Purpose**: Quantify project effort and resource requirements

**Input**:
```python
EffortEstimationOutput
├── total_estimated_hours: float
├── total_estimated_days: int
├── work_packages: List[WorkPackage]
│   ├── package_name: str
│   ├── estimated_hours: float
│   └── recommended_team_size: int
└── cost: CostEstimate
    ├── estimated_cost: float
    └── cost_per_hour: float
```

**Calculation**:

```
1. Extract metrics:
   - total_hours: from effort estimation
   - total_days: from timeline
   - team_size: sum of team sizes across work packages
   - cost: estimated project cost

2. Component 1 - Hours Score (0-100):
   - Low threshold: ≤ hours_low_max (e.g., 500h) → score=20
   - Medium threshold: ≤ hours_med_max (e.g., 1500h) → score=50
   - High: > hours_med_max → score = 50 + (excess/max_excess × 50)

3. Component 2 - Timeline Score (0-100):
   - Calculate team capacity: hours_per_week = team_size × 40
   - Estimate feasibility: weeks_needed / weeks_available
   - Apply thresholds similar to hours

4. Component 3 - Cost Score (0-100):
   - Compare to typical project budget (e.g., $50k)
   - Cost ratio = estimated_cost / typical_budget
   - Low: ≤30% ratio → score=20
   - Medium: ≤100% ratio → score=50
   - High: >100% ratio → scale up to 100

5. Weighted average:
   effort_score = (
       hours_score × hours_weight +
       timeline_score × timeline_weight +
       cost_score × cost_weight
   )
   Where weights default to: 50% hours, 30% timeline, 20% cost

6. Determine category:
   - LOW: 0-33
   - MEDIUM: 34-66
   - HIGH: 67-100

7. Output: EffortScore with metrics and reasoning
```

**Output**:
```python
EffortScore
├── effort_score: float (0-100)
├── effort_category: EffortCategory (LOW | MEDIUM | HIGH)
├── metrics: EffortMetrics
│   ├── total_hours: float
│   ├── total_days: int
│   ├── team_size: int
│   ├── estimated_cost: float
│   └── cost_per_hour: float
├── complexity_factors: List[str]
├── resource_needs: List[str]
├── scoring_logic: str (detailed explanation)
└── summary: str (executive summary)
```

**Example**:
```
Effort Profile: MEDIUM
- Hours: 850 hours
- Duration: 90 days
- Team: 4 people
- Cost: $85,000

Complexity factors:
- Significant effort: 850 hours
- Team size: 4 people
- Reasonable budget: $85,000

Resource needs:
- Team size: 4 people
- Duration: 90 calendar days
- Weekly commitment: 160 hours/week
- Cost: $85,000

Effort score: 48.5/100
```

**Thresholds** (configurable):
```python
ScoringConfig.effort_thresholds:
├── low_maximum_hours: 500.0
├── medium_maximum_hours: 1500.0
├── low_maximum_days: 30
├── medium_maximum_days: 90
└── typical_project_budget: 50000.0
```

---

### 4. Integrated Tender Score

**Purpose**: Combine all three dimensions into final bid recommendation

**Input**:
- EligibilityScore
- RiskScore
- EffortScore
- ScoringConfig (weights)

**Calculation**:

```
1. Normalize component scores to 0-1:
   - eligibility_normalized = eligibility_score / 100
   - risk_normalized = 1.0 - (risk_score / 100)  # Invert: high risk = low score
   - effort_normalized = 1.0 - (effort_score / 100)  # Invert: high effort = low score

2. Calculate weighted average:
   overall_score = (
       eligibility_normalized × eligibility_weight +
       risk_normalized × risk_weight +
       effort_normalized × effort_weight
   ) × 100
   
   Default weights:
   - Eligibility: 35%
   - Risk: 35%
   - Effort: 30%

3. Generate bid recommendation:
   
   Logic:
   IF not_eligible:
       recommendation = NO_BID
   ELSE IF (high_risk AND deal_breakers):
       recommendation = NO_BID
   ELSE IF (high_effort AND partially_eligible):
       recommendation = CONDITIONAL
   ELSE IF overall_score >= 75:
       recommendation = BID
   ELSE IF overall_score >= 50:
       recommendation = CONDITIONAL
   ELSE:
       recommendation = NO_BID

4. Identify strengths and weaknesses:
   - Strengths: What's going well (eligibility ✓, low risk, manageable effort)
   - Weaknesses: What needs attention (gaps, high risk, high effort)
   - Critical items: Top priorities for mitigation

5. Output: TenderScore with comprehensive analysis
```

**Output**:
```python
TenderScore
├── tender_id: str
├── eligibility: EligibilityScore
├── risk: RiskScore
├── effort: EffortScore
├── overall_score: float (0-100)
├── bid_recommendation: str (BID | NO_BID | CONDITIONAL)
├── recommendation_reasoning: str
├── scoring_summary: str
├── strengths: List[str]
├── weaknesses: List[str]
└── critical_items: List[str]
```

**Example**:
```
Tender ID: TENDER_2024_001

COMPONENT SCORES:
- Eligibility: 95% (ELIGIBLE)
- Risk: 35% (LOW)
- Effort: 48% (MEDIUM)

INTEGRATED SCORE: 78/100

BID RECOMMENDATION: BID

Reasoning:
- Strong eligibility: 95% of mandatory met
- Low risk profile: 2 low-severity risks
- Manageable effort: 850 hours over 90 days

Strengths:
✓ Meets all mandatory requirements
✓ Low risk profile (only 2 risks, both manageable)
✓ Reasonable effort: ~850 hours

Weaknesses:
- Medium timeline constraint (90 days)
- High team resource requirements (4 people)
- Cost at budget limit ($85k)

Critical Items:
- Address budget contingency (15% reserve recommended)
- Confirm team availability for 3-month engagement
```

**Weighting** (configurable):
```python
ScoringConfig:
├── eligibility_weight: 0.35  (35%)
├── risk_weight: 0.35         (35%)
└── effort_weight: 0.30       (30%)
```

---

## Configuration

### ScoringConfig Reference

```python
ScoringConfig(
    # Eligibility thresholds
    eligibility_thresholds=EligibilityThresholds(
        eligible_minimum=90.0,           # 90% = Eligible
        partially_eligible_minimum=70.0, # 70% = Partially Eligible
    ),
    
    # Risk thresholds
    risk_thresholds=RiskThresholds(
        low_maximum=33.0,    # 0-33 = Low
        medium_maximum=66.0, # 34-66 = Medium, 67+ = High
    ),
    
    # Risk component weights
    risk_severity_weight=0.6,  # 60% of impact from severity
    risk_probability_weight=0.4,  # 40% of impact from probability
    
    # Effort thresholds (hours)
    effort_thresholds=EffortThresholds(
        low_maximum_hours=500.0,
        medium_maximum_hours=1500.0,
        low_maximum_days=30,
        medium_maximum_days=90,
        typical_project_budget=50000.0,
    ),
    
    # Effort component weights
    effort_hours_weight=0.5,      # 50% from hours
    effort_timeline_weight=0.3,   # 30% from timeline feasibility
    effort_cost_weight=0.2,       # 20% from cost
    
    # Integrated scoring weights
    eligibility_weight=0.35,  # 35% in final score
    risk_weight=0.35,        # 35% in final score
    effort_weight=0.30,       # 30% in final score
)
```

### Customizing Weights

```python
from app.services.scoring_models import ScoringConfig

# Example: Lower risk tolerance
custom_config = ScoringConfig(
    risk_severity_weight=0.8,     # More weight to severity
    risk_probability_weight=0.2,  # Less weight to probability
    risk_weight=0.45,              # Increase risk weight in final score
)

from app.services.scoring_engine import TenderScoringEngine

engine = TenderScoringEngine(custom_config)
```

---

## Usage

### Basic Usage

```python
from app.services.scoring_engine import TenderScoringEngine
from app.services.ai_schemas import (
    EligibilityReasoningOutput,
    RiskIdentificationOutput,
    EffortEstimationOutput,
)

# Get analysis results from Step-7
eligibility_result = ...  # From EligibilityEvaluator
risk_result = ...         # From RiskAnalyzer
effort_result = ...       # From EffortEstimator

# Create scoring engine
engine = TenderScoringEngine()

# Score tender
tender_score = engine.score_tender(
    tender_id="TENDER_2024_001",
    eligibility_result=eligibility_result,
    risk_result=risk_result,
    effort_result=effort_result,
)

# Use results
print(f"Score: {tender_score.overall_score}/100")
print(f"Recommendation: {tender_score.bid_recommendation}")
print(f"Reasoning: {tender_score.recommendation_reasoning}")
print(f"Strengths: {tender_score.strengths}")
print(f"Weaknesses: {tender_score.weaknesses}")
```

### Individual Dimension Scoring

```python
from app.services.scoring_engine import (
    score_eligibility,
    score_risks,
    score_effort,
)

# Score individual dimensions
eligibility_score = score_eligibility(eligibility_result)
risk_score = score_risks(risk_result)
effort_score = score_effort(effort_result)

print(f"Eligibility: {eligibility_score.eligibility_score}% ({eligibility_score.category})")
print(f"Risk: {risk_score.risk_score}/100 ({risk_score.risk_category})")
print(f"Effort: {effort_score.effort_score}/100 ({effort_score.effort_category})")
```

### Custom Configuration

```python
from app.services.scoring_models import ScoringConfig

# Adjust for your organization
config = ScoringConfig(
    # More lenient eligibility
    eligibility_thresholds__eligible_minimum=80.0,
    
    # Risk-averse
    risk_weight=0.4,
    risk_severity_weight=0.7,
)

engine = TenderScoringEngine(config)
```

---

## Testing

### Running Unit Tests

```bash
cd backend
pytest tests/test_scoring_engine.py -v
```

### Test Coverage

```
✓ Eligibility Scorer (5 tests)
  - Eligible company
  - Partially eligible company
  - Not eligible company
  - Score is percentage (0-100)
  - Convenience function

✓ Risk Scorer (5 tests)
  - Low-risk tender
  - High-risk tender
  - Score is 0-100
  - Risk assessments created
  - Convenience function

✓ Effort Scorer (5 tests)
  - Low-effort tender
  - High-effort tender
  - Score is 0-100
  - Complexity factors identified
  - Convenience function

✓ Tender Scoring Engine (8 tests)
  - Strong BID recommendation
  - Strong NO_BID recommendation
  - Integrated score is 0-100
  - Recommendation reasoning provided
  - Strengths and weaknesses identified
  - Convenience function

✓ Determinism (4 tests)
  - Eligibility is deterministic
  - Risk scoring is deterministic
  - Effort scoring is deterministic
  - Tender scoring is deterministic

✓ Explainability (3 tests)
  - Eligibility includes explanation
  - Risk scoring includes explanation
  - Effort scoring includes explanation

✓ Edge Cases (3 tests)
  - Single requirement
  - No requirements
  - No risks

Total: 33 test cases, all passing
```

### Example Test

```python
def test_bid_recommendation_green_light():
    """Test strong BID recommendation"""
    
    # Setup: Eligible company, low risk, low effort
    eligibility = EligibilityReasoningOutput(...)
    risk = RiskIdentificationOutput(...)
    effort = EffortEstimationOutput(...)
    
    # Execute
    engine = TenderScoringEngine()
    tender_score = engine.score_tender("TENDER_001", eligibility, risk, effort)
    
    # Assert
    assert tender_score.bid_recommendation == "BID"
    assert tender_score.overall_score >= 75
```

---

## Integration with Step-7

### Pipeline Flow

```
Step-7: AI Extraction
├─ TenderAnalyzer
│  ├─ extract_clauses() → ClauseExtractionOutput
│  ├─ evaluate_eligibility() → EligibilityReasoningOutput
│  ├─ analyze_risks() → RiskIdentificationOutput
│  └─ estimate_effort() → EffortEstimationOutput
│
Step-8: Scoring
├─ TenderScoringEngine.score_tender()
│  ├─ EligibilityScorer → EligibilityScore
│  ├─ RiskScorer → RiskScore
│  ├─ EffortScorer → EffortScore
│  └─ Combine → TenderScore + Recommendation
│
Output: BID/NO_BID/CONDITIONAL Decision
```

### Example Integration

```python
from app.services.tender_analyzer import TenderAnalyzer
from app.services.scoring_engine import TenderScoringEngine

# Step 7: Analyze tender
analyzer = TenderAnalyzer()
analysis = analyzer.analyze(tender_chunks, tender_id)

# Step 8: Score tender
scorer = TenderScoringEngine()
tender_score = scorer.score_tender(
    tender_id=tender_id,
    eligibility_result=analysis.eligibility,
    risk_result=analysis.risks,
    effort_result=analysis.effort,
)

# Make decision
if tender_score.bid_recommendation == "BID":
    # Proceed with bid
    proceed_with_bid(tender_score)
elif tender_score.bid_recommendation == "CONDITIONAL":
    # Flag for review
    flag_for_review(tender_score)
else:
    # Decline bid
    decline_bid(tender_score)
```

---

## Key Formulas

### Eligibility Score

```
Overall % = (Total Met / Total Requirements) × 100

Category Decision (based on Mandatory %):
- IF Mandatory % >= 90%  → ELIGIBLE
- ELSE IF Mandatory % >= 70% → PARTIALLY_ELIGIBLE
- ELSE → NOT_ELIGIBLE
```

### Risk Score

```
For each risk:
  Impact = (
    Severity_Weight × Severity_Factor +
    Probability_Weight × Probability_Factor
  ) × 100

Risk_Score = Average(All Impacts) (clamped 0-100)

Category Decision:
- IF Risk_Score <= 33  → LOW
- ELSE IF Risk_Score <= 66  → MEDIUM
- ELSE → HIGH
```

### Effort Score

```
Hours_Score = Scale(total_hours, thresholds)
Timeline_Score = Scale(weeks_needed/weeks_available, thresholds)
Cost_Score = Scale(cost/typical_budget, thresholds)

Effort_Score = (
  Hours_Score × 0.5 +
  Timeline_Score × 0.3 +
  Cost_Score × 0.2
)

Category Decision:
- IF Effort_Score <= 33  → LOW
- ELSE IF Effort_Score <= 66  → MEDIUM
- ELSE → HIGH
```

### Overall Tender Score

```
Eligibility_Norm = Eligibility_Score / 100
Risk_Norm = 1.0 - (Risk_Score / 100)  # Inverted
Effort_Norm = 1.0 - (Effort_Score / 100)  # Inverted

Overall_Score = (
  Eligibility_Norm × 0.35 +
  Risk_Norm × 0.35 +
  Effort_Norm × 0.30
) × 100
```

---

## Data Models

### Input Models

**EligibilityReasoningOutput**
```python
tender_id: str
requirement_evaluations: List[RequirementEvaluation]
eligibility_determination: str
```

**RiskIdentificationOutput**
```python
tender_id: str
total_risks_identified: int
critical_risks: int
high_risks: int
medium_risks: int
low_risks: int
risks: List[RiskAssessmentItem]
```

**EffortEstimationOutput**
```python
tender_id: str
total_estimated_hours: float
total_estimated_days: int
work_packages: List[WorkPackage]
cost: CostEstimate
```

### Output Models

**EligibilityScore**
```python
tender_id: str
eligibility_score: float (0-100)
category: EligibilityCategory
mandatory_percentage: float
overall_percentage: float
requirements_assessments: List[EligibilityRequirementAssessment]
scoring_logic: str
summary: str
```

**RiskScore**
```python
tender_id: str
risk_score: float (0-100)
risk_category: RiskCategory
total_risks: int
critical_count: int
high_count: int
risk_assessments: List[RiskAssessment]
scoring_logic: str
summary: str
```

**EffortScore**
```python
tender_id: str
effort_score: float (0-100)
effort_category: EffortCategory
metrics: EffortMetrics
complexity_factors: List[str]
resource_needs: List[str]
scoring_logic: str
summary: str
```

**TenderScore**
```python
tender_id: str
overall_score: float (0-100)
bid_recommendation: str (BID | NO_BID | CONDITIONAL)
recommendation_reasoning: str
eligibility: EligibilityScore
risk: RiskScore
effort: EffortScore
strengths: List[str]
weaknesses: List[str]
critical_items: List[str]
```

---

## Best Practices

### 1. Always Include Context

```python
# ✓ Good: Provides context
tender_score = scorer.score_tender(
    tender_id="TENDER_2024_001",
    eligibility_result=eligibility,
    risk_result=risks,
    effort_result=effort,
)

# ✗ Avoid: Missing context
score = scorer.score_tender(...)
```

### 2. Validate Input Before Scoring

```python
# ✓ Good: Validate inputs
if not eligibility_result.requirement_evaluations:
    logger.warning("No requirements evaluated")

scorer = EligibilityScorer()
score = scorer.score(eligibility_result)

# ✗ Avoid: Assuming valid data
score = scorer.score(eligibility_result)  # May fail silently
```

### 3. Review Scores with Explanations

```python
# ✓ Good: Show reasoning
print(f"Score: {score.overall_score}")
print(f"Explanation: {score.scoring_logic}")

# ✗ Avoid: Using score without context
if score.overall_score > 50:
    proceed()  # Why? Where did 50 come from?
```

### 4. Customize Config for Your Organization

```python
# ✓ Good: Documented custom config
config = ScoringConfig(
    risk_severity_weight=0.7,  # More risk-averse
    effort_weight=0.4,         # High cost sensitivity
)
# Document why these weights matter for your team

# ✗ Avoid: Changing defaults without documentation
config = ScoringConfig()
config.risk_severity_weight = 0.7  # Why?
```

### 5. Log Scoring Decisions

```python
# ✓ Good: Log for audit trail
logger.info(f"Tender {tender_id} scored: {score.bid_recommendation}")
logger.debug(f"Details: {score.recommendation_reasoning}")

# ✗ Avoid: Silent decisions
return score  # No audit trail
```

---

## Troubleshooting

### Issue: Score doesn't match expectations

**Diagnosis**:
1. Check `scoring_logic` field - shows exact calculation
2. Review `requirement_evaluations` - verify inputs
3. Confirm `ScoringConfig` weights

**Example**:
```python
score = scorer.score(result)
print(score.scoring_logic)  # Shows: "mandatory_met=2/3, %=66.7%"
```

### Issue: Recommendation seems wrong

**Check**:
1. View `bid_recommendation` and `recommendation_reasoning`
2. Look at component scores: `eligibility`, `risk`, `effort`
3. Review `critical_items` - what's blocking?

**Example**:
```python
print(f"Recommendation: {score.bid_recommendation}")
print(f"Reasoning: {score.recommendation_reasoning}")
print(f"Critical: {score.critical_items}")
```

### Issue: Inconsistent scores

**Verify**:
1. Same input? (determinism should apply)
2. Same config? (weights affect results)
3. Same Step-7 output? (inputs changed?)

**Test**:
```python
# Determinism check
score1 = scorer.score(result)
score2 = scorer.score(result)
assert score1.overall_score == score2.overall_score  # Should pass
```

---

## Performance Notes

- **Eligibility Scoring**: O(n) where n = number of requirements (typically 5-20)
- **Risk Scoring**: O(r) where r = number of risks (typically 3-10)
- **Effort Scoring**: O(p) where p = number of work packages (typically 3-5)
- **Total Scoring**: < 100ms for typical tender

No external API calls (deterministic calculations only)

---

## Future Enhancements

Potential improvements for future versions:

1. **Learning from Bid Outcomes**
   - Track actual outcomes vs. recommendations
   - Auto-calibrate thresholds based on win rate

2. **Machine Learning Scoring**
   - Train models on historical tender data
   - Predict win probability based on score profiles

3. **Advanced Risk Modeling**
   - Consider risk correlations
   - Scenario analysis (best/worst case)

4. **Portfolio Optimization**
   - Score tenders relative to portfolio strategy
   - Resource conflict detection

5. **Sensitivity Analysis**
   - Show impact of each component on final score
   - "What-if" scenarios

---

## Support

For questions about:
- **Scoring logic**: See "Key Formulas" section
- **Configuration**: See "Configuration" section
- **Testing**: See "Testing" section
- **Integration**: See "Integration with Step-7" section

