# Slice 1 — Capture (Design)

_Date: 2026-06-21_
_Status: Approved, ready for implementation planning_

---

## Goal

Get raw text into the system with minimum friction, from four input paths:
web browser, voice (Apple Shortcut), CLI, and direct API. Every capture is
saved to the `captures` table immediately with `status='pending'`. No cleaning,
no task creation — that is Slice 2's job. **Raw text is never lost.**

---

## Scope

### In scope
- `POST /api/capture` — JSON endpoint, bearer-token auth, saves raw capture.
- `GET /capture` — HTML brain-dump page (big textarea, submit button).
- `POST /partials/capture` — HTMX form target, returns a result fragment.
- `static/manifest.json` — PWA manifest for "Add to Home Screen."
- Apple Shortcut setup documentation (voice capture).
- `brain` shell-alias snippet (CLI capture).

### Out of scope (deferred)
- AI cleaning and task creation → Slice 2.
- Service worker / offline queue / PWA icons → later.
- Cookie/session login → not needed; token-in-page is sufficient for LAN.

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Cleaning in Slice 1 | None — save raw only | Clean separation; Slice 2 owns the cleaner |
| `source` validation | Validate against `web`/`voice`/`cli`/`api` | Keep data clean from day one |
| PWA scope | Page + `manifest.json` only | Add-to-home-screen without service-worker complexity |
| Architecture | Thin route + service layer | Matches spec layout; sets up Slice 2 reuse |
| Web auth | `CAPTURE_TOKEN` embedded in page HTML | LAN security without complexity; matches v0 spec stance |

---

## Architecture

Thin HTTP routes delegating to a small service layer:

```
routes/capture.py      → HTTP handling, auth, response shaping
services/capture_service.py → save_capture(session, raw, source) -> Capture
```

The capture endpoint saves to `captures` with `status='pending'` and returns
immediately. No AI call. Slice 2 will call the same `save_capture` (or extend
the service) before invoking the cleaner.

---

## Components

### `schemas.py` (modify `CaptureRequest`)
- `raw: str` — must be non-empty after stripping whitespace (reject blank with 422).
- `source: Literal["web", "voice", "cli", "api"]` — default `"web"`; unknown values rejected with 422.

`CaptureResponse` is unchanged: `{ capture_id, status, task_ids: [] }`.
In this slice `status` is always `"pending"` and `task_ids` is always `[]`.

### `services/capture_service.py` (new)
- `async def save_capture(session, raw: str, source: str) -> Capture`
  - Creates a `Capture` row (`status="pending"`), commits, returns it.
  - Single responsibility: persist raw input. No cleaning logic.

### `routes/capture.py` (new)
- `POST /api/capture` — `CaptureAuth`; body `CaptureRequest`; returns `CaptureResponse`.
- `GET /capture` — no auth; renders `capture.html` with `CAPTURE_TOKEN` embedded.
- `POST /partials/capture` — HTMX target; saves capture; returns `capture_result.html` fragment.

`GET /capture` lives in `capture.py` for this slice (only page here); split into
`pages.py` when more pages arrive.

### Templates (under `src/adhdaf/templates/`)
- `base.html` — minimal shell: head, viewport meta, vendored htmx `<script>`.
- `capture.html` — big textarea + submit button, mobile-first CSS. Embeds the capture token for HTMX (`hx-headers` or a JS variable).
- `partials/capture_result.html` — fragment swapped in after submit ("Captured ✓" or an error message).

### Static (under `src/adhdaf/static/`)
- `style.css` — mobile-first styles for the capture page.
- `manifest.json` — PWA manifest (name, `display=standalone`, theme color). No `icons` entry yet — icons are deferred, so the manifest simply omits them.

### App wiring (`app.py`)
- Mount the new capture router.
- Mount `StaticFiles` for `/static`.
- Configure Jinja2 templates pointing at `src/adhdaf/templates/`.

---

## Data Flow

### CLI / Shortcut / API path
```
curl → POST /api/capture
       Authorization: Bearer <CAPTURE_TOKEN>
       { "raw": "...", "source": "cli" }
   → save_capture() → 200 { capture_id, status: "pending", task_ids: [] }
```

### Web path
```
GET /capture (no auth) → render capture.html with CAPTURE_TOKEN embedded
User types + submits
   → HTMX POST /partials/capture (token sent as header)
   → save_capture()
   → return capture_result.html fragment ("Captured ✓")
   → textarea clears, ready for next dump
```

On any failure the web page keeps the typed text in the textarea (never clears
unless the save succeeded) — guarantees raw text is never lost.

---

## Error Handling

| Condition | HTTP | Web behavior |
|-----------|------|--------------|
| Empty/whitespace `raw` | 422 | Inline "Can't capture an empty thought." Text preserved. |
| Invalid `source` | 422 | Error fragment. Text preserved. |
| Missing token | 401 | "Auth failed." Text preserved. |
| Wrong token | 403 | "Auth failed." Text preserved. |
| DB write fails | 500 | "Couldn't save — try again." Text preserved. |

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
- `POST /partials/capture` returns the expected HTML fragment.

### Manual (in `docs/manual_test.md`)
- Web: open `/capture` on phone browser, type, submit, see confirmation.
- Voice: "Hey Siri, brain dump" → dictate → row appears in DB.
- CLI: `brain "messy thought"` → row appears in DB.

---

## Non-Code Deliverables

- **Apple Shortcut doc**: Dictate Text → Get Contents of URL → POST to
  `/api/capture` with bearer token → Show Result. Plain HTTP POST (NOT the
  dead-end "Ask Claude" action).
- **`brain` shell alias**: a curl one-liner posting to `/api/capture` with the
  capture token, documented for the user to add to their shell profile.

---

## Gate

Can capture from phone (voice + tap), desktop (browser + terminal). All four
paths work. Raw text is never lost.
