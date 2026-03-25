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
    stat_breakdown: List[StatBreakdown]


@router.post("/matchup", response_model=PredictionResponse)
async def api_predict_matchup(req: MatchupRequest):
    """Predict the winner of a head-to-head matchup."""
    try:
        result = predict_matchup(req.team_a, req.team_b, req.season)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
