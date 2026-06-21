# ABOUTME: Tests for the POST /api/capture endpoint.
# ABOUTME: Covers auth tiers, validation errors, and successful persistence.
import pytest
from sqlalchemy import select

from adhdaf.models import Capture

AUTH = {"Authorization": "Bearer test-capture-token"}


@pytest.mark.asyncio
async def test_capture_saves_and_returns_pending(client, db_session):
    resp = await client.post(
        "/api/capture", headers=AUTH, json={"raw": "buy milk", "source": "voice"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["capture_id"]
    assert data["status"] == "pending"
    assert data["task_ids"] == []

    row = (
        await db_session.execute(select(Capture).where(Capture.id == data["capture_id"]))
    ).scalar_one()
    assert row.raw_text == "buy milk"
    assert row.source == "voice"
    assert row.status == "pending"


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
