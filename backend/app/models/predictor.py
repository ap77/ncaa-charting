"""
Prediction service: load trained model and generate matchup predictions
with SHAP-based explainability.
"""

import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import shap

from backend.app.data.database import SessionLocal, Team, TeamSeasonStats
from backend.app.data.features import (
    STAT_COLUMNS,
    STAT_DISPLAY_NAMES,
    build_matchup_features,
    get_feature_names,
)
from backend.app.data.team_names import normalize_team_name

logger = logging.getLogger(__name__)

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "bracket_predictor.joblib"
SHAP_PATH = MODEL_DIR / "shap_explainer.joblib"

_model = None
_explainer = None


def _load_model():
    """Lazy-load model and SHAP explainer."""
    global _model, _explainer
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Model not found. Run training first: python -m backend.scripts.run_train"
            )
        _model = joblib.load(MODEL_PATH)
        _explainer = joblib.load(SHAP_PATH)
    return _model, _explainer


def _get_team_stats(session, team_name: str, season: int) -> tuple[Team, TeamSeasonStats]:
    """Look up a team and its season stats."""
    normalized = normalize_team_name(team_name)
    team = session.query(Team).filter_by(name_normalized=normalized).first()
    if team is None:
        # Fuzzy fallback: try ilike match
        team = session.query(Team).filter(Team.name.ilike(f"%{team_name}%")).first()
    if team is None:
        raise ValueError(f"Team not found: '{team_name}'")

    stats = (
        session.query(TeamSeasonStats)
        .filter_by(team_id=team.id, season=season)
        .first()
    )
    if stats is None:
        # Try most recent season
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
    season: int = 2025,
) -> dict:
    """
    Predict the winner of a matchup between two teams.

    Returns:
        {
            "winner": str,
            "loser": str,
            "confidence": float (0-1),
            "team_a": str,
            "team_b": str,
            "win_probability_a": float,
            "win_probability_b": float,
            "stat_breakdown": [
                {
                    "stat": str (display name),
                    "stat_key": str,
                    "impact": float (SHAP value, positive = favors A),
                    "team_a_value": float,
                    "team_b_value": float,
                    "delta": float,
                    "favors": str (team name),
                },
                ...
            ]
        }
    """
    model, explainer = _load_model()
    feature_cols = get_feature_names()

    session = SessionLocal()
    try:
        team_a, stats_a = _get_team_stats(session, team_a_name, season)
        team_b, stats_b = _get_team_stats(session, team_b_name, season)

        # Build features
        stats_a_dict = {col: getattr(stats_a, col) for col in STAT_COLUMNS}
        stats_b_dict = {col: getattr(stats_b, col) for col in STAT_COLUMNS}

        features = build_matchup_features(
            stats_a_dict, stats_b_dict,
            seed_a=stats_a.seed, seed_b=stats_b.seed,
        )

        X = np.array([[features[col] for col in feature_cols]])

        # Predict
        prob_a = model.predict_proba(X)[0, 1]  # P(team_a wins)
        prob_b = 1.0 - prob_a

        winner = team_a.name if prob_a >= 0.5 else team_b.name
        loser = team_b.name if prob_a >= 0.5 else team_a.name
        confidence = max(prob_a, prob_b)

        # SHAP explanation
        shap_values = explainer.shap_values(X)[0]  # shape: (n_features,)

        stat_breakdown = _build_stat_breakdown(
            feature_cols, shap_values, features,
            stats_a_dict, stats_b_dict,
            team_a.name, team_b.name,
            seed_a=stats_a.seed, seed_b=stats_b.seed,
        )

        return {
            "winner": winner,
            "loser": loser,
            "confidence": round(float(confidence), 4),
            "team_a": team_a.name,
            "team_b": team_b.name,
            "win_probability_a": round(float(prob_a), 4),
            "win_probability_b": round(float(prob_b), 4),
            "stat_breakdown": stat_breakdown,
        }
    finally:
        session.close()


def _build_stat_breakdown(
    feature_cols: list[str],
    shap_values: np.ndarray,
    features: dict,
    stats_a: dict,
    stats_b: dict,
    name_a: str,
    name_b: str,
    seed_a: Optional[int] = None,
    seed_b: Optional[int] = None,
) -> list[dict]:
    """
    Build a ranked list of stat contributions to the prediction.
    Sorted by absolute SHAP impact (most influential first).
    """
    breakdown = []

    for i, col in enumerate(feature_cols):
        shap_val = float(shap_values[i])
        delta = features[col]

        # Map feature column back to the original stat name
        if col == "seed_diff":
            stat_key = "seed_diff"
            val_a = seed_a
            val_b = seed_b
        else:
            stat_key = col.replace("delta_", "")
            val_a = stats_a.get(stat_key)
            val_b = stats_b.get(stat_key)

        display_name = STAT_DISPLAY_NAMES.get(stat_key, stat_key)

        # Positive SHAP = favors team A winning
        favors = name_a if shap_val > 0 else name_b

        breakdown.append({
            "stat": display_name,
            "stat_key": stat_key,
            "impact": round(abs(shap_val), 4),
            "direction": round(shap_val, 4),
            "team_a_value": round(float(val_a), 2) if val_a is not None else None,
            "team_b_value": round(float(val_b), 2) if val_b is not None else None,
            "delta": round(float(delta), 4),
            "favors": favors,
        })

    # Sort by absolute impact, descending
    breakdown.sort(key=lambda x: x["impact"], reverse=True)
    return breakdown
