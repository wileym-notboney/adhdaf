# v0 Spec — adhdaf

The complete technical specification for the first usable version of adhdaf.
v0 = Phases 0-3 from the original plan: skeleton, capture, cleaning, and
billboard visibility. Everything needed to replace the paper notebook.

---

## Architecture: One Python Process, Zero Build Steps

**Stack**: Python FastAPI + SQLite + Jinja2/HTMX + SortableJS

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | FastAPI + uvicorn | Already known (network-sentry) |
| Database | SQLite (aiosqlite) | Zero infrastructure, one file |
| ORM | SQLAlchemy async | Already known (network-sentry) |
| Frontend | Jinja2 templates + HTMX | No npm, no build step |
| Drag-drop | SortableJS (vendored locally) | 10KB, framework-agnostic, no CDN dependency |
| AI cleaning | Anthropic SDK, configurable model (default `claude-haiku-4-5-20251001`) | ~$0.001 per brain dump |
| Notifications | Apprise | Already known (network-sentry) |
| Phone capture | Apple Shortcut → API POST + PWA | Voice via Siri, tap via home screen |
| Auth | Simple bearer token (`CAPTURE_TOKEN` / `ADMIN_TOKEN`) | LAN security without complexity |
| Port | 1738 | Thematic, memorable |

**Dev**: `uv run fastapi dev --port 1738`
**Deploy**: `uvicorn adhdaf.app:app --host 0.0.0.0 --port 1738` (or systemd service)

---

## Data Model

### captures table (raw input, never lost)

| Column | Type | Purpose |
|--------|------|---------|
| id | TEXT (UUID) | PK |
| raw_text | TEXT NOT NULL | Original messy input |
| source | TEXT NOT NULL | web / voice / cli / api |
| status | TEXT NOT NULL | pending / processed / failed |
| error | TEXT | Error message if cleaning failed |
| created_at | DATETIME NOT NULL | |
| processed_at | DATETIME | When cleaning completed |

### tasks table (cleaned, actionable)

| Column | Type | Purpose |
|--------|------|---------|
| id | TEXT (UUID) | PK |
| capture_id | TEXT FK nullable | Links back to original capture |
| title | TEXT NOT NULL | Cleaned, action-first title |
| notes | TEXT | Additional context (preserves original wording) |
| checklist | JSON | `[{text, done}]` for grouped sub-steps |
| status | TEXT NOT NULL | inbox / next / doing / waiting / done / archived |
| priority | TEXT | low / medium / high / urgent |
| area | TEXT nullable | homelab / house / errands / family / health / shopping / work |
| tags | JSON DEFAULT [] | Lightweight categorization |
| source | TEXT NOT NULL | capture / voice / api / import |
| position | INTEGER DEFAULT 0 | Ordering within column |
| is_focus | BOOLEAN DEFAULT FALSE | Single spotlight task (enforced by partial unique index) |
| due_at | DATETIME | Hard deadline |
| remind_at | DATETIME | When to resurface (softer than due) |
| snoozed_until | DATETIME | Temporarily hidden from board, visible in search/all |
| completed_at | DATETIME | Set when moved to done |
| created_at | DATETIME NOT NULL | |
| updated_at | DATETIME NOT NULL | |

**Constraints**:
- Partial unique index on `is_focus` — only one active focus task allowed:
  `CREATE UNIQUE INDEX one_focus_task ON tasks(is_focus) WHERE is_focus = 1 AND status NOT IN ('done', 'archived');`
- `doing` column limited to 1-3 tasks (enforced in app logic, surfaced in UI)

**Status definitions**:

| Status | Meaning |
|--------|---------|
| inbox | Captured but not reviewed/trusted |
| next | Reviewed and available to do |
| doing | Actively in progress (keep to 1-3 max) |
| waiting | Blocked by someone/something external |
| done | Completed recently |
| archived | Hidden historical task |

### nudges table

