"""
Feature engineering for matchup prediction.

Transforms raw team season stats into pairwise matchup features
for model training and inference.

Key design: features are computed as (Team A stat - Team B stat) deltas,
making the model learn relative advantage rather than absolute values.

Feature philosophy: prioritize causal game factors (efficiency, tempo,
rate stats) over selection proxies (wins, seeds, SOS). Selection proxies
correlate with winning but don't cause it in a specific matchup.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.data.database import SessionLocal, TeamSeasonStats, TournamentGame, Team

logger = logging.getLogger(__name__)

# ---- TIER 1: Causal game factors (efficiency & rate stats) ----
# These directly measure HOW a team plays, not how good their resume looks.
TIER1_STATS = [
    "adjusted_offensive_efficiency",   # Points per 100 possessions
    "adjusted_defensive_efficiency",   # Opp points per 100 possessions
    "effective_fg_pct",                # eFG% (weights 3s)
    "true_shooting_pct",               # TS% (includes FTs)
    "turnover_pct",                    # TOV% — turnovers per 100 plays
    "offensive_rebound_pct",           # ORB% — second-chance rate
    "total_rebound_pct",              # TRB% — overall board control
    "free_throw_rate",                 # FTA/FGA — getting to the line
    "three_point_rate",                # 3PA/FGA — reliance on the 3
    "tempo",                           # Pace — possessions per game
    "free_throw_pct",                  # FT% — clutch shooting
]

# ---- TIER 2: Supporting box-score stats ----
TIER2_STATS = [
    "assist_pct",                      # AST% — ball movement
    "steal_pct",                       # STL% — disruptive defense
    "block_pct",                       # BLK% — rim protection
    "points_per_game",
    "opp_points_per_game",
    "field_goal_pct",
    "three_point_pct",
]

# ---- TIER 3: Selection proxies (kept but de-emphasized) ----
# These tell you the team is good, not why they'd win a specific game.
TIER3_STATS = [
    "wins",
    "losses",
    "strength_of_schedule",
    "simple_rating_system",
]

# Combined list — all stats available for UI display
STAT_COLUMNS = TIER1_STATS + TIER2_STATS + TIER3_STATS

# Features the model actually trains on — excludes selection proxies.
# Wins, losses, SOS, SRS, and seed_diff are shown in the UI for context
# but do NOT influence the model's prediction.
TRAINING_STATS = TIER1_STATS + TIER2_STATS

# Readable display names for the UI
STAT_DISPLAY_NAMES = {
    "adjusted_offensive_efficiency": "Adj. Offensive Efficiency",
    "adjusted_defensive_efficiency": "Adj. Defensive Efficiency",
    "effective_fg_pct": "Effective FG%",
    "true_shooting_pct": "True Shooting %",
    "turnover_pct": "Turnover Rate (TOV%)",
    "offensive_rebound_pct": "Off. Rebound %",
    "total_rebound_pct": "Total Rebound %",
    "free_throw_rate": "Free Throw Rate (FTA/FGA)",
    "three_point_rate": "3-Point Rate (3PA/FGA)",
    "tempo": "Tempo (Possessions/Game)",
    "free_throw_pct": "Free Throw %",
    "assist_pct": "Assist Rate (AST%)",
    "steal_pct": "Steal Rate (STL%)",
    "block_pct": "Block Rate (BLK%)",
    "points_per_game": "Points Per Game",
    "opp_points_per_game": "Opp. Points Per Game",
    "field_goal_pct": "Field Goal %",
    "three_point_pct": "3-Point %",
    "wins": "Season Wins",
    "losses": "Season Losses",
    "strength_of_schedule": "Strength of Schedule",
    "simple_rating_system": "Simple Rating System (SRS)",
    "seed_diff": "Seed Difference",
}

# Stats where lower = better (flip sign so positive delta = Team A advantage)
LOWER_IS_BETTER = [
    "adjusted_defensive_efficiency",
    "opp_points_per_game",
    "turnover_pct",
    "losses",
]


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

    Positive delta = Team A advantage for all features
    (defensive/turnover stats are sign-flipped).
    """
    features = {}
    for col in STAT_COLUMNS:
        val_a = stats_a.get(col)
        val_b = stats_b.get(col)
        if val_a is not None and val_b is not None:
            features[f"delta_{col}"] = float(val_a) - float(val_b)
        else:
            features[f"delta_{col}"] = 0.0

    # Flip sign for stats where lower is better
    for col in LOWER_IS_BETTER:
        key = f"delta_{col}"
        if key in features:
            features[key] = -features[key]

    # Seed difference (lower seed = better, so flip)
    if seed_a is not None and seed_b is not None:
        features["seed_diff"] = float(seed_b) - float(seed_a)
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


def get_feature_names():
    """Return ordered list of feature column names the model trains on.
    Excludes selection proxies (wins, losses, SOS, SRS, seed_diff)."""
    return [f"delta_{col}" for col in TRAINING_STATS]


def get_all_feature_names():
    """Return all feature names including proxies (for UI display)."""
    return [f"delta_{col}" for col in STAT_COLUMNS] + ["seed_diff"]
