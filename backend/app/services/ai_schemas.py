"""
JSON Schemas for Step-7 AI Extraction Outputs

Structured output models for LLM-based analysis.
All outputs are strictly JSON with no summarization.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class RiskLevel(str, Enum):
    """Risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffortLevel(str, Enum):
    """Effort/complexity levels"""
    TRIVIAL = "trivial"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============================================================================
# CLAUSE EXTRACTION SCHEMAS
# ============================================================================

class ClauseRequirement(BaseModel):
    """Individual requirement from a clause"""
    requirement_text: str = Field(..., description="Exact requirement statement")
    type: str = Field(..., description="Type: mandatory, recommended, optional")
    category: str = Field(..., description="Category: deliverable, timeline, quality, cost, etc.")
    measurable: bool = Field(..., description="Whether requirement is measurable/testable")
    metric: Optional[str] = Field(None, description="Measurement criteria if measurable")


class ExtractedClause(BaseModel):
    """Extracted clause with parsed information"""
    clause_number: str = Field(..., description="Clause number/reference")
    clause_title: str = Field(..., description="Clause title/heading")
    raw_text: str = Field(..., description="Original clause text")
    requirements: List[ClauseRequirement] = Field(..., description="Parsed requirements")
    key_terms: List[str] = Field(..., description="Important terms and keywords")
    penalty_applies: bool = Field(..., description="Whether penalties apply if not met")
    penalty_description: Optional[str] = Field(None, description="Description of penalties")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other clauses")


class ClauseExtractionOutput(BaseModel):
    """Complete clause extraction result"""
    tender_id: str = Field(..., description="Tender ID")
    total_clauses_found: int = Field(..., description="Total number of clauses")
    clauses: List[ExtractedClause] = Field(..., description="Extracted clauses")
    extraction_confidence: float = Field(..., ge=0, le=1, description="Overall extraction confidence 0-1")
    extraction_notes: List[str] = Field(default_factory=list, description="Notes about extraction process")


# ============================================================================
# ELIGIBILITY REASONING SCHEMAS
# ============================================================================

class EligibilityRequirement(BaseModel):
    """Single eligibility requirement from tender"""
    requirement_id: str = Field(..., description="Requirement ID")
    requirement_text: str = Field(..., description="Full requirement text")
    category: str = Field(..., description="Category: experience, certification, financial, legal, technical")
    is_mandatory: bool = Field(..., description="Whether requirement is mandatory")
    specificity: str = Field(..., description="Level: general, specific, measurable")


class CompanyCapability(BaseModel):
    """Company's capability for a requirement"""
    capability_name: str = Field(..., description="Capability name")
    level: str = Field(..., description="Level: none, basic, intermediate, expert")
    supporting_evidence: str = Field(..., description="Evidence from company profile")
    years_relevant: int = Field(..., description="Years of relevant experience")


class RequirementEvaluation(BaseModel):
    """Evaluation of one eligibility requirement against company"""
    requirement_id: str = Field(..., description="Requirement ID")
    requirement_text: str = Field(..., description="Requirement text")
    company_meets: bool = Field(..., description="Does company meet requirement? T/F")
    reasoning: str = Field(..., description="Detailed reasoning for decision (clause-level analysis)")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in assessment 0-1")
    required_capability: str = Field(..., description="Capability needed")
    company_capability_level: str = Field(..., description="Company's capability level")
    gap_description: Optional[str] = Field(None, description="Gap if requirement not met")
    recommendation: str = Field(..., description="Action recommendation (accept/conditional/reject/clarify)")


class EligibilityReasoningOutput(BaseModel):
    """Complete eligibility evaluation result"""
    tender_id: str = Field(..., description="Tender ID")
    company_profile: Dict[str, Any] = Field(..., description="Company profile summary")
    total_requirements: int = Field(..., description="Total eligibility requirements")
    total_met: int = Field(..., description="Number of requirements met")
    total_not_met: int = Field(..., description="Number of requirements not met")
    total_conditional: int = Field(..., description="Number of conditional requirements")
    requirement_evaluations: List[RequirementEvaluation] = Field(..., description="Individual evaluations")
    overall_eligibility_verdict: str = Field(..., description="Overall verdict: eligible, partially_eligible, not_eligible")
    eligibility_score: float = Field(..., ge=0, le=100, description="Eligibility score 0-100")
    critical_gaps: List[str] = Field(default_factory=list, description="Critical gaps that block bid")
    recommendable_gaps: List[str] = Field(default_factory=list, description="Gaps that can be addressed")


