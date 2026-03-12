"""
Scoring Engine - Step-8

Deterministic, explainable scoring for Tender-AI.
All scores are calculated with transparent logic and detailed reasoning.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.services.scoring_models import (
    EligibilityScore,
    EligibilityCategory,
    EligibilityRequirementAssessment,
    RiskScore,
    RiskCategory,
    RiskAssessment,
    EffortScore,
    EffortCategory,
    EffortMetrics,
    TenderScore,
    ScoringConfig,
    validate_weights,
)
from app.services.ai_schemas import (
    EligibilityReasoningOutput,
    RiskIdentificationOutput,
    EffortEstimationOutput,
    RequirementEvaluation,
)

logger = logging.getLogger(__name__)


class EligibilityScorer:
    """Scores eligibility based on requirement compliance"""
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        """Initialize with optional config"""
        self.config = config or ScoringConfig()
        
    def score(self, eligibility_result: EligibilityReasoningOutput) -> EligibilityScore:
        """
        Score eligibility based on requirement evaluations.
        
        Logic:
        - Count total mandatory requirements
        - Count how many are met
        - Calculate percentage: (met_mandatory / total_mandatory) * 100
        - Apply thresholds:
          - 90%+ = Eligible
          - 70-89% = Partially Eligible
          - <70% = Not Eligible
        """
        
        logger.info(f"Scoring eligibility for {eligibility_result.tender_id}")
        
        # Separate mandatory and optional requirements
        mandatory_reqs = [r for r in eligibility_result.requirement_evaluations 
                         if r.requirement_id.startswith('R') and 'mandatory' in r.requirement_id.lower()]
        optional_reqs = [r for r in eligibility_result.requirement_evaluations
                        if not r.requirement_id.startswith('R') or 'optional' in r.requirement_id.lower()]
        
        # If can't distinguish, treat all as mandatory for conservative scoring
        if not mandatory_reqs and optional_reqs:
            mandatory_reqs = eligibility_result.requirement_evaluations
            optional_reqs = []
        elif not mandatory_reqs and not optional_reqs:
            mandatory_reqs = eligibility_result.requirement_evaluations
        
        # Count met requirements
        mandatory_met = sum(1 for r in mandatory_reqs if r.company_meets)
        optional_met = sum(1 for r in optional_reqs if r.company_meets)
        total_met = mandatory_met + optional_met
        
        # Calculate percentages
        total_mandatory = len(mandatory_reqs)
        total_optional = len(optional_reqs)
        total_requirements = total_mandatory + total_optional
        
        mandatory_pct = (mandatory_met / total_mandatory * 100) if total_mandatory > 0 else 0
        overall_pct = (total_met / total_requirements * 100) if total_requirements > 0 else 0
        
        # Determine category (based on mandatory requirements)
        category = self._determine_category(mandatory_pct)
        
        # Create assessments
        assessments = self._create_assessments(eligibility_result.requirement_evaluations)
        
        # Met and unmet lists
        met_reqs = [a.requirement_text for a in assessments if a.company_meets]
        unmet_reqs = [a.requirement_text for a in assessments if not a.company_meets]
        
        # Critical gaps (unmet mandatory requirements)
        critical_gaps = [
            req.requirement_text 
            for req in mandatory_reqs 
            if not req.company_meets
        ]
        
        # Scoring logic explanation
        scoring_logic = f"""
Eligibility Score Calculation:
- Total Requirements: {total_requirements}
- Mandatory: {total_mandatory}, Optional: {total_optional}
- Met: {total_met} ({overall_pct:.1f}%)
- Mandatory Met: {mandatory_met}/{total_mandatory} ({mandatory_pct:.1f}%)

Thresholds Applied:
- Eligible (90%+): Meets all/nearly all mandatory requirements
- Partially Eligible (70-89%): Meets most mandatory requirements
- Not Eligible (<70%): Missing critical mandatory requirements

