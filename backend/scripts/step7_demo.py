"""
Step-7 Comprehensive Demo - AI Extraction Pipelines

Demonstrates all 4 pipelines with realistic examples.
Can be run with or without actual API keys.
"""

import json
import sys
from datetime import datetime
from pprint import pprint
from pathlib import Path

# Ensure backend root is importable when running from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ai_schemas import (
    ClauseExtractionOutput,
    EligibilityReasoningOutput,
    RiskIdentificationOutput,
    EffortEstimationOutput,
)
from app.services.clause_extractor import ClauseExtractor
from app.services.eligibility_evaluator import EligibilityEvaluator
from app.services.risk_analyzer import RiskAnalyzer
from app.services.effort_estimator import EffortEstimator
from app.services.tender_analyzer import TenderAnalyzer
from app.services.llm_client import (
    LLMClient,
    LLMConfig,
    LLMProvider,
    LLMModel,
)


# ============================================================================
# SAMPLE DATA
# ============================================================================

SAMPLE_TENDER = """
TENDER: AI Platform Development - RFP #2024-001

SECTION 1: SCOPE OF WORK

1.1 OBJECTIVE
The client seeks development of an AI-powered document analysis platform. The system must analyze 
tender and RFP documents, extract key information, and generate bid recommendations.

1.2 DELIVERABLES
The contractor shall deliver:
- Document ingestion system supporting PDF, DOCX, TXT formats
- AI extraction engine for clause, requirement, and risk identification
- REST API with authentication and document upload capabilities
- Web dashboard for results visualization
- Complete documentation and knowledge transfer

1.3 TECHNICAL REQUIREMENTS
The solution must be developed in Python 3.11+ with FastAPI framework. It must integrate with
OpenAI GPT-4 API for document analysis. The system must process documents within 60 seconds
and achieve 95% extraction accuracy.

SECTION 2: ELIGIBILITY REQUIREMENTS

2.1 MANDATORY REQUIREMENTS
- 5+ years experience in enterprise software development
- Demonstrated expertise in Python and FastAPI (2+ projects)
- Experience with LLM integrations (OpenAI, Anthropic, or similar)
- Team must include at least 1 person with AI/ML background
- Must be registered as a legal entity
- Must have $500k+ annual revenue or equivalent capital

2.2 RECOMMENDED REQUIREMENTS
- Prior experience with document processing (PDF/NLP)
- Experience with AWS or similar cloud platforms
- Track record of delivering SaaS products
- 3+ years in healthcare or regulated industries

SECTION 3: DELIVERY AND TIMELINE

3.1 CRITICAL DATES
- Proposal Submission: 2024-03-15
- Project Start: 2024-04-01
- Phase 1 (Design & Setup): 6 weeks
- Phase 2 (Development): 12 weeks
- Phase 3 (Testing & Deployment): 4 weeks
- Final Delivery: 2024-09-30

3.2 MILESTONES
Week 4: Architecture approved
Week 10: Core extraction engine complete
Week 16: API and dashboard complete
Week 20: Full system testing complete
Week 22: Final delivery and knowledge transfer

SECTION 4: COMPLIANCE AND PENALTIES

4.1 PENALTIES FOR NON-COMPLIANCE
- Late delivery: 0.5% of contract value per week (max 5%)
- Missing deliverables: 10% per missing component
- Performance below SLAs: 2% per incident
- Documentation gaps: 5% of final payment

4.2 LIABILITY LIMITATIONS
Contractor liability is limited to the contract value. Client assumes responsibility for proper 
data handling of confidential documents processed through the system.

4.3 INTELLECTUAL PROPERTY
All work product becomes property of the client. Contractor may use general architectural 
patterns and approaches in other projects (non-confidential).

SECTION 5: EVALUATION CRITERIA

5.1 Technical Approach (40%): Solution architecture, technology choices, risk mitigation
5.2 Team Experience (30%): Relevant project experience, team composition, track record
5.3 Project Management (20%): Timeline feasibility, resource allocation, risk management
5.4 Cost (10%): Price competitiveness vs scope

SECTION 6: SPECIAL TERMS

6.1 The contractor must maintain 99.9% API uptime post-deployment for 6 months
6.2 Contractor shall provide on-site technical support for 2 weeks post-deployment
6.3 Source code must be delivered with comprehensive inline documentation
6.4 Contractor must sign NDA and data processing agreement before work starts
"""

