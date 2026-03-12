"""
Eligibility Evaluator - Step-7 Pipeline

Evaluates company eligibility against tender requirements using LLM.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.ai_schemas import (
    EligibilityReasoningOutput,
    RequirementEvaluation,
    EligibilityRequirement,
)
from app.services.llm_client import LLMClient, LLMModel, get_default_llm_client
from app.services.prompts import PromptManager

logger = logging.getLogger(__name__)


class EligibilityEvaluator:
    """
    Evaluates company eligibility against tender requirements using LLM.
    
    Process:
    1. Extract eligibility requirements from tender
    2. Get company profile/capabilities
    3. Use LLM to reason about each requirement
    4. Generate structured output with evaluations
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize eligibility evaluator"""
        self.llm = llm_client or get_default_llm_client()
        
    def evaluate_eligibility(
        self,
        tender_id: str,
        tender_requirements_text: str,
        company_profile: Dict[str, Any],
        model: Optional[LLMModel] = None
    ) -> EligibilityReasoningOutput:
        """
        Evaluate company eligibility for tender.
        
        Args:
            tender_id: Tender identifier
            tender_requirements_text: Text with eligibility requirements
            company_profile: Company information (name, experience, certifications, etc.)
            model: Optional specific model to use
            
        Returns:
            EligibilityReasoningOutput with evaluations
        """
        
        try:
            logger.info(f"Evaluating eligibility for tender {tender_id}")
            
            # Format company profile as readable text
            company_profile_text = self._format_company_profile(company_profile)
            
            # Get LLM to evaluate
            prompt = PromptManager.get_eligibility_reasoning_prompt(
                company_profile_text,
                tender_requirements_text
            )
            
            if model:
                original_model = self.llm.config.model
                self.llm.config.model = model
            
            logger.info("Sending eligibility evaluation to LLM")
            response = self.llm.generate_json(prompt, EligibilityReasoningOutput)
            
            if model:
                self.llm.config.model = original_model
            
            # Ensure it's properly formatted
            if isinstance(response, dict):
                output = EligibilityReasoningOutput(**response)
            else:
                output = response
            
            logger.info(
                f"Eligibility evaluation complete: "
                f"{output.total_met}/{output.total_requirements} requirements met"
            )
            
            return output
        
        except Exception as e:
            logger.error(f"Error evaluating eligibility: {e}", exc_info=True)
            raise
    
    def evaluate_single_requirement(
        self,
        requirement_id: str,
        requirement_text: str,
        company_profile: Dict[str, Any]
    ) -> Optional[RequirementEvaluation]:
        """
        Evaluate company capability for a single requirement.
        
        Args:
            requirement_id: Requirement identifier
            requirement_text: Requirement text
            company_profile: Company information
            
        Returns:
            Evaluation of this requirement or None
        """
        
        try:
            logger.info(f"Evaluating requirement {requirement_id}")
            
            company_profile_text = self._format_company_profile(company_profile)
            
            prompt = f"""You are a bid qualification analyst. Evaluate if this company meets a tender requirement.

COMPANY:
{company_profile_text}

REQUIREMENT #{requirement_id}:
{requirement_text}

Analyze:
1. Does company meet this requirement? (yes/no)
2. Specific reasoning based on company profile
3. If not met, what is the gap?
4. Recommendation (accept/conditional/reject/clarify)
5. Confidence in assessment (0-1)

