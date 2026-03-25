"""
Prediction service: load trained models and generate matchup predictions
with feature-importance-based explainability.

Supports two modes:
- "safe": Uses all features including selection proxies (seeds, wins, SOS)
- "spicy": Uses only causal game factors (efficiency, rate stats, tempo)
"""

import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from app.data.database import SessionLocal, Team, TeamSeasonStats
from app.data.features import (
    STAT_COLUMNS,
    STAT_DISPLAY_NAMES,
    build_matchup_features,
    get_feature_names,
    get_all_feature_names,
)
from app.data.team_names import normalize_team_name

logger = logging.getLogger(__name__)

# Find models dir — works both locally and in Docker
MODEL_DIR = None
for _candidate in [
    Path(__file__).resolve().parent.parent.parent.parent / "models",
    Path(__file__).resolve().parent.parent.parent / "models",
    Path("/app/models"),
]:
    if _candidate.exists():
        MODEL_DIR = _candidate
        break
if MODEL_DIR is None:
    MODEL_DIR = Path("models")

_models = {}  # mode -> (model, feature_cols)


def _load_model(mode: str = "safe"):
    """Lazy-load model for the given mode."""
    if mode in _models:
        return _models[mode]

    if mode == "spicy":
        model_path = MODEL_DIR / "spicy_jen.joblib"
        feature_cols = get_feature_names()
    else:
        model_path = MODEL_DIR / "safe_jen.joblib"
        feature_cols = get_all_feature_names()

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found ({mode}). Run training first."
        )

    model = joblib.load(model_path)
    _models[mode] = (model, feature_cols)
    return model, feature_cols


def _get_team_stats(session, team_name: str, season: int):
    """Look up a team and its season stats."""
    normalized = normalize_team_name(team_name)
    team = session.query(Team).filter_by(name_normalized=normalized).first()
    if team is None:
        team = session.query(Team).filter(Team.name.ilike(f"%{team_name}%")).first()
    if team is None:
        raise ValueError(f"Team not found: '{team_name}'")

    stats = (
        session.query(TeamSeasonStats)
        .filter_by(team_id=team.id, season=season)
        .first()
    )

    # If no stats, try via normalized alias (e.g. "Penn" -> "Pennsylvania")
    if stats is None and normalized != team.name_normalized:
        alt_team = session.query(Team).filter_by(name_normalized=normalized).first()
        if alt_team and alt_team.id != team.id:
            stats = (
                session.query(TeamSeasonStats)
                .filter_by(team_id=alt_team.id, season=season)
                .first()
            )
            if stats:
                team = alt_team

    # Fallback: most recent season
    if stats is None:
        stats = (
            session.query(TeamSeasonStats)
            .filter_by(team_id=team.id)
            .order_by(TeamSeasonStats.season.desc())
            .first()
        )
    if stats is None:
        raise ValueError(f"No stats found for {team.name} in season {season}")

    return team, stats


def predict_matchup(
    team_a_name: str,
    team_b_name: str,
    season: int = 2026,
    mode: str = "safe",
) -> dict:
    """Predict the winner of a matchup between two teams."""
    model, feature_cols = _load_model(mode)

    session = SessionLocal()
    try:
        team_a, stats_a = _get_team_stats(session, team_a_name, season)
        team_b, stats_b = _get_team_stats(session, team_b_name, season)

        stats_a_dict = {col: getattr(stats_a, col) for col in STAT_COLUMNS}
        stats_b_dict = {col: getattr(stats_b, col) for col in STAT_COLUMNS}

        features = build_matchup_features(
            stats_a_dict, stats_b_dict,
            seed_a=stats_a.seed, seed_b=stats_b.seed,
        )

        X = np.array([[features[col] for col in feature_cols]])

        prob_a = model.predict_proba(X)[0, 1]
        prob_b = 1.0 - prob_a

        winner = team_a.name if prob_a >= 0.5 else team_b.name
        loser = team_b.name if prob_a >= 0.5 else team_a.name
        confidence = max(prob_a, prob_b)

        # Build explanation using feature importance * delta direction
        importances = model.feature_importances_
        stat_breakdown = _build_stat_breakdown(
            feature_cols, importances, features,
            stats_a_dict, stats_b_dict,
            team_a.name, team_b.name,
            seed_a=stats_a.seed, seed_b=stats_b.seed,
            prob_a=prob_a,
        )

        return {
            "winner": winner,
            "loser": loser,
            "confidence": round(float(confidence), 4),
            "team_a": team_a.name,
            "team_b": team_b.name,
            "win_probability_a": round(float(prob_a), 4),
            "win_probability_b": round(float(prob_b), 4),
            "mode": mode,
            "stat_breakdown": stat_breakdown,
        }
    finally:
        session.close()


def _build_stat_breakdown(
    feature_cols, importances, features, stats_a, stats_b,
    name_a, name_b, seed_a=None, seed_b=None, prob_a=0.5,
):
    """
    Build a ranked list of stat contributions using feature importance
    weighted by the delta value direction.

    Impact = feature_importance * |delta|, direction based on which
    team the delta favors relative to the prediction.
    """
    breakdown = []

    for i, col in enumerate(feature_cols):
        delta = features[col]
        importance = float(importances[i])

        if col == "seed_diff":
            stat_key = "seed_diff"
            val_a = seed_a
            val_b = seed_b
        else:
            stat_key = col.replace("delta_", "")
            val_a = stats_a.get(stat_key)
            val_b = stats_b.get(stat_key)

        display_name = STAT_DISPLAY_NAMES.get(stat_key, stat_key)

        # Impact = importance * |delta| (how much this feature matters here)
        impact = importance * abs(delta) if delta != 0 else 0.0

        # Direction: positive delta favors team A (by feature design)
        direction = impact if delta > 0 else -impact
        favors = name_a if delta > 0 else name_b

        breakdown.append({
            "stat": display_name,
            "stat_key": stat_key,
            "impact": round(impact, 4),
            "direction": round(direction, 4),
            "team_a_value": round(float(val_a), 2) if val_a is not None else None,
            "team_b_value": round(float(val_b), 2) if val_b is not None else None,
            "delta": round(float(delta), 4),
            "favors": favors,
        })

    breakdown.sort(key=lambda x: x["impact"], reverse=True)
    return breakdown