SAMPLE_COMPANY_PROFILE = {
    "company_name": "TechFlow Solutions",
    "industry": "Software Development / AI Consulting",
    "years_in_business": 7,
    "team_size": 45,
    "annual_revenue": "$2.5M",
    "expertise_areas": [
        "Python development",
        "FastAPI/Django frameworks",
        "OpenAI/LLM integrations",
        "Document processing",
        "AWS cloud architecture",
    ],
    "certifications": [
        "AWS Solutions Architect",
        "Python Professional",
        "ISO 27001 certified",
    ],
    "past_projects": [
        {
            "name": "Healthcare Data Pipeline",
            "client": "MediCorp Inc",
            "duration": "6 months",
            "technologies": "Python, FastAPI, AWS, Bedrock",
            "status": "completed",
        },
        {
            "name": "Contract Analysis Platform",
            "client": "LawTech Partners",
            "duration": "4 months",
            "technologies": "Python, OpenAI, NLP",
            "status": "completed",
        },
        {
            "name": "Document Intelligence System",
            "client": "Financial Services Co",
            "duration": "3 months",
            "technologies": "Python, Claude API, LangChain",
            "status": "in-progress",
        },
    ],
    "key_team_members": [
        {"name": "John Doe", "role": "Technical Lead", "experience_years": 10},
        {"name": "Sarah Chen", "role": "AI/ML Specialist", "experience_years": 6},
        {"name": "Mike Johnson", "role": "Senior Backend Dev", "experience_years": 8},
        {"name": "Emma Davis", "role": "DevOps Engineer", "experience_years": 5},
    ],
    "financial_capacity": "$2.5M",
    "certifications_relevant": ["AWS", "Python", "ISO 27001"],
}


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

