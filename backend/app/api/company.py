from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.tables import User, CompanyProfile
from app.models.schemas import CompanyProfileCreate, CompanyProfileUpdate, CompanyProfileResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/company", tags=["company"])


@router.post("/profile", response_model=CompanyProfileResponse)
def create_company_profile(
    profile: CompanyProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create company profile for current user"""
    existing = db.query(CompanyProfile).filter(
        CompanyProfile.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company profile already exists"
        )
    
    new_profile = CompanyProfile(
        user_id=current_user.id,
        **profile.dict()
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile


@router.get("/profile", response_model=CompanyProfileResponse)
def get_company_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get company profile for current user"""
    profile = db.query(CompanyProfile).filter(
        CompanyProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    return profile


@router.put("/profile", response_model=CompanyProfileResponse)
def update_company_profile(
    profile_update: CompanyProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update company profile"""
    profile = db.query(CompanyProfile).filter(
        CompanyProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile
