import os
import threading
import time
from typing import Optional, Dict, Any, List

from pymongo import ASCENDING

from app.db.mongo import db, logs_collection

_RETENTION_THREAD_STARTED = False
_RETENTION_THREAD_LOCK = threading.Lock()


def _get_collection_size_bytes() -> Optional[int]:
    """
    Returns collection size in bytes using MongoDB collStats.
    Returns None if the command fails.
    """
    try:
        stats = db.command("collStats", logs_collection.name)
        # Prefer logical size for retention decisions
        return int(stats.get("size", 0))
    except Exception:
        return None


def enforce_log_retention(max_size_mb: int, delete_batch_docs: int = 2000) -> Dict[str, Any]:
    """
    Enforce a size-based retention policy on firewall logs.

    If the collection exceeds max_size_mb, deletes oldest documents (by timestamp)
    in batches until the size is within limit.
    """
    before_bytes = _get_collection_size_bytes()
    if before_bytes is None:
        return {"ok": False, "reason": "collStats unavailable"}

    max_bytes = int(max_size_mb) * 1024 * 1024
    deleted_total = 0

    while before_bytes > max_bytes:
        # Fetch oldest docs
        cursor = logs_collection.find({}, {"_id": 1}).sort("timestamp", ASCENDING).limit(int(delete_batch_docs))
        ids: List[Any] = [doc["_id"] for doc in cursor]
        if not ids:
            break
        result = logs_collection.delete_many({"_id": {"$in": ids}})
        deleted_total += int(result.deleted_count or 0)

        # Re-check size
        before_bytes = _get_collection_size_bytes()
        if before_bytes is None:
            break

    after_bytes = _get_collection_size_bytes()
    return {
        "ok": True,
        "deleted_docs": deleted_total,
        "size_before_bytes": before_bytes,
        "size_after_bytes": after_bytes,
        "max_size_mb": max_size_mb,
    }


def start_log_retention_worker(
    max_size_mb: Optional[int] = None,
    interval_seconds: Optional[int] = None,
    delete_batch_docs: Optional[int] = None,
) -> None:
    """
    Start a background daemon thread that periodically enforces log retention.
    Safe to call multiple times; only starts once per process.
    """
    global _RETENTION_THREAD_STARTED

    with _RETENTION_THREAD_LOCK:
        if _RETENTION_THREAD_STARTED:
            return
        _RETENTION_THREAD_STARTED = True

    # Defaults via env
    enabled = os.getenv("LOG_RETENTION_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    if not enabled:
        return

    max_size_mb = int(max_size_mb or os.getenv("LOG_RETENTION_MAX_MB", "450"))
    interval_seconds = int(interval_seconds or os.getenv("LOG_RETENTION_INTERVAL_SECONDS", "300"))
    delete_batch_docs = int(delete_batch_docs or os.getenv("LOG_RETENTION_DELETE_BATCH_DOCS", "2000"))

    def _loop():
        # run once quickly at startup
        try:
            enforce_log_retention(max_size_mb=max_size_mb, delete_batch_docs=delete_batch_docs)
        except Exception:
            pass

        while True:
            time.sleep(interval_seconds)
            try:
                enforce_log_retention(max_size_mb=max_size_mb, delete_batch_docs=delete_batch_docs)
            except Exception:
                # Don't crash the worker
                pass

    t = threading.Thread(target=_loop, name="log-retention-worker", daemon=True)
    t.start()


