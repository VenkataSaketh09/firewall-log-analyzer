"""
Train Anomaly Detection Model (Isolation Forest)

- Loads labeled dataset splits (train/val/test)
- Extracts features using FeatureExtractor
- Fits and saves a FeatureNormalizer (scaler)
- Trains IsolationForest on NORMAL-only samples
- Saves model + calibration + metrics + metadata
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import joblib
import numpy as np
import pandas as pd

from ml_engine.config.ml_config import (
    TRAINING_CONFIG,
    DATASET_DIR,
    DATASET_CSV,
    ANOMALY_DETECTOR_MODEL,
    FEATURE_SCALER,
    ANOMALY_METRICS_FILE,
    MODEL_METADATA_FILE,
)
from ml_engine.features.feature_extractor import FeatureExtractor
from ml_engine.features.feature_normalizer import FeatureNormalizer
from ml_engine.training.data_splitter import load_splits
from ml_engine.training.prepare_data import prepare_complete_dataset
from ml_engine.utils.artifacts import utc_now_iso, write_json, sha256_file, safe_relpath

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.metrics import roc_auc_score
except Exception:  # pragma: no cover
    IsolationForest = None
    roc_auc_score = None

logger = logging.getLogger(__name__)


def _load_or_prepare_labeled_splits() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    try:
        return load_splits(DATASET_DIR, prefix="labeled_dataset")
    except Exception:
        logger.info("Labeled splits not found; running prepare_data pipeline to generate them.")
        train_df, val_df, test_df, _ = prepare_complete_dataset(save_splits_to_disk=True, stratify=True)
        return train_df, val_df, test_df


def _fit_or_load_scaler(X_train: pd.DataFrame, force_refit: bool = False) -> FeatureNormalizer:
    scaler_type = TRAINING_CONFIG.get("feature_engineering", {}).get("scaler_type", "standard")
    if FEATURE_SCALER.exists() and not force_refit:
        logger.info(f"Loading existing scaler: {FEATURE_SCALER}")
        return FeatureNormalizer.load(FEATURE_SCALER)

    logger.info(f"Fitting scaler ({scaler_type}) on training features and saving to: {FEATURE_SCALER}")
    normalizer = FeatureNormalizer(scaler_type=scaler_type)
    normalizer.fit(X_train)
    normalizer.save(FEATURE_SCALER)
    return normalizer


def _calibrate_scores(raw_scores: np.ndarray) -> Dict[str, float]:
    """
    Calibration to map raw anomaly scores into [0, 1].
    Uses robust quantiles to avoid a few extreme values dominating scaling.
    """
    q_low = float(np.quantile(raw_scores, 0.01))
    q_high = float(np.quantile(raw_scores, 0.99))
    if q_high <= q_low:
        q_high = q_low + 1e-9
    return {"q_low": q_low, "q_high": q_high}


def raw_to_unit_interval(raw_scores: np.ndarray, calibration: Dict[str, float]) -> np.ndarray:
    q_low = calibration["q_low"]
    q_high = calibration["q_high"]
    scaled = (raw_scores - q_low) / (q_high - q_low)
    return np.clip(scaled, 0.0, 1.0)


def _compute_anomaly_metrics(
    df: pd.DataFrame,
    anomaly_scores: np.ndarray,
    threshold: float,
) -> Dict[str, Any]:
    # Binary ground truth: NORMAL=0, anything else=1
    y_true = (df["label"].astype(str) != "NORMAL").astype(int).to_numpy()
    y_pred = (anomaly_scores >= threshold).astype(int)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else 0.0

    auc = None
    if roc_auc_score is not None:
        try:
            auc = float(roc_auc_score(y_true, anomaly_scores))
        except Exception:
            auc = None

    # Per-class average anomaly score for sanity
    score_by_label = (
        pd.DataFrame({"label": df["label"].astype(str), "score": anomaly_scores})
        .groupby("label")["score"]
        .agg(["mean", "median", "min", "max", "count"])
        .to_dict(orient="index")
    )

    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "roc_auc": auc,
        "score_by_label": score_by_label,
    }


def train_anomaly_model(force_refit_scaler: bool = False) -> Dict[str, Any]:
    if IsolationForest is None:
        raise ImportError("scikit-learn is required to train IsolationForest")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    train_df, val_df, test_df = _load_or_prepare_labeled_splits()

    extractor = FeatureExtractor()
    train_features_df = extractor.extract_features(train_df)
    X_train, feature_names = extractor.get_feature_matrix(train_features_df)

    normalizer = _fit_or_load_scaler(X_train, force_refit=force_refit_scaler)
    X_train_scaled = normalizer.transform(X_train)

    # Train on NORMAL-only baseline
    train_is_normal = train_df["label"].astype(str) == "NORMAL"
    X_normal = X_train_scaled.loc[train_is_normal.values]
    if len(X_normal) == 0:
        raise ValueError("No NORMAL samples found in training data; cannot train anomaly detector.")

    if_config = TRAINING_CONFIG.get("anomaly_detector", {})
    model = IsolationForest(**if_config)
    logger.info(f"Training IsolationForest on {len(X_normal)} NORMAL samples, {X_normal.shape[1]} features")
    model.fit(X_normal.to_numpy())

    # Calibration on training NORMAL scores
    raw_scores_normal = (-model.decision_function(X_normal.to_numpy())).astype(float)
    calibration = _calibrate_scores(raw_scores_normal)

    # Evaluate on val/test
    threshold = float(TRAINING_CONFIG.get("inference_threshold", 0.5))  # fallback
    try:
        from ml_engine.config.ml_config import INFERENCE_CONFIG
        threshold = float(INFERENCE_CONFIG.get("anomaly_threshold", threshold))
    except Exception:
        pass

    def score_df(df: pd.DataFrame) -> np.ndarray:
        feat_df = extractor.extract_features(df)
        X, _ = extractor.get_feature_matrix(feat_df)
        X_scaled = normalizer.transform(X)
        raw = (-model.decision_function(X_scaled.to_numpy())).astype(float)
        return raw_to_unit_interval(raw, calibration)

    val_scores = score_df(val_df)
    test_scores = score_df(test_df)

    metrics = {
        "trained_at_utc": utc_now_iso(),
        "dataset": {
            "structured_csv": safe_relpath(DATASET_CSV, base=Path(__file__).resolve().parent.parent),
            "sha256": sha256_file(DATASET_CSV) if Path(DATASET_CSV).exists() else None,
        },
        "splits": {"train": int(len(train_df)), "validation": int(len(val_df)), "test": int(len(test_df))},
        "features": {"count": int(len(feature_names)), "names": list(feature_names)},
        "model": {"type": "IsolationForest", "params": if_config},
        "calibration": calibration,
        "validation": _compute_anomaly_metrics(val_df, val_scores, threshold),
        "test": _compute_anomaly_metrics(test_df, test_scores, threshold),
    }

    # Persist model package
    ANOMALY_DETECTOR_MODEL.parent.mkdir(parents=True, exist_ok=True)
    package = {
        "model": model,
        "feature_names": list(feature_names),
        "scaler_path": str(FEATURE_SCALER),
        "calibration": calibration,
        "trained_at_utc": metrics["trained_at_utc"],
        "params": if_config,
    }
    joblib.dump(package, ANOMALY_DETECTOR_MODEL)
    write_json(ANOMALY_METRICS_FILE, metrics)

    # Update global metadata file (append-ish)
    metadata = {}
    if MODEL_METADATA_FILE.exists():
        try:
            from ml_engine.utils.artifacts import read_json

            metadata = read_json(MODEL_METADATA_FILE)
        except Exception:
            metadata = {}

    metadata.setdefault("models", {})
    metadata["models"]["anomaly_detector"] = {
        "path": str(ANOMALY_DETECTOR_MODEL),
        "metrics_path": str(ANOMALY_METRICS_FILE),
        "trained_at_utc": metrics["trained_at_utc"],
        "feature_count": int(len(feature_names)),
    }
    write_json(MODEL_METADATA_FILE, metadata)

    logger.info(f"Saved anomaly detector model: {ANOMALY_DETECTOR_MODEL}")
    logger.info(f"Saved anomaly metrics: {ANOMALY_METRICS_FILE}")
    return metrics


if __name__ == "__main__":
    train_anomaly_model()


