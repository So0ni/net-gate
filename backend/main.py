import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from api.router import api_router
from api.ws import router as ws_router
from config import settings
from core.gateway import init_gateway, teardown_gateway
from db import get_session, init_db
from services.policy_service import restore_all_policies

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    init_db()
    logger.info("Initializing gateway...")
    init_gateway()
    logger.info("Restoring device policies...")
    session: Session = next(get_session())
    restore_all_policies(session)
    yield
    # Shutdown
    logger.info("Tearing down gateway...")
    teardown_gateway()


app = FastAPI(title="Network Gate", lifespan=lifespan)

# API routes under /api
app.include_router(api_router, prefix="/api")

# WebSocket at /ws
app.include_router(ws_router)

# Serve frontend
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
