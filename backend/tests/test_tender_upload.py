"""
Test tender upload and async processing pipeline
"""

import pytest
import os
import tempfile
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend package imports work regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.core.database import Base, get_db
from app.models.tables import User, CompanyProfile, Tender
from app.services.parser import DocumentParser
import uuid
from datetime import datetime

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tenderiq.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def cleanup_db():
    """Clean up test database"""
    yield
    if os.path.exists("./test_tenderiq.db"):
        os.remove("./test_tenderiq.db")


@pytest.fixture
def test_user_and_company(cleanup_db):
    """Create test user and company profile"""
    db = TestingSessionLocal()
    
    # Create user
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.flush()
    
    # Create company
    company = CompanyProfile(
        user_id=user.id,
        name="Test Company",
        industry="IT Services",
        certifications=["ISO 9001", "ISO 27001"],
        past_experience_years=5
    )
    db.add(company)
    db.commit()
    
    yield user, company
    db.close()


def test_tender_upload_without_company():
    """Test tender upload fails without company profile"""
    # Register user
    register_response = client.post(
        "/auth/register",
        json={"email": "nocompany@example.com", "password": "password123"}
    )
    assert register_response.status_code == 200
    
    # Login
    login_response = client.post(
        "/auth/login",
        json={"email": "nocompany@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Try upload without company
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"PDF content")
        tmp.flush()
        
        with open(tmp.name, "rb") as f:
            response = client.post(
                "/tender/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {token}"}
            )
    
    os.unlink(tmp.name)
    assert response.status_code == 400
    assert "company profile" in response.json()["detail"].lower()


def test_tender_upload_with_company():
    """Test successful tender upload with company profile"""
    # Register and create company
    client.post(
        "/auth/register",
        json={"email": "withcompany@example.com", "password": "password123"}
    )
    
    login_response = client.post(
        "/auth/login",
        json={"email": "withcompany@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Create company profile
    client.post(
        "/company/profile",
        json={
            "name": "Test Company",
            "industry": "IT",
            "certifications": ["ISO 9001"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Upload tender
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4\n%test pdf content")
        tmp.flush()
        
        with open(tmp.name, "rb") as f:
            response = client.post(
                "/tender/upload",
                files={"file": ("test_tender.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {token}"}
            )
    
    os.unlink(tmp.name)
    
    assert response.status_code == 200
    data = response.json()
    assert "tender_id" in data
    assert data["status"] == "uploaded"
    assert "Processing started" in data["message"]


def test_tender_status_polling():
    """Test tender status polling"""
    # Setup
    client.post(
        "/auth/register",
        json={"email": "status@example.com", "password": "password123"}
    )
    
    login_response = client.post(
        "/auth/login",
        json={"email": "status@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    client.post(
        "/company/profile",
        json={"name": "Status Test Co", "industry": "IT"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Upload
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.4\n%status test")
        tmp.flush()
        
        with open(tmp.name, "rb") as f:
            upload_response = client.post(
                "/tender/upload",
                files={"file": ("status_test.pdf", f, "application/pdf")},
                headers={"Authorization": f"Bearer {token}"}
            )
    
    os.unlink(tmp.name)
    tender_id = upload_response.json()["tender_id"]
    
    # Poll status
    status_response = client.get(
        f"/tender/{tender_id}/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["tender_id"] == tender_id
    assert data["status"] in ["uploaded", "processing", "completed", "failed"]
    assert data["filename"] == "status_test.pdf"


def test_tender_upload_unsupported_format():
    """Test tender upload with unsupported file format"""
    # Setup
    client.post(
        "/auth/register",
        json={"email": "format@example.com", "password": "password123"}
    )
    
    login_response = client.post(
        "/auth/login",
        json={"email": "format@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    client.post(
        "/company/profile",
        json={"name": "Format Test Co", "industry": "IT"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Try unsupported format
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"text file")
        tmp.flush()
        
        with open(tmp.name, "rb") as f:
            response = client.post(
                "/tender/upload",
                files={"file": ("test.txt", f, "text/plain")},
                headers={"Authorization": f"Bearer {token}"}
            )
    
    os.unlink(tmp.name)
    assert response.status_code == 400
    assert "Only PDF and DOCX" in response.json()["detail"]


def test_tender_not_found():
    """Test accessing non-existent tender"""
    # Setup
    client.post(
        "/auth/register",
        json={"email": "notfound@example.com", "password": "password123"}
    )
    
    login_response = client.post(
        "/auth/login",
        json={"email": "notfound@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    # Access non-existent tender
    fake_id = str(uuid.uuid4())
    response = client.get(
        f"/tender/{fake_id}/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
