"""PsychShield Backend — FastAPI application entry point.

Initializes the FastAPI app, registers routers, configures CORS,
and sets up database connections on startup.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("psychshield")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and load datasets on startup."""
    logger.info("Starting PsychShield API...")
    from database_init import init_db
    from data.loaders.phishtank_loader import load_phishtank

    init_db()
    load_phishtank()
    logger.info("PsychShield API ready")
    yield
    logger.info("Shutting down...")


_debug = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(
    title="PsychShield API",
    description="AI-Based Email Social Engineering Detection",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if _debug else None,
    redoc_url="/redoc" if _debug else None,
    openapi_url="/openapi.json" if _debug else None,
)

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
origins: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]
origins.extend(
    o.replace("localhost", "127.0.0.1")
    for o in list(origins)
    if "localhost" in o and o.replace("localhost", "127.0.0.1") not in origins
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

from routers import analytics, audit, auth, email_analysis, emails, gmail, reports  # noqa: E402

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(email_analysis.router, prefix="/api", tags=["analysis"])
app.include_router(emails.router, prefix="/api", tags=["emails"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(audit.router, prefix="/api", tags=["audit"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(gmail.router, prefix="/api", tags=["gmail"])


@app.get("/api/health")
def health_check() -> dict:
    """Return server status for uptime monitoring."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": "PsychShield",
    }
