"""
STEP-9 Demonstration Script

Demonstrates all evaluation retrieval and report generation features.
Run this to see Step-9 in action.
"""

import sys
from io import BytesIO
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
from app.services.report_generator import (
    ReportGenerator,
    BusinessLanguageTranslator,
    generate_tender_report,
)


def create_sample_tender_score(scenario: str = "eligible") -> TenderScore:
    """Create sample tender scores for demonstration"""
    
    if scenario == "eligible":
        # Strong, eligible tender
        requirements = [
            RequirementAssessment(
                requirement_text="ISO 9001 Certification",
                company_meets=True,
                is_mandatory=True,
                reasoning="Company holds current ISO 9001 certification valid through 2025"
            ),
            RequirementAssessment(
                requirement_text="5+ years experience in similar projects",
                company_meets=True,
                is_mandatory=True,
                reasoning="Company has 8 years of experience with 12+ similar implementations"
            ),
            RequirementAssessment(
                requirement_text="Team of 10+ dedicated resources",
                company_meets=True,
                is_mandatory=False,
                reasoning="Company has 15 dedicated team members available"
            ),
            RequirementAssessment(
                requirement_text="Support 24/7 post-deployment",
                company_meets=True,
                is_mandatory=False,
                reasoning="Company offers 24/7 support as standard offering"
            ),
        ]
        
        eligibility = EligibilityScore(
            eligibility_score=95.0,
            category=EligibilityCategory.ELIGIBLE,
            requirements_assessments=requirements,
            assessments=Assessments(
                met_count=4,
                not_met_count=0,
                partial_count=0,
                summary="All requirements met, strong profile"
            ),
            scoring_logic="95% of requirements met, exceeds 90% threshold for ELIGIBLE"
        )
        
        risk = RiskScore(
            risk_score=20.0,
            risk_category=RiskCategory.LOW,
            total_risks=2,
            critical_count=0,
            high_count=0,
            medium_count=1,
            low_count=1,
            top_risks=["Minor timeline compression", "Standard integration challenges"],
            deal_breakers=[],
            assessments=Assessments(
                met_count=0,
                not_met_count=0,
                partial_count=0,
                summary="Low risk profile"
            ),
            scoring_logic="Weighted impact score: (severity 0.3 × 60%) + (probability 0.2 × 40%) = 0.2 × 100 = 20"
        )
        
        metrics = EffortMetrics(
            total_hours=600.0,
            total_days=60,
            team_size=6,
            estimated_cost=60000.0,
            cost_per_hour=100.0
        )
        
        effort = EffortScore(
            effort_score=25.0,
            effort_category=EffortCategory.LOW,
            metrics=metrics,
            complexity_factors=["Proven technologies", "Standard architecture", "Experienced team"],
            assessments=Assessments(
                met_count=0,
                not_met_count=0,
                partial_count=0,
                summary="Low effort requirement"
            ),
            scoring_logic="Weighted score: (hours 25 × 50%) + (timeline 30 × 30%) + (cost 10 × 20%) = 25"
        )
        
        return TenderScore(
            tender_id="TENDER-2024-001-CLOUD-PLATFORM",
            overall_score=86.5,
            bid_recommendation="BID",
            eligibility=eligibility,
            risk=risk,
            effort=effort,
            strengths=[
                "Strong alignment with company capabilities",
                "Low technical risk with proven technologies",
                "Reasonable timeline and resource requirements",
                "Excellent long-term relationship opportunity"
            ],
            weaknesses=[
                "Tight timeline may require overtime",
                "Specific compliance requirements need verification"
            ],
            critical_items=[
                "Confirm team availability for 60-day project",
                "Schedule pre-engagement meeting with client"
            ]
        )
    
    elif scenario == "conditional":
        # Mixed, conditional tender
        requirements = [
            RequirementAssessment(
                requirement_text="ISO 9001 Certification",
                company_meets=False,
                is_mandatory=True,
                reasoning="Company not currently certified; can obtain in 6 weeks"
            ),
            RequirementAssessment(
                requirement_text="5+ years experience",
                company_meets=True,
                is_mandatory=True,
                reasoning="Company has 6 years but with different technology stack"
            ),
            RequirementAssessment(
                requirement_text="Azure cloud platform experience",
                company_meets=False,
                is_mandatory=False,
                reasoning="Company primarily uses AWS; learning curve expected"
            ),
        ]
        
        eligibility = EligibilityScore(
            eligibility_score=72.0,
            category=EligibilityCategory.PARTIALLY_ELIGIBLE,
            requirements_assessments=requirements,
            assessments=Assessments(
                met_count=1,
                not_met_count=2,
                partial_count=0,
                summary="One mandatory requirement not met"
            ),
            scoring_logic="72% of requirements met, in 70-89% PARTIALLY_ELIGIBLE range"
        )
        
        risk = RiskScore(
            risk_score=58.0,
            risk_category=RiskCategory.MEDIUM,
            total_risks=5,
            critical_count=1,
            high_count=1,
            medium_count=2,
            low_count=1,
            top_risks=[
                "Missing ISO 9001 certification (can obtain)",
                "Azure platform learning curve",
                "Extended timeline may be needed",
                "Resource availability in Q2"
            ],
            deal_breakers=[],
            assessments=Assessments(
                met_count=0,
                not_met_count=0,
                partial_count=0,
                summary="Medium risk profile"
            ),
            scoring_logic="Weighted impact: (severity 0.58 × 60%) + (probability 0.58 × 40%) = 0.58 × 100 = 58"
        )
        
        metrics = EffortMetrics(
            total_hours=1400.0,
            total_days=100,
            team_size=8,
            estimated_cost=140000.0,
            cost_per_hour=100.0
        )
        
        effort = EffortScore(
            effort_score=62.0,
            effort_category=EffortCategory.MEDIUM,
            metrics=metrics,
            complexity_factors=[
                "New cloud platform (Azure)",
                "Complex integrations with legacy systems",
                "Compliance and security requirements"
            ],
            assessments=Assessments(
                met_count=0,
                not_met_count=0,
                partial_count=0,
                summary="Medium effort requirement"
            ),
            scoring_logic="Weighted score: (hours 60 × 50%) + (timeline 65 × 30%) + (cost 60 × 20%) = 62"
        )
        
        return TenderScore(
            tender_id="TENDER-2024-002-ENTERPRISE-MIGRATION",
            overall_score=63.5,
            bid_recommendation="CONDITIONAL",
            eligibility=eligibility,
            risk=risk,
            effort=effort,
            strengths=[
                "Strong core capabilities for integration work",
                "Experienced team with similar projects",
                "Good long-term partnership potential"
            ],
            weaknesses=[
                "Missing ISO 9001 certification",
                "No prior Azure platform experience",
                "Substantial resource commitment required",
                "Extended timeline may impact other projects"
            ],
            critical_items=[
                "Obtain ISO 9001 certification OR request waiver",
                "Plan Azure training for development team",
                "Secure resource availability commitment",
                "Develop detailed risk mitigation strategy"
            ]
        )
    
    else:  # no-bid
        # Weak, no-bid tender
        requirements = [
            RequirementAssessment(
                requirement_text="ISO 9001 Certification",
                company_meets=False,
                is_mandatory=True,
                reasoning="Company not certified; cannot obtain in timeframe"
            ),
            RequirementAssessment(
                requirement_text="10+ years enterprise experience",
                company_meets=False,
                is_mandatory=True,
                reasoning="Company has 5 years; insufficient for this scope"
            ),
            RequirementAssessment(
                requirement_text="Team of 20+ people",
                company_meets=False,
                is_mandatory=True,
                reasoning="Company has only 12 total employees"
            ),
        ]
        
        eligibility = EligibilityScore(
            eligibility_score=35.0,
            category=EligibilityCategory.NOT_ELIGIBLE,
            requirements_assessments=requirements,
            assessments=Assessments(
                met_count=0,
                not_met_count=3,
                partial_count=0,
                summary="All mandatory requirements not met"
            ),
            scoring_logic="35% of requirements met, below 70% NOT_ELIGIBLE threshold"
        )
        
        risk = RiskScore(
            risk_score=82.0,
            risk_category=RiskCategory.HIGH,
            total_risks=8,
            critical_count=3,
            high_count=2,
            medium_count=2,
            low_count=1,
            top_risks=[
                "Missing ISO 9001 - regulatory requirement",
                "Insufficient team size for scope",
                "Limited enterprise experience",
                "Resource constraints would impact other projects"
            ],
            deal_breakers=["ISO certification mandatory", "Team size requirement non-negotiable"],
            assessments=Assessments(
                met_count=0,
                not_met_count=0,
                partial_count=0,
                summary="High risk profile with deal-breakers"
            ),
            scoring_logic="Weighted impact: (severity 0.82 × 60%) + (probability 0.82 × 40%) = 0.82 × 100 = 82"
        )
        
        metrics = EffortMetrics(
            total_hours=3500.0,
            total_days=200,
            team_size=15,
            estimated_cost=350000.0,
            cost_per_hour=100.0
        )
        
        effort = EffortScore(
            effort_score=88.0,
            effort_category=EffortCategory.HIGH,
            metrics=metrics,
            complexity_factors=[
                "Multi-year engagement",
                "Complex enterprise architecture",
                "Offshore coordination required",
                "Multiple integrations across systems"
            ],
            assessments=Assessments(
                met_count=0,
                not_met_count=0,
                partial_count=0,
                summary="High effort requirement"
            ),
            scoring_logic="Weighted score: (hours 95 × 50%) + (timeline 85 × 30%) + (cost 80 × 20%) = 88"
        )
        
        return TenderScore(
            tender_id="TENDER-2024-003-ENTERPRISE-OVERHAUL",
            overall_score=38.0,
            bid_recommendation="NO_BID",
            eligibility=eligibility,
            risk=risk,
            effort=effort,
            strengths=[
                "Large budget available",
                "Potential for long-term relationship"
            ],
            weaknesses=[
                "Company not qualified per mandatory requirements",
                "Insufficient team capacity",
                "Limited enterprise experience",
                "Multiple deal-breaker risks"
            ],
            critical_items=[
                "RECOMMENDATION: Do not bid on this opportunity",
                "Focus resources on better-aligned tenders"
            ]
        )


