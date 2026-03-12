from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID


# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Company Profile Schemas
class CompanyProfileCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    annual_turnover: Optional[float] = None
    certifications: List[str] = []
    past_experience_years: Optional[int] = None


class CompanyProfileUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    annual_turnover: Optional[float] = None
    certifications: Optional[List[str]] = None
    past_experience_years: Optional[int] = None


class CompanyProfileResponse(BaseModel):
    id: UUID
    name: str
    industry: Optional[str]
    annual_turnover: Optional[float]
    certifications: List[str]
    past_experience_years: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Tender Schemas
class TenderUploadResponse(BaseModel):
    tender_id: str
    status: str
    message: str


class TenderStatusResponse(BaseModel):
    tender_id: str
    status: str
    filename: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None


# Clause Evaluation Schemas
class ClauseEvaluationResponse(BaseModel):
    clause_text: str
    status: str
    reason: Optional[str]
    
    class Config:
        from_attributes = True


# Evaluation Schemas
class EvaluationResponse(BaseModel):
    tender_id: str
    eligibility_verdict: str
    eligibility_score: int
    risk_score: int
    risk_level: str
    effort_score: int
    effort_level: str
    ai_summary: Optional[str]
    missing_documents: List[str]
    risk_factors: List[str]
    clause_evaluations: List[ClauseEvaluationResponse]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Report Generation
class ReportGenerationRequest(BaseModel):
    format: str = "pdf"  # pdf or docx
