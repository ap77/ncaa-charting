#!/usr/bin/env python3
"""Backfill advanced rate stats into existing team_season_stats records."""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from backend.app.data.database import SessionLocal, TeamSeasonStats, Team
from backend.app.data.scraper import scrape_advanced_stats
from backend.app.data.team_names import normalize_team_name

SEASONS = [y for y in range(2008, 2026) if y != 2020]


def safe_float(val):
    try:
        v = float(val)
        import math
        return v if math.isfinite(v) else None
    except (ValueError, TypeError):
        return None


def backfill():
    session = SessionLocal()
    total_updated = 0

    for season in SEASONS:
        logger.info("Backfilling advanced stats for %d...", season)
        adv_df = scrape_advanced_stats(season)
        if adv_df.empty:
            logger.warning("No advanced stats for %d", season)
            continue

        if "school_name" not in adv_df.columns:
            logger.warning("No school_name column for %d", season)
            continue

        updated = 0
        for _, row in adv_df.iterrows():
            name = row.get("school_name", "")
            if not name:
                continue
            norm = normalize_team_name(name)
            team = session.query(Team).filter_by(name_normalized=norm).first()
            if not team:
                continue
            stat = session.query(TeamSeasonStats).filter_by(
                team_id=team.id, season=season
            ).first()
            if not stat:
                continue

            stat.effective_fg_pct = safe_float(row.get("efg_pct"))
            stat.true_shooting_pct = safe_float(row.get("ts_pct"))
            stat.turnover_pct = safe_float(row.get("tov_pct"))
            stat.offensive_rebound_pct = safe_float(row.get("orb_pct"))
            stat.total_rebound_pct = safe_float(row.get("trb_pct"))
            stat.free_throw_rate = safe_float(row.get("ft_rate"))
            stat.three_point_rate = safe_float(row.get("fg3a_per_fga_pct"))
            stat.assist_pct = safe_float(row.get("ast_pct"))
            stat.steal_pct = safe_float(row.get("stl_pct"))
            stat.block_pct = safe_float(row.get("blk_pct"))
            updated += 1

        session.commit()
        total_updated += updated
        logger.info("  Updated %d records for %d", updated, season)

    session.close()
    logger.info("Backfill complete: %d total records updated", total_updated)


if __name__ == "__main__":
    backfill()
