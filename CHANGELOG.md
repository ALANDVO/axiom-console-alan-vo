# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-15

### Added

- **Backend**: FastAPI application with SQLAlchemy models for `Fixture` and `AuditRun` using SQLite persistent storage.
- **Backend**: Audit engine (`AuditEngine`) orchestrating fixture loading, provider interactions, inspection execution, scoring, and report generation (JSON + Markdown).
- **Backend**: Mock provider (`MockProvider`) with deterministic output via fixed seed — runs fully offline without LLM keys.
- **Backend**: Inspection suite framework with three implemented inspections:
  - B01 — Tool Invocation Governance (Fabrication pillar, mandatory minimum)
  - B08 — Privilege Escalation Detection (Manipulation pillar, mandatory minimum)
  - P01 — Plausible-Justification Destruction Resistance (Manipulation pillar, mandatory minimum)
- **Backend**: REST APIs for fixtures (CRUD + validation) and audit runs (create, list, get, update, cancel, delete) with pagination, filtering, and background execution.
- **Backend**: Provider configuration schema supporting mock, OpenAI, Anthropic, and HTTP-compatible providers.
- **Backend**: SQLite database with UTC timestamps, audit fields, and transactional mutations.
- **Backend**: 20 pytest tests covering health checks, audit run CRUD, mock provider determinism, inspection logic, and registry.
- **Backend**: Dockerfile with non-root user, healthcheck, and security best practices.
- **Frontend**: React + TypeScript + Vite application with typed API client.
- **Frontend**: Dashboard page showing audit run list, status badges, scores, and an inline creation modal with fixture selection, provider configuration, and suite selection.
- **Frontend**: Audit run detail page with scorecard visualization, pillar scores, inspection results, report export (JSON/Markdown), and run details.
- **Frontend**: Scorecard component with grade badges, score badges, pillar score cards, and inspection result rows.
- **Frontend**: Fixtures management page with listing, creation, and deletion.
- **Frontend**: Tailwind CSS with custom design system (buttons, cards, badges, inputs).
- **Frontend**: 9 vitest tests covering Loading, Scorecard/GradeBadge, and Dashboard empty states.
- **Frontend**: Dockerfile with nginx runtime and non-root user.
- **Infrastructure**: Docker Compose with backend, frontend, and Keycloak services.
- **Infrastructure**: GitHub Actions CI workflow (backend pytest, frontend typecheck + build + test, Docker build).
- **Documentation**: README with architecture diagram, API reference, provider configuration table, security limitations, and deployment guidance.
- **Documentation**: `.env.example` with blank credentials.
- **Documentation**: MIT LICENSE.