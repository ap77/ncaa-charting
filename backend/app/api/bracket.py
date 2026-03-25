"""Bracket simulation endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class BracketRequest(BaseModel):
    season: int = Field(default=2025, ge=2008, le=2030, description="Tournament season year")
    mode: str = Field(default="safe", description="'safe' or 'spicy'")


class BracketTeam(BaseModel):
    name: str
    seed: int


class GameTeamDetail(BaseModel):
    name: str
    seed: int
    win_probability: float


class MatchupResult(BaseModel):
    game_number: int
    round: str
    team_a: GameTeamDetail
    team_b: GameTeamDetail
    predicted_winner: BracketTeam
    confidence: float
    stat_breakdown: list


class RegionResult(BaseModel):
    region: str
    teams: list
    rounds: dict


class FinalFourResult(BaseModel):
    teams: list
    games: list


class ChampionshipResult(BaseModel):
    game: dict


class RoundReliability(BaseModel):
    historical_accuracy: Optional[float]
    sample_size: Optional[int]
    note: str


class BracketResponse(BaseModel):
    season: int
    regions: dict
    final_four: dict
    championship: dict
    champion: BracketTeam
    total_games: int
    model_reliability: dict


@router.post("/simulate", response_model=BracketResponse)
async def simulate_bracket(req: BracketRequest):
    """
    Simulate a full 64-team NCAA tournament bracket.

    Queries all tournament-seeded teams for the requested season, groups them
    into four regions, and simulates every round from the Round of 64 through
    the Championship game using the trained prediction model.

    Returns structured results for every matchup including win probabilities,
    confidence scores, key stat breakdowns, and per-round model reliability
    metadata.
    """
    from app.services.bracket_simulator import simulate_bracket as run_simulation

    try:
        result = run_simulation(season=req.season, mode=req.mode)
    except FileNotFoundError as exc:
        logger.error("Model not found: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Prediction model is not available. Train the model first.",
        )
    except ValueError as exc:
        logger.error("Bracket simulation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error during bracket simulation")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during bracket simulation.",
        )

    return result
