"""
Load historical NCAA data from CSV files (Kaggle March Machine Learning Mania format).

Expected files in data/raw/:
  - MNCAATourneyDetailedResults.csv  (tournament game results)
  - MTeams.csv                        (team ID → name mapping)
  - MTeamSpellings.csv                (alternate spellings)
  - MRegularSeasonDetailedResults.csv  (for computing season averages)
  - MNCAATourneySeeds.csv             (seeds)

Download from: https://www.kaggle.com/competitions/march-machine-learning-mania-2024/data
"""

import logging
import os
from pathlib import Path
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
from backend.app.data.team_names import normalize_team_name

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")

ROUND_MAP_BY_DAY = {
    # DayNum ranges approximate round assignment
    # Kaggle data uses DayNum; these are approximate boundaries
}


def _load_csv(filename: str) -> Optional[pd.DataFrame]:
    path = RAW_DIR / filename
    if not path.exists():
        logger.warning("Missing CSV: %s", path)
        return None
    return pd.read_csv(path)


def _get_or_create_team(session: Session, name: str, team_id_kaggle: int = None) -> Team:
    normalized = normalize_team_name(name)
    team = session.query(Team).filter_by(name_normalized=normalized).first()
    if team is None:
        team = Team(name=name, name_normalized=normalized)
        session.add(team)
        session.flush()
    return team


def _compute_season_averages(regular_season_df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-team per-season averages from detailed game results."""
    records = []

    for (season, team_id), games in regular_season_df.groupby(["Season", "WTeamID"]):
        n = len(games)
        records.append({
            "Season": season,
            "TeamID": team_id,
            "wins": n,
            "pts": games["WScore"].mean(),
            "fgm": games["WFGM"].mean() if "WFGM" in games else None,
            "fga": games["WFGA"].mean() if "WFGA" in games else None,
            "fgm3": games["WFGM3"].mean() if "WFGM3" in games else None,
            "fga3": games["WFGA3"].mean() if "WFGA3" in games else None,
            "ftm": games["WFTM"].mean() if "WFTM" in games else None,
            "fta": games["WFTA"].mean() if "WFTA" in games else None,
            "or": games["WOR"].mean() if "WOR" in games else None,
            "dr": games["WDR"].mean() if "WDR" in games else None,
            "ast": games["WAst"].mean() if "WAst" in games else None,
            "to": games["WTO"].mean() if "WTO" in games else None,
            "stl": games["WStl"].mean() if "WStl" in games else None,
            "blk": games["WBlk"].mean() if "WBlk" in games else None,
            "opp_pts": games["LScore"].mean(),
        })

    # Also count losses
    loss_counts = regular_season_df.groupby(["Season", "LTeamID"]).size().reset_index(name="losses")
    loss_counts.rename(columns={"LTeamID": "TeamID"}, inplace=True)

    df = pd.DataFrame(records)
    df = df.merge(loss_counts, on=["Season", "TeamID"], how="left")
    df["losses"] = df["losses"].fillna(0).astype(int)

    # Derived stats
    df["fg_pct"] = df["fgm"] / df["fga"].replace(0, np.nan)
    df["fg3_pct"] = df["fgm3"] / df["fga3"].replace(0, np.nan)
    df["ft_pct"] = df["ftm"] / df["fta"].replace(0, np.nan)

    return df


def _assign_round(day_num: int) -> tuple[str, int]:
    """Map Kaggle DayNum to round name and number."""
    if day_num <= 136:
        return ("R64", 1)
    elif day_num <= 138:
        return ("R32", 2)
    elif day_num <= 143:
        return ("S16", 3)
    elif day_num <= 145:
        return ("E8", 4)
    elif day_num <= 152:
        return ("F4", 5)
    else:
        return ("championship", 6)


def load_from_csv() -> dict:
    """Load all data from Kaggle CSV files."""
    init_db()
    session = SessionLocal()

    teams_df = _load_csv("MTeams.csv")
    tourney_df = _load_csv("MNCAATourneyDetailedResults.csv")
    regular_df = _load_csv("MRegularSeasonDetailedResults.csv")
    seeds_df = _load_csv("MNCAATourneySeeds.csv")

    if teams_df is None:
        logger.error("MTeams.csv is required")
        return {"error": "Missing MTeams.csv"}

    # Build kaggle_id → name mapping
    id_to_name = dict(zip(teams_df["TeamID"], teams_df["TeamName"]))

    # --- Ingest team season stats ---
    total_stats = 0
    if regular_df is not None:
        avg_df = _compute_season_averages(regular_df)

        # Parse seeds
        seed_lookup = {}
        if seeds_df is not None:
            for _, row in seeds_df.iterrows():
                seed_str = row["Seed"]
                seed_num = int("".join(c for c in seed_str if c.isdigit()))
                seed_lookup[(row["Season"], row["TeamID"])] = seed_num

        for _, row in avg_df.iterrows():
            team_name = id_to_name.get(row["TeamID"], f"Team_{row['TeamID']}")
            team = _get_or_create_team(session, team_name)

            season = int(row["Season"])
            existing = (
                session.query(TeamSeasonStats)
                .filter_by(team_id=team.id, season=season)
                .first()
            )
            if existing:
                continue

            stat = TeamSeasonStats(
                team_id=team.id,
                season=season,
                wins=int(row["wins"]),
                losses=int(row["losses"]),
                points_per_game=row["pts"],
                field_goal_pct=row["fg_pct"],
                three_point_pct=row["fg3_pct"],
                free_throw_pct=row["ft_pct"],
                offensive_rebounds_per_game=row["or"],
                assists_per_game=row["ast"],
                turnovers_per_game=row["to"],
                opp_points_per_game=row["opp_pts"],
                steals_per_game=row["stl"],
                blocks_per_game=row["blk"],
                defensive_rebounds_per_game=row["dr"],
                seed=seed_lookup.get((season, row["TeamID"])),
            )
            session.add(stat)
            total_stats += 1

        session.commit()

    # --- Ingest tournament games ---
    total_games = 0
    if tourney_df is not None:
        for _, row in tourney_df.iterrows():
            season = int(row["Season"])
            w_name = id_to_name.get(row["WTeamID"], f"Team_{row['WTeamID']}")
            l_name = id_to_name.get(row["LTeamID"], f"Team_{row['LTeamID']}")

            team_a = _get_or_create_team(session, w_name)
            team_b = _get_or_create_team(session, l_name)

            round_name, round_num = _assign_round(int(row["DayNum"]))

            existing = (
                session.query(TournamentGame)
                .filter_by(
                    season=season,
                    round_number=round_num,
                    team_a_id=team_a.id,
                    team_b_id=team_b.id,
                )
                .first()
            )
            if existing:
                continue

            game = TournamentGame(
                season=season,
                round_name=round_name,
                round_number=round_num,
                team_a_id=team_a.id,
                team_b_id=team_b.id,
                team_a_seed=None,
                team_b_seed=None,
                team_a_score=int(row["WScore"]),
                team_b_score=int(row["LScore"]),
                winner_id=team_a.id,
            )
            session.add(game)
            total_games += 1

        session.commit()

    session.close()
    logger.info("CSV load complete: %d stats, %d games", total_stats, total_games)
    return {"team_seasons": total_stats, "tournament_games": total_games}
