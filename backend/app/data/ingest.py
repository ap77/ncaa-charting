"""
Main ingestion pipeline: scrape, clean, normalize, and store
historical tournament results + team stats into SQLite.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.data.database import (
    SessionLocal,
    Team,
    TeamSeasonStats,
    TournamentGame,
    init_db,
)
from backend.app.data.scraper import (
    scrape_advanced_stats,
    scrape_team_season_stats,
    scrape_tournament_results,
)
from backend.app.data.team_names import normalize_team_name

logger = logging.getLogger(__name__)

# Seasons to ingest (2008-2025, skipping 2020 — COVID cancellation)
DEFAULT_SEASONS = [y for y in range(2008, 2026) if y != 2020]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    try:
        v = float(val)
        return v if np.isfinite(v) else None
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _get_or_create_team(session: Session, name: str) -> Team:
    # Strip "NCAA" suffix from display name (Sports Ref adds this for tourney teams)
    display_name = name.rstrip()
    if display_name.endswith("NCAA"):
        display_name = display_name[:-4].rstrip()
    normalized = normalize_team_name(name)
    team = session.query(Team).filter_by(name_normalized=normalized).first()
    if team is None:
        team = Team(name=display_name, name_normalized=normalized)
        session.add(team)
        session.flush()
    return team


# ---------------------------------------------------------------------------
# Ingest team stats for a season
# ---------------------------------------------------------------------------

def ingest_team_stats(session: Session, season: int, seeds: dict = None) -> int:
    """Scrape and store team stats for one season. Returns row count."""
    basic_df = scrape_team_season_stats(season)
    adv_df = scrape_advanced_stats(season)
    if seeds is None:
        seeds = {}

    if basic_df.empty:
        logger.warning("No basic stats for %d", season)
        return 0

    # Both tables use data-stat="school_name" as the key column
    if "school_name" not in basic_df.columns:
        logger.warning("No school_name column in basic stats for %d", season)
        return 0

    basic_df["school_norm"] = basic_df["school_name"].apply(normalize_team_name)
    merged = basic_df.copy()

    if not adv_df.empty and "school_name" in adv_df.columns:
        adv_df["school_norm"] = adv_df["school_name"].apply(normalize_team_name)
        # Drop overlapping columns before merge (keep basic's version)
        overlap = set(merged.columns) & set(adv_df.columns) - {"school_norm"}
        adv_df = adv_df.drop(columns=list(overlap), errors="ignore")
        merged = merged.merge(adv_df, on="school_norm", how="left")

    count = 0
    for _, row in merged.iterrows():
        school_name = row.get("school_name", "")
        if not school_name:
            continue

        team = _get_or_create_team(session, school_name)

        existing = (
            session.query(TeamSeasonStats)
            .filter_by(team_id=team.id, season=season)
            .first()
        )
        if existing:
            continue

        # Compute per-game stats from season totals
        games = _safe_float(row.get("g")) or 1.0
        norm = team.name_normalized

        # Basic stats use data-stat keys: pts, opp_pts, fg_pct, fg3_pct, ft_pct,
        # orb, trb, ast, stl, blk, tov, srs, sos
        # Advanced stats use: pace, off_rtg, def_rtg
        pts_total = _safe_float(row.get("pts"))
        opp_pts_total = _safe_float(row.get("opp_pts"))
        orb_total = _safe_float(row.get("orb"))
        trb_total = _safe_float(row.get("trb"))
        ast_total = _safe_float(row.get("ast"))
        stl_total = _safe_float(row.get("stl"))
        blk_total = _safe_float(row.get("blk"))
        tov_total = _safe_float(row.get("tov"))

        # DRB = TRB - ORB
        drb_total = None
        if trb_total is not None and orb_total is not None:
            drb_total = trb_total - orb_total

        stat = TeamSeasonStats(
            team_id=team.id,
            season=season,
            wins=_safe_int(row.get("wins")),
            losses=_safe_int(row.get("losses")),
            points_per_game=pts_total / games if pts_total else None,
            field_goal_pct=_safe_float(row.get("fg_pct")),
            three_point_pct=_safe_float(row.get("fg3_pct")),
            free_throw_pct=_safe_float(row.get("ft_pct")),
            offensive_rebounds_per_game=orb_total / games if orb_total else None,
            assists_per_game=ast_total / games if ast_total else None,
            turnovers_per_game=tov_total / games if tov_total else None,
            opp_points_per_game=opp_pts_total / games if opp_pts_total else None,
            steals_per_game=stl_total / games if stl_total else None,
            blocks_per_game=blk_total / games if blk_total else None,
            defensive_rebounds_per_game=drb_total / games if drb_total else None,
            adjusted_offensive_efficiency=_safe_float(row.get("off_rtg")),
            adjusted_defensive_efficiency=_safe_float(row.get("def_rtg")),
            tempo=_safe_float(row.get("pace")),
            strength_of_schedule=_safe_float(row.get("sos")),
            simple_rating_system=_safe_float(row.get("srs")),
            seed=seeds.get(norm),
        )
        session.add(stat)
        count += 1

    session.commit()
    logger.info("Ingested %d team stats for %d", count, season)
    return count


# ---------------------------------------------------------------------------
# Ingest tournament games for a season
# ---------------------------------------------------------------------------

def ingest_tournament_games(session: Session, season: int) -> tuple[int, dict]:
    """Scrape and store tournament bracket results. Returns (game_count, seeds_dict)."""
    games = scrape_tournament_results(season)
    count = 0

    # Extract seeds from bracket data to avoid a separate request
    seeds = {}
    for g in games:
        if g.get("seed_a") and g.get("team_a"):
            seeds[normalize_team_name(g["team_a"])] = g["seed_a"]
        if g.get("seed_b") and g.get("team_b"):
            seeds[normalize_team_name(g["team_b"])] = g["seed_b"]

    for g in games:
        if not g.get("winner"):
            continue

        team_a = _get_or_create_team(session, g["team_a"])
        team_b = _get_or_create_team(session, g["team_b"])
        winner = _get_or_create_team(session, g["winner"])

        existing = (
            session.query(TournamentGame)
            .filter_by(
                season=season,
                round_number=g.get("round_number", 0),
                team_a_id=team_a.id,
                team_b_id=team_b.id,
            )
            .first()
        )
        if existing:
            continue

        game = TournamentGame(
            season=season,
            round_name=g.get("round_name", "unknown"),
            round_number=g.get("round_number", 0),
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            team_a_seed=g.get("seed_a"),
            team_b_seed=g.get("seed_b"),
            team_a_score=g.get("score_a"),
            team_b_score=g.get("score_b"),
            winner_id=winner.id,
        )
        session.add(game)
        count += 1

    session.commit()
    logger.info("Ingested %d tournament games for %d", count, season)
    return count, seeds


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_full_ingest(seasons: Optional[list[int]] = None):
    """Run the complete ingestion pipeline for all seasons."""
    if seasons is None:
        seasons = DEFAULT_SEASONS

    init_db()
    session = SessionLocal()

    total_stats = 0
    total_games = 0

    try:
        for season in seasons:
            logger.info("=== Ingesting season %d ===", season)
            # Scrape bracket first to get seeds, then pass to stats ingest
            game_count, seeds = ingest_tournament_games(session, season)
            total_games += game_count
            total_stats += ingest_team_stats(session, season, seeds=seeds)
    finally:
        session.close()

    logger.info(
        "Pipeline complete: %d team-seasons, %d tournament games",
        total_stats,
        total_games,
    )
    return {"team_seasons": total_stats, "tournament_games": total_games}
