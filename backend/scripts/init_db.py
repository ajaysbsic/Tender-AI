"""
Initialize database - Create all tables without Alembic
Run this once to set up the database
"""
import sys
from pathlib import Path

# Ensure backend root is importable when running from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, engine
from app.models.tables import (
    User, CompanyProfile, Tender, TenderSection, 
    Clause, Evaluation, ClauseEvaluation
)

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")