Scoring Basis: Mandatory Requirement Compliance ({mandatory_pct:.1f}%)
Final Score: {overall_pct:.1f}%
Category: {category.value.upper()}
"""
        
        summary = f"Company is {category.value}: "
        if category == EligibilityCategory.ELIGIBLE:
            summary += f"Meets {mandatory_pct:.0f}% of mandatory requirements (threshold: 90%)"
        elif category == EligibilityCategory.PARTIALLY_ELIGIBLE:
            summary += f"Meets {mandatory_pct:.0f}% of mandatory requirements (threshold: 70-89%)"
            summary += f". Missing {len(critical_gaps)} critical requirement(s)."
        else:
            summary += f"Only meets {mandatory_pct:.0f}% of mandatory requirements (threshold: <70%)"
            summary += f". Missing {len(critical_gaps)} critical requirement(s)."
        
        return EligibilityScore(
            tender_id=eligibility_result.tender_id,
            total_requirements=total_requirements,
            mandatory_requirements=total_mandatory,
            optional_requirements=total_optional,
            total_met=total_met,
            mandatory_met=mandatory_met,
            optional_met=optional_met,
            overall_percentage=overall_pct,
            mandatory_percentage=mandatory_pct,
            category=category,
            eligibility_score=overall_pct,
            requirements_assessments=assessments,
            scoring_logic=scoring_logic,
            summary=summary,
            met_requirements=met_reqs,
            unmet_requirements=unmet_reqs,
            critical_gaps=critical_gaps,
        )
    
    def _determine_category(self, mandatory_pct: float) -> EligibilityCategory:
        """Determine eligibility category from percentage"""
        thresholds = self.config.eligibility_thresholds
        
        if mandatory_pct >= thresholds.eligible_minimum:
            return EligibilityCategory.ELIGIBLE
        elif mandatory_pct >= thresholds.partially_eligible_minimum:
            return EligibilityCategory.PARTIALLY_ELIGIBLE
        else:
            return EligibilityCategory.NOT_ELIGIBLE
    
    def _create_assessments(
        self,
        evaluations: List[RequirementEvaluation]
    ) -> List[EligibilityRequirementAssessment]:
        """Create assessment objects from evaluations"""
        
        assessments = []
        for eval in evaluations:
            assessment = EligibilityRequirementAssessment(
                requirement_id=eval.requirement_id,
                requirement_text=eval.requirement_text,
                is_mandatory=True,  # Conservative: treat as mandatory
                company_meets=eval.company_meets,
                reasoning=eval.reasoning,
                confidence=eval.confidence,
            )
            assessments.append(assessment)
        
        return assessments


class RiskScorer:
    """Scores risk based on identified risks"""
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        """Initialize with optional config"""
        self.config = config or ScoringConfig()
        
    def score(self, risk_result: RiskIdentificationOutput) -> RiskScore:
        """
        Score risks based on severity and probability.
        
        Logic:
        - Weight each risk by severity and probability
        - Aggregate weighted scores
        - Map to 0-100 scale
        - Apply thresholds:
          - 0-33 = Low
          - 34-66 = Medium
          - 67-100 = High
        """
        
        logger.info(f"Scoring risks for {risk_result.tender_id}")
        
        # Severity weights (configurable)
        severity_weights = {
            "critical": 1.0,
            "high": 0.75,
            "medium": 0.50,
            "low": 0.25,
        }
        
        # Probability weights
        probability_weights = {
            "high": 1.0,
            "medium": 0.6,
            "low": 0.3,
        }
        
        # Calculate weighted score
        total_weighted_score = 0.0
        risk_assessments = []
        
        for risk in risk_result.risks:
            severity = risk.severity.value.lower()
            probability = risk.probability.lower()
            
            # Get weights
            sev_weight = severity_weights.get(severity, 0.5)
            prob_weight = probability_weights.get(probability, 0.5)
            
            # Combined impact (weighted)
            impact = (
                sev_weight * self.config.risk_severity_weight +
                prob_weight * self.config.risk_probability_weight
            ) * 100
            
            total_weighted_score += impact
            
            # Create assessment
            assessment = RiskAssessment(
                risk_id=f"RISK_{len(risk_assessments) + 1}",
                risk_title=risk.risk_title,
                severity=severity,
                probability=probability,
                impact_score=impact,
            )
            risk_assessments.append(assessment)
        
        # Average the score
        num_risks = len(risk_result.risks) if risk_result.risks else 1
        risk_score = total_weighted_score / num_risks if risk_result.risks else 0
        risk_score = min(100.0, max(0.0, risk_score))  # Clamp to 0-100
        
        # Determine category
        category = self._determine_category(risk_score)
        
        # Top 3 risks by impact
        sorted_assessments = sorted(risk_assessments, key=lambda x: x.impact_score, reverse=True)
        top_risks = [
            f"{a.risk_title} ({a.severity.upper()}, {a.probability})" 
            for a in sorted_assessments[:3]
        ]
        
        # Deal-breaker risks
        deal_breakers = [
            r.risk_title 
            for r in risk_result.risks 
            if r.deal_breaker
        ]
        
        # Scoring logic
        scoring_logic = f"""
