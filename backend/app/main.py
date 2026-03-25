"""FastAPI application entry point."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.predictions import router as predictions_router
from app.api.teams import router as teams_router
from app.api.bracket import router as bracket_router

app = FastAPI(
    title="Jen-erate the Winner",
    version="0.2.0",
    description="NCAA tournament matchup predictions — Safe Jen & Spicy Jen",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions_router, prefix="/api/predictions", tags=["predictions"])
app.include_router(teams_router, prefix="/api/teams", tags=["teams"])
app.include_router(bracket_router, prefix="/api/bracket", tags=["bracket"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve frontend static files
# Find frontend dist — works both locally and in Docker
_FRONTEND_DIST = None
for _candidate in [
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",  # local dev
    Path(__file__).resolve().parent.parent / "frontend" / "dist",         # Docker /app
    Path("/app/frontend/dist"),                                            # Docker absolute
]:
    if _candidate.exists():
        _FRONTEND_DIST = _candidate
        break

if _FRONTEND_DIST is not None:
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React SPA for all non-API routes."""
        file_path = _FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_FRONTEND_DIST / "index.html"))
