"""Team lookup endpoints."""

from fastapi import APIRouter
from sqlalchemy import func

from app.data.database import SessionLocal, Team, TeamSeasonStats

router = APIRouter()


@router.get("")
async def list_teams(season: int = 2025, q: str = ""):
    """List teams, optionally filtered by name query and season."""
    session = SessionLocal()
    try:
        query = session.query(Team).join(TeamSeasonStats)
        if season:
            query = query.filter(TeamSeasonStats.season == season)
        if q:
            query = query.filter(Team.name.ilike(f"%{q}%"))
        teams = query.order_by(Team.name).limit(50).all()
        return [{"id": t.id, "name": t.name} for t in teams]
    finally:
        session.close()


@router.get("/{team_id}/stats")
async def team_stats(team_id: int, season: int = 2025):
    """Get a team's season stats."""
    session = SessionLocal()
    try:
        stats = (
            session.query(TeamSeasonStats)
            .filter_by(team_id=team_id, season=season)
            .first()
        )
        if not stats:
            return {"error": "Stats not found"}
        return {
            col: getattr(stats, col)
            for col in TeamSeasonStats.__table__.columns.keys()
            if col not in ("id", "team_id")
        }
    finally:
        session.close()
