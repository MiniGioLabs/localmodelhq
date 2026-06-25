"""LocalModel HQ — Find out what local AI models your machine can run."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tdir = settings.TEMPLATES_DIR or str(Path(__file__).parent / "templates")
sdir = settings.STATIC_DIR or str(Path(__file__).parent / "static")
templates = Jinja2Templates(directory=tdir)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .database import init_db
    await init_db()
    yield


app = FastAPI(title="LocalModel HQ", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=sdir), name="static")

from .routers.dashboard import router as dashboard_router
app.include_router(dashboard_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
