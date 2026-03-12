"""
Effort Estimator - Step-7 Pipeline

Estimates project effort, timeline, and cost using LLM.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.services.ai_schemas import (
    EffortEstimationOutput,
    EffortEstimate,
    TimelineEstimate,
    CostEstimate,
    EffortLevel,
)
from app.services.llm_client import LLMClient, LLMModel, get_default_llm_client
from app.services.prompts import PromptManager

logger = logging.getLogger(__name__)


class EffortEstimator:
    """
    Estimates project effort, timeline, and cost using LLM.
    
    Process:
    1. Extract deliverables and requirements from tender
    2. Break into work packages
    3. Use LLM to estimate effort for each package
    4. Calculate timeline and cost
    5. Generate comprehensive estimation output
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize effort estimator"""
        self.llm = llm_client or get_default_llm_client()
        
    def estimate_effort(
        self,
        tender_id: str,
        project_scope: str,
        requirements_text: str,
        resource_rates: Optional[Dict[str, float]] = None,
        company_type: str = "engineering",
        model: Optional[LLMModel] = None
    ) -> EffortEstimationOutput:
        """
        Estimate project effort, timeline, and cost.
        
        Args:
            tender_id: Tender identifier
            project_scope: Project scope description
            requirements_text: Deliverables and requirements
            resource_rates: Dictionary of role -> hourly rate
            company_type: Type of company (for context)
            model: Optional specific model to use
            
        Returns:
            EffortEstimationOutput with detailed estimates
        """
        
        try:
            logger.info(f"Estimating effort for tender {tender_id}")
            
            # Format resource rates
            resource_rates_text = self._format_resource_rates(resource_rates)
            
            # Get LLM to estimate
            prompt = PromptManager.get_effort_estimation_prompt(
                tender_id=tender_id,
                project_scope=project_scope,
                requirements_text=requirements_text,
                resource_rates=resource_rates_text,
                company_type=company_type
            )
            
            if model:
                original_model = self.llm.config.model
                self.llm.config.model = model
            
            logger.info("Sending effort estimation to LLM")
            response = self.llm.generate_json(prompt, EffortEstimationOutput)
            
            if model:
                self.llm.config.model = original_model
            
            # Ensure proper format
            if isinstance(response, dict):
                output = EffortEstimationOutput(**response)
            else:
                output = response
            
            logger.info(
                f"Effort estimation complete: "
                f"{output.total_estimated_hours:.0f} hours, "
                f"${output.cost.estimated_cost:,.0f}"
            )
            
            return output
        
        except Exception as e:
            logger.error(f"Error estimating effort: {e}", exc_info=True)
            raise
    
    def estimate_work_package(
        self,
        package_id: str,
        package_description: str,
        requirements: List[str],
        complexity_hints: Optional[str] = None
    ) -> Optional[EffortEstimate]:
        """
        Estimate effort for a single work package.
        
        Args:
            package_id: Work package identifier
            package_description: Package description
            requirements: List of requirements this package fulfills
            complexity_hints: Optional hints about complexity
            
        Returns:
            Effort estimate for package
        """
        
        try:
            logger.info(f"Estimating work package {package_id}")
            
            prompt = f"""You are an experienced project estimator. Estimate effort for this work package:

PACKAGE: {package_id}
DESCRIPTION:
{package_description}

REQUIREMENTS:
{chr(10).join(f'- {r}' for r in requirements)}

{f'HINTS: {complexity_hints}' if complexity_hints else ''}

Estimate:
1. Effort in hours (base, low, high estimates)
2. Complexity level (trivial/low/medium/high/very_high)
3. Estimation basis (why these hours?)
4. Key complexity drivers
5. Assumptions made
6. Required skills
7. Recommended team size
8. Specialists needed
9. Risks that could affect effort