def demo_clause_extraction():
    """Demo: Clause extraction from tender"""
    print("\n" + "="*80)
    print("DEMO 1: CLAUSE EXTRACTION")
    print("="*80)
    print("\nExtracting clauses from tender document...")
    print("(Note: Will structure output, no summarization)")
    
    try:
        extractor = ClauseExtractor()
        
        # This would normally call the LLM
        print("\nWould extract:")
        print("  ✓ Scope section")
        print("  ✓ Deliverables with requirements")
        print("  ✓ Technical requirements with metrics")
        print("  ✓ Timeline milestones and penalties")
        print("  ✓ Compliance and IP clauses")
        print("  ✓ Evaluation criteria")
        
        print("\nExample output structure:")
        example = {
            "tender_id": "RFP-2024-001",
            "total_clauses_found": 6,
            "clauses": [
                {
                    "clause_number": "1.2",
                    "clause_title": "Deliverables",
                    "requirements": [
                        {
                            "requirement_text": "Document ingestion system supporting PDF, DOCX, TXT",
                            "type": "mandatory",
                            "category": "deliverable",
                            "measurable": True,
                        },
                        {
                            "requirement_text": "AI extraction engine for clause and risk identification",
                            "type": "mandatory",
                            "category": "technical",
                            "measurable": False,
                        },
                    ],
                }
            ],
            "extraction_confidence": 0.92,
        }
        pprint(example)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def demo_eligibility_evaluation():
    """Demo: Eligibility evaluation"""
    print("\n" + "="*80)
    print("DEMO 2: ELIGIBILITY EVALUATION")
    print("="*80)
    print("\nEvaluating company eligibility...")
    print(f"Company: {SAMPLE_COMPANY_PROFILE['company_name']}")
    
    try:
        evaluator = EligibilityEvaluator()
        
        print("\nRequirements Analysis:")
        requirements = [
            ("R1", "5+ years enterprise software development experience"),
            ("R2", "Python and FastAPI expertise (2+ projects)"),
            ("R3", "LLM integration experience (OpenAI/Anthropic)"),
            ("R4", "Team member with AI/ML background"),
            ("R5", "$500k+ annual revenue"),
        ]
        
        for req_id, req_text in requirements:
            print(f"\n  {req_id}: {req_text}")
            # Would call LLM for evaluation
            if req_id == "R1":
                print(f"    ✓ MET - Company has {SAMPLE_COMPANY_PROFILE['years_in_business']} years experience")
            elif req_id == "R2":
                print(f"    ✓ MET - Multiple FastAPI/Python projects documented")
            elif req_id == "R3":
                print(f"    ✓ MET - OpenAI and Claude integrations in past projects")
            elif req_id == "R4":
                print(f"    ✓ MET - Sarah Chen (AI/ML Specialist, 6 years)")
            elif req_id == "R5":
                print(f"    ✓ MET - Annual revenue ${SAMPLE_COMPANY_PROFILE['financial_capacity']}")
        
        print("\nEligibility Result:")
        example = {
            "tender_id": "RFP-2024-001",
            "total_requirements": 5,
            "total_met": 5,
            "eligibility_score": 100.0,
            "overall_eligibility_verdict": "eligible",
            "critical_gaps": [],
        }
        pprint(example)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def demo_risk_analysis():
    """Demo: Risk analysis"""
    print("\n" + "="*80)
    print("DEMO 3: RISK ANALYSIS")
    print("="*80)
    print("\nAnalyzing risks in tender clauses...")
    
    try:
        analyzer = RiskAnalyzer()
        
        print("\nIdentified Risks:")
        risks = [
            {
                "title": "Tight 22-week timeline",
                "severity": "high",
                "source": "Section 3.1",
                "desc": "Must deliver complex AI system in 22 weeks including testing",
            },
            {
                "title": "99.9% uptime SLA post-deployment",
                "severity": "medium",
                "source": "Section 6.1",
                "desc": "Required for 6 months; infrastructure failures could trigger penalties",
            },
            {
                "title": "Unlimited liability for performance",
                "severity": "critical",
                "source": "Section 4.2",
                "desc": "Liability is limited to contract value, but SLA penalties are separate",
            },
            {
                "title": "On-site presence requirement",
                "severity": "medium",
                "source": "Section 6.2",
                "desc": "Must provide 2 weeks on-site support post-deployment (travel/logistics)",
            },
            {
                "title": "95% extraction accuracy requirement",
                "severity": "high",
                "source": "Section 1.3",
                "desc": "LLM-based extraction may not achieve 95% consistently",
            },
        ]
        
        for i, risk in enumerate(risks, 1):
            print(f"\n  Risk {i}: {risk['title']}")
            print(f"    Severity: {risk['severity']}")
            print(f"    Source: {risk['source']}")
            print(f"    Details: {risk['desc']}")
        
        print("\nRisk Analysis Result:")
        example = {
            "tender_id": "RFP-2024-001",
            "total_risks_identified": 5,
            "critical_risks": 1,
            "high_risks": 2,
            "medium_risks": 2,
            "overall_risk_level": "high",
            "risk_score": 68.0,
            "deal_breaker_risks": [],
        }
        pprint(example)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def demo_effort_estimation():
    """Demo: Effort estimation"""
    print("\n" + "="*80)
    print("DEMO 4: EFFORT ESTIMATION")
    print("="*80)
    print("\nEstimating project effort, timeline, and cost...")
    
    try:
        estimator = EffortEstimator()
        
        print("\nWork Packages:")
        packages = [
            ("WP1", "Architecture & Setup", 80, "Design, infrastructure setup, CI/CD"),
            ("WP2", "Document Ingestion", 200, "PDF/DOCX parsers, text extraction"),
            ("WP3", "AI Extraction Engine", 320, "LLM integration, prompt engineering, extraction logic"),
            ("WP4", "API Development", 160, "FastAPI endpoints, authentication, validation"),
            ("WP5", "Dashboard & UI", 200, "React frontend, results visualization"),
            ("WP6", "Testing & QA", 160, "Unit tests, integration tests, performance testing"),
            ("WP7", "Documentation", 80, "Technical docs, API docs, knowledge transfer"),
            ("WP8", "Deployment & Support", 40, "Production deployment, 2-week on-site support"),
        ]
        
        total_hours = 0
        for pkg_id, pkg_name, hours, desc in packages:
            print(f"\n  {pkg_id}: {pkg_name}")
            print(f"    Effort: {hours} hours")
            print(f"    Description: {desc}")
            total_hours += hours
        
        team_size = 4
        working_days_per_week = 5
        hours_per_day = 8
        calendar_days = (total_hours / (team_size * hours_per_day * working_days_per_week)) * working_days_per_week
        
        print(f"\nEffort Summary:")
        print(f"  Total Effort: {total_hours} hours")
        print(f"  Team Size: {team_size} people")
        print(f"  Timeline: ~{calendar_days:.0f} calendar days")
        print(f"  Cost per hour: $100")
        total_cost = total_hours * 100 * 1.2  # 20% overhead
        print(f"  Estimated Cost: ${total_cost:,.0f}")
        
        print("\nEffort Estimation Result:")
        example = {
            "tender_id": "RFP-2024-001",
            "total_estimated_hours": total_hours,
            "total_estimated_days": calendar_days,
            "overall_effort_level": "high",
            "work_packages": len(packages),
            "cost": {
                "estimated_cost": total_cost,
                "labor_cost": total_hours * 100,
                "cost_per_hour": 100,
            },
        }
        pprint(example)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def demo_integrated_analysis():
    """Demo: Integrated analysis with bid recommendation"""
    print("\n" + "="*80)
    print("DEMO 5: INTEGRATED ANALYSIS & BID RECOMMENDATION")
    print("="*80)
    print("\nRunning all 4 pipelines and generating bid recommendation...")
    
    try:
        analyzer = TenderAnalyzer()
        
        print("\n✓ Clause Extraction: 6 clauses extracted")
        print("✓ Eligibility Evaluation: 5/5 requirements met (100%)")
        print("✓ Risk Analysis: 5 risks identified (1 critical, 2 high)")
        print("✓ Effort Estimation: 1,240 hours, $124k, 22-week timeline")
        
        print("\nBid Decision Analysis:")
        print("  Eligibility: ✓ PASS (100%)")
        print("  Risks: ⚠ HIGH (68/100)")
        print("  Feasibility: ✓ ACCEPTABLE")
        
        print("\nBID RECOMMENDATION: CONDITIONAL")
        print("\nReasoning:")
        print("  + Company meets all eligibility requirements")
        print("  + Technical expertise matches requirements")
        print("  + Team capacity sufficient for timeline")
        print("  - High risk profile due to tight timeline")
        print("  - Critical SLA requirements need careful planning")
        print("  - 95% accuracy requirement may be challenging")
        
        print("\nKey Strengths:")
        print("  1. Company has directly relevant experience")
        print("  2. Strong AI/ML expertise with recent LLM projects")
        print("  3. Sufficient team size (45 people)")
        print("  4. Appropriate technology stack")
        
        print("\nKey Weaknesses:")
        print("  1. Very tight 22-week timeline for complex system")
        print("  2. High performance requirements (99.9% uptime)")
        print("  3. On-site presence requirement (logistics)")
        print("  4. 95% accuracy for LLM-based extraction is aggressive")
        
        print("\nCritical Success Factors:")
        print("  1. Experienced PM for tight timeline management")
        print("  2. Robust testing framework for accuracy")
        print("  3. Redundancy architecture for uptime")
        print("  4. Clear escalation procedures with client")
        
        print("\nMust-Do Before Bid:")
        print("  1. Confirm team availability for full 22 weeks")
        print("  2. Plan SLA compliance strategy (99.9% uptime)")
        print("  3. Assess 95% accuracy feasibility with OpenAI")
        print("  4. Arrange on-site support logistics")
        print("  5. Review and finalize scope with client")
        
        example = {
            "tender_id": "RFP-2024-001",
            "recommendation": "CONDITIONAL",
            "feasibility_score": 82.5,
            "risk_adjusted_score": 68.0,
            "eligibility_score": 100.0,
            "risk_score": 68.0,
            "effort_hours": 1240,
            "cost": 124000,
        }
        print("\nMetrics:")
        pprint(example)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def demo_api_keys_info():
    """Demo: API Keys information"""
    print("\n" + "="*80)
    print("DEMO 6: API KEY REQUIREMENTS")
    print("="*80)
    
    print("\nStep-7 requires API keys for LLM integration:")
    print("\nREQUIRED:")
    print("  • OPENAI_API_KEY")
    print("    - Used for GPT-4-turbo (main model)")
    print("    - Required for production use")
    print("    - Get from: https://platform.openai.com/api-keys")
    
    print("\nOPTIONAL:")
    print("  • ANTHROPIC_API_KEY")
    print("    - Used for Claude models (alternative)")
    print("    - Can switch between OpenAI and Anthropic")
    print("    - Get from: https://console.anthropic.com/")
    
    print("\nHOW TO SET:")
    print("  1. Copy .env.example to .env")
    print("  2. Add API keys:")
    print("     OPENAI_API_KEY=sk-...")
    print("     ANTHROPIC_API_KEY=sk-ant-...")
    print("  3. Load with: source .env (Linux/Mac) or set (Windows)")
    print("  4. Restart backend server")
    
    print("\nIMPLEMENTATION STATUS:")
    print("  ✓ All extraction pipelines implemented")
    print("  ✓ Structured JSON output ready")
    print("  ✓ LLM client supports both providers")
    print("  ✓ Prompt templates prepared")
    print("  ⏳ Ready for API key activation")
    
    print("\nTESTING WITHOUT API KEYS:")
    print("  You can test the structure of all outputs without API keys:")
    print("  - Run unit tests for schema validation")
    print("  - Test LLM client initialization (will warn about missing keys)")
    print("  - Verify prompt template formatting")
    print("  - Check integration flow logic")
    
    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run comprehensive demo"""
    
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "STEP-7: AI EXTRACTION PIPELINES DEMO" + " "*24 + "║")
    print("║" + " "*78 + "║")
    print("║" + " "*15 + "Demonstrates all 4 AI extraction pipelines for tenders" + " "*11 + "║")
    print("╚" + "="*78 + "╝")
    
    demos = [
        ("1", "Clause Extraction", demo_clause_extraction),
        ("2", "Eligibility Evaluation", demo_eligibility_evaluation),
        ("3", "Risk Analysis", demo_risk_analysis),
        ("4", "Effort Estimation", demo_effort_estimation),
        ("5", "Integrated Analysis & Bid Recommendation", demo_integrated_analysis),
        ("6", "API Key Requirements", demo_api_keys_info),
    ]
    
    print("\nAvailable Demos:")
    for idx, name, _ in demos:
        print(f"  {idx}. {name}")
    print("  0. Run all demos")
    print("  Q. Quit")
    
    try:
        while True:
            choice = input("\nSelect demo (0-6, Q to quit): ").strip().upper()
            
            if choice == "Q":
                print("\nThank you for exploring Step-7!")
                break
            elif choice == "0":
                print("\nRunning all demos...\n")
                for idx, name, demo_func in demos:
                    try:
                        demo_func()
                    except Exception as e:
                        print(f"Error in demo {idx}: {e}")
            else:
                for idx, name, demo_func in demos:
                    if choice == idx:
                        demo_func()
                        break
                else:
                    print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")


if __name__ == "__main__":
    main()
