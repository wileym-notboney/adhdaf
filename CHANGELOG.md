# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- ABOUTME comments on all source files
- CHANGELOG.md with backfilled history

### Fixed
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
