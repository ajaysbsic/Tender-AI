"""
Unit tests for Scoring Engine - Step-8

Tests all scoring components with synthetic data.
Ensures deterministic, explainable scoring.
"""

import pytest
from datetime import datetime

from app.services.scoring_engine import (
    EligibilityScorer,
    RiskScorer,
    EffortScorer,
    TenderScoringEngine,
    score_eligibility,
    score_risks,
    score_effort,
    score_tender,
)
from app.services.scoring_models import (
    EligibilityCategory,
    RiskCategory,
    EffortCategory,
    ScoringConfig,
)
from app.services.ai_schemas import (
    RequirementEvaluation,
    EligibilityReasoningOutput,
    RiskIdentificationOutput,
    RiskAssessmentItem,
    WorkPackage,
    CostEstimate,
    EffortEstimationOutput,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def basic_scoring_config():
    """Basic scoring configuration"""
    return ScoringConfig()


@pytest.fixture
def eligible_requirements():
    """All requirements met"""
    return [
        RequirementEvaluation(
            requirement_id="R1_mandatory",
            requirement_text="ISO 9001 Certification",
            company_meets=True,
            reasoning="Company has valid certification",
            confidence=0.95,
        ),
        RequirementEvaluation(
            requirement_id="R2_mandatory",
            requirement_text="5+ Years Experience",
            company_meets=True,
            reasoning="Company founded in 2015",
            confidence=0.95,
        ),
        RequirementEvaluation(
            requirement_id="R3_optional",
            requirement_text="Cloud Infrastructure",
            company_meets=True,
            reasoning="AWS certified",
            confidence=0.90,
        ),
    ]


@pytest.fixture
def partially_eligible_requirements():
    """Some requirements met"""
    return [
        RequirementEvaluation(
            requirement_id="R1_mandatory",
            requirement_text="ISO 9001 Certification",
            company_meets=True,
            reasoning="Company has valid certification",
            confidence=0.95,
        ),
        RequirementEvaluation(
            requirement_id="R2_mandatory",
            requirement_text="5+ Years Experience",
            company_meets=False,
            reasoning="Company only 3 years old",
            confidence=0.95,
        ),
        RequirementEvaluation(
            requirement_id="R3_optional",
            requirement_text="Cloud Infrastructure",
            company_meets=True,
            reasoning="AWS certified",
            confidence=0.90,
        ),
    ]


@pytest.fixture
def not_eligible_requirements():
    """Most requirements not met"""
    return [
        RequirementEvaluation(
            requirement_id="R1_mandatory",
            requirement_text="ISO 9001 Certification",
            company_meets=False,
            reasoning="No certification",
            confidence=0.95,
        ),
        RequirementEvaluation(
            requirement_id="R2_mandatory",
            requirement_text="5+ Years Experience",
            company_meets=False,
            reasoning="Company only 1 year old",
            confidence=0.95,
        ),
        RequirementEvaluation(
            requirement_id="R3_mandatory",
            requirement_text="Team size > 10",
            company_meets=False,
            reasoning="Team only 5 people",
            confidence=0.95,
        ),
    ]


@pytest.fixture
def low_risk_tender():
    """Tender with low risks"""
    return RiskIdentificationOutput(
        tender_id="TENDER_001",
        total_risks_identified=2,
        critical_risks=0,
        high_risks=0,
        medium_risks=1,
        low_risks=1,
        risks=[
            RiskAssessmentItem(
                risk_title="Minor documentation requirement",
                severity="low",
                probability="low",
                deal_breaker=False,
            ),
            RiskAssessmentItem(
                risk_title="Standard timeline",
                severity="medium",
                probability="low",
                deal_breaker=False,
            ),
        ],
    )


@pytest.fixture
def high_risk_tender():
    """Tender with high risks"""
    return RiskIdentificationOutput(
        tender_id="TENDER_002",
        total_risks_identified=3,
        critical_risks=1,
        high_risks=1,
        medium_risks=1,
        low_risks=0,
        risks=[
            RiskAssessmentItem(
                risk_title="Critical technology gap",
                severity="critical",
                probability="high",
                deal_breaker=True,
            ),
            RiskAssessmentItem(
                risk_title="Unrealistic timeline",
                severity="high",
                probability="high",
                deal_breaker=False,
            ),
            RiskAssessmentItem(
                risk_title="Budget constraints",
                severity="medium",
                probability="medium",
                deal_breaker=False,
            ),
        ],
    )


@pytest.fixture
def low_effort_tender():
    """Tender with low effort"""
    return EffortEstimationOutput(
        tender_id="TENDER_001",
        total_estimated_hours=300,
        total_estimated_days=30,
        work_packages=[
            WorkPackage(
                package_name="Phase 1: Design",
                estimated_hours=100,
                recommended_team_size=2,
            ),
            WorkPackage(
                package_name="Phase 2: Development",
                estimated_hours=150,
                recommended_team_size=2,
            ),
            WorkPackage(
                package_name="Phase 3: Testing",
                estimated_hours=50,
                recommended_team_size=1,
            ),
        ],
        cost=CostEstimate(
            estimated_cost=25000,
            cost_per_hour=83.33,
        ),
    )


@pytest.fixture
def high_effort_tender():
    """Tender with high effort"""
    return EffortEstimationOutput(
        tender_id="TENDER_003",
        total_estimated_hours=2500,
        total_estimated_days=180,
        work_packages=[
            WorkPackage(
                package_name="Phase 1: Requirements & Design",
                estimated_hours=800,
                recommended_team_size=3,
            ),
            WorkPackage(
                package_name="Phase 2: Development",
                estimated_hours=1200,
                recommended_team_size=4,
            ),
            WorkPackage(
                package_name="Phase 3: QA & Deployment",
                estimated_hours=500,
                recommended_team_size=2,
            ),
        ],
        cost=CostEstimate(
            estimated_cost=250000,
            cost_per_hour=100.0,
        ),
    )


# ============================================================================
# ELIGIBILITY SCORER TESTS
# ============================================================================

class TestEligibilityScorer:
    """Test eligibility scoring"""
    
    def test_eligible_company(self, basic_scoring_config, eligible_requirements):
        """Test scoring for eligible company"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible for bid",
        )
        
        scorer = EligibilityScorer(basic_scoring_config)
        score = scorer.score(result)
        
        assert score.tender_id == "TENDER_001"
        assert score.category == EligibilityCategory.ELIGIBLE
        assert score.eligibility_score == 100.0
        assert score.total_requirements == 3
        assert score.total_met == 3
        assert len(score.met_requirements) == 3
        assert len(score.critical_gaps) == 0
    
    def test_partially_eligible_company(self, basic_scoring_config, partially_eligible_requirements):
        """Test scoring for partially eligible company"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_002",
            requirement_evaluations=partially_eligible_requirements,
            eligibility_determination="Partially eligible",
        )
        
        scorer = EligibilityScorer(basic_scoring_config)
        score = scorer.score(result)
        
        assert score.tender_id == "TENDER_002"
        assert score.category == EligibilityCategory.PARTIALLY_ELIGIBLE
        assert 70 <= score.eligibility_score < 100
        assert score.total_met == 2
        assert len(score.critical_gaps) >= 0
    
    def test_not_eligible_company(self, basic_scoring_config, not_eligible_requirements):
        """Test scoring for ineligible company"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_003",
            requirement_evaluations=not_eligible_requirements,
            eligibility_determination="Not eligible",
        )
        
        scorer = EligibilityScorer(basic_scoring_config)
        score = scorer.score(result)
        
        assert score.tender_id == "TENDER_003"
        assert score.category == EligibilityCategory.NOT_ELIGIBLE
        assert score.eligibility_score < 70
        assert score.total_met < score.total_requirements
    
    def test_eligibility_score_is_percentage(self, basic_scoring_config, eligible_requirements):
        """Test that eligibility score is 0-100 percentage"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        scorer = EligibilityScorer(basic_scoring_config)
        score = scorer.score(result)
        
        assert 0 <= score.eligibility_score <= 100
    
    def test_convenience_function(self, eligible_requirements):
        """Test convenience function"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        score = score_eligibility(result)
        
        assert score.tender_id == "TENDER_001"
        assert score.category == EligibilityCategory.ELIGIBLE


# ============================================================================
# RISK SCORER TESTS
# ============================================================================

class TestRiskScorer:
    """Test risk scoring"""
    
    def test_low_risk_tender(self, basic_scoring_config, low_risk_tender):
        """Test scoring for low-risk tender"""
        
        scorer = RiskScorer(basic_scoring_config)
        score = scorer.score(low_risk_tender)
        
        assert score.tender_id == "TENDER_001"
        assert score.risk_category == RiskCategory.LOW
        assert score.risk_score <= 33
        assert score.total_risks == 2
        assert score.critical_count == 0
    
    def test_high_risk_tender(self, basic_scoring_config, high_risk_tender):
        """Test scoring for high-risk tender"""
        
        scorer = RiskScorer(basic_scoring_config)
        score = scorer.score(high_risk_tender)
        
        assert score.tender_id == "TENDER_002"
        assert score.risk_category == RiskCategory.HIGH
        assert score.risk_score >= 67
        assert score.total_risks == 3
        assert score.critical_count == 1
        assert len(score.deal_breakers) == 1
    
    def test_risk_score_is_0_to_100(self, basic_scoring_config, low_risk_tender):
        """Test that risk score is 0-100"""
        
        scorer = RiskScorer(basic_scoring_config)
        score = scorer.score(low_risk_tender)
        
        assert 0 <= score.risk_score <= 100
    
    def test_risk_assessments_created(self, basic_scoring_config, low_risk_tender):
        """Test that individual risk assessments are created"""
        
        scorer = RiskScorer(basic_scoring_config)
        score = scorer.score(low_risk_tender)
        
        assert len(score.risk_assessments) == len(low_risk_tender.risks)
        for assessment in score.risk_assessments:
            assert 0 <= assessment.impact_score <= 100
    
    def test_convenience_function(self, low_risk_tender):
        """Test convenience function"""
        
        score = score_risks(low_risk_tender)
        
        assert score.tender_id == "TENDER_001"
        assert score.risk_category == RiskCategory.LOW


# ============================================================================
# EFFORT SCORER TESTS
# ============================================================================

class TestEffortScorer:
    """Test effort scoring"""
    
    def test_low_effort_tender(self, basic_scoring_config, low_effort_tender):
        """Test scoring for low-effort tender"""
        
        scorer = EffortScorer(basic_scoring_config)
        score = scorer.score(low_effort_tender)
        
        assert score.tender_id == "TENDER_001"
        assert score.effort_category == EffortCategory.LOW
        assert score.effort_score <= 33
        assert score.metrics.total_hours == 300
    
    def test_high_effort_tender(self, basic_scoring_config, high_effort_tender):
        """Test scoring for high-effort tender"""
        
        scorer = EffortScorer(basic_scoring_config)
        score = scorer.score(high_effort_tender)
        
        assert score.tender_id == "TENDER_003"
        assert score.effort_category == EffortCategory.HIGH
        assert score.effort_score >= 67
        assert score.metrics.total_hours == 2500
    
    def test_effort_score_is_0_to_100(self, basic_scoring_config, low_effort_tender):
        """Test that effort score is 0-100"""
        
        scorer = EffortScorer(basic_scoring_config)
        score = scorer.score(low_effort_tender)
        
        assert 0 <= score.effort_score <= 100
    
    def test_effort_score_includes_complexity(self, basic_scoring_config, high_effort_tender):
        """Test that complexity factors are identified"""
        
        scorer = EffortScorer(basic_scoring_config)
        score = scorer.score(high_effort_tender)
        
        assert len(score.complexity_factors) > 0
    
    def test_convenience_function(self, low_effort_tender):
        """Test convenience function"""
        
        score = score_effort(low_effort_tender)
        
        assert score.tender_id == "TENDER_001"
        assert score.effort_category == EffortCategory.LOW


# ============================================================================
# TENDER SCORING ENGINE TESTS
# ============================================================================

class TestTenderScoringEngine:
    """Test integrated tender scoring"""
    
    def test_bid_recommendation_green_light(
        self,
        basic_scoring_config,
        eligible_requirements,
        low_risk_tender,
        low_effort_tender,
    ):
        """Test strong BID recommendation"""
        
        eligibility = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        engine = TenderScoringEngine(basic_scoring_config)
        tender_score = engine.score_tender(
            "TENDER_001",
            eligibility,
            low_risk_tender,
            low_effort_tender,
        )
        
        assert tender_score.tender_id == "TENDER_001"
        assert tender_score.overall_score >= 60
        assert tender_score.bid_recommendation in ["BID", "CONDITIONAL"]
    
    def test_no_bid_recommendation_red_light(
        self,
        basic_scoring_config,
        not_eligible_requirements,
        high_risk_tender,
        high_effort_tender,
    ):
        """Test strong NO_BID recommendation"""
        
        eligibility = EligibilityReasoningOutput(
            tender_id="TENDER_002",
            requirement_evaluations=not_eligible_requirements,
            eligibility_determination="Not eligible",
        )
        
        engine = TenderScoringEngine(basic_scoring_config)
        tender_score = engine.score_tender(
            "TENDER_002",
            eligibility,
            high_risk_tender,
            high_effort_tender,
        )
        
        assert tender_score.tender_id == "TENDER_002"
        assert tender_score.bid_recommendation in ["NO_BID", "CONDITIONAL"]
    
    def test_integrated_score_is_0_to_100(
        self,
        basic_scoring_config,
        eligible_requirements,
        low_risk_tender,
        low_effort_tender,
    ):
        """Test that integrated score is 0-100"""
        
        eligibility = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        engine = TenderScoringEngine(basic_scoring_config)
        tender_score = engine.score_tender(
            "TENDER_001",
            eligibility,
            low_risk_tender,
            low_effort_tender,
        )
        
        assert 0 <= tender_score.overall_score <= 100
    
    def test_recommendation_reasoning_provided(
        self,
        basic_scoring_config,
        eligible_requirements,
        low_risk_tender,
        low_effort_tender,
    ):
        """Test that reasoning is provided"""
        
        eligibility = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        engine = TenderScoringEngine(basic_scoring_config)
        tender_score = engine.score_tender(
            "TENDER_001",
            eligibility,
            low_risk_tender,
            low_effort_tender,
        )
        
        assert len(tender_score.recommendation_reasoning) > 0
        assert ";" in tender_score.recommendation_reasoning  # Multiple factors
    
    def test_strengths_and_weaknesses_identified(
        self,
        basic_scoring_config,
        eligible_requirements,
        low_risk_tender,
        low_effort_tender,
    ):
        """Test that strengths and weaknesses are identified"""
        
        eligibility = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        engine = TenderScoringEngine(basic_scoring_config)
        tender_score = engine.score_tender(
            "TENDER_001",
            eligibility,
            low_risk_tender,
            low_effort_tender,
        )
        
        assert len(tender_score.strengths) > 0
        assert len(tender_score.weaknesses) >= 0
    
    def test_convenience_function(
        self,
        eligible_requirements,
        low_risk_tender,
        low_effort_tender,
    ):
        """Test convenience function"""
        
        eligibility = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        tender_score = score_tender(
            "TENDER_001",
            eligibility,
            low_risk_tender,
            low_effort_tender,
        )
        
        assert tender_score.tender_id == "TENDER_001"
        assert 0 <= tender_score.overall_score <= 100


# ============================================================================
# DETERMINISM TESTS
# ============================================================================

class TestDeterminism:
    """Verify that scoring is deterministic (same input = same output)"""
    
    def test_eligibility_scoring_deterministic(self, basic_scoring_config, eligible_requirements):
        """Eligibility scoring should be deterministic"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        scorer = EligibilityScorer(basic_scoring_config)
        
        # Score twice
        score1 = scorer.score(result)
        score2 = scorer.score(result)
        
        # Results should be identical
        assert score1.eligibility_score == score2.eligibility_score
        assert score1.category == score2.category
    
    def test_risk_scoring_deterministic(self, basic_scoring_config, low_risk_tender):
        """Risk scoring should be deterministic"""
        
        scorer = RiskScorer(basic_scoring_config)
        
        # Score twice
        score1 = scorer.score(low_risk_tender)
        score2 = scorer.score(low_risk_tender)
        
        # Results should be identical
        assert score1.risk_score == score2.risk_score
        assert score1.risk_category == score2.risk_category
    
    def test_effort_scoring_deterministic(self, basic_scoring_config, low_effort_tender):
        """Effort scoring should be deterministic"""
        
        scorer = EffortScorer(basic_scoring_config)
        
        # Score twice
        score1 = scorer.score(low_effort_tender)
        score2 = scorer.score(low_effort_tender)
        
        # Results should be identical
        assert score1.effort_score == score2.effort_score
        assert score1.effort_category == score2.effort_category
    
    def test_tender_scoring_deterministic(
        self,
        basic_scoring_config,
        eligible_requirements,
        low_risk_tender,
        low_effort_tender,
    ):
        """Tender scoring should be deterministic"""
        
        eligibility = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        engine = TenderScoringEngine(basic_scoring_config)
        
        # Score twice
        score1 = engine.score_tender("TENDER_001", eligibility, low_risk_tender, low_effort_tender)
        score2 = engine.score_tender("TENDER_001", eligibility, low_risk_tender, low_effort_tender)
        
        # Results should be identical
        assert score1.overall_score == score2.overall_score
        assert score1.bid_recommendation == score2.bid_recommendation


