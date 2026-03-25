"""
Bracket simulation service.

Simulates a full 64-team NCAA tournament bracket using the trained
prediction model, producing per-round results with confidence scores
and model reliability metadata.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.data.database import SessionLocal, Team, TeamSeasonStats
from backend.app.models.predictor import predict_matchup

logger = logging.getLogger(__name__)

MODEL_METADATA_PATH = Path("models") / "model_metadata.json"

# Standard NCAA first-round seed matchups within each region (higher seed listed first).
FIRST_ROUND_SEED_MATCHUPS: List[Tuple[int, int]] = [
    (1, 16),
    (8, 9),
    (5, 12),
    (4, 13),
    (6, 11),
    (3, 14),
    (7, 10),
    (2, 15),
]

ROUND_NAMES: List[str] = ["R64", "R32", "S16", "E8", "F4", "Championship"]

# Region labels used when grouping the 64 teams into four pods.
REGION_LABELS: List[str] = ["South", "East", "West", "Midwest"]


def _load_round_accuracy() -> Dict[str, Any]:
    """Load per-round model accuracy metadata from disk."""
    if not MODEL_METADATA_PATH.exists():
        logger.warning("Model metadata file not found at %s", MODEL_METADATA_PATH)
        return {}
    with open(MODEL_METADATA_PATH, "r") as fh:
        metadata = json.load(fh)
    return metadata.get("round_accuracy", {})


def _fetch_tournament_teams(
    season: int,
) -> List[Dict[str, Any]]:
    """
    Return all tournament-seeded teams for *season*, ordered by seed.

    Each entry is a dict with keys: team_id, name, seed, conference.
    Raises ValueError if fewer than 64 seeded teams are found.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Team, TeamSeasonStats)
            .join(TeamSeasonStats, Team.id == TeamSeasonStats.team_id)
            .filter(
                TeamSeasonStats.season == season,
                TeamSeasonStats.seed.isnot(None),
            )
            .order_by(TeamSeasonStats.seed)
            .all()
        )

        teams = [
            {
                "team_id": team.id,
                "name": team.name,
                "seed": stats.seed,
                "conference": team.conference,
            }
            for team, stats in rows
        ]

        if len(teams) < 60:
            raise ValueError(
                f"Expected ~64 tournament teams for season {season}, "
                f"found {len(teams)}. Ensure seeding data has been ingested."
            )
        if len(teams) < 64:
            logger.warning(
                "Found %d teams for season %d (expected 64). "
                "Some play-in teams may be missing.",
                len(teams), season,
            )

        return teams
    finally:
        session.close()


