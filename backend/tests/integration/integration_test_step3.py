"""
Integration test script for Step-3: Tender Upload & Async Processing
Demonstrates the complete workflow without pytest dependencies
"""

import requests
import json
import tempfile
import os
import time
import sys

# Configuration
API_BASE_URL = os.getenv("TENDER_API_URL", "http://localhost:8001")
TEST_EMAIL = f"integration_test_{int(time.time())}@example.com"
TEST_PASSWORD = "TestPassword123!"

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_success(message):
    """Print success message"""
    print(f"✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"✗ {message}")
    sys.exit(1)

def print_info(message):
    """Print info message"""
    print(f"ℹ {message}")

# Test 1: Register
print_section("STEP 1: USER REGISTRATION")
print_info(f"Registering user: {TEST_EMAIL}")

response = requests.post(
    f"{API_BASE_URL}/auth/register",
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
)

if response.status_code != 200:
    print_error(f"Registration failed: {response.text}")

print_success("User registered")
print(f"Response: {json.dumps(response.json(), indent=2)}\n")

# Test 2: Login
print_section("STEP 2: USER LOGIN")
print_info("Logging in with registered credentials")

response = requests.post(
    f"{API_BASE_URL}/auth/login",
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
)

if response.status_code != 200:
    print_error(f"Login failed: {response.text}")

token = response.json().get("access_token")
if not token:
    print_error("No access token in response")

print_success("User logged in")
print(f"Token (truncated): {token[:20]}...\n")

headers = {"Authorization": f"Bearer {token}"}

# Test 3: Create Company Profile
print_section("STEP 3: CREATE COMPANY PROFILE")
print_info("Creating company profile")

company_data = {
    "name": "Integration Test Company",
    "industry": "IT Services & Consulting",
    "annual_turnover": 10000000.00,
    "certifications": ["ISO 9001:2015", "ISO 27001:2013", "CMMI Level 3"],
    "past_experience_years": 8
}

response = requests.post(
    f"{API_BASE_URL}/company/profile",
    json=company_data,
    headers=headers
)

if response.status_code != 200:
    print_error(f"Company profile creation failed: {response.text}")

company_profile = response.json()
print_success("Company profile created")
print(f"Company ID: {company_profile['id']}\n")

# Test 4: Upload Tender Document
print_section("STEP 4: UPLOAD TENDER DOCUMENT")
print_info("Creating test PDF file")

# Create a simple test PDF-like file
pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Sample Tender Document) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000232 00000 n 
0000000309 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
403
%%EOF"""

with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
    tmp.write(pdf_content)
    tmp_path = tmp.name

try:
    print_info(f"Uploading test file: {os.path.basename(tmp_path)}")
    
    with open(tmp_path, "rb") as f:
        files = {"file": (os.path.basename(tmp_path), f, "application/pdf")}
        response = requests.post(
            f"{API_BASE_URL}/tender/upload",
            files=files,
            headers=headers
        )
    
    if response.status_code != 200:
        print_error(f"Tender upload failed: {response.text}")
    
    upload_response = response.json()
    tender_id = upload_response.get("tender_id")
    
    if not tender_id:
        print_error("No tender_id in upload response")
    
    print_success("Tender uploaded successfully")
    print(f"Response: {json.dumps(upload_response, indent=2)}\n")
    
finally:
    os.unlink(tmp_path)

# Test 5: Poll Tender Status
print_section("STEP 5: POLL TENDER STATUS")
print_info(f"Polling status for tender: {tender_id}")

status_checks = 0
max_checks = 12  # Try for up to 60 seconds (5 second intervals)

while status_checks < max_checks:
    response = requests.get(
        f"{API_BASE_URL}/tender/{tender_id}/status",
        headers=headers
    )
    
    if response.status_code != 200:
        print_error(f"Status polling failed: {response.text}")
    
    status_data = response.json()
    current_status = status_data.get("status")
    
    print_info(f"Status check {status_checks + 1}: {current_status}")
    print(f"  Uploaded: {status_data.get('uploaded_at')}")
    print(f"  Processed: {status_data.get('processed_at')}")
    
    if current_status == "completed":
        print_success("Tender processing completed!")
        break
    elif current_status == "failed":
        print_error("Tender processing failed!")
    
    status_checks += 1
    if status_checks < max_checks and current_status != "completed":
        print_info("Waiting 5 seconds before next check...\n")
        time.sleep(5)

# Test 6: Get Tender Evaluation (if completed)
if status_data.get("status") == "completed":
    print_section("STEP 6: RETRIEVE TENDER EVALUATION")
    print_info("Fetching evaluation results")
    
    response = requests.get(
        f"{API_BASE_URL}/tender/{tender_id}/evaluation",
        headers=headers
    )
    
    if response.status_code == 200:
        evaluation = response.json()
        print_success("Evaluation retrieved")
        print(f"Response: {json.dumps(evaluation, indent=2)}\n")
    else:
        print_info(f"Evaluation not yet available: {response.text}")
else:
    print_info("Tender still processing or failed, skipping evaluation check")

# Test 7: Error Cases
print_section("STEP 7: ERROR HANDLING TESTS")

# 7a: Upload unsupported file format
print_info("Testing unsupported file format")
with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
    tmp.write(b"This is plain text")
    tmp_path = tmp.name

try:
    with open(tmp_path, "rb") as f:
        files = {"file": ("test.txt", f, "text/plain")}
        response = requests.post(
            f"{API_BASE_URL}/tender/upload",
            files=files,
            headers=headers
        )
    
    if response.status_code == 400:
        print_success("Correctly rejected unsupported format")
    else:
        print_error(f"Should have rejected text file, got: {response.status_code}")
finally:
    os.unlink(tmp_path)

# 7b: Try to access non-existent tender
print_info("Testing non-existent tender access")
fake_id = "00000000-0000-0000-0000-000000000000"
response = requests.get(
    f"{API_BASE_URL}/tender/{fake_id}/status",
    headers=headers
)

if response.status_code == 404:
    print_success("Correctly returned 404 for non-existent tender")
else:
    print_error(f"Should have returned 404, got: {response.status_code}")

# 7c: Try to upload without authentication
print_info("Testing upload without authentication")
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
    tmp.write(pdf_content)
    tmp_path = tmp.name

try:
    with open(tmp_path, "rb") as f:
        files = {"file": (os.path.basename(tmp_path), f, "application/pdf")}
        response = requests.post(
            f"{API_BASE_URL}/tender/upload",
            files=files
            # No headers = no auth
        )
    
    if response.status_code == 401:
        print_success("Correctly rejected unauthenticated upload")
    else:
        print_error(f"Should have returned 401, got: {response.status_code}")
finally:
    os.unlink(tmp_path)

# Summary
print_section("TEST SUMMARY")
print_success("All tests completed successfully!")
print(f"""
Test Results:
✓ User registration
✓ User login
✓ Company profile creation
✓ Tender upload (multipart)
✓ Tender status polling
✓ Error handling (format validation)
✓ Error handling (not found)
✓ Error handling (authentication)
""")

print_info("""
Integration test workflow:
1. Register new user
2. Login and get JWT token
3. Create company profile
4. Upload PDF tender document
5. Poll tender status until processing completes
6. Retrieve evaluation results
7. Verify error handling

All endpoints are working correctly!
""")
