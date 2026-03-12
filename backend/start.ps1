# TenderIQ Backend Startup Script

# Activate virtual environment
$venvPath = "d:\AI Projects\Tender-AI\backend\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "Virtual environment not found at: $venvPath" -ForegroundColor Red
    exit 1
}

# Start FastAPI server
Write-Host "Starting TenderIQ API server..." -ForegroundColor Green
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