Return JSON with EffortEstimate structure."""
            
            response = self.llm.generate_json(prompt, EffortEstimate)
            
            if isinstance(response, dict):
                return EffortEstimate(**response)
            
            return response
        
        except Exception as e:
            logger.error(f"Error estimating package {package_id}: {e}")
            return None
    
    def batch_estimate_packages(
        self,
        packages: List[tuple[str, str, List[str]]]  # (id, description, requirements)
    ) -> List[EffortEstimate]:
        """
        Estimate multiple work packages in batch.
        
        Args:
            packages: List of (package_id, description, requirements)
            
        Returns:
            List of effort estimates
        """
        
        logger.info(f"Batch estimating {len(packages)} work packages")
        
        results = []
        for pkg_id, pkg_desc, pkg_reqs in packages:
            try:
                estimate = self.estimate_work_package(
                    pkg_id,
                    pkg_desc,
                    pkg_reqs
                )
                if estimate:
                    results.append(estimate)
            except Exception as e:
                logger.warning(f"Failed to estimate package {pkg_id}: {e}")
        
        return results
    
    def calculate_total_effort(self, estimates: List[EffortEstimate]) -> float:
        """Calculate total effort from package estimates"""
        return sum(e.estimated_hours for e in estimates)
    
    def calculate_timeline(
        self,
        total_hours: float,
        team_size: int = 1,
        working_days_per_week: float = 5.0,
        hours_per_day: float = 8.0
    ) -> float:
        """
        Calculate timeline in days.
        
        Simple calculation: total_hours / (team_size * hours_per_day * working_days_per_week)
        Actual timeline will be longer due to dependencies and coordination.
        """
        
        if team_size <= 0 or hours_per_day <= 0 or working_days_per_week <= 0:
            return 0.0
        
        hours_per_week = team_size * hours_per_day * working_days_per_week
        weeks = total_hours / hours_per_week
        days = weeks * working_days_per_week
        
        return days
    
    def calculate_cost(
        self,
        estimates: List[EffortEstimate],
        hourly_rates: Optional[Dict[str, float]] = None,
        overhead_percentage: float = 0.2,  # 20% overhead
        contingency_percentage: float = 0.15  # 15% contingency
    ) -> CostEstimate:
        """
        Calculate total project cost.
        
        Args:
            estimates: Work package estimates
            hourly_rates: Dictionary of skill -> hourly rate
            overhead_percentage: Overhead as % of labor
            contingency_percentage: Contingency as % of total
            
        Returns:
            CostEstimate with breakdown
        """
        
        # Default rates if not provided
        if not hourly_rates:
            hourly_rates = {
                "junior": 50.0,
                "senior": 100.0,
                "specialist": 150.0,
                "average": 80.0,
            }
        
        # Calculate labor cost
        total_labor = 0.0
        for estimate in estimates:
            # Simple: use average rate
            rate = hourly_rates.get("average", 80.0)
            total_labor += estimate.estimated_hours * rate
        
        # Add overhead
        overhead_cost = total_labor * overhead_percentage
        
        # Subtotal
        subtotal = total_labor + overhead_cost
        
        # Add contingency
        contingency = subtotal * contingency_percentage
        
        total_cost = subtotal + contingency
        
        return CostEstimate(
            estimated_cost=total_cost,
            cost_range_low=subtotal,
            cost_range_high=subtotal + (subtotal * 0.3),  # 30% uncertainty
            currency="USD",
            labor_cost=total_labor,
            tools_licenses_cost=subtotal * 0.1,  # Estimate 10% for tools
            infrastructure_cost=0.0,
            contingency_cost=contingency,
            cost_per_hour=hourly_rates.get("average", 80.0),
            estimation_basis="Based on effort estimates and hourly rates"
        )
    
    def assess_effort_level(self, total_hours: float) -> EffortLevel:
        """Assess overall effort level"""
        
        if total_hours < 160:  # < 1 person-month
            return EffortLevel.TRIVIAL
        elif total_hours < 320:  # ~ 1 person-month
            return EffortLevel.LOW
        elif total_hours < 960:  # ~ 3 person-months
            return EffortLevel.MEDIUM
        elif total_hours < 2400:  # ~ 8 person-months
            return EffortLevel.HIGH
        else:
            return EffortLevel.VERY_HIGH
    
    def identify_critical_path(
        self,
        estimates: List[EffortEstimate]
    ) -> List[str]:
        """
        Identify work packages on critical path (high effort, high dependencies).
        
        In simple case, just return highest effort packages.
        """
        
        sorted_estimates = sorted(
            estimates,
            key=lambda e: e.estimated_hours,
            reverse=True
        )
        
        return [e.package_id for e in sorted_estimates[:3]]
    
    def _format_resource_rates(self, rates: Optional[Dict[str, float]]) -> str:
        """Format resource rates for LLM"""
        
        if not rates:
            return "Standard consulting rates (Junior: $50/hr, Senior: $100/hr, Specialist: $150/hr)"
        
        lines = ["Resource Rates:"]
        for role, rate in rates.items():
            lines.append(f"  {role}: ${rate:.2f}/hour")
        
        return "\n".join(lines)


# ============================================================================
# ESTIMATION UTILITIES
# ============================================================================

class EstimationTemplates:
    """Common estimation templates"""
    
    @staticmethod
    def get_software_development_template() -> Dict[str, Any]:
        """Template for software development projects"""
        return {
            "packages": [
                {"name": "Requirements & Design", "hours_range": (40, 80)},
                {"name": "Development", "hours_range": (200, 400)},
                {"name": "Testing & QA", "hours_range": (100, 200)},
                {"name": "Deployment", "hours_range": (20, 40)},
                {"name": "Documentation", "hours_range": (20, 40)},
            ]
        }
    
    @staticmethod
    def get_consulting_template() -> Dict[str, Any]:
        """Template for consulting projects"""
        return {
            "packages": [
                {"name": "Discovery & Analysis", "hours_range": (40, 80)},
                {"name": "Strategy Development", "hours_range": (80, 160)},
                {"name": "Implementation Support", "hours_range": (100, 200)},
                {"name": "Training & Knowledge Transfer", "hours_range": (40, 80)},
                {"name": "Final Report", "hours_range": (20, 40)},
            ]
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def estimate_project_effort(
    tender_id: str,
    project_scope: str,
    requirements_text: str,
    company_type: str = "engineering"
) -> EffortEstimationOutput:
    """Convenience function to estimate project effort"""
    estimator = EffortEstimator()
    return estimator.estimate_effort(
        tender_id,
        project_scope,
        requirements_text,
        company_type=company_type
    )


def estimate_work_package(
    package_id: str,
    description: str,
    requirements: List[str]
) -> Optional[EffortEstimate]:
    """Convenience function to estimate work package"""
    estimator = EffortEstimator()
    return estimator.estimate_work_package(package_id, description, requirements)
