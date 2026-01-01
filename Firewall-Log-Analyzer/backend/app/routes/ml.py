from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Any, Dict

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel, Field

from app.services.ml_service import ml_service
from app.services.ml_storage import start_training_run, finish_training_run
from app.services.ml_retrain_pipeline import run_retrain

router = APIRouter(prefix="/api/ml", tags=["ml"])


class ManualPredictRequest(BaseModel):
    raw_log: str = Field(..., description="Raw log line")
    timestamp: Optional[datetime] = Field(None, description="Optional timestamp (defaults to now)")
    log_source: Optional[str] = Field(None, description="Optional log source hint, e.g. auth.log / ufw.log")
    event_type: Optional[str] = Field(None, description="Optional event type hint, e.g. SSH_FAILED_LOGIN")
    threat_type_hint: Optional[str] = Field(None, description="Optional rule-based label hint (BRUTE_FORCE/DDOS/PORT_SCAN)")
    severity_hint: Optional[str] = Field(None, description="Optional severity hint (CRITICAL/HIGH/MEDIUM/LOW)")
    source_ip: Optional[str] = Field(None, description="Optional source IP address")


class RetrainRequest(BaseModel):
    train_anomaly: bool = Field(True, description="Retrain anomaly detector")
    train_classifier: bool = Field(True, description="Retrain threat classifier")


_LAST_RETRAIN: Dict[str, Any] = {"status": "never", "started_at": None, "finished_at": None, "error": None}


def _run_retrain(train_anomaly: bool, train_classifier: bool) -> None:
    global _LAST_RETRAIN
    requested = {"train_anomaly": train_anomaly, "train_classifier": train_classifier}
    run_id = start_training_run(requested)
    _LAST_RETRAIN = {"status": "running", "started_at": datetime.now(timezone.utc).isoformat(), "finished_at": None, "error": None, "run_id": run_id}
    try:
        payload = run_retrain(train_anomaly, train_classifier, run_id=run_id)
        _LAST_RETRAIN["status"] = "completed"
        _LAST_RETRAIN["finished_at"] = datetime.now(timezone.utc).isoformat()
        _LAST_RETRAIN["versions"] = {"pre": payload.get("pre_version"), "post": payload.get("post_version")}
        finish_training_run(run_id, status="completed", results=payload)
    except Exception as e:
        _LAST_RETRAIN["status"] = "failed"
        _LAST_RETRAIN["finished_at"] = datetime.now(timezone.utc).isoformat()
        _LAST_RETRAIN["error"] = str(e)
        finish_training_run(run_id, status="failed", error=str(e))


@router.get("/status")
def ml_status():
    return {"ml": ml_service.status(), "retrain": _LAST_RETRAIN}


@router.post("/predict")
def manual_predict(body: ManualPredictRequest = Body(...)):
    result = ml_service.score(
        source_ip=body.source_ip,
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


@router.get("/versions")
def list_model_versions(limit: int = 50):
    try:
        ml_service.initialize()
        from ml_engine.utils.model_versioning import list_versions, get_active_version

        return {"active_version": get_active_version(), "versions": list_versions(limit=limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing model versions: {str(e)}")


class RollbackRequest(BaseModel):
    version_id: str = Field(..., description="Version id folder name under ml_engine/models/versions/")


@router.post("/rollback")
def rollback_models(body: RollbackRequest = Body(...)):
    try:
        ml_service.initialize()
        from ml_engine.utils.model_versioning import rollback_to_version, get_active_version

        rollback_to_version(body.version_id)
        ml_service.initialize(force_reload=True)
        return {"status": "rolled_back", "active_version": get_active_version()}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


