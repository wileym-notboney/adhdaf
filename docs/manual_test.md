# Manual Test Plan — adhdaf

Run after each slice to verify end-to-end behavior. Automated tests catch
regressions; this catches "it works but feels wrong."

---

## After Every Slice

1. `uv run pytest` — all tests pass
2. `uv run ruff check . && uv run ruff format --check .` — clean
3. Start server: `uv run fastapi dev --port 1738`

---

## Slice 0 — Skeleton ✅

- [x] Server starts without errors
- [x] `GET /health` returns `{"status": "ok", "version": "0.1.0"}`
- [x] SQLite DB file created in `data/`
- [x] Migration `001_initial.sql` applied (captures, tasks, nudges tables exist)
- [x] `schema_migrations` table tracks applied migrations
- [x] Re-running migrations is idempotent (no duplicate entries)
- [x] SQLite WAL mode enabled (verified via `PRAGMA journal_mode`)
- [x] SQLite `busy_timeout` set to 5000ms
- [x] SQLite `foreign_keys` enabled
- [x] Auth rejects requests without valid bearer token (401)
- [x] Auth rejects requests with wrong token (403)
- [x] Capture token and admin token both work for capture-tier endpoints
- [x] Only admin token works for admin-tier endpoints
- [x] `uv run pytest` — 16 tests pass
- [x] `uv run ruff check . && uv run ruff format --check .` — clean

---

## Slice 1 — Capture

### 1a. API capture
- [ ] `POST /api/capture` with valid token → 200, capture saved
- [ ] `POST /api/capture` without token → 401
- [ ] `POST /api/capture` with empty body → 422
- [ ] Capture row exists in DB with correct `source` and `status`

### 1b. Web capture
- [ ] Open `/capture` on phone browser
- [ ] Type messy thought, submit
- [ ] See confirmation with task title
- [ ] Reload page — form is clear, ready for next dump

### 1c. Voice capture (Apple Shortcut)
- [ ] "Hey Siri, brain dump" triggers shortcut
- [ ] Dictate a messy thought
- [ ] Shortcut shows confirmation
- [ ] Task appears in DB

### 1d. CLI capture
- [ ] `brain "messy thought"` from terminal
- [ ] Task appears in DB
- [ ] Empty input is rejected gracefully

---

## Slice 2 — Cleaning

- [ ] Submit messy dump → get clean task with action-first title
- [ ] Related items grouped into one task with checklist (not shredded)
- [ ] Dates extracted correctly ("next Friday" → correct date)
- [ ] Vague input → "Clarify: ..." title, not invented details
- [ ] Kill network → capture saved with `status=failed`, not lost
- [ ] Re-trigger cleaning on failed capture → succeeds
- [ ] Model swap via env var works without code changes

---

## Slice 3 — Visibility

### 3a. Billboard
- [ ] Open `/billboard` on second monitor/TV
- [ ] Focus task displays large (48px+)
- [ ] Dark theme, high contrast, readable from across room
- [ ] Capture a new task → appears on billboard within 30s
- [ ] Empty sections are hidden (no "Overdue: nothing" clutter)
- [ ] No buttons or interactive elements on billboard

### 3b. Task list
- [ ] Open `/board` — tasks grouped by status
- [ ] Change task status via button → moves to correct group
- [ ] Search by keyword → finds previously captured task

### 3c. Unprocessed captures
- [ ] Failed captures visible in UI
- [ ] Retry button re-triggers cleaning
- [ ] Successful retry moves capture to processed

---

## Slice 4 — Kanban (post-v0)

- [ ] Drag task card between columns → status changes
- [ ] Drag to reorder within column → position persists
- [ ] Refresh page → order preserved
- [ ] Snooze task → disappears from board, visible in search
- [ ] Archive task → disappears from board

---

## Slice 5 — Reminders (post-v0)

- [ ] Create task with past due date → notification fires within 15 min
- [ ] Due-soon notification fires ~24h before deadline
- [ ] Stale task (3+ days untouched) → nudge notification
- [ ] Restart server → no duplicate notifications sent
- [ ] Dismiss nudge → same nudge doesn't reappear
- [ ] "Send test notification" endpoint works
