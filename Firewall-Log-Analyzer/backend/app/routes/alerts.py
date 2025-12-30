from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.services.alert_service import get_or_compute_alerts, sort_alert_docs

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/latest")
def get_latest_alerts(
    lookback_seconds: int = Query(24 * 3600, ge=60, le=7 * 24 * 3600, description="Lookback window in seconds"),
    bucket_minutes: int = Query(5, ge=1, le=60, description="Bucket size in minutes for caching"),
    include_details: bool = Query(False, description="Include detector details payload (can be large)")
):
    """
    Return the latest computed alerts (persisted in MongoDB).
    This is backed by cached/stored computations so the dashboard doesn't have to recompute each time.
    """
    try:
        start_date, end_date, docs = get_or_compute_alerts(
            now=datetime.utcnow(),
            lookback_seconds=lookback_seconds,
            bucket_minutes=bucket_minutes,
        )
        docs = sort_alert_docs(docs)

        out = []
        for d in docs:
            out_doc = {
                "id": str(d.get("_id")) if d.get("_id") else None,
                "bucket_end": d.get("bucket_end").isoformat() if d.get("bucket_end") else None,
                "lookback_seconds": d.get("lookback_seconds"),
                "alert_type": d.get("alert_type"),
                "source_ip": d.get("source_ip"),
                "severity": d.get("severity"),
                "first_seen": d.get("first_seen").isoformat() if d.get("first_seen") else None,
                "last_seen": d.get("last_seen").isoformat() if d.get("last_seen") else None,
                "count": d.get("count", 0),
                "description": d.get("description", ""),
                "computed_at": d.get("computed_at").isoformat() if d.get("computed_at") else None,
            }
            if include_details:
                out_doc["details"] = d.get("details")
            out.append(out_doc)

        return {
            "time_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "count": len(out),
            "alerts": out,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")


