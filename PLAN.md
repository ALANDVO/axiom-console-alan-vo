# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

fixture-management

## Roadmap

### core-skeleton — FastAPI/React Skeleton with Mock Audit Run

Status: done

Acceptance:
- FastAPI backend starts and serves /health and /api/v1/audit/runs endpoints
- React frontend builds and serves dashboard with audit run creation form
- Mock provider runs a deterministic audit against a minimal fixture
- Results stored in SQLite and returned via API
- Frontend displays audit run status and scorecard
- Docker Compose brings up backend, frontend, and Keycloak
- Basic CI pipeline runs backend tests and frontend typecheck/build/test

Implementation: `backend/app/main.py`, `backend/app/models/audit_run.py`, `backend/app/models/fixture.py`, `backend/app/api/routes/health.py`, `backend/app/api/routes/audit_runs.py`, `backend/app/api/routes/fixtures.py`, `backend/app/services/audit_engine.py`, `backend/app/services/providers/mock.py`, `backend/app/services/providers/registry.py`, `backend/app/services/inspections/`, `frontend/src/App.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/AuditRunDetail.tsx`, `frontend/src/pages/Fixtures.tsx`, `frontend/src/components/AuditRunForm.tsx`, `frontend/src/components/Scorecard.tsx`, `frontend/src/components/Layout.tsx`, `frontend/Dockerfile`, `docker-compose.yaml`

Tests: `backend/tests/test_health.py`, `backend/tests/test_audit_runs.py`, `backend/tests/test_mock_provider.py`, `backend/tests/test_inspections.py`, `frontend/src/components/Loading.test.tsx`, `frontend/src/components/Scorecard.test.tsx`, `frontend/src/pages/Dashboard.test.tsx`

### fixture-management — Fixture CRUD and Validation

Status: done

Acceptance:
- Create, list, get, update, delete fixtures via API
- Validate fixture content structure against schema
- Builtin fixture seeding endpoint

Implementation: `backend/app/schemas/__init__.py`, `backend/app/api/routes/fixtures.py`, `backend/tests/test_fixtures.py`

Tests: `backend/tests/test_fixtures.py`

### llm-provider-adapters — OpenAI, Anthropic, Gemini, Ollama Provider Adapters

Status: planned

Acceptance:
- HTTP adapters using httpx with bounded timeouts
- API key from LLM_API_KEY server-side only
- Redacted error messages on provider failure

### judge-ensemble-scoring — Multi-Judge Ensemble and Pillar Grading

Status: planned

Acceptance:
- Score aggregation across pillars with configurable weights
- Mandatory minimum enforcement capping overall grade

### core-inspections — Full Essential Inspection Suite

Status: planned

Acceptance:
- B02, B03, B04, B06, B09, B12, B16, B18, B20, B27 implemented and registered

### oidc-authentication — Keycloak OIDC Login with Roles

Status: planned

Acceptance:
- Authorization code + PKCE login
- Viewer/analyst/admin role enforcement on all endpoints
- Unauthenticated rejection and role denial in tests

### reporting-export — Reporting and Export

Status: planned

Acceptance:
- Markdown, JSON, and PDF report download
- Historical comparison between runs

### policy-lab — Business Policy Composition Analysis

Status: planned

Acceptance:
- Parse and visualize policy layers
- Detect gaps and conflicts in governance configuration

