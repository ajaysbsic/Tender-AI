# ⚠️ IMPORTANT: Python Version Issue

## Problem
Python 3.14 is incompatible with SQLAlchemy due to changes in the typing module.

## Solution: Use Python 3.11 or 3.13

### Step 1: Install Python 3.11 (if not already)
```powershell
winget install Python.Python.3.11
```

### Step 2: Delete current venv
```powershell
Remove-Item -Recurse -Force .venv
```

### Step 3: Create new venv with Python 3.11
```powershell
py -3.11 -m venv .venv
```

### Step 4: Activate venv
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 5: Install dependencies
```powershell
cd backend
pip install -r requirements.txt
```

### Step 6: Initialize database
```powershell
# Option 1: Using Python script (recommended)
python init_db.py

# Option 2: Using Alembic (if no errors)
alembic upgrade head
```

### Step 7: Start API server
```powershell
uvicorn app.main:app --reload
```

## API will be available at
- http://localhost:8000
- Docs: http://localhost:8000/docs
