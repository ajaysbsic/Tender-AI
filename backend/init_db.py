"""
Initialize database - Create all tables without Alembic
Run this once to set up the database
"""
from app.core.database import Base, engine
from app.models.tables import (
    User, CompanyProfile, Tender, TenderSection, 
    Clause, Evaluation, ClauseEvaluation
)

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")
