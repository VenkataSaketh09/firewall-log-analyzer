"""
Phase 11: Model versioning utilities

Creates versioned snapshots of model artifacts, supports listing versions and rollback.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ml_engine.config.ml_config import (
    MODELS_DIR,
    MODEL_VERSIONS_DIR,
    ACTIVE_VERSION_FILE,
    ANOMALY_DETECTOR_MODEL,
    THREAT_CLASSIFIER_MODEL,
    FEATURE_SCALER,
    LABEL_ENCODER,
    ANOMALY_METRICS_FILE,
    CLASSIFIER_METRICS_FILE,
    MODEL_METADATA_FILE,
)
from ml_engine.utils.artifacts import write_json, read_json, sha256_file, utc_now_iso


ARTIFACTS: List[Path] = [
    ANOMALY_DETECTOR_MODEL,
    THREAT_CLASSIFIER_MODEL,
    FEATURE_SCALER,
    LABEL_ENCODER,
    ANOMALY_METRICS_FILE,
    CLASSIFIER_METRICS_FILE,
    MODEL_METADATA_FILE,
]


def _version_id_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")


def get_active_version() -> Optional[str]:
    try:
        if ACTIVE_VERSION_FILE.exists():
            v = ACTIVE_VERSION_FILE.read_text(encoding="utf-8").strip()
            return v or None
    except Exception:
        return None
    return None


def set_active_version(version_id: str) -> None:
    ACTIVE_VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_VERSION_FILE.write_text(version_id.strip() + "\n", encoding="utf-8")


def list_versions(limit: int = 50) -> List[Dict[str, Any]]:
    MODEL_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    versions = []
    for d in sorted(MODEL_VERSIONS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        meta_path = d / "snapshot_metadata.json"
        meta = {}
        if meta_path.exists():
            try:
                meta = read_json(meta_path)
            except Exception:
                meta = {}
        versions.append({"version_id": d.name, "path": str(d), **meta})
        if len(versions) >= limit:
            break
    return versions


def snapshot_current_models(
    *,
    reason: str,
    run_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    version_id: Optional[str] = None,
    mark_active: bool = False,
) -> str:
    """
    Copy current model artifacts into a versioned folder.
    """
    MODEL_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    vid = version_id or _version_id_now()
    dest = MODEL_VERSIONS_DIR / vid
    dest.mkdir(parents=True, exist_ok=True)

    copied = []
    missing = []
    hashes: Dict[str, Optional[str]] = {}

    for p in ARTIFACTS:
        if p.exists():
            shutil.copy2(p, dest / p.name)
            copied.append(p.name)
            try:
                hashes[p.name] = sha256_file(p)
            except Exception:
                hashes[p.name] = None
        else:
            missing.append(p.name)
            hashes[p.name] = None

    meta = {
        "snapshot_at_utc": utc_now_iso(),
        "reason": reason,
        "run_id": run_id,
        "active_before": get_active_version(),
        "copied": copied,
        "missing": missing,
        "sha256": hashes,
        "extra": extra or {},
    }
    write_json(dest / "snapshot_metadata.json", meta)

    if mark_active:
        set_active_version(vid)

    return vid


def rollback_to_version(version_id: str) -> None:
    """
    Restore artifacts from a version directory back into ml_engine/models/.
    """
    src = MODEL_VERSIONS_DIR / version_id
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(f"Version not found: {version_id}")

    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for p in ARTIFACTS:
        candidate = src / p.name
        if candidate.exists():
            shutil.copy2(candidate, p)

    # Mark active version after restore
    set_active_version(version_id)


