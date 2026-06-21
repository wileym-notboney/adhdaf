# ABOUTME: Tests for bearer token authentication middleware.
# ABOUTME: Verifies both capture-tier and admin-tier token checks.
import pytest
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient

from adhdaf.auth import AdminAuth, CaptureAuth


@pytest.fixture
async def auth_client():
    app = FastAPI()
    router = APIRouter()

    @router.get("/needs-capture")
    async def needs_capture(token: str = CaptureAuth):
        return {"ok": True}

    @router.get("/needs-admin")
    async def needs_admin(token: str = AdminAuth):
        return {"ok": True}

    app.include_router(router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_no_token_returns_401(auth_client):
    resp = await auth_client.get("/needs-capture")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_token_returns_403(auth_client):
    resp = await auth_client.get("/needs-capture", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_capture_token_accepted(auth_client):
    resp = await auth_client.get(
        "/needs-capture", headers={"Authorization": "Bearer test-capture-token"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_token_works_for_capture(auth_client):
    resp = await auth_client.get(
        "/needs-capture", headers={"Authorization": "Bearer test-admin-token"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_capture_token_rejected_for_admin(auth_client):
    resp = await auth_client.get(
        "/needs-admin", headers={"Authorization": "Bearer test-capture-token"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_token_accepted_for_admin(auth_client):
    resp = await auth_client.get(
        "/needs-admin", headers={"Authorization": "Bearer test-admin-token"}
    )
    assert resp.status_code == 200
