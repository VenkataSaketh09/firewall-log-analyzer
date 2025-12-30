"""
Model Loader Utilities
Loads trained ML artifacts for inference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

import joblib

from ml_engine.config.ml_config import (
    ANOMALY_DETECTOR_MODEL,
    THREAT_CLASSIFIER_MODEL,
    FEATURE_SCALER,
    LABEL_ENCODER,
)
from ml_engine.features.feature_normalizer import FeatureNormalizer


@dataclass
class LoadedModels:
    scaler: FeatureNormalizer
    anomaly_package: Optional[Dict[str, Any]] = None
    classifier_package: Optional[Dict[str, Any]] = None
    label_encoder_data: Optional[Dict[str, Any]] = None


_CACHE: Optional[LoadedModels] = None


def load_models(force_reload: bool = False) -> LoadedModels:
    global _CACHE
    if _CACHE is not None and not force_reload:
        return _CACHE

    scaler = FeatureNormalizer.load(FEATURE_SCALER)

    anomaly_package = joblib.load(ANOMALY_DETECTOR_MODEL) if ANOMALY_DETECTOR_MODEL.exists() else None
    classifier_package = joblib.load(THREAT_CLASSIFIER_MODEL) if THREAT_CLASSIFIER_MODEL.exists() else None
    label_encoder_data = joblib.load(LABEL_ENCODER) if LABEL_ENCODER.exists() else None

    _CACHE = LoadedModels(
        scaler=scaler,
        anomaly_package=anomaly_package,
        classifier_package=classifier_package,
        label_encoder_data=label_encoder_data,
    )
    return _CACHE