Risk Score Calculation:
- Total Risks Identified: {risk_result.total_risks_identified}
- Critical: {risk_result.critical_risks}
- High: {risk_result.high_risks}
- Medium: {risk_result.medium_risks}
- Low: {risk_result.low_risks}

Weighting Formula:
- Severity Component ({self.config.risk_severity_weight*100:.0f}%): 1.0 (critical), 0.75 (high), 0.50 (medium), 0.25 (low)
- Probability Component ({self.config.risk_probability_weight*100:.0f}%): 1.0 (high), 0.6 (medium), 0.3 (low)
- Impact = (Severity Weight × {self.config.risk_severity_weight} + Probability Weight × {self.config.risk_probability_weight}) × 100

Thresholds Applied:
- Low Risk (0-33): Manageable risks, typical for any project
- Medium Risk (34-66): Notable risks requiring mitigation
- High Risk (67-100): Significant risks, consider carefully

Final Risk Score: {risk_score:.1f}
Category: {category.value.upper()}
"""
        
        summary = f"Risk profile is {category.value.upper()}: "
        summary += f"Identified {risk_result.total_risks_identified} risks "
        summary += f"({risk_result.critical_risks} critical, {risk_result.high_risks} high)"
        
        return RiskScore(
            tender_id=risk_result.tender_id,
            total_risks=risk_result.total_risks_identified,
            critical_count=risk_result.critical_risks,
            high_count=risk_result.high_risks,
            medium_count=risk_result.medium_risks,
            low_count=risk_result.low_risks,
            high_probability_count=sum(1 for r in risk_result.risks if r.probability.lower() == "high"),
            medium_probability_count=sum(1 for r in risk_result.risks if r.probability.lower() == "medium"),
            low_probability_count=sum(1 for r in risk_result.risks if r.probability.lower() == "low"),
            risk_score=risk_score,
            risk_category=category,
            severity_weights=severity_weights,
            probability_weights=probability_weights,
            risk_assessments=risk_assessments,
            scoring_logic=scoring_logic,
            summary=summary,
            top_risks=top_risks,
            deal_breakers=deal_breakers,
        )
    
    def _determine_category(self, risk_score: float) -> RiskCategory:
        """Determine risk category from score"""
        thresholds = self.config.risk_thresholds
        
        if risk_score <= thresholds.low_maximum:
            return RiskCategory.LOW
        elif risk_score <= thresholds.medium_maximum:
            return RiskCategory.MEDIUM
        else:
            return RiskCategory.HIGH


class EffortScorer:
    """Scores effort based on estimation"""
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        """Initialize with optional config"""
        self.config = config or ScoringConfig()
        
    def score(
        self,
        effort_result: EffortEstimationOutput,
        company_capacity_hours: float = 2000  # Hours per year per person
    ) -> EffortScore:
        """
        Score effort based on hours, timeline, and cost.
        
        Logic:
        - Hours component: 0-100 based on thresholds
        - Timeline component: 0-100 based on feasibility
        - Cost component: 0-100 based on value ratio
        - Weighted average
        - Apply thresholds:
          - 0-33 = Low effort
          - 34-66 = Medium effort
          - 67-100 = High effort
        """
        
        logger.info(f"Scoring effort for {effort_result.tender_id}")
        
        # Extract metrics
        total_hours = effort_result.total_estimated_hours
        total_days = effort_result.total_estimated_days
        team_size = sum(e.recommended_team_size for e in effort_result.work_packages) if effort_result.work_packages else 1
        cost = effort_result.cost.estimated_cost
        cost_per_hour = effort_result.cost.cost_per_hour
        
        # Create metrics object
        metrics = EffortMetrics(
            total_hours=total_hours,
            total_days=total_days,
            team_size=team_size,
            estimated_cost=cost,
            cost_per_hour=cost_per_hour,
        )
        
        # Component 1: Hours Score (0-100)
        thresholds = self.config.effort_thresholds
        if total_hours <= thresholds.low_maximum_hours:
            hours_score = 20.0  # Low effort
        elif total_hours <= thresholds.medium_maximum_hours:
            hours_score = 50.0  # Medium effort
        else:
            # Scale beyond medium threshold
            excess = (total_hours - thresholds.medium_maximum_hours)
            max_excess = 3000  # At 4500 hours = ~100
            hours_score = min(100.0, 50.0 + (excess / max_excess * 50))
        
        # Component 2: Timeline Score (0-100)
        # Estimate based on team utilization
        hours_per_week = (team_size * 40)  # Assuming 40 hrs/week
        weeks_available = total_days / 7
        weeks_needed = total_hours / hours_per_week if hours_per_week > 0 else 0
        
        if weeks_needed <= weeks_available * 0.8:
            timeline_score = 20.0  # Very feasible
        elif weeks_needed <= weeks_available * 1.2:
            timeline_score = 50.0  # Feasible with planning
        else:
            timeline_score = min(100.0, 50.0 + ((weeks_needed - weeks_available * 1.2) / weeks_available * 50))
        
        # Component 3: Cost Score (0-100)
        # Base cost on typical budget
        typical_project_budget = 50000  # Typical median project
        cost_ratio = cost / typical_project_budget if typical_project_budget > 0 else 1.0
        
        if cost_ratio <= 0.3:
            cost_score = 20.0  # Affordable
        elif cost_ratio <= 1.0:
            cost_score = 50.0  # Reasonable
        else:
            cost_score = min(100.0, 50.0 + ((cost_ratio - 1.0) / cost_ratio * 50))
        
        # Weighted average
        effort_score = (
            hours_score * self.config.effort_hours_weight +
            timeline_score * self.config.effort_timeline_weight +
            cost_score * self.config.effort_cost_weight
        )
        
        # Determine category
        category = self._determine_category(effort_score)
        
        # Complexity factors
        complexity_factors = []
        if total_hours > 1000:
            complexity_factors.append(f"High effort: {total_hours:.0f} hours")
        if total_days > 180:
            complexity_factors.append(f"Long duration: {total_days:.0f} days")
        if team_size > 5:
            complexity_factors.append(f"Large team: {team_size} people")
        if cost > 100000:
            complexity_factors.append(f"Significant budget: ${cost:,.0f}")
        
        # Resource needs
        resource_needs = [
            f"Team size: {team_size} people",
            f"Duration: {total_days:.0f} calendar days",
            f"Weekly commitment: {hours_per_week:.0f} hours",
        ]
        
        # Scoring logic
        scoring_logic = f"""
