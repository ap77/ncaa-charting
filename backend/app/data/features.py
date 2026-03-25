"""
Feature engineering for matchup prediction.

Transforms raw team season stats into pairwise matchup features
for model training and inference.

Key design: features are computed as (Team A stat - Team B stat) deltas,
making the model learn relative advantage rather than absolute values.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.data.database import SessionLocal, TeamSeasonStats, TournamentGame, Team

logger = logging.getLogger(__name__)

# The 18 features our model uses, ordered by typical predictive importance
STAT_COLUMNS = [
    "adjusted_offensive_efficiency",
    "adjusted_defensive_efficiency",
    "simple_rating_system",
    "strength_of_schedule",
    "points_per_game",
    "opp_points_per_game",
    "field_goal_pct",
    "three_point_pct",
    "free_throw_pct",
    "tempo",
    "offensive_rebounds_per_game",
    "defensive_rebounds_per_game",
    "assists_per_game",
    "turnovers_per_game",
    "steals_per_game",
    "blocks_per_game",
    "wins",
    "losses",
]

# Readable display names for the UI
STAT_DISPLAY_NAMES = {
    "adjusted_offensive_efficiency": "Adj. Offensive Efficiency",
    "adjusted_defensive_efficiency": "Adj. Defensive Efficiency",
    "simple_rating_system": "Simple Rating System (SRS)",
    "strength_of_schedule": "Strength of Schedule",
    "points_per_game": "Points Per Game",
    "opp_points_per_game": "Opp. Points Per Game",
    "field_goal_pct": "Field Goal %",
    "three_point_pct": "3-Point %",
    "free_throw_pct": "Free Throw %",
    "tempo": "Tempo (Possessions/Game)",
    "offensive_rebounds_per_game": "Offensive Rebounds/Game",
    "defensive_rebounds_per_game": "Defensive Rebounds/Game",
    "assists_per_game": "Assists/Game",
    "turnovers_per_game": "Turnovers/Game",
    "steals_per_game": "Steals/Game",
    "blocks_per_game": "Blocks/Game",
    "wins": "Season Wins",
    "losses": "Season Losses",
    "seed_diff": "Seed Difference",
}


def _stats_to_dict(stat: TeamSeasonStats) -> dict:
    """Convert a TeamSeasonStats ORM object to a dict of numeric values."""
    return {col: getattr(stat, col) for col in STAT_COLUMNS}


def build_matchup_features(
    stats_a: dict,
    stats_b: dict,
    seed_a: Optional[int] = None,
    seed_b: Optional[int] = None,
) -> dict:
    """
    Compute delta features for a matchup: (Team A - Team B).

    For defensive stats and turnovers/losses, lower is better,
    so the delta interpretation stays consistent:
    positive delta = Team A advantage.
    """
    features = {}
    for col in STAT_COLUMNS:
        val_a = stats_a.get(col)
        val_b = stats_b.get(col)
        if val_a is not None and val_b is not None:
            features[f"delta_{col}"] = float(val_a) - float(val_b)
        else:
            features[f"delta_{col}"] = 0.0

    # Flip sign for stats where lower is better (so positive = A is better)
    for col in ["adjusted_defensive_efficiency", "opp_points_per_game", "turnovers_per_game", "losses"]:
        key = f"delta_{col}"
        if key in features:
            features[key] = -features[key]

    # Seed difference (lower seed = better, so flip)
    if seed_a is not None and seed_b is not None:
        features["seed_diff"] = float(seed_b) - float(seed_a)  # positive = A has better seed
    else:
        features["seed_diff"] = 0.0

    return features


def build_training_dataset(session: Session = None) -> pd.DataFrame:
    """
    Build the full training dataset from stored tournament games + stats.

    Each row = one tournament matchup with delta features and binary label
    (1 = team_a won, 0 = team_b won).
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        games = session.query(TournamentGame).all()
        rows = []

        for game in games:
            stats_a = (
                session.query(TeamSeasonStats)
                .filter_by(team_id=game.team_a_id, season=game.season)
                .first()
            )
            stats_b = (
                session.query(TeamSeasonStats)
                .filter_by(team_id=game.team_b_id, season=game.season)
                .first()
            )

            if stats_a is None or stats_b is None:
                continue

            features = build_matchup_features(
                _stats_to_dict(stats_a),
                _stats_to_dict(stats_b),
                seed_a=game.team_a_seed or stats_a.seed,
                seed_b=game.team_b_seed or stats_b.seed,
            )

            features["label"] = 1 if game.winner_id == game.team_a_id else 0
            features["season"] = game.season
            features["round_number"] = game.round_number

            rows.append(features)

        df = pd.DataFrame(rows)
        logger.info("Built training dataset: %d matchups, %d features", len(df), len(df.columns) - 3)
        return df

    finally:
        if close_session:
            session.close()


def get_feature_names() -> list[str]:
    """Return ordered list of feature column names the model expects."""
    return [f"delta_{col}" for col in STAT_COLUMNS] + ["seed_diff"]
