"""
TaskFlow — FastAPI application entry point.

Start with:
    cd backend
    uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
# Custom logging middleware (Section 1 Task 7)
# Must be added BEFORE the CORS middleware so every request is timed correctly.
# ---------------------------------------------------------------------------
app.add_middleware(LoggingMiddleware)

# ---------------------------------------------------------------------------
# CORS middleware (Section 1 Task 8)
# Explicitly names the frontend origin(s); no unconditional wildcard.
# Adjust FRONTEND_ORIGINS to match whichever port you serve the frontend from.
# ---------------------------------------------------------------------------
FRONTEND_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5501",
    "http://127.0.0.1:5501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # If you open index.html directly (file://) some browsers send a null Origin;
    # add "null" here only while developing locally, remove before production.
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
# Routers
# ---------------------------------------------------------------------------
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(stats.router)
app.include_router(quick_add.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "app": "TaskFlow API", "version": "1.0.0"}
