"""
Evaluate saved models on the labeled test split.

This is useful for auditing model performance without retraining.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd

from ml_engine.config.ml_config import (
    DATASET_DIR,
    ANOMALY_DETECTOR_MODEL,
    THREAT_CLASSIFIER_MODEL,
    FEATURE_SCALER,
    LABEL_ENCODER,
    ANOMALY_METRICS_FILE,
    CLASSIFIER_METRICS_FILE,
)
from ml_engine.features.feature_extractor import FeatureExtractor
from ml_engine.features.feature_normalizer import FeatureNormalizer
from ml_engine.training.data_splitter import load_splits
from ml_engine.training.train_anomaly_detector import raw_to_unit_interval, _compute_anomaly_metrics
from ml_engine.training.train_threat_classifier import _evaluate_classifier, _filter_supported_labels
from ml_engine.utils.artifacts import utc_now_iso, write_json

logger = logging.getLogger(__name__)


def evaluate_saved_models() -> Dict[str, Any]:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    _, _, test_df = load_splits(DATASET_DIR, prefix="labeled_dataset")

    extractor = FeatureExtractor()
    normalizer = FeatureNormalizer.load(FEATURE_SCALER)

    out: Dict[str, Any] = {"evaluated_at_utc": utc_now_iso()}

    # --- Anomaly ---
    if ANOMALY_DETECTOR_MODEL.exists():
        package = joblib.load(ANOMALY_DETECTOR_MODEL)
        model = package["model"]
        calibration = package.get("calibration", {"q_low": 0.0, "q_high": 1.0})

        feat_df = extractor.extract_features(test_df)
        X, _ = extractor.get_feature_matrix(feat_df)
        X_scaled = normalizer.transform(X)
        raw = (-model.decision_function(X_scaled.to_numpy())).astype(float)
        scores = raw_to_unit_interval(raw, calibration)

        try:
            from ml_engine.config.ml_config import INFERENCE_CONFIG

            threshold = float(INFERENCE_CONFIG.get("anomaly_threshold", 0.5))
        except Exception:
            threshold = 0.5

        anomaly_metrics = _compute_anomaly_metrics(test_df, scores, threshold)
        out["anomaly"] = anomaly_metrics

        # Update metrics file (overwrite with new evaluation time + test metrics)
        try:
            existing = {}
            if ANOMALY_METRICS_FILE.exists():
                from ml_engine.utils.artifacts import read_json

                existing = read_json(ANOMALY_METRICS_FILE)
            existing.setdefault("evaluations", [])
            existing["evaluations"].append({"evaluated_at_utc": out["evaluated_at_utc"], "test": anomaly_metrics})
            write_json(ANOMALY_METRICS_FILE, existing)
        except Exception:
            pass

    # --- Classifier ---
    if THREAT_CLASSIFIER_MODEL.exists() and LABEL_ENCODER.exists():
        test_df_c = _filter_supported_labels(test_df)
        package = joblib.load(THREAT_CLASSIFIER_MODEL)
        model = package["model"]
        le_data = joblib.load(LABEL_ENCODER)
        le = le_data["label_encoder"]
        classes = list(le_data.get("classes", le.classes_))

        feat_df = extractor.extract_features(test_df_c)
        X, _ = extractor.get_feature_matrix(feat_df)
        X_scaled = normalizer.transform(X).to_numpy()
        y_true = le.transform(test_df_c["label"].astype(str).to_numpy())
        y_pred = model.predict(X_scaled)

        classifier_metrics = _evaluate_classifier(y_true, y_pred, classes)
        out["classifier"] = classifier_metrics

        try:
            existing = {}
            if CLASSIFIER_METRICS_FILE.exists():
                from ml_engine.utils.artifacts import read_json

                existing = read_json(CLASSIFIER_METRICS_FILE)
            existing.setdefault("evaluations", [])
            existing["evaluations"].append({"evaluated_at_utc": out["evaluated_at_utc"], "test": classifier_metrics})
            write_json(CLASSIFIER_METRICS_FILE, existing)
        except Exception:
            pass

    return out


if __name__ == "__main__":
    results = evaluate_saved_models()
    print(results)


