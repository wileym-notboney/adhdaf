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


from adhdaf.services.capture_service import save_capture


@pytest.mark.asyncio
async def test_save_capture_creates_pending_row(db_session):
    capture = await save_capture(db_session, "buy milk", "voice")
    assert capture.id
    assert capture.raw_text == "buy milk"
    assert capture.source == "voice"
    assert capture.status == "pending"
    assert capture.created_at is not None