# ============================================================================
# RISK IDENTIFICATION SCHEMAS
# ============================================================================

class IdentifiedRisk(BaseModel):
    """Single identified risk from tender analysis"""
    risk_id: str = Field(..., description="Unique risk ID")
    risk_category: str = Field(..., description="Category: contractual, timeline, financial, technical, legal, reputational")
    risk_title: str = Field(..., description="Short risk title")
    risk_description: str = Field(..., description="Detailed risk description (clause-level analysis)")
    source_clause: str = Field(..., description="Clause where risk originates")
    severity: RiskLevel = Field(..., description="Risk severity")
    probability: str = Field(..., description="Probability: low, medium, high")
    impact_if_occurs: str = Field(..., description="What happens if risk occurs")
    
    # Mitigation
    mitigations: List[str] = Field(..., description="Possible mitigation strategies")
    can_mitigate: bool = Field(..., description="Can risk be mitigated before signing?")
    mitigation_cost: Optional[str] = Field(None, description="Estimated cost to mitigate")
    
    # Business impact
    business_impact: str = Field(..., description="Impact on business: project delay, budget increase, legal liability, reputation damage")
    deal_breaker: bool = Field(..., description="Is this a deal-breaker risk?")


class RiskIdentificationOutput(BaseModel):
    """Complete risk analysis result"""
    tender_id: str = Field(..., description="Tender ID")
    analysis_scope: str = Field(..., description="What was analyzed: all risks, top 10, by category, etc.")
    total_risks_identified: int = Field(..., description="Total risks found")
    
    # Risk breakdown
    critical_risks: int = Field(..., description="Count of critical risks")
    high_risks: int = Field(..., description="Count of high risks")
    medium_risks: int = Field(..., description="Count of medium risks")
    low_risks: int = Field(..., description="Count of low risks")
    
    # Risk details
    risks: List[IdentifiedRisk] = Field(..., description="Detailed risk list")
    
    # Summary
    overall_risk_level: RiskLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0, le=100, description="Overall risk score 0-100 (higher=riskier)")
    deal_breaker_risks: List[str] = Field(default_factory=list, description="Deal-breaker risk IDs")
    top_mitigations: List[str] = Field(default_factory=list, description="Top recommended mitigations")


# ============================================================================
# EFFORT ESTIMATION SCHEMAS
# ============================================================================

class WorkPackage(BaseModel):
    """Work package for estimation"""
    package_id: str = Field(..., description="Package ID")
    package_name: str = Field(..., description="Package name")
    description: str = Field(..., description="Package description")
    dependencies: List[str] = Field(default_factory=list, description="Dependent packages")
    source_requirements: List[str] = Field(..., description="Requirements this package fulfills")


class EffortEstimate(BaseModel):
    """Effort estimate for a work package"""
    package_id: str = Field(..., description="Work package ID")
    package_name: str = Field(..., description="Package name")
    
    # Effort metrics
    estimated_hours: float = Field(..., description="Estimated effort in hours")
    effort_range_low: float = Field(..., description="Low estimate in hours")
    effort_range_high: float = Field(..., description="High estimate in hours")
    effort_level: EffortLevel = Field(..., description="Complexity level")
    
    # Reasoning
    estimation_basis: str = Field(..., description="Basis for estimation (clause-level analysis)")
    key_drivers: List[str] = Field(..., description="Key complexity drivers")
    assumptions: List[str] = Field(..., description="Assumptions in estimation")
    risks_affecting_effort: List[str] = Field(..., description="Risks that could affect effort")
    
    # Skills/Resources
    required_skills: List[str] = Field(..., description="Required skills")
    recommended_team_size: int = Field(..., description="Recommended team size")
    required_specialists: List[str] = Field(..., description="Specialist roles needed")


class TimelineEstimate(BaseModel):
    """Project timeline estimate"""
    total_duration_days: float = Field(..., description="Total project duration in days")
    duration_range_days: Dict[str, float] = Field(..., description="Duration range {min, max}")
    critical_path_duration_days: float = Field(..., description="Critical path duration")
    
    # Phases
    phases: List[Dict[str, Any]] = Field(..., description="Project phases with durations")
    
    # Buffers
    contingency_percentage: float = Field(..., ge=0, le=100, description="Recommended contingency %")
    total_with_contingency_days: float = Field(..., description="Total duration with contingency")


