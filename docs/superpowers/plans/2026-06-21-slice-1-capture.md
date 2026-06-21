# Slice 1 — Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accept a raw brain-dump via `POST /api/capture` from an Apple Shortcut and store it in the `captures` table with `status='pending'`.

**Architecture:** A thin FastAPI route (`routes/capture.py`) handles HTTP and auth, delegating persistence to a single service function (`services/capture_service.py`). No AI cleaning — that is Slice 2. The endpoint is generic JSON so other input paths can reuse it later.

**Tech Stack:** FastAPI, SQLAlchemy async, aiosqlite, Pydantic v2, pytest (asyncio auto mode), httpx AsyncClient.

## Global Constraints

- Python `>=3.12`; ruff line-length 100; lint rules `E, F, I, N, W, UP`.
- Every source/test file opens with two `# ABOUTME: ` comment lines.
- Tests run with `uv run pytest`; async tests need no explicit marker (pyproject sets `asyncio_mode = "auto"`), but match existing files which use `@pytest.mark.asyncio`.
- Auth: capture endpoints depend on `CaptureAuth` (from `adhdaf.auth`). Missing token → 401, wrong token → 403.
- DB sessions come from `get_session` (from `adhdaf.database`); tests override it via the `client` fixture in `tests/conftest.py`.
- `Capture` model fields: `id`, `raw_text`, `source`, `status` (default `"pending"`), `error`, `created_at`, `processed_at`.
- `CaptureResponse` shape is fixed: `{ capture_id: str, status: str, task_ids: list[str] }`. In this slice `status` is always `"pending"` and `task_ids` is always `[]`.

---

## File Structure

- `src/adhdaf/schemas.py` — MODIFY `CaptureRequest`: validate non-empty `raw`, constrain `source`.
- `src/adhdaf/services/capture_service.py` — CREATE `save_capture()`.
- `src/adhdaf/routes/capture.py` — CREATE `POST /api/capture` route.
- `src/adhdaf/app.py` — MODIFY to mount the capture router.
- `tests/test_capture_service.py` — CREATE service tests.
- `tests/test_routes_capture.py` — CREATE route tests.
- `docs/apple_shortcut.md` — CREATE Shortcut setup guide.
- `docs/manual_test.md` — MODIFY to add the voice-capture manual check.

---

### Task 1: Validate the capture request schema

**Files:**
- Modify: `src/adhdaf/schemas.py:8-10` (the `CaptureRequest` class)
- Test: `tests/test_capture_service.py` (new file; schema tests live here alongside the service they feed)

**Interfaces:**
- Consumes: nothing.
- Produces: `CaptureRequest(raw: str, source: Literal["web","voice","cli","api"] = "voice")`. The `raw` field is stripped of surrounding whitespace and must be non-empty; blank raw raises a validation error (HTTP 422 when used in a route).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_capture_service.py`:

```python
# ABOUTME: Tests for capture request validation and the save_capture service.
# ABOUTME: Covers schema rules (non-empty raw, allowed source) and DB persistence.
import pytest
from pydantic import ValidationError

from adhdaf.schemas import CaptureRequest


def test_capture_request_strips_and_keeps_raw():
    req = CaptureRequest(raw="  buy milk  ", source="voice")
    assert req.raw == "buy milk"
    assert req.source == "voice"


def test_capture_request_defaults_source_to_voice():
    req = CaptureRequest(raw="buy milk")
    assert req.source == "voice"


def test_capture_request_rejects_blank_raw():
    with pytest.raises(ValidationError):
        CaptureRequest(raw="   ")


def test_capture_request_rejects_unknown_source():
    with pytest.raises(ValidationError):
        CaptureRequest(raw="buy milk", source="carrier-pigeon")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_capture_service.py -v`
Expected: FAIL — blank raw and unknown source are currently accepted (no validation yet).

- [ ] **Step 3: Implement the validation**

In `src/adhdaf/schemas.py`, replace the existing `CaptureRequest` class (lines 8-10) and add the needed imports. The current top of the file is:

```python
# ABOUTME: Pydantic models for API request/response validation.
# ABOUTME: Shared between routes — keeps serialization rules in one place.
from datetime import datetime

from pydantic import BaseModel
```

Change the import line and class to:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class CaptureRequest(BaseModel):
    raw: str
    source: Literal["web", "voice", "cli", "api"] = "voice"

    @field_validator("raw")
    @classmethod
    def raw_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("raw must not be empty")
        return stripped
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_capture_service.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/adhdaf/schemas.py tests/test_capture_service.py
git commit -m "feat: validate capture request (non-empty raw, allowed source)"
```

