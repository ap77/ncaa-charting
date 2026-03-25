"""
Bracket simulation service.

Pulls the REAL tournament bracket from the database (scraped from
Sports Reference) and simulates every game using the trained model.
Uses actual first-round matchups, not synthetic ones.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.data.database import SessionLocal, Team, TeamSeasonStats, TournamentGame
from app.models.predictor import predict_matchup

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODEL_METADATA_PATH = _PROJECT_ROOT / "models" / "safe_jen_metadata.json"

FIRST_ROUND_SEED_PAIRS = {
    (1, 16), (8, 9), (5, 12), (4, 13),
    (6, 11), (3, 14), (7, 10), (2, 15),
}

ROUND_NAMES = ["R64", "R32", "S16", "E8", "F4", "Championship"]
REGION_LABELS = ["Region 1", "Region 2", "Region 3", "Region 4"]


def _load_round_accuracy() -> Dict[str, Any]:
    if not MODEL_METADATA_PATH.exists():
        return {}
    with open(MODEL_METADATA_PATH, "r") as fh:
        metadata = json.load(fh)
    return metadata.get("round_accuracy", {})


def _fetch_real_r64(season: int) -> List[List[Tuple[Dict[str, Any], Dict[str, Any]]]]:
    """
    Fetch the actual R64 matchups from the DB, grouped into 4 regions of 8 games.

    Returns a list of 4 regions, each containing 8 (team_a, team_b) tuples
    in bracket order.
    """
    session = SessionLocal()
    try:
        all_games = (
            session.query(TournamentGame)
            .filter_by(season=season)
            .order_by(TournamentGame.id)
            .all()
        )

        # Identify R64 games by seed pattern (1v16, 8v9, etc.)
        r64_matchups = []
        for g in all_games:
            pair = (min(g.team_a_seed or 0, g.team_b_seed or 0),
                    max(g.team_a_seed or 0, g.team_b_seed or 0))
            if pair in FIRST_ROUND_SEED_PAIRS:
                team_a = session.get(Team, g.team_a_id)
                team_b = session.get(Team, g.team_b_id)
                r64_matchups.append((
                    {"name": team_a.name, "seed": g.team_a_seed},
                    {"name": team_b.name, "seed": g.team_b_seed},
                ))

        if len(r64_matchups) < 32:
            raise ValueError(
                f"Expected 32 R64 games for season {season}, found {len(r64_matchups)}. "
                f"Ensure bracket data has been ingested."
            )

        # Split into 4 regions of 8 games (they come in bracket order from the scraper)
        regions = []
        for i in range(0, 32, 8):
            regions.append(r64_matchups[i:i + 8])

        return regions
    finally:
        session.close()


def _get_region_label(season: int, region_idx: int) -> str:
    """Get the region label. We use generic labels since the scraper
    doesn't reliably capture region names."""
    # Common region name patterns by 1-seed
    return REGION_LABELS[region_idx]


def _build_matchup_result(
    team_a: Dict[str, Any],
    team_b: Dict[str, Any],
    season: int,
    round_name: str,
    game_number: int,
    mode: str = "safe",
) -> Dict[str, Any]:
    prediction = predict_matchup(
        team_a_name=team_a["name"],
        team_b_name=team_b["name"],
        season=season,
        mode=mode,
    )

    winner_name = prediction["winner"]
    winner_entry = team_a if team_a["name"] == winner_name else team_b

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
    results = []
    winners = []

    for idx, (team_a, team_b) in enumerate(matchups):
        game_result = _build_matchup_result(
            team_a, team_b, season, round_name,
            game_number=game_offset + idx + 1, mode=mode,
        )
        results.append(game_result)

        winner_name = game_result["predicted_winner"]["name"]
        winner_entry = team_a if team_a["name"] == winner_name else team_b
        winners.append(winner_entry)

    return results, winners


def _pair_winners(winners: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    return [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]


def simulate_bracket(season: int, mode: str = "safe") -> Dict[str, Any]:
    """
    Simulate a full NCAA tournament bracket using REAL matchups
    from the database for the given season.
    """
    round_accuracy = _load_round_accuracy()
    region_matchups = _fetch_real_r64(season)

    bracket = {
        "season": season,
        "regions": {},
        "final_four": None,
        "championship": None,
        "champion": None,
        "model_reliability": {},
    }

    for rnd in ROUND_NAMES:
        info = round_accuracy.get(rnd, {})
        bracket["model_reliability"][rnd] = {
            "historical_accuracy": info.get("accuracy"),
            "sample_size": info.get("n_games"),
            "note": _reliability_note(rnd, info.get("accuracy")),
        }

    final_four_teams = []
    game_counter = 0

    for region_idx, r64_games in enumerate(region_matchups):
        region_label = _get_region_label(season, region_idx)

        # Collect all teams in this region for display
        all_teams = set()
        for a, b in r64_games:
            all_teams.add((a["name"], a["seed"]))
            all_teams.add((b["name"], b["seed"]))

        region_data = {
            "region": region_label,
            "teams": [
                {"name": name, "seed": seed}
                for name, seed in sorted(all_teams, key=lambda x: x[1])
            ],
            "rounds": {},
        }

        # R64 — use the REAL matchups
        r64_results, r64_winners = _simulate_round(
            r64_games, season, "R64", game_offset=game_counter, mode=mode
        )
        game_counter += len(r64_results)
        region_data["rounds"]["R64"] = r64_results

        # R32 — pair consecutive R64 winners
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
        final_four_teams.append(e8_winners[0])

    # Final Four
    f4_matchups = [
        (final_four_teams[0], final_four_teams[1]),
        (final_four_teams[2], final_four_teams[3]),
    ]
    f4_results, f4_winners = _simulate_round(
        f4_matchups, season, "F4", game_offset=game_counter, mode=mode
    )
    game_counter += len(f4_results)
    bracket["final_four"] = {
        "teams": [{"name": t["name"], "seed": t["seed"]} for t in final_four_teams],
        "games": f4_results,
    }

    # Championship
    champ_matchups = _pair_winners(f4_winners)
    champ_results, champ_winners = _simulate_round(
        champ_matchups, season, "Championship", game_offset=game_counter, mode=mode
    )
    bracket["championship"] = {"game": champ_results[0]}
    bracket["champion"] = {
        "name": champ_winners[0]["name"],
        "seed": champ_winners[0]["seed"],
    }
    bracket["total_games"] = game_counter + len(champ_results)

    return bracket


def _reliability_note(round_name: str, accuracy: Optional[float]) -> str:
    if accuracy is None:
        return "No historical accuracy data available."
    if accuracy >= 0.85:
        return "High reliability -- model performs strongly in this round."
    if accuracy >= 0.70:
        return "Moderate reliability -- predictions are solid but upsets occur."
    if accuracy >= 0.55:
        return "Lower reliability -- later rounds are inherently harder to predict."
    return "Limited reliability -- treat predictions with caution."
