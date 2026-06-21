# Implementation Slices — adhdaf

Ordered build plan. Each slice is a vertical cut that delivers testable value.
Don't start a slice until the previous one's gate passes.

---

## Slice 0 — Skeleton + Durability ✅ DONE

Get `uv run` working with a solid foundation.

- [x] `pyproject.toml` with dependencies
- [x] `src/adhdaf/` package structure
- [x] `config.py` — pydantic-settings, all config from `.env`
- [x] `database.py` — SQLAlchemy async engine + session
- [x] `models.py` — Capture, Task, Nudge tables
- [x] Simple SQL migration runner (`migrations/001_initial.sql`)
- [x] `app.py` — FastAPI app + lifespan with DB init + migration
- [x] `GET /health` endpoint
- [x] Vendor `htmx.min.js` and `sortable.min.js` into `static/vendor/`
- [x] `.env.example` with all config vars
- [x] Auth middleware (bearer token)
- [x] Test fixtures with in-memory SQLite

**Gate**: `uv run fastapi dev --port 1738` starts, `/health` returns OK. ✅

---

## Slice 1 — Capture (adoption-critical, all input paths)

Raw text goes in with minimum friction. Stores to `captures` table immediately.
Attempts cleaning, falls back gracefully.

### 1a. Core capture endpoint
- `POST /api/capture` — accepts `{"raw": "messy thought", "source": "web"}`,
  auth via bearer token
- Saves to `captures` table immediately (before any AI call)
- Attempts cleaning synchronously, creates task(s) if successful
- If cleaning fails, capture saved with `status=failed`, visible in UI
- Returns confirmation with capture ID and any created task IDs

### 1b. Capture web page
- `capture.html` — big textarea, submit button, nothing else
- PWA manifest for home screen install (no offline queue yet — show clear
  failure if offline)
- Mobile-first CSS
- **Verify**: open on phone browser, type, submit, see confirmation

### 1c. Apple Shortcut (voice capture)
- Document the Shortcut: Dictate Text → Get Contents of URL → POST to
  `/api/capture` with bearer token → Show Result
- Plain HTTP POST, NOT the dead-end "Ask Claude" action
- **Verify**: "Hey Siri, brain dump" → dictate → task appears in DB

### 1d. CLI capture
- Shell alias: `brain "messy thought"` → curl with bearer token
- **Verify**: run from terminal, task appears in DB

**Gate**: can capture from phone (voice + tap), desktop (browser + terminal).
All four paths work. Raw text is never lost.

---

## Slice 2 — Cleaning Service (isolated, model-swappable)

Separated from capture so the AI model is easy to evaluate, tune, or replace.

### 2a. Cleaner module
- `services/cleaner.py` — takes raw text, returns structured task fields
- Uses `tool_use` for guaranteed structured output
- System prompt uses cleaning rules from v0_spec.md
- Model configured via `ANTHROPIC_MODEL` env var — swap by changing one value
- Fallback: capture stays in `captures` table with `status=failed`

### 2b. Cleaning integration
- On capture: attempt cleaning immediately (best UX)
- `POST /api/tasks/{id}/clean` — manually re-trigger on a failed capture
- Background retry for captures with `status=failed` or `status=pending`
- Tests: mock Anthropic client, verify structured output, verify fallback

### 2c. Evaluation
- Capture 10-15 real messy dumps from notebook
- Run through cleaner, review output quality
- Tune system prompt and cleaning rules
- **Verify**: messy input → clean, actionable task. Model doesn't
  over-structure or invent details.

**Gate**: messy text in → clean structured tasks out. Model choice validated.
If not good enough, swap model before building more.

---

## Slice 3 — Visibility (billboard + simple list)

Billboard is the ambient external brain. Proves value before adding full kanban.

### 3a. Billboard display
- `billboard.html` — TV-optimized, read-only, auto-refreshes every 30s via HTMX
- Large text (48px focus task), dark theme, high contrast
- Sections: Focus task, Doing, Due Today, Overdue, Waiting, Recent Captures
- Empty sections hidden, no buttons, no interactivity
- `GET /api/dashboard` aggregate endpoint

### 3b. Simple task list
- `board.html` — initially a simple grouped list
  (inbox / next / doing / waiting / done)
- Task cards show title, priority, area, due date
- Status change via buttons (drag-drop comes later)
- Search: `GET /api/tasks?q=` and `/search` page

### 3c. Unprocessed captures view
- Show captures with `status=failed` or `status=pending`
- Button to retry cleaning

**Gate**: open billboard on second screen, capture a task, see it appear
within 30s. Search for a previously captured task by keyword.

---

## Config Reference

All config via `.env` (pydantic-settings):

| Var | Default | Purpose |
|-----|---------|---------|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | AI cleaning model |
| `CAPTURE_TOKEN` | (required) | Auth for capture endpoint |
| `ADMIN_TOKEN` | (required) | Auth for management endpoints |
| `APPRISE_URLS` | (empty) | Notification targets |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/adhdaf.db` | DB connection |
