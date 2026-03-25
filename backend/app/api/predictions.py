"""Prediction API endpoints."""

from typing import Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.models.predictor import predict_matchup

router = APIRouter()


class MatchupRequest(BaseModel):
    team_a: str
    team_b: str
    season: int = 2025
    mode: str = "safe"  # "safe" or "spicy"


class StatBreakdown(BaseModel):
    stat: str
    stat_key: str
    impact: float
    direction: float
    team_a_value: Any = None
    team_b_value: Any = None
    delta: float
    favors: str


class PredictionResponse(BaseModel):
    winner: str
    loser: str
    confidence: float
    team_a: str
    team_b: str
    win_probability_a: float
    win_probability_b: float
    mode: str
    stat_breakdown: List[StatBreakdown]


@router.post("/matchup", response_model=PredictionResponse)
async def api_predict_matchup(req: MatchupRequest):
    """Predict the winner of a head-to-head matchup."""
    if req.mode not in ("safe", "spicy"):
        raise HTTPException(status_code=400, detail="Mode must be 'safe' or 'spicy'")
    try:
        result = predict_matchup(req.team_a, req.team_b, req.season, mode=req.mode)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
