"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.predictions import router as predictions_router
from app.api.teams import router as teams_router
from app.api.bracket import router as bracket_router

app = FastAPI(
    title="Jen-erate the Winner",
    version="0.2.0",
    description="NCAA tournament matchup predictions — Safe Jen & Spicy Jen",
)

# Allow all origins in production (static frontend on different domain)
allowed_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

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
