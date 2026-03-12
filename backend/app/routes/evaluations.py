"""
Evaluation API Routes - Step-9

Endpoints for retrieving tender evaluations and downloading reports.
Supports both individual evaluation retrieval and report generation.
"""

import logging
from typing import Optional, List
from io import BytesIO

from fastapi import APIRouter, HTTPException, Query, Response, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.models import Tender, TenderEvaluation
from app.services.scoring_models import TenderScore, EligibilityCategory, RiskCategory, EffortCategory
from app.services.report_generator import generate_tender_report

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/evaluations",
    tags=["evaluations"],
    responses={404: {"description": "Not found"}}
)


# ============================================================================
# GET EVALUATION ENDPOINTS
# ============================================================================

@router.get("/tender/{tender_id}", response_model=dict)
async def get_tender_evaluation(
    tender_id: str,
    db: Session = None
):
    """
    Retrieve evaluation results for a tender.
    
    Returns:
    - Tender metadata
    - Scoring results (eligibility, risk, effort)
    - Bid recommendation
    - Strengths and weaknesses
    - Key metrics
    """
    if db is None:
        db = next(get_db())
    
    logger.info(f"Retrieving evaluation for tender: {tender_id}")
    
    # Fetch tender
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        logger.warning(f"Tender not found: {tender_id}")
        raise HTTPException(status_code=404, detail=f"Tender {tender_id} not found")
    
    # Fetch evaluation
    evaluation = db.query(TenderEvaluation).filter(
        TenderEvaluation.tender_id == tender_id
    ).first()
    
    if not evaluation:
        logger.warning(f"Evaluation not found for tender: {tender_id}")
        raise HTTPException(status_code=404, detail=f"Evaluation for tender {tender_id} not found")
    
    # Reconstruct TenderScore from evaluation data
    tender_score = _reconstruct_tender_score(evaluation)
    
    return _format_evaluation_response(tender, tender_score)