---

### Task 2: Persist captures with save_capture

**Files:**
- Create: `src/adhdaf/services/capture_service.py`
- Test: `tests/test_capture_service.py` (append to the file from Task 1)

**Interfaces:**
- Consumes: `Capture` model (`adhdaf.models`), an `AsyncSession`.
- Produces: `async def save_capture(session: AsyncSession, raw: str, source: str) -> Capture` — inserts a `Capture` row with `status="pending"`, commits, refreshes, and returns the persisted instance (with `id` and `created_at` populated).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_capture_service.py`:

```python
from adhdaf.services.capture_service import save_capture


@pytest.mark.asyncio
async def test_save_capture_creates_pending_row(db_session):
    capture = await save_capture(db_session, "buy milk", "voice")
    assert capture.id
    assert capture.raw_text == "buy milk"
    assert capture.source == "voice"
    assert capture.status == "pending"
    assert capture.created_at is not None
```

The `db_session` fixture already exists in `tests/conftest.py` (in-memory SQLite).

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_capture_service.py::test_save_capture_creates_pending_row -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'adhdaf.services.capture_service'`

- [ ] **Step 3: Write the service**

Create `src/adhdaf/services/capture_service.py`:

```python
# ABOUTME: Capture persistence — saves raw brain-dump text to the captures table.
# ABOUTME: No cleaning here; that is Slice 2. This just guarantees raw text is stored.
from sqlalchemy.ext.asyncio import AsyncSession

from adhdaf.models import Capture


async def save_capture(session: AsyncSession, raw: str, source: str) -> Capture:
    capture = Capture(raw_text=raw, source=source, status="pending")
    session.add(capture)
    await session.commit()
    await session.refresh(capture)
    return capture
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_capture_service.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/adhdaf/services/capture_service.py tests/test_capture_service.py
git commit -m "feat: add save_capture service for raw captures"
```

---

### Task 3: Expose POST /api/capture

**Files:**
- Create: `src/adhdaf/routes/capture.py`
- Modify: `src/adhdaf/app.py` (import and include the router)
- Test: `tests/test_routes_capture.py` (new file)

**Interfaces:**
- Consumes: `CaptureRequest`/`CaptureResponse` (`adhdaf.schemas`), `save_capture` (`adhdaf.services.capture_service`), `CaptureAuth` (`adhdaf.auth`), `get_session` (`adhdaf.database`).
- Produces: `router` (FastAPI `APIRouter`) exposing `POST /api/capture` → `CaptureResponse`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_routes_capture.py`:

```python
# ABOUTME: Tests for the POST /api/capture endpoint.
# ABOUTME: Covers auth tiers, validation errors, and successful persistence.
import pytest

AUTH = {"Authorization": "Bearer test-capture-token"}


