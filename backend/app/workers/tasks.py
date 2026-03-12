from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.core.database import Base
from app.models.tables import (
    Tender, TenderStatus, TenderSection
)
from app.services.parser import DocumentParser
from datetime import datetime
import logging
import uuid

settings = get_settings()
logger = logging.getLogger(__name__)

# Create database session factory
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@shared_task(bind=True, max_retries=3)
def process_tender_task(self, tender_id: str):
    """
    Async task to process tender document (PARSING ONLY)
    
    Current stage: Document parsing and section extraction
    TODO: Add AI extraction pipeline once AI logic is implemented
    """
    db = SessionLocal()
    
    try:
        logger.info(f"Processing tender: {tender_id}")

        try:
            tender_uuid = uuid.UUID(tender_id)
        except ValueError:
            logger.error(f"Invalid tender ID: {tender_id}")
            return
        
        # Get tender
        tender = db.query(Tender).filter(Tender.id == tender_uuid).first()
        if not tender:
            logger.error(f"Tender not found: {tender_id}")
            return
        
        # Update status to processing
        tender.status = TenderStatus.PROCESSING
        db.commit()
        
        # Step 1: Parse document
        logger.info(f"Parsing document: {tender.file_path}")
        pages = DocumentParser.parse_document(tender.file_path)
        
        # Step 2: Detect sections
        logger.info("Detecting sections")
        sections_dict = DocumentParser.split_by_sections(pages)
        
        # Save sections to database
        for section_name, section_text in sections_dict.items():
            section = TenderSection(
                tender_id=tender.id,
                section_name=section_name,
                section_text=section_text
            )
            db.add(section)
        db.commit()
        
        logger.info(f"Extracted {len(sections_dict)} sections")
        
        # TODO: Next steps (when AI logic is implemented):
        # 1. Extract clauses using AI (ai_extractor.extract_clauses)
        # 2. Evaluate eligibility (ai_extractor.evaluate_eligibility)
        # 3. Calculate scores (scoring.calculate_eligibility, calculate_risk, calculate_effort)
        # 4. Generate evaluation report
        # 5. Store evaluation results
        
        # Update tender status to completed (placeholder)
        tender.status = TenderStatus.COMPLETED
        tender.processed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Tender parsing completed: {tender_id}")
        
    except Exception as e:
        logger.error(f"Error processing tender {tender_id}: {str(e)}")
        
        # Update tender status to failed
        tender = db.query(Tender).filter(Tender.id == tender_uuid).first()
        if tender:
            tender.status = TenderStatus.FAILED
            db.commit()
        
        # Retry
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()