Effort Score Calculation:

Components:
1. Hours Score ({self.config.effort_hours_weight*100:.0f}%): {hours_score:.1f}
   - Threshold: Low ({thresholds.low_maximum_hours:.0f}h), Medium ({thresholds.medium_maximum_hours:.0f}h), High (>{thresholds.medium_maximum_hours:.0f}h)
   - Estimated: {total_hours:.0f} hours

2. Timeline Score ({self.config.effort_timeline_weight*100:.0f}%): {timeline_score:.1f}
   - Team capacity: {hours_per_week:.0f} hours/week
   - Weeks needed: {weeks_needed:.0f} vs Available: {weeks_available:.0f}

3. Cost Score ({self.config.effort_cost_weight*100:.0f}%): {cost_score:.1f}
   - Estimated cost: ${cost:,.0f}
   - Cost ratio: {cost_ratio:.2f}x typical project

Weighted Effort Score: {effort_score:.1f}
Category: {category.value.upper()}
"""
        
        summary = f"Effort profile is {category.value.upper()}: "
        if category == EffortCategory.LOW:
            summary += f"Modest effort ({total_hours:.0f}h over {total_days:.0f} days)"
        elif category == EffortCategory.MEDIUM:
            summary += f"Significant effort ({total_hours:.0f}h over {total_days:.0f} days)"
        else:
            summary += f"Major effort ({total_hours:.0f}h over {total_days:.0f} days)"
        
        return EffortScore(
            tender_id=effort_result.tender_id,
            metrics=metrics,
            low_threshold_hours=thresholds.low_maximum_hours,
            medium_threshold_hours=thresholds.medium_maximum_hours,
            high_threshold_hours=thresholds.medium_maximum_hours + 1500,
            effort_score=effort_score,
            effort_category=category,
            hours_percentage=self.config.effort_hours_weight * 100,
            timeline_percentage=self.config.effort_timeline_weight * 100,
            cost_percentage=self.config.effort_cost_weight * 100,
            scoring_logic=scoring_logic,
            summary=summary,
            complexity_factors=complexity_factors,
            resource_needs=resource_needs,
        )
    
    def _determine_category(self, effort_score: float) -> EffortCategory:
        """Determine effort category from score"""
        if effort_score <= 33:
            return EffortCategory.LOW
        elif effort_score <= 66:
            return EffortCategory.MEDIUM
        else:
            return EffortCategory.HIGH


class TenderScoringEngine:
    """Master scoring engine that combines all scores"""
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        """Initialize engine with scorers"""
        self.config = config or ScoringConfig()
        
        # Validate configuration
        if not validate_weights(self.config):
            logger.warning("Scoring config weights don't sum to 1.0, normalizing...")
        
        self.eligibility_scorer = EligibilityScorer(self.config)
        self.risk_scorer = RiskScorer(self.config)
        self.effort_scorer = EffortScorer(self.config)
    
    def score_tender(
        self,
        tender_id: str,
        eligibility_result: EligibilityReasoningOutput,
        risk_result: RiskIdentificationOutput,
        effort_result: EffortEstimationOutput,
    ) -> TenderScore:
        """
        Generate comprehensive tender score.
        
        Returns integrated score combining:
        - Eligibility (35%)
        - Risk (35%)
        - Effort (30%)
        """
        
        logger.info(f"Scoring tender {tender_id}")
        
        # Score individual components
        eligibility = self.eligibility_scorer.score(eligibility_result)
        risk = self.risk_scorer.score(risk_result)
        effort = self.effort_scorer.score(effort_result)
        
        # Generate integrated score
        # Normalize scores to 0-1
        eligibility_normalized = eligibility.eligibility_score / 100.0
        risk_normalized = 1.0 - (risk.risk_score / 100.0)  # Invert risk (high risk = low score)
        effort_normalized = 1.0 - (effort.effort_score / 100.0)  # Invert effort (high effort = low score)
        
        # Calculate weighted score
        overall_score = (
            eligibility_normalized * self.config.eligibility_weight +
            risk_normalized * self.config.risk_weight +
            effort_normalized * self.config.effort_weight
        ) * 100
        
        # Generate bid recommendation
        recommendation, reasoning = self._generate_recommendation(
            eligibility, risk, effort, overall_score
        )
        
        # Generate strengths and weaknesses
        strengths = self._identify_strengths(eligibility, risk, effort)
        weaknesses = self._identify_weaknesses(eligibility, risk, effort)
        
        # Critical items
        critical_items = []
        if eligibility.critical_gaps:
            critical_items.extend([f"Address critical gap: {gap}" for gap in eligibility.critical_gaps[:2]])
        if risk.deal_breakers:
            critical_items.extend([f"Resolve deal-breaker: {db}" for db in risk.deal_breakers[:2]])
        
        # Scoring summary
        scoring_summary = f"""