@pytest.mark.asyncio
async def test_capture_saves_and_returns_pending(client):
    resp = await client.post("/api/capture", headers=AUTH, json={"raw": "buy milk", "source": "voice"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["capture_id"]
    assert data["status"] == "pending"
    assert data["task_ids"] == []


@pytest.mark.asyncio
async def test_capture_defaults_source(client):
    resp = await client.post("/api/capture", headers=AUTH, json={"raw": "call the vet"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_capture_rejects_blank_raw(client):
    resp = await client.post("/api/capture", headers=AUTH, json={"raw": "   "})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_capture_rejects_unknown_source(client):
    resp = await client.post("/api/capture", headers=AUTH, json={"raw": "x", "source": "fax"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_capture_requires_token(client):
    resp = await client.post("/api/capture", json={"raw": "buy milk", "source": "voice"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_capture_rejects_wrong_token(client):
    resp = await client.post(
        "/api/capture",
        headers={"Authorization": "Bearer nope"},
        json={"raw": "buy milk", "source": "voice"},
    )
    assert resp.status_code == 403
```

Note: the missing-token and wrong-token tests send a *valid* body so the only thing under test is auth.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_routes_capture.py -v`
Expected: FAIL — `POST /api/capture` returns 404 (route not mounted yet).

- [ ] **Step 3: Write the route**

Create `src/adhdaf/routes/capture.py`:

```python
# ABOUTME: HTTP route for capturing raw brain-dump text via POST /api/capture.
# ABOUTME: Authenticates with the capture token, persists the raw input, returns its id.
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adhdaf.auth import CaptureAuth
from adhdaf.database import get_session
from adhdaf.schemas import CaptureRequest, CaptureResponse
from adhdaf.services.capture_service import save_capture

router = APIRouter(prefix="/api")


@router.post("/capture", response_model=CaptureResponse)
async def capture(
    body: CaptureRequest,
    session: AsyncSession = Depends(get_session),
    token: str = CaptureAuth,
):
    saved = await save_capture(session, body.raw, body.source)
    return CaptureResponse(capture_id=saved.id, status=saved.status, task_ids=[])
```

- [ ] **Step 4: Mount the router**

Modify `src/adhdaf/app.py`. The current file ends with:

```python
from adhdaf.database import ensure_db_directory, run_migrations
from adhdaf.routes.health import router as health_router
```

and later:

```python
app = FastAPI(title="adhdaf", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
```

Add the capture router import beside the health import:

```python
from adhdaf.database import ensure_db_directory, run_migrations
from adhdaf.routes.capture import router as capture_router
from adhdaf.routes.health import router as health_router
```

and add one line after the existing `include_router`:

```python
app = FastAPI(title="adhdaf", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(capture_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_routes_capture.py -v`
Expected: PASS (6 passed)

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest`
Expected: PASS (all prior tests plus the new ones, 27 total)

- [ ] **Step 7: Commit**

```bash
git add src/adhdaf/routes/capture.py src/adhdaf/app.py tests/test_routes_capture.py
git commit -m "feat: add POST /api/capture endpoint"
```

---

### Task 4: Document the Apple Shortcut + manual test

**Files:**
- Create: `docs/apple_shortcut.md`
- Modify: `docs/manual_test.md` (add a Slice 1 voice-capture section)

**Interfaces:**
- Consumes: the live `POST /api/capture` endpoint from Task 3.
- Produces: human-readable setup steps; no code.

- [ ] **Step 1: Write the Shortcut guide**

Create `docs/apple_shortcut.md`:

```markdown
# Apple Shortcut — Voice Capture

Captures a spoken thought straight into adhdaf. Uses a plain HTTP POST — NOT
the "Ask Claude" action (that one can't reach our API).

## Build the Shortcut

1. Open the **Shortcuts** app → **+** to create a new shortcut.
2. Add action **Dictate Text** (Language: your default).
3. Add action **Get Contents of URL**:
   - URL: `http://<your-server-host>:1738/api/capture`
   - Method: **POST**
   - Headers:
     - `Authorization` = `Bearer <CAPTURE_TOKEN>`
     - `Content-Type` = `application/json`
   - Request Body: **JSON**
     - `raw` = (Magic Variable) **Dictated Text**
     - `source` = `voice`
4. Add action **Show Result** with the **Contents of URL** output (shows the
   capture id so you know it saved).
5. Rename the shortcut to **Brain Dump**.

## Use it

Say **"Hey Siri, Brain Dump"**, speak your thought, and it lands in the
`captures` table with `status=pending`. Slice 2 will clean it into a task.

## Notes

- `<your-server-host>` is the LAN IP or hostname of the machine running adhdaf.
- `<CAPTURE_TOKEN>` is the value from your `.env`.
- A 401/403 means the token is missing or wrong; a 422 means the dictation was
  empty.
```

- [ ] **Step 2: Add the manual test entry**

Open `docs/manual_test.md` and add this section (keep the file's existing heading style; place it after the Slice 0 section):

```markdown
## Slice 1 — Capture (Apple Shortcut)

- [ ] Build the **Brain Dump** shortcut per `docs/apple_shortcut.md`.
- [ ] Run it: "Hey Siri, Brain Dump" → speak a thought.
- [ ] Confirm the Shortcut shows a result containing a `capture_id`.
- [ ] Query the DB and confirm a row exists in `captures` with
      `source="voice"` and `status="pending"`:
      `sqlite3 data/adhdaf.db "SELECT raw_text, source, status FROM captures ORDER BY created_at DESC LIMIT 1;"`
```

- [ ] **Step 3: Commit**

```bash
git add docs/apple_shortcut.md docs/manual_test.md
git commit -m "docs: Apple Shortcut voice-capture setup + manual test"
```

---

## Final verification

- [ ] Run the full suite: `uv run pytest` → all green.
- [ ] Lint: `uv run ruff check . && uv run ruff format --check .` → clean.
- [ ] Update `CHANGELOG.md` under `[Unreleased] → Added`: "POST /api/capture endpoint (saves raw captures with status=pending)" and "Apple Shortcut voice-capture guide". Commit with the changelog staged.
