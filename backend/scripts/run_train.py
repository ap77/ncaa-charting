#!/usr/bin/env python3
"""
Train the NCAA bracket prediction models.

Usage:
    python -m backend.scripts.run_train              # train both modes
    python -m backend.scripts.run_train --mode safe   # train Safe Jen only
    python -m backend.scripts.run_train --mode spicy  # train Spicy Jen only
"""

import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def print_results(metadata, label):
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"  Test accuracy:  {metadata['test_accuracy']:.1%}")
    print(f"  Test AUC:       {metadata['test_auc']:.4f}")
    print(f"  Test log-loss:  {metadata['test_logloss']:.4f}")
    print(f"  Train size:     {metadata['train_size']} matchups")
    print(f"  Test size:      {metadata['test_size']} matchups")

    print("\n  Per-round accuracy:")
    for rname, info in metadata["round_accuracy"].items():
        print(f"    {rname:15s} {info['accuracy']:.1%}  ({info['n_games']} games)")

    print("\n  Top 10 features (SHAP):")
    for i, (feat, imp) in enumerate(list(metadata["feature_importance_shap"].items())[:10]):
        print(f"    {i+1:2d}. {feat:40s} {imp:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Train bracket prediction models")
    parser.add_argument(
        "--mode",
        choices=["safe", "spicy", "both"],
        default="both",
        help="Which model to train (default: both)",
    )
    parser.add_argument(
        "--test-seasons",
        nargs="+",
        type=int,
        default=[2024, 2025],
    )
    args = parser.parse_args()

    if args.mode == "both":
        from backend.app.models.trainer import train_both

        results = train_both(test_seasons=args.test_seasons)
        print_results(results["safe"], "SAFE JEN (trusts the committee)")
        print_results(results["spicy"], "SPICY JEN (pure basketball)")
    else:
        from backend.app.models.trainer import train_model

        metadata = train_model(test_seasons=args.test_seasons, mode=args.mode)
        label = "SAFE JEN" if args.mode == "safe" else "SPICY JEN"
        print_results(metadata, label)


if __name__ == "__main__":
    main()
