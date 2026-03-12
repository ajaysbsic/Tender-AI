from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.tables import Evaluation, Tender, EligibilityVerdict, RiskLevel, EffortLevel, User

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def _compute_bid_recommendation(eval_obj: Evaluation) -> str:
    if eval_obj.eligibility_verdict == EligibilityVerdict.NOT_ELIGIBLE:
        return "NOT_RECOMMENDED"
    if eval_obj.risk_level == RiskLevel.HIGH or eval_obj.effort_level == EffortLevel.HIGH:
        return "CONSIDER_WITH_CAUTION"
    return "RECOMMENDED"


def _format_eval(eval_obj: Evaluation) -> dict:
    eligibility_score = eval_obj.eligibility_score or 0
    risk_score = eval_obj.risk_score or 0
    effort_score = eval_obj.effort_score or 0
    overall_score = float((eligibility_score + risk_score + effort_score) / 3)

    return {
        "tender_id": str(eval_obj.tender_id),
        "overall_score": overall_score,
        "bid_recommendation": _compute_bid_recommendation(eval_obj),
        "scores": {
            "eligibility": {"score": eligibility_score, "category": eval_obj.eligibility_verdict.value},
            "risk": {"score": risk_score, "category": (eval_obj.risk_level.value if eval_obj.risk_level else "")},
            "effort": {"score": effort_score, "category": (eval_obj.effort_level.value if eval_obj.effort_level else "")},
        },
        "strengths": [],
        "weaknesses": [],
        "critical_items": [],
    }


@router.get("/list")
def list_evaluations(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Evaluation).join(Tender, Evaluation.tender_id == Tender.id)
    query = query.filter(Tender.user_id == current_user.id)
    evaluations = query.order_by(Evaluation.created_at.desc()).offset(offset).limit(limit).all()
    return {"items": [_format_eval(e) for e in evaluations], "total": len(evaluations)}


@router.get("/tender/{tender_id}")
def get_evaluation(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tender = db.query(Tender).filter(Tender.id == tender_id, Tender.user_id == current_user.id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    evaluation = db.query(Evaluation).filter(Evaluation.tender_id == tender_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return _format_eval(evaluation)


@router.get("/tender/{tender_id}/eligibility")
def get_eligibility_details(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evaluation = db.query(Evaluation).join(Tender, Evaluation.tender_id == Tender.id).filter(
        Evaluation.tender_id == tender_id,
        Tender.user_id == current_user.id
    ).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {
        "category": evaluation.eligibility_verdict.value,
        "score_percentage": evaluation.eligibility_score or 0,
        "requirements_met": 0,
        "total_requirements": 0,
        "requirements": []
    }


@router.get("/tender/{tender_id}/risk")
def get_risk_assessment(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evaluation = db.query(Evaluation).join(Tender, Evaluation.tender_id == Tender.id).filter(
        Evaluation.tender_id == tender_id,
        Tender.user_id == current_user.id
    ).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {
        "score": evaluation.risk_score or 0,
        "level": evaluation.risk_level.value if evaluation.risk_level else ""
    }


@router.get("/tender/{tender_id}/effort")
def get_effort_assessment(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evaluation = db.query(Evaluation).join(Tender, Evaluation.tender_id == Tender.id).filter(
        Evaluation.tender_id == tender_id,
        Tender.user_id == current_user.id
    ).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {
        "score": evaluation.effort_score or 0,
        "level": evaluation.effort_level.value if evaluation.effort_level else ""
    }


@router.get("/tender/{tender_id}/report/summary")
def get_report_summary(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evaluation = db.query(Evaluation).join(Tender, Evaluation.tender_id == Tender.id).filter(
        Evaluation.tender_id == tender_id,
        Tender.user_id == current_user.id
    ).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {"summary": evaluation.ai_summary or "Report summary not available yet."}
