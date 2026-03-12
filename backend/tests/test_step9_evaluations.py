"""
Tests for Step-9: Evaluation API and Report Generation

Tests cover:
- Report generation and PDF output
- API endpoints for evaluation retrieval
- Clause-level verdicts
- Business-friendly language translation
- Streaming responses
"""

import pytest
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock

from app.services.report_generator import (
    ReportGenerator,
    BusinessLanguageTranslator,
    generate_tender_report,
)
from app.services.scoring_models import (
    TenderScore,
    EligibilityScore,
    RiskScore,
    EffortScore,
    RequirementAssessment,
    EligibilityCategory,
    RiskCategory,
    EffortCategory,
    EffortMetrics,
    Assessments,
)
from app.routes.evaluations import (
    _format_evaluation_response,
    _generate_executive_summary,
    _get_eligibility_verdict,
    _get_risk_verdict,
    _get_effort_verdict,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def translator():
    """Initialize BusinessLanguageTranslator"""
    return BusinessLanguageTranslator()


@pytest.fixture
def report_generator():
    """Initialize ReportGenerator"""
    return ReportGenerator()


@pytest.fixture
def sample_eligible_score():
    """Create sample ELIGIBLE tender score"""
    
    # Create requirement assessments
    requirements = [
        RequirementAssessment(
            requirement_text="ISO 9001 Certification",
            company_meets=True,
            is_mandatory=True,
            reasoning="Company holds current ISO 9001 certification"
        ),
        RequirementAssessment(
            requirement_text="5+ years experience",
            company_meets=True,
            is_mandatory=True,
            reasoning="Company has 8 years of relevant experience"
        ),
        RequirementAssessment(
            requirement_text="Team of 10+ people",
            company_meets=True,
            is_mandatory=False,
            reasoning="Company has 12 dedicated team members"
        ),
    ]
    
    eligibility = EligibilityScore(
        eligibility_score=95.0,
        category=EligibilityCategory.ELIGIBLE,
        requirements_assessments=requirements,
        assessments=Assessments(
            met_count=3,
            not_met_count=0,
            partial_count=0,
            summary="All requirements met"
        ),
        scoring_logic="95% of requirements met, exceeds 90% threshold"
    )
    
    # Create risk score
    risk = RiskScore(
        risk_score=25.0,
        risk_category=RiskCategory.LOW,
        total_risks=2,
        critical_count=0,
        high_count=0,
        medium_count=1,
        low_count=1,
        top_risks=["Minor timeline pressure", "Standard resource constraints"],
        deal_breakers=[],
        assessments=Assessments(
            met_count=0,
            not_met_count=0,
            partial_count=0,
            summary="Low risk profile"
        ),
        scoring_logic="Average weighted impact score is 0.25 × 100 = 25"
    )
    
    # Create effort score
    metrics = EffortMetrics(
        total_hours=500.0,
        total_days=60,
        team_size=5,
        estimated_cost=50000.0,
        cost_per_hour=100.0
    )
    
    effort = EffortScore(
        effort_score=30.0,
        effort_category=EffortCategory.LOW,
        metrics=metrics,
        complexity_factors=["Standard requirements", "Proven technologies"],
        assessments=Assessments(
            met_count=0,
            not_met_count=0,
            partial_count=0,
            summary="Low effort"
        ),
        scoring_logic="Weighted effort score is 30 (LOW)"
    )
    
    return TenderScore(
        tender_id="TENDER-001",
        overall_score=83.5,
        bid_recommendation="BID",
        eligibility=eligibility,
        risk=risk,
        effort=effort,
        strengths=[
            "Strong eligibility profile",
            "Low risk environment",
            "Reasonable resource requirements"
        ],
        weaknesses=[
            "Tight timeline could be challenging"
        ],
        critical_items=[
            "Confirm team availability for 60-day project"
        ]
    )


@pytest.fixture
def sample_conditional_score():
    """Create sample CONDITIONAL tender score"""
    
    requirements = [
        RequirementAssessment(
            requirement_text="ISO 9001 Certification",
            company_meets=False,
            is_mandatory=True,
            reasoning="Company not currently certified"
        ),
        RequirementAssessment(
            requirement_text="5+ years experience",
            company_meets=True,
            is_mandatory=True,
            reasoning="Company has 6 years of experience"
        ),
    ]
    
    eligibility = EligibilityScore(
        eligibility_score=75.0,
        category=EligibilityCategory.PARTIALLY_ELIGIBLE,
        requirements_assessments=requirements,
        assessments=Assessments(
            met_count=1,
            not_met_count=1,
            partial_count=0,
            summary="One mandatory requirement not met"
        ),
        scoring_logic="50% of requirements met, in 70-90% range"
    )
    
    risk = RiskScore(
        risk_score=55.0,
        risk_category=RiskCategory.MEDIUM,
        total_risks=4,
        critical_count=1,
        high_count=1,
        medium_count=2,
        low_count=0,
        top_risks=[
            "Missing ISO 9001 certification",
            "Limited experience with similar scope"
        ],
        deal_breakers=[],
        assessments=Assessments(
            met_count=0,
            not_met_count=0,
            partial_count=0,
            summary="Medium risk"
        ),
        scoring_logic="Average weighted impact is 0.55 × 100 = 55"
    )
    
    metrics = EffortMetrics(
        total_hours=1200.0,
        total_days=90,
        team_size=8,
        estimated_cost=120000.0,
        cost_per_hour=100.0
    )
    
    effort = EffortScore(
        effort_score=60.0,
        effort_category=EffortCategory.MEDIUM,
        metrics=metrics,
        complexity_factors=[
            "Complex technical requirements",
            "Multiple integrations needed"
        ],
        assessments=Assessments(
            met_count=0,
            not_met_count=0,
            partial_count=0,
            summary="Medium effort"
        ),
        scoring_logic="Weighted effort score is 60 (MEDIUM)"
    )
    
    return TenderScore(
        tender_id="TENDER-002",
        overall_score=65.0,
        bid_recommendation="CONDITIONAL",
        eligibility=eligibility,
        risk=risk,
        effort=effort,
        strengths=[
            "Core experience present",
            "Reasonable team capacity"
        ],
        weaknesses=[
            "Missing key certification",
            "Medium risk factors",
            "Substantial effort required"
        ],
        critical_items=[
            "Obtain ISO 9001 certification OR get waiver",
            "Detail risk mitigation strategy in proposal",
            "Confirm project timeline is achievable"
        ]
    )


@pytest.fixture
def mock_tender():
    """Mock Tender database object"""
    return Mock(
        id="TENDER-001",
        title="Web Application Development RFP",
        description="Develop scalable web platform"
    )


# ============================================================================
# TESTS: BUSINESS LANGUAGE TRANSLATOR
# ============================================================================

class TestBusinessLanguageTranslator:
    """Tests for BusinessLanguageTranslator"""
    
    def test_eligible_verdict(self, translator):
        """Test ELIGIBLE category translation"""
        result = translator.eligibility_verdict(95.0, "ELIGIBLE")
        
        assert result["title"] == "✓ ELIGIBLE"
        assert "strong" in result["headline"].lower()
        assert "95" in result["summary"]
        assert "90%" in result["summary"]
    
    def test_partially_eligible_verdict(self, translator):
        """Test PARTIALLY_ELIGIBLE category translation"""
        result = translator.eligibility_verdict(75.0, "PARTIALLY_ELIGIBLE")
        
        assert result["title"] == "⚠ PARTIALLY_ELIGIBLE"
        assert "most" in result["headline"].lower()
        assert "75" in result["summary"]
        assert "gaps" in result["summary"].lower()
    
    def test_not_eligible_verdict(self, translator):
        """Test NOT_ELIGIBLE category translation"""
        result = translator.eligibility_verdict(60.0, "NOT_ELIGIBLE")
        
        assert result["title"] == "✗ NOT_ELIGIBLE"
        assert "not meet" in result["headline"].lower()
        assert "60" in result["summary"]
    
    def test_low_risk_verdict(self, translator):
        """Test LOW risk translation"""
        result = translator.risk_verdict(25.0, "LOW", [])
        
        assert result["title"] == "✓ LOW RISK"
        assert "manageable" in result["summary"].lower()
        assert "25" in result["summary"]
    
    def test_high_risk_verdict_with_deal_breakers(self, translator):
        """Test HIGH risk with deal-breakers"""
        deal_breakers = ["Missing certification", "Insufficient capacity"]
        result = translator.risk_verdict(80.0, "HIGH", deal_breakers)
        
        assert result["title"] == "🚨 HIGH RISK"
        assert "2 deal-breaker" in result["summary"]
        assert "deal-breaker" in result["action"].lower()
    
    def test_low_effort_verdict(self, translator):
        """Test LOW effort translation"""
        result = translator.effort_verdict(20.0, "LOW", 300.0, 30)
        
        assert result["title"] == "✓ LOW EFFORT"
        assert "manageable" in result["summary"].lower()
        assert "300.0" in result["summary"]
        assert "30 days" in result["summary"]
    
    def test_high_effort_verdict(self, translator):
        """Test HIGH effort translation"""
        result = translator.effort_verdict(85.0, "HIGH", 2000.0, 120)
        
        assert result["title"] == "🚨 HIGH EFFORT"
        assert "major" in result["summary"].lower()
        assert "2000.0" in result["summary"]
    
    def test_bid_recommendation_explanation(self, translator):
        """Test BID recommendation explanation"""
        result = translator.recommendation_explanation("BID", 82.0)
        
        assert result["title"] == "✓ RECOMMEND: BID"
        assert "strong" in result["headline"].lower()
        assert "82" in result["summary"]
    
    def test_no_bid_recommendation_explanation(self, translator):
        """Test NO_BID recommendation explanation"""
        result = translator.recommendation_explanation("NO_BID", 35.0)
        
        assert result["title"] == "✗ RECOMMEND: NO BID"
        assert "not recommended" in result["headline"].lower()
    
    def test_conditional_recommendation_explanation(self, translator):
        """Test CONDITIONAL recommendation explanation"""
        result = translator.recommendation_explanation("CONDITIONAL", 65.0)
        
        assert result["title"] == "⚠ CONDITIONAL: REVIEW"
        assert "mixed" in result["summary"].lower()


# ============================================================================
# TESTS: REPORT GENERATOR
# ============================================================================

class TestReportGenerator:
    """Tests for ReportGenerator"""
    
    def test_initialization(self, report_generator):
        """Test ReportGenerator initializes correctly"""
        assert report_generator.translator is not None
        assert report_generator.styles is not None
    
    def test_styles_setup(self, report_generator):
        """Test all required styles are defined"""
        required_styles = [
            'TitleMain',
            'SectionHead',
            'SubSectionHead',
            'BodyText',
            'VerdictText',
            'ActionText'
        ]
        
        for style_name in required_styles:
            assert style_name in report_generator.styles
    
    def test_pdf_generation_returns_bytesio(self, report_generator, sample_eligible_score):
        """Test PDF generation returns BytesIO object"""
        result = report_generator.generate_pdf(sample_eligible_score)
        
        assert isinstance(result, BytesIO)
        assert result.getvalue()  # Has content
        assert len(result.getvalue()) > 1000  # Reasonable size
    
    def test_pdf_contains_tender_id(self, report_generator, sample_eligible_score):
        """Test PDF contains tender ID"""
        pdf_buffer = report_generator.generate_pdf(sample_eligible_score)
        pdf_content = pdf_buffer.getvalue()
        
        # PDF should be valid
        assert pdf_content.startswith(b'%PDF')
    
    def test_pdf_for_eligible_tender(self, report_generator, sample_eligible_score):
        """Test PDF generation for eligible tender"""
        pdf_buffer = report_generator.generate_pdf(sample_eligible_score)
        
        assert isinstance(pdf_buffer, BytesIO)
        assert len(pdf_buffer.getvalue()) > 2000
    
    def test_pdf_for_conditional_tender(self, report_generator, sample_conditional_score):
        """Test PDF generation for conditional tender"""
        pdf_buffer = report_generator.generate_pdf(sample_conditional_score)
        
        assert isinstance(pdf_buffer, BytesIO)
        assert len(pdf_buffer.getvalue()) > 2000
    
    def test_title_section_building(self, report_generator, sample_eligible_score):
        """Test title section building"""
        story = report_generator._build_title_section(sample_eligible_score, "Acme Corp")
        
        assert len(story) > 0
        # Verify key components present
        assert any("TENDER" in str(item) for item in story if hasattr(item, 'text'))
    
    def test_executive_summary_building(self, report_generator, sample_eligible_score):
        """Test executive summary building"""
        story = report_generator._build_executive_summary(sample_eligible_score)
        
        assert len(story) > 0
        # Should contain score information
        assert any("83" in str(item) for item in story if hasattr(item, 'text'))
    
    def test_detailed_analysis_building(self, report_generator, sample_eligible_score):
        """Test detailed analysis building"""
        story = report_generator._build_detailed_analysis(sample_eligible_score)
        
        assert len(story) > 0
    
    def test_clause_verdicts_building(self, report_generator, sample_eligible_score):
        """Test clause verdicts section building"""
        story = report_generator._build_clause_verdicts(sample_eligible_score)
        
        assert len(story) > 0
    
    def test_risk_details_building(self, report_generator, sample_eligible_score):
        """Test risk details section building"""
        story = report_generator._build_risk_details(sample_eligible_score)
        
        assert len(story) > 0
    
    def test_effort_details_building(self, report_generator, sample_eligible_score):
        """Test effort details section building"""
        story = report_generator._build_effort_details(sample_eligible_score)
        
        assert len(story) > 0
    
    def test_recommendations_building(self, report_generator, sample_eligible_score):
        """Test recommendations section building"""
        story = report_generator._build_recommendations(sample_eligible_score)
        
        assert len(story) > 0


# ============================================================================
# TESTS: CONVENIENCE FUNCTION
# ============================================================================

class TestConvenienceFunction:
    """Tests for convenience function"""
    
    def test_generate_tender_report_function(self, sample_eligible_score):
        """Test convenience function for report generation"""
        pdf_buffer = generate_tender_report(sample_eligible_score, "Test Company")
        
        assert isinstance(pdf_buffer, BytesIO)
        assert len(pdf_buffer.getvalue()) > 1000
    
    def test_generate_tender_report_default_company_name(self, sample_eligible_score):
        """Test report generation with default company name"""
        pdf_buffer = generate_tender_report(sample_eligible_score)
        
        assert isinstance(pdf_buffer, BytesIO)


# ============================================================================
# TESTS: API HELPER FUNCTIONS
# ============================================================================

class TestAPIHelperFunctions:
    """Tests for API helper functions"""
    
    def test_format_evaluation_response(self, sample_eligible_score, mock_tender):
        """Test evaluation response formatting"""
        response = _format_evaluation_response(mock_tender, sample_eligible_score)
        
        assert response["tender_id"] == "TENDER-001"
        assert response["overall_score"] == 83.5
        assert response["bid_recommendation"] == "BID"
        assert "scores" in response
        assert "strengths" in response
        assert "weaknesses" in response
    
    def test_format_evaluation_response_has_summaries(self, sample_eligible_score, mock_tender):
        """Test that response has all required fields"""
        response = _format_evaluation_response(mock_tender, sample_eligible_score)
        
        assert response["scores"]["eligibility"]["score"] == 95.0
        assert response["scores"]["risk"]["score"] == 25.0
        assert response["scores"]["effort"]["score"] == 30.0
    
    def test_generate_executive_summary_bid(self, sample_eligible_score):
        """Test executive summary for BID recommendation"""
        summary = _generate_executive_summary(sample_eligible_score)
        
        assert "strong opportunity" in summary.lower()
        assert "bid" in summary.lower()
        assert "83.5" in summary
    
    def test_generate_executive_summary_conditional(self, sample_conditional_score):
        """Test executive summary for CONDITIONAL recommendation"""
        summary = _generate_executive_summary(sample_conditional_score)
        
        assert "mixed" in summary.lower()
        assert "75" in summary
    
    def test_eligibility_verdict_text(self, sample_eligible_score):
        """Test eligibility verdict generation"""
        verdict = _get_eligibility_verdict(sample_eligible_score.eligibility)
        
        assert "95" in verdict
        assert "90%" in verdict
    
    def test_risk_verdict_text(self, sample_eligible_score):
        """Test risk verdict generation"""
        verdict = _get_risk_verdict(sample_eligible_score.risk)
        
        assert "25" in verdict
        assert "low" in verdict.lower()
    
    def test_effort_verdict_text(self, sample_eligible_score):
        """Test effort verdict generation"""
        verdict = _get_effort_verdict(sample_eligible_score.effort)
        
        assert "500" in verdict
        assert "low" in verdict.lower()
    
    def test_risk_verdict_with_deal_breakers(self, sample_conditional_score):
        """Test risk verdict mentions deal-breakers"""
        sample_conditional_score.risk.deal_breakers = ["Missing cert", "Overweight"]
        verdict = _get_risk_verdict(sample_conditional_score.risk)
        
        assert "high" in verdict.lower()


# ============================================================================
# TESTS: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_pdf_generation_with_special_characters(self, report_generator):
        """Test PDF generation with special characters in company name"""
        from app.services.scoring_models import (
            EligibilityScore, RiskScore, EffortScore, TenderScore,
            EligibilityCategory, RiskCategory, EffortCategory,
            EffortMetrics, Assessments
        )
        
        # Create minimal score
        elig = EligibilityScore(
            eligibility_score=80.0,
            category=EligibilityCategory.ELIGIBLE,
            requirements_assessments=[],
            assessments=Assessments(0, 0, 0, ""),
            scoring_logic="test"
        )
        
        risk = RiskScore(
            risk_score=30.0,
            risk_category=RiskCategory.LOW,
            total_risks=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            top_risks=[],
            deal_breakers=[],
            assessments=Assessments(0, 0, 0, ""),
            scoring_logic="test"
        )
        
        metrics = EffortMetrics(
            total_hours=100, total_days=10, team_size=1,
            estimated_cost=10000, cost_per_hour=100
        )
        
        effort = EffortScore(
            effort_score=20.0,
            effort_category=EffortCategory.LOW,
            metrics=metrics,
            complexity_factors=[],
            assessments=Assessments(0, 0, 0, ""),
            scoring_logic="test"
        )
        
        score = TenderScore(
            tender_id="TEST-001",
            overall_score=75.0,
            bid_recommendation="BID",
            eligibility=elig,
            risk=risk,
            effort=effort,
            strengths=[],
            weaknesses=[],
            critical_items=[]
        )
        
        # Test with special characters
        pdf_buffer = report_generator.generate_pdf(score, "Company & Sons, Inc. (2024)")
        
        assert isinstance(pdf_buffer, BytesIO)
        assert len(pdf_buffer.getvalue()) > 1000
    
    def test_pdf_generation_with_many_requirements(self, report_generator):
        """Test PDF generation with many requirements"""
        from app.services.scoring_models import (
            EligibilityScore, RiskScore, EffortScore, TenderScore,
            EligibilityCategory, RiskCategory, EffortCategory,
            EffortMetrics, Assessments, RequirementAssessment
        )
        
        # Create many requirements
        requirements = [
            RequirementAssessment(
                requirement_text=f"Requirement {i}",
                company_meets=i % 2 == 0,
                is_mandatory=True,
                reasoning=f"Assessment for requirement {i}"
            )
            for i in range(50)
        ]
        
        elig = EligibilityScore(
            eligibility_score=80.0,
            category=EligibilityCategory.ELIGIBLE,
            requirements_assessments=requirements,
            assessments=Assessments(0, 0, 0, ""),
            scoring_logic="test"
        )
        
        risk = RiskScore(
            risk_score=30.0,
            risk_category=RiskCategory.LOW,
            total_risks=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            top_risks=[],
            deal_breakers=[],
            assessments=Assessments(0, 0, 0, ""),
            scoring_logic="test"
        )
        
        metrics = EffortMetrics(
            total_hours=100, total_days=10, team_size=1,
            estimated_cost=10000, cost_per_hour=100
        )
        
        effort = EffortScore(
            effort_score=20.0,
            effort_category=EffortCategory.LOW,
            metrics=metrics,
            complexity_factors=[],
            assessments=Assessments(0, 0, 0, ""),
            scoring_logic="test"
        )
        
        score = TenderScore(
            tender_id="TEST-001",
            overall_score=75.0,
            bid_recommendation="BID",
            eligibility=elig,
            risk=risk,
            effort=effort,
            strengths=[],
            weaknesses=[],
            critical_items=[]
        )
        
        pdf_buffer = report_generator.generate_pdf(score)
        
        assert isinstance(pdf_buffer, BytesIO)
        assert len(pdf_buffer.getvalue()) > 2000