| Column | Type | Purpose |
|--------|------|---------|
| id | TEXT (UUID) | PK |
| task_id | TEXT FK | Links to task |
| type | TEXT NOT NULL | overdue / due_soon / stale / waiting_followup |
| message | TEXT NOT NULL | Human-readable nudge |
| status | TEXT NOT NULL | pending / sent / dismissed / expired |
| condition_hash | TEXT | Avoid resending identical nudge |
| created_at | DATETIME NOT NULL | |
| sent_at | DATETIME | When actually fired |
| dismissed_at | DATETIME | When user dismissed |
| expires_at | DATETIME | Old nudges auto-expire |

---

## AI Cleaning Rules

Uses `tool_use` for guaranteed structured output. Model configured via
`ANTHROPIC_MODEL` env var.

**Hard rules for the cleaner system prompt:**
- Never create more than 5 tasks from one dump unless user explicitly lists many items
- Preserve original wording in notes
- Infer due dates only when explicitly stated — do not invent deadlines
- Mark uncertain dates in notes, not `due_at`
- Split only when actions are truly distinct
- If input is vague, create one inbox task titled "Clarify: ..."
- Action-first titles (start with verb)
- Guess priority from language/urgency/timing — default to medium
- Default status = inbox

**Example** — input: "Need to deal with car thing and maybe call insurance Friday"
- Title: "Clarify car insurance issue"
- Notes: "Original dump mentioned 'car thing' and possibly calling insurance Friday."
- Priority: medium
- Due/remind: only set if Friday is clearly intended as a deadline
- NOT: "Call insurance about car accident claim" (invents too much)

**Fallback**: if API fails, capture is saved in `captures` table with
`status=failed`. Nothing lost. Raw text visible in "Unprocessed" view.

---

## API Endpoints

**HTML pages** (Jinja2, full page loads):
- `GET /` → redirect to `/billboard`
- `GET /capture` — Brain dump page (PWA entry point)
- `GET /billboard` — TV/monitor display (read-only, auto-refreshes)
- `GET /board` — Kanban board
- `GET /search` — Search page

**JSON API** (auth required):
- `POST /api/capture` — store raw dump → attempt clean → return result
- `GET /api/tasks` — list, filterable by status/priority/area, supports `?q=` search
- `POST /api/tasks` — create (already-clean, manual)
- `PATCH /api/tasks/{id}` — update fields
- `PATCH /api/tasks/{id}/status` — move between columns
- `POST /api/tasks/reorder` — drag-drop ordering
- `POST /api/tasks/{id}/clean` — re-trigger cleaning
- `GET /api/captures` — list raw captures (for unprocessed view)
- `GET /api/dashboard` — aggregated billboard data
- `GET /health` — no auth

**HTMX partials** (return HTML fragments):
- `GET /partials/column/{status}` — re-render one kanban column
- `POST /partials/capture` — submit dump, return result fragment
- `GET /partials/billboard` — refresh billboard content

---

## Directory Structure

```
adhdaf/
  pyproject.toml
  .env.example
  CLAUDE.md
  docs/
    v0_spec.md
    implementation_slices.md
    manual_test.md
    later_backlog.md
  src/adhdaf/
    app.py
    config.py
    database.py
    models.py
    schemas.py
    migrations/
      001_initial.sql
    routes/
      capture.py
      tasks.py
      dashboard.py
      pages.py
      health.py
    services/
      cleaner.py
      task_service.py
      nudge_service.py
      reminder_service.py
    templates/
      base.html
      board.html
      capture.html
      billboard.html
      search.html
      partials/
        task_card.html
        column.html
        capture_result.html
    static/
      style.css
      app.js
      manifest.json
      vendor/
        htmx.min.js
        sortable.min.js
  tests/
    conftest.py
    test_models.py
    test_cleaner.py
    test_task_service.py
    test_routes_capture.py
    test_routes_tasks.py
    test_routes_dashboard.py
  data/                       # .gitignored
    adhdaf.db
    backups/
```

---

## What to Reuse

**From old TypeScript project (design reference only)**: status/priority enums,
nudge detection rules + thresholds, dashboard query structure, billboard layout
concept, position-based ordering, single-focus pattern.

**From network-sentry (code patterns)**: pydantic-settings config, SQLAlchemy
async setup, Apprise integration.

**From CLAUDE.md §5**: capture operating spec (task structuring rules for the
cleaner system prompt).

**Don't copy**: TypeScript code, monorepo structure, React components, Postgres
setup.
