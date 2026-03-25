"""
Scrape historical NCAA tournament results and team season stats
from Sports Reference (sports-reference.com/cbb).

Covers 2008-present (configurable). Respects rate limits with delays.
"""

import logging
import re
import time
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

from backend.app.data.team_names import normalize_team_name

logger = logging.getLogger(__name__)

BASE_URL = "https://www.sports-reference.com/cbb"
REQUEST_DELAY = 3.5  # Sports Reference rate-limits at ~20 req/min

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _get(url: str) -> Optional[BeautifulSoup]:
    """GET with rate-limiting and error handling."""
    time.sleep(REQUEST_DELAY)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Tournament bracket scraping
# ---------------------------------------------------------------------------

def _parse_team_div(div) -> Optional[dict]:
    """
    Parse a team div from the bracket HTML.
    Structure: <div [class="winner"]><span>seed</span><a>team</a><a>score</a></div>
    """
    span = div.find("span")
    links = div.find_all("a")
    if not links:
        return None

    team_name = None
    score = None
    for link in links:
        href = link.get("href", "")
        text = link.get_text(strip=True)
        if "/cbb/schools/" in href and team_name is None:
            team_name = text
        elif "/cbb/boxscores/" in href and text.isdigit():
            score = int(text)

    if team_name is None:
        return None

    seed = None
    if span:
        seed_text = span.get_text(strip=True)
        if seed_text.isdigit():
            seed = int(seed_text)

    is_winner = "winner" in (div.get("class") or [])

    return {"name": team_name, "seed": seed, "score": score, "is_winner": is_winner}


def scrape_tournament_results(season: int) -> list[dict]:
    """
    Scrape NCAA tournament bracket for a given season.
    Returns list of game dicts with: season, round_name, round_number,
    team_a, team_b, seed_a, seed_b, score_a, score_b, winner.
    """
    url = f"{BASE_URL}/postseason/{season}-ncaa.html"
    soup = _get(url)
    if soup is None:
        return []

    games = []
    bracket = soup.find("div", {"id": "brackets"})
    if not bracket:
        logger.warning("No bracket found for %d", season)
        return []

    # Each region has <div class="round"> elements containing game divs.
    # Each game div has two team child divs + a location span.
    for round_div in bracket.find_all("div", class_="round"):
        for game_div in round_div.find_all("div", recursive=False):
            # Each game_div should have 2 team child divs
            team_divs = [
                d for d in game_div.find_all("div", recursive=False)
                if d.find("a")
            ]
            if len(team_divs) < 2:
                continue

            a = _parse_team_div(team_divs[0])
            b = _parse_team_div(team_divs[1])
            if a is None or b is None:
                continue

            # Determine winner from the "winner" class
            winner = None
            if a["is_winner"]:
                winner = a["name"]
            elif b["is_winner"]:
                winner = b["name"]
            elif a["score"] is not None and b["score"] is not None:
                winner = a["name"] if a["score"] > b["score"] else b["name"]

            games.append({
                "season": season,
                "team_a": a["name"],
                "team_b": b["name"],
                "seed_a": a["seed"],
                "seed_b": b["seed"],
                "score_a": a["score"],
                "score_b": b["score"],
                "winner": winner,
            })

    # Assign round info based on game count pattern: 32, 16, 8, 4, 2, 1
    round_sizes = [32, 16, 8, 4, 2, 1]
    round_labels = [("R64", 1), ("R32", 2), ("S16", 3), ("E8", 4), ("F4", 5), ("championship", 6)]
    idx = 0
    for size, (rname, rnum) in zip(round_sizes, round_labels):
        for j in range(size):
            if idx < len(games):
                games[idx]["round_name"] = rname
                games[idx]["round_number"] = rnum
                idx += 1

    logger.info("Scraped %d tournament games for %d", len(games), season)
    return games


# ---------------------------------------------------------------------------
# Team season stats scraping
# ---------------------------------------------------------------------------

def _parse_table_by_data_stat(table) -> list[dict]:
    """Parse a Sports Reference table using data-stat attributes as keys."""
    rows = []
    tbody = table.find("tbody")
    if tbody is None:
        return rows

    for tr in tbody.find_all("tr"):
        if tr.get("class") and "thead" in tr.get("class", []):
            continue
        cells = tr.find_all(["th", "td"])
        if len(cells) < 5:
            continue
        row = {}
        for cell in cells:
            key = cell.get("data-stat", "")
            if key and key != "DUMMY":
                row[key] = cell.get_text(strip=True)
        if row.get("school_name"):
            rows.append(row)
    return rows


def scrape_team_season_stats(season: int) -> pd.DataFrame:
    """
    Scrape team-level season statistics from Sports Reference.
    Returns DataFrame with one row per team, keyed by data-stat attributes.
    """
    url = f"{BASE_URL}/seasons/{season}-school-stats.html"
    soup = _get(url)
    if soup is None:
        return pd.DataFrame()

    table = soup.find("table", {"id": "basic_school_stats"})
    if table is None:
        logger.warning("No stats table for %d", season)
        return pd.DataFrame()

    rows = _parse_table_by_data_stat(table)
    df = pd.DataFrame(rows)
    df["season"] = season
    return df


def scrape_advanced_stats(season: int) -> pd.DataFrame:
    """Scrape advanced/efficiency stats from Sports Reference."""
    url = f"{BASE_URL}/seasons/{season}-advanced-school-stats.html"
    soup = _get(url)
    if soup is None:
        return pd.DataFrame()

    table = soup.find("table", {"id": "adv_school_stats"})
    if table is None:
        logger.warning("No advanced stats table for %d", season)
        return pd.DataFrame()

    rows = _parse_table_by_data_stat(table)
    df = pd.DataFrame(rows)
    df["season"] = season
    return df


# ---------------------------------------------------------------------------
# Seed data from tournament pages
# ---------------------------------------------------------------------------

def scrape_tournament_seeds(season: int) -> dict[str, int]:
    """Return {normalized_team_name: seed} from the bracket page."""
    url = f"{BASE_URL}/postseason/{season}-ncaa.html"
    soup = _get(url)
    if soup is None:
        return {}

    seeds = {}
    bracket = soup.find("div", {"id": "brackets"})
    if not bracket:
        return {}

    for span in bracket.find_all("span"):
        seed_text = span.get_text(strip=True)
        if seed_text.isdigit():
            link = span.find_next("a")
            if link and "/cbb/schools/" in link.get("href", ""):
                team = normalize_team_name(link.get_text(strip=True))
                seeds[team] = int(seed_text)

    return seeds
