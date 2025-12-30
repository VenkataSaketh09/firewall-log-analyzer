from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.db.mongo import alerts_collection
from app.services.brute_force_detection import detect_brute_force
from app.services.ddos_detection import detect_ddos
from app.services.port_scan_detection import detect_port_scan


def floor_datetime(dt: datetime, minutes: int = 5) -> datetime:
    """Floor a UTC datetime to the nearest N-minute boundary."""
    if minutes <= 0:
        return dt.replace(second=0, microsecond=0)
    floored_minute = dt.minute - (dt.minute % minutes)
    return dt.replace(minute=floored_minute, second=0, microsecond=0)


def _severity_order(sev: str) -> int:
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return order.get((sev or "").upper(), 99)


def compute_alert_docs(
    *,
    start_date: datetime,
    end_date: datetime,
    bucket_end: datetime,
    lookback_seconds: int,
    max_per_type: int = 200,
) -> List[Dict[str, Any]]:
    """
    Compute alerts from logs and convert them into DB documents.
    This is still compute-heavy, but we cache results in Mongo for reuse.
    """
    brute_force = detect_brute_force(
        time_window_minutes=15,
        threshold=5,
        start_date=start_date,
        end_date=end_date,
    )[:max_per_type]

    ddos = detect_ddos(
        time_window_seconds=60,
        single_ip_threshold=100,
        distributed_ip_count=10,
        distributed_request_threshold=500,
        start_date=start_date,
        end_date=end_date,
    )[:max_per_type]

    port_scan = detect_port_scan(
        time_window_minutes=10,
        unique_ports_threshold=10,
        min_total_attempts=20,
        start_date=start_date,
        end_date=end_date,
    )[:max_per_type]

    docs: List[Dict[str, Any]] = []
    now = datetime.utcnow()

    for d in brute_force:
        docs.append(
            {
                "bucket_end": bucket_end,
                "lookback_seconds": lookback_seconds,
                "alert_type": "BRUTE_FORCE",
                "source_ip": d.get("source_ip") or "Unknown",
                "severity": d.get("severity") or "LOW",
                "first_seen": d.get("first_attempt"),
                "last_seen": d.get("last_attempt"),
                "count": int(d.get("total_attempts") or 0),
                "description": f"Brute force attack: {int(d.get('total_attempts') or 0)} failed login attempts",
                "details": d,
                "computed_at": now,
            }
        )

    for d in ddos:
        attack_type = d.get("attack_type") or "UNKNOWN"
        src_ips = d.get("source_ips") or []
        primary_ip = src_ips[0] if src_ips else "Multiple IPs"
        if attack_type == "DISTRIBUTED_FLOOD":
            description = (
                f"Distributed DDoS: {int(d.get('source_ip_count') or 0)} IPs, "
                f"{int(d.get('total_requests') or 0)} requests"
            )
        else:
            description = f"Single IP flood: {int(d.get('total_requests') or 0)} requests"

        docs.append(
            {
                "bucket_end": bucket_end,
                "lookback_seconds": lookback_seconds,
                "alert_type": "DDOS",
                "source_ip": primary_ip,
                "severity": d.get("severity") or "LOW",
                "first_seen": d.get("first_request"),
                "last_seen": d.get("last_request"),
                "count": int(d.get("total_requests") or 0),
                "description": description,
                "details": d,
                "computed_at": now,
            }
        )

    for d in port_scan:
        docs.append(
            {
                "bucket_end": bucket_end,
                "lookback_seconds": lookback_seconds,
                "alert_type": "PORT_SCAN",
                "source_ip": d.get("source_ip") or "Unknown",
                "severity": d.get("severity") or "LOW",
                "first_seen": d.get("first_attempt"),
                "last_seen": d.get("last_attempt"),
                "count": int(d.get("total_attempts") or 0),
                "description": f"Port scan detected: {int(d.get('unique_ports_attempted') or 0)} unique ports attempted",
                "details": d,
                "computed_at": now,
            }
        )

    return docs


def upsert_alert_docs(alert_docs: List[Dict[str, Any]]) -> None:
    for doc in alert_docs:
        alerts_collection.update_one(
            {
                "bucket_end": doc["bucket_end"],
                "lookback_seconds": doc["lookback_seconds"],
                "alert_type": doc["alert_type"],
                "source_ip": doc["source_ip"],
            },
            {"$set": doc},
            upsert=True,
        )


def get_cached_alert_docs(
    *,
    bucket_end: datetime,
    lookback_seconds: int,
    max_age_seconds: int = 120,
) -> Optional[List[Dict[str, Any]]]:
    """
    Return cached alerts for the bucket if they exist and are fresh enough.
    """
    threshold = datetime.utcnow() - timedelta(seconds=max_age_seconds)
    docs = list(
        alerts_collection.find(
            {
                "bucket_end": bucket_end,
                "lookback_seconds": lookback_seconds,
                "computed_at": {"$gte": threshold},
            }
        )
    )
    return docs or None


def get_or_compute_alerts(
    *,
    now: Optional[datetime] = None,
    lookback_seconds: int = 24 * 3600,
    bucket_minutes: int = 5,
) -> Tuple[datetime, datetime, List[Dict[str, Any]]]:
    """
    Fetch alerts from cache (Mongo) for a stable time bucket, otherwise compute and persist them.
    Returns (start_date, end_date, alert_docs).
    """
    if now is None:
        now = datetime.utcnow()
    bucket_end = floor_datetime(now, minutes=bucket_minutes)
    start_date = bucket_end - timedelta(seconds=lookback_seconds)

    cached = get_cached_alert_docs(bucket_end=bucket_end, lookback_seconds=lookback_seconds)
    if cached is not None:
        return start_date, bucket_end, cached

    computed = compute_alert_docs(
        start_date=start_date,
        end_date=bucket_end,
        bucket_end=bucket_end,
        lookback_seconds=lookback_seconds,
    )
    upsert_alert_docs(computed)
    return start_date, bucket_end, computed


def sort_alert_docs(alert_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        alert_docs,
        key=lambda d: (
            _severity_order(d.get("severity", "")),
            -(d.get("last_seen") or datetime.min).timestamp(),
        ),
    )