# ============================================================================
# EXPLAINABILITY TESTS
# ============================================================================

class TestExplainability:
    """Verify that scoring provides clear explanations"""
    
    def test_eligibility_scoring_includes_explanation(self, basic_scoring_config, eligible_requirements):
        """Eligibility score includes reasoning"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=eligible_requirements,
            eligibility_determination="Eligible",
        )
        
        scorer = EligibilityScorer(basic_scoring_config)
        score = scorer.score(result)
        
        assert len(score.scoring_logic) > 0
        assert "Thresholds" in score.scoring_logic
        assert "%" in score.scoring_logic
    
    def test_risk_scoring_includes_explanation(self, basic_scoring_config, low_risk_tender):
        """Risk score includes reasoning"""
        
        scorer = RiskScorer(basic_scoring_config)
        score = scorer.score(low_risk_tender)
        
        assert len(score.scoring_logic) > 0
        assert "Weighting" in score.scoring_logic
        assert "Severity" in score.scoring_logic
    
    def test_effort_scoring_includes_explanation(self, basic_scoring_config, low_effort_tender):
        """Effort score includes reasoning"""
        
        scorer = EffortScorer(basic_scoring_config)
        score = scorer.score(low_effort_tender)
        
        assert len(score.scoring_logic) > 0
        assert "Components" in score.scoring_logic
        assert "Weighted" in score.scoring_logic


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_single_requirement(self, basic_scoring_config):
        """Test with single requirement"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=[
                RequirementEvaluation(
                    requirement_id="R1",
                    requirement_text="Certification",
                    company_meets=True,
                    reasoning="Certified",
                    confidence=1.0,
                ),
            ],
            eligibility_determination="Eligible",
        )
        
        scorer = EligibilityScorer(basic_scoring_config)
        score = scorer.score(result)
        
        assert score.total_requirements == 1
        assert score.total_met == 1
    
    def test_no_requirements(self, basic_scoring_config):
        """Test with no requirements"""
        
        result = EligibilityReasoningOutput(
            tender_id="TENDER_001",
            requirement_evaluations=[],
            eligibility_determination="Unknown",
        )
        
        scorer = EligibilityScorer(basic_scoring_config)
        score = scorer.score(result)
        
        assert score.total_requirements == 0
        assert score.overall_percentage == 0
    
    def test_no_risks(self, basic_scoring_config):
        """Test with no identified risks"""
        
        risk = RiskIdentificationOutput(
            tender_id="TENDER_001",
            total_risks_identified=0,
            critical_risks=0,
            high_risks=0,
            medium_risks=0,
            low_risks=0,
            risks=[],
        )
        
        scorer = RiskScorer(basic_scoring_config)
        score = scorer.score(risk)
        
        assert score.total_risks == 0
        assert score.risk_score == 0  # No risk