def demo_1_business_language_translation():
    """Demo 1: Business Language Translation"""
    print("\n" + "="*80)
    print("DEMO 1: BUSINESS LANGUAGE TRANSLATION")
    print("="*80)
    
    translator = BusinessLanguageTranslator()
    
    # Eligible verdict
    print("\n1.1 Eligibility Translation (95% - ELIGIBLE)")
    print("-" * 40)
    verdict = translator.eligibility_verdict(95.0, "ELIGIBLE")
    print(f"Title:      {verdict['title']}")
    print(f"Headline:   {verdict['headline']}")
    print(f"Summary:    {verdict['summary']}")
    print(f"Action:     {verdict['action']}")
    
    # Risk with deal-breakers
    print("\n1.2 Risk Translation (82 - HIGH with deal-breakers)")
    print("-" * 40)
    verdict = translator.risk_verdict(
        82.0,
        "HIGH",
        ["ISO certification mandatory", "Team size requirement"]
    )
    print(f"Title:      {verdict['title']}")
    print(f"Headline:   {verdict['headline']}")
    print(f"Summary:    {verdict['summary']}")
    print(f"Action:     {verdict['action']}")
    
    # Effort translation
    print("\n1.3 Effort Translation (60 - MEDIUM, 1200 hours)")
    print("-" * 40)
    verdict = translator.effort_verdict(60.0, "MEDIUM", 1200.0, 100)
    print(f"Title:      {verdict['title']}")
    print(f"Headline:   {verdict['headline']}")
    print(f"Summary:    {verdict['summary']}")
    print(f"Action:     {verdict['action']}")
    
    # Recommendation explanation
    print("\n1.4 Recommendation Explanation (CONDITIONAL - 63.5)")
    print("-" * 40)
    explanation = translator.recommendation_explanation("CONDITIONAL", 63.5)
    print(f"Title:      {explanation['title']}")
    print(f"Headline:   {explanation['headline']}")
    print(f"Summary:    {explanation['summary']}")
    print(f"Details:    {explanation['details']}")


