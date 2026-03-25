"""Normalize team names across different data sources."""

import re

# Common abbreviations and alternate names → canonical name
ALIASES = {
    "uconn": "connecticut",
    "u conn": "connecticut",
    "unc": "north carolina",
    "nc state": "north carolina state",
    "ncst": "north carolina state",
    "vcu": "virginia commonwealth",
    "lsu": "louisiana state",
    "smu": "southern methodist",
    "tcu": "texas christian",
    "ucf": "central florida",
    "usc": "southern california",
    "ucla": "ucla",
    "unlv": "nevada-las vegas",
    "utep": "texas-el paso",
    "ole miss": "mississippi",
    "pitt": "pittsburgh",
    "st. john's": "st johns",
    "saint john's": "st johns",
    "saint mary's": "saint marys",
    "st. mary's": "saint marys",
    "saint joseph's": "saint josephs",
    "st. joseph's": "saint josephs",
    "byu": "brigham young",
    "etsu": "east tennessee state",
    "mtsu": "middle tennessee",
    "fau": "florida atlantic",
    "fiu": "florida international",
    "umbc": "maryland-baltimore county",
    "ualr": "arkansas-little rock",
    "uta": "texas-arlington",
    "utsa": "texas-san antonio",
    "siue": "southern illinois-edwardsville",
    "siu edwardsville": "southern illinois-edwardsville",
    "siu-edwardsville": "southern illinois-edwardsville",
    "siu": "southern illinois",
}


def normalize_team_name(name: str) -> str:
    """Normalize a team name for consistent matching across data sources."""
    name = name.strip()
    # Sports Reference appends "NCAA" to tournament team names in stats tables
    if name.endswith("NCAA"):
        name = name[:-4].rstrip()
    name = name.lower()
    # Remove common suffixes
    name = re.sub(r"\s*(university|univ\.?|college|coll\.?)$", "", name)
    # Remove parenthetical state abbreviations
    name = re.sub(r"\s*\([a-z]{2}\)$", "", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name)
    # Remove periods
    name = name.replace(".", "")
    # Check alias table
    if name in ALIASES:
        name = ALIASES[name]
    return name
