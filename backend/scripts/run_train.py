#!/usr/bin/env python3
"""
Train the NCAA bracket prediction model.

Usage:
    python -m backend.scripts.run_train
    python -m backend.scripts.run_train --test-seasons 2024 2025
"""

import argparse
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    parser = argparse.ArgumentParser(description="Train bracket prediction model")
    parser.add_argument(
        "--test-seasons",
        nargs="+",
        type=int,
        default=[2024, 2025],
        help="Seasons to hold out for testing (default: 2024 2025)",
    )
    args = parser.parse_args()

    from backend.app.models.trainer import train_model

    metadata = train_model(test_seasons=args.test_seasons)

    print("\n" + "=" * 60)
    print("MODEL TRAINING COMPLETE")
    print("=" * 60)
    print(f"Test accuracy:  {metadata['test_accuracy']:.1%}")
    print(f"Test AUC:       {metadata['test_auc']:.4f}")
    print(f"Test log-loss:  {metadata['test_logloss']:.4f}")
    print(f"Train size:     {metadata['train_size']} matchups")
    print(f"Test size:      {metadata['test_size']} matchups")

    print("\nPer-round accuracy:")
    for rname, info in metadata["round_accuracy"].items():
        print(f"  {rname:15s} {info['accuracy']:.1%}  ({info['n_games']} games)")

    print("\nTop 10 features (SHAP):")
    for i, (feat, imp) in enumerate(list(metadata["feature_importance_shap"].items())[:10]):
        print(f"  {i+1:2d}. {feat:40s} {imp:.4f}")


if __name__ == "__main__":
    main()
