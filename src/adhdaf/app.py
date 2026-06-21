# ABOUTME: FastAPI application entry point with lifespan hook.
# ABOUTME: Creates data directory and runs migrations on startup, mounts all routers.
from contextlib import asynccontextmanager

from fastapi import FastAPI

from adhdaf.database import ensure_db_directory, run_migrations
from adhdaf.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_db_directory()
    await run_migrations()
    yield


app = FastAPI(title="adhdaf", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