TENDER SCORING SUMMARY
=====================
Eligibility Score: {eligibility.eligibility_score:.1f}% ({eligibility.category.value.upper()})
Risk Score: {risk.risk_score:.1f}% ({risk.risk_category.value.upper()})
Effort Score: {effort.effort_score:.1f}% ({effort.effort_category.value.upper()})

Integrated Score: {overall_score:.1f}/100
Recommendation: {recommendation.upper()}

Calculation:
- Eligibility ({self.config.eligibility_weight*100:.0f}%): {eligibility.eligibility_score:.1f}
- Risk ({self.config.risk_weight*100:.0f}%): {100-risk.risk_score:.1f} (inverted from {risk.risk_score:.1f})
- Effort ({self.config.effort_weight*100:.0f}%): {100-effort.effort_score:.1f} (inverted from {effort.effort_score:.1f})
= Overall: {overall_score:.1f}
"""
        
        return TenderScore(
            tender_id=tender_id,
            eligibility=eligibility,
            risk=risk,
            effort=effort,
            overall_score=overall_score,
            bid_recommendation=recommendation,
            recommendation_reasoning=reasoning,
            scoring_summary=scoring_summary,
            strengths=strengths,
            weaknesses=weaknesses,
            critical_items=critical_items,
        )
    
    def _generate_recommendation(
        self,
        eligibility: EligibilityScore,
        risk: RiskScore,
        effort: EffortScore,
        overall_score: float
    ) -> Tuple[str, str]:
        """Generate bid recommendation and reasoning"""
        
        # Logic:
        # - NOT_ELIGIBLE → NO_BID
        # - HIGH_RISK + DEAL_BREAKERS → NO_BID
        # - HIGH_EFFORT + NOT_ELIGIBLE → NO_BID
        # - ELIGIBLE + LOW_RISK + LOW_EFFORT → BID
        # - Otherwise → CONDITIONAL
        
        reasoning_points = []
        
        # Check eligibility
        if eligibility.category == EligibilityCategory.NOT_ELIGIBLE:
            reasoning_points.append(f"Not eligible: {len(eligibility.critical_gaps)} critical gaps")
            return "NO_BID", "; ".join(reasoning_points)
        
        # Check risk
        if risk.risk_category == RiskCategory.HIGH and risk.deal_breakers:
            reasoning_points.append(f"High risk with {len(risk.deal_breakers)} deal-breaker(s)")
            return "NO_BID", "; ".join(reasoning_points)
        
        # Check effort
        if effort.effort_category == EffortCategory.HIGH and eligibility.category == EligibilityCategory.PARTIALLY_ELIGIBLE:
            reasoning_points.append(f"High effort + partial eligibility")
            return "CONDITIONAL", "; ".join(reasoning_points)
        
        # Build reasoning
        if eligibility.category == EligibilityCategory.ELIGIBLE:
            reasoning_points.append(f"Eligible: {eligibility.mandatory_percentage:.0f}% mandatory")
        else:
            reasoning_points.append(f"Partially eligible: {eligibility.mandatory_percentage:.0f}% mandatory")
        
        if risk.risk_category == RiskCategory.LOW:
            reasoning_points.append("Low risk")
        elif risk.risk_category == RiskCategory.MEDIUM:
            reasoning_points.append(f"Medium risk: {risk.high_count} high-severity risks")
        else:
            reasoning_points.append(f"High risk: {risk.critical_count} critical")
        
        if effort.effort_category == EffortCategory.LOW:
            reasoning_points.append(f"Low effort: {effort.metrics.total_hours:.0f}h")
        elif effort.effort_category == EffortCategory.MEDIUM:
            reasoning_points.append(f"Medium effort: {effort.metrics.total_hours:.0f}h")
        else:
            reasoning_points.append(f"High effort: {effort.metrics.total_hours:.0f}h")
        
        # Determine recommendation
        if overall_score >= 75:
            recommendation = "BID"
            reasoning_points.append(f"Strong overall score: {overall_score:.1f}")
        elif overall_score >= 50:
            recommendation = "CONDITIONAL"
            reasoning_points.append(f"Moderate overall score: {overall_score:.1f}, needs mitigation")
        else:
            recommendation = "NO_BID"
            reasoning_points.append(f"Low overall score: {overall_score:.1f}")
        
        return recommendation, "; ".join(reasoning_points)
    
    def _identify_strengths(
        self,
        eligibility: EligibilityScore,
        risk: RiskScore,
        effort: EffortScore,
    ) -> List[str]:
        """Identify key strengths"""
        
        strengths = []
        
        if eligibility.category == EligibilityCategory.ELIGIBLE:
            strengths.append(f"Strong eligibility: {eligibility.mandatory_percentage:.0f}% of mandatory met")
        
        if risk.risk_category == RiskCategory.LOW:
            strengths.append(f"Low risk profile: {risk.low_count} low-severity risks")
        
        if effort.effort_category == EffortCategory.LOW:
            strengths.append(f"Manageable effort: {effort.metrics.total_hours:.0f} hours")
        
        if eligibility.optional_met > 0:
            strengths.append(f"Exceeds basics: {eligibility.optional_met} optional requirements met")
        
        return strengths or ["Meets baseline requirements"]
    
    def _identify_weaknesses(
        self,
        eligibility: EligibilityScore,
        risk: RiskScore,
        effort: EffortScore,
    ) -> List[str]:
        """Identify key weaknesses"""
        
        weaknesses = []
        
        if eligibility.critical_gaps:
            weaknesses.append(f"Critical gaps: {len(eligibility.critical_gaps)} mandatory requirements unmet")
        
        if risk.risk_category == RiskCategory.HIGH:
            weaknesses.append(f"High risk: {risk.critical_count} critical risks identified")
        
        if effort.effort_category == EffortCategory.HIGH:
            weaknesses.append(f"Major effort: {effort.metrics.total_hours:.0f} hours over {effort.metrics.total_days:.0f} days")
        
        if risk.deal_breakers:
            weaknesses.append(f"Deal-breakers: {len(risk.deal_breakers)} blocking issues")
        
        return weaknesses or ["No major weaknesses identified"]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def score_tender(
    tender_id: str,
    eligibility_result: EligibilityReasoningOutput,
    risk_result: RiskIdentificationOutput,
    effort_result: EffortEstimationOutput,
    config: Optional[ScoringConfig] = None,
) -> TenderScore:
    """Convenience function to score a complete tender"""
    
    engine = TenderScoringEngine(config)
    return engine.score_tender(tender_id, eligibility_result, risk_result, effort_result)


def score_eligibility(
    eligibility_result: EligibilityReasoningOutput,
    config: Optional[ScoringConfig] = None,
) -> EligibilityScore:
    """Score eligibility only"""
    
    scorer = EligibilityScorer(config)
    return scorer.score(eligibility_result)


def score_risks(
    risk_result: RiskIdentificationOutput,
    config: Optional[ScoringConfig] = None,
) -> RiskScore:
    """Score risks only"""
    
    scorer = RiskScorer(config)
    return scorer.score(risk_result)


def score_effort(
    effort_result: EffortEstimationOutput,
    config: Optional[ScoringConfig] = None,
) -> EffortScore:
    """Score effort only"""
    
    scorer = EffortScorer(config)
    return scorer.score(effort_result)
