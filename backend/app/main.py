"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.predictions import router as predictions_router
from backend.app.api.teams import router as teams_router
from backend.app.api.bracket import router as bracket_router

app = FastAPI(
    title="NCAA Tournament Bracket Predictor",
    version="0.1.0",
    description="Predict NCAA tournament matchup outcomes using ML",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
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
