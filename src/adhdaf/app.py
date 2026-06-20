from contextlib import asynccontextmanager

from fastapi import FastAPI

from adhdaf.database import run_migrations
from adhdaf.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations()
    yield


app = FastAPI(title="adhdaf", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
