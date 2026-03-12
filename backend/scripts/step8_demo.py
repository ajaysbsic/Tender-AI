"""
Step-8 Scoring Engine Demo

Demonstrates all scoring features with synthetic tender data.
Run: python step8_demo.py
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Ensure backend root is importable when running from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.scoring_engine import TenderScoringEngine
from app.services.scoring_models import ScoringConfig
from app.services.ai_schemas import (
    RequirementEvaluation,
    EligibilityReasoningOutput,
    RiskIdentificationOutput,
    RiskAssessmentItem,
    WorkPackage,
    CostEstimate,
    EffortEstimationOutput,
)


def create_demo_eligibility() -> EligibilityReasoningOutput:
    """Create demo eligibility evaluation"""
    
    return EligibilityReasoningOutput(
        tender_id="TENDER_2024_001",
        requirement_evaluations=[
            RequirementEvaluation(
                requirement_id="R1_mandatory",
                requirement_text="ISO 9001 Certification",
                company_meets=True,
                reasoning="Company has valid ISO 9001:2015 certification since 2020",
                confidence=0.95,
            ),
            RequirementEvaluation(
                requirement_id="R2_mandatory",
                requirement_text="Minimum 5 years of experience in similar projects",
                company_meets=True,
                reasoning="Company founded in 2015, extensive portfolio in similar domains",
                confidence=0.92,
            ),
            RequirementEvaluation(
                requirement_id="R3_mandatory",
                requirement_text="Team size greater than 10 people",
                company_meets=True,
                reasoning="Current team size: 15 people (8 engineers, 4 PMs, 3 ops)",
                confidence=0.98,
            ),
            RequirementEvaluation(
                requirement_id="R4_mandatory",
                requirement_text="Experience with cloud infrastructure (AWS/Azure)",
                company_meets=True,
                reasoning="AWS certified team, 3+ years of cloud project experience",
                confidence=0.90,
            ),
            RequirementEvaluation(
                requirement_id="R5_optional",
                requirement_text="Government security clearance for team leads",
                company_meets=False,
                reasoning="No current government clearances, can apply if required",
                confidence=0.85,
            ),
            RequirementEvaluation(
                requirement_id="R6_optional",
                requirement_text="Demonstrated track record with Fortune 500 clients",
                company_meets=True,
                reasoning="Has worked with 3 Fortune 500 companies on similar projects",
                confidence=0.88,
            ),
        ],
        eligibility_determination="Company appears eligible for bid participation",
    )


def create_demo_risks() -> RiskIdentificationOutput:
    """Create demo risk assessment"""
    
    return RiskIdentificationOutput(
        tender_id="TENDER_2024_001",
        total_risks_identified=5,
        critical_risks=1,
        high_risks=1,
        medium_risks=2,
        low_risks=1,
        risks=[
            RiskAssessmentItem(
                risk_title="Technology Stack Compatibility",
                severity="critical",
                probability="high",
                deal_breaker=True,
                mitigation="Requires proof-of-concept phase"
            ),
            RiskAssessmentItem(
                risk_title="Tight Project Timeline",
                severity="high",
                probability="high",
                deal_breaker=False,
                mitigation="Requires extended team and overtime budget"
            ),
            RiskAssessmentItem(
                risk_title="Budget Constraints",
                severity="medium",
                probability="medium",
                deal_breaker=False,
                mitigation="Negotiate scope or timeline adjustment"
            ),
            RiskAssessmentItem(
                risk_title="Stakeholder Alignment Issues",
                severity="medium",
                probability="low",
                deal_breaker=False,
                mitigation="Early engagement with all stakeholders"
            ),
            RiskAssessmentItem(
                risk_title="Resource Availability",
                severity="low",
                probability="low",
                deal_breaker=False,
                mitigation="Maintain bench strength for flex capacity"
            ),
        ],
    )


def create_demo_effort() -> EffortEstimationOutput:
    """Create demo effort estimation"""
    
    return EffortEstimationOutput(
        tender_id="TENDER_2024_001",
        total_estimated_hours=1200,
        total_estimated_days=120,
        work_packages=[
            WorkPackage(
                package_name="Phase 1: Requirements & Architecture",
                estimated_hours=250,
                recommended_team_size=3,
            ),
            WorkPackage(
                package_name="Phase 2: Core Development",
                estimated_hours=600,
                recommended_team_size=4,
            ),
            WorkPackage(
                package_name="Phase 3: Testing & QA",
                estimated_hours=200,
                recommended_team_size=2,
            ),
            WorkPackage(
                package_name="Phase 4: Deployment & Handoff",
                estimated_hours=150,
                recommended_team_size=2,
            ),
        ],
        cost=CostEstimate(
            estimated_cost=120000,
            cost_per_hour=100.0,
        ),
    )


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")


def print_subsection(title: str):
    """Print formatted subsection header"""
    print(f"\n{title}")
    print(f"{'-'*60}\n")


def demo_individual_scoring():
    """Demonstrate individual dimension scoring"""
    
    print_section("STEP-8: TENDER SCORING ENGINE DEMO")
    
    # Create demo data
    eligibility = create_demo_eligibility()
    risks = create_demo_risks()
    effort = create_demo_effort()
    
    # Create engine
    engine = TenderScoringEngine()
    
    # Demo 1: Eligibility Scoring
    print_subsection("1. ELIGIBILITY SCORING")
    
    eligibility_score = engine.eligibility_scorer.score(eligibility)
    print(f"Tender ID: {eligibility_score.tender_id}")
    print(f"Category: {eligibility_score.category.value.upper()}")
    print(f"Eligibility Score: {eligibility_score.eligibility_score:.1f}%")
    print(f"\nBreakdown:")
    print(f"  Total Requirements: {eligibility_score.total_requirements}")
    print(f"  Mandatory: {eligibility_score.mandatory_requirements}")
    print(f"  Optional: {eligibility_score.optional_requirements}")
    print(f"  Total Met: {eligibility_score.total_met}")
    print(f"  Mandatory Met: {eligibility_score.mandatory_met}")
    print(f"  Mandatory Percentage: {eligibility_score.mandatory_percentage:.1f}%")
    
    print(f"\nMet Requirements:")
    for req in eligibility_score.met_requirements[:5]:
        print(f"  ✓ {req}")
    
    if eligibility_score.unmet_requirements:
        print(f"\nUnmet Requirements:")
        for req in eligibility_score.unmet_requirements:
            print(f"  ✗ {req}")
    
    print(f"\nSummary: {eligibility_score.summary}")
    
    # Demo 2: Risk Scoring
    print_subsection("2. RISK SCORING")
    
    risk_score = engine.risk_scorer.score(risks)
    print(f"Tender ID: {risk_score.tender_id}")
    print(f"Category: {risk_score.risk_category.value.upper()}")
    print(f"Risk Score: {risk_score.risk_score:.1f}/100")
    print(f"\nBreakdown:")
    print(f"  Total Risks: {risk_score.total_risks}")
    print(f"  Critical: {risk_score.critical_count}")
    print(f"  High: {risk_score.high_count}")
    print(f"  Medium: {risk_score.medium_count}")
    print(f"  Low: {risk_score.low_count}")
    
    print(f"\nTop Risks:")
    for i, risk in enumerate(risk_score.top_risks, 1):
        print(f"  {i}. {risk}")
    
    if risk_score.deal_breakers:
        print(f"\nDeal-Breaker Risks:")
        for db in risk_score.deal_breakers:
            print(f"  🚫 {db}")
    
    print(f"\nSummary: {risk_score.summary}")
    
    # Demo 3: Effort Scoring
    print_subsection("3. EFFORT SCORING")
    
    effort_score = engine.effort_scorer.score(effort)
    print(f"Tender ID: {effort_score.tender_id}")
    print(f"Category: {effort_score.effort_category.value.upper()}")
    print(f"Effort Score: {effort_score.effort_score:.1f}/100")
    print(f"\nMetrics:")
    print(f"  Total Hours: {effort_score.metrics.total_hours:.0f}")
    print(f"  Timeline: {effort_score.metrics.total_days} days")
    print(f"  Team Size: {effort_score.metrics.team_size} people")
    print(f"  Estimated Cost: ${effort_score.metrics.estimated_cost:,.0f}")
    print(f"  Cost per Hour: ${effort_score.metrics.cost_per_hour:.2f}")
    
    print(f"\nComplexity Factors:")
    for factor in effort_score.complexity_factors:
        print(f"  • {factor}")
    
    print(f"\nResource Needs:")
    for need in effort_score.resource_needs:
        print(f"  • {need}")
    
    print(f"\nSummary: {effort_score.summary}")


def demo_integrated_scoring():
    """Demonstrate integrated tender scoring"""
    
    print_section("INTEGRATED TENDER SCORING")
    
    # Create demo data
    eligibility = create_demo_eligibility()
    risks = create_demo_risks()
    effort = create_demo_effort()
    
    # Create engine and score
    engine = TenderScoringEngine()
    tender_score = engine.score_tender(
        tender_id="TENDER_2024_001",
        eligibility_result=eligibility,
        risk_result=risks,
        effort_result=effort,
    )
    
    # Overall score
    print_subsection("OVERALL ASSESSMENT")
    print(f"Tender ID: {tender_score.tender_id}")
    print(f"Overall Score: {tender_score.overall_score:.1f}/100")
    print(f"Bid Recommendation: {tender_score.bid_recommendation.upper()}")
    
    print(f"\nComponent Scores:")
    print(f"  Eligibility: {tender_score.eligibility.eligibility_score:.1f}% ({tender_score.eligibility.category.value})")
    print(f"  Risk: {tender_score.risk.risk_score:.1f}/100 ({tender_score.risk.risk_category.value})")
    print(f"  Effort: {tender_score.effort.effort_score:.1f}/100 ({tender_score.effort.effort_category.value})")
    
    print(f"\nRecommendation Reasoning:")
    print(f"  {tender_score.recommendation_reasoning}")
    
    print(f"\nStrengths:")
    for strength in tender_score.strengths:
        print(f"  ✓ {strength}")
    
    print(f"\nWeaknesses:")
    for weakness in tender_score.weaknesses:
        print(f"  ⚠ {weakness}")
    
    if tender_score.critical_items:
        print(f"\nCritical Items:")
        for item in tender_score.critical_items:
            print(f"  🔴 {item}")
    
    print(f"\n{'─'*60}")
    print(f"DECISION: {tender_score.bid_recommendation.upper()}")
    print(f"{'─'*60}")


def demo_custom_config():
    """Demonstrate custom configuration"""
    
    print_section("CUSTOM CONFIGURATION EXAMPLE")
    
    print("Creating risk-averse configuration...")
    print("  - Higher weight on risk dimension (40% instead of 35%)")
    print("  - More weight to severity in risk calculation (70% instead of 60%)")
    print("  - Stricter eligibility threshold (95% instead of 90%)\n")
    
    # Custom config for risk-averse organization
    custom_config = ScoringConfig(
        # Risk aversion
        risk_weight=0.40,            # Increase from 35%
        risk_severity_weight=0.70,   # Increase from 60%
        
        # Stricter eligibility
        eligibility_thresholds__eligible_minimum=95.0,  # Increase from 90%
    )
    
    # Score with custom config
    eligibility = create_demo_eligibility()
    risks = create_demo_risks()
    effort = create_demo_effort()
    
    engine = TenderScoringEngine(custom_config)
    tender_score = engine.score_tender(
        tender_id="TENDER_2024_001_CUSTOM",
        eligibility_result=eligibility,
        risk_result=risks,
        effort_result=effort,
    )
    
    print("Results with Custom Configuration:")
    print(f"  Overall Score: {tender_score.overall_score:.1f}/100")
    print(f"  Bid Recommendation: {tender_score.bid_recommendation}")
    print(f"  Eligibility Category: {tender_score.eligibility.category.value}")
    
    print(f"\nNote: Risk-averse config prioritizes risk management,")
    print(f"resulting in more conservative scoring and recommendations.")


def demo_explanation_output():
    """Demonstrate detailed scoring explanations"""
    
    print_section("DETAILED SCORING EXPLANATIONS")
    
    # Create demo data
    eligibility = create_demo_eligibility()
    risks = create_demo_risks()
    effort = create_demo_effort()
    
    # Score
    engine = TenderScoringEngine()
    tender_score = engine.score_tender(
        tender_id="TENDER_2024_001",
        eligibility_result=eligibility,
        risk_result=risks,
        effort_result=effort,
    )
    
    # Show scoring logic for each dimension
    print_subsection("ELIGIBILITY SCORING LOGIC")
    print(tender_score.eligibility.scoring_logic)
    
    print_subsection("RISK SCORING LOGIC")
    print(tender_score.risk.scoring_logic)
    
    print_subsection("EFFORT SCORING LOGIC")
    print(tender_score.effort.scoring_logic)


def demo_unit_testing():
    """Demonstrate unit testing capabilities"""
    
    print_section("UNIT TESTING DEMONSTRATION")
    
    print("Testing Determinism: Running same score twice...\n")
    
    eligibility = create_demo_eligibility()
    risks = create_demo_risks()
    effort = create_demo_effort()
    
    engine = TenderScoringEngine()
    
    # Score twice
    score1 = engine.score_tender("TENDER_001", eligibility, risks, effort)
    score2 = engine.score_tender("TENDER_001", eligibility, risks, effort)
    
    # Compare
    print(f"First Run:")
    print(f"  Overall Score: {score1.overall_score:.1f}")
    print(f"  Recommendation: {score1.bid_recommendation}")
    
    print(f"\nSecond Run:")
    print(f"  Overall Score: {score2.overall_score:.1f}")
    print(f"  Recommendation: {score2.bid_recommendation}")
    
    print(f"\nDeterminism Check:")
    if score1.overall_score == score2.overall_score:
        print(f"  ✓ PASS: Scores are identical (deterministic)")
    else:
        print(f"  ✗ FAIL: Scores differ (non-deterministic)")
    
    if score1.bid_recommendation == score2.bid_recommendation:
        print(f"  ✓ PASS: Recommendations match (deterministic)")
    else:
        print(f"  ✗ FAIL: Recommendations differ (non-deterministic)")


def main():
    """Run all demonstrations"""
    
    try:
        # Individual scoring
        demo_individual_scoring()
        
        # Integrated scoring
        demo_integrated_scoring()
        
        # Custom configuration
        demo_custom_config()
        
        # Detailed explanations
        demo_explanation_output()
        
        # Unit testing
        demo_unit_testing()
        
        # Summary
        print_section("SUMMARY")
        print("✓ Eligibility Scoring: Determines if company meets mandatory requirements")
        print("✓ Risk Scoring: Quantifies project risk exposure")
        print("✓ Effort Scoring: Assesses project effort and resource requirements")
        print("✓ Integrated Scoring: Combines dimensions for bid/no-bid decision")
        print("✓ Configuration: Customizable thresholds and weights")
        print("✓ Testing: All scores deterministic and well-explained")
        print("\nFor full test suite: pytest tests/test_scoring_engine.py -v")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
