import pytest
from sqlalchemy import select

from adhdaf.models import Capture, Task


@pytest.mark.asyncio
async def test_create_capture(db_session):
    capture = Capture(raw_text="messy thought about stuff", source="web")
    db_session.add(capture)
    await db_session.commit()

    result = await db_session.execute(select(Capture))
    row = result.scalar_one()
    assert row.raw_text == "messy thought about stuff"
    assert row.source == "web"
    assert row.status == "pending"
    assert row.id is not None


@pytest.mark.asyncio
async def test_create_task(db_session):
    task = Task(title="Call the dentist", source="capture", status="inbox")
    db_session.add(task)
    await db_session.commit()

    result = await db_session.execute(select(Task))
    row = result.scalar_one()
    assert row.title == "Call the dentist"
    assert row.status == "inbox"
    assert row.priority == "medium"
    assert row.is_focus is False
    assert row.tags == []


@pytest.mark.asyncio
async def test_task_linked_to_capture(db_session):
    capture = Capture(raw_text="need to call dentist", source="voice")
    db_session.add(capture)
    await db_session.commit()

    task = Task(title="Call the dentist", source="capture", capture_id=capture.id)
    db_session.add(task)
    await db_session.commit()

    result = await db_session.execute(select(Task))
    row = result.scalar_one()
    assert row.capture_id == capture.id
