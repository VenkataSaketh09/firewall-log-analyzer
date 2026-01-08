"""
Predictor Functions
Provides simple APIs for anomaly scoring and threat classification.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple, Union, Optional

import numpy as np
import pandas as pd

from ml_engine.features.feature_extractor import FeatureExtractor
from ml_engine.inference.model_loader import load_models
from ml_engine.training.train_anomaly_detector import raw_to_unit_interval


def _to_dataframe(x: Union[pd.DataFrame, Dict[str, Any], pd.Series]) -> pd.DataFrame:
    if isinstance(x, pd.DataFrame):
        return x
    if isinstance(x, pd.Series):
        return x.to_frame().T
    if isinstance(x, dict):
        return pd.DataFrame([x])
    raise TypeError(f"Unsupported input type: {type(x)}")


def _build_feature_matrix(df_or_features: Union[pd.DataFrame, Dict[str, Any], pd.Series]) -> pd.DataFrame:
    """
    Accepts either:
    - Raw log rows (expects columns like Content/EventId/Component/Month/Date/Time), OR
    - Precomputed feature rows (already numeric feature columns)
    """
    df = _to_dataframe(df_or_features)

    # Heuristic: if it looks like raw logs, extract engineered features.
    raw_cols = {"Content", "EventId", "Component", "Month", "Date", "Time", "EventTemplate"}
    if len(raw_cols.intersection(set(df.columns))) >= 2:
        extractor = FeatureExtractor()
        feat_df = extractor.extract_features(df)
        X, _ = extractor.get_feature_matrix(feat_df)
        return X

    # Otherwise assume it's already a feature matrix
    return df.copy()


def predict_anomaly(
    log_features: Union[pd.DataFrame, Dict[str, Any], pd.Series],
) -> Union[float, np.ndarray]:
    """
    Returns anomaly score(s) in [0, 1].
    """
    models = load_models()
    if models.anomaly_package is None:
        raise FileNotFoundError("Anomaly detector model is not available. Train it first.")

    X = _build_feature_matrix(log_features)
    X_scaled = models.scaler.transform(X)

    model = models.anomaly_package["model"]
    calibration = models.anomaly_package.get("calibration", {"q_low": 0.0, "q_high": 1.0})

    raw = (-model.decision_function(X_scaled.to_numpy())).astype(float)
    scores = raw_to_unit_interval(raw, calibration)

    if scores.shape[0] == 1:
        return float(scores[0])
    return scores


def predict_threat_type(
    log_features: Union[pd.DataFrame, Dict[str, Any], pd.Series],
) -> Union[Tuple[str, float], Tuple[np.ndarray, np.ndarray]]:
    """
    Returns:
    - For single row: (predicted_label, confidence)
    - For multiple rows: (labels, confidences)
    """
    models = load_models()
    if models.classifier_package is None or models.label_encoder_data is None:
        raise FileNotFoundError("Threat classifier model is not available. Train it first.")

    X = _build_feature_matrix(log_features)
    X_scaled = models.scaler.transform(X).to_numpy()

    model = models.classifier_package["model"]
    le = models.label_encoder_data["label_encoder"]
    classes = list(models.label_encoder_data.get("classes", le.classes_))

    proba = model.predict_proba(X_scaled)
    pred_idx = np.argmax(proba, axis=1)
    confidences = np.max(proba, axis=1)
    labels = np.array([classes[i] for i in pred_idx], dtype=object)

    if labels.shape[0] == 1:
        return str(labels[0]), float(confidences[0])
    return labels, confidences


def predict_threat_proba(
    log_features: Union[pd.DataFrame, Dict[str, Any], pd.Series],
) -> Dict[str, float]:
    """
    Convenience helper (single row): returns full probability distribution.
    """
    df = _to_dataframe(log_features)
    if len(df) != 1:
        raise ValueError("predict_threat_proba expects a single row.")

    models = load_models()
    if models.classifier_package is None or models.label_encoder_data is None:
        raise FileNotFoundError("Threat classifier model is not available. Train it first.")

    X = _build_feature_matrix(df)
    X_scaled = models.scaler.transform(X).to_numpy()
    model = models.classifier_package["model"]

    le = models.label_encoder_data["label_encoder"]
    classes = list(models.label_encoder_data.get("classes", le.classes_))
    proba = model.predict_proba(X_scaled)[0]
    return {classes[i]: float(proba[i]) for i in range(len(classes))}


