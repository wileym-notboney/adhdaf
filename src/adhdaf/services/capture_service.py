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
