"""
Train gradient boosting model on historical NCAA tournament matchup data.

Pipeline:
1. Build training dataset from DB (delta features per matchup)
2. Train/evaluate with time-based cross-validation (train on past seasons, test on future)
3. Compute SHAP values for explainability
4. Save model + metadata
"""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

from backend.app.data.features import build_training_dataset, get_feature_names

logger = logging.getLogger(__name__)

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "bracket_predictor.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"
SHAP_PATH = MODEL_DIR / "shap_explainer.joblib"


def train_model(test_seasons: list[int] = None) -> dict:
    """
    Train the bracket prediction model.

    Uses leave-future-out cross-validation: for each fold, train on all
    seasons before the test season(s) and evaluate on the held-out season.

    Args:
        test_seasons: Seasons to hold out for final evaluation.
                      Defaults to [2024, 2025].

    Returns:
        Dict with training metrics and feature importances.
    """
    if test_seasons is None:
        test_seasons = [2024, 2025]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Build dataset
    logger.info("Building training dataset...")
    df = build_training_dataset()
    feature_cols = get_feature_names()

    if df.empty:
        raise ValueError("No training data found. Run ingestion first.")

    logger.info("Dataset: %d matchups, %d features, seasons %d-%d",
                len(df), len(feature_cols), df["season"].min(), df["season"].max())

    # Split: train on historical, test on recent seasons
    train_df = df[~df["season"].isin(test_seasons)].copy()
    test_df = df[df["season"].isin(test_seasons)].copy()

    X_train = train_df[feature_cols].values
    y_train = train_df["label"].values
    X_test = test_df[feature_cols].values
    y_test = test_df["label"].values

    logger.info("Train: %d matchups (%d-%d), Test: %d matchups (%s)",
                len(train_df), train_df["season"].min(), train_df["season"].max(),
                len(test_df), test_seasons)

    # --- Time-based cross-validation on training set ---
    cv_results = _time_based_cv(train_df, feature_cols)

    # --- Train final model on all training data ---
    model = GradientBoostingClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        max_features=0.8,
        min_samples_leaf=5,
        random_state=42,
    )

    model.fit(X_train, y_train)

    # --- Evaluate on held-out test set ---
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    test_accuracy = accuracy_score(y_test, y_pred)
    test_logloss = log_loss(y_test, y_pred_proba)
    test_auc = roc_auc_score(y_test, y_pred_proba)

    logger.info("Test accuracy: %.3f, AUC: %.3f, LogLoss: %.3f",
                test_accuracy, test_auc, test_logloss)

    # --- Per-round accuracy on test set ---
    round_acc = _per_round_accuracy(test_df, y_pred)

    # --- Feature importance (gain-based) ---
    importance = dict(zip(feature_cols, model.feature_importances_))
    importance_sorted = sorted(importance.items(), key=lambda x: x[1], reverse=True)

    logger.info("Top 10 features by importance:")
    for feat, imp in importance_sorted[:10]:
        logger.info("  %s: %.4f", feat, imp)

    # --- SHAP explainer ---
    logger.info("Computing SHAP explainer...")
    explainer = shap.TreeExplainer(model)
    # Compute SHAP values on test set for validation
    shap_values = explainer.shap_values(X_test)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    shap_importance = dict(zip(feature_cols, mean_abs_shap))
    shap_sorted = sorted(shap_importance.items(), key=lambda x: x[1], reverse=True)

    logger.info("Top 10 features by SHAP importance:")
    for feat, imp in shap_sorted[:10]:
        logger.info("  %s: %.4f", feat, imp)

    # --- Save model and metadata ---
    joblib.dump(model, MODEL_PATH)
    joblib.dump(explainer, SHAP_PATH)
    logger.info("Model saved to %s", MODEL_PATH)

    metadata = {
        "feature_columns": feature_cols,
        "test_seasons": test_seasons,
        "train_size": len(train_df),
        "test_size": len(test_df),
        "test_accuracy": round(test_accuracy, 4),
        "test_auc": round(test_auc, 4),
        "test_logloss": round(test_logloss, 4),
        "cv_results": cv_results,
        "round_accuracy": round_acc,
        "feature_importance_gain": {k: round(float(v), 4) for k, v in importance_sorted},
        "feature_importance_shap": {k: round(float(v), 4) for k, v in shap_sorted},
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def _time_based_cv(train_df: pd.DataFrame, feature_cols: list[str]) -> list[dict]:
    """
    Time-based cross-validation: for each season in training data,
    train on all prior seasons and test on that season.
    Only uses seasons with enough prior data (at least 3 seasons of training).
    """
    seasons = sorted(train_df["season"].unique())
    results = []

    for i, test_season in enumerate(seasons):
        if i < 3:  # Need at least 3 seasons to train
            continue

        fold_train = train_df[train_df["season"] < test_season]
        fold_test = train_df[train_df["season"] == test_season]

        if len(fold_test) == 0:
            continue

        X_tr = fold_train[feature_cols].values
        y_tr = fold_train["label"].values
        X_te = fold_test[feature_cols].values
        y_te = fold_test["label"].values

        model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            max_features=0.8,
            min_samples_leaf=5,
            random_state=42,
        )
        model.fit(X_tr, y_tr)

        y_pred_proba = model.predict_proba(X_te)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)

        acc = accuracy_score(y_te, y_pred)
        results.append({
            "test_season": int(test_season),
            "train_seasons": int(i),
            "n_test": int(len(fold_test)),
            "accuracy": round(acc, 4),
        })
        logger.info("  CV fold %d (test=%d): accuracy=%.3f (%d games)",
                     i, test_season, acc, len(fold_test))

    avg_acc = np.mean([r["accuracy"] for r in results]) if results else 0
    logger.info("CV average accuracy: %.3f across %d folds", avg_acc, len(results))
    return results


def _per_round_accuracy(test_df: pd.DataFrame, y_pred: np.ndarray) -> dict:
    """Compute accuracy broken down by tournament round."""
    round_names = {1: "R64", 2: "R32", 3: "S16", 4: "E8", 5: "F4", 6: "Championship"}
    result = {}

    for rnum, rname in round_names.items():
        mask = test_df["round_number"].values == rnum
        if mask.sum() == 0:
            continue
        acc = accuracy_score(test_df["label"].values[mask], y_pred[mask])
        result[rname] = {
            "accuracy": round(acc, 4),
            "n_games": int(mask.sum()),
        }
        logger.info("  %s: %.3f (%d games)", rname, acc, mask.sum())

    return result
