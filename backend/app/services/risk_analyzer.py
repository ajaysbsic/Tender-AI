"""
Risk Analyzer - Step-7 Pipeline

Identifies and analyzes risks in tender documents using LLM.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.ai_schemas import (
    RiskIdentificationOutput,
    IdentifiedRisk,
    RiskLevel,
)
from app.services.llm_client import LLMClient, LLMModel, get_default_llm_client
from app.services.prompts import PromptManager

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    Analyzes and identifies risks in tender documents using LLM.
    
    Process:
    1. Extract risk-bearing clauses from tender
    2. Use LLM to identify specific risks with clause-level analysis
    3. Assess severity, probability, and business impact
    4. Identify deal-breaker risks
    5. Suggest mitigations
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize risk analyzer"""
        self.llm = llm_client or get_default_llm_client()
        
    def analyze_risks(
        self,
        tender_id: str,
        tender_text: str,
        company_context: str = "",
        model: Optional[LLMModel] = None
    ) -> RiskIdentificationOutput:
        """
        Analyze and identify risks in tender document.
        
        Args:
            tender_id: Tender identifier
            tender_text: Full tender text
            company_context: Company information for context
            model: Optional specific model to use
            
        Returns:
            RiskIdentificationOutput with identified risks
        """
        
        try:
            logger.info(f"Analyzing risks for tender {tender_id}")
            
            # Get LLM to identify risks
            prompt = PromptManager.get_risk_identification_prompt(
                tender_text,
                company_context or "General risk analysis mode"
            )
            
            if model:
                original_model = self.llm.config.model
                self.llm.config.model = model
            
            logger.info("Sending risk analysis to LLM")
            response = self.llm.generate_json(prompt, RiskIdentificationOutput)
            
            if model:
                self.llm.config.model = original_model
            
            # Ensure proper format
            if isinstance(response, dict):
                output = RiskIdentificationOutput(**response)
            else:
                output = response
            
            logger.info(
                f"Risk analysis complete: "
                f"Identified {len(output.risks)} risks "
                f"({output.critical_risks} critical, {output.high_risks} high)"
            )
            
            return output
        
        except Exception as e:
            logger.error(f"Error analyzing risks: {e}", exc_info=True)
            raise
    
    def identify_single_risk(
        self,
        risk_source: str,
        risk_context: str,
        company_context: str = ""
    ) -> Optional[IdentifiedRisk]:
        """
        Identify a single risk from a clause or requirement.
        
        Args:
            risk_source: Clause/requirement with potential risk
            risk_context: Context about what could go wrong
            company_context: Company context for assessment
            
        Returns:
            Identified risk or None
        """
        
        try:
            logger.info("Analyzing single risk")
            
            prompt = f"""You are a contract risk analyst. Identify and analyze this risk:

SOURCE:
{risk_source}

CONTEXT:
{risk_context}

COMPANY:
{company_context or "General company context"}

Analyze:
1. What is the risk? (specific, from clause)
2. What causes it? (clause-level analysis)
3. Severity: critical/high/medium/low
4. Probability: low/medium/high
5. What happens if it occurs?
6. Can we mitigate? (yes/no)
7. Mitigation strategies
8. Is it a deal-breaker?
9. Business impact

Return JSON with:
- risk_id
- risk_title
- risk_description
- severity
- probability
- deal_breaker (boolean)
- mitigations (list)
- etc."""
            
            response = self.llm.generate_json(prompt, IdentifiedRisk)
            
            if isinstance(response, dict):
                return IdentifiedRisk(**response)
            
            return response
        
        except Exception as e:
            logger.error(f"Error identifying single risk: {e}")
            return None
    
    def batch_identify_risks(
        self,
        risk_sources: List[tuple[str, str]],  # (source_id, source_text)
        company_context: str = ""
    ) -> List[IdentifiedRisk]:
        """
        Identify multiple risks in batch.
        
        Args:
            risk_sources: List of (source_id, source_text)
            company_context: Company context
            
        Returns:
            List of identified risks
        """
        
        logger.info(f"Batch analyzing {len(risk_sources)} potential risks")
        
        results = []
        for source_id, source_text in risk_sources:
            try:
                risk = self.identify_single_risk(
                    source_text,
                    f"Risk source: {source_id}",
                    company_context
                )
                if risk:
                    results.append(risk)
            except Exception as e:
                logger.warning(f"Failed to analyze risk from {source_id}: {e}")
        
        return results
    
    def calculate_risk_score(self, risks: List[IdentifiedRisk]) -> float:
        """
        Calculate overall risk score.
        
        Score 0-100 where:
        - 0-20: Low risk
        - 21-40: Medium-low risk
        - 41-60: Medium risk
        - 61-80: High risk
        - 81-100: Critical risk
        """
        
        if not risks:
            return 0.0
        
        # Weight by severity
        severity_scores = {
            RiskLevel.CRITICAL: 100,
            RiskLevel.HIGH: 75,
            RiskLevel.MEDIUM: 50,
            RiskLevel.LOW: 25,
        }
        
        # Weight by probability
        prob_multipliers = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4,
        }
        
        total_score = 0.0
        for risk in risks:
            severity_score = severity_scores.get(risk.severity, 50)
            prob_mult = prob_multipliers.get(risk.probability.lower(), 0.5)
            
            risk_score = (severity_score * prob_mult) / 100
            total_score += risk_score
        
        # Average across risks
        avg_score = (total_score / len(risks)) * 100
        return min(avg_score, 100.0)
    
    def categorize_risks_by_severity(self, risks: List[IdentifiedRisk]) -> Dict[RiskLevel, List[IdentifiedRisk]]:
        """Group risks by severity level"""
        
        categorized = {
            RiskLevel.CRITICAL: [],
            RiskLevel.HIGH: [],
            RiskLevel.MEDIUM: [],
            RiskLevel.LOW: [],
        }
        
        for risk in risks:
            categorized[risk.severity].append(risk)
        
        return categorized
    
    def identify_deal_breaker_risks(self, risks: List[IdentifiedRisk]) -> List[str]:
        """Identify risks that would block the bid"""
        
        deal_breakers = []
        
        for risk in risks:
            if risk.deal_breaker:
                deal_breakers.append(
                    f"{risk.risk_title} ({risk.risk_category}): {risk.impact_if_occurs}"
                )
        
        return deal_breakers
    
    def suggest_top_mitigations(self, risks: List[IdentifiedRisk], top_n: int = 5) -> List[str]:
        """Suggest top mitigations for highest severity risks"""
        
        # Sort by severity and probability
        severity_rank = {RiskLevel.CRITICAL: 4, RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}
        prob_rank = {"high": 3, "medium": 2, "low": 1}
        
        sorted_risks = sorted(
            risks,
            key=lambda r: (
                severity_rank.get(r.severity, 0),
                prob_rank.get(r.probability.lower(), 0)
            ),
            reverse=True
        )
        
        mitigations = []
        for risk in sorted_risks[:top_n]:
            if risk.can_mitigate and risk.mitigations:
                for mitigation in risk.mitigations[:1]:  # Top mitigation per risk
                    mitigations.append(
                        f"For '{risk.risk_title}': {mitigation}"
                    )
        
        return mitigations
    
    def assess_overall_risk_level(self, risk_score: float) -> RiskLevel:
        """Assess overall risk level from score"""
        
        if risk_score >= 80:
            return RiskLevel.CRITICAL
        elif risk_score >= 60:
            return RiskLevel.HIGH
        elif risk_score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


