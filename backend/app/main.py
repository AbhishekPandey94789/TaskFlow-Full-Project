"""
TaskFlow — FastAPI application entry point.

Single-process run (production / Render):
    uvicorn app.main:app --host 0.0.0.0 --port $PORT

Two-process run (local dev):
    Terminal 1: cd backend && uvicorn app.main:app --reload --port 8000
    Terminal 2: cd frontend && python -m http.server 5500
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine
from app.models import Base
from app.middleware import LoggingMiddleware
from app.routers import users, projects, tasks, stats, quick_add

# ---------------------------------------------------------------------------
# Create all tables on startup (idempotent)
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TaskFlow API",
    description="Internal task-and-project management platform for Blinkit engineering pods.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Custom logging middleware
# ---------------------------------------------------------------------------
app.add_middleware(LoggingMiddleware)

# ---------------------------------------------------------------------------
# CORS — kept for local two-process dev; same-origin requests from the
# static mount below don't need CORS at all.
# ---------------------------------------------------------------------------
FRONTEND_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5501",
    "http://127.0.0.1:5501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# ---------------------------------------------------------------------------
# API Routers (must be registered BEFORE the static-file catch-all)
# ---------------------------------------------------------------------------
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(stats.router)
app.include_router(quick_add.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "app": "TaskFlow API", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Serve the frontend as static files (single-process / production mode)
# The frontend/ directory sits one level above backend/, so we resolve
# the path relative to this file regardless of the working directory.
# ---------------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.is_dir():
    # Serve assets (styles.css, script.js, etc.)
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    # Serve index.html at the root URL "/"
    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    # Catch-all: return index.html for any unmatched path so deep-links work
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        requested = FRONTEND_DIR / full_path
        if requested.is_file():
            return FileResponse(str(requested))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
