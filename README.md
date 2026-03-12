# Tender-AI

Tender-AI is an AI-assisted tender/RFP evaluation platform that helps teams decide faster whether to bid by processing tender documents and presenting structured decision support.

## Documentation
The documentation set has been consolidated to two canonical files:

1. `Documentation/PROJECT_GUIDE.md`
- Product context, scope, current behavior, stack overview, and roadmap direction.

2. `Documentation/DEVELOPER_ARCHITECTURE_GUIDE.md`
- Developer-focused architecture, modules, request flows, auth/CORS behavior, and local run guidance.

## Quick Start (Local)
### Backend
```bash
cd backend
.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend
```bash
cd frontend
npm install
npm start -- --port 4203
```

## Current Login (local test user)
- Email: `ajay.kumar@alfanar.com`
- Password: `Ajay123#`

## Notes
- Local development ports may vary. Ensure frontend API base URL matches backend port in `frontend/src/environments/environment.ts`.
- CORS is configured for localhost development with wildcard localhost-port support in backend settings.
