"""
Integrated Tender Analysis - Step-7 Master Pipeline

Orchestrates all AI extraction pipelines for comprehensive tender analysis.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.ai_schemas import (
    ClauseExtractionOutput,
    EligibilityReasoningOutput,
    RiskIdentificationOutput,
    EffortEstimationOutput,
    TenderAnalysisIntegration,
)
from app.services.clause_extractor import ClauseExtractor
from app.services.eligibility_evaluator import EligibilityEvaluator
from app.services.risk_analyzer import RiskAnalyzer
from app.services.effort_estimator import EffortEstimator
from app.services.llm_client import LLMClient, LLMModel, get_default_llm_client

logger = logging.getLogger(__name__)


class TenderAnalyzer:
    """
    Master analyzer for comprehensive tender analysis.
    
    Orchestrates all 4 pipelines:
    1. Clause extraction
    2. Eligibility evaluation
    3. Risk analysis
    4. Effort estimation
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize tender analyzer with components"""
        self.llm = llm_client or get_default_llm_client()
        self.clause_extractor = ClauseExtractor(self.llm)
        self.eligibility_evaluator = EligibilityEvaluator(self.llm)
        self.risk_analyzer = RiskAnalyzer(self.llm)
        self.effort_estimator = EffortEstimator(self.llm)
        self.analysis_start_time = None
        
    def analyze_tender(
        self,
        tender_id: str,
        tender_text: str,
        company_profile: Dict[str, Any],
        company_context: str = "",
        model: Optional[LLMModel] = None
    ) -> TenderAnalysisIntegration:
        """
        Perform comprehensive tender analysis.
        
        Runs all 4 pipelines and integrates results.
        
        Args:
            tender_id: Tender identifier
            tender_text: Full tender document text
            company_profile: Company profile for eligibility/risk context
            company_context: Additional company context
            model: Optional specific model to use
            
        Returns:
            Integrated analysis result with bid recommendation
        """
        
        self.analysis_start_time = datetime.now()
        
        try:
            logger.info(f"Starting comprehensive tender analysis for {tender_id}")
            
            # Run all 4 pipelines
            logger.info("Pipeline 1/4: Clause extraction")
            clauses = self.clause_extractor.extract_clauses(tender_id, tender_text, model)
            logger.info(f"  -> Extracted {clauses.total_clauses_found} clauses")
            
            logger.info("Pipeline 2/4: Eligibility evaluation")
            eligibility = self.eligibility_evaluator.evaluate_eligibility(
                tender_id,
                tender_text,
                company_profile,
                model
            )
            logger.info(f"  -> Score: {eligibility.eligibility_score:.1f}%, Verdict: {eligibility.overall_eligibility_verdict}")
            
            logger.info("Pipeline 3/4: Risk analysis")
            risks = self.risk_analyzer.analyze_risks(
                tender_id,
                tender_text,
                company_context,
                model
            )
            logger.info(f"  -> Identified {risks.total_risks_identified} risks (Score: {risks.risk_score:.1f})")
            
            logger.info("Pipeline 4/4: Effort estimation")
            effort = self.effort_estimator.estimate_effort(
                tender_id,
                company_profile.get("company_name", "Project"),
                tender_text,
                model=model
            )
            logger.info(f"  -> Estimated {effort.total_estimated_hours:.0f} hours, ${effort.cost.estimated_cost:,.0f}")
            
            # Integrate results
            logger.info("Integrating results and generating bid recommendation")
            integration = self._integrate_results(
                tender_id,
                clauses,
                eligibility,
                risks,
                effort
            )
            
            elapsed = (datetime.now() - self.analysis_start_time).total_seconds()
            logger.info(f"Analysis complete in {elapsed:.1f} seconds")
            
            return integration
        
        except Exception as e:
            logger.error(f"Error during tender analysis: {e}", exc_info=True)
            raise
    
    def _integrate_results(
        self,
        tender_id: str,
        clauses: ClauseExtractionOutput,
        eligibility: EligibilityReasoningOutput,
        risks: RiskIdentificationOutput,
        effort: EffortEstimationOutput
    ) -> TenderAnalysisIntegration:
        """
        Integrate results from all 4 pipelines.
        
        Generates:
        - Overall recommendation (BID/NO_BID/CONDITIONAL)
        - Key strengths and weaknesses
        - Critical success factors
        - Must-dos before bid
        """
        
        # Determine bid recommendation
        recommendation, reasoning = self._generate_bid_recommendation(
            eligibility,
            risks,
            effort
        )
        
        # Extract company strengths (from eligibility)
        strengths = [
            f"Meets {eligibility.total_met} of {eligibility.total_requirements} eligibility requirements",
        ]
        if eligibility.total_met == eligibility.total_requirements:
            strengths.append("100% eligible for this tender")
        
        # Extract weaknesses (from eligibility and risks)
        weaknesses = [
            f"Identified {risks.total_risks_identified} risks ({risks.critical_risks} critical)",
        ]
        
        if eligibility.critical_gaps:
            weaknesses.extend([f"Critical gap: {gap}" for gap in eligibility.critical_gaps[:3]])
        
        # Critical success factors
        critical_factors = [
            f"Deliver {len(effort.work_packages)} major work packages on schedule",
            "Maintain quality per evaluation criteria",
            "Manage identified risks proactively",
        ]
        
        if risks.deal_breaker_risks:
            critical_factors.extend([
                f"Resolve deal-breaker: {risk}" for risk in risks.deal_breaker_risks[:2]
            ])
        
        # Must-dos
        must_dos = []
        
        # Address critical gaps
        if eligibility.critical_gaps:
            must_dos.extend([
                f"Address critical gap: {gap}" for gap in eligibility.critical_gaps
            ])
        
        # Mitigate deal-breaker risks
        if risks.deal_breaker_risks:
            must_dos.extend([
                f"Resolve deal-breaker risk: {risk}" for risk in risks.deal_breaker_risks
            ])
        
        # Resource planning
        if effort.work_packages:
            total_team = sum(e.recommended_team_size for e in effort.work_packages)
            must_dos.append(f"Secure {total_team} team members for {effort.total_estimated_days:.0f} days")
        
        # Calculate scores
        bid_feasibility = self._calculate_feasibility_score(eligibility, effort)
        risk_adjusted = self._calculate_risk_adjusted_score(
            bid_feasibility,
            risks
        )
        
        return TenderAnalysisIntegration(
            tender_id=tender_id,
            clauses=clauses,
            eligibility=eligibility,
            risks=risks,
            effort=effort,
            overall_recommendation=recommendation,
            go_no_go_reasoning=reasoning,
            bid_feasibility_score=bid_feasibility,
            risk_adjusted_score=risk_adjusted,
            key_strengths=strengths,
            key_weaknesses=weaknesses,
            critical_success_factors=critical_factors,
            must_dos_before_bid=must_dos,
        )
    
    def _generate_bid_recommendation(
        self,
        eligibility: EligibilityReasoningOutput,
        risks: RiskIdentificationOutput,
        effort: EffortEstimationOutput
    ) -> tuple[str, str]:
        """
        Generate bid recommendation based on all factors.
        
        Returns: (recommendation, reasoning)
        """
        
        recommendation = "BID"
        reasoning_points = []
        
        # Eligibility check
        if eligibility.overall_eligibility_verdict == "not_eligible":
            recommendation = "NO_BID"
            reasoning_points.append(f"Not eligible: {len(eligibility.critical_gaps)} critical gaps")
        elif eligibility.overall_eligibility_verdict == "partially_eligible":
            recommendation = "CONDITIONAL"
            reasoning_points.append(f"Partially eligible: {len(eligibility.recommendable_gaps)} addressable gaps")
        else:
            reasoning_points.append(f"Eligible: All key requirements met")
        
        # Risk check
        if risks.overall_risk_level.value == "critical":
            if recommendation == "BID":
                recommendation = "NO_BID"
            reasoning_points.append(f"Critical risk level: {len(risks.deal_breaker_risks)} deal-breaker risks")
        elif risks.overall_risk_level.value == "high":
            if recommendation == "BID":
                recommendation = "CONDITIONAL"
            reasoning_points.append(f"High risk: {risks.high_risks} high-severity risks identified")
        else:
            reasoning_points.append(f"Acceptable risk level")
        
        # Effort check (basic feasibility)
        if effort.total_estimated_hours > 5000:  # Very large effort
            reasoning_points.append(f"High effort: {effort.total_estimated_hours:.0f} hours estimated")
        else:
            reasoning_points.append(f"Effort feasible: {effort.total_estimated_hours:.0f} hours")
        
        reasoning = "; ".join(reasoning_points)
        
        return recommendation, reasoning
    
    def _calculate_feasibility_score(
        self,
        eligibility: EligibilityReasoningOutput,
        effort: EffortEstimationOutput
    ) -> float:
        """Calculate bid feasibility score (0-100)"""
        
        # 50% from eligibility
        eligibility_component = eligibility.eligibility_score * 0.5
        
        # 50% from effort feasibility
        # Assume high effort = lower feasibility
        effort_factor = min(1.0, 100.0 / max(1, effort.total_estimated_hours / 10))
        effort_component = effort_factor * 50
        
        return eligibility_component + effort_component
    
    def _calculate_risk_adjusted_score(
        self,
        feasibility_score: float,
        risks: RiskIdentificationOutput
    ) -> float:
        """Calculate risk-adjusted score (0-100)"""
        
        # Start with feasibility
        adjusted = feasibility_score
        
        # Reduce by risk level
        risk_reduction = (risks.risk_score / 100.0) * 30  # Up to 30 point reduction
        
        adjusted = max(0, adjusted - risk_reduction)
        
        return adjusted
    
    def analyze_tender_full_pipeline(
        self,
        tender_id: str,
        tender_text: str,
        company_profile: Dict[str, Any],
        save_results: bool = False
    ) -> Dict[str, Any]:
        """
        Full pipeline analysis with optional results saving.
        
        Returns analysis results as dictionary.
        """
        
        # Run analysis
        integration = self.analyze_tender(
            tender_id,
            tender_text,
            company_profile
        )
        
        # Convert to dict
        results = {
            "tender_id": tender_id,
            "timestamp": datetime.now().isoformat(),
            "recommendation": integration.overall_recommendation,
            "feasibility_score": integration.bid_feasibility_score,
            "risk_adjusted_score": integration.risk_adjusted_score,
            "eligibility": integration.eligibility.model_dump(),
            "risks": integration.risks.model_dump(),
            "effort": integration.effort.model_dump(),
            "clauses": integration.clauses.model_dump(),
            "summary": {
                "key_strengths": integration.key_strengths,
                "key_weaknesses": integration.key_weaknesses,
                "critical_success_factors": integration.critical_success_factors,
                "must_dos": integration.must_dos_before_bid,
            }
        }
        
        return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def analyze_tender_comprehensive(
    tender_id: str,
    tender_text: str,
    company_profile: Dict[str, Any],
    company_context: str = ""
) -> TenderAnalysisIntegration:
    """Convenience function for comprehensive tender analysis"""
    analyzer = TenderAnalyzer()
    return analyzer.analyze_tender(
        tender_id,
        tender_text,
        company_profile,
        company_context
    )


def get_bid_recommendation(
    tender_id: str,
    tender_text: str,
    company_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """Get bid recommendation for tender"""
    analyzer = TenderAnalyzer()
    integration = analyzer.analyze_tender(tender_id, tender_text, company_profile)
    
    return {
        "tender_id": tender_id,
        "recommendation": integration.overall_recommendation,
        "reasoning": integration.go_no_go_reasoning,
        "feasibility_score": integration.bid_feasibility_score,
        "risk_adjusted_score": integration.risk_adjusted_score,
        "eligibility_score": integration.eligibility.eligibility_score,
        "risk_score": integration.risks.risk_score,
        "effort_hours": integration.effort.total_estimated_hours,
        "cost": integration.effort.cost.estimated_cost,
        "must_dos": integration.must_dos_before_bid[:5],  # Top 5
    }
