"""
Scoring Models - Step-8

Pydantic models for scoring engine outputs.
All models include explainability and reasoning.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class EligibilityCategory(str, Enum):
    """Eligibility verdict categories"""
    ELIGIBLE = "eligible"
    PARTIALLY_ELIGIBLE = "partially_eligible"
    NOT_ELIGIBLE = "not_eligible"


class RiskCategory(str, Enum):
    """Risk severity categories"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EffortCategory(str, Enum):
    """Effort/complexity categories"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# ELIGIBILITY SCORING
# ============================================================================

class EligibilityRequirementAssessment(BaseModel):
    """Assessment of a single requirement"""
    requirement_id: str = Field(..., description="Requirement identifier")
    requirement_text: str = Field(..., description="Requirement text")
    is_mandatory: bool = Field(..., description="Is requirement mandatory?")
    company_meets: bool = Field(..., description="Does company meet requirement?")
    reasoning: str = Field(..., description="Why or why not")
    confidence: float = Field(..., ge=0, le=1, description="Confidence 0-1")


class EligibilityScore(BaseModel):
    """Comprehensive eligibility score"""
    tender_id: str = Field(..., description="Tender ID")
    
    # Counts
    total_requirements: int = Field(..., description="Total requirements")
    mandatory_requirements: int = Field(..., description="Mandatory count")
    optional_requirements: int = Field(..., description="Optional count")
    
    # Met counts
    total_met: int = Field(..., description="Total requirements met")
    mandatory_met: int = Field(..., description="Mandatory requirements met")
    optional_met: int = Field(..., description="Optional requirements met")
    
    # Percentages
    overall_percentage: float = Field(..., ge=0, le=100, description="Overall %")
    mandatory_percentage: float = Field(..., ge=0, le=100, description="Mandatory %")
    
    # Category
    category: EligibilityCategory = Field(..., description="Eligible/Partially/Not")
    
    # Score
    eligibility_score: float = Field(..., ge=0, le=100, description="Score 0-100")
    
    # Details
    requirements_assessments: List[EligibilityRequirementAssessment] = Field(
        ..., description="Individual requirement assessments"
    )
    
    # Reasoning
    scoring_logic: str = Field(..., description="How score was calculated")
    summary: str = Field(..., description="Executive summary")
    met_requirements: List[str] = Field(..., description="Requirements met")
    unmet_requirements: List[str] = Field(..., description="Requirements not met")
    critical_gaps: List[str] = Field(default_factory=list, description="Critical gaps")


# ============================================================================
# RISK SCORING
# ============================================================================

class RiskAssessment(BaseModel):
    """Assessment of a single risk"""
    risk_id: str = Field(..., description="Risk identifier")
    risk_title: str = Field(..., description="Risk title")
    severity: str = Field(..., description="critical/high/medium/low")
    probability: str = Field(..., description="low/medium/high")
    impact_score: float = Field(..., ge=0, le=100, description="0-100 impact")


class RiskScore(BaseModel):
    """Comprehensive risk score"""
    tender_id: str = Field(..., description="Tender ID")
    
    # Risk counts
    total_risks: int = Field(..., description="Total risks identified")
    critical_count: int = Field(..., description="Critical severity count")
    high_count: int = Field(..., description="High severity count")
    medium_count: int = Field(..., description="Medium severity count")
    low_count: int = Field(..., description="Low severity count")
    
    # Probability distribution
    high_probability_count: int = Field(..., description="High probability count")
    medium_probability_count: int = Field(..., description="Medium probability count")
    low_probability_count: int = Field(..., description="Low probability count")
    
    # Score
    risk_score: float = Field(..., ge=0, le=100, description="Risk score 0-100")
    risk_category: RiskCategory = Field(..., description="Low/Medium/High")
    
    # Weights used in calculation
    severity_weights: Dict[str, float] = Field(
        ..., description="Weights for each severity level"
    )
    probability_weights: Dict[str, float] = Field(
        ..., description="Weights for each probability"
    )
    
    # Details
    risk_assessments: List[RiskAssessment] = Field(..., description="Individual risks")
    
    # Reasoning
    scoring_logic: str = Field(..., description="How score was calculated")
    summary: str = Field(..., description="Executive summary")
    top_risks: List[str] = Field(..., description="Top 3 risks by impact")
    deal_breakers: List[str] = Field(default_factory=list, description="Deal-breaker risks")


# ============================================================================
# EFFORT SCORING
# ============================================================================

class EffortMetrics(BaseModel):
    """Effort metrics"""
    total_hours: float = Field(..., description="Total estimated hours")
    total_days: float = Field(..., description="Total calendar days")
    team_size: int = Field(..., description="Recommended team size")
    estimated_cost: float = Field(..., description="Estimated cost")
    cost_per_hour: float = Field(..., description="Average cost per hour")


class EffortScore(BaseModel):
    """Comprehensive effort score"""
    tender_id: str = Field(..., description="Tender ID")
    
    # Metrics
    metrics: EffortMetrics = Field(..., description="Effort metrics")
    
    # Thresholds used
    low_threshold_hours: float = Field(..., description="Hours threshold for LOW")
    medium_threshold_hours: float = Field(..., description="Hours threshold for MEDIUM")
    high_threshold_hours: float = Field(..., description="Hours threshold for HIGH")
    
    # Score
    effort_score: float = Field(..., ge=0, le=100, description="Score 0-100")
    effort_category: EffortCategory = Field(..., description="Low/Medium/High")
    
    # Breakdown
    hours_percentage: float = Field(..., description="% of effort score from hours")
    timeline_percentage: float = Field(..., description="% of effort score from timeline")
    cost_percentage: float = Field(..., description="% of effort score from cost")
    
    # Reasoning
    scoring_logic: str = Field(..., description="How score was calculated")
    summary: str = Field(..., description="Executive summary")
    complexity_factors: List[str] = Field(..., description="Key complexity drivers")
    resource_needs: List[str] = Field(..., description="Resource needs identified")


# ============================================================================
# INTEGRATED TENDER SCORE
# ============================================================================

class TenderScore(BaseModel):
    """Integrated scoring for tender"""
    tender_id: str = Field(..., description="Tender ID")
    
    # Individual scores
    eligibility: EligibilityScore = Field(..., description="Eligibility score")
    risk: RiskScore = Field(..., description="Risk score")
    effort: EffortScore = Field(..., description="Effort score")
    
    # Integrated score
    overall_score: float = Field(..., ge=0, le=100, description="Overall score 0-100")
    
    # Bid readiness
    bid_recommendation: str = Field(
        ..., description="BID/NO_BID/CONDITIONAL"
    )
    
    # Reasoning
    recommendation_reasoning: str = Field(..., description="Why this recommendation")
    scoring_summary: str = Field(..., description="Summary of all scores")
    
    # Key insights
    strengths: List[str] = Field(..., description="Key strengths")
    weaknesses: List[str] = Field(..., description="Key weaknesses")
    critical_items: List[str] = Field(..., description="Critical action items")


# ============================================================================
# SCORING CONFIGURATION
# ============================================================================

class EligibilityThresholds(BaseModel):
    """Eligibility score thresholds"""
    eligible_minimum: float = Field(default=90.0, description="% for Eligible")
    partially_eligible_minimum: float = Field(
        default=70.0, description="% for Partially Eligible"
    )
    # Below partially_eligible_minimum = Not Eligible


class RiskThresholds(BaseModel):
    """Risk score thresholds"""
    low_maximum: float = Field(default=33.0, description="Max score for Low risk")
    medium_maximum: float = Field(default=66.0, description="Max score for Medium risk")
    # Above medium_maximum = High risk


class EffortThresholds(BaseModel):
    """Effort score thresholds"""
    low_maximum_hours: float = Field(default=500.0, description="Max hours for Low effort")
    medium_maximum_hours: float = Field(default=1500.0, description="Max hours for Medium")
    # Above medium_maximum = High effort


class ScoringConfig(BaseModel):
    """Configuration for scoring engine"""
    eligibility_thresholds: EligibilityThresholds = Field(
        default_factory=EligibilityThresholds,
        description="Eligibility thresholds"
    )
    risk_thresholds: RiskThresholds = Field(
        default_factory=RiskThresholds,
        description="Risk thresholds"
    )
    effort_thresholds: EffortThresholds = Field(
        default_factory=EffortThresholds,
        description="Effort thresholds"
    )
    
    # Weights for integrated scoring (sum to 1.0)
    eligibility_weight: float = Field(default=0.35, description="Eligibility weight")
    risk_weight: float = Field(default=0.35, description="Risk weight")
    effort_weight: float = Field(default=0.30, description="Effort weight")
    
    # Risk weighting (sum to 1.0)
    risk_severity_weight: float = Field(default=0.60, description="Severity component")
    risk_probability_weight: float = Field(default=0.40, description="Probability component")
    
    # Effort weighting
    effort_hours_weight: float = Field(default=0.50, description="Hours component")
    effort_timeline_weight: float = Field(default=0.30, description="Timeline component")
    effort_cost_weight: float = Field(default=0.20, description="Cost component")


# ============================================================================
# VALIDATION & UTILITIES
# ============================================================================

def validate_weights(config: ScoringConfig) -> bool:
    """Validate that weights sum to 1.0"""
    eligibility_sum = config.eligibility_weight + config.risk_weight + config.effort_weight
    risk_sum = config.risk_severity_weight + config.risk_probability_weight
    effort_sum = config.effort_hours_weight + config.effort_timeline_weight + config.effort_cost_weight
    
    return (
        abs(eligibility_sum - 1.0) < 0.01 and
        abs(risk_sum - 1.0) < 0.01 and
        abs(effort_sum - 1.0) < 0.01
    )
