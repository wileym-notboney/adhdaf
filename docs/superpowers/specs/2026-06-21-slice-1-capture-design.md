# Slice 1 — Capture (Design)

_Date: 2026-06-21_
_Status: Approved, ready for implementation planning_

---

## Goal

Get raw text into the system with minimum friction via a single input path:
the Apple Shortcut (voice capture from the phone). The capture is saved to the
`captures` table immediately with `status='pending'`. No cleaning, no task
creation — that is Slice 2's job. **Raw text is never lost.**

---

## Scope

### In scope
- `POST /api/capture` — JSON endpoint, bearer-token auth, saves raw capture.
- Apple Shortcut setup documentation (voice capture).

### Out of scope (deferred)
- AI cleaning and task creation → Slice 2.
- Web capture page, HTMX partial, templates, `style.css` → later slice.
- PWA manifest / icons / service worker → later.
- CLI `brain` alias → later (can be added trivially once the endpoint exists).

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Input paths | Apple Shortcut only | Lowest-friction path (voice from phone); other paths deferred |
| Cleaning in Slice 1 | None — save raw only | Clean separation; Slice 2 owns the cleaner |
| `source` validation | Validate against `web`/`voice`/`cli`/`api` | Keep data clean from day one; Shortcut sends `voice` |
| Architecture | Thin route + service layer | Matches spec layout; sets up Slice 2 reuse |

---

## Architecture

Thin HTTP route delegating to a small service layer:

```
routes/capture.py           → HTTP handling, auth, response shaping
services/capture_service.py → save_capture(session, raw, source) -> Capture
```

The capture endpoint saves to `captures` with `status='pending'` and returns
immediately. No AI call. Slice 2 will call the same `save_capture` (or extend
the service) before invoking the cleaner.

---

## Components

### `schemas.py` (modify `CaptureRequest`)
- `raw: str` — must be non-empty after stripping whitespace (reject blank with 422).
- `source: Literal["web", "voice", "cli", "api"]` — default `"voice"`; unknown values rejected with 422.

`CaptureResponse` is unchanged: `{ capture_id, status, task_ids: [] }`.
In this slice `status` is always `"pending"` and `task_ids` is always `[]`.

### `services/capture_service.py` (new)
- `async def save_capture(session, raw: str, source: str) -> Capture`
  - Creates a `Capture` row (`status="pending"`), commits, returns it.
  - Single responsibility: persist raw input. No cleaning logic.

### `routes/capture.py` (new)
- `POST /api/capture` — `CaptureAuth`; body `CaptureRequest`; returns `CaptureResponse`.

### App wiring (`app.py`)
- Mount the new capture router.

---

## Data Flow

### Shortcut path
```
Apple Shortcut → POST /api/capture
       Authorization: Bearer <CAPTURE_TOKEN>
       { "raw": "...", "source": "voice" }
   → save_capture() → 200 { capture_id, status: "pending", task_ids: [] }
   → Shortcut shows the confirmation result
```

The raw text is persisted before any other processing, so it is never lost.

---

## Error Handling

| Condition | HTTP | Shortcut behavior |
|-----------|------|-------------------|
| Empty/whitespace `raw` | 422 | Shortcut surfaces the error; nothing saved. |
| Invalid `source` | 422 | Shortcut surfaces the error. |
| Missing token | 401 | Shortcut surfaces "unauthorized." |
| Wrong token | 403 | Shortcut surfaces "forbidden." |
| DB write fails | 500 | Shortcut surfaces "server error." |

---

## Testing

### `tests/test_capture_service.py`
- `save_capture` creates a row with `status="pending"`, correct `raw_text` and `source`.

### `tests/test_routes_capture.py`
- Valid capture → 200, row persisted, response shape correct.
- Empty `raw` → 422.
- Invalid `source` → 422.
- Missing token → 401.
- Wrong token → 403.

### Manual (in `docs/manual_test.md`)
- Voice: "Hey Siri, brain dump" → dictate → row appears in DB with `source="voice"`.

---

## Non-Code Deliverables

- **Apple Shortcut doc**: Dictate Text → Get Contents of URL → POST to
  `/api/capture` with bearer token → Show Result. Plain HTTP POST (NOT the
  dead-end "Ask Claude" action).

---

## Gate

Can capture from the phone by voice via the Apple Shortcut. The raw text lands
in the `captures` table with `status='pending'` and is never lost.
