# Tender-AI Developer Architecture Guide

## Repository Layout
- `backend/` : FastAPI application, workers, services, migrations, tests.
- `frontend/` : Angular application, pages, services, i18n assets.
- `Documentation/` : consolidated project and architecture docs.

## Backend Architecture
### Entry Points
- `backend/app/main.py`
  - Creates FastAPI app.
  - Applies CORS middleware.
  - Registers API routers (`auth`, `company`, `tender`, `evaluations`).

### Core Modules
- `backend/app/api/`
  - `auth.py`: login/register, JWT creation, bearer-token user resolution.
  - `company.py`: company profile create/read/update.
  - `tender.py`: upload, status, evaluation retrieval.
  - `evaluations.py`: evaluation list/detail endpoints used by frontend.

- `backend/app/core/`
  - `config.py`: environment-driven settings.
  - `database.py`: engine/session/base setup.
  - `celery_app.py`: async task app wiring.

- `backend/app/models/`
  - SQLAlchemy tables and Pydantic schemas.
  - UUID-backed IDs for major entities.

- `backend/app/services/`
  - Parser and sectioning pipeline in active processing path.
  - Additional AI analyzers/scorers available for deeper integration.

- `backend/app/workers/tasks.py`
  - `process_tender_task`: background processing task for uploads.

## Frontend Architecture
### App Structure
- `src/app/pages/`
  - `login`, `dashboard`, `tender`, `evaluations`, `profile`.
- `src/app/services/`
  - `auth.service.ts`: token storage/login/logout.
  - `upload.service.ts`: multipart upload + progress.
  - `status-polling.service.ts`: polling lifecycle and state normalization.
  - `api.service.ts`: typed API calls.

### Request Flow
1. `tender.component.ts` uploads via `upload.service.ts`.
2. On success, frontend starts polling `GET /tender/{id}/status`.
3. Polling service updates UI until terminal status.
4. User navigates to evaluations/dashboard views.

## Authentication and Authorization
- JWT bearer token issued by `/auth/login` and `/auth/register`.
- Angular interceptor injects `Authorization: Bearer <token>` for protected endpoints.
- Backend `get_current_user` resolves token subject to UUID user ID.

## Status Model and Polling
- Backend status values originate from `TenderStatus` enum (`uploaded`, `processing`, `completed`, `failed`).
- Frontend polling service normalizes statuses for UI behavior and handles terminal failure.

## CORS and Local Development
- CORS middleware supports localhost origins and wildcard regex for changing local ports.
- Frontend and backend can run on different ports (e.g., 4203 and 8001).

## Environment and Configuration
### Backend
- Use `backend/.env` (optional, defaults available for local runs).
- Important values: `DATABASE_URL`, `SECRET_KEY`, upload/chunk settings, broker settings.

### Frontend
- `frontend/src/environments/environment.ts` sets API base URL for local dev.
- `environment.prod.ts` for production target API URL.

## Local Run (Developer)
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

## Recommended Next Engineering Tasks
1. Wire AI analyzers/scoring into mandatory post-upload pipeline output.
2. Add robust integration tests for upload -> processing -> evaluation path.
3. Harden background task error propagation for cleaner frontend messaging.
4. Add production-grade storage and queue observability.