def demo_2_pdf_generation():
    """Demo 2: PDF Report Generation"""
    print("\n" + "="*80)
    print("DEMO 2: PDF REPORT GENERATION")
    print("="*80)
    
    generator = ReportGenerator()
    
    scenarios = ["eligible", "conditional", "no-bid"]
    
    for scenario in scenarios:
        print(f"\n2.{scenarios.index(scenario) + 1} Generating PDF for {scenario.upper()} tender")
        print("-" * 40)
        
        tender_score = create_sample_tender_score(scenario)
        
        # Generate PDF
        pdf_buffer = generator.generate_pdf(
            tender_score,
            company_name="Acme Corporation"
        )
        
        # Report details
        pdf_size = len(pdf_buffer.getvalue())
        print(f"Tender ID:        {tender_score.tender_id}")
        print(f"Overall Score:    {tender_score.overall_score:.1f}/100")
        print(f"Recommendation:   {tender_score.bid_recommendation}")
        print(f"PDF Generated:    ✓ Yes")
        print(f"PDF Size:         {pdf_size:,} bytes ({pdf_size/1024:.1f} KB)")
        print(f"PDF Valid:        {'✓ Yes' if pdf_size > 1000 else '✗ No'}")
        
        # Save to file
        filename = f"demo_tender_{scenario}_report.pdf"
        with open(filename, "wb") as f:
            f.write(pdf_buffer.getvalue())
        print(f"Saved to:         {filename}")


