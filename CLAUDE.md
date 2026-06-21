# CLAUDE.md — adhdaf

_Last updated: 2026-06-21_

---

## What This Is

A low-friction ADHD productivity system: **Capture → Clean → Store/See.**

1. **Capture** a messy thought via voice, phone, browser, or CLI.
2. **Clean** it automatically with Claude Haiku into a structured task.
3. **See** it on a billboard display or kanban board.

The #1 design constraint: if capture is harder than grabbing a notebook, it dies.
Favor the smallest thing that reduces friction over anything elaborate.

---

## Who panda boss Is

- Has ADHD. Hardest struggles: starting tasks, remembering/follow-through, focus.
- Beginner with code. Explain in plain terms, no jargon.
- Concise and direct answers only.

---

## Tech Stack

Python FastAPI + SQLite + Jinja2/HTMX + SortableJS. One process, zero build steps.

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + uvicorn |
| Database | SQLite (aiosqlite) via SQLAlchemy async |
| Frontend | Jinja2 templates + HTMX |
| AI cleaning | Anthropic SDK (`claude-haiku-4-5-20251001`) |
| Notifications | Apprise |
| Auth | Bearer tokens (`CAPTURE_TOKEN` / `ADMIN_TOKEN`) |
| Port | 1738 |

---

## Commands

```bash
# Dev server
uv run fastapi dev --port 1738

# Tests
uv run pytest

# Lint
uv run ruff check . && uv run ruff format --check .
```

---

## Project Status

**Slice 0 — Skeleton**: ✅ Done. FastAPI app, SQLite + migrations, auth,
health endpoint, vendored static assets, test fixtures.

**Next up**: Slice 1 — Capture (all input paths).

---

## Docs

| Doc | What's in it |
|-----|-------------|
| [docs/v0_spec.md](docs/v0_spec.md) | Full technical spec — architecture, data model, AI rules, API surface, directory layout |
| [docs/implementation_slices.md](docs/implementation_slices.md) | Ordered build plan with gates. Current progress tracked here |
| [docs/manual_test.md](docs/manual_test.md) | Per-slice manual test checklists |
| [docs/later_backlog.md](docs/later_backlog.md) | Deferred features (kanban, reminders, polish) + dead ends + legacy Notion refs |

---

## Capture Operating Spec

When given a brain dump: **clean it and file it automatically, then report
what you did** (minimal back-and-forth).

- Produce the **smallest number of clear, manageable tasks**. Don't shred one
  thought into many tiny tasks.
- **Group related steps into ONE task** with a checklist; only split genuinely
  unrelated things.
- Short, **action-first titles** (start with a verb); fix typos.
- **Pull out dates/deadlines** into a due-date field (resolve relative dates
  against today).
- **Guess priority** from language, urgency, timing (High / Medium / Low).
- Default status = **inbox**.

---

## Decisions (don't re-pitch)

- Notion dropped as backend.
- Apple Shortcuts "Ask Claude" action is a dead end (can't run tools).
- Cleaning happens on intake, not in a nightly batch.
- Browser-direct-to-cloud blocked by CORS — server required.
