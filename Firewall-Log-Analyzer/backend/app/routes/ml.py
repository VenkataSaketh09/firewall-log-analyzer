from __future__ import annotations

from datetime import datetime
from typing import Optional, Any, Dict

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel, Field

from app.services.ml_service import ml_service
from app.services.ml_storage import start_training_run, finish_training_run

router = APIRouter(prefix="/api/ml", tags=["ml"])


class ManualPredictRequest(BaseModel):
    raw_log: str = Field(..., description="Raw log line")
    timestamp: Optional[datetime] = Field(None, description="Optional timestamp (defaults to now)")
    log_source: Optional[str] = Field(None, description="Optional log source hint, e.g. auth.log / ufw.log")
    event_type: Optional[str] = Field(None, description="Optional event type hint, e.g. SSH_FAILED_LOGIN")
    threat_type_hint: Optional[str] = Field(None, description="Optional rule-based label hint (BRUTE_FORCE/DDOS/PORT_SCAN)")
    severity_hint: Optional[str] = Field(None, description="Optional severity hint (CRITICAL/HIGH/MEDIUM/LOW)")


class RetrainRequest(BaseModel):
    train_anomaly: bool = Field(True, description="Retrain anomaly detector")
    train_classifier: bool = Field(True, description="Retrain threat classifier")


_LAST_RETRAIN: Dict[str, Any] = {"status": "never", "started_at": None, "finished_at": None, "error": None}


def _run_retrain(train_anomaly: bool, train_classifier: bool) -> None:
    global _LAST_RETRAIN
    requested = {"train_anomaly": train_anomaly, "train_classifier": train_classifier}
    run_id = start_training_run(requested)
    _LAST_RETRAIN = {"status": "running", "started_at": datetime.utcnow().isoformat(), "finished_at": None, "error": None, "run_id": run_id}
    try:
        # Ensure ml_engine imports work in backend context
        ml_service.initialize(force_reload=True)

        results: Dict[str, Any] = {}

        if train_anomaly:
            from ml_engine.training.train_anomaly_detector import train_anomaly_model

            results["anomaly"] = train_anomaly_model(force_refit_scaler=False)

        if train_classifier:
            from ml_engine.training.train_threat_classifier import train_classifier_model

            results["classifier"] = train_classifier_model(force_refit_scaler=False)

        # Reload models after training
        ml_service.initialize(force_reload=True)

        _LAST_RETRAIN["status"] = "completed"
        _LAST_RETRAIN["finished_at"] = datetime.utcnow().isoformat()
        finish_training_run(run_id, status="completed", results={"results": results})
    except Exception as e:
        _LAST_RETRAIN["status"] = "failed"
        _LAST_RETRAIN["finished_at"] = datetime.utcnow().isoformat()
        _LAST_RETRAIN["error"] = str(e)
        finish_training_run(run_id, status="failed", error=str(e))


@router.get("/status")
def ml_status():
    return {"ml": ml_service.status(), "retrain": _LAST_RETRAIN}


@router.post("/predict")
def manual_predict(body: ManualPredictRequest = Body(...)):
    result = ml_service.score(
        threat_type_hint=body.threat_type_hint,
        severity_hint=body.severity_hint,
        timestamp=body.timestamp,
        log_source=body.log_source,
        event_type=body.event_type,
        raw_log=body.raw_log,
    )
    return {
        "ml_enabled": result.ml_enabled,
        "ml_available": result.ml_available,
        "anomaly_score": result.anomaly_score,
        "predicted_label": result.predicted_label,
        "confidence": result.confidence,
        "risk_score": result.risk_score,
        "reasoning": result.reasoning or [],
        "error": result.error,
    }


@router.get("/metrics")
def ml_metrics():
    try:
        ml_service.initialize()
        from ml_engine.config.ml_config import ANOMALY_METRICS_FILE, CLASSIFIER_METRICS_FILE, MODEL_METADATA_FILE
        from ml_engine.utils.artifacts import read_json

        out: Dict[str, Any] = {}
        if MODEL_METADATA_FILE.exists():
            out["metadata"] = read_json(MODEL_METADATA_FILE)
        if ANOMALY_METRICS_FILE.exists():
            out["anomaly"] = read_json(ANOMALY_METRICS_FILE)
        if CLASSIFIER_METRICS_FILE.exists():
            out["classifier"] = read_json(CLASSIFIER_METRICS_FILE)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading ML metrics: {str(e)}")


@router.post("/retrain")
def retrain_models(body: RetrainRequest = Body(...), background: BackgroundTasks = None):
    if background is None:
        raise HTTPException(status_code=500, detail="Background task system not available")

    background.add_task(_run_retrain, body.train_anomaly, body.train_classifier)
    return {"status": "scheduled", "requested": body.model_dump(), "retrain": _LAST_RETRAIN}


