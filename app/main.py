"""Point d'entrée FastAPI — /health + API v1."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.api.v1.router import api_router
from app.core.audit import register_audit_hooks
from app.core.config import get_settings
from app.core.database import engine

# Doit tourner à l'import pour que les hooks soient actifs
# même quand le lifespan n'est pas déclenché (tests ASGITransport).
register_audit_hooks()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent : ne rebranche rien si déjà fait.
    register_audit_hooks()
    yield
    await engine.dispose()


settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


@app.get("/health", tags=["system"])
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    result = await session.execute(text("SELECT 1"))
    db_ok = result.scalar_one() == 1
    return {
        "status": "ok",
        "env": settings.app_env,
        "timezone": settings.app_timezone,
        "db": db_ok,
    }


app.include_router(api_router)