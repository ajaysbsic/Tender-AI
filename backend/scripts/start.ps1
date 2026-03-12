# TenderIQ Backend Startup Script

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendRoot = Resolve-Path (Join-Path $scriptDir "..")

# Activate virtual environment
$venvPath = Join-Path $backendRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "Virtual environment not found at: $venvPath" -ForegroundColor Red
    exit 1
}

# Start FastAPI server from backend root
Write-Host "Starting TenderIQ API server..." -ForegroundColor Green
Push-Location $backendRoot
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
Pop-Location