Return JSON with:
- requirement_id
- requirement_text
- company_meets (boolean)
- reasoning (detailed)
- confidence (0-1)
- gap_description (if not met)
- recommendation"""
            
            response = self.llm.generate_json(prompt, RequirementEvaluation)
            
            if isinstance(response, dict):
                return RequirementEvaluation(**response)
            
            return response
        
        except Exception as e:
            logger.error(f"Error evaluating requirement {requirement_id}: {e}")
            return None
    
    def batch_evaluate_requirements(
        self,
        requirements: List[tuple[str, str]],  # (requirement_id, requirement_text)
        company_profile: Dict[str, Any]
    ) -> List[RequirementEvaluation]:
        """
        Evaluate multiple requirements in batch.
        
        Args:
            requirements: List of (requirement_id, requirement_text)
            company_profile: Company information
            
        Returns:
            List of requirement evaluations
        """
        
        logger.info(f"Batch evaluating {len(requirements)} requirements")
        
        results = []
        for req_id, req_text in requirements:
            try:
                evaluation = self.evaluate_single_requirement(
                    req_id,
                    req_text,
                    company_profile
                )
                if evaluation:
                    results.append(evaluation)
            except Exception as e:
                logger.warning(f"Failed to evaluate requirement {req_id}: {e}")
        
        return results
    
    def calculate_eligibility_score(self, evaluations: List[RequirementEvaluation]) -> float:
        """
        Calculate eligibility score from evaluations.
        
        Score = (met_requirements / total_requirements) * 100
        """
        if not evaluations:
            return 0.0
        
        met = sum(1 for e in evaluations if e.company_meets)
        total = len(evaluations)
        
        return (met / total) * 100 if total > 0 else 0.0
    
    def identify_critical_gaps(self, evaluations: List[RequirementEvaluation]) -> List[str]:
        """Identify requirements not met that would block the bid"""
        
        critical_gaps = []
        
        for eval in evaluations:
            if not eval.company_meets:
                # Check if this is marked as blocking
                if eval.recommendation in ["reject", "not_eligible"]:
                    critical_gaps.append(
                        f"{eval.requirement_id}: {eval.gap_description or eval.requirement_text}"
                    )
        
        return critical_gaps
    
    def identify_addressable_gaps(self, evaluations: List[RequirementEvaluation]) -> List[str]:
        """Identify requirements not met but addressable before bid"""
        
        addressable_gaps = []
        
        for eval in evaluations:
            if not eval.company_meets:
                if eval.recommendation in ["conditional", "clarify"]:
                    addressable_gaps.append(
                        f"{eval.requirement_id}: {eval.gap_description or eval.requirement_text}"
                    )
        
        return addressable_gaps
    
    def generate_overall_verdict(self, score: float, critical_gaps: List[str]) -> str:
        """
        Generate overall eligibility verdict.
        
        Returns: "eligible", "partially_eligible", "not_eligible"
        """
        
        if critical_gaps:
            return "not_eligible"
        elif score >= 90:
            return "eligible"
        elif score >= 70:
            return "partially_eligible"
        else:
            return "not_eligible"
    
    def _format_company_profile(self, profile: Dict[str, Any]) -> str:
        """Format company profile as readable text for LLM"""
        
        lines = [
            "=== COMPANY PROFILE ===",
            f"Name: {profile.get('name', 'N/A')}",
            f"Industry: {profile.get('industry', 'N/A')}",
            f"Years in Business: {profile.get('years_in_business', 'N/A')}",
        ]
        
        if 'team_size' in profile:
            lines.append(f"Team Size: {profile['team_size']}")
        
        if 'expertise_areas' in profile:
            lines.append(f"Expertise: {', '.join(profile['expertise_areas'])}")
        
        if 'certifications' in profile:
            lines.append(f"Certifications: {', '.join(profile['certifications'])}")
        
        if 'past_projects' in profile:
            lines.append(f"Past Projects: {len(profile['past_projects'])} relevant projects")
        
        if 'financial_capacity' in profile:
            lines.append(f"Annual Revenue: ${profile['financial_capacity']}")
        
        if 'key_team_members' in profile:
            lines.append("Key Team Members:")
            for member in profile['key_team_members']:
                if isinstance(member, dict):
                    lines.append(f"  - {member.get('name')}: {member.get('role')}")
                else:
                    lines.append(f"  - {member}")
        
        if 'additional_info' in profile:
            lines.append(f"Additional: {profile['additional_info']}")
        
        return "\n".join(lines)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def evaluate_eligibility(
    tender_id: str,
    requirements_text: str,
    company_profile: Dict[str, Any]
) -> EligibilityReasoningOutput:
    """Convenience function to evaluate eligibility"""
    evaluator = EligibilityEvaluator()
    return evaluator.evaluate_eligibility(
        tender_id,
        requirements_text,
        company_profile
    )


def evaluate_requirement(
    requirement_id: str,
    requirement_text: str,
    company_profile: Dict[str, Any]
) -> Optional[RequirementEvaluation]:
    """Convenience function to evaluate single requirement"""
    evaluator = EligibilityEvaluator()
    return evaluator.evaluate_single_requirement(
        requirement_id,
        requirement_text,
        company_profile
    )
