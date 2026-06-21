# Plan: adhdaf — ADHD Productivity System

## Context

User has ADHD — biggest struggles: starting tasks, remembering/follow-through, focus. A previous TypeScript monorepo (Next.js + Fastify + Postgres) was too heavy and abandoned. Current habit is a paper notebook: great for capture, bad for reminders and visibility.

**Goal**: replace the notebook with something equally effortless to capture into, that also cleans messy thoughts into structured tasks, reminds you about them, and stays visible on dedicated screens.

**Critical adoption insight**: capture must work via voice ("Hey Siri") or one-tap-to-textbox. If it's harder than grabbing a notebook, it dies. Billboard displays are must-haves, not nice-to-haves.

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

**Status definitions** (explicit, for AI and UI):

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

Uses `tool_use` for guaranteed structured output. Model configured via `ANTHROPIC_MODEL` env var.

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

**Fallback**: if API fails, capture is saved in `captures` table with `status=failed`. Nothing lost. Raw text visible in "Unprocessed" view.

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

**HTMX partials** (return HTML fragments, strict separation from JSON API):
- `GET /partials/column/{status}` — re-render one kanban column
- `POST /partials/capture` — submit dump, return result fragment
- `GET /partials/billboard` — refresh billboard content

---

## Implementation Phases

### Phase 0 — Skeleton + Durability

Get `uv run` working with a solid foundation.

- `pyproject.toml` with dependencies
- `src/adhdaf/` package structure
- `config.py` — pydantic-settings, all config from `.env`:
  - `ANTHROPIC_MODEL` (default `claude-haiku-4-5-20251001`)
  - `CAPTURE_TOKEN`, `ADMIN_TOKEN`
  - `APPRISE_URLS`
  - `DATABASE_URL` (default `sqlite+aiosqlite:///data/adhdaf.db`)
- `database.py` — SQLAlchemy async engine + session
- `models.py` — Capture, Task, Nudge tables
- Simple SQL migration runner (`src/adhdaf/migrations/001_initial.sql`)
- `app.py` — FastAPI app + lifespan with DB init + migration
- `GET /health` endpoint
- Vendor `htmx.min.js` and `sortable.min.js` into `static/vendor/`
- `.env.example` with all config vars
- DB backup command: `uv run adhdaf backup` (SQLite backup API, keep 30 daily)
- Test fixtures with in-memory SQLite
- **Verify**: `uv run fastapi dev --port 1738` starts, `/health` returns OK

### Phase 1 — Capture (adoption-critical, all input paths)

Raw text goes in with minimum friction. Stores to `captures` table immediately. Attempts cleaning, falls back gracefully.

**1a. Core capture endpoint**
- `POST /api/capture` — accepts `{"raw": "messy thought", "source": "web"}`, auth via bearer token
- Saves to `captures` table immediately (before any AI call)
- Attempts cleaning synchronously, creates task(s) if successful
- If cleaning fails, capture saved with `status=failed`, visible in UI
- Returns confirmation with capture ID and any created task IDs

**1b. Capture web page**
- `capture.html` — big textarea, submit button, nothing else
- PWA manifest for home screen install (no offline queue yet — show clear failure if offline)
- Mobile-first CSS
- **Verify**: open on phone browser, type, submit, see confirmation

**1c. Apple Shortcut (voice capture)**
- Document the Shortcut: Dictate Text → Get Contents of URL → POST to `/api/capture` with bearer token → Show Result
- Plain HTTP POST, NOT the dead-end "Ask Claude" action
- **Verify**: "Hey Siri, brain dump" → dictate → task appears in DB

**1d. CLI capture**
- Shell alias: `brain "messy thought"` → curl with bearer token
- **Verify**: run from terminal, task appears in DB

**End of Phase 1 gate**: can capture from phone (voice + tap), desktop (browser + terminal). All four paths work. Raw text is never lost.

### Phase 2 — Cleaning Service (isolated, model-swappable)

Separated from capture so the AI model is easy to evaluate, tune, or replace.