def _assign_regions(
    teams: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Split 64 seeded teams into four 16-team regions.

    Teams are assumed to be ordered by seed.  For each seed value (1-16),
    the four teams holding that seed are distributed across the four regions
    in order.  This mirrors the real bracket structure where each region
    contains exactly one of each seed 1-16.
    """
    regions: Dict[str, List[Dict[str, Any]]] = {
        label: [] for label in REGION_LABELS
    }

    # Group teams by seed value.
    seed_groups: Dict[int, List[Dict[str, Any]]] = {}
    for team in teams:
        seed_groups.setdefault(team["seed"], []).append(team)

    for seed_val in range(1, 17):
        group = seed_groups.get(seed_val, [])
        for idx, team in enumerate(group):
            region_label = REGION_LABELS[idx % 4]
            regions[region_label].append(team)

    return regions


def _build_matchup_result(
    team_a: Dict[str, Any],
    team_b: Dict[str, Any],
    season: int,
    round_name: str,
    game_number: int,
    mode: str = "safe",
) -> Dict[str, Any]:
    """
    Run the predictor for a single game and return a structured result dict.
    """
    prediction = predict_matchup(
        team_a_name=team_a["name"],
        team_b_name=team_b["name"],
        season=season,
        mode=mode,
    )

    winner_name = prediction["winner"]
    winner_entry = team_a if team_a["name"] == winner_name else team_b
    loser_entry = team_b if winner_entry is team_a else team_a

    return {
        "game_number": game_number,
        "round": round_name,
        "team_a": {
            "name": team_a["name"],
            "seed": team_a["seed"],
            "win_probability": prediction["win_probability_a"],
        },
        "team_b": {
            "name": team_b["name"],
            "seed": team_b["seed"],
            "win_probability": prediction["win_probability_b"],
        },
        "predicted_winner": {
            "name": winner_entry["name"],
            "seed": winner_entry["seed"],
        },
        "confidence": prediction["confidence"],
        "stat_breakdown": prediction["stat_breakdown"],
    }


def _simulate_round(
    matchups: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    season: int,
    round_name: str,
    game_offset: int = 0,
    mode: str = "safe",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Simulate all games in a single round.

    Returns:
        (results, winners) where *results* is the list of game result dicts
        and *winners* is the list of advancing team entries (in matchup order).
    """
    results: List[Dict[str, Any]] = []
    winners: List[Dict[str, Any]] = []

    for idx, (team_a, team_b) in enumerate(matchups):
        game_result = _build_matchup_result(
            team_a, team_b, season, round_name, game_number=game_offset + idx + 1,
            mode=mode,
        )
        results.append(game_result)

        # Determine the advancing team entry.
        winner_name = game_result["predicted_winner"]["name"]
        winner_entry = team_a if team_a["name"] == winner_name else team_b
        winners.append(winner_entry)

    return results, winners


def _pair_winners(winners: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Pair up consecutive winners for the next round."""
    return [
        (winners[i], winners[i + 1])
        for i in range(0, len(winners), 2)
    ]


def simulate_bracket(season: int, mode: str = "safe") -> Dict[str, Any]:
    """
    Simulate a full 64-team NCAA tournament bracket for the given season.

    Returns a structured dict containing:
        - season
        - regions (with per-region round results through Elite Eight)
        - final_four, championship (cross-region rounds)
        - champion
        - model_reliability (per-round accuracy metadata)
    """
    round_accuracy = _load_round_accuracy()
    teams = _fetch_tournament_teams(season)
    regions = _assign_regions(teams)

    bracket: Dict[str, Any] = {
        "season": season,
        "regions": {},
        "final_four": None,
        "championship": None,
        "champion": None,
        "model_reliability": {},
    }

    # ---- Build model reliability section ----
    for rnd in ROUND_NAMES:
        info = round_accuracy.get(rnd, {})
        bracket["model_reliability"][rnd] = {
            "historical_accuracy": info.get("accuracy"),
            "sample_size": info.get("n_games"),
            "note": _reliability_note(rnd, info.get("accuracy")),
        }

    # ---- Simulate each region through the Elite Eight ----
    final_four_teams: List[Dict[str, Any]] = []
    game_counter = 0

    for region_label in REGION_LABELS:
        region_teams = regions[region_label]

        # Build a lookup by seed for easy first-round pairing.
        by_seed: Dict[int, Dict[str, Any]] = {t["seed"]: t for t in region_teams}

        # First round (Round of 64): pair by standard seed matchups.
        # Skip matchups where a seed is missing (play-in losers).
        r64_matchups: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        r64_byes: List[Dict[str, Any]] = []
        for hi, lo in FIRST_ROUND_SEED_MATCHUPS:
            if hi in by_seed and lo in by_seed:
                r64_matchups.append((by_seed[hi], by_seed[lo]))
            elif hi in by_seed:
                r64_byes.append(by_seed[hi])
            elif lo in by_seed:
                r64_byes.append(by_seed[lo])

        region_data: Dict[str, Any] = {
            "region": region_label,
            "teams": [
                {"name": t["name"], "seed": t["seed"]}
                for t in sorted(region_teams, key=lambda t: t["seed"])
            ],
            "rounds": {},
        }

        # R64
        r64_results, r64_winners = _simulate_round(
            r64_matchups, season, "R64", game_offset=game_counter, mode=mode
        )
        # Add bye teams (missing opponents) to winners list
        r64_winners.extend(r64_byes)
        game_counter += len(r64_results)
        region_data["rounds"]["R64"] = r64_results

        # R32
        r32_matchups = _pair_winners(r64_winners)
        r32_results, r32_winners = _simulate_round(
            r32_matchups, season, "R32", game_offset=game_counter, mode=mode
        )
        game_counter += len(r32_results)
        region_data["rounds"]["R32"] = r32_results

        # Sweet 16
        s16_matchups = _pair_winners(r32_winners)
        s16_results, s16_winners = _simulate_round(
            s16_matchups, season, "S16", game_offset=game_counter, mode=mode
        )
        game_counter += len(s16_results)
        region_data["rounds"]["S16"] = s16_results

        # Elite 8
        e8_matchups = _pair_winners(s16_winners)
        e8_results, e8_winners = _simulate_round(
            e8_matchups, season, "E8", game_offset=game_counter, mode=mode
        )
        game_counter += len(e8_results)
        region_data["rounds"]["E8"] = e8_results

        bracket["regions"][region_label] = region_data

        # The single E8 winner advances to the Final Four.
        assert len(e8_winners) == 1, (
            f"Expected 1 Elite Eight winner per region, got {len(e8_winners)}"
        )
        final_four_teams.append(e8_winners[0])

    # ---- Final Four ----
    f4_matchups: List[Tuple[Dict[str, Any], Dict[str, Any]]] = [
        (final_four_teams[0], final_four_teams[1]),
        (final_four_teams[2], final_four_teams[3]),
    ]
    f4_results, f4_winners = _simulate_round(
        f4_matchups, season, "F4", game_offset=game_counter, mode=mode
    )
    game_counter += len(f4_results)
    bracket["final_four"] = {
        "teams": [
            {"name": t["name"], "seed": t["seed"]}
            for t in final_four_teams
        ],
        "games": f4_results,
    }

    # ---- Championship ----
    champ_matchups = _pair_winners(f4_winners)
    champ_results, champ_winners = _simulate_round(
        champ_matchups, season, "Championship", game_offset=game_counter, mode=mode
    )
    bracket["championship"] = {
        "game": champ_results[0],
    }
    bracket["champion"] = {
        "name": champ_winners[0]["name"],
        "seed": champ_winners[0]["seed"],
    }

    bracket["total_games"] = game_counter + len(champ_results)

    return bracket


def _reliability_note(round_name: str, accuracy: Optional[float]) -> str:
    """Generate a human-readable reliability note for a tournament round."""
    if accuracy is None:
        return "No historical accuracy data available."
    if accuracy >= 0.85:
        return "High reliability — model performs strongly in this round."
    if accuracy >= 0.70:
        return "Moderate reliability — predictions are solid but upsets occur."
    if accuracy >= 0.55:
        return "Lower reliability — later rounds are inherently harder to predict."
    return "Limited reliability — treat predictions with caution."
