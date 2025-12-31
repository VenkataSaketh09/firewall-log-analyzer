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


def enforce_log_retention(max_size_mb: int, delete_size_mb: int = 5) -> Dict[str, Any]:
    """
    Enforce a size-based retention policy on firewall logs.

    If the collection exceeds max_size_mb, deletes oldest documents (by timestamp)
    in size-based batches (e.g., delete 5MB worth of logs) until the size is within limit.
    
    Args:
        max_size_mb: Maximum collection size in MB
        delete_size_mb: Amount of space to free up per deletion cycle (in MB)
    """
    before_bytes = _get_collection_size_bytes()
    if before_bytes is None:
        return {"ok": False, "reason": "collStats unavailable"}

    max_bytes = int(max_size_mb) * 1024 * 1024
    delete_target_bytes = int(delete_size_mb) * 1024 * 1024
    deleted_total = 0

    while before_bytes > max_bytes:
        # Calculate how much we need to delete (with some buffer)
        excess_bytes = before_bytes - max_bytes
        # Delete at least the excess, plus the delete_size_mb to create buffer
        target_delete_bytes = max(excess_bytes, delete_target_bytes)
        
        # Get average document size from stats
        try:
            stats = db.command("collStats", logs_collection.name)
            avg_obj_size = stats.get("avgObjSize", 1024)  # Default 1KB if not available
        except Exception:
            avg_obj_size = 1024  # Fallback to 1KB per document
        
        # Estimate how many documents to delete to free up target_delete_bytes
        # Add 20% buffer to account for size variations
        estimated_docs_to_delete = int((target_delete_bytes / avg_obj_size) * 1.2)
        # Minimum batch size to ensure progress
        batch_size = max(100, min(estimated_docs_to_delete, 10000))
        
        # Fetch oldest docs
        cursor = logs_collection.find({}, {"_id": 1}).sort("timestamp", ASCENDING).limit(batch_size)
        ids: List[Any] = [doc["_id"] for doc in cursor]
        if not ids:
            break
        
        # Delete the batch
        result = logs_collection.delete_many({"_id": {"$in": ids}})
        deleted_count = int(result.deleted_count or 0)
        deleted_total += deleted_count
        
        if deleted_count == 0:
            break  # No more documents to delete

        # Re-check size after deletion
        before_bytes = _get_collection_size_bytes()
        if before_bytes is None:
            break
        
        # If we've deleted enough, break (size is now under limit)
        if before_bytes <= max_bytes:
            break

    after_bytes = _get_collection_size_bytes()
    return {
        "ok": True,
        "deleted_docs": deleted_total,
        "size_before_bytes": before_bytes,
        "size_after_bytes": after_bytes,
        "max_size_mb": max_size_mb,
        "deleted_size_mb": round((before_bytes - (after_bytes or before_bytes)) / (1024 * 1024), 2),
    }


def start_log_retention_worker(
    max_size_mb: Optional[int] = None,
    interval_seconds: Optional[int] = None,
    delete_size_mb: Optional[int] = None,
) -> None:
    """
    Start a background daemon thread that periodically enforces log retention.
    Safe to call multiple times; only starts once per process.
    
    Args:
        max_size_mb: Maximum collection size in MB (default: 480)
        interval_seconds: Check interval in seconds (default: 300 = 5 minutes)
        delete_size_mb: Amount of space to free up per cycle in MB (default: 5)
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

    max_size_mb = int(max_size_mb or os.getenv("LOG_RETENTION_MAX_MB", "480"))
    interval_seconds = int(interval_seconds or os.getenv("LOG_RETENTION_INTERVAL_SECONDS", "300"))
    delete_size_mb = int(delete_size_mb or os.getenv("LOG_RETENTION_DELETE_SIZE_MB", "5"))

    def _loop():
        # run once quickly at startup
        try:
            enforce_log_retention(max_size_mb=max_size_mb, delete_size_mb=delete_size_mb)
        except Exception:
            pass

        while True:
            time.sleep(interval_seconds)
            try:
                enforce_log_retention(max_size_mb=max_size_mb, delete_size_mb=delete_size_mb)
            except Exception:
                # Don't crash the worker
                pass

    t = threading.Thread(target=_loop, name="log-retention-worker", daemon=True)
    t.start()