# ============================================================================
# RISK ASSESSMENT UTILITIES
# ============================================================================

class RiskCategories:
    """Risk categorization"""
    
    CONTRACTUAL = [
        "Liability limitations",
        "Indemnification",
        "Warranties",
        "IP ownership",
    ]
    
    TIMELINE = [
        "Impossible deadlines",
        "Dependency risks",
        "Resource constraints",
    ]
    
    FINANCIAL = [
        "Fixed price uncertainty",
        "Payment terms",
        "Penalty clauses",
        "Price escalation",
    ]
    
    TECHNICAL = [
        "Scope creep",
        "Technology risks",
        "Integration complexity",
        "Knowledge gaps",
    ]
    
    LEGAL = [
        "Compliance requirements",
        "Regulatory changes",
        "Jurisdiction issues",
    ]
    
    REPUTATIONAL = [
        "Client expectations",
        "Quality issues",
        "Delivery failure",
    ]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def analyze_tender_risks(
    tender_id: str,
    tender_text: str,
    company_context: str = ""
) -> RiskIdentificationOutput:
    """Convenience function to analyze tender risks"""
    analyzer = RiskAnalyzer()
    return analyzer.analyze_risks(tender_id, tender_text, company_context)


def identify_risk(
    risk_source: str,
    context: str,
    company_context: str = ""
) -> Optional[IdentifiedRisk]:
    """Convenience function to identify single risk"""
    analyzer = RiskAnalyzer()
    return analyzer.identify_single_risk(risk_source, context, company_context)