class CostEstimate(BaseModel):
    """Cost estimate"""
    estimated_cost: float = Field(..., description="Estimated total cost")
    cost_range_low: float = Field(..., description="Low cost estimate")
    cost_range_high: float = Field(..., description="High cost estimate")
    currency: str = Field(default="USD", description="Currency")
    
    # Breakdown
    labor_cost: float = Field(..., description="Labor cost")
    tools_licenses_cost: float = Field(..., description="Tools and licenses cost")
    infrastructure_cost: float = Field(..., description="Infrastructure cost")
    contingency_cost: float = Field(..., description="Contingency/buffer cost")
    
    # Details
    cost_per_hour: float = Field(..., description="Average labor cost per hour")
    estimation_basis: str = Field(..., description="Basis for cost estimation")


class EffortEstimationOutput(BaseModel):
    """Complete effort estimation result"""
    tender_id: str = Field(..., description="Tender ID")
    project_name: str = Field(..., description="Project name from tender")
    
    # Overview
    total_estimated_hours: float = Field(..., description="Total estimated hours")
    total_estimated_days: float = Field(..., description="Total estimated calendar days")
    overall_effort_level: EffortLevel = Field(..., description="Overall effort level")
    
    # Details
    work_packages: List[EffortEstimate] = Field(..., description="Work package estimates")
    timeline: TimelineEstimate = Field(..., description="Timeline estimate")
    cost: CostEstimate = Field(..., description="Cost estimate")
    
    # Key insights
    major_complexity_areas: List[str] = Field(..., description="Areas of high complexity")
    effort_drivers: List[str] = Field(..., description="Main effort drivers")
    key_assumptions: List[str] = Field(..., description="Key estimation assumptions")
    risks_to_estimate: List[str] = Field(..., description="Risks affecting estimate")
    
    # Confidence
    estimation_confidence: float = Field(..., ge=0, le=1, description="Confidence in estimates 0-1")
    confidence_notes: str = Field(..., description="Notes on confidence level")


# ============================================================================
# INTEGRATED ANALYSIS SCHEMA
# ============================================================================

class TenderAnalysisIntegration(BaseModel):
    """Integrated result combining all analyses"""
    tender_id: str = Field(..., description="Tender ID")
    
    # Component results
    clauses: ClauseExtractionOutput = Field(..., description="Clause extraction")
    eligibility: EligibilityReasoningOutput = Field(..., description="Eligibility evaluation")
    risks: RiskIdentificationOutput = Field(..., description="Risk analysis")
    effort: EffortEstimationOutput = Field(..., description="Effort estimation")
    
    # Integrated decision
    overall_recommendation: str = Field(..., description="BID/NO_BID/CONDITIONAL")
    go_no_go_reasoning: str = Field(..., description="Reasoning for recommendation")
    
    # Key metrics
    bid_feasibility_score: float = Field(..., ge=0, le=100, description="Feasibility score")
    risk_adjusted_score: float = Field(..., ge=0, le=100, description="Risk-adjusted score")
    
    # Executive summary (NOT summarization, but structured key points)
    key_strengths: List[str] = Field(..., description="Company strengths for this bid")
    key_weaknesses: List[str] = Field(..., description="Company weaknesses for this bid")
    critical_success_factors: List[str] = Field(..., description="What's critical to succeed")
    must_dos_before_bid: List[str] = Field(..., description="Must-dos before submitting bid")


# ============================================================================
# UTILITY SCHEMAS
# ============================================================================

class ExtractionError(BaseModel):
    """Error in extraction"""
    error_type: str = Field(..., description="Type: parsing_error, content_error, llm_error, validation_error")
    error_message: str = Field(..., description="Error message")
    affected_component: str = Field(..., description="Which component had the error")
    partial_result: Optional[Dict] = Field(None, description="Partial result if available")


class ExtractionMetadata(BaseModel):
    """Metadata about extraction process"""
    extraction_timestamp: str = Field(..., description="When extraction occurred")
    llm_model_used: str = Field(..., description="LLM model used")
    llm_tokens_used: int = Field(..., description="Total tokens used")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    extraction_version: str = Field(default="1.0", description="Extraction schema version")


def get_json_schema(model_class):
    """Get JSON schema for a model class"""
    return model_class.model_json_schema()


def validate_output(model_class, data: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate output against schema.
    
    Returns: (is_valid, error_message)
    """
    try:
        model_class(**data)
        return True, None
    except Exception as e:
        return False, str(e)