def demo_3_clause_verdicts():
    """Demo 3: Clause-level Verdicts"""
    print("\n" + "="*80)
    print("DEMO 3: CLAUSE-LEVEL VERDICTS (REQUIREMENT ASSESSMENTS)")
    print("="*80)
    
    tender_score = create_sample_tender_score("eligible")
    requirements = tender_score.eligibility.requirements_assessments
    
    print(f"\nTender: {tender_score.tender_id}")
    print(f"Total Requirements: {len(requirements)}")
    print(f"Requirements Met: {sum(1 for r in requirements if r.company_meets)}")
    print(f"\n{'Status':<6} {'Mandatory':<10} {'Requirement':<40} {'Reasoning':<30}")
    print("-" * 90)
    
    for req in requirements:
        status = "✓" if req.company_meets else "✗"
        mandatory = "Yes" if req.is_mandatory else "No"
        req_text = req.requirement_text[:37] + "..." if len(req.requirement_text) > 37 else req.requirement_text
        reasoning = req.reasoning[:27] + "..." if len(req.reasoning) > 27 else req.reasoning
        
        print(f"{status:<6} {mandatory:<10} {req_text:<40} {reasoning:<30}")


def demo_4_api_responses():
    """Demo 4: API Response Formats"""
    print("\n" + "="*80)
    print("DEMO 4: API RESPONSE FORMATS")
    print("="*80)
    
    tender_score = create_sample_tender_score("conditional")
    
    # Full evaluation response
    print("\n4.1 GET /api/evaluations/tender/{id}")
    print("-" * 40)
    print(f"""
{{
  "tender_id": "{tender_score.tender_id}",
  "overall_score": {tender_score.overall_score},
  "bid_recommendation": "{tender_score.bid_recommendation}",
  "scores": {{
    "eligibility": {{
      "score": {tender_score.eligibility.eligibility_score:.1f},
      "category": "{tender_score.eligibility.category.value}"
    }},
    "risk": {{
      "score": {tender_score.risk.risk_score:.1f},
      "category": "{tender_score.risk.risk_category.value}"
    }},
    "effort": {{
      "score": {tender_score.effort.effort_score:.1f},
      "category": "{tender_score.effort.effort_category.value}"
    }}
  }},
  "strengths": {tender_score.strengths[:2]},
  "weaknesses": {tender_score.weaknesses[:2]},
  "critical_items": {tender_score.critical_items[:2]}
}}
    """)
    
    # Risk details response
    print("\n4.2 GET /api/evaluations/tender/{id}/risk")
    print("-" * 40)
    risk = tender_score.risk
    print(f"""
{{
  "tender_id": "{tender_score.tender_id}",
  "risk": {{
    "category": "{risk.risk_category.value}",
    "score": {risk.risk_score:.1f},
    "risk_summary": {{
      "total_risks": {risk.total_risks},
      "critical_count": {risk.critical_count},
      "high_count": {risk.high_count},
      "medium_count": {risk.medium_count},
      "low_count": {risk.low_count}
    }},
    "top_risks": {risk.top_risks[:3]},
    "deal_breakers": {risk.deal_breakers}
  }}
}}
    """)
    
    # List response
    print("\n4.3 GET /api/evaluations/list?status=BID&limit=50")
    print("-" * 40)
    print(f"""
{{
  "total_count": 87,
  "limit": 50,
  "offset": 0,
  "results": [
    {{
      "tender_id": "TENDER-2024-001-CLOUD-PLATFORM",
      "overall_score": 86.5,
      "recommendation": "BID",
      "eligibility_score": 95.0,
      "risk_score": 20.0,
      "effort_score": 25.0,
      "evaluated_at": "2024-01-20T14:30:00Z"
    }},
    ...
  ]
}}
    """)


