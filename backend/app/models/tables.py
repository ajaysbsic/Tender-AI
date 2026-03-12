from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum, Text, UUID, JSON, func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base
import enum


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    company_profiles = relationship("CompanyProfile", back_populates="user")
    tenders = relationship("Tender", back_populates="user")


class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    industry = Column(String)
    annual_turnover = Column(Numeric)
    certifications = Column(JSON, default=[])  # Changed from ARRAY to JSON for SQLite compatibility
    past_experience_years = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="company_profiles")
    tenders = relationship("Tender", back_populates="company")


class TenderStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Tender(Base):
    __tablename__ = "tenders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    language_detected = Column(String, default="en")
    status = Column(Enum(TenderStatus), default=TenderStatus.UPLOADED)
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    
    user = relationship("User", back_populates="tenders")
    company = relationship("CompanyProfile", back_populates="tenders")
    sections = relationship("TenderSection", back_populates="tender", cascade="all, delete-orphan")
    evaluation = relationship("Evaluation", back_populates="tender", uselist=False, cascade="all, delete-orphan")


class TenderSection(Base):
    __tablename__ = "tender_sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False)
    section_name = Column(String, nullable=False)
    section_text = Column(Text, nullable=False)
    page_range = Column(String)
    
    tender = relationship("Tender", back_populates="sections")
    clauses = relationship("Clause", back_populates="section", cascade="all, delete-orphan")


class Clause(Base):
    __tablename__ = "clauses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("tender_sections.id"), nullable=False)
    clause_text = Column(Text, nullable=False)
    clause_order = Column(Integer)
    
    section = relationship("TenderSection", back_populates="clauses")
    evaluations = relationship("ClauseEvaluation", back_populates="clause", cascade="all, delete-orphan")


class EligibilityVerdict(str, enum.Enum):
    ELIGIBLE = "eligible"
    PARTIALLY_ELIGIBLE = "partially_eligible"
    NOT_ELIGIBLE = "not_eligible"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EffortLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, unique=True)
    eligibility_verdict = Column(Enum(EligibilityVerdict), nullable=False)
    eligibility_score = Column(Integer)
    risk_score = Column(Integer)
    risk_level = Column(Enum(RiskLevel))
    effort_score = Column(Integer)
    effort_level = Column(Enum(EffortLevel))
    ai_summary = Column(Text)
    missing_documents = Column(JSON, default=[])  # Changed from ARRAY to JSON
    risk_factors = Column(JSON, default=[])  # Changed from ARRAY to JSON
    created_at = Column(DateTime, server_default=func.now())
    
    tender = relationship("Tender", back_populates="evaluation")
    clause_evaluations = relationship("ClauseEvaluation", back_populates="evaluation", cascade="all, delete-orphan")


class ClauseStatus(str, enum.Enum):
    ELIGIBLE = "eligible"
    PARTIALLY_ELIGIBLE = "partially_eligible"
    NOT_ELIGIBLE = "not_eligible"


class ClauseEvaluation(Base):
    __tablename__ = "clause_evaluations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluations.id"), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    status = Column(Enum(ClauseStatus), nullable=False)
    reason = Column(Text)
    
    evaluation = relationship("Evaluation", back_populates="clause_evaluations")
    clause = relationship("Clause", back_populates="evaluations")


# Step-5: Chunking and Section Detection Models

class SectionTypeEnum(str, enum.Enum):
    """Tender section types"""
    ELIGIBILITY = "eligibility"
    TECHNICAL_REQUIREMENTS = "technical_requirements"
    COMMERCIAL_REQUIREMENTS = "commercial_requirements"
    DEADLINES = "deadlines"
    PENALTIES = "penalties"
    EVALUATION_CRITERIA = "evaluation_criteria"
    SCOPE = "scope"
    DELIVERABLES = "deliverables"
    OTHER = "other"


class TenderChunk(Base):
    """
    Chunked tender content with section metadata.
    For Step-5 & Step-6 processing.
    """
    __tablename__ = "tender_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)  # Position in document
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    character_count = Column(Integer, nullable=False)
    section_type = Column(Enum(SectionTypeEnum), default=SectionTypeEnum.OTHER, index=True)
    page_number = Column(Integer, nullable=False)
    section_header = Column(String)  # Header of the section this chunk belongs to
    confidence = Column(Numeric, default=0.0)  # Confidence in section classification
    created_at = Column(DateTime, server_default=func.now())
    
    tender = relationship("Tender", back_populates="chunks")
    embedding = relationship("TenderEmbedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        # Composite index for efficient querying by tender and section
        None,
    )


# Step-6: Embedding Models

class TenderEmbedding(Base):
    """
    FAISS embeddings for tender chunks.
    For semantic search and retrieval.
    """
    __tablename__ = "tender_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("tender_chunks.id"), nullable=False, unique=True, index=True)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    embedding_vector = Column(JSON, nullable=False)  # Store as JSON array (FAISS will handle binary)
    embedding_model = Column(String, nullable=False)  # e.g., "text-embedding-3-small"
    model_dimension = Column(Integer, nullable=False)  # Embedding dimension (typically 1536 or 384)
    faiss_index_id = Column(Integer)  # Index ID in FAISS (if using persisted index)
    created_at = Column(DateTime, server_default=func.now())
    
    chunk = relationship("TenderChunk", back_populates="embedding")
    tender = relationship("Tender", back_populates="embeddings")


class FAISSIndex(Base):
    """
    Metadata for FAISS indices.
    Tracks embedding pipelines per tender.
    """
    __tablename__ = "faiss_indices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, unique=True, index=True)
    index_path = Column(String, nullable=False)  # Local file path to FAISS index
    embedding_model = Column(String, nullable=False)  # Model used for embeddings
    model_dimension = Column(Integer, nullable=False)  # Embedding dimension
    total_chunks = Column(Integer, default=0)  # Number of chunks indexed
    index_type = Column(String, default="flat")  # FAISS index type: flat, ivf, hnsw, etc.
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    tender = relationship("Tender", back_populates="faiss_index")


# Update Tender model to include new relationships
Tender.chunks = relationship("TenderChunk", back_populates="tender", cascade="all, delete-orphan")
Tender.embeddings = relationship("TenderEmbedding", back_populates="tender", cascade="all, delete-orphan")
Tender.faiss_index = relationship("FAISSIndex", back_populates="tender", uselist=False, cascade="all, delete-orphan")