@router.get("/tender/{tender_id}/eligibility", response_model=dict)
async def get_eligibility_evaluation(
    tender_id: str,
    db: Session = None
):
    """
    Retrieve eligibility evaluation only.
    
    Returns:
    - Eligibility category (ELIGIBLE / PARTIALLY_ELIGIBLE / NOT_ELIGIBLE)
    - Requirements met percentage
    - Individual requirement assessments
    - Reasoning for verdict
    """
    if db is None:
        db = next(get_db())
    
    logger.info(f"Retrieving eligibility evaluation for tender: {tender_id}")
    
    evaluation = db.query(TenderEvaluation).filter(
        TenderEvaluation.tender_id == tender_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation not found for {tender_id}")
    
    tender_score = _reconstruct_tender_score(evaluation)
    
    return {
        "tender_id": tender_id,
        "eligibility": {
            "category": tender_score.eligibility.category.value,
            "score_percentage": round(tender_score.eligibility.eligibility_score, 1),
            "requirements_met": sum(1 for r in tender_score.eligibility.requirements_assessments if r.company_meets),
            "total_requirements": len(tender_score.eligibility.requirements_assessments),
            "verdict": _get_eligibility_verdict(tender_score.eligibility),
            "requirements": [
                {
                    "text": r.requirement_text,
                    "met": r.company_meets,
                    "mandatory": r.is_mandatory,
                    "reasoning": r.reasoning
                }
                for r in tender_score.eligibility.requirements_assessments
            ]
        }
    }


@router.get("/tender/{tender_id}/risk", response_model=dict)
async def get_risk_evaluation(
    tender_id: str,
    db: Session = None
):
    """
    Retrieve risk evaluation only.
    
    Returns:
    - Risk category (LOW / MEDIUM / HIGH)
    - Risk score (0-100)
    - Individual risk assessments
    - Deal-breaker risks
    - Risk summary statistics
    """
    if db is None:
        db = next(get_db())
    
    logger.info(f"Retrieving risk evaluation for tender: {tender_id}")
    
    evaluation = db.query(TenderEvaluation).filter(
        TenderEvaluation.tender_id == tender_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation not found for {tender_id}")
    
    tender_score = _reconstruct_tender_score(evaluation)
    risk = tender_score.risk
    
    return {
        "tender_id": tender_id,
        "risk": {
            "category": risk.risk_category.value,
            "score": round(risk.risk_score, 1),
            "verdict": _get_risk_verdict(risk),
            "risk_summary": {
                "total_risks": risk.total_risks,
                "critical_count": risk.critical_count,
                "high_count": risk.high_count,
                "medium_count": risk.medium_count,
                "low_count": risk.low_count,
            },
            "top_risks": risk.top_risks[:5],
            "deal_breakers": risk.deal_breakers,
        }
    }


@router.get("/tender/{tender_id}/effort", response_model=dict)
async def get_effort_evaluation(
    tender_id: str,
    db: Session = None
):
    """
    Retrieve effort evaluation only.
    
    Returns:
    - Effort category (LOW / MEDIUM / HIGH)
    - Effort score (0-100)
    - Resource requirements (hours, team size, estimated cost)
    - Timeline and complexity factors
    """
    if db is None:
        db = next(get_db())
    
    logger.info(f"Retrieving effort evaluation for tender: {tender_id}")
    
    evaluation = db.query(TenderEvaluation).filter(
        TenderEvaluation.tender_id == tender_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation not found for {tender_id}")
    
    tender_score = _reconstruct_tender_score(evaluation)
    effort = tender_score.effort
    metrics = effort.metrics
    
    return {
        "tender_id": tender_id,
        "effort": {
            "category": effort.effort_category.value,
            "score": round(effort.effort_score, 1),
            "verdict": _get_effort_verdict(effort),
            "resources": {
                "total_hours": round(metrics.total_hours, 1),
                "total_days": metrics.total_days,
                "team_size": metrics.team_size,
                "estimated_cost": round(metrics.estimated_cost, 2),
                "cost_per_hour": round(metrics.cost_per_hour, 2),
            },
            "complexity_factors": effort.complexity_factors,
        }
    }


# ============================================================================
# REPORT GENERATION ENDPOINTS
# ============================================================================

@router.get("/tender/{tender_id}/report/pdf")
async def get_pdf_report(
    tender_id: str,
    company_name: Optional[str] = Query(default="Your Company"),
    db: Session = None
):
    """
    Generate and stream PDF report for tender evaluation.
    
    Supports streaming download for efficient client-side processing.
    
    Query Parameters:
    - company_name: Name to display in report (default: "Your Company")
    
    Returns:
    - PDF file stream
    """
    if db is None:
        db = next(get_db())
    
    logger.info(f"Generating PDF report for tender: {tender_id}")
    
    # Fetch evaluation
    evaluation = db.query(TenderEvaluation).filter(
        TenderEvaluation.tender_id == tender_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation not found for {tender_id}")
    
    try:
        # Reconstruct tender score
        tender_score = _reconstruct_tender_score(evaluation)
        
        # Generate PDF
        pdf_buffer = generate_tender_report(tender_score, company_name)
        
        logger.info(f"PDF report generated successfully for {tender_id}")
        
        # Return as streaming response
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=tender_{tender_id}_report.pdf"
            }
        )
    
    except Exception as e:
        logger.error(f"Error generating PDF report for {tender_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")


@router.get("/tender/{tender_id}/report/summary")
async def get_report_summary(
    tender_id: str,
    db: Session = None
):
    """
    Get text summary of evaluation in business-friendly language.
    
    Returns:
    - Executive summary
    - Bid recommendation with reasoning
    - Key strengths and weaknesses
    - Critical action items
    """
    if db is None:
        db = next(get_db())
    
    logger.info(f"Retrieving report summary for tender: {tender_id}")
    
    evaluation = db.query(TenderEvaluation).filter(
        TenderEvaluation.tender_id == tender_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail=f"Evaluation not found for {tender_id}")
    
    tender_score = _reconstruct_tender_score(evaluation)
    
    return {
        "tender_id": tender_id,
        "summary": {
            "overall_score": round(tender_score.overall_score, 1),
            "recommendation": tender_score.bid_recommendation,
            "executive_summary": _generate_executive_summary(tender_score),
            "strengths": tender_score.strengths[:5],
            "weaknesses": tender_score.weaknesses[:5],
            "critical_items": tender_score.critical_items[:5],
        }
    }


# ============================================================================
# BATCH/LIST ENDPOINTS
# ============================================================================

@router.get("/list")
async def list_evaluations(
    status: Optional[str] = Query(default=None, description="Filter by bid recommendation"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = None
):
    """
    List all tender evaluations with optional filtering.
    
    Query Parameters:
    - status: Filter by recommendation (BID, NO_BID, CONDITIONAL)
    - limit: Number of results to return (1-500)
    - offset: Pagination offset
    
    Returns:
    - List of tender evaluations with summary data
    """
    if db is None:
        db = next(get_db())
    
    logger.info(f"Listing evaluations with filters: status={status}, limit={limit}, offset={offset}")
    
    query = db.query(TenderEvaluation)
    
    # Filter by status if provided
    if status:
        valid_statuses = ["BID", "NO_BID", "CONDITIONAL"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        query = query.filter(TenderEvaluation.bid_recommendation == status)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    evaluations = query.offset(offset).limit(limit).all()
    
    # Format results
    results = []
    for evaluation in evaluations:
        tender_score = _reconstruct_tender_score(evaluation)
        results.append({
            "tender_id": evaluation.tender_id,
            "overall_score": round(tender_score.overall_score, 1),
            "recommendation": tender_score.bid_recommendation,
            "eligibility_score": round(tender_score.eligibility.eligibility_score, 1),
            "risk_score": round(tender_score.risk.risk_score, 1),
            "effort_score": round(tender_score.effort.effort_score, 1),
            "evaluated_at": evaluation.evaluated_at,
        })
    
    return {
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "results": results
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _reconstruct_tender_score(evaluation: TenderEvaluation) -> TenderScore:
    """Reconstruct TenderScore from database evaluation"""
    
    # This would reconstruct from stored JSON data
    # Implementation depends on how evaluation is stored in database
    # For now, assume evaluation has a to_tender_score() method or similar
    
    if hasattr(evaluation, 'to_tender_score'):
        return evaluation.to_tender_score()
    
    # Fallback: construct from available data
    # This is a simplified version - would need full implementation
    logger.warning("Using fallback score reconstruction")
    
    # Return placeholder - in real implementation, deserialize from JSON storage
    raise NotImplementedError("Score reconstruction not yet implemented for database model")


def _format_evaluation_response(tender: Tender, tender_score: TenderScore) -> dict:
    """Format evaluation response"""
    
    return {
        "tender_id": tender_score.tender_id,
        "tender_title": getattr(tender, 'title', 'Unknown'),
        "overall_score": round(tender_score.overall_score, 1),
        "bid_recommendation": tender_score.bid_recommendation,
        "scores": {
            "eligibility": {
                "score": round(tender_score.eligibility.eligibility_score, 1),
                "category": tender_score.eligibility.category.value,
            },
            "risk": {
                "score": round(tender_score.risk.risk_score, 1),
                "category": tender_score.risk.risk_category.value,
            },
            "effort": {
                "score": round(tender_score.effort.effort_score, 1),
                "category": tender_score.effort.effort_category.value,
            },
        },
        "summary": _generate_executive_summary(tender_score),
        "strengths": tender_score.strengths[:5],
        "weaknesses": tender_score.weaknesses[:5],
        "critical_items": tender_score.critical_items[:5],
    }


def _generate_executive_summary(tender_score: TenderScore) -> str:
    """Generate business-friendly executive summary"""
    
    summary_parts = []
    
    # Overall recommendation
    if tender_score.bid_recommendation == "BID":
        summary_parts.append("RECOMMEND: This is a strong opportunity to bid on.")
    elif tender_score.bid_recommendation == "CONDITIONAL":
        summary_parts.append("CONDITIONAL: This opportunity has mixed signals and requires careful review.")
    else:
        summary_parts.append("NOT RECOMMENDED: This opportunity does not align well with your profile.")
    
    # Eligibility summary
    elig_pct = tender_score.eligibility.eligibility_score
    if elig_pct >= 90:
        summary_parts.append(f"Eligibility is strong at {elig_pct:.0f}%.")
    elif elig_pct >= 70:
        summary_parts.append(f"Eligibility is acceptable at {elig_pct:.0f}%, though there are some gaps.")
    else:
        summary_parts.append(f"Eligibility is weak at {elig_pct:.0f}%; significant requirements are not met.")
    
    # Risk summary
    risk_category = tender_score.risk.risk_category.value
    if risk_category == "LOW":
        summary_parts.append("Risk profile is favorable.")
    elif risk_category == "MEDIUM":
        summary_parts.append("Risk profile is moderate and manageable with proper planning.")
    else:
        summary_parts.append(f"Risk profile is concerning with {len(tender_score.risk.deal_breakers)} deal-breaker risks.")
    
    # Effort summary
    effort_cat = tender_score.effort.effort_category.value
    hours = tender_score.effort.metrics.total_hours
    if effort_cat == "LOW":
        summary_parts.append(f"Resource requirements are modest at approximately {hours:.0f} hours.")
    elif effort_cat == "MEDIUM":
        summary_parts.append(f"Resource requirements are substantial at approximately {hours:.0f} hours.")
    else:
        summary_parts.append(f"This is a major undertaking requiring approximately {hours:.0f} hours.")
    
    return " ".join(summary_parts)


def _get_eligibility_verdict(eligibility) -> str:
    """Get eligibility verdict text"""
    
    pct = eligibility.eligibility_score
    
    if eligibility.category.value == EligibilityCategory.ELIGIBLE.value:
        return f"Excellent fit - meets {pct:.0f}% of requirements (90%+ threshold)"
    elif eligibility.category.value == EligibilityCategory.PARTIALLY_ELIGIBLE.value:
        return f"Viable with gaps - meets {pct:.0f}% of requirements (70-90% range)"
    else:
        return f"Not recommended - meets {pct:.0f}% of requirements (below 70% threshold)"


def _get_risk_verdict(risk) -> str:
    """Get risk verdict text"""
    
    score = risk.risk_score
    category = risk.risk_category.value
    
    if category == RiskCategory.LOW.value:
        return f"Low risk profile (score: {score:.0f}/100) - manageable risks"
    elif category == RiskCategory.MEDIUM.value:
        return f"Medium risk profile (score: {score:.0f}/100) - requires mitigation planning"
    else:
        deal_breakers_text = f" with {len(risk.deal_breakers)} deal-breaker risk(s)" if risk.deal_breakers else ""
        return f"High risk profile (score: {score:.0f}/100) - significant concerns{deal_breakers_text}"


def _get_effort_verdict(effort) -> str:
    """Get effort verdict text"""
    
    score = effort.effort_score
    category = effort.effort_category.value
    hours = effort.metrics.total_hours
    
    if category == EffortCategory.LOW.value:
        return f"Low effort (score: {score:.0f}/100) - approximately {hours:.0f} hours"
    elif category == EffortCategory.MEDIUM.value:
        return f"Medium effort (score: {score:.0f}/100) - approximately {hours:.0f} hours"
    else:
        return f"High effort (score: {score:.0f}/100) - approximately {hours:.0f} hours - major undertaking"