**2a. Cleaner module**
- `services/cleaner.py` — takes raw text, returns structured task fields
- Uses `tool_use` for guaranteed structured output
- System prompt uses cleaning rules defined above
- Model configured via `ANTHROPIC_MODEL` env var — swap by changing one value
- Fallback: capture stays in `captures` table with `status=failed`

**2b. Cleaning integration**
- On capture: attempt cleaning immediately (best UX)
- `POST /api/tasks/{id}/clean` — manually re-trigger on a failed capture
- Background retry for captures with `status=failed` or `status=pending`
- Tests: mock Anthropic client, verify structured output, verify fallback

**2c. Evaluation**
- Capture 10-15 real messy dumps from notebook
- Run through cleaner, review output quality
- Tune system prompt and cleaning rules
- **Verify**: messy input → clean, actionable task. Model doesn't over-structure or invent details.

**End of Phase 2 gate**: messy text in → clean structured tasks out. Model choice validated. If not good enough, swap before building more.

### Phase 3 — Visibility (billboard + simple list)

Billboard is the ambient external brain. Proves value before adding full kanban.

**3a. Billboard display**
- `billboard.html` — TV-optimized, read-only, auto-refreshes every 30s via HTMX
- Large text (48px focus task), dark theme, high contrast
- Sections: Focus task, Doing, Due Today, Overdue, Waiting, Recent Captures
- Empty sections hidden, no buttons, no interactivity
- `GET /api/dashboard` aggregate endpoint

**3b. Simple task list**
- `board.html` — initially a simple grouped list (inbox / next / doing / waiting / done)
- Task cards show title, priority, area, due date
- Status change via buttons (drag-drop comes later)
- Search: `GET /api/tasks?q=` and `/search` page

**3c. Unprocessed captures view**
- Show captures with `status=failed` or `status=pending`
- Button to retry cleaning

**Verify**: open billboard on second screen, capture a task, see it appear within 30s. Search for a previously captured task by keyword.

### Phase 4 — Kanban Board (organizing)

- Upgrade `board.html` to full kanban columns with drag-drop
- SortableJS (vendored) for reordering
- Status change + reorder endpoints
- Snooze, archive actions
- Snoozed tasks: hidden from board columns, visible in search/all tasks
- Dark theme CSS
- **Verify**: drag a card between columns, refresh, see it persisted

### Phase 5 — Reminders

- Nudge detection: overdue, due soon (24h), stale (3+ days), waiting followup (2+ days)
- `remind_at` triggers separate from `due_at`
- Apprise integration via `APPRISE_URLS` env var
- Background asyncio task in lifespan (acceptable for single-user)
- Idempotency via `condition_hash` — don't resend identical nudge
- Cooldown tracking via `sent_at`
- Nudges expire via `expires_at`
- Runs every 15 minutes, gentle factual tone
- Manual "send test notification" endpoint for setup
- **Verify**: create an overdue task, receive a notification. Restart server, verify no duplicate sends.

### Phase 6 — Polish

- Keyboard shortcuts on board
- Mobile-responsive CSS refinements
- Offline capture queue in service worker (deferred — complex, not needed until app is stable)
- Shell alias packaging
- Import/export: `uv run adhdaf export > backup.json`
- Deployment guide for homelab (Proxmox LXC, systemd service)

---

## Directory Structure

```
adhdaf/
  pyproject.toml
  .env.example
  CLAUDE.md
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

## Verification Plan

After each phase:
1. `uv run pytest` — all tests pass
2. `uv run ruff check . && uv run ruff format --check .` — clean
3. Start server: `uv run fastapi dev --port 1738`
4. Manual test the feature end-to-end in browser/phone
5. Verify DB backup runs: `uv run adhdaf backup`

---

## What to Reuse

**From old TypeScript project (design reference only)**: status/priority enums, nudge detection rules + thresholds, dashboard query structure, billboard layout concept, position-based ordering, single-focus pattern.

**From network-sentry (code patterns)**: pydantic-settings config, SQLAlchemy async setup, Apprise integration.

**From CLAUDE.md §5**: capture operating spec (task structuring rules for the cleaner system prompt).

**Don't copy**: TypeScript code, monorepo structure, React components, Postgres setup.
