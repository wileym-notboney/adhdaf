# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- SQLite pragmas: WAL mode, busy_timeout (5s), foreign_keys enforcement
- `create_app_engine()` factory for reusable engine setup with pragmas
- `ensure_db_directory()` creates data dir from DATABASE_URL on startup
- `run_migrations()` now accepts optional engine arg for testability
- Tests for SQLite pragmas, migration runner, and auth middleware (16 total)
- Project docs: `docs/v0_spec.md`, `docs/implementation_slices.md`, `docs/manual_test.md`, `docs/later_backlog.md`
- HOST and PORT to `.env.example`
- ABOUTME comments on all source files
- CHANGELOG.md with backfilled history

### Changed
- CLAUDE.md rewritten as lean orientation doc pointing to `docs/`
- Migration runner cleaned up: proper `text()` imports, no more `__import__` hack
- Test conftest uses `create_app_engine()` factory and shared `db_engine` fixture
- Old monolith plan archived to `docs/archive/`

### Fixed
- Missing trailing semicolon on nudges table in `001_initial.sql`
- Config default host changed from `0.0.0.0` to `127.0.0.1` for security

## [0.1.0] - 2026-06-20

### Added
- FastAPI application skeleton with async lifespan
- SQLAlchemy async models: Capture, Task, Nudge
- SQLite database with file-based migration runner
- Bearer token auth (capture tier + admin tier)
- Pydantic request/response schemas
- `GET /health` endpoint
- CLI with database backup command (30-rotation)
- Vendor JS: htmx.min.js, sortable.min.js
- pydantic-settings config with `.env` support
- Test fixtures with in-memory SQLite
- Tests for health endpoint and model creation
- Initial SQL migration (001_initial.sql)
- Project CLAUDE.md with full design context
