"""
Phase 11 retraining pipeline (shared by API + auto worker)

- Snapshots current models before retraining
- Runs training
- Snapshots newly trained models and marks active
- Returns version ids + metrics
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple

from app.services.ml_service import ml_service


def run_retrain(train_anomaly: bool, train_classifier: bool, *, run_id: str) -> Dict[str, Any]:
    # Ensure ml_engine imports work in backend context
    ml_service.initialize(force_reload=True)

    from ml_engine.utils.model_versioning import snapshot_current_models

    pre_version = snapshot_current_models(
        reason="pre_retrain_snapshot",
        run_id=run_id,
        extra={"requested": {"train_anomaly": train_anomaly, "train_classifier": train_classifier}},
        mark_active=False,
    )

    results: Dict[str, Any] = {}

    if train_anomaly:
        from ml_engine.training.train_anomaly_detector import train_anomaly_model

        results["anomaly"] = train_anomaly_model(force_refit_scaler=False)

    if train_classifier:
        from ml_engine.training.train_threat_classifier import train_classifier_model

        results["classifier"] = train_classifier_model(force_refit_scaler=False)

    # Reload models after training
    ml_service.initialize(force_reload=True)

    post_version = snapshot_current_models(
        reason="post_retrain_snapshot",
        run_id=run_id,
        extra={"results_summary": {"has_anomaly": bool(train_anomaly), "has_classifier": bool(train_classifier)}},
        mark_active=True,
    )

    return {"pre_version": pre_version, "post_version": post_version, "results": results}


