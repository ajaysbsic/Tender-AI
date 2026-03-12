from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.orm import Session
import os
import uuid
from app.core.database import get_db
from app.core.config import get_settings
from app.models.tables import User, Tender, TenderStatus, Evaluation, CompanyProfile
from app.models.schemas import TenderUploadResponse, TenderStatusResponse, EvaluationResponse
from app.api.auth import get_current_user
from app.workers.tasks import process_tender_task

router = APIRouter(prefix="/tender", tags=["tender"])
settings = get_settings()


@router.post("/upload", response_model=TenderUploadResponse)
async def upload_tender(
    file: UploadFile = File(...),
    company_description: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Upload tender document for processing"""
    
    # Validate file type
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )
    
    # Ensure company profile exists (auto-create a basic profile for first-time users)
    company = current_user.company_profiles[0] if current_user.company_profiles else None
    if company is None:
        inferred_name = (company_description or "").strip()
        if inferred_name:
            inferred_name = inferred_name[:120]
        else:
            inferred_name = f"{current_user.email.split('@')[0]} Company"

        company = CompanyProfile(
            user_id=current_user.id,
            name=inferred_name,
            industry="General"
        )
        db.add(company)
        db.commit()
        db.refresh(company)
    
    # Create upload directory if not exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create tender record
    tender = Tender(
        user_id=current_user.id,
        company_id=company.id,
        original_filename=file.filename,
        file_path=file_path,
        status=TenderStatus.UPLOADED
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)
    
    # Queue async processing
    if background_tasks:
        background_tasks.add_task(process_tender_task, str(tender.id))
    
    return {
        "tender_id": str(tender.id),
        "status": TenderStatus.UPLOADED.value,
        "message": "Tender uploaded successfully. Processing started."
    }


@router.get("/{tender_id}/status", response_model=TenderStatusResponse)
def get_tender_status(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tender processing status"""
    try:
        tender_uuid = uuid.UUID(tender_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tender ID"
        )

    tender = db.query(Tender).filter(
        Tender.id == tender_uuid,
        Tender.user_id == current_user.id
    ).first()
    
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found"
        )

    status_value = tender.status.value if hasattr(tender.status, "value") else str(tender.status)
    
    return {
        "tender_id": str(tender.id),
        "status": status_value,
        "filename": tender.original_filename,
        "uploaded_at": tender.uploaded_at,
        "processed_at": tender.processed_at
    }


@router.get("/{tender_id}/evaluation", response_model=EvaluationResponse)
def get_tender_evaluation(
    tender_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tender evaluation results"""
    try:
        tender_uuid = uuid.UUID(tender_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tender ID"
        )

    tender = db.query(Tender).filter(
        Tender.id == tender_uuid,
        Tender.user_id == current_user.id
    ).first()
    
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found"
        )
    
    tender_status_value = tender.status.value if hasattr(tender.status, "value") else str(tender.status)
    if tender_status_value != TenderStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tender processing status: {tender_status_value}"
        )
    
    evaluation = db.query(Evaluation).filter(
        Evaluation.tender_id == tender_uuid
    ).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    return evaluation
