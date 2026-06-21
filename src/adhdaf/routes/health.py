# ABOUTME: Health check endpoint for monitoring and uptime checks.
# ABOUTME: Returns app status and version — no auth required.
from fastapi import APIRouter

from adhdaf.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")
