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
