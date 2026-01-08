"""
SQL Injection Detection Service
Detects SQL injection attempts from firewall logs.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from collections import defaultdict
from app.db.mongo import logs_collection


def detect_sql_injection(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source_ip: Optional[str] = None,
    min_attempts: int = 1,
) -> List[Dict[str, Any]]:
    """
    Detect SQL injection attempts from logs.
    
    Args:
        start_date: Start of time range (default: 24 hours ago)
        end_date: End of time range (default: now)
        source_ip: Filter by specific source IP
        min_attempts: Minimum number of attempts to consider (default: 1)
    
    Returns:
        List of SQL injection detection dictionaries
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(hours=24)
    
    # Build query
    query = {
        "timestamp": {"$gte": start_date, "$lte": end_date},
        "event_type": {"$in": ["SQL_INJECTION_ATTEMPT", "SQL_AUTH_FAILED", "SQL_PORT_ACCESS"]}
    }
    
    if source_ip:
        query["source_ip"] = source_ip
    
    # Fetch logs
    logs = list(logs_collection.find(query).sort("timestamp", 1))
    
    if not logs:
        return []
    
    # Group by source IP
    ip_groups = defaultdict(list)
    for log in logs:
        ip = log.get("source_ip")
        if ip:
            ip_groups[ip].append(log)
    
    detections = []
    for ip, ip_logs in ip_groups.items():
        if len(ip_logs) < min_attempts:
            continue
        
        # Count by event type
        injection_attempts = [l for l in ip_logs if l.get("event_type") == "SQL_INJECTION_ATTEMPT"]
        auth_failed = [l for l in ip_logs if l.get("event_type") == "SQL_AUTH_FAILED"]
        port_access = [l for l in ip_logs if l.get("event_type") == "SQL_PORT_ACCESS"]
        
        total_attempts = len(ip_logs)
        injection_count = len(injection_attempts)
        
        # Determine severity
        if injection_count > 0:
            severity = "CRITICAL"
        elif len(auth_failed) >= 5:
            severity = "HIGH"
        elif total_attempts >= 10:
            severity = "HIGH"
        elif total_attempts >= 5:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        # Get ports accessed
        ports = list(set([l.get("destination_port") for l in ip_logs if l.get("destination_port")]))
        
        # Get timestamps
        timestamps = sorted([l.get("timestamp") for l in ip_logs if l.get("timestamp")])
        first_attempt = timestamps[0] if timestamps else None
        last_attempt = timestamps[-1] if timestamps else None
        
        detection = {
            "source_ip": ip,
            "severity": severity,
            "total_attempts": total_attempts,
            "injection_attempts": injection_count,
            "auth_failed_count": len(auth_failed),
            "port_access_count": len(port_access),
            "ports_attempted": ports,
            "first_attempt": first_attempt,
            "last_attempt": last_attempt,
            "detection_type": "SQL_INJECTION" if injection_count > 0 else "SQL_SUSPICIOUS_ACTIVITY"
        }
        
        detections.append(detection)
    
    # Sort by severity and last attempt time
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    detections.sort(
        key=lambda d: (
            severity_order.get(d.get("severity", "LOW"), 3),
            -(d.get("last_attempt") or datetime.min).timestamp()
        )
    )
    
    return detections

