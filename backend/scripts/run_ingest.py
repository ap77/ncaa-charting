#!/usr/bin/env python3
"""
CLI script to run the NCAA data ingestion pipeline.

Usage:
    python -m backend.scripts.run_ingest                    # all seasons
    python -m backend.scripts.run_ingest --seasons 2023 2024
    python -m backend.scripts.run_ingest --from-csv         # load from CSV files
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    parser = argparse.ArgumentParser(description="NCAA data ingestion pipeline")
    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        help="Specific seasons to ingest (e.g., 2023 2024)",
    )
    parser.add_argument(
        "--from-csv",
        action="store_true",
        help="Load data from CSV files in data/raw/ instead of scraping",
    )
    args = parser.parse_args()

    if args.from_csv:
        from backend.app.data.csv_loader import load_from_csv

        result = load_from_csv()
    else:
        from backend.app.data.ingest import run_full_ingest

        result = run_full_ingest(seasons=args.seasons)

    print(f"\nIngestion complete: {result}")


if __name__ == "__main__":
    main()
