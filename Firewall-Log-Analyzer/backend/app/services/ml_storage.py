"""
Phase 7: ML persistence helpers

- Store ML predictions
- Track training history
- Cache feature computations
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.db.mongo import (
    ml_predictions_collection,
    ml_training_history_collection,
    ml_features_cache_collection,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def make_cache_key(payload: Dict[str, Any]) -> str:
    """
    Deterministic cache key for a dict payload.
    """
    s = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


def cache_get_features(cache_key: str) -> Optional[Dict[str, Any]]:
    doc = ml_features_cache_collection.find_one({"cache_key": cache_key})
    if not doc:
        return None
    features = doc.get("features")
    if isinstance(features, dict):
        return features
    return None


def cache_set_features(cache_key: str, features: Dict[str, Any]) -> None:
    now = _utcnow()
    ml_features_cache_collection.update_one(
        {"cache_key": cache_key},
        {"$set": {"cache_key": cache_key, "features": features, "created_at": now}},
        upsert=True,
    )


def store_prediction(doc: Dict[str, Any]) -> None:
    """
    Insert one ML prediction record.
    """
    now = _utcnow()
    payload = {"created_at": now, **doc}
    ml_predictions_collection.insert_one(payload)


def start_training_run(requested: Dict[str, Any]) -> str:
    now = _utcnow()
    doc = {
        "started_at": now,
        "finished_at": None,
        "status": "running",
        "requested": requested,
        "error": None,
        "results": None,
    }
    res = ml_training_history_collection.insert_one(doc)
    return str(res.inserted_id)


def finish_training_run(run_id: str, *, status: str, results: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
    now = _utcnow()
    ml_training_history_collection.update_one(
        {"_id": _to_object_id(run_id)},
        {"$set": {"finished_at": now, "status": status, "results": results, "error": error}},
    )


def _to_object_id(raw: str):
    from bson import ObjectId

    return ObjectId(raw)