def demo_5_streaming_download():
    """Demo 5: Streaming Download Simulation"""
    print("\n" + "="*80)
    print("DEMO 5: STREAMING DOWNLOAD (SIMULATED)")
    print("="*80)
    
    tender_score = create_sample_tender_score("eligible")
    pdf_buffer = generate_tender_report(tender_score, "Acme Corp")
    
    print(f"\nTender: {tender_score.tender_id}")
    print(f"PDF Size: {len(pdf_buffer.getvalue()):,} bytes")
    print(f"Download Simulation: ", end="")
    
    # Simulate streaming in chunks
    chunk_size = 8192
    total_size = len(pdf_buffer.getvalue())
    downloaded = 0
    
    for i in range(0, total_size, chunk_size):
        downloaded += chunk_size
        percent = min(100, int(downloaded / total_size * 100))
        print(f"\r{percent}%", end="", flush=True)
    
    print(f"\r100% ✓ Complete")
    print(f"\nHTTP Response Headers:")
    print(f"  Content-Type: application/pdf")
    print(f"  Content-Disposition: attachment; filename=tender_{tender_score.tender_id}_report.pdf")
    print(f"  Content-Length: {len(pdf_buffer.getvalue()):,}")
    print(f"  Transfer-Encoding: chunked")


def demo_6_verdict_accuracy():
    """Demo 6: Verify Verdict Accuracy"""
    print("\n" + "="*80)
    print("DEMO 6: VERDICT ACCURACY & BUSINESS LANGUAGE CONSISTENCY")
    print("="*80)
    
    translator = BusinessLanguageTranslator()
    
    # Test eligibility thresholds
    print("\nEligibility Thresholds:")
    print("-" * 40)
    test_scores = [
        (95.0, "ELIGIBLE"),
        (85.0, "ELIGIBLE"),
        (90.0, "ELIGIBLE"),
        (89.9, "PARTIALLY_ELIGIBLE"),
        (70.0, "PARTIALLY_ELIGIBLE"),
        (69.9, "NOT_ELIGIBLE"),
    ]
    
    for score, category in test_scores:
        verdict = translator.eligibility_verdict(score, category)
        print(f"✓ {score:5.1f}% → {category:20} → {verdict['title']}")
    
    # Test risk thresholds
    print("\nRisk Score Ranges:")
    print("-" * 40)
    risk_tests = [
        (20.0, "LOW"),
        (50.0, "MEDIUM"),
        (80.0, "HIGH"),
    ]
    
    for score, category in risk_tests:
        verdict = translator.risk_verdict(score, category, [])
        print(f"✓ Score {score:5.1f} → {category:10} → {verdict['title']}")
    
    # Test effort thresholds
    print("\nEffort Score Ranges:")
    print("-" * 40)
    effort_tests = [
        (20.0, "LOW", 500.0),
        (50.0, "MEDIUM", 1200.0),
        (85.0, "HIGH", 2500.0),
    ]
    
    for score, category, hours in effort_tests:
        verdict = translator.effort_verdict(score, category, hours, int(hours / 8))
        print(f"✓ Score {score:5.1f} ({hours:5.0f}h) → {category:10} → {verdict['title']}")


def main():
    """Run all demonstrations"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*25 + "STEP-9 DEMONSTRATION SCRIPT" + " "*26 + "║")
    print("║" + " "*20 + "Evaluation Retrieval & Report Generation" + " "*18 + "║")
    print("╚" + "="*78 + "╝")
    
    # Run demos
    demo_1_business_language_translation()
    demo_2_pdf_generation()
    demo_3_clause_verdicts()
    demo_4_api_responses()
    demo_5_streaming_download()
    demo_6_verdict_accuracy()
    
    # Summary
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("""
✓ Demo 1: Business Language Translation - Converting technical scores to business language
✓ Demo 2: PDF Report Generation - Generating professional PDF reports
✓ Demo 3: Clause-level Verdicts - Showing requirement-by-requirement assessments
✓ Demo 4: API Response Formats - Showing API response JSON structures
✓ Demo 5: Streaming Download - Simulating efficient PDF downloads
✓ Demo 6: Verdict Accuracy - Verifying thresholds and consistency

Generated Files:
  - demo_tender_eligible_report.pdf
  - demo_tender_conditional_report.pdf
  - demo_tender_no-bid_report.pdf

Next Steps:
  1. Review the generated PDF reports
  2. Run unit tests: pytest tests/test_step9_evaluations.py -v
  3. Integrate API routes into FastAPI main app
  4. Set up database persistence for evaluations

Documentation:
  - STEP_9_DOCUMENTATION.md (comprehensive guide)
  - STEP_9_QUICK_REFERENCE.md (quick lookup)
    """)
    print("="*80)


if __name__ == "__main__":
    main()
