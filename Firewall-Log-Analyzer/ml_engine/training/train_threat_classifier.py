"""
Train Threat Classification Model (Random Forest)

- Loads labeled dataset splits (train/val/test)
- Extracts features using FeatureExtractor
- Fits/loads FeatureNormalizer (scaler) for consistent inference
- Trains RandomForestClassifier on labels: NORMAL, BRUTE_FORCE, SUSPICIOUS
- Saves model + label encoder + metrics + metadata
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd

from ml_engine.config.ml_config import (
    TRAINING_CONFIG,
    DATASET_DIR,
    DATASET_CSV,
    THREAT_CLASSIFIER_MODEL,
    FEATURE_SCALER,
    LABEL_ENCODER,
    CLASSIFIER_METRICS_FILE,
    MODEL_METADATA_FILE,
)
from ml_engine.features.feature_extractor import FeatureExtractor
from ml_engine.features.feature_normalizer import FeatureNormalizer
from ml_engine.training.data_splitter import load_splits
from ml_engine.training.prepare_data import prepare_complete_dataset
from ml_engine.utils.artifacts import utc_now_iso, write_json, sha256_file, safe_relpath

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        accuracy_score,
        precision_recall_fscore_support,
        confusion_matrix,
        classification_report,
    )
    from sklearn.preprocessing import LabelEncoder
except Exception:  # pragma: no cover
    RandomForestClassifier = None
    accuracy_score = None
    precision_recall_fscore_support = None
    confusion_matrix = None
    classification_report = None
    LabelEncoder = None

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


def _filter_supported_labels(df: pd.DataFrame) -> pd.DataFrame:
    supported = {"NORMAL", "BRUTE_FORCE", "SUSPICIOUS"}
    df = df.copy()
    df["label"] = df["label"].astype(str)
    return df[df["label"].isin(supported)].copy()


def _evaluate_classifier(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: list[str],
) -> Dict[str, Any]:
    acc = float(accuracy_score(y_true, y_pred))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(labels))), zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(labels)))).tolist()
    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(labels))),
        target_names=labels,
        zero_division=0,
        output_dict=True,
    )
    return {
        "accuracy": acc,
        "per_class": {
            labels[i]: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i in range(len(labels))
        },
        "macro_avg": {
            "precision": float(np.mean(precision)),
            "recall": float(np.mean(recall)),
            "f1": float(np.mean(f1)),
        },
        "confusion_matrix": cm,
        "classification_report": report,
    }


def train_classifier_model(force_refit_scaler: bool = False) -> Dict[str, Any]:
    if RandomForestClassifier is None or LabelEncoder is None:
        raise ImportError("scikit-learn is required to train RandomForestClassifier")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    train_df, val_df, test_df = _load_or_prepare_labeled_splits()
    train_df = _filter_supported_labels(train_df)
    val_df = _filter_supported_labels(val_df)
    test_df = _filter_supported_labels(test_df)

    extractor = FeatureExtractor()
    train_features_df = extractor.extract_features(train_df)
    X_train, feature_names = extractor.get_feature_matrix(train_features_df)

    normalizer = _fit_or_load_scaler(X_train, force_refit=force_refit_scaler)
    X_train_scaled = normalizer.transform(X_train)

    # Labels
    le = LabelEncoder()
    y_train = le.fit_transform(train_df["label"].astype(str))
    label_classes = list(le.classes_)

    # Optional resampling (imbalanced-learn)
    X_train_np = X_train_scaled.to_numpy()
    y_train_np = y_train
    resampling_used = None
    try:
        if TRAINING_CONFIG.get("threat_classifier_resampling", None) == "random_over":
            from imblearn.over_sampling import RandomOverSampler

            ros = RandomOverSampler(random_state=TRAINING_CONFIG.get("random_seed", 42))
            X_train_np, y_train_np = ros.fit_resample(X_train_np, y_train_np)
            resampling_used = "RandomOverSampler"
    except Exception:
        resampling_used = None

    rf_config = TRAINING_CONFIG.get("threat_classifier", {})
    model = RandomForestClassifier(**rf_config)
    logger.info(
        f"Training RandomForestClassifier on {X_train_np.shape[0]} samples, {X_train_np.shape[1]} features "
        f"(classes={label_classes})"
    )
    model.fit(X_train_np, y_train_np)

    # Save label encoder
    LABEL_ENCODER.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"label_encoder": le, "classes": label_classes}, LABEL_ENCODER)

    # Evaluate on val/test
    def predict_df(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        feat_df = extractor.extract_features(df)
        X, _ = extractor.get_feature_matrix(feat_df)
        X_scaled = normalizer.transform(X).to_numpy()
        y_true = le.transform(df["label"].astype(str).to_numpy())
        y_pred = model.predict(X_scaled)
        return y_true, y_pred

    y_val_true, y_val_pred = predict_df(val_df)
    y_test_true, y_test_pred = predict_df(test_df)

    # Feature importance
    importances = None
    try:
        importances = (
            pd.DataFrame({"feature": feature_names, "importance": model.feature_importances_})
            .sort_values("importance", ascending=False)
            .head(50)
            .to_dict(orient="records")
        )
    except Exception:
        importances = None

    metrics = {
        "trained_at_utc": utc_now_iso(),
        "dataset": {
            "structured_csv": safe_relpath(DATASET_CSV, base=Path(__file__).resolve().parent.parent),
            "sha256": sha256_file(DATASET_CSV) if Path(DATASET_CSV).exists() else None,
        },
        "splits": {"train": int(len(train_df)), "validation": int(len(val_df)), "test": int(len(test_df))},
        "features": {"count": int(len(feature_names)), "names": list(feature_names)},
        "model": {"type": "RandomForestClassifier", "params": rf_config},
        "label_encoder": {"classes": label_classes, "path": str(LABEL_ENCODER)},
        "resampling": resampling_used,
        "validation": _evaluate_classifier(y_val_true, y_val_pred, label_classes),
        "test": _evaluate_classifier(y_test_true, y_test_pred, label_classes),
        "feature_importance_top50": importances,
    }

    # Persist model package
    THREAT_CLASSIFIER_MODEL.parent.mkdir(parents=True, exist_ok=True)
    package = {
        "model": model,
        "feature_names": list(feature_names),
        "scaler_path": str(FEATURE_SCALER),
        "label_encoder_path": str(LABEL_ENCODER),
        "trained_at_utc": metrics["trained_at_utc"],
        "params": rf_config,
    }
    joblib.dump(package, THREAT_CLASSIFIER_MODEL)
    write_json(CLASSIFIER_METRICS_FILE, metrics)

    # Update global metadata file
    metadata: Dict[str, Any] = {}
    if MODEL_METADATA_FILE.exists():
        try:
            from ml_engine.utils.artifacts import read_json

            metadata = read_json(MODEL_METADATA_FILE)
        except Exception:
            metadata = {}

    metadata.setdefault("models", {})
    metadata["models"]["threat_classifier"] = {
        "path": str(THREAT_CLASSIFIER_MODEL),
        "metrics_path": str(CLASSIFIER_METRICS_FILE),
        "trained_at_utc": metrics["trained_at_utc"],
        "feature_count": int(len(feature_names)),
        "classes": label_classes,
    }
    write_json(MODEL_METADATA_FILE, metadata)

    logger.info(f"Saved threat classifier model: {THREAT_CLASSIFIER_MODEL}")
    logger.info(f"Saved classifier metrics: {CLASSIFIER_METRICS_FILE}")
    return metrics


if __name__ == "__main__":
    train_classifier_model()


